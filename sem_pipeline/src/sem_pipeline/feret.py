"""Feret diameter calculations for particle classification."""

from __future__ import annotations

import numpy as np
from scipy.spatial import ConvexHull


def compute_feret_min_all(
    labels: np.ndarray,
    labels_list: list[int],
) -> np.ndarray:
    """Compute minimum Feret diameter for each particle label.

    Uses convex hull + rotating calipers approximation (18 angles).
    """
    n = len(labels_list)
    feret_min = np.zeros(n)

    for i, lbl in enumerate(labels_list):
        mask = labels == lbl
        ys, xs = np.where(mask)
        if len(ys) < 3:
            feret_min[i] = 0
            continue
        pts = np.column_stack([xs, ys])
        try:
            hull = ConvexHull(pts)
            hp = pts[hull.vertices]
            min_w = float("inf")
            for theta in np.linspace(0, np.pi, 18, endpoint=False):
                rot = np.array(
                    [[np.cos(theta), -np.sin(theta)],
                     [np.sin(theta),  np.cos(theta)]],
                )
                rp = hp @ rot.T
                w = rp[:, 0].max() - rp[:, 0].min()
                if w < min_w:
                    min_w = w
            feret_min[i] = min_w
        except Exception:
            feret_min[i] = 0

    return feret_min
