"""Scale-bar detection — find the bar via brightness + tick marks."""

from __future__ import annotations

import cv2
import numpy as np
from numpy.typing import NDArray

# calibrated ROI (fractions from top-left)
X_LEFT = 0.2545
X_RIGHT = 0.3251
Y_TOP = 0.9143
Y_BOT = 0.9655
THRESHOLD = 190

# known physical sizes per image group (nm)
PHYS_MAP: dict[str, float] = {
    "01": 3000, "02": 3000, "03": 3000,
    "06": 5000, "07": 5000, "08": 5000,
    "09": 5000, "11": 5000, "12": 5000,
}


def detect(image: NDArray) -> dict:
    """Find the scale bar and return its pixel length."""
    h, w = image.shape[:2]

    x1 = int(X_LEFT * w); x2 = int(X_RIGHT * w)
    y1 = int(Y_TOP * h); y2 = int(Y_BOT * h)
    if x2 <= x1 or y2 <= y1:
        return {}

    roi = image[y1:y2, x1:x2]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if roi.ndim == 3 else roi
    rh, rw = gray.shape

    bright = gray > THRESHOLD

    row_sum = bright.sum(axis=1)
    bar_y = int(np.argmax(row_sum))

    bar_band = bright[max(0, bar_y - 2):min(rh, bar_y + 3), :]
    bar_col = bar_band.sum(axis=0) > 0
    runs = _runs(bar_col)
    if not runs:
        return {}
    bar_run = max(runs, key=lambda r: r[1] - r[0])
    bar_L, bar_R = bar_run

    ticks = []
    for col in range(bar_L, bar_R + 1):
        above = bright[max(0, bar_y - 12):bar_y + 1, col].sum()
        below = bright[bar_y:min(rh, bar_y + 12), col].sum()
        if above >= 2 and below >= 2:
            ticks.append(col)

    merged = _merge_ticks(ticks)

    if len(merged) >= 4:
        bar_px = (merged[-2] + merged[-1]) / 2.0 - (merged[0] + merged[1]) / 2.0
        bar_x1 = x1 + merged[0]
        bar_x2 = x1 + merged[-1]
    elif len(merged) >= 2:
        bar_px = float(merged[-1] - merged[0] + 1)
        bar_x1 = x1 + merged[0]
        bar_x2 = x1 + merged[-1]
    else:
        bar_px = float(bar_R - bar_L + 1)
        bar_x1 = x1 + bar_L
        bar_x2 = x1 + bar_R

    return {
        "bar_px": round(bar_px, 1),
        "bar_y": round(float(y1 + bar_y), 1),
        "bar_x1": round(float(bar_x1), 1),
        "bar_x2": round(float(bar_x2), 1),
    }


def get_scale(image_name: str, image: NDArray | None = None) -> float:
    """Return nm-per-pixel for a given image."""
    from pathlib import Path
    name = image_name
    if "/" in name or "\\" in name:
        name = Path(image_name).stem
    phys = PHYS_MAP.get(name, 0)
    if phys <= 0 or image is None:
        return 0.0

    bar = detect(image)
    if not bar or bar["bar_px"] <= 0:
        return 0.0

    return phys / bar["bar_px"]


def _runs(mask):
    runs = []
    s = -1
    for i, d in enumerate(mask):
        if d and s < 0: s = i
        elif not d and s >= 0: runs.append((s, i - 1)); s = -1
    if s >= 0: runs.append((s, len(mask) - 1))
    return runs


def _merge_ticks(ticks):
    if not ticks:
        return []
    mg = [ticks[0]]
    for t in ticks[1:]:
        if t - mg[-1] > 3:
            mg.append(t)
    return mg
