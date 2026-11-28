from __future__ import annotations
import argparse, os, csv, time
import numpy as np
import cv2

from capture import Camera
from background import RunningAverageBG, threshold_and_clean
from segmentation import connected_components
from tracking import MultiTracker
from visualize import draw_objects, draw_tracks
from utils import ensure_gray, to_uint8_vis, put_fps, put_hint

def parse_args():
    ap = argparse.ArgumentParser(description="1 FPS capture + BG removal + connected components + tracking")
    ap.add_argument('--serial', type=str, default='23251773', help='FLIR camera serial number (default 23251773)')
    ap.add_argument('--width', type=int, default=None, help='request width')
    ap.add_argument('--height', type=int, default=None, help='request height')
    ap.add_argument('--alpha', type=float, default=0.02, help='running-average BG alpha (0..1)')
    ap.add_argument('--thresh', type=int, default=20, help='foreground binary threshold (0..255)')
    ap.add_argument('--min-area', type=int, default=50, help='minimum area to keep a blob')
    ap.add_argument('--max-missed', type=int, default=3, help='max missed frames before deleting a track')
    ap.add_argument('--max-dist', type=float, default=60.0, help='max centroid distance to associate (pixels)')
    ap.add_argument('--save', action='store_true', help='start with save-to-video enabled')
    ap.add_argument('--outdir', type=str, default='output', help='output directory')
    ap.add_argument('--video', type=str, default=None, help='use a video file as fake camera input')
    return ap.parse_args()

def main():
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    if args.video:
        from .capture_fake import Camera as FakeCamera
        cam = FakeCamera(video_path=args.video, width=args.width, height=args.height, loop=True, sample_every_n=1)
    else:
        from .capture import Camera as RealCamera
        cam = RealCamera(width=args.width, height=args.height, serial_number=args.serial)
    bg = RunningAverageBG(alpha=args.alpha)
    tracker = MultiTracker(max_missed=args.max_missed, max_dist=args.max_dist)

    writer = None
    saving = args.save

    last = time.time()
    fps = 0.0
    paused = False
    csv_path = os.path.join(args.outdir, 'tracks.csv')

    with open(csv_path, 'w', newline='') as fcsv:
        wcsv = csv.writer(fcsv)
        wcsv.writerow(['time_s','id','x','y'])

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

                # 可视化：原图/背景/前景/掩膜 拼图 + 轨迹
                vis_bg = cv2.applyColorMap(to_uint8_vis(bg_img), cv2.COLORMAP_INFERNO)
                vis_fg = cv2.applyColorMap(to_uint8_vis(fg),    cv2.COLORMAP_INFERNO)
                vis_mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

                overlay = draw_objects(g, objects)
                overlay = draw_tracks(overlay, tracker.tracks)

                # top = np.hstack([cv2.cvtColor(g, cv2.COLOR_GRAY2BGR), vis_bg])
                top = np.hstack([overlay, vis_bg])
                bottom = np.hstack([vis_fg, vis_mask])
                tiled = np.vstack([top, bottom])
                put_fps(tiled, fps)
                put_hint(tiled, "q=quit, s=save toggle, p=pause", y=40)

                cv2.namedWindow('FLIR 1FPS Tracker', cv2.WINDOW_NORMAL)
                cv2.resizeWindow('FLIR 1FPS Tracker', 1440, 1440)  # 指定窗口大小
                cv2.imshow('FLIR 1FPS Tracker', overlay)

                end_proc = time.time()
                proc_time = end_proc - t0  # 或 end_proc - start_proc
                print(f"[{time.strftime('%H:%M:%S')}] Frame processed in {proc_time:.3f} s")

                # 延迟创建视频写入器（知道分辨率后）
                if saving and writer is None:
                    h, w = tiled.shape[:2]
                    writer = cv2.VideoWriter(os.path.join(args.outdir, 'annotated.mp4'),
                                             cv2.VideoWriter_fourcc(*'mp4v'),
                                             10.0, (w, h))
                if saving and writer is not None:
                    writer.write(tiled)

                # 写入 CSV（每个轨迹的最新点）
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

            # —— 控制到 ~1 FPS —— #
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
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
