"""Interactive line-drawing annotator for homography correction.

Draw ANY 4 lines passing through the 4 edges of the screen.
All 6 pairwise intersections are computed; the 4 that form the largest
convex quadrilateral are used as corners for perspective warp.

Controls
--------
  LEFT CLICK    — place a point (2 points = 1 line)
  RIGHT CLICK   — undo last point / last line
  r             — reset all lines
  c / ESC       — cancel
  s             — save result (after 4 lines drawn)
  + / -         — zoom in / out
  Mouse wheel   — scroll to zoom
  Middle drag   — pan

Usage
-----
  uv run python -m sem_analysis.annotator SEM_imgs/00.jpg
"""

from __future__ import annotations

import itertools
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np
from numpy.typing import NDArray

# ---------------------------------------------------------------------------
# geometry helpers
# ---------------------------------------------------------------------------

def _line_intersection(
    p1: NDArray[np.floating],
    p2: NDArray[np.floating],
    p3: NDArray[np.floating],
    p4: NDArray[np.floating],
) -> tuple[float, float]:
    """Intersection of infinite line (p1,p2) with (p3,p4)."""
    x1, y1 = float(p1[0]), float(p1[1])
    x2, y2 = float(p2[0]), float(p2[1])
    x3, y3 = float(p3[0]), float(p3[1])
    x4, y4 = float(p4[0]), float(p4[1])
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-10:
        return (float("nan"), float("nan"))
    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denom
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denom
    return (px, py)


def _find_quad_corners(
    lines: list[NDArray[np.floating]],
    image_w: int,
    image_h: int,
) -> list[tuple[float, float]] | None:
    """Given 4 lines, compute all 6 intersections and pick the 4 that
    form the largest convex quadrilateral.

    Returns list of 4 corners ordered TL, TR, BR, BL, or None.
    """
    # all 6 pairwise intersections
    pts: list[tuple[float, float]] = []
    for i, j in itertools.combinations(range(4), 2):
        ix = _line_intersection(lines[i][0], lines[i][1],
                                lines[j][0], lines[j][1])
        pts.append(ix)

    valid: list[tuple[float, float]] = []
    margin = max(image_w, image_h) * 2.0
    for cx, cy in pts:
        if np.isfinite(cx) and np.isfinite(cy):
            if abs(cx) < margin and abs(cy) < margin:
                valid.append((cx, cy))

    # If not enough valid points within margin, try with larger margin
    if len(valid) < 4:
        valid = [(cx, cy) for cx, cy in pts
                 if np.isfinite(cx) and np.isfinite(cy)]

    if len(valid) < 4:
        return None

    valid_arr = np.array(valid, dtype=np.float32)

    # find convex hull (keep only outer points)
    hull = cv2.convexHull(valid_arr.reshape(-1, 1, 2).astype(np.int32))
    hull_pts = hull.reshape(-1, 2).astype(np.float32)

    if len(hull_pts) < 4:
        return None

    # if hull has > 4 points, approx to quadrilateral
    if len(hull_pts) > 4:
        peri = cv2.arcLength(hull_pts.reshape(-1, 1, 2).astype(np.float32), True)
        for _ in range(3):
            hull_pts = cv2.approxPolyDP(
                hull_pts.reshape(-1, 1, 2).astype(np.float32),
                0.02 * peri, True,
            ).reshape(-1, 2).astype(np.float32)
            if len(hull_pts) <= 4:
                break

    if len(hull_pts) != 4:
        return None

    # order TL, TR, BR, BL
    ordered = np.zeros((4, 2), dtype=np.float32)
    s = hull_pts.sum(axis=1)
    ordered[0] = hull_pts[np.argmin(s)]
    ordered[2] = hull_pts[np.argmax(s)]
    d = np.diff(hull_pts, axis=1)
    ordered[1] = hull_pts[np.argmin(d)]
    ordered[3] = hull_pts[np.argmax(d)]

    return [(float(ordered[i][0]), float(ordered[i][1])) for i in range(4)]


def _extend_line_to_bounds(
    p1: NDArray[np.floating],
    p2: NDArray[np.floating],
    w: int,
    h: int,
) -> tuple[NDArray[np.floating], NDArray[np.floating]]:
    dx = float(p2[0] - p1[0])
    dy = float(p2[1] - p1[1])
    if abs(dx) < 1e-10 and abs(dy) < 1e-10:
        return (p1.copy(), p2.copy())

    ts: list[float] = [0.0, 1.0]
    if abs(dx) > 1e-10:
        ts.append(-p1[0] / dx)
        ts.append((w - 1 - p1[0]) / dx)
    if abs(dy) > 1e-10:
        ts.append(-p1[1] / dy)
        ts.append((h - 1 - p1[1]) / dy)

    pts = []
    for t in ts:
        x = p1[0] + t * dx
        y = p1[1] + t * dy
        if -100 <= x <= w + 99 and -100 <= y <= h + 99:
            pts.append((x, y))

    if len(pts) < 2:
        return (p1.copy(), p2.copy())

    pts.sort(key=lambda p: p[0] ** 2 + p[1] ** 2)
    return (np.array(pts[0], dtype=np.float32),
            np.array(pts[-1], dtype=np.float32))


