from __future__ import annotations
import cv2
import numpy as np

def draw_objects(frame, objects):
    out = frame.copy()
    if out.ndim == 2:
        out = cv2.cvtColor(out, cv2.COLOR_GRAY2BGR)
    for obj in objects:
        x, y, w, h = obj['bbox']
        cx, cy = obj['centroid']
        cv2.rectangle(out, (x,y), (x+w,y+h), (0,255,0), 1)
        cv2.circle(out, (int(cx), int(cy)), 3, (0,0,255), -1)
    return out

def draw_tracks(frame, tracks):
    out = frame.copy()
    if out.ndim == 2:
        out = cv2.cvtColor(out, cv2.COLOR_GRAY2BGR)
    for tid, tr in tracks.items():
        pts = [(int(x), int(y)) for (_, x, y) in tr.trace[-100:]]
        for i in range(1, len(pts)):
            cv2.line(out, pts[i-1], pts[i], (255,0,0), 2)
        cx, cy = tr.centroid
        cv2.putText(out, f"ID {tid}", (int(cx)+5, int(cy)-5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,0), 1, cv2.LINE_AA)
    return out

