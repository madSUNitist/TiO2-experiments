"""Statistical analysis — D10, D50, D90, descriptive stats."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from .config import STATS as CFG


def particle_statistics(sizes_nm: NDArray) -> dict[str, float]:
    """Compute descriptive statistics for a 1-D array of particle sizes.

    Returns dict with count, mean, std, min, max, median, and
    user-configured percentiles (D10, D25, D50, D75, D90).
    """
    if len(sizes_nm) == 0:
        return {"count": 0}

    stats: dict[str, float] = {
        "count": float(len(sizes_nm)),
        "mean": float(np.mean(sizes_nm)),
        "std": float(np.std(sizes_nm)),
        "min": float(np.min(sizes_nm)),
        "max": float(np.max(sizes_nm)),
        "median": float(np.median(sizes_nm)),
    }

    for p in CFG["percentiles"]:
        stats[f"D{p}"] = float(np.percentile(sizes_nm, p))

    return stats


def aggregate_statistics(
    all_results: list[dict[str, NDArray]],
    labels: list[str],
) -> dict:
    """Merge per-image statistics into a summary."""
    all_sizes = np.concatenate([r["ecd"] for r in all_results])
    summary = particle_statistics(all_sizes)
    summary["total_particles"] = float(len(all_sizes))
    summary["num_images"] = float(len(all_results))

    per_image = {}
    for lbl, res in zip(labels, all_results):
        per_image[lbl] = particle_statistics(res["ecd"])

    return {"summary": summary, "per_image": per_image}
