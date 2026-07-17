"""Simulate powder XRD patterns from CIF files in docs/refs/ using pymatgen.

Usage
-----
    cd xrd_pipeline
    uv run python tools/simulate_ref.py                     # batch all CIFs
    uv run python tools/simulate_ref.py <file.cif>          # single CIF
    uv run python tools/simulate_ref.py --peaks             # print peak tables
    uv run python tools/simulate_ref.py --export            # export .npz for pipeline

Instrument parameters
--------------------
    Source     Cu Kα (λ = 1.5406 Å)
    2θ range   10° – 80°
    Voltage    40.0 kV
    Current    10.0 mA
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

matplotlib.use("Agg")

from pymatgen.analysis.diffraction.xrd import XRDCalculator
from pymatgen.core import Structure

ROOT = Path(__file__).resolve().parents[1]
REFS_DIR = ROOT.parent / "docs" / "refs"
OUTPUT_DIR = ROOT / "output"

WAVELENGTH_LABEL = "CuKa"
WAVELENGTH_A = 1.5406
TWO_THETA_RANGE = (10.0, 80.0)
VOLTAGE_KV = 40.0
CURRENT_MA = 40.0
FWHM = 1.0

COLORS: dict[str, str] = {
    "TiO2-[tP6]": "#b2182b",
    "TiO2-[tI12]": "#2166ac",
}
PHASE_LABELS: dict[str, str] = {
    "TiO2-[tP6]": "Rutile (P4_2/mnm, SG 136)",
    "TiO2-[tI12]": "Anatase (I4_1/amd, SG 141)",
}


def collect_cif_files(args: list[str]) -> list[Path]:
    if args:
        paths = [Path(a) for a in args]
    else:
        paths = sorted(REFS_DIR.glob("*.cif"))
    for p in paths:
        if not p.exists():
            raise FileNotFoundError(str(p))
    return paths


def simulate_pattern(cif_path: Path):
    structure = Structure.from_file(str(cif_path))
    calc = XRDCalculator(wavelength=WAVELENGTH_LABEL, symprec=0.1)
    return calc.get_pattern(structure, two_theta_range=TWO_THETA_RANGE)


def _instrument_annotation() -> str:
    return (
        f"Cu Kα (λ = {WAVELENGTH_A} Å)  |  "
        f"{VOLTAGE_KV:.1f} kV  |  {CURRENT_MA:.1f} mA  |  "
        f"2θ: {TWO_THETA_RANGE[0]:.0f}° – {TWO_THETA_RANGE[1]:.0f}°"
    )


def _make_profile(pattern, fwhm: float = FWHM, step: float = 0.01):
    x_min, x_max = TWO_THETA_RANGE
    x = np.arange(x_min, x_max + step, step)
    y = np.zeros_like(x)
    sigma = fwhm / (2 * np.sqrt(2 * np.log(2)))

    for pos, intensity in zip(pattern.x, pattern.y):
        y += intensity * np.exp(-0.5 * ((x - pos) / sigma) ** 2)

    ymax = np.max(y)
    if ymax > 0:
        y /= ymax

    return x, y


def plot_individual(pattern, label: str, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(18, 6))

    x_profile, y_profile = _make_profile(pattern)
    ax.plot(x_profile, y_profile, linewidth=0.8, color=COLORS.get(label, "#202020"))

    ymax = np.max(pattern.y)
    profile_at_peak = np.interp(pattern.x, x_profile, y_profile)
    for two_theta, intensity, prof_y, hkl_list in zip(
        pattern.x, pattern.y, profile_at_peak, pattern.hkls
    ):
        if intensity < 0.03 * ymax:
            continue
        hkl_strs = ["".join(str(s) for s in entry["hkl"]) for entry in hkl_list]
        label_str = "/".join(hkl_strs)
        ax.annotate(
            f"({label_str})\n{two_theta:.2f}°",
            xy=(two_theta, prof_y),
            xytext=(0, 10),
            textcoords="offset points",
            fontsize=6,
            color=COLORS.get(label, "#202020"),
            ha="center",
            va="bottom",
            linespacing=1.2,
        )
        ax.scatter(
            [two_theta],
            [prof_y],
            marker="v",
            color=COLORS.get(label, "#202020"),
            edgecolors="white",
            linewidths=0.5,
            s=30,
            zorder=3,
        )

    ax.set_xlabel("2θ / degree", fontsize=12)
    ax.set_ylabel("Intensity (normalised)", fontsize=12)
    ax.set_title(
        f"Simulated XRD — {PHASE_LABELS.get(label, label)}",
        fontsize=14,
        fontweight="bold",
    )
    ax.text(
        0.99, 0.01, _instrument_annotation(),
        transform=ax.transAxes, fontsize=7, ha="right", va="bottom",
        color="gray",
    )
    ax.set_xlim(*TWO_THETA_RANGE)
    ax.tick_params(labelsize=10)

    fig.savefig(out_path, format="svg", dpi=300, bbox_inches="tight", transparent=True)
    plt.close(fig)
    print(f"  Saved: {out_path}")


def plot_combined(patterns: list[tuple], out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(18, 6))

    for label, pattern in patterns:
        x_profile, y_profile = _make_profile(pattern)
        ax.plot(
            x_profile, y_profile,
            linewidth=0.8,
            color=COLORS.get(label, "#202020"),
            label=PHASE_LABELS.get(label, label),
        )

    ax.set_xlabel("2θ / degree", fontsize=12)
    ax.set_ylabel("Intensity (normalised)", fontsize=12)
    ax.set_title("Simulated XRD — Rutile vs Anatase", fontsize=14, fontweight="bold")
    ax.text(
        0.99, 0.01, _instrument_annotation(),
        transform=ax.transAxes, fontsize=7, ha="right", va="bottom",
        color="gray",
    )
    ax.set_xlim(*TWO_THETA_RANGE)
    ax.tick_params(labelsize=10)
    ax.legend(fontsize=10, loc="upper right", framealpha=0.85)

    fig.savefig(out_path, format="svg", dpi=300, bbox_inches="tight", transparent=True)
    plt.close(fig)
    print(f"  Saved: {out_path}")


def print_peaks(pattern, label: str) -> list[tuple[str, float]]:
    print(f"\n  {label}  ({PHASE_LABELS.get(label, label)})")
    print(
        f"  {'hkl':>12s} | {'2θ':>8s} | {'Intensity':>10s} | "
        f"{'I/Imax':>8s} | {'d (Å)':>8s}"
    )
    print(f"  {'-' * 12}-+-{'-' * 8}-+-{'-' * 10}-+-{'-' * 8}-+-{'-' * 8}")
    ymax = np.max(pattern.y)
    peaks: list[tuple[str, float]] = []
    for two_theta, intensity, d, hkl_list in zip(
        pattern.x, pattern.y, pattern.d_hkls, pattern.hkls
    ):
        if intensity < 0.03 * ymax:
            continue
        hkl_strs = ["".join(str(s) for s in entry["hkl"]) for entry in hkl_list]
        label_str = "/".join(hkl_strs)
        print(
            f"  {label_str:>12s} | {two_theta:8.2f} | {intensity:10.2f} | "
            f"{intensity / ymax:7.4f} | {d:8.4f}"
        )
        peaks.append((label_str, float(two_theta)))
    return peaks


def export_peak_dict(peaks: list[tuple[str, float]], label: str) -> str:
    lines = [f"{label}_REF = {{"]
    for hkl, tt in peaks:
        lines.append(f'    "({hkl})": {tt:.2f},')
    lines.append("}")
    return "\n".join(lines)


def export_npz(pattern, label: str, out_dir: Path) -> Path:
    npz_path = out_dir / f"{label}_simulated.npz"
    np.savez_compressed(
        npz_path,
        two_theta=pattern.x.astype(np.float32),
        intensity=pattern.y.astype(np.float32),
        wavelength=np.float32(WAVELENGTH_A),
        voltage_kv=np.float32(VOLTAGE_KV),
        current_ma=np.float32(CURRENT_MA),
        two_theta_min=np.float32(TWO_THETA_RANGE[0]),
        two_theta_max=np.float32(TWO_THETA_RANGE[1]),
    )
    print(f"  Exported: {npz_path}")
    return npz_path


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    args = sys.argv[1:]

    show_peaks = "--peaks" in args
    export_data = "--export" in args
    file_args = [a for a in args if a not in ("--peaks", "--export")]
    cif_paths = collect_cif_files(file_args)

    if not cif_paths:
        print(f"No .cif files found in {REFS_DIR}")
        return

    print(f"Instrument: {_instrument_annotation()}\n")
    print(f"Found {len(cif_paths)} CIF file(s)")
    patterns: list[tuple[str, object]] = []

    for cif_path in cif_paths:
        label = cif_path.stem
        print(f"\nProcessing: {label}")

        pattern = simulate_pattern(cif_path)
        patterns.append((label, pattern))

        out_individual = OUTPUT_DIR / f"simulated_{label}.svg"
        plot_individual(pattern, label, out_individual)

        if export_data:
            export_npz(pattern, label, OUTPUT_DIR)

        if show_peaks:
            peaks = print_peaks(pattern, label)
            print(f"\n  # Python dict form:")
            print(export_peak_dict(peaks, label))

    if len(patterns) > 1:
        out_combined = OUTPUT_DIR / "simulated_comparison.svg"
        plot_combined(patterns, out_combined)

    print(f"\nDone. Output saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
