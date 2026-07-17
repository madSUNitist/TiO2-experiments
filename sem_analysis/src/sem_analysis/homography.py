"""Homography correction — blue-mask line detection + optimal quad search.

Pipeline
--------
1. Downscale to 1024 px wide.
2. Blue mask = case/bezel pixels (BGR 5–50).
3. Flood-fill bottom-left to remove computer case.
4. Canny + HoughLinesP on blue mask boundaries.
5. Exclude lines touching the central 50 % × 50 % rectangle.
6. Filter orientation: ±30° of horizontal or vertical.
7. Merge collinear fragments (same slope, nearby intercept).
8. Keep lines spanning > 40 % of image dimension.
9. Split into top / bottom / left / right candidates.
10. Enumerate all 4-line combinations; compute intersection corners.
11. Pick the quad maximising blue-pixel count inside,
    with area between 55 % and 85 % of image.
12. Perspective warp to 1920 px wide.
"""

from __future__ import annotations

from itertools import product
from pathlib import Path

import cv2
import numpy as np
from numpy.typing import NDArray

from .config import HOMOGRAPHY as CFG

BLUE_LO = (5, 5, 5)
BLUE_HI = (50, 50, 50)


# ---------------------------------------------------------------------------
# blue mask
# ---------------------------------------------------------------------------

def _blue_mask(bgr: NDArray) -> NDArray:
    m = np.ones(bgr.shape[:2], dtype=bool)
    for c in range(3):
        m &= (bgr[:, :, c] >= BLUE_LO[c]) & (bgr[:, :, c] <= BLUE_HI[c])
    return m


def _post_merge_cleanup(blue: NDArray, long_h: list, long_v: list,
                        sh: int) -> tuple:
    """Remove dense blue blobs on both sides.  Done after merge."""
    h, w = blue.shape
    limit = h * 2 // 3
    col_d = blue[limit:, :].mean(axis=0)
    density_threshold = 0.50  # only remove very dense case blobs

    # left side
    left_end = 0
    for x in range(5, w):
        if col_d[x] > density_threshold:
            left_end = x + 1
        else:
            break

    # right side
    right_start = w
    for x in range(w - 6, -1, -1):
        if col_d[x] > density_threshold:
            right_start = x
        else:
            break

    if left_end > 5:
        blue[:, :left_end] = False
        long_v = [l for l in long_v
                  if min(l[0], l[2]) > left_end]
        long_h = [l for l in long_h
                  if min(l[0], l[2]) > left_end and max(l[0], l[2]) > left_end]
    if right_start < w - 5:
        blue[:, right_start:] = False
        long_v = [l for l in long_v
                  if max(l[0], l[2]) < right_start]
        long_h = [l for l in long_h
                  if max(l[0], l[2]) < right_start and min(l[0], l[2]) < right_start]

    return blue, long_h, long_v


# ---------------------------------------------------------------------------
# line detection + filtering
# ---------------------------------------------------------------------------

def _detect_lines(blue: NDArray) -> list:
    b8 = blue.astype(np.uint8) * 255
    e = cv2.Canny(b8, 50, 150)
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    e = cv2.dilate(e, k, iterations=1)
    lines = cv2.HoughLinesP(e, 1, np.pi / 180, threshold=40,
                            minLineLength=int(min(b8.shape) * 0.05),
                            maxLineGap=30)
    if lines is None:
        return []
    return lines.reshape(-1, 4).tolist()


def _filter_center(lines, sw, sh):
    cx1, cx2 = int(sw * 0.25), int(sw * 0.75)
    cy1, cy2 = int(sh * 0.25), int(sh * 0.75)
    kept = []
    for x1, y1, x2, y2 in lines:
        ok = True
        for t in np.linspace(0, 1, 12):
            x = int(x1 + t * (x2 - x1))
            y = int(y1 + t * (y2 - y1))
            if cx1 <= x <= cx2 and cy1 <= y <= cy2:
                ok = False
                break
        if ok:
            kept.append((x1, y1, x2, y2))
    return kept


