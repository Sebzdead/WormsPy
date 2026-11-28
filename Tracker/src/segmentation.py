from __future__ import annotations
import cv2

def connected_components(mask, min_area=50):
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
    objects = []
    for i in range(1, num_labels):  # 0 是背景
        x, y, w, h, area = stats[i]
        cx, cy = centroids[i]
        if area >= min_area:
            objects.append({
                'label': i,
                'bbox': (int(x), int(y), int(w), int(h)),
                'area': int(area),
                'centroid': (float(cx), float(cy)),
            })
    return objects, labels
