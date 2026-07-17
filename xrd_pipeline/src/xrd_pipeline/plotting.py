"""XRD figure generation — one sample per figure, plus diagnostic mode."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

from .config import (
    ANATASE_REF, RUTILE_REF, CONFIG,
    COLOR_ANATASE, COLOR_RUTILE, COLOR_PATTERN, COLOR_BASELINE,
    SIM_VOLTAGE_KV, SIM_CURRENT_MA, SIM_WAVELENGTH_A,
    SIM_TWO_THETA_RANGE,
    SCHERRER_K, WAVELENGTH_NM, INSTRUMENTAL_FWHM_DEG,
    SCHERRER_MIN_ISOLATION_DEG,
)
from .processing import (
    process_data, find_local_peak, estimate_phase_composition,
    estimate_phase_composition_nnls,
    measure_fwhm, scherrer_size, _interp_crossing,
)
from .simulation import get_anatase_peaks, get_rutile_peaks


def _instrument_str() -> str:
    return (
        f"Cu Kα (λ={SIM_WAVELENGTH_A:.4f} Å), "
        f"{SIM_VOLTAGE_KV:.0f} kV, {SIM_CURRENT_MA:.0f} mA, "
        f"{SIM_TWO_THETA_RANGE[0]:.0f}°–{SIM_TWO_THETA_RANGE[1]:.0f}°"
    )


def _draw_sim_panel(
    ax,
    tt_anatase: np.ndarray, ya: np.ndarray,
    tt_rutile: np.ndarray, yr: np.ndarray,
    *,
    with_title: bool = True,
) -> None:
    """Draw simulated reference stick patterns (normalised to 100)."""
    ya_norm = ya / np.max(ya) * 100.0 if np.max(ya) > 0 else ya
    yr_norm = yr / np.max(yr) * 100.0 if np.max(yr) > 0 else yr

    peaks: list[tuple[float, float, str]] = []
    for tt, intens in zip(tt_anatase, ya_norm):
        peaks.append((float(tt), float(intens), "Anatase"))
    for tt, intens in zip(tt_rutile, yr_norm):
        peaks.append((float(tt), float(intens), "Rutile"))
    peaks.sort(key=lambda x: x[0])

    deduped: list[tuple[float, float, str]] = []
    for i, (tt, iv, ph) in enumerate(peaks):
        if deduped and abs(tt - deduped[-1][0]) < 0.08:
            continue
        deduped.append((tt, iv, ph))
    peaks = deduped

    for tt, iv, phase in peaks:
        c = COLOR_ANATASE if phase == "Anatase" else COLOR_RUTILE
        ax.plot([tt, tt], [0, -iv],
                linewidth=1.2, color=c, alpha=0.70, zorder=2,
                solid_capstyle="butt", clip_on=False)

    ax.set_xlim(*SIM_TWO_THETA_RANGE)
    ax.set_ylim(-112, 0)
    if with_title:
        ax.set_title(f"Simulated reference — {_instrument_str()}",
                     fontsize=CONFIG["font_title"] - 2)
    ax.set_ylabel("")
    ax.tick_params(left=False, labelleft=False)

    ax.spines["right"].set_visible(False)

    legend_sim = [
        Line2D([0], [0], color=COLOR_ANATASE, linewidth=2, alpha=0.75,
               label="Anatase sim"),
        Line2D([0], [0], color=COLOR_RUTILE, linewidth=2, alpha=0.75,
               label="Rutile sim"),
    ]
    ax.legend(handles=legend_sim, loc="lower right",
              fontsize=CONFIG["font_legend"], framealpha=0.85)


def plot_one_sample(
    two_theta: np.ndarray,
    intensity: np.ndarray,
    sample_label: str,
    out_dir: Path,
) -> None:
    """Create and save one figure for a single XRD pattern."""
    print(f"  Processing: {sample_label}")

    smoothed, baseline = process_data(intensity)
    anat_pct, rut_pct, comp_status = estimate_phase_composition(two_theta, smoothed)
    y_max = float(np.max(smoothed))

    tt_anatase, sim_anatase = get_anatase_peaks()
    tt_rutile, sim_rutile = get_rutile_peaks()

    a_nnls, r_nnls, r2_nnls, nnls_status = estimate_phase_composition_nnls(
        two_theta, smoothed, tt_anatase, sim_anatase, tt_rutile, sim_rutile,
    )

    fig, (ax_exp, ax_sim) = plt.subplots(
        2, 1, figsize=(CONFIG["figsize"][0], CONFIG["figsize"][1] * 1.3),
        gridspec_kw={"hspace": 0.0, "height_ratios": [1.0, 0.35]},
        sharex=True,
    )

    # ── top panel: experimental ──────────────────────────────────────────

    ax_exp.plot(two_theta, baseline, linewidth=0.8, color=COLOR_BASELINE,
                linestyle="--", alpha=0.50, zorder=0)
    ax_exp.plot(two_theta, smoothed, linewidth=0.7, color=COLOR_PATTERN, zorder=1)

    peaks_by_ref: list[tuple[float, float, str, str]] = []
    for hkl, ref_tt in ANATASE_REF.items():
        iv = float(np.interp(ref_tt, two_theta, smoothed))
        peaks_by_ref.append((ref_tt, iv, hkl, "Anatase"))
    for hkl, ref_tt in RUTILE_REF.items():
        iv = float(np.interp(ref_tt, two_theta, smoothed))
        peaks_by_ref.append((ref_tt, iv, hkl, "Rutile"))
    peaks_by_ref.sort(key=lambda x: x[0])

    DEDUP = CONFIG["dedup_tolerance"]
    deduped: list[tuple[float, float, str, str]] = []
    for pp in peaks_by_ref:
        if deduped and abs(pp[0] - deduped[-1][0]) < DEDUP:
            prev = deduped[-1]
            merged_hkl = prev[2] + "/" + pp[2]
            if pp[1] > prev[1]:
                deduped[-1] = (pp[0], pp[1], merged_hkl, pp[3])
            else:
                deduped[-1] = (prev[0], prev[1], merged_hkl, prev[3])
        else:
            deduped.append(pp)
    peaks_by_ref = deduped

    GAP_DEG = 1.5
    HALF_WINDOW = 1.25
    NORM_OFF = 8
    HIGH_OFF = 16
    stagger_high = False
    for i, (ref_tt, iv, hkl, phase) in enumerate(peaks_by_ref):
        c = COLOR_ANATASE if phase == "Anatase" else COLOR_RUTILE

        mask = (two_theta >= ref_tt - HALF_WINDOW) & (two_theta <= ref_tt + HALF_WINDOW)
        if mask.any():
            local_max = float(np.max(smoothed[mask]))
        else:
            local_max = iv
        anchor_y = local_max + local_max * 0.03

        too_close = False
        if i > 0 and (ref_tt - peaks_by_ref[i - 1][0]) < GAP_DEG:
            too_close = True
        if i < len(peaks_by_ref) - 1 and (peaks_by_ref[i + 1][0] - ref_tt) < GAP_DEG:
            too_close = True

        if too_close:
            stagger_high = not stagger_high
            yoff = HIGH_OFF if stagger_high else NORM_OFF
        else:
            stagger_high = False
            yoff = NORM_OFF

        ax_exp.scatter(
            [ref_tt], [anchor_y], marker="v", color=c,
            edgecolors="white", linewidths=0.5, s=40, zorder=3, clip_on=False,
        )
        ax_exp.annotate(
            f"{hkl} {ref_tt:.2f}°",
            xy=(ref_tt, anchor_y), xytext=(0, yoff), textcoords="offset points",
            fontsize=CONFIG["font_peak_label"], color=c,
            ha="center", va="bottom", rotation=90,
        )

    ax_exp.set_ylim(-y_max * 0.04, y_max * 1.25)
    ax_exp.set_xlim(two_theta[0], two_theta[-1])
    ax_exp.set_ylabel("Intensity / counts", fontsize=CONFIG["font_axis_label"])
    ax_exp.set_title(sample_label, fontsize=CONFIG["font_title"], fontweight="bold")
    ax_exp.tick_params(labelsize=CONFIG["font_tick"])
    ax_exp.spines["bottom"].set_visible(False)
    ax_exp.spines["top"].set_visible(False)
    ax_exp.spines["right"].set_visible(False)

    # ── Scherrer size for characteristic peaks ────────────────────────────

    verified_tts: list[float] = []
    for ref_tt_peak in list(ANATASE_REF.values()) + list(RUTILE_REF.values()):
        result = find_local_peak(ref_tt_peak, two_theta, smoothed)
        if result is not None:
            verified_tts.append(result[0])

    scherrer_key_peaks = {
        "Anatase": ("(101)", ANATASE_REF["(101)"]),
        "Rutile": ("(110)", RUTILE_REF["(110)"]),
    }
    size_info: list[str] = []
    for phase, (hkl, ref_tt) in scherrer_key_peaks.items():
        result = find_local_peak(ref_tt, two_theta, smoothed)
        if result is None:
            continue
        actual_tt, iv = result
        neighbors = [t for t in verified_tts if abs(t - actual_tt) > 1e-6]
        fwhm = measure_fwhm(actual_tt, two_theta, smoothed, neighbor_tts=neighbors)
        if fwhm is None:
            continue
        size = scherrer_size(fwhm, actual_tt)
        size_info.append(f"{phase} {hkl} ({actual_tt:.2f}°)  "
                         f"FWHM={fwhm:.4f}°  D={size:.1f} nm")

        c = COLOR_ANATASE if phase == "Anatase" else COLOR_RUTILE
        mask = (two_theta >= actual_tt - HALF_WINDOW) & (two_theta <= actual_tt + HALF_WINDOW)
        anchor_y = float(np.max(smoothed[mask])) if mask.any() else iv
        ax_exp.scatter(
            [actual_tt], [anchor_y + anchor_y * 0.03],
            marker="s", color=c, edgecolors="white",
            linewidths=0.5, s=30, zorder=4, clip_on=False,
        )
        ax_exp.annotate(
            f"D={size:.0f} nm",
            xy=(actual_tt, anchor_y + anchor_y * 0.03),
            xytext=(20, 0), textcoords="offset points",
            fontsize=CONFIG["font_peak_label"], color=c,
            ha="left", va="center",
        )

    if size_info:
        print(f"    Scherrer size:")
        for line in size_info:
            print(f"      {line}")
    else:
        print(f"    Scherrer size: no characteristic peaks measured")

    if nnls_status:
        print(f"    NNLS: {nnls_status}")
    else:
        print(f"    NNLS: Anatase {a_nnls}%  Rutile {r_nnls}%  R^2={r2_nnls:.4f}")

    legend_exp = [
        Line2D([0], [0], color=COLOR_BASELINE, linewidth=1.5,
               linestyle="--", label="Baseline"),
    ]
    ax_exp.legend(handles=legend_exp, loc="upper right",
                  fontsize=CONFIG["font_legend"], framealpha=0.85)

    if comp_status:
        comp_text = comp_status
    else:
        comp_text = (
            f"Spurr-Myers:  Anatase {anat_pct}%  Rutile {rut_pct}%\n"
            f"NNLS (R^2={r2_nnls:.3f}):  Anatase {a_nnls}%  Rutile {r_nnls}%"
        )
    ax_exp.text(
        0.02, 0.96, comp_text,
        transform=ax_exp.transAxes, fontsize=CONFIG["font_composition"], va="top",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.75,
                  edgecolor="gray"),
    )

    # ── bottom panel: simulated reference ─────────────────────────────────

    _draw_sim_panel(ax_sim, tt_anatase, sim_anatase, tt_rutile, sim_rutile,
                    with_title=False)

    ax_sim.spines["bottom"].set_visible(False)
    ax_sim.xaxis.set_ticks_position("top")
    ax_sim.xaxis.set_label_position("top")
    ax_sim.set_xlabel("2θ / degree", fontsize=CONFIG["font_axis_label"])

    for fmt in ("svg", "pdf"):
        out_path = out_dir / f"{sample_label}.{fmt}"
        fig.savefig(out_path, format=fmt, dpi=300, bbox_inches="tight",
                    transparent=True)
        print(f"    Saved: {out_path}")
    plt.close(fig)


def diagnose_peaks(
    two_theta: np.ndarray,
    intensity: np.ndarray,
    sample_label: str,
    out_dir: Path,
) -> None:
    """Diagnostic peak report + multi-panel figure."""
    smoothed, baseline = process_data(intensity)
    y_max = float(np.max(smoothed))

    verified: list[tuple[str, float, float, float, str]] = []
    for hkl, tt in ANATASE_REF.items():
        result = find_local_peak(tt, two_theta, smoothed)
        if result is not None:
            actual_tt, iv = result
            verified.append((hkl, tt, actual_tt, iv, "Anatase"))
    for hkl, tt in RUTILE_REF.items():
        result = find_local_peak(tt, two_theta, smoothed)
        if result is not None:
            actual_tt, iv = result
            verified.append((hkl, tt, actual_tt, iv, "Rutile"))
    verified.sort(key=lambda r: r[1])

    all_tts = [v[2] for v in verified]

    ref_rows: list[tuple[str, float, float, float, str, float, float]] = []
    for hkl, ref_tt, actual_tt, iv, phase in verified:
        neighbors = [t for t in all_tts if abs(t - actual_tt) > 1e-6]
        fwhm = measure_fwhm(actual_tt, two_theta, smoothed, neighbor_tts=neighbors)
        size = scherrer_size(fwhm, actual_tt) if fwhm is not None else 0.0
        ref_rows.append((hkl, ref_tt, actual_tt, iv, phase, fwhm or 0.0, size))

    n_found = len(ref_rows)
    n_total = len(ANATASE_REF) + len(RUTILE_REF)
    print(f"\n{'=' * 78}")
    print(f"  Reference Peak Report: {sample_label}")
    print(f"{'=' * 78}")
    print(f"  Config:  sg_window={CONFIG['sg_window']}"
          f"  baseline_lam={CONFIG['baseline_lam']:.0e}"
          f"  baseline_p={CONFIG['baseline_p']}"
          f"  search_window={CONFIG['local_search_window']}°"
          f"  base_window={CONFIG['local_base_window']}°"
          f"  prominence_min={CONFIG['local_prominence_min']} (local)")
    print(f"  Scherrer: K={SCHERRER_K}  λ={WAVELENGTH_NM:.5f} nm"
          f"  instr FWHM={INSTRUMENTAL_FWHM_DEG:.3f}°"
          f"  min isolation={SCHERRER_MIN_ISOLATION_DEG}°")
    print(f"  Raw data: {len(intensity)} points, "
          f"2θ range [{two_theta[0]:.2f}°, {two_theta[-1]:.2f}°]")
    print(f"  Peaks verified: {n_found} / {n_total} ref. positions")
    print()
    hdr = (f"  {'hkl':>10s} | {'2θ ref':>8s} | {'2θ found':>8s} | "
           f"{'Intensity':>10s} | {'I/max':>8s} | {'FWHM':>8s} | "
           f"{'Size':>8s} | {'Phase':>8s}")
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for hkl, ref_tt, actual_tt, iv, phase, fwhm, size in ref_rows:
        fwhm_str = f"{fwhm:.4f}°" if fwhm > 0 else "  N/A  "
        size_str = f"{size:.1f}nm" if size > 0 else "  N/A  "
        print(f"  {hkl:>10s} | {ref_tt:8.2f} | {actual_tt:8.2f} | "
              f"{iv:10.1f} | {iv / y_max:7.4f} | {fwhm_str:>8s} | "
              f"{size_str:>8s} | {phase:>8s}")
    print()

    size_lines: list[str] = []
    for hkl, ref_tt, actual_tt, iv, phase, fwhm, size in ref_rows:
        if size <= 0:
            continue
        size_lines.append(f"    {phase} {hkl} ({actual_tt:.2f}°): "
                          f"FWHM={fwhm:.4f}°  D={size:.1f} nm")
    if size_lines:
        print("  Crystallite size (Scherrer):")
        for line in size_lines:
            print(line)
        print()
    else:
        print("  Crystallite size: no measurable peaks\n")

    tt_anatase, sim_anatase = get_anatase_peaks()
    tt_rutile, sim_rutile = get_rutile_peaks()

    fig_h = CONFIG["figsize"][1] * 1.8
    fig, (ax_a, ax_c, ax_sim) = plt.subplots(
        3, 1, figsize=(CONFIG["figsize"][0], fig_h),
        gridspec_kw={"hspace": 0.25, "height_ratios": [1.0, 1.0, 0.35]},
        sharex=True,
    )

    # ── panel (a): raw + baseline + corrected ────────────────────────────

    ax_a.plot(two_theta, intensity, linewidth=0.4, color="#cccccc",
              label="Raw data")
    ax_a.plot(two_theta, baseline, linewidth=0.8, color=COLOR_BASELINE,
              linestyle="--", alpha=0.50, label="ALS baseline")
    ax_a.plot(two_theta, smoothed, linewidth=0.8, color=COLOR_PATTERN,
              label="Corrected")
    ax_a.set_xlim(two_theta[0], two_theta[-1])
    ax_a.set_ylabel("Intensity", fontsize=CONFIG["font_axis_label"])
    ax_a.set_title(f"(a) Raw + Baseline + Corrected — {sample_label}",
                   fontsize=CONFIG["font_title"], fontweight="bold")
    ax_a.legend(fontsize=CONFIG["font_legend"], framealpha=0.85)
    ax_a.tick_params(labelsize=CONFIG["font_tick"])
    ax_a.spines["bottom"].set_visible(False)
    ax_a.spines["top"].set_visible(False)
    ax_a.spines["right"].set_visible(False)

    # ── panel (b): corrected with verified peaks ──────────────────────────

    ax_c.plot(two_theta, smoothed, linewidth=0.7, color=COLOR_PATTERN, zorder=1)

    stagger_high = False
    GAP_DEG = 1.5
    HIGH_OFF, NORM_OFF = 13, 7
    for i, (hkl, ref_tt, actual_tt, iv, phase, fwhm, size) in enumerate(ref_rows):
        c = COLOR_ANATASE if phase == "Anatase" else COLOR_RUTILE
        too_close = False
        if i > 0 and (actual_tt - ref_rows[i - 1][2]) < GAP_DEG:
            too_close = True
        if i < len(ref_rows) - 1 and (ref_rows[i + 1][2] - actual_tt) < GAP_DEG:
            too_close = True
        if too_close:
            stagger_high = not stagger_high
            yoff = HIGH_OFF if stagger_high else NORM_OFF
        else:
            stagger_high = False
            yoff = NORM_OFF

        label = f"{hkl}\n{actual_tt:.2f}°"
        if size > 0:
            label += f"\nD={size:.0f}nm"

        ax_c.scatter([actual_tt], [iv], s=36, marker="v",
                     color=c, edgecolors="white", linewidths=0.4, zorder=5)
        ax_c.annotate(
            label, xy=(actual_tt, iv),
            xytext=(0, yoff), textcoords="offset points",
            fontsize=CONFIG["font_peak_label"],
            color=c, ha="center", va="bottom", linespacing=1.2,
        )

    ax_c.set_xlim(two_theta[0], two_theta[-1])
    ax_c.set_ylim(-y_max * 0.04, y_max * 1.25)
    ax_c.set_ylabel("Intensity / counts", fontsize=CONFIG["font_axis_label"])
    ax_c.set_title(
        f"(b) Verified ref. peaks on corrected data  "
        f"({n_found}/{n_total} confirmed)",
        fontsize=CONFIG["font_title"] - 1,
    )
    ax_c.tick_params(labelsize=CONFIG["font_tick"])

    legend_c = [
        Line2D([0], [0], marker="v", color="w",
               markerfacecolor=COLOR_ANATASE, markersize=8, label="Anatase"),
        Line2D([0], [0], marker="v", color="w",
               markerfacecolor=COLOR_RUTILE, markersize=8, label="Rutile"),
    ]
    ax_c.legend(handles=legend_c, loc="upper right",
                fontsize=CONFIG["font_legend"], framealpha=0.85)
    ax_c.spines["bottom"].set_visible(False)
    ax_c.spines["top"].set_visible(False)
    ax_c.spines["right"].set_visible(False)

    # ── panel (c): simulated reference ────────────────────────────────────

    _draw_sim_panel(ax_sim, tt_anatase, sim_anatase, tt_rutile, sim_rutile,
                    with_title=True)

    ax_sim.spines["bottom"].set_visible(False)
    ax_sim.xaxis.set_ticks_position("top")
    ax_sim.xaxis.set_label_position("top")
    ax_sim.set_xlabel("2θ / degree", fontsize=CONFIG["font_axis_label"])

    for fmt in ("svg", "pdf"):
        out_path = out_dir / f"test_{sample_label}.{fmt}"
        fig.savefig(out_path, format=fmt, dpi=300, bbox_inches="tight",
                    transparent=True)
        print(f"  Diagnostic figure saved: {out_path}")
    plt.close(fig)


def plot_fwhm_debug(
    ref_tt: float,
    two_theta: np.ndarray,
    smoothed: np.ndarray,
    phase: str,
    hkl: str,
    out_dir: Path,
) -> None:
    """Generate a zoomed-in debug figure showing the FWHM measurement.

    Displays the corrected data segment around the peak, the half-maximum
    line, the left/right interpolated crossing points, and the derived
    Scherrer size.
    """
    import math

    result = find_local_peak(ref_tt, two_theta, smoothed)
    if result is None:
        print(f"    [FWHM debug] {phase} {hkl}: peak not found, skipping")
        return
    actual_tt, _ = result

    search_window = CONFIG["local_base_window"]
    lo, hi = actual_tt - search_window, actual_tt + search_window
    mask = (two_theta >= lo) & (two_theta <= hi)
    if mask.sum() < 5:
        print(f"    [FWHM debug] {phase} {hkl}: too few data points in window")
        return
    indices = np.flatnonzero(mask)
    start, end = int(indices[0]), int(indices[-1])

    segment = smoothed[start:end + 1]
    tt_seg = two_theta[start:end + 1]

    i_peak = int(np.argmax(segment))
    if i_peak == 0 or i_peak == end - start:
        print(f"    [FWHM debug] {phase} {hkl}: peak at window boundary")
        return
    peak_h = float(segment[i_peak])
    peak_tt_actual = float(tt_seg[i_peak])
    half_h = peak_h / 2.0

    left_tt = _interp_crossing(tt_seg, segment, half_h, i_peak, direction=-1)
    right_tt = _interp_crossing(tt_seg, segment, half_h, i_peak, direction=+1)
    if left_tt is None or right_tt is None:
        print(f"    [FWHM debug] {phase} {hkl}: half-max crossings not found")
        return

    fwhm = right_tt - left_tt
    size = scherrer_size(fwhm, peak_tt_actual)
    c = COLOR_ANATASE if phase == "Anatase" else COLOR_RUTILE

    fig, ax = plt.subplots(figsize=(10, 5))

    ax.plot(tt_seg, segment, linewidth=1.2, color=c,
            label=f"{phase} {hkl} (corrected)")

    ax.scatter([peak_tt_actual], [peak_h], marker="v", color=c, s=60,
               edgecolors="white", linewidths=1.0, zorder=5)
    ax.annotate(
        f"peak: {peak_tt_actual:.3f}°\nh={peak_h:.1f}",
        xy=(peak_tt_actual, peak_h), xytext=(0, 15),
        textcoords="offset points", fontsize=8, color=c,
        ha="center", va="bottom",
    )

    ax.axhline(y=half_h, color="gray", linestyle="--", linewidth=0.8,
               label=f"half-max = {half_h:.1f}")

    left_y = float(np.interp(left_tt, tt_seg, segment))
    ax.scatter([left_tt], [left_y], marker=">", color="orange", s=60,
               edgecolors="white", linewidths=0.8, zorder=5)
    ax.annotate(
        f"{left_tt:.3f}°",
        xy=(left_tt, left_y), xytext=(0, -12),
        textcoords="offset points", fontsize=7, color="orange",
        ha="center", va="top",
    )

    right_y = float(np.interp(right_tt, tt_seg, segment))
    ax.scatter([right_tt], [right_y], marker="<", color="orange", s=60,
               edgecolors="white", linewidths=0.8, zorder=5)
    ax.annotate(
        f"{right_tt:.3f}°",
        xy=(right_tt, right_y), xytext=(0, -12),
        textcoords="offset points", fontsize=7, color="orange",
        ha="center", va="top",
    )

    mid_tt = (left_tt + right_tt) / 2.0
    ax.annotate(
        "", xy=(left_tt, half_h), xytext=(right_tt, half_h),
        arrowprops=dict(arrowstyle="<->", color="red", linewidth=1.5,
                        shrinkA=0, shrinkB=0),
    )
    ax.annotate(
        f"FWHM = {fwhm:.4f}°\nD = {size:.1f} nm",
        xy=(mid_tt, half_h), xytext=(0, 18),
        textcoords="offset points", fontsize=9, color="red",
        ha="center", va="bottom",
        bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.85,
                  edgecolor="red"),
    )

    beta_deg = math.sqrt(max(0.0, fwhm**2 - INSTRUMENTAL_FWHM_DEG**2))
    beta_rad = math.radians(beta_deg)
    theta_rad = math.radians(peak_tt_actual / 2.0)
    cos_theta = math.cos(theta_rad)
    info_text = (
        f"β = √(FWHM² − β_inst²) = √({fwhm:.4f}² − {INSTRUMENTAL_FWHM_DEG:.3f}²) = {beta_deg:.4f}°\n"
        f"D = K·λ / (β_rad · cos θ) = {SCHERRER_K} × {WAVELENGTH_NM:.5f} / "
        f"({beta_rad:.6f} × {cos_theta:.4f}) = {size:.1f} nm"
    )
    ax.text(
        0.98, 0.02, info_text,
        transform=ax.transAxes, fontsize=6, va="bottom", ha="right",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.85,
                  edgecolor="gray"),
    )

    ax.set_xlabel("2θ / degree", fontsize=CONFIG["font_axis_label"])
    ax.set_ylabel("Intensity (corrected)", fontsize=CONFIG["font_axis_label"])
    ax.set_title(
        f"FWHM Debug — {phase} {hkl}  "
        f"(Scherrer: K={SCHERRER_K}, λ={WAVELENGTH_NM:.5f} nm, "
        f"β_inst={INSTRUMENTAL_FWHM_DEG:.3f}°)",
        fontsize=CONFIG["font_title"] - 2, fontweight="bold",
    )
    ax.legend(fontsize=CONFIG["font_legend"], framealpha=0.85)
    ax.tick_params(labelsize=CONFIG["font_tick"])

    safe_hkl = hkl.replace("(", "").replace(")", "").replace("/", "_")
    for fmt in ("svg", "pdf"):
        out_path = out_dir / f"fwhm_debug_{phase}_{safe_hkl}.{fmt}"
        fig.savefig(out_path, format=fmt, dpi=300, bbox_inches="tight",
                    transparent=True)
        print(f"    FWHM debug saved: {out_path}")
    plt.close(fig)
