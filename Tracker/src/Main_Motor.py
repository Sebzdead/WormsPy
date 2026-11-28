from __future__ import annotations
import sys
import os

# Add parent directory to path so src module can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import csv
import time
import numpy as np
import cv2
import yaml

from src.capture import Camera
from src.background import RunningAverageBG, threshold_and_clean
from src.segmentation import connected_components
from src.tracking import MultiTracker
from src.visualize import draw_objects, draw_tracks
from src.utils import ensure_gray, to_uint8_vis, put_fps, put_hint

from zaber_motion import Units
from zaber_motion.ascii import Connection

# 你的标定文件
CALIB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "camera_stage_calibration.yaml")


def parse_args():
    ap = argparse.ArgumentParser(
        description="1 FPS capture + BG removal + connected components + tracking + Zaber stage"
    )
    ap.add_argument('--serial', type=str, default='23251773', help='FLIR camera serial number (default 23251773)')
    ap.add_argument('--width', type=int, default=3000, help='request width')
    ap.add_argument('--height', type=int, default=3000, help='request height')
    ap.add_argument('--alpha', type=float, default=0.02, help='running-average BG alpha (0..1)')
    ap.add_argument('--thresh', type=int, default=20, help='foreground binary threshold (0..255)')
    ap.add_argument('--min-area', type=int, default=50, help='minimum area to keep a blob')
    ap.add_argument('--max-missed', type=int, default=3, help='max missed frames before deleting a track')
    ap.add_argument('--max-dist', type=float, default=60.0, help='max centroid distance to associate (pixels)')
    ap.add_argument('--save', action='store_true', help='start with save-to-video enabled')
    ap.add_argument('--outdir', type=str, default='output', help='output directory')
    ap.add_argument('--video', type=str, default=None, help='use a video file as fake camera input')
    return ap.parse_args()


# ==========================
# 标定 & 寻找最近轨迹
# ==========================

def load_calibration(calib_path: str = CALIB_FILE):
    if not os.path.exists(calib_path):
        raise FileNotFoundError(f"Calibration file not found: {calib_path}")
    with open(calib_path, "r") as f:
        calib = yaml.safe_load(f)
    H = np.array(calib["H_pix2world"], dtype=float)
    stage_cfg = calib.get("stage", {})
    return H, stage_cfg


def pixel_to_world_mm(u: float, v: float, H: np.ndarray):
    p = np.array([u, v, 1.0], dtype=float)
    w = H @ p
    if w[2] == 0:
        raise RuntimeError("Homography mapping produced w[2]=0.")
    w = w / w[2]
    x = float(w[0])
    y = float(w[1])
    x = x
    y = y
    return x,y


def find_closest_track(tracker: MultiTracker, click_xy: tuple[int, int], max_dist_px: float = 50.0):
    if not tracker.tracks:
        return None, None
    cx, cy = click_xy
    best_tid = None
    best_pos = None
    best_d2 = float("inf")

    for tid, tr in tracker.tracks.items():
        if not tr.trace:
            continue
        t_last, x_last, y_last = tr.trace[-1]
        dx = x_last - cx
        dy = y_last - cy
        d2 = dx * dx + dy * dy
        if d2 < best_d2:
            best_d2 = d2
            best_tid = tid
            best_pos = (x_last, y_last)

    if best_tid is None:
        return None, None
    if best_d2 > max_dist_px * max_dist_px:
        return None, None
    return best_tid, best_pos


# ==========================
# 主程序
# ==========================

