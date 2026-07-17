"""Manual-annotation pipeline for 14.jpg and 16.jpg.

Replaces the automatic blue-mask homography detection with manual line annotation
of the display bezel edges.  Each image is processed independently (not as
replicates); a combined histogram and cumulative ECD plot are produced.

Usage
-----
    cd sem_pipeline && uv run python tools/manual_pipeline_14_16.py
"""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from sem_analysis.annotator import annotate_image
from sem_analysis.filter import classify_particles
from sem_analysis.homography import apply_homography
from sem_analysis.scale_bar import detect
from sem_analysis.segment import segment

from sem_pipeline.annotate import annotate_particles
from sem_pipeline.config import DATA_DIR, GROUP_COLORS, OUTPUT_SUBDIRS
from sem_pipeline.crop import crop_sem_region
from sem_pipeline.feret import compute_feret_min_all
from sem_pipeline.histogram import save_combined_histogram, save_histogram

IMAGES = ["14.jpg", "16.jpg"]
OUTPUT_DIR = OUTPUT_SUBDIRS["corrected"].parent


def _ensure_dirs() -> dict[str, Path]:
    dirs = OUTPUT_SUBDIRS.copy()
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs


def _resolve_scale(name: str, rectified: np.ndarray) -> float:
    bar = detect(rectified)
    if bar and bar.get("bar_px", 0) > 0:
        phys = input(
            f"  [{name}] Scale bar detected: {bar['bar_px']:.0f} px. "
            f"Enter physical length in nm: "
        )
        try:
            return float(phys) / bar["bar_px"]
        except ValueError:
            pass

    manual = input(f"  [{name}] Scale bar not detected. Enter nm/px manually: ")
    try:
        return float(manual)
    except ValueError:
        return 0.0


def process_one(
    fpath: Path,
    dirs: dict[str, Path],
    results: dict,
) -> None:
    name = fpath.stem
    print(f"\n{'=' * 60}")
    print(f"  {fpath.name}")
    print(f"{'=' * 60}")

    img = cv2.imread(str(fpath))
    if img is None:
        print("  ERROR: cannot read")
        return

    # ------------------------------------------------------------------
    # 1) manual line annotation
    # ------------------------------------------------------------------
    print("  → draw 4 lines along the display bezel edges (any order)")
    print("    2 clicks per line  |  RIGHT = undo  |  R = reset  |  S = save")
    corners = annotate_image(img)
    if corners is None:
        print("  Cancelled by user.")
        return

    labels = ("TL", "TR", "BR", "BL")
    print("  Corners:")
    for i, (cx, cy) in enumerate(corners):
        print(f"    {labels[i]}: ({cx:.1f}, {cy:.1f})")

    # ------------------------------------------------------------------
    # 2) homography
    # ------------------------------------------------------------------
    c_arr = np.array(corners, dtype=np.float32)
    rectified = apply_homography(img, c_arr, target_width=1920, trust_order=True)
    print(f"  homography: {rectified.shape[1]}x{rectified.shape[0]}")

    cv2.imwrite(str(dirs["corrected"] / f"{name}_corrected.jpg"), rectified)

    jp = dirs["corrected"] / f"{name}_corners.json"
    jp.write_text(
        json.dumps(
            {
                "image": str(fpath.name),
                "src_resolution": [img.shape[1], img.shape[0]],
                "corners": {
                    labels[i]: [round(cx, 2), round(cy, 2)]
                    for i, (cx, cy) in enumerate(corners)
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    # ------------------------------------------------------------------
    # 3) scale bar
    # ------------------------------------------------------------------
    nm_per_px = _resolve_scale(name, rectified)
    if nm_per_px <= 0:
        nm_per_px = 0.0
    print(f"  scale: {nm_per_px:.4f} nm/px")

    # ------------------------------------------------------------------
    # 4) crop → segment → classify → annotate → histogram → CSV
    # ------------------------------------------------------------------
    crop = crop_sem_region(rectified)
    print(f"  crop: {crop.shape[1]}x{crop.shape[0]}")

    labels_seg, props = segment(crop)
    df = pd.DataFrame(props)
    n = len(df)
    feret = df["feret_diameter_max"].values
    feret_nm = feret * nm_per_px if nm_per_px else feret
    print(f"  particles: {n}")

    if n == 0:
        return

    feret_min_vals = compute_feret_min_all(labels_seg, df["label"].values)

    single_mask = classify_particles(
        df["area"].values,
        df["perimeter"].values,
        df["solidity"].values,
        df["extent"].values,
        feret,
        feret_min_vals,
    )
    n_single = int(single_mask.sum())
    n_aggl = n - n_single
    print(f"  single: {n_single}  agglomerate: {n_aggl}")

    vis, feret_lines = annotate_particles(
        crop,
        labels_seg,
        df["label"].values,
        df["feret_diameter_max"].values,
        single_mask,
        nm_per_px,
    )
    cv2.imwrite(str(dirs["annotated"] / f"{name}_annotated.jpg"), vis)

    if nm_per_px:
        df["ecd_nm"] = df["ecd"] * nm_per_px
        df["feret_nm"] = df["feret_diameter_max"] * nm_per_px
        df["area_nm2"] = df["area"] * nm_per_px * nm_per_px

    if len(feret_lines) == n:
        fl = np.array(feret_lines)
        df["feret_x1"] = fl[:, 0]
        df["feret_y1"] = fl[:, 1]
        df["feret_x2"] = fl[:, 2]
        df["feret_y2"] = fl[:, 3]

    df["single"] = single_mask.astype(int)
    df.to_csv(dirs["data"] / f"{name}_particles.csv", index=False)

    size_data = feret_nm[single_mask] if n_single > 0 else feret_nm
    unit = "nm" if nm_per_px else "px"

    save_histogram(
        size_data,
        name,
        str(dirs["histograms"] / f"{name}_histogram.svg"),
        unit=unit,
    )

    feret_single = feret_nm[single_mask] if n_single > 0 else feret_nm
    print(
        f"  Feret: mean={feret_single.mean():.1f} "
        f"median={np.median(feret_single):.1f} "
        f"min={feret_single.min():.1f} "
        f"max={feret_single.max():.1f} {unit}"
    )
    print(f"  saved: corrected, annotated, CSV, histogram")

    results["summary_rows"].append(
        {
            "image": name,
            "n": n_single,
            "n_total": n,
            "mean_nm": float(feret_single.mean()),
            "median_nm": float(np.median(feret_single)),
            "std_nm": float(feret_single.std()),
            "min_nm": float(feret_single.min()),
            "max_nm": float(feret_single.max()),
            "scale_nm_px": nm_per_px,
        }
    )
    results["all_sizes"][name] = feret_single


# ---------------------------------------------------------------------------
# combined outputs
# ---------------------------------------------------------------------------

def _write_summary(results: dict, dirs: dict[str, Path]) -> None:
    rows = results.get("summary_rows", [])
    if not rows:
        return
    summary_df = pd.DataFrame(rows)
    summary_df.to_csv(dirs["data"] / "summary_14_16.csv", index=False)
    print("\n" + "=" * 60)
    print("PER-IMAGE SUMMARY (Feret diam.)")
    print("=" * 60)
    for r in rows:
        print(
            f"  {r['image']}: n={r['n']:4d}  mean={r['mean_nm']:6.0f}  "
            f"median={r['median_nm']:6.0f}  std={r['std_nm']:5.0f} nm"
        )


def _resolve_combined_unit(results: dict) -> str:
    rows = results.get("summary_rows", [])
    for r in rows:
        if r.get("scale_nm_px", 0) <= 0:
            return "px"
    return "nm"


def _write_combined_histogram(results: dict, dirs: dict[str, Path]) -> None:
    all_sizes = results.get("all_sizes", {})
    if len(all_sizes) < 2:
        return

    group_vals = []
    group_labels = []
    for name, arr in all_sizes.items():
        group_vals.append(arr)
        group_labels.append(f"{name} (n={len(arr)})")

    unit = _resolve_combined_unit(results)
    save_combined_histogram(
        group_vals,
        group_labels,
        GROUP_COLORS,
        str(dirs["histograms"] / "combined_histogram_14_16.svg"),
        unit=unit,
    )
    all_vals = np.concatenate(group_vals)
    print(f"\nCombined histogram saved (n={len(all_vals)})")


def _write_cumulative_ecd(results: dict, dirs: dict[str, Path]) -> None:
    all_sizes = results.get("all_sizes", {})
    if not all_sizes:
        return

    combined = np.concatenate(list(all_sizes.values()))

    fig, ax = plt.subplots(figsize=(10, 6))

    for (k, v), c in zip(all_sizes.items(), ["#2166ac", "#b2182b"]):
        vs = np.sort(v)
        cy = np.arange(1, len(vs) + 1) / len(vs) * 100.0
        ax.plot(vs, cy, color=c, lw=1.5, alpha=0.7, label=f"{k} (n={len(v)})")

    cs = np.sort(combined)
    cc = np.arange(1, len(cs) + 1) / len(cs) * 100.0
    ax.plot(cs, cc, "k-", lw=2.5, label=f"Combined (n={len(combined)})")

    d10 = float(np.percentile(combined, 10))
    d50 = float(np.percentile(combined, 50))
    d90 = float(np.percentile(combined, 90))
    for val, lbl in [(d10, "D10"), (d50, "D50"), (d90, "D90")]:
        ax.axvline(val, color="gray", ls="--", alpha=0.5)
        ax.text(
            val, 52, f"  {lbl}={val:.0f}", fontsize=8,
            color="gray", rotation=90, va="bottom",
        )

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
    ax.set_title("Cumulative ECD Distribution — 14 & 16")
    ax.legend(fontsize=9, loc="lower right")
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
    out = dirs["histograms"] / "cumulative_ecd_14_16.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"Cumulative ECD saved: {out}")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    dirs = _ensure_dirs()

    results: dict = {"summary_rows": [], "all_sizes": {}}

    for img_name in IMAGES:
        fpath = DATA_DIR / img_name
        if not fpath.exists():
            print(f"SKIP: {fpath} not found")
            continue
        process_one(fpath, dirs, results)

    _write_summary(results, dirs)
    _write_combined_histogram(results, dirs)
    _write_cumulative_ecd(results, dirs)

    print("\nDone.")


if __name__ == "__main__":
    main()
