"""SEM particle analysis — main pipeline."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pandas as pd

from sem_analysis.homography import correct_image
from sem_analysis.segment import segment
from sem_analysis.scale_bar import get_scale
from sem_analysis.filter import classify_particles

from .config import DATA_DIR, OUTPUT_DIR, OUTPUT_SUBDIRS, SCALE, STACK_GROUPS, GROUP_COLORS
from .crop import crop_sem_region
from .feret import compute_feret_min_all
from .annotate import annotate_particles
from .histogram import save_histogram, save_combined_histogram


def _ensure_dirs() -> dict[str, Path]:
    dirs = OUTPUT_SUBDIRS.copy()
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs


def process_single_image(
    fpath: Path,
    dirs: dict[str, Path],
    results: dict,
) -> None:
    """Process one SEM image: homography → crop → segment → classify → annotate → export."""
    name = fpath.stem
    print(f"--- {fpath.name} ---")

    img = cv2.imread(str(fpath))
    if img is None:
        print("  ERROR: cannot read")
        return

    rectified, _ = correct_image(img)
    h, w = rectified.shape[:2]
    print(f"  homography: {w}x{h}")

    crop = crop_sem_region(rectified)
    print(f"  crop: {crop.shape[1]}x{crop.shape[0]}")

    labels, props = segment(crop)
    df = pd.DataFrame(props)
    n = len(df)
    nm_per_px = get_scale(name, rectified) or SCALE.get(name, 0)
    feret = df["feret_diameter_max"].values
    feret_nm = feret * nm_per_px if nm_per_px else feret
    print(f"  particles: {n}")

    if n == 0:
        return

    feret_min_vals = compute_feret_min_all(labels, df["label"].values)

    single_mask = classify_particles(
        df["area"].values, df["perimeter"].values,
        df["solidity"].values, df["extent"].values,
        feret, feret_min_vals,
    )
    n_single = int(single_mask.sum())
    n_aggl = n - n_single
    print(f"  single: {n_single}  agglomerate: {n_aggl}")

    vis, feret_lines = annotate_particles(
        crop, labels,
        df["label"].values,
        df["feret_diameter_max"].values,
        single_mask, nm_per_px,
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
        size_data, name,
        str(dirs["histograms"] / f"{name}_histogram.svg"),
        unit=unit,
    )

    feret_single = feret_nm[single_mask] if n_single > 0 else feret_nm
    print(f"  scale: {nm_per_px:.2f} nm/px")
    print(f"  Feret: mean={feret_single.mean():.1f} median={np.median(feret_single):.1f} "
          f"min={feret_single.min():.1f} max={feret_single.max():.1f} {unit}")
    print(f"  saved: annotated, CSV, histogram")
    print()

    results["summary_rows"].append({
        "image": name,
        "n": n_single,
        "n_total": n,
        "mean_nm": float(feret_single.mean()),
        "median_nm": float(np.median(feret_single)),
        "std_nm": float(feret_single.std()),
        "min_nm": float(feret_single.min()),
        "max_nm": float(feret_single.max()),
        "scale_nm_px": nm_per_px,
    })
    results["all_sizes"][name] = feret_single


def run_pipeline(image_filter: str | None = None) -> dict:
    """Run the full SEM analysis pipeline.

    Parameters
    ----------
    image_filter : If provided (e.g. "01.jpg"), process only that image.
                   Otherwise process all *.jpg in data/.

    Returns
    -------
    dict with summary_rows and all_sizes for downstream consumers.
    """
    dirs = _ensure_dirs()

    if image_filter:
        jpgs = [DATA_DIR / image_filter]
    else:
        jpgs = sorted(DATA_DIR.glob("*.jpg"))

    if not jpgs:
        print("No images found.")
        return {"summary_rows": [], "all_sizes": {}}

    print(f"Processing {len(jpgs)} SEM image(s)\n")

    results: dict = {"summary_rows": [], "all_sizes": {}}

    for fpath in jpgs:
        if fpath.suffix.lower() not in (".jpg", ".jpeg"):
            continue
        process_single_image(fpath, dirs, results)

    _write_summary(results, dirs)
    _write_combined_histogram(results, dirs)

    return results


def _write_summary(results: dict, dirs: dict[str, Path]) -> None:
    rows = results.get("summary_rows", [])
    if not rows:
        return

    summary_df = pd.DataFrame(rows)
    summary_df.to_csv(dirs["data"] / "summary.csv", index=False)
    print("\n" + "=" * 70)
    print("PER-IMAGE SUMMARY (Feret diam.)")
    print("=" * 70)
    for r in rows:
        print(f"  {r['image']}: n={r['n']:4d}  mean={r['mean_nm']:6.0f}  "
              f"median={r['median_nm']:6.0f}  std={r['std_nm']:5.0f} nm")
    print(f"\nSummary saved to {dirs['data'] / 'summary.csv'}")


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
    labels = []
    for gname, keys in STACK_GROUPS:
        vals = []
        for k in keys:
            if k in all_sizes:
                vals.append(all_sizes[k])
        if not vals:
            continue
        gv = np.concatenate(vals)
        group_vals.append(gv)
        labels.append(f"{gname} (n={len(gv)})")

    if group_vals:
        unit = _resolve_combined_unit(results)
        save_combined_histogram(
            group_vals, labels, GROUP_COLORS,
            str(dirs["histograms"] / "combined_histogram.svg"),
            unit=unit,
        )
        all_vals = np.concatenate(group_vals)
        print(f"\nCombined histogram saved to {dirs['histograms'] / 'combined_histogram'}")
        print(f"  n={len(all_vals)} mean={all_vals.mean():.0f} "
              f"std={all_vals.std():.0f} median={np.median(all_vals):.0f} {unit}")