def main():
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    # ---------- 载入标定 ----------
    H = None
    stage_cfg = {}
    try:
        H, stage_cfg = load_calibration(CALIB_FILE)
        print(f"[Calib] Loaded calibration from {CALIB_FILE}")
    except Exception as e:
        print(f"[Calib] WARNING: cannot load calibration: {e}")

    # ---------- 初始化 Zaber ----------
    connection = None
    axis_x = None
    axis_y = None
    try:
        port = stage_cfg.get("port", "COM6") if H is not None else "COM6"
        print(f"[Stage] Opening port {port} ...")

        connection = Connection.open_serial_port(port)
        connection.enable_alerts()

        device_list = connection.detect_devices()
        print(f"[Stage] Found {len(device_list)} devices on {port}")
        for i, dev in enumerate(device_list):
            print(f"  Device[{i}] addr={dev.device_address}, name={dev.name}")

        if len(device_list) == 0:
            print("[Stage] No devices found, stage disabled.")
        else:
            # 这里用第一个设备当 X，第二个设备当 Y
            device_x = device_list[0]
            axis_x = device_x.get_axis(1)

            if not axis_x.is_homed():
                print("[Stage] Homing X axis...")
                axis_x.home()

            if len(device_list) > 1:
                device_y = device_list[1]
                axis_y = device_y.get_axis(1)
                if not axis_y.is_homed():
                    print("[Stage] Homing Y axis...")
                    axis_y.home()

            print("[Stage] Homing done.")
            
            # Set higher velocity for faster movement
            try:
                axis_x.velocity = 3.0  # mm/s
                print(f"[Stage] X axis velocity set to {axis_x.velocity} mm/s")
                if axis_y is not None:
                    axis_y.velocity = 3.0  # mm/s
                    print(f"[Stage] Y axis velocity set to {axis_y.velocity} mm/s")
            except Exception as e:
                print(f"[Stage] WARNING: could not set velocity: {e}")

            # ---------- 开始采集前，移动到 (0, 0) mm ----------
            try:
                moving_axes = []
                if axis_x is not None:
                    axis_x.move_absolute(
                        0.0,
                        Units.LENGTH_MILLIMETRES,
                        wait_until_idle=False  # 非阻塞，下同
                    )
                    moving_axes.append(axis_x)
                if axis_y is not None:
                    axis_y.move_absolute(
                        0.0,
                        Units.LENGTH_MILLIMETRES,
                        wait_until_idle=False
                    )
                    moving_axes.append(axis_y)

                for ax in moving_axes:
                    ax.wait_until_idle()

                print("[Stage] Moved to (0, 0) mm before capture.")
            except Exception as e:
                print(f"[Stage] WARNING: failed to move to (0,0): {e}")

            print("[Stage] Ready.")
    except Exception as e:
        print(f"[Stage] ERROR initializing stage: {e}")
        connection = None
        axis_x = None
        axis_y = None

    # ---------- 相机 ----------
    if args.video:
        from src.capture_fake import Camera as FakeCamera
        cam = FakeCamera(
            video_path=args.video,
            width=args.width,
            height=args.height,
            loop=True,
            sample_every_n=1
        )
    else:
        from src.capture import Camera as RealCamera
        cam = RealCamera(width=args.width, height=args.height, serial_number=args.serial)

    bg = RunningAverageBG(alpha=args.alpha)
    tracker = MultiTracker(max_missed=args.max_missed, max_dist=args.max_dist)

    writer = None
    saving = args.save

    last = time.time()
    fps = 0.0
    paused = False
    csv_path = os.path.join(args.outdir, 'tracks.csv')

    # 鼠标选择状态
    selected_track_id = None

    win_name = 'FLIR 1FPS Tracker'
    cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win_name, 1440, 1440)

    # ---------- 鼠标回调：点击 worm → 最近轨迹 → 像素→mm → move ----------
    def on_mouse(event, x, y, flags, param):
        nonlocal selected_track_id
        if event == cv2.EVENT_LBUTTONDOWN:
            if H is None:
                print("[Click] No calibration loaded, cannot map to mm.")
                return
            if axis_x is None and axis_y is None:
                print("[Click] Stage not initialized, cannot move.")
                return

            tid, pos = find_closest_track(tracker, (x, y), max_dist_px=50.0)
            if tid is None:
                # No nearby track: move to the clicked pixel position
                print("[Click] No track close to click. Moving to clicked position.")
                selected_track_id = None
                px, py = x, y
            else:
                selected_track_id = tid
                px, py = pos
            x_mm, y_mm = pixel_to_world_mm(px, py, H)
            print(f"[Click] Track {tid} at pixel ({px:.1f}, {py:.1f}) -> ({x_mm:.2f}, {y_mm:.2f}) mm")

            try:
                moving_axes = []

                if axis_x is not None:
                    axis_x.move_absolute(
                        x_mm,
                        Units.LENGTH_MILLIMETRES,
                        wait_until_idle=False
                    )
                    moving_axes.append(axis_x)

                if axis_y is not None:
                    axis_y.move_absolute(
                        y_mm,
                        Units.LENGTH_MILLIMETRES,
                        wait_until_idle=False
                    )
                    moving_axes.append(axis_y)

                # 现在两个轴已经在动，统一等待结束
                for ax in moving_axes:
                    ax.wait_until_idle()

                print("[Stage] Move complete.")
                # Release all resources after move completes
                if writer is not None:
                    writer.release()
                cam.release()
                if connection is not None:
                    connection.close()
                    print("[Stage] Connection closed.")
                print("[Stage] All resources released.")
                return
            except Exception as e:
                print(f"[Stage] Move failed: {e}")

    cv2.setMouseCallback(win_name, on_mouse)

    # ---------- 主循环 ----------
    with open(csv_path, 'w', newline='') as fcsv:
        wcsv = csv.writer(fcsv)
        wcsv.writerow(['time_s', 'id', 'x', 'y'])

        while True:
            t0 = time.time()
            if not paused:
                frame = cam.read()
                start_proc = time.time()
                g = ensure_gray(frame)

                # 背景与前景
                fg, bg_img = bg.apply(g)
                mask = threshold_and_clean(fg, thresh=args.thresh, ksize=3, iters=1)

                # 连通域与质心
                objects, _ = connected_components(mask, min_area=args.min_area)
                dets = [obj['centroid'] for obj in objects]

                # 跟踪
                tracker.step(dets, t0)

                # 可视化
                vis_bg = cv2.applyColorMap(to_uint8_vis(bg_img), cv2.COLORMAP_INFERNO)
                vis_fg = cv2.applyColorMap(to_uint8_vis(fg),    cv2.COLORMAP_INFERNO)
                vis_mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

                overlay = draw_objects(g, objects)
                overlay = draw_tracks(overlay, tracker.tracks)

                # 高亮当前选中的 track
                if selected_track_id is not None and selected_track_id in tracker.tracks:
                    tr = tracker.tracks[selected_track_id]
                    if tr.trace:
                        _, sx, sy = tr.trace[-1]
                        cv2.circle(overlay, (int(sx), int(sy)), 10, (0, 255, 255), 2)
                        cv2.putText(
                            overlay,
                            f"SELECTED {selected_track_id}",
                            (int(sx) + 10, int(sy) - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (0, 255, 255),
                            2
                        )

                top = np.hstack([overlay, vis_bg])
                bottom = np.hstack([vis_fg, vis_mask])
                tiled = np.vstack([top, bottom])
                put_fps(tiled, fps)
                put_hint(tiled, "q=quit, s=save, p=pause, click worm to move stage", y=40)

                cv2.imshow(win_name, overlay)

                end_proc = time.time()
                proc_time = end_proc - t0
                print(f"[{time.strftime('%H:%M:%S')}] Frame processed in {proc_time:.3f} s")

                # 写视频
                if saving and writer is None:
                    h, w = tiled.shape[:2]
                    writer = cv2.VideoWriter(
                        os.path.join(args.outdir, 'annotated.mp4'),
                        cv2.VideoWriter_fourcc(*'mp4v'),
                        10.0,
                        (w, h)
                    )
                if saving and writer is not None:
                    writer.write(tiled)

                # 写 CSV
                for tid, tr in tracker.tracks.items():
                    if tr.trace:
                        t, x, y = tr.trace[-1]
                        wcsv.writerow([f"{t:.3f}", tid, f"{x:.2f}", f"{y:.2f}"])
                        fcsv.flush()

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                saving = not saving
                if not saving and writer is not None:
                    writer.release()
                    writer = None
            elif key == ord('p'):
                paused = not paused

            # 控制到 ~1 FPS
            if not paused:
                elapsed = time.time() - t0
                if elapsed < 1.0:
                    time.sleep(1.0 - elapsed)

            now = time.time()
            fps = 1.0 / max(1e-9, now - last)
            last = now

    if writer is not None:
        writer.release()
    cam.release()
    if connection is not None:
        connection.close()
        print("[Stage] Connection closed.")
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()