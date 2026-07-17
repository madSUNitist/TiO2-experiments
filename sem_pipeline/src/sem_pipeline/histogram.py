"""Per-image and combined histograms with log-normal fits."""

from __future__ import annotations

import numpy as np
from scipy import stats as sp_stats

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def save_histogram(
    size_data: np.ndarray,
    name: str,
    out_path: str,
    unit: str = "nm",
) -> None:
    """Save single-image histogram with log-normal fit."""
    fig, ax = plt.subplots(figsize=(9, 6))
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")

    n_bins = 40
    ax.hist(
        size_data, bins=n_bins, color="#2166ac",
        edgecolor="white", linewidth=0.5, alpha=0.85, density=True,
    )

    if len(size_data) >= 5:
        shape, loc, scale = sp_stats.lognorm.fit(size_data, floc=0)
        x_fit = np.linspace(size_data.min(), size_data.max(), 200)
        pdf_fit = sp_stats.lognorm.pdf(x_fit, shape, loc, scale)
        ax.plot(x_fit, pdf_fit, color="#b2182b", linewidth=2)
        mu = np.log(scale)
        sigma = shape
        mean_ln = np.exp(mu + sigma**2 / 2)
        std_ln = mean_ln * np.sqrt(np.exp(sigma**2) - 1)
    else:
        mean_ln = size_data.mean()
        std_ln = size_data.std()

    ax.set_xlabel(f"Feret diameter ({unit})", fontsize=12)
    ax.set_ylabel("Density", fontsize=12)
    ax.set_title(f"{name}  —  {len(size_data)} single particles", fontsize=13, fontweight="bold")
    ax.tick_params(labelsize=10)
    ax.text(
        0.97, 0.95,
        f"mean = {mean_ln:.0f} {unit}\n"
        f"std  = {std_ln:.0f} {unit}\n"
        f"median = {np.median(size_data):.0f} {unit}",
        transform=ax.transAxes, fontsize=9, ha="right", va="top",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                  edgecolor="#cccccc", alpha=0.9),
    )
    fig.tight_layout()
    fig.savefig(out_path, transparent=True)
    plt.close(fig)


def save_combined_histogram(
    group_vals: list[np.ndarray],
    labels: list[str],
    colors: list[str],
    out_path: str,
) -> None:
    """Save stacked combined histogram across image groups."""
    all_vals = np.concatenate(group_vals)
    bins = np.histogram_bin_edges(all_vals, bins=50)

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")

    ax.hist(
        group_vals, bins=bins, stacked=True,
        color=colors[:len(group_vals)], label=labels,
        edgecolor="white", linewidth=0.3, density=True,
    )

    shape, loc, scale = sp_stats.lognorm.fit(all_vals, floc=0)
    xf = np.linspace(all_vals.min(), all_vals.max(), 300)
    pf = sp_stats.lognorm.pdf(xf, shape, loc, scale)
    ax.plot(xf, pf, color="#333333", linewidth=2.5)

    mu = np.log(scale)
    sigma = shape
    ml = np.exp(mu + sigma**2 / 2)
    sl = ml * np.sqrt(np.exp(sigma**2) - 1)

    ax.set_xlabel("Feret diameter (nm)", fontsize=12)
    ax.set_ylabel("Density", fontsize=12)
    ax.set_title(f"Combined  —  {len(all_vals)} particles", fontsize=13, fontweight="bold")
    ax.legend(fontsize=8, ncol=2)
    ax.tick_params(labelsize=10)
    ax.text(
        0.97, 0.95,
        f"mean = {ml:.0f} nm\n"
        f"std  = {sl:.0f} nm\n"
        f"median = {np.median(all_vals):.0f} nm",
        transform=ax.transAxes, fontsize=9, ha="right", va="top",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                  edgecolor="#cccccc", alpha=0.9),
    )
    fig.tight_layout()
    fig.savefig(out_path, transparent=True)
    plt.close(fig)
