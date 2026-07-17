"""Agglomerate filtering — classify particles as single vs. agglomerate."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from .config import FILTER as CFG


def classify_particles(
    area: NDArray,
    perimeter: NDArray,
    solidity: NDArray,
    extent: NDArray,
    feret_max: NDArray,
    feret_min: NDArray,
) -> NDArray:
    """Return boolean mask: True = single particle, False = agglomerate.

    Heuristics
    ----------
    - Circularity < min → irregular → likely agglomerate.
    - Solidity < min → porous → likely agglomerate.
    - Area > max_relative × median → too large → agglomerate.
    - Aspect ratio > max → very elongated → likely agglomerate or debris.
    """
    peri_safe = np.where(perimeter > 0, perimeter, 1.0)
    circularity = 4.0 * np.pi * area / (peri_safe * peri_safe)

    median_area = float(np.median(area)) if len(area) > 0 else 1.0
    relative_area = area / max(median_area, 1.0)

    aspect_ratio = np.where(
        feret_min > 0,
        feret_max / feret_min,
        1.0,
    )

    mask = np.ones(len(area), dtype=bool)
    mask &= circularity >= CFG["circularity_min"]
    mask &= solidity >= CFG["solidity_min"]
    mask &= relative_area <= CFG["max_relative_area"]
    mask &= aspect_ratio <= CFG["aspect_ratio_max"]

    return mask