# ---------------------------------------------------------------------------
# state
# ---------------------------------------------------------------------------

LINE_COLORS = [(0, 255, 255), (255, 200, 0), (200, 0, 255), (128, 255, 128)]


@dataclass
class State:
    image: NDArray
    zoom: float = 1.0
    pan_x: float = 0.0
    pan_y: float = 0.0

    lines: list[NDArray[np.floating]] = field(default_factory=list)
    current_pts: list[NDArray[np.floating]] = field(default_factory=list)
    corners: list[tuple[float, float]] | None = None

    @property
    def image_h(self) -> int:
        return self.image.shape[0]

    @property
    def image_w(self) -> int:
        return self.image.shape[1]

    def invert_transform(self, sx: float, sy: float) -> NDArray[np.floating]:
        return np.array(
            [(sx - self.pan_x) / self.zoom, (sy - self.pan_y) / self.zoom],
            dtype=np.float32,
        )


# ---------------------------------------------------------------------------
# drawing
# ---------------------------------------------------------------------------

def _draw(state: State, window_name: str) -> None:
    h, w = state.image_h, state.image_w
    zw = int(w * state.zoom)
    zh = int(h * state.zoom)
    display = cv2.resize(state.image, (zw, zh))
    display = cv2.copyMakeBorder(
        display, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=(64, 64, 64),
    )
    ox = int(20 + state.pan_x)
    oy = int(20 + state.pan_y)

    def to_disp(pt: NDArray[np.floating]) -> tuple[int, int]:
        return (int(pt[0] * state.zoom + ox), int(pt[1] * state.zoom + oy))

    # draw completed lines
    for i, pts in enumerate(state.lines):
        color = LINE_COLORS[i % 4]
        ep1, ep2 = _extend_line_to_bounds(pts[0], pts[1], w, h)
        cv2.line(display, to_disp(ep1), to_disp(ep2), color, 2, cv2.LINE_AA)
        cv2.circle(display, to_disp(pts[0]), 4, color, -1)
        cv2.circle(display, to_disp(pts[1]), 4, color, -1)

    # current line
    for pt in state.current_pts:
        cv2.circle(display, to_disp(pt), 6, (0, 255, 0), -1)
    if len(state.current_pts) == 2:
        ep1, ep2 = _extend_line_to_bounds(
            state.current_pts[0], state.current_pts[1], w, h,
        )
        cv2.line(display, to_disp(ep1), to_disp(ep2), (0, 255, 0), 2, cv2.LINE_AA)

    # corners
    if state.corners is not None:
        labels = ("TL", "TR", "BR", "BL")
        for i, (cx, cy) in enumerate(state.corners):
            if np.isfinite(cx) and np.isfinite(cy):
                cpt = np.array([cx, cy], dtype=np.float32)
                cv2.circle(display, to_disp(cpt), 8, (0, 0, 255), -1)
                cv2.putText(display, labels[i],
                            (to_disp(cpt)[0] + 10, to_disp(cpt)[1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    # status
    n_lines = len(state.lines)
    if n_lines < 4:
        if len(state.current_pts) == 0:
            status = f"Line {n_lines + 1}/4 — click first point"
        else:
            status = f"Line {n_lines + 1}/4 — click second point"
    else:
        status = "All 4 lines done! [s to save] [r to restart]"
        if state.corners is None:
            status += " (no valid quad — adjust lines)"
    cv2.putText(display, status, (10, display.shape[0] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)

    hint = "Draw 4 lines passing through screen edges (any order). LEFT: point | RIGHT: undo | R: reset | S: save"
    cv2.putText(display, hint, (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1, cv2.LINE_AA)

    cv2.imshow(window_name, display)


# ---------------------------------------------------------------------------
# mouse callback
# ---------------------------------------------------------------------------

def _make_mouse_cb(state: State):
    dragging = [False]
    last_pt = [0, 0]

    def cb(event: int, x: int, y: int, flags: int, _param: object) -> None:
        nonlocal last_pt, dragging

        if event == cv2.EVENT_LBUTTONDOWN:
            if len(state.lines) >= 4:
                return
            pt_img = state.invert_transform(float(x - 20), float(y - 20))
            state.current_pts.append(pt_img)
            if len(state.current_pts) == 2:
                state.lines.append(state.current_pts.copy())
                state.current_pts.clear()
                if len(state.lines) == 4:
                    state.corners = _find_quad_corners(
                        state.lines, state.image_w, state.image_h,
                    )

        elif event == cv2.EVENT_RBUTTONDOWN:
            if state.current_pts:
                state.current_pts.pop()
            elif state.lines:
                state.lines.pop()
                state.corners = None

        elif event == cv2.EVENT_MBUTTONDOWN:
            dragging[0] = True
            last_pt = [x, y]
        elif event == cv2.EVENT_MOUSEMOVE and dragging[0]:
            dx = x - last_pt[0]; dy = y - last_pt[1]
            state.pan_x += dx; state.pan_y += dy
            last_pt = [x, y]
        elif event == cv2.EVENT_MBUTTONUP:
            dragging[0] = False
        elif event == cv2.EVENT_MOUSEWHEEL:
            factor = 1.1 if flags > 0 else 0.9
            nz = max(0.1, min(5.0, state.zoom * factor))
            cx = float(x - 20) / state.zoom - state.pan_x / state.zoom
            cy = float(y - 20) / state.zoom - state.pan_y / state.zoom
            state.pan_x = x - 20 - cx * nz
            state.pan_y = y - 20 - cy * nz
            state.zoom = nz

    return cb


# ---------------------------------------------------------------------------
# main loop
# ---------------------------------------------------------------------------

def annotate_image(image: NDArray) -> list[tuple[float, float]] | None:
    """Open an interactive window to annotate 4 screen edges."""
    state = State(image=image)
    window = "SEM Annotator — draw 4 lines along screen edges"

    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window, min(image.shape[1], 1600), min(image.shape[0], 900))
    cv2.setMouseCallback(window, _make_mouse_cb(state))

    while True:
        _draw(state, window)
        key = cv2.waitKey(30) & 0xFF

        if key in (27, ord("c")):
            cv2.destroyWindow(window)
            return None

        if key == ord("r"):
            state.lines.clear()
            state.current_pts.clear()
            state.corners = None

        if key == ord("s") and state.corners is not None:
            cv2.destroyWindow(window)
            return state.corners

        if key in (ord("+"), ord("=")):
            cx, cy = state.image_w / 2, state.image_h / 2
            nz = min(5.0, state.zoom * 1.2)
            state.pan_x = (state.pan_x + cx * state.zoom) - cx * nz
            state.pan_y = (state.pan_y + cy * state.zoom) - cy * nz
            state.zoom = nz
        if key == ord("-"):
            cx, cy = state.image_w / 2, state.image_h / 2
            nz = max(0.1, state.zoom * 0.8)
            state.pan_x = (state.pan_x + cx * state.zoom) - cx * nz
            state.pan_y = (state.pan_y + cy * state.zoom) - cy * nz
            state.zoom = nz
        if key == ord("0"):
            state.zoom = 1.0; state.pan_x = 0.0; state.pan_y = 0.0
        if key == 81: state.pan_x -= 40
        if key == 83: state.pan_x += 40
        if key == 82: state.pan_y -= 40
        if key == 84: state.pan_y += 40

    return None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: uv run python -m sem_analysis.annotator <image_path>")
        sys.exit(1)

    img_path = Path(sys.argv[1])
    if not img_path.exists():
        print(f"File not found: {img_path}")
        sys.exit(1)

    img = cv2.imread(str(img_path))
    if img is None:
        print(f"Cannot read image: {img_path}")
        sys.exit(1)

    print(f"Loaded: {img_path.name}  ({img.shape[1]}x{img.shape[0]})")
    print("Draw 4 lines passing through screen edges (any order).")
    print("2 clicks per line. Intersections form the quad corners.")
    print()

    corners = annotate_image(img)

    if corners is None:
        print("Cancelled.")
        return

    labels = ("TL", "TR", "BR", "BL")
    print("Corners (original image coords):")
    for i, (cx, cy) in enumerate(corners):
        print(f"  {labels[i]}: ({cx:.1f}, {cy:.1f})")

    # validation
    img_area = img.shape[0] * img.shape[1]
    quad_area = cv2.contourArea(
        np.array(corners, dtype=np.float32).reshape(-1, 1, 2)
    )
    if quad_area / img_area < 0.01:
        print("WARNING: quad area < 1% — lines may not form a valid rectangle.")
        print("Try again with straighter lines along each screen edge.")
        return

    # save corners
    out_dir = img_path.parent.parent / "SEM_results" / "corrected"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{img_path.stem}_corners.json"
    json_path.write_text(
        json.dumps({
            "image": str(img_path.name),
            "src_resolution": [img.shape[1], img.shape[0]],
            "corners": {
                labels[i]: [round(cx, 2), round(cy, 2)]
                for i, (cx, cy) in enumerate(corners)
            },
        }, indent=2),
        encoding="utf-8",
    )
    print(f"Corners saved: {json_path}")

    # apply homography
    try:
        from .homography import apply_homography
    except ImportError:
        from sem_analysis.homography import apply_homography

    c_arr = np.array(corners, dtype=np.float32)
    rectified = apply_homography(img, c_arr, target_width=1920, trust_order=True)

    preview_h = min(1080, int(1920 * rectified.shape[0] / max(rectified.shape[1], 1)))
    preview = cv2.resize(rectified, (1920, preview_h))
    cv2.imshow("Preview — press any key to close", preview)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    out_path = out_dir / f"{img_path.stem}_corrected.jpg"
    cv2.imwrite(str(out_path), rectified)
    print(f"Image saved: {out_path}")


if __name__ == "__main__":
    main()
