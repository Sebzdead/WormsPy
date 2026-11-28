from __future__ import annotations
import cv2
import numpy as np
import yaml
import os
from capture import Camera  # 你的 PySpin 相机类
# 显示缩放系数（只影响 UI，不影响真实计算）
DISPLAY_SCALE = 0.35
CALIB_FILE = "C:\\Users\\User\\Documents\\WormSpy\\WormSpy\\backend\\code\\modules\\FlirTracker\\src\\camera_stage_calibration.yaml"
class CalibState:
    """
    每个点有自己的 stack + 全局撤销栈
    """
    def __init__(self):
        self.current_label: str | None = None
        # 当前使用的坐标（每个点只保留“当前版本”）
        self.points: dict[str, tuple[int, int] | None] = {
            "center": None,
            "bottom_left": None,
            "bottom_right": None,
            "top_right": None,
        }
        # 历史栈：每个点一个栈
        self.stacks: dict[str, list[tuple[int, int]]] = {
            "center": [],
            "bottom_left": [],
            "bottom_right": [],
            "top_right": [],
        }
        # 全局撤销历史：记录最近 push 的 label
        self.global_history: list[str] = []
        # 每个点的颜色
        self.colors = {
            "center":      (0, 255, 255),  # yellow
            "bottom_left": (255, 0, 0),    # blue
            "bottom_right": (0, 255, 0),   # green
            "top_right":   (0, 0, 255),    # red
        }
        # 显示用名字（画在图上的文字）
        self.display_names = {
            "center": "CENTER",
            "bottom_left": "BOTTOM-LEFT",
            "bottom_right": "BOTTOM-RIGHT",
            "top_right": "TOP-RIGHT",
        }
    def push_point(self, label: str, pt: tuple[int, int]):
        """记录一个新点（压入 stack + 更新当前值 + 记录全局历史）"""
        self.stacks[label].append(pt)
        self.points[label] = pt
        self.global_history.append(label)
        print(f":加粗的对钩: Recorded {label} at {pt}")
    def undo_last(self):
        """撤销最近一个点（全局）"""
        if not self.global_history:
            print(":警告: No point to undo")
            return
        last_label = self.global_history.pop()
        stack = self.stacks[last_label]
        if stack:
            stack.pop()
        self.points[last_label] = stack[-1] if stack else None
        print(f":左弯钩: Undo {last_label}, now = {self.points[last_label]}")
def grab_one_frame_from_flir(serial_number: str = "23251773"):
    cam = Camera(serial_number=serial_number)
    try:
        frame = cam.read()
    finally:
        cam.release()
    return frame
