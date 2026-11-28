from __future__ import annotations
import cv2
import numpy as np

def ensure_gray(frame):
    if frame.ndim == 3:
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return frame

def to_uint8_vis(img):
    """
    将16位/浮点影像线性拉伸到8位以便可视化。
    兼容 NumPy 2.0（使用 np.ptp 而非 ndarray.ptp），并处理全常数图像避免除零。
    """
    img = np.asarray(img)

    if img.dtype == np.uint16:
        # 16位：用分位数做鲁棒拉伸，避免热像极值干扰
        mn, mx = np.percentile(img, (1, 99))
        if not np.isfinite(mn) or not np.isfinite(mx) or mx <= mn:
            return np.zeros(img.shape, dtype=np.uint8)
        out = np.clip((img - mn) * (255.0 / (mx - mn)), 0, 255).astype(np.uint8)
        return out

    if np.issubdtype(img.dtype, np.floating):
        mn = float(np.nanmin(img))
        mx = float(np.nanmax(img))
        if not np.isfinite(mn) or not np.isfinite(mx) or mx <= mn:
            return np.zeros(img.shape, dtype=np.uint8)
        out = np.clip((img - mn) * (255.0 / (mx - mn)), 0, 255).astype(np.uint8)
        return out

    if img.dtype != np.uint8:
        # 其他整数类型，直接做幅度映射
        rng = float(np.ptp(img))  # 注意：这里用 np.ptp()，兼容 NumPy 2.0
        if rng <= 0 or not np.isfinite(rng):
            return np.zeros(img.shape, dtype=np.uint8)
        out = np.clip((img - img.min()) * (255.0 / rng), 0, 255).astype(np.uint8)
        return out

    return img
def put_fps(img, fps):
    cv2.putText(img, f"{fps:.1f} FPS", (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1, cv2.LINE_AA)

def put_hint(img, text, y=40):
    cv2.putText(img, text, (10, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255), 1, cv2.LINE_AA)