def _filter_orientation(lines):
    h, v = [], []
    for x1, y1, x2, y2 in lines:
        dx, dy = abs(x2 - x1), abs(y2 - y1)
        if dx < 1e-6 and dy < 1e-6:
            continue
        a = abs(np.arctan2(dy, dx) * 180.0 / np.pi)
        if a < 30 or a > 150:
            h.append((x1, y1, x2, y2))
        elif 60 < a < 120:
            v.append((x1, y1, x2, y2))
    return h, v


# ---------------------------------------------------------------------------
# line merging
# ---------------------------------------------------------------------------

def _merge(lines_h, lines_v):
    def _group(lines, is_h):
        if len(lines) <= 1:
            return lines
        if is_h:
            lines.sort(key=lambda l: min(l[0], l[2]))
        else:
            lines.sort(key=lambda l: min(l[1], l[3]))
        mg = []
        cur = list(lines[0])
        for line in lines[1:]:
            x1c, y1c, x2c, y2c = cur
            x1n, y1n, x2n, y2n = line
            if is_h:
                cmin, cmax = min(x1c, x2c), max(x1c, x2c)
                nmin, nmax = min(x1n, x2n), max(x1n, x2n)
                gap = max(0, nmin - cmax, cmin - nmax)
                ts = (cmax - cmin) + (nmax - nmin)
                if gap < ts * 0.2:
                    nx1 = min(x1c, x2c, x1n, x2n)
                    nx2 = max(x1c, x2c, x1n, x2n)
                    dx = x2c - x1c
                    if abs(dx) > 1e-6:
                        s = (y2c - y1c) / dx
                        cur = [nx1, int(y1c + s * (nx1 - x1c)),
                               nx2, int(y1c + s * (nx2 - x1c))]
                    else:
                        cur = [nx1, y1c, nx2, y2c]
                else:
                    mg.append(tuple(cur))
                    cur = list(line)
            else:
                cmin, cmax = min(y1c, y2c), max(y1c, y2c)
                nmin, nmax = min(y1n, y2n), max(y1n, y2n)
                gap = max(0, nmin - cmax, cmin - nmax)
                ts = (cmax - cmin) + (nmax - nmin)
                if gap < ts * 0.2:
                    ny1 = min(y1c, y2c, y1n, y2n)
                    ny2 = max(y1c, y2c, y1n, y2n)
                    dy = y2c - y1c
                    if abs(dy) > 1e-6:
                        s = (x2c - x1c) / dy
                        cur = [int(x1c + s * (ny1 - y1c)), ny1,
                               int(x1c + s * (ny2 - y1c)), ny2]
                    else:
                        cur = [x1c, ny1, x2c, ny2]
                else:
                    mg.append(tuple(cur))
                    cur = list(line)
        mg.append(tuple(cur))
        return mg

    # group H by slope & intercept
    hg = {}
    for x1, y1, x2, y2 in lines_h:
        dx = x2 - x1
        s = (y2 - y1) / dx if abs(dx) > 1e-6 else 0.0
        ic = y1 - s * x1
        key = (round(s * 100), round(ic / 10) * 10)
        hg.setdefault(key, []).append((x1, y1, x2, y2))
    mh = []
    for g in hg.values():
        mh.extend(_group(g, True))

    # group V by inverse slope & x-intercept
    vg = {}
    for x1, y1, x2, y2 in lines_v:
        dy = y2 - y1
        if abs(dy) > 1e-6:
            isl = (x2 - x1) / dy
            ic = x1 - isl * y1
        else:
            isl = 999.0
            ic = x1
        key = (round(isl * 100), round(ic / 10) * 10)
        vg.setdefault(key, []).append((x1, y1, x2, y2))
    mv = []
    for g in vg.values():
        mv.extend(_group(g, False))

    return mh, mv


# ---------------------------------------------------------------------------
# geometry
# ---------------------------------------------------------------------------

