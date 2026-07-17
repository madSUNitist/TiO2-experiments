"""Experimental: phase ratio via inner product / NNLS spectral unmixing.

Approaches:
  1. Spurr-Myers (single-peak RIR) — current method
  2. NNLS full-pattern — y_exp = w_a * Ana + w_r * Rut + offset
  3. NNLS no-offset — same without baseline offset term
  4. Cosine ratio — simple ratio of inner products

Usage:
    cd xrd_pipeline
    uv run python tools/inner_product_ratio.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import nnls

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from xrd_pipeline.data import parse_xrd_file
from xrd_pipeline.processing import process_data, estimate_phase_composition
from xrd_pipeline.simulation import get_anatase_peaks, get_rutile_peaks
from xrd_pipeline.config import (
    DATA_DIR, OUTPUT_DIR,
    COLOR_ANATASE, COLOR_RUTILE, COLOR_PATTERN,
)

FWHM = 1.0

# Focus on the main peak region (exclude low-angle and high-angle noise)
TT_MASK = (20.0, 65.0)


def _broaden_to_grid(tt_peaks, intens_peaks, tt_grid, fwhm=FWHM):
    y = np.zeros_like(tt_grid, dtype=np.float64)
    sigma = fwhm / (2 * np.sqrt(2 * np.log(2)))
    for pos, intens in zip(tt_peaks, intens_peaks):
        y += intens * np.exp(-0.5 * ((tt_grid - pos) / sigma) ** 2)
    return y


def _ratio_from_weights(w_a, w_r):
    if w_a + w_r > 1e-10:
        return round(100 * w_a / (w_a + w_r), 1), round(100 * w_r / (w_a + w_r), 1)
    return 0.0, 0.0


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    txt_files = sorted(DATA_DIR.glob("*.txt"))
    if not txt_files:
        print("No .txt files found")
        return

    tt_a, intens_a_raw = get_anatase_peaks()
    tt_r, intens_r_raw = get_rutile_peaks()

    hdr = (
        f"{'Sample':<25s}  {'Spurr-Myers':>18s}  "
        f"{'NNLS+off':>18s}  {'NNLS no-off':>18s}  {'cos-ratio':>18s}"
    )
    print(hdr)
    print("-" * 105)

    for txt_path in txt_files:
        tt_exp, intens_exp, name = parse_xrd_file(txt_path)
        smoothed, _baseline = process_data(intens_exp)

        a_spurr, r_spurr, _status = estimate_phase_composition(tt_exp, smoothed)

        # ---- build broadened references on experimental grid ----
        y_a = _broaden_to_grid(tt_a, intens_a_raw, tt_exp)
        y_r = _broaden_to_grid(tt_r, intens_r_raw, tt_exp)

        # ---- mask to main peak region ----
        mask = (tt_exp >= TT_MASK[0]) & (tt_exp <= TT_MASK[1])
        tt_m = tt_exp[mask]
        y_exp_m = smoothed[mask]
        y_a_m = y_a[mask]
        y_r_m = y_r[mask]

        # Normalise each to max=1 within the mask
        y_a_n = y_a_m / np.max(y_a_m)
        y_r_n = y_r_m / np.max(y_r_m)
        y_exp_n = y_exp_m / np.max(y_exp_m)

        # ---- cosine similarity ----
        norm_exp = np.linalg.norm(y_exp_n)
        cos_a = np.dot(y_exp_n, y_a_n) / (norm_exp * np.linalg.norm(y_a_n))
        cos_r = np.dot(y_exp_n, y_r_n) / (norm_exp * np.linalg.norm(y_r_n))
        # Simple ratio from cosines
        cos_total = cos_a + cos_r
        a_cos = round(100 * cos_a / cos_total, 1) if cos_total > 0 else 0.0
        r_cos = round(100 * cos_r / cos_total, 1) if cos_total > 0 else 0.0

        # ---- NNLS with offset ----
        A_off = np.column_stack([y_a_n, y_r_n, np.ones_like(y_exp_n)])
        w_off, _ = nnls(A_off, y_exp_n)
        a_off, r_off = _ratio_from_weights(w_off[0], w_off[1])
        y_recon_off = A_off @ w_off
        ss_res_off = np.sum((y_exp_n - y_recon_off) ** 2)
        ss_tot_off = np.sum((y_exp_n - np.mean(y_exp_n)) ** 2)
        r2_off = 1 - ss_res_off / ss_tot_off if ss_tot_off > 0 else 0.0

        # ---- NNLS without offset ----
        A_no = np.column_stack([y_a_n, y_r_n])
        w_no, _ = nnls(A_no, y_exp_n)
        a_no, r_no = _ratio_from_weights(w_no[0], w_no[1])
        y_recon_no = A_no @ w_no
        ss_res_no = np.sum((y_exp_n - y_recon_no) ** 2)
        ss_tot_no = np.sum((y_exp_n - np.mean(y_exp_n)) ** 2)
        r2_no = 1 - ss_res_no / ss_tot_no if ss_tot_no > 0 else 0.0

        spurr_str = f"A {a_spurr}% R {r_spurr}%"
        off_str = f"A {a_off}% R {r_off}%"
        no_str = f"A {a_no}% R {r_no}%"
        cos_str = f"A {a_cos}% R {r_cos}%"
        print(f"{name:<25s}  {spurr_str:>18s}  {off_str:>18s}  {no_str:>18s}  {cos_str:>18s}")

        # Plot first sample
        if txt_path == txt_files[0]:
            _plot_decomposition(
                tt_m, y_exp_n, y_a_n, y_r_n,
                w_no, y_recon_no, r2_no,
                name, a_spurr, r_spurr, a_no, r_no,
                a_off, r_off, r2_off, a_cos, r_cos,
                cos_a, cos_r,
            )


def _plot_decomposition(
    tt, y_exp, y_a, y_r,
    w, y_recon, r2,
    name, a_s, r_s, a_n, r_n,
    a_off, r_off, r2_off, a_cos, r_cos, cos_a, cos_r,
):
    fig, axes = plt.subplots(3, 1, figsize=(18, 12), sharex=True)

    # Panel 1: experimental
    ax = axes[0]
    ax.plot(tt, y_exp, linewidth=0.7, color=COLOR_PATTERN)
    ax.set_ylim(-0.04, 1.15)
    ax.set_ylabel("Normalised intensity")
    ax.set_title(f"{name}  (mask {TT_MASK[0]:.0f}°–{TT_MASK[1]:.0f}°)", fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Panel 2: NNLS decomposition (no offset)
    ax = axes[1]
    w_a, w_r = w
    ax.plot(tt, y_exp, linewidth=0.5, color="#888888", alpha=0.5,
            label="Experimental")
    ax.plot(tt, w_a * y_a, linewidth=0.8, color=COLOR_ANATASE, alpha=0.7,
            label=f"Anatase (w={w_a:.3f})")
    ax.plot(tt, w_r * y_r, linewidth=0.8, color=COLOR_RUTILE, alpha=0.7,
            label=f"Rutile  (w={w_r:.3f})")
    ax.plot(tt, y_recon, linewidth=0.9, color="#202020", linestyle="--",
            label=f"Reconstructed (R²={r2:.4f})")
    ax.set_ylabel("Normalised intensity")
    ax.set_title(f"NNLS (no offset) — A={a_n}%  R={r_n}%")
    ax.legend(fontsize=8, loc="upper right")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Panel 3: residual
    ax = axes[2]
    residual = y_exp - y_recon
    ax.plot(tt, residual, linewidth=0.4, color="#333333")
    ax.axhline(0, color="#999999", linewidth=0.5, linestyle="--")
    ax.set_ylabel("Residual")
    ax.set_xlabel("2θ / degree")
    ax.set_title("Residual (Exp − Reconstructed)")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    text = (
        f"Spurr-Myers:  A={a_s}%  R={r_s}%\n"
        f"NNLS+offset:  A={a_off}%  R={r_off}%  (R²={r2_off:.3f})\n"
        f"NNLS no-off:  A={a_n}%  R={r_n}%  (R²={r2:.3f})\n"
        f"cos-ratio:    A={a_cos}%  R={r_cos}%\n"
        f"cos(Exp,Ana)={cos_a:.4f}  cos(Exp,Rut)={cos_r:.4f}"
    )
    fig.text(0.02, 0.01, text, fontsize=9, family="monospace",
             bbox=dict(boxstyle="round", facecolor="white", alpha=0.9,
                       edgecolor="gray"))

    fig.tight_layout(rect=[0, 0.06, 1, 1])
    out_path = OUTPUT_DIR / f"inner_product_{name}.svg"
    fig.savefig(out_path, format="svg", dpi=300, bbox_inches="tight",
                transparent=True)
    plt.close(fig)
    print(f"  Decomposition plot → {out_path}")


if __name__ == "__main__":
    main()
