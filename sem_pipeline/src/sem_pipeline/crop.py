"""Crop the largest axis-aligned non-blue rectangle from an SEM image.

Blue pixels correspond to SEM UI text annotations (B > 180, dominant over R, G).
The search is restricted to the central 90 % of the image.
"""

from __future__ import annotations

import numpy as np


def crop_sem_region(image: np.ndarray) -> np.ndarray:
    B = image[:, :, 0].astype(np.float32)
    G = image[:, :, 1].astype(np.float32)
    R = image[:, :, 2].astype(np.float32)
    blue = (B > 180) & (B > G * 1.2) & (B > R * 1.2)

    h, w = image.shape[:2]
    m = 0.05
    y0, y1 = int(h * m), int(h * (1 - m))
    x0, x1 = int(w * m), int(w * (1 - m))
    blue_crop = blue[y0:y1, x0:x1]
    ch, cw = blue_crop.shape

    heights = np.zeros(cw, dtype=np.int32)
    best = None
    best_area = 0

    for row in range(ch):
        heights = np.where(blue_crop[row, :], 0, heights + 1)
        stack = []
        for col in range(cw + 1):
            hc = heights[col] if col < cw else 0
            start = col
            while stack and stack[-1][0] > hc:
                hp, sp = stack.pop()
                area = hp * (col - sp)
                if area > best_area:
                    best_area = area
                    best = (sp, row - hp + 1, col - 1, row)
                start = sp
            if col < cw and (not stack or stack[-1][0] < hc):
                stack.append((hc, start))

    if best is None:
        return image[y0:y1, x0:x1]

    bx1, by1, bx2, by2 = best
    return image[y0 + by1:y0 + by2 + 1, x0 + bx1:x0 + bx2 + 1]