def to_builtin(obj):
    """
    递归把 numpy 类型转换成 Python 原生类型，方便 YAML 保存。
    """
    if isinstance(obj, dict):
        return {k: to_builtin(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_builtin(x) for x in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj
def main():
    frame = grab_one_frame_from_flir()
    if frame.ndim == 2:
        disp = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
    else:
        disp = frame.copy()
    state = CalibState()
    win = "Calibration (scaled view)"
    cv2.namedWindow(win)
    # 鼠标：点击记录点
    def mouse_cb(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and state.current_label is not None:
            # 映射回原图坐标
            real_x = int(x / DISPLAY_SCALE)
            real_y = int(y / DISPLAY_SCALE)
            h, w = disp.shape[:2]
            real_x = int(np.clip(real_x, 0, w - 1))
            real_y = int(np.clip(real_y, 0, h - 1))
            state.push_point(state.current_label, (real_x, real_y))
            state.current_label = None
    cv2.setMouseCallback(win, mouse_cb)
    while True:
        canvas = disp.copy()
        # ============ 把指令画在窗口上 ============
        instructions = [
            "Calibration Instructions:",
            " 1: CENTER (15,15) -> CLICK",
            " 2: BOTTOM-LEFT (0,50.8) -> CLICK",
            " 3: BOTTOM-RIGHT (50.8,50.8) -> CLICK",
            " 4: TOP-RIGHT (50.8,0) -> CLICK",
            " u: undo last point",
            " q: save and exit",
            " ESC: cancel",
        ]
        FONT = cv2.FONT_HERSHEY_SIMPLEX
        SCALE = 1.5
        THICKNESS = 2
        COLOR = (0, 255, 0)  # 绿色
        (_, text_h), _ = cv2.getTextSize("Sample", FONT, SCALE, THICKNESS)
        LINE_SPACING = text_h + 8
        y0 = 40
        for i, text in enumerate(instructions):
            y = y0 + i * LINE_SPACING
            cv2.putText(
                canvas,
                text,
                (20, y),
                FONT,
                SCALE,
                COLOR,
                THICKNESS,
                cv2.LINE_AA,
            )
        # 显示当前等待的点类型
        if state.current_label is not None:
            cv2.putText(
                canvas,
                f"Waiting for: {state.current_label}",
                (20, y0 + len(instructions) * LINE_SPACING),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 255, 255),
                2,
                cv2.LINE_AA,
            )
        # 画四个点和文字标签（文字挪到点右下，避免和指令重叠）
        for label, pt in state.points.items():
            if pt is not None:
                color = state.colors[label]
                name = state.display_names[label]
                x, y = pt
                # 点本身
                cv2.circle(canvas, (x, y), 8, color, -1)
                # 标签文字：稍微偏右下，避免挡住点
                text_offset_x = 10
                text_offset_y = 25
                cv2.putText(
                    canvas,
                    name,
                    (x + text_offset_x, y + text_offset_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    color,
                    2,
                    cv2.LINE_AA,
                )
        # 缩小显示
        small = cv2.resize(canvas, None, fx=DISPLAY_SCALE, fy=DISPLAY_SCALE)
        cv2.imshow(win, small)
        key = cv2.waitKey(20) & 0xFF
        # ESC — 退出不保存
        if key == 27:
            print(":x: Canceled")
            cv2.destroyAllWindows()
            return
        # 选择点类型
        if key == ord('1'):
            state.current_label = "center"
        elif key == ord('2'):
            state.current_label = "bottom_left"
        elif key == ord('3'):
            state.current_label = "bottom_right"
        elif key == ord('4'):
            state.current_label = "top_right"
        # 撤销
        if key == ord('u'):
            state.undo_last()
        # 保存
        if key == ord('q'):
            if all(state.points[label] is not None for label in state.points):
                break
            else:
                incomplete = [l for l in state.points if state.points[l] is None]
                print(":警告: Missing:", incomplete)
    cv2.destroyAllWindows()
    # ============ 保存标定矩阵 ============
    order = ["center", "bottom_left", "bottom_right", "top_right"]
    pixel_pts = np.array([state.points[l] for l in order], np.float32)
    world_pts = np.array([
        [15, 15],       # center
        [0.0, 50.8],      # bottom-left
        [50.8, 50.8],     # bottom-right
        [50.8, 0.0],      # top-right
    ], np.float32)
    H = cv2.getPerspectiveTransform(pixel_pts, world_pts)
    calib = {
        "pixel_points": {l: state.points[l] for l in order},
        "pixel_points_order": order,
        "world_points_mm": world_pts.tolist(),
        "H_pix2world": H.tolist(),
        "stage": {
            "port": "COM6",
            "x_device_address": 1,
            "y_device_address": 2,
            "travel_mm": 50.8,
        },
    }
    # 先把 numpy 类型转成原生 Python，再写 YAML
    calib_clean = to_builtin(calib)
    with open(CALIB_FILE, "w") as f:
        yaml.safe_dump(calib_clean, f, sort_keys=False)
    print(":礼花: Saved calibration to:", os.path.abspath(CALIB_FILE))
if __name__ == "__main__":
    main()