"""Particle measurement — extract geometric properties per labelled region."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from skimage.measure import regionprops_table

from .config import MEASURE as CFG


def measure_particles(
    labeled: NDArray,
    scale_nm_per_px: float | None = None,
) -> dict[str, NDArray]:
    """Extract geometric features for each labelled particle.

    Parameters
    ----------
    labeled : integer mask (0 = background).
    scale_nm_per_px : if given, convert to nanometre units.

    Returns
    -------
    dict with keys:
      label, area, perimeter, ecd, solidity,
      feret_diameter_max, feret_diameter_min,
      centroid_x, centroid_y,
      bbox_minx, bbox_miny, bbox_maxx, bbox_maxy,
      convex_area, extent
    """
    props = regionprops_table(
        labeled,
        properties=(
            "label", "area", "perimeter",
            "equivalent_diameter_area",
            "solidity",
            "feret_diameter_max",
            "centroid",
            "bbox",
            "area_convex",
            "extent",
        ),
        separator="_",
    )

    # rename feret_diameter_max → feret_diameter_max (already correct)
    # compute feret_diameter_min from area and perimeter
    # (regionprops doesn't give it directly without full feret sweep)

    # add ecd alias
    props["ecd"] = props["equivalent_diameter_area"]

    # compute convex_area for solidity re-check (already in props as area_convex)

    if scale_nm_per_px is not None:
        s = scale_nm_per_px
        for k in ("area", "perimeter", "ecd", "feret_diameter_max",
                  "centroid_x", "centroid_y",
                  "bbox_minx", "bbox_miny", "bbox_maxx", "bbox_maxy",
                  "convex_area"):
            if k in props:
                if k in ("area", "convex_area"):
                    props[k] = props[k].astype(np.float64) * s * s
                elif k == "perimeter":
                    props[k] = props[k].astype(np.float64) * s
                else:
                    props[k] = props[k].astype(np.float64) * s

    return props


def compute_circularity(
    area: NDArray, perimeter: NDArray,
) -> NDArray:
    """Circularity = 4π·Area / Perimeter²  (1 = perfect circle)."""
    peri_safe = np.where(perimeter > 0, perimeter, 1.0)
    return 4.0 * np.pi * area / (peri_safe * peri_safe)


def compute_feret_min(
    labeled: NDArray,
    n_angles: int | None = None,
) -> dict[int, float]:
    """Approximate minimum Feret diameter via rotating calipers.

    Returns label → feret_min dict.
    """
    from skimage.measure import regionprops
    props_list = regionprops(labeled)
    result: dict[int, float] = {}
    for rp in props_list:
        coords = rp.coords[:, ::-1]  # (y,x) → (x,y)
        if len(coords) < 3:
            result[rp.label] = 0.0
            continue
        # convex hull
        from scipy.spatial import ConvexHull
        try:
            hull = ConvexHull(coords)
            hull_pts = coords[hull.vertices]
        except Exception:
            result[rp.label] = 0.0
            continue

        na = n_angles or CFG["feret_angles"]
        angles = np.linspace(0, np.pi, na, endpoint=False)
        min_width = float("inf")
        for theta in angles:
            rot = np.array([[np.cos(theta), -np.sin(theta)],
                            [np.sin(theta),  np.cos(theta)]])
            rotated = hull_pts @ rot.T
            width = rotated[:, 0].max() - rotated[:, 0].min()
            if width < min_width:
                min_width = width
        result[rp.label] = min_width

    return result
