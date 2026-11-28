from __future__ import annotations
import numpy as np
import cv2
from .utils import ensure_gray

class RunningAverageBG:
    """简单的运行平均背景模型，适合缓慢变化的场景。"""
    def __init__(self, alpha=0.02):
        self.alpha = float(alpha)
        self.bg = None

    def apply(self, frame_gray):
        frame_gray = ensure_gray(frame_gray).astype(np.float32)
        if self.bg is None:
            self.bg = frame_gray.copy()
        # 背景更新
        self.bg = (1.0 - self.alpha) * self.bg + self.alpha * frame_gray
        # 前景差分
        fg = cv2.absdiff(frame_gray, self.bg).astype(np.float32)
        return fg, self.bg

def threshold_and_clean(fg, thresh=20, ksize=3, iters=1):
    """阈值 + 形态学开闭降噪。"""
    fg8 = cv2.convertScaleAbs(fg)
    _, mask = cv2.threshold(fg8, thresh, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ksize, ksize))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=iters)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=iters)
    return mask