def _intersect(l1, l2):
    x1, y1, x2, y2 = l1
    x3, y3, x4, y4 = l2
    d = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(d) < 1e-10:
        return None
    px = ((x1 * y2 - y1 * x2) * (x3 - x4)
          - (x1 - x2) * (x3 * y4 - y3 * x4)) / d
    py = ((x1 * y2 - y1 * x2) * (y3 - y4)
          - (y1 - y2) * (x3 * y4 - y3 * x4)) / d
    return (px, py)


def _blue_inside(tl, tr, br, bl, blue_mask):
    pts = np.array([tl, tr, br, bl], np.int32)
    m = np.zeros(blue_mask.shape, np.uint8)
    cv2.fillPoly(m, [pts], 255)
    return int(((m > 0) & (blue_mask > 0)).sum())


# ---------------------------------------------------------------------------
# optimal quad search
# ---------------------------------------------------------------------------

def _find_optimal_quad(long_h, long_v, blue_mask, sw, sh):
    top_c = [l for l in long_h if (l[1] + l[3]) / 2 < sh * CFG["cand_split"]]
    bot_c = [l for l in long_h if (l[1] + l[3]) / 2 > sh * (1 - CFG["cand_split"])]
    lft_c = [l for l in long_v if (l[0] + l[2]) / 2 < sw * CFG["cand_split"]]
    rgt_c = [l for l in long_v if (l[0] + l[2]) / 2 > sw * (1 - CFG["cand_split"])]

    best = None
    best_blue = 0

    for top, bot, left, right in product(top_c, bot_c, lft_c, rgt_c):
        tl = _intersect(top, left)
        tr = _intersect(top, right)
        br = _intersect(bot, right)
        bl = _intersect(bot, left)
        if tl is None or tr is None or br is None or bl is None:
            continue

        corners = np.array([tl, tr, br, bl], np.float32).reshape(-1, 1, 2)
        area_pct = cv2.contourArea(corners) / (sw * sh) * 100
        if area_pct < CFG["area_min"] or area_pct > CFG["area_max"]:
            continue

        nb = _blue_inside(tl, tr, br, bl, blue_mask)
        if nb > best_blue:
            best_blue = nb
            best = (tl, tr, br, bl)

    if best is None:
        return None
    return np.array(best, dtype=np.float32)


# ---------------------------------------------------------------------------
# perspective warp
# ---------------------------------------------------------------------------

def _order_corners(pts: NDArray[np.float32]) -> NDArray[np.float32]:
    rect = np.zeros((4, 2), dtype=np.float32)
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    d = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(d)]
    rect[3] = pts[np.argmax(d)]
    return rect


def apply_homography(image: NDArray, corners: NDArray[np.float32],
                     target_width: int | None = None, *,
                     trust_order: bool = False) -> NDArray:
    rect = corners.copy() if trust_order else _order_corners(corners.copy())
    # use source quad's approximate width as target, then force 16:9
    aw = float(max(np.linalg.norm(rect[2] - rect[3]),
                   np.linalg.norm(rect[1] - rect[0])))
    tw = target_width or max(1200, min(4000, int(aw)))
    th = max(int(tw * 9 / 16), 1)
    dst = np.array(
        [[0, 0], [tw - 1, 0], [tw - 1, th - 1], [0, th - 1]],
        dtype=np.float32,
    )
    M = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(image, M, (tw, th))


# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------

def _pipeline(image: NDArray):
    """Run the full detection pipeline and return (quad_corners, blue_mask, scale)."""
    h, w = image.shape[:2]
    dw = CFG["downscale_max_width"]
    scale = dw / w if w > dw else 1.0
    small = cv2.resize(image, (dw, int(h * scale))) if scale != 1.0 else image
    sh, sw = small.shape[:2]

    blue = _blue_mask(small)
    raw = _detect_lines(blue)
    raw = _filter_center(raw, sw, sh)
    hl, vl = _filter_orientation(raw)
    mh, mv = _merge(hl, vl)

    long_h = [l for l in mh if abs(l[2] - l[0]) > sw * CFG["long_ratio"]]
    long_v = [l for l in mv if abs(l[3] - l[1]) > sh * CFG["long_ratio"]]

    blue, long_h, long_v = _post_merge_cleanup(blue, long_h, long_v, sh)
    result = _find_optimal_quad(long_h, long_v, blue, sw, sh)
    if result is None:
        return None

    corners = result / scale if scale != 1.0 else result
    return corners


