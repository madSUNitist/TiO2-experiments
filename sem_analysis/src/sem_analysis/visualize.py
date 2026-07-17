"""Visualization — annotated particle images and size-distribution histograms."""

from __future__ import annotations

from pathlib import Path

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from numpy.typing import NDArray

from .config import VISUALIZE as CFG


def draw_particle_outlines(
    image_bgr: NDArray,
    labeled: NDArray,
    single_mask: NDArray | None = None,
) -> NDArray:
    """Draw coloured outlines on the image for each particle.

    single_mask: bool array (True = single particle, False = agglomerate).
    If provided, single particles get green outlines;
    agglomerates get red outlines.
    """
    disp = image_bgr.copy()
    props = _regionprops_simple(labeled)

    green = CFG["particle_outline_color"]       # (0, 255, 0) BGR
    red = CFG["agglomerate_outline_color"]       # (255, 0, 0) BGR
    cyan = (255, 255, 0)  # BGR cyan for unclassified

    for i, (contour, lbl) in enumerate(props):
        if single_mask is not None:
            color = green if single_mask[i] else red
        else:
            color = cyan

        cv2.drawContours(disp, [contour.astype(np.int32)], -1, color, 1, cv2.LINE_AA)

        # label number
        M = cv2.moments(contour)
        if M["m00"] > 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            cv2.putText(disp, str(lbl), (cx - 8, cy + 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, color, 1, cv2.LINE_AA)

    return disp


def _regionprops_simple(labeled: NDArray) -> list[tuple[NDArray, int]]:
    """Quick (contour, label) pairs."""
    from skimage.measure import regionprops
    result = []
    for rp in regionprops(labeled):
        contour = _mask_to_contour(labeled == rp.label)
        if contour is not None and len(contour) >= 3:
            result.append((contour, rp.label))
    return result


def _mask_to_contour(mask: NDArray) -> NDArray | None:
    """Get the outer contour of a binary mask."""
    m = mask.astype(np.uint8) * 255
    contours, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    # squeeze to (N, 2) → (N, 1, 2)
    c = max(contours, key=cv2.contourArea)
    return c


def plot_histogram(
    sizes_nm: NDArray,
    title: str,
    output_path: str | Path,
    *,
    unit: str = "nm",
) -> None:
    """Save a size-distribution histogram."""
    fig, ax = plt.subplots(figsize=CFG["figsize_histogram"])
    bins = CFG["histogram_bins"]

    if len(sizes_nm) < 2:
        ax.text(0.5, 0.5, "Not enough data", ha="center", va="center",
                transform=ax.transAxes)
    else:
        ax.hist(sizes_nm, bins=bins, color=CFG["histogram_color"],
                edgecolor="white", alpha=0.85, density=True)

        # overlay KDE
        try:
            from scipy.stats import gaussian_kde
            kde = gaussian_kde(sizes_nm)
            xs = np.linspace(sizes_nm.min(), sizes_nm.max(), 200)
            ax.plot(xs, kde(xs), color="#b2182b", linewidth=1.5)
        except Exception:
            pass

        # vertical lines for D10, D50, D90
        if len(sizes_nm) >= 4:
            d10 = np.percentile(sizes_nm, 10)
            d50 = np.percentile(sizes_nm, 50)
            d90 = np.percentile(sizes_nm, 90)
            for val, lbl, ls in [(d10, "D10", "--"),
                                  (d50, "D50", "-"),
                                  (d90, "D90", "--")]:
                ax.axvline(val, color="#333333", linestyle=ls, linewidth=1.0, alpha=0.7)
                ax.text(val, ax.get_ylim()[1] * 0.92, f" {lbl}={val:.0f}",
                        fontsize=8, color="#333333", rotation=90, va="top")

        stats_text = (
            f"N={len(sizes_nm)}  "
            f"mean={np.mean(sizes_nm):.0f}  "
            f"std={np.std(sizes_nm):.0f}  "
            f"median={np.median(sizes_nm):.0f}"
        )

    ax.set_xlabel(f"Particle size ({unit})")
    ax.set_ylabel("Density")
    ax.set_title(title)
    ax.text(0.98, 0.96, stats_text, transform=ax.transAxes,
            fontsize=9, ha="right", va="top",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.75))

    fig.tight_layout()
    fig.savefig(output_path, dpi=CFG["dpi"])
    plt.close(fig)
