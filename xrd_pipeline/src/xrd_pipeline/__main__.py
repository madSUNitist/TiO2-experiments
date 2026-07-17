"""XRD pipeline CLI entry point.

Usage
-----
  python -m xrd_pipeline                    batch-plot all samples
  python -m xrd_pipeline --diagnose NAME    diagnostic peak report
  python -m xrd_pipeline --debug-fwhm NAME  FWHM debug plots per peak
"""

from __future__ import annotations

import sys

from .config import DATA_DIR, OUTPUT_DIR, ANATASE_REF, RUTILE_REF
from .data import parse_xrd_file, clean_sample_label
from .plotting import plot_one_sample, diagnose_peaks, plot_fwhm_debug
from .processing import process_data, find_local_peak


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    args = sys.argv[1:]

    if args and args[0] == "--diagnose":
        target = args[1] if len(args) > 1 else "sample_01"
        txt_files = sorted(DATA_DIR.glob("*.txt"))
        found = None
        for fpath in txt_files:
            tt, intens, raw_name = parse_xrd_file(fpath)
            label = clean_sample_label(raw_name)
            if label == target or target in raw_name:
                found = fpath
                break
        if found is None:
            print(f"Sample '{target}' not found in {DATA_DIR}. Available:")
            for fpath in txt_files:
                print(f"  {clean_sample_label(parse_xrd_file(fpath)[2])}")
            return
        tt, intens, raw_name = parse_xrd_file(found)
        label = clean_sample_label(raw_name)
        diagnose_peaks(tt, intens, label, OUTPUT_DIR)
        return

    if args and args[0] == "--debug-fwhm":
        target = args[1] if len(args) > 1 else "sample_01"
        txt_files = sorted(DATA_DIR.glob("*.txt"))
        found = None
        for fpath in txt_files:
            tt, intens, raw_name = parse_xrd_file(fpath)
            label = clean_sample_label(raw_name)
            if label == target or target in raw_name:
                found = fpath
                break
        if found is None:
            print(f"Sample '{target}' not found in {DATA_DIR}. Available:")
            for fpath in txt_files:
                print(f"  {clean_sample_label(parse_xrd_file(fpath)[2])}")
            return
        tt, intens, raw_name = parse_xrd_file(found)
        label = clean_sample_label(raw_name)
        smoothed, _ = process_data(intens)

        print(f"FWHM debug plots for: {label}\n")
        for hkl, ref_tt in ANATASE_REF.items():
            result = find_local_peak(ref_tt, tt, smoothed)
            if result is not None:
                plot_fwhm_debug(ref_tt, tt, smoothed, "Anatase", hkl, OUTPUT_DIR)
        for hkl, ref_tt in RUTILE_REF.items():
            result = find_local_peak(ref_tt, tt, smoothed)
            if result is not None:
                plot_fwhm_debug(ref_tt, tt, smoothed, "Rutile", hkl, OUTPUT_DIR)
        print(f"\nDone. FWHM debug plots saved to {OUTPUT_DIR}")
        return

    txt_files = sorted(DATA_DIR.glob("*.txt"))
    if not txt_files:
        print(f"No .txt XRD files found in {DATA_DIR}")
        return

    print(f"Found {len(txt_files)} XRD data file(s)\n")

    for fpath in txt_files:
        tt, intens, raw_name = parse_xrd_file(fpath)
        label = clean_sample_label(raw_name)
        plot_one_sample(tt, intens, label, OUTPUT_DIR)

    print(f"\nDone. {len(txt_files)} plot(s) saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