def correct_image(image: NDArray) -> tuple[NDArray, NDArray[np.float32] | None]:
    corners = _pipeline(image)
    if corners is None:
        return image, None
    return apply_homography(image, corners), corners


def correct_file(src: str | Path,
                 dst_dir: str | Path | None = None
                 ) -> tuple[NDArray, NDArray[np.float32] | None]:
    src = Path(src)
    img = cv2.imread(str(src))
    if img is None:
        raise FileNotFoundError(str(src))

    rectified, corners = correct_image(img)
    if dst_dir is not None:
        dst_dir = Path(dst_dir)
        dst_dir.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(dst_dir / f"{src.stem}_corrected.jpg"), rectified)
        cv2.imwrite(str(dst_dir / f"{src.stem}_debug.jpg"),
                    _draw_debug(img, corners))
        cv2.imwrite(str(dst_dir / f"{src.stem}_segmentation.jpg"),
                    _draw_seg(img, corners))
    return rectified, corners


# ---------------------------------------------------------------------------
# debug visualisation
# ---------------------------------------------------------------------------

def _draw_debug(image: NDArray,
                corners: NDArray[np.float32] | None) -> NDArray:
    h, w = image.shape[:2]
    scl = min(1200 / w, 1.0)
    dw = 1200 if w > 1200 else w
    disp = cv2.resize(image, (dw, int(h * scl))) if scl != 1.0 else image.copy()
    if corners is not None:
        pts = (corners * scl).astype(np.int32) if scl != 1.0 else corners.astype(np.int32)
        for i, l in enumerate(("TL", "TR", "BR", "BL")):
            cv2.circle(disp, tuple(pts[i]), 10, (0, 255, 255), -1)
            cv2.putText(disp, l, (pts[i][0] + 12, pts[i][1] - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.polylines(disp, [pts], True, (0, 255, 0), 3)
    else:
        cv2.putText(disp, "NOT DETECTED", (30, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
    return disp


def _draw_seg(image: NDArray,
              corners: NDArray[np.float32] | None) -> NDArray:
    h, w = image.shape[:2]
    dw = CFG["downscale_max_width"]
    scale = dw / w if w > dw else 1.0
    small = cv2.resize(image, (dw, int(h * scale))) if scale != 1.0 else image
    sh, sw = small.shape[:2]

    blue = _blue_mask(small)
    raw = _detect_lines(blue)
    raw = _filter_center(raw, sw, sh)
    hl, vl = _filter_orientation(raw)
    mh, mv = _merge(hl, vl)

    long_h = [l for l in mh if abs(l[2] - l[0]) > sw * CFG["long_ratio"]]
    long_v = [l for l in mv if abs(l[3] - l[1]) > sh * CFG["long_ratio"]]
    blue_before = blue.copy()
    blue, long_h, long_v = _post_merge_cleanup(blue, long_h, long_v, sh)
    removed = blue_before & (~blue)

    blue8 = blue.astype(np.uint8) * 255
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    vis = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    vis[blue8 > 0] = (255, 0, 0)
    vis[removed] = (0, 0, 255)

    cv2.rectangle(vis, (int(sw * .25), int(sh * .25)),
                  (int(sw * .75), int(sh * .75)), (0, 0, 255), 1)
    for l in long_h:
        cv2.line(vis, (l[0], l[1]), (l[2], l[3]), (0, 255, 255), 1, cv2.LINE_AA)
    for l in long_v:
        cv2.line(vis, (l[0], l[1]), (l[2], l[3]), (255, 0, 255), 1, cv2.LINE_AA)

    if corners is not None:
        cs = (corners * scale).astype(np.int32) if scale != 1.0 else corners.astype(np.int32)
        cv2.polylines(vis, [cs], True, (0, 255, 0), 2)

    r = 400 / sh
    return cv2.resize(vis, (int(sw * r), 400))
