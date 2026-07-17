"""Preprocessing — enhance contrast, denoise, and optionally crop SEM UI."""

from __future__ import annotations

import cv2
import numpy as np
from numpy.typing import NDArray

from .config import PREPROCESS as CFG


def enhance(image: NDArray) -> NDArray:
    """Apply CLAHE contrast enhancement to a BGR image."""
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(
        clipLimit=CFG["clahe_clip_limit"],
        tileGridSize=CFG["clahe_tile_size"],
    )
    l_eq = clahe.apply(l)
    merged = cv2.merge([l_eq, a, b])
    return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)


def denoise(image: NDArray) -> NDArray:
    """Bilateral filter — preserves edges while removing noise."""
    return cv2.bilateralFilter(
        image,
        d=CFG["bilateral_d"],
        sigmaColor=CFG["bilateral_sigma_color"],
        sigmaSpace=CFG["bilateral_sigma_space"],
    )


def crop_margins(image: NDArray) -> NDArray:
    """Crop a thin margin to remove SEM UI borders."""
    h, w = image.shape[:2]
    m = CFG["crop_margin_pct"]
    y0, y1 = int(h * m), int(h * (1 - m))
    x0, x1 = int(w * m), int(w * (1 - m))
    return image[y0:y1, x0:x1]


def preprocess(image: NDArray) -> NDArray:
    """Full pipeline: enhance → denoise."""
    img = enhance(image)
    img = denoise(img)
    return img
