"""Draw annotated SEM images with particle contours and Feret diameters."""

from __future__ import annotations

import cv2
import numpy as np
from scipy.spatial import ConvexHull


def annotate_particles(
    image: np.ndarray,
    labels_map: np.ndarray,
    label_ids: np.ndarray,
    feret_values: np.ndarray,
    single_mask: np.ndarray,
    nm_per_px: float,
) -> tuple[np.ndarray, list[tuple[int, int, int, int]]]:
    """Draw particle outlines (green=single, red=agglomerate) and Feret lines.

    Parameters
    ----------
    image : 2D label map from segmentation.
    labels_map : label image (2D int array).
    label_ids : 1D array of label IDs matching feret_values order.
    feret_values : Feret max diameter per particle.
    single_mask : bool array, True = single particle.
    nm_per_px : nanometres per pixel scale.

    Returns
    -------
    annotated_image, feret_line_coords [(x1,y1,x2,y2), ...]
    """
    n = len(label_ids)
    vis = image.copy()
    feret_lines: list[tuple[int, int, int, int]] = []

    for i in range(n):
        lbl = int(label_ids[i])
        mask = (labels_map == lbl).astype(np.uint8)
        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE,
        )
        cv2.drawContours(
            vis, contours, -1,
            (0, 255, 0) if single_mask[i] else (0, 0, 255), 1,
        )

        ys, xs = np.where(mask)
        if len(ys) < 3:
            feret_lines.append((0, 0, 0, 0))
            continue
        pts = np.column_stack([xs, ys])
        try:
            hull = ConvexHull(pts)
            hull_pts = pts[hull.vertices]
        except Exception:
            feret_lines.append((0, 0, 0, 0))
            continue

        max_d2 = 0
        p1 = p2 = (0, 0)
        for a in range(len(hull_pts)):
            for b in range(a + 1, len(hull_pts)):
                d2 = (hull_pts[a][0] - hull_pts[b][0]) ** 2 + \
                     (hull_pts[a][1] - hull_pts[b][1]) ** 2
                if d2 > max_d2:
                    max_d2 = d2
                    p1 = (int(hull_pts[a][0]), int(hull_pts[a][1]))
                    p2 = (int(hull_pts[b][0]), int(hull_pts[b][1]))

        cv2.line(vis, p1, p2, (255, 0, 0), 1)
        feret_lines.append((*p1, *p2))

        dia = float(feret_values[i]) * nm_per_px if nm_per_px else float(feret_values[i])
        mx = (p1[0] + p2[0]) // 2
        my = (p1[1] + p2[1]) // 2
        text = f"{dia:.0f}"
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.3, 1)
        cv2.putText(
            vis, text, (mx - tw // 2, my + th // 2),
            cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1,
        )

    return vis, feret_lines
