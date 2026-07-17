"""Scale-bar detection debug visualisation for 14.jpg / 16.jpg.

Reads the already-corrected images and draws the detection ROI, bright mask,
bar line, bar endpoints, and tick marks.

Usage
-----
    cd sem_pipeline && uv run python tools/scalebar_debug.py
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from sem_analysis.scale_bar import (
    X_LEFT, X_RIGHT, Y_TOP, Y_BOT, THRESHOLD, detect,
)
from sem_pipeline.config import OUTPUT_SUBDIRS


def _draw_scalebar_debug(
    image: np.ndarray,
    name: str,
    out_dir: Path,
) -> None:
    h, w = image.shape[:2]

    x1 = int(X_LEFT * w)
    x2 = int(X_RIGHT * w)
    y1 = int(Y_TOP * h)
    y2 = int(Y_BOT * h)

    roi = image[y1:y2, x1:x2].copy()
    rh, rw = roi.shape[:2]

    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if roi.ndim == 3 else roi
    bright = gray > THRESHOLD

    bar_info = detect(image)

    # ------------------------------------------------------------------
    # draw ROI magnified panel (right side)
    # ------------------------------------------------------------------
    zoom = min(4.0, 1200.0 / max(rh, 1))

    roi_color = roi.copy()
    roi_bright = (
        np.dstack([bright.astype(np.uint8) * 255] * 3)
        if roi.ndim == 3
        else cv2.cvtColor(bright.astype(np.uint8) * 255, cv2.COLOR_GRAY2BGR)
    )

    if bar_info:
        bar_y_rel = int(bar_info["bar_y"]) - y1
        bar_x1_rel = int(bar_info["bar_x1"]) - x1
        bar_x2_rel = int(bar_info["bar_x2"]) - x1

        # bar line (yellow)
        cv2.line(
            roi_color,
            (0, bar_y_rel),
            (rw - 1, bar_y_rel),
            (0, 255, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.line(
            roi_bright,
            (0, bar_y_rel),
            (rw - 1, bar_y_rel),
            (0, 255, 255),
            2,
            cv2.LINE_AA,
        )

        # bar endpoints (red)
        for bx in (bar_x1_rel, bar_x2_rel):
            cv2.circle(roi_color, (bx, bar_y_rel), 5, (0, 0, 255), -1)
            cv2.circle(roi_bright, (bx, bar_y_rel), 5, (0, 0, 255), -1)

    # magnify
    roi_zoom = cv2.resize(
        roi_color, (int(rw * zoom), int(rh * zoom)),
        interpolation=cv2.INTER_NEAREST,
    )
    bright_zoom = cv2.resize(
        roi_bright, (int(rw * zoom), int(rh * zoom)),
        interpolation=cv2.INTER_NEAREST,
    )

    # label on zoom
    if bar_info:
        info_lines = [
            f"bar_px = {bar_info['bar_px']}",
            f"bar_x1 = {bar_info['bar_x1']:.0f}",
            f"bar_x2 = {bar_info['bar_x2']:.0f}",
            f"bar_y  = {bar_info['bar_y']:.0f}",
        ]
    else:
        info_lines = ["NOT DETECTED"]
    cy = 30
    for ln in info_lines:
        cv2.putText(
            roi_zoom, ln, (10, cy),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2, cv2.LINE_AA,
        )
        cy += 24

    # ------------------------------------------------------------------
    # draw full image with ROI box (left side)
    # ------------------------------------------------------------------
    full = image.copy()
    cv2.rectangle(full, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.putText(
        full, "ROI", (x1 + 4, y1 - 8),
        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2, cv2.LINE_AA,
    )

    full_s = cv2.resize(
        full, (900, int(900 * h / w)),
    )

    # ------------------------------------------------------------------
    # tile:  full | roi_color | roi_bright
    # ------------------------------------------------------------------
    pad = 10
    panel_h = max(
        full_s.shape[0],
        roi_zoom.shape[0],
        bright_zoom.shape[0],
    )

    def _pad(panel: np.ndarray, target_h: int) -> np.ndarray:
        dh = target_h - panel.shape[0]
        if dh > 0:
            return cv2.copyMakeBorder(
                panel, 0, dh, 0, 0,
                cv2.BORDER_CONSTANT, value=(64, 64, 64),
            )
        return panel

    panels = [
        _pad(full_s, panel_h),
        _pad(roi_zoom, panel_h),
        _pad(bright_zoom, panel_h),
    ]

    # title bars
    titles = ["Full image (ROI in green)", "ROI magnified", "Bright mask (white > thresh)"]
    for i, t in enumerate(titles):
        title_bar = np.full((28, panels[i].shape[1], 3), (64, 64, 64), dtype=np.uint8)
        cv2.putText(
            title_bar, t, (6, 20),
            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA,
        )
        panels[i] = np.vstack([title_bar, panels[i]])

    result = np.hstack(panels)

    out_path = out_dir / f"{name}_scalebar_debug.jpg"
    cv2.imwrite(str(out_path), result)
    print(f"  saved: {out_path}")


def main() -> None:
    out_dir = OUTPUT_SUBDIRS["corrected"]
    out_dir.mkdir(parents=True, exist_ok=True)

    for name in ("14", "16"):
        img_path = out_dir / f"{name}_corrected.jpg"
        if not img_path.exists():
            print(f"SKIP: {img_path} not found")
            continue

        img = cv2.imread(str(img_path))
        if img is None:
            print(f"ERROR: cannot read {img_path}")
            continue

        print(f"\n{name}:")
        bar = detect(img)
        if bar:
            for k, v in bar.items():
                print(f"  {k} = {v}")
        else:
            print("  NOT DETECTED")

        _draw_scalebar_debug(img, name, out_dir)


if __name__ == "__main__":
    main()
