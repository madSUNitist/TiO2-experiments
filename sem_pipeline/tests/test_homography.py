"""Validation script — test homography correction on all SEM images."""

from __future__ import annotations

from pathlib import Path

import cv2

from sem_analysis.homography import correct_file

_PKG = Path(__file__).resolve().parent.parent
DATA_DIR = _PKG / "data"
OUT_DIR = _PKG / "output" / "corrected"


def main() -> None:
    jpgs = sorted(DATA_DIR.glob("*.jpg"))
    if not jpgs:
        print("No .jpg files found in data/")
        return

    print(f"Processing {len(jpgs)} image(s)\n")

    ok = 0
    for fpath in jpgs:
        print(f"--- {fpath.name} ---")
        try:
            _, corners = correct_file(fpath, OUT_DIR)
            if corners is not None:
                ok += 1
                print("  status: detected")
            else:
                print("  status: NOT DETECTED — saved uncorrected")
        except Exception as exc:
            print(f"  ERROR: {exc}")

    print(f"\n{'='*50}")
    print(f"Detected in {ok}/{len(jpgs)} images.")
    print(f"Output: {OUT_DIR}")


if __name__ == "__main__":
    main()
