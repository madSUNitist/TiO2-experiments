"""Particle segmentation for SEM TiO2 images."""

from __future__ import annotations

import cv2
import numpy as np
from numpy.typing import NDArray
from scipy import ndimage as ndi
from skimage.feature import peak_local_max
from skimage.segmentation import watershed
from skimage.measure import regionprops_table


def segment(image_bgr: NDArray,
            threshold: int = 170,
            min_area: int = 20,
            max_area_ratio: float = 8.0,
            min_distance: int = 4,
            dilate_iters: int = 2,
            ) -> tuple[NDArray, dict]:
    """Segment particles from a cropped SEM image.

    Large connected components in the binary mask (agglomerates)
    are removed BEFORE watershed to prevent them from being split
    into many false small particles.
    """
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)

    binary = (gray > threshold).astype(np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
    dilated = cv2.dilate(closed, kernel, iterations=dilate_iters)

    # remove large connected components (agglomerates) before watershed
    num_cc, cc_labels = cv2.connectedComponents(dilated, connectivity=8)
    if num_cc > 1:
        cc_areas = np.bincount(cc_labels.ravel())[1:]  # skip background
        if len(cc_areas) > 1:
            median_cc = float(np.median(cc_areas))
            max_allowed = median_cc * max_area_ratio
            for lbl in range(1, num_cc):
                if cc_areas[lbl - 1] > max_allowed:
                    dilated[cc_labels == lbl] = 0

    distance = ndi.distance_transform_edt(dilated)
    coords = peak_local_max(distance, min_distance=min_distance,
                            labels=dilated, exclude_border=False)
    markers = np.zeros_like(distance, dtype=np.int32)
    for i, (y, x) in enumerate(coords):
        markers[y, x] = i + 1

    labels = watershed(-distance, markers, mask=dilated.astype(bool))
    labels = labels.astype(np.int32)

    h, w = labels.shape
    for lbl in np.unique(labels):
        if lbl == 0:
            continue
        mask = (labels == lbl)
        if mask.sum() < min_area:
            labels[mask] = 0
            continue
        ys, xs = np.where(mask)
        if (ys.min() <= 1 or ys.max() >= h - 2 or
                xs.min() <= 1 or xs.max() >= w - 2):
            labels[mask] = 0

    props = regionprops_table(
        labels,
        properties=("label", "area", "perimeter",
                    "equivalent_diameter_area", "solidity",
                    "feret_diameter_max", "centroid", "bbox", "extent"),
        separator="_",
    )
    props["ecd"] = props["equivalent_diameter_area"]
    props["circularity"] = (
        4.0 * np.pi * props["area"]
        / np.maximum(props["perimeter"] ** 2, 1.0)
    )

    return labels, props
