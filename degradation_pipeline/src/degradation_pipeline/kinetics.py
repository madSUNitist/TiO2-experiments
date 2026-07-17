"""Photocatalytic degradation kinetics of Rhodamine B by TiO2.

Generates two figures:
  1. Degradation curve (c/c0 vs t)
  2. First-order kinetic fit (ln(c/c0) vs t) with rate constant k
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

_PKG = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = _PKG / "output"


t = np.array([0, 5, 15, 30, 45, 60, 90], dtype=np.float64)
A = np.array([1.351, 1.125, 1.043, 0.745, 0.475, 0.229, 0.058],
             dtype=np.float64)

A0 = A[0]
c_over_c0 = A / A0
ln_c_over_c0 = np.log(c_over_c0)


def plot_degradation_curve(t_data=None, A_data=None, suffix="") -> None:
    if t_data is None:
        t_data = t
        A_data = A
    A_d = np.asarray(A_data, dtype=np.float64)
    c_c0 = A_d / A_d[0]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(6, 3.5))
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")

    ax.plot(t_data, c_c0, "o-", color="#2166ac", markersize=6,
            linewidth=1.5, markerfacecolor="white",
            markeredgewidth=1.5, label="c / c₀")

    ax.set_xlabel("Time (min)", fontsize=12)
    ax.set_ylabel("c / c₀", fontsize=12)
    ax.set_title("Photocatalytic Degradation of RhB", fontsize=13,
                 fontweight="bold")
    ax.set_ylim(0, 1.05)
    ax.tick_params(labelsize=10)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.legend(fontsize=10, framealpha=0.5,
              edgecolor="#cccccc").get_frame().set_facecolor("white")

    fig.tight_layout()
    base = f"degradation_curve{suffix}"
    for fmt in ("svg", "pdf"):
        fig.savefig(OUTPUT_DIR / f"{base}.{fmt}", transparent=True)
    plt.close(fig)
    print(f"Degradation curve saved -> {OUTPUT_DIR / base}")


def plot_kinetic_fit(t_data=None, A_data=None, suffix="") -> None:
    if t_data is None:
        t_data = t
        A_data = A
    t_d = np.asarray(t_data, dtype=np.float64)
    A_d = np.asarray(A_data, dtype=np.float64)
    c_c0 = A_d / A_d[0]
    ln_c_c0 = np.log(c_c0)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    slope, intercept, rval, pval, stderr = stats.linregress(
        t_d, ln_c_c0,
    )
    k = -slope
    r_squared = rval ** 2

    t_fit = np.linspace(0, t_d.max() * 1.05, 100)
    ln_fit = slope * t_fit + intercept

    fig, ax = plt.subplots(figsize=(6, 3.5))
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")

    ax.scatter(t_d, ln_c_c0, color="#2166ac", s=40, zorder=3,
               edgecolors="white", linewidths=0.8, label="Data")
    ax.plot(t_fit, ln_fit, "--", color="#b2182b", linewidth=1.5,
            label=(f"Linear fit\n"
                   f"ln(c/c₀) = {slope:.4f} t + {intercept:.4f}\n"
                   f"k = {k:.4f} min⁻¹\n"
                   f"R² = {r_squared:.4f}"))

    ax.set_xlabel("Time (min)", fontsize=12)
    ax.set_ylabel("ln(c / c₀)", fontsize=12)
    ax.set_title("First-Order Kinetic Fit", fontsize=13,
                 fontweight="bold")
    ax.tick_params(labelsize=10)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.spines["bottom"].set_position("zero")
    ax.xaxis.set_label_coords(0.5, -0.12)
    ax.legend(fontsize=9, framealpha=0.5,
              edgecolor="#cccccc").get_frame().set_facecolor("white")

    fig.tight_layout()
    base = f"kinetic_fit{suffix}"
    for fmt in ("svg", "pdf"):
        fig.savefig(OUTPUT_DIR / f"{base}.{fmt}", transparent=True)
    plt.close(fig)
    print(f"Kinetic fit saved -> {OUTPUT_DIR / base}")
    print(f"  k = {k:.4f} +/- {stderr:.4f} min^-1")
    print(f"  intercept = {intercept:.4f}")
    print(f"  R^2 = {r_squared:.4f}")
