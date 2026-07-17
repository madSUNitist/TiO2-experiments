"""Cumulative ECD distribution plot from existing CSV data."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

from .config import OUTPUT_DIR, KEYS


COLORS = ["#2166ac", "#b2182b", "#4daf4a", "#ff7f00", "#984ea3", "#a65628"]


def plot_cumulative() -> None:
    data_dir = OUTPUT_DIR / "data"
    hist_dir = OUTPUT_DIR / "histograms"
    hist_dir.mkdir(parents=True, exist_ok=True)

    arrays: dict[str, np.ndarray] = {}
    for k in KEYS:
        csv_path = data_dir / f"{k}_particles.csv"
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            arrays[k] = df["ecd_nm"].to_numpy(dtype=np.float64)
            print(f"{k}: {len(arrays[k])} particles")

    if not arrays:
        print("No particle CSV files found.")
        return

    combined = np.concatenate(list(arrays.values()))

    fig, ax = plt.subplots(figsize=(10, 6))

    for (k, v), c in zip(arrays.items(), COLORS):
        vs = np.sort(v)
        cy = np.arange(1, len(vs) + 1) / len(vs) * 100.0
        ax.plot(vs, cy, color=c, lw=1.2, alpha=0.6,
                label=f"{k} (n={len(v)})")

    cs = np.sort(combined)
    cc = np.arange(1, len(cs) + 1) / len(cs) * 100.0
    ax.plot(cs, cc, "k-", lw=2.5,
            label=f"Combined (n={len(combined)})")

    d10 = float(np.percentile(combined, 10))
    d50 = float(np.percentile(combined, 50))
    d90 = float(np.percentile(combined, 90))
    for val, lbl in [(d10, "D10"), (d50, "D50"), (d90, "D90")]:
        ax.axvline(val, color="gray", ls="--", alpha=0.5)
        ax.text(val, 52, f"  {lbl}={val:.0f}", fontsize=8,
                color="gray", rotation=90, va="bottom")

    shape, loc, scale = stats.lognorm.fit(combined, floc=0)
    xf = np.linspace(float(combined.min()), float(combined.max()), 300)
    cf = stats.lognorm.cdf(xf, shape, loc, scale) * 100.0
    ax.plot(xf, cf, "r--", lw=2, label="Log-normal fit")

    mu = np.log(scale)
    sigma = shape
    mean_ln = float(np.exp(mu + sigma * sigma / 2.0))
    std_ln = float(mean_ln * np.sqrt(np.exp(sigma * sigma) - 1.0))

    ax.set_xlabel("ECD (nm)")
    ax.set_ylabel("Cumulative (%)")
    ax.set_title("Cumulative ECD Distribution")
    ax.legend(fontsize=8, loc="lower right")
    ax.set_xlim(0, float(combined.max()) * 1.02)
    ax.set_ylim(0, 105)

    ax.text(
        0.97, 0.35,
        f"Log-normal fit:\n"
        f"mean = {mean_ln:.0f} nm\n"
        f"std  = {std_ln:.0f} nm\n"
        f"D10 = {d10:.0f} nm\n"
        f"D50 = {d50:.0f} nm\n"
        f"D90 = {d90:.0f} nm",
        transform=ax.transAxes, fontsize=9, ha="right", va="top",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.85),
    )

    fig.tight_layout()
    out = hist_dir / "combined_cumulative.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)

    print(f"Saved: {out}")
    print(f"Combined: n={len(combined)}  mean={mean_ln:.0f}  std={std_ln:.0f}  "
          f"median={d50:.0f}  D10={d10:.0f}  D90={d90:.0f} nm")
