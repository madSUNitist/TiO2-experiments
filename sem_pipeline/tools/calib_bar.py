"""Calibrate scale bar ROI — draw rectangles on corrected images.

LEFT drag -> draw rectangle
RIGHT click -> undo
ENTER -> save & next
ESC -> quit

Outputs: output/corrected/_bar_calib.json
"""

from pathlib import Path
import json
import cv2
import numpy as np

_PKG = Path(__file__).resolve().parent.parent
SRC = _PKG / "output" / "corrected"
OUT = SRC / "_bar_calib.json"

drawing = False
rect_start = (0, 0)
rect_end = (0, 0)
rects: list[dict] = []


def on_mouse(event, x, y, flags, param):
    global drawing, rect_start, rect_end
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        rect_start = (x, y)
    elif event == cv2.EVENT_MOUSEMOVE and drawing:
        rect_end = (x, y)
    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        rect_end = (x, y)


def main():
    global drawing, rect_start, rect_end, rects

    corrected = sorted(SRC.glob("*_corrected.jpg"))
    if not corrected:
        print("No corrected images found.")
        return

    cv2.namedWindow("calib", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback("calib", on_mouse)

    idx = 0
    while idx < len(corrected):
        fpath = corrected[idx]
        img = cv2.imread(str(fpath))
        h, w = img.shape[:2]
        disp = img.copy()

        if drawing or rect_end != rect_start:
            cv2.rectangle(disp, rect_start, rect_end, (0, 255, 0), 2)

        stats = ""
        if rects:
            avg_x = np.mean([r["x_frac"] for r in rects])
            avg_y = np.mean([r["y_frac"] for r in rects])
            avg_w = np.mean([r["w_frac"] for r in rects])
            avg_h = np.mean([r["h_frac"] for r in rects])
            stats = (f"avg: x={avg_x:.4f} y={avg_y:.4f} "
                     f"w={avg_w:.4f} h={avg_h:.4f}  ({len(rects)} samples)")
        cv2.putText(disp, f"{fpath.name}  {stats}",
                    (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        cv2.imshow("calib", disp)
        key = cv2.waitKey(30) & 0xFF

        if key == 27:
            break
        elif key == 13:
            x1, y1 = min(rect_start[0], rect_end[0]), min(rect_start[1], rect_end[1])
            x2, y2 = max(rect_start[0], rect_end[0]), max(rect_start[1], rect_end[1])
            if x2 > x1 and y2 > y1:
                rects.append({
                    "image": fpath.name,
                    "x_frac": round(x1 / w, 6),
                    "y_frac": round(y1 / h, 6),
                    "w_frac": round((x2 - x1) / w, 6),
                    "h_frac": round((y2 - y1) / h, 6),
                })
                idx += 1
                rect_start = (0, 0)
                rect_end = (0, 0)
        elif key == ord("r"):
            if rects:
                rects.pop()
                idx = max(0, idx - 1)

    cv2.destroyAllWindows()

    if rects:
        OUT.write_text(json.dumps(rects, indent=2), encoding="utf-8")
        avg_x = np.mean([r["x_frac"] for r in rects])
        avg_y = np.mean([r["y_frac"] for r in rects])
        avg_w = np.mean([r["w_frac"] for r in rects])
        avg_h = np.mean([r["h_frac"] for r in rects])
        print(f"\nSaved: {OUT}")
        print(f"Average ({len(rects)} samples):")
        print(f"  x_left={avg_x:.4f}  x_right={avg_x+avg_w:.4f}")
        print(f"  y_top={avg_y:.4f}   y_bot={avg_y+avg_h:.4f}")
    else:
        print("No rectangles saved.")


if __name__ == "__main__":
    main()
