"""Optimal screen quad detection — full pipeline with inside-blue filter."""

from pathlib import Path
from itertools import product

import cv2
import numpy as np

_PKG = Path(__file__).resolve().parent.parent
DATA_DIR = _PKG / "data"
OUT_DIR = _PKG / "output" / "corrected"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def in_range(bgr, lo, hi):
    m = np.ones(bgr.shape[:2], dtype=bool)
    for c in range(3):
        m &= (bgr[:, :, c] >= lo[c]) & (bgr[:, :, c] <= hi[c])
    return m


def merge_lines(lines_h, lines_v):
    def merge_group(group, is_h):
        if len(group) <= 1:
            return group
        if is_h:
            group.sort(key=lambda l: min(l[0], l[2]))
        else:
            group.sort(key=lambda l: min(l[1], l[3]))
        merged = []
        curr = list(group[0])
        for line in group[1:]:
            x1c, y1c, x2c, y2c = curr
            x1n, y1n, x2n, y2n = line
            if is_h:
                cmin_x = min(x1c, x2c)
                cmax_x = max(x1c, x2c)
                nmin_x = min(x1n, x2n)
                nmax_x = max(x1n, x2n)
                gap = max(0, nmin_x - cmax_x, cmin_x - nmax_x)
                ts = (cmax_x - cmin_x) + (nmax_x - nmin_x)
                if gap < ts * 0.2:
                    nx1 = min(x1c, x2c, x1n, x2n)
                    nx2 = max(x1c, x2c, x1n, x2n)
                    dx = x2c - x1c
                    if abs(dx) > 1e-6:
                        s = (y2c - y1c) / dx
                        curr = [nx1, int(y1c + s * (nx1 - x1c)), nx2, int(y1c + s * (nx2 - x1c))]
                    else:
                        curr = [nx1, y1c, nx2, y2c]
                else:
                    merged.append(tuple(curr))
                    curr = list(line)
            else:
                cmin_y = min(y1c, y2c)
                cmax_y = max(y1c, y2c)
                nmin_y = min(y1n, y2n)
                nmax_y = max(y1n, y2n)
                gap = max(0, nmin_y - cmax_y, cmin_y - nmax_y)
                ts = (cmax_y - cmin_y) + (nmax_y - nmin_y)
                if gap < ts * 0.2:
                    ny1 = min(y1c, y2c, y1n, y2n)
                    ny2 = max(y1c, y2c, y1n, y2n)
                    dy = y2c - y1c
                    if abs(dy) > 1e-6:
                        s = (x2c - x1c) / dy
                        curr = [int(x1c + s * (ny1 - y1c)), ny1, int(x1c + s * (ny2 - y1c)), ny2]
                    else:
                        curr = [x1c, ny1, x2c, ny2]
                else:
                    merged.append(tuple(curr))
                    curr = list(line)
        merged.append(tuple(curr))
        return merged

    h_groups = {}
    for x1, y1, x2, y2 in lines_h:
        dx = x2 - x1
        slope = (y2 - y1) / dx if abs(dx) > 1e-6 else 0.0
        intercept = y1 - slope * x1
        key = (round(slope * 100), round(intercept / 10) * 10)
        h_groups.setdefault(key, []).append((x1, y1, x2, y2))
    mh = []
    for g in h_groups.values():
        mh.extend(merge_group(g, True))

    v_groups = {}
    for x1, y1, x2, y2 in lines_v:
        dy = y2 - y1
        inv_s = (x2 - x1) / dy if abs(dy) > 1e-6 else 999.0
        intercept = x1 - inv_s * y1 if abs(dy) > 1e-6 else x1
        key = (round(inv_s * 100), round(intercept / 10) * 10)
        v_groups.setdefault(key, []).append((x1, y1, x2, y2))
    mv = []
    for g in v_groups.values():
        mv.extend(merge_group(g, False))
    return mh, mv


def intersect(l1, l2):
    x1, y1, x2, y2 = l1
    x3, y3, x4, y4 = l2
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-10:
        return None
    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denom
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denom
    return (px, py)


def blue_in_quad(tl, tr, br, bl, blue_mask):
    pts = np.array([tl, tr, br, bl], np.int32)
    mask = np.zeros(blue_mask.shape, np.uint8)
    cv2.fillPoly(mask, [pts], 255)
    return ((mask > 0) & (blue_mask > 0)).sum()


def is_inside_blue(line, blue_mask, sw, sh, edge_type):
    x1, y1, x2, y2 = line
    dx = x2 - x1
    dy = y2 - y1
    L = np.sqrt(dx * dx + dy * dy)
    if L < 1:
        return False

    if edge_type == 'top':
        nx, ny = 0, 1
    elif edge_type == 'bottom':
        nx, ny = 0, -1
    elif edge_type == 'left':
        nx, ny = 1, 0
    else:
        nx, ny = -1, 0

    n_samples = 8
    inside_ct = 0
    outside_ct = 0
    valid = 0
    for i in range(n_samples):
        t = i / (n_samples - 1)
        px = int(x1 + t * dx)
        py = int(y1 + t * dy)
        ix = int(px + nx * 5)
        iy = int(py + ny * 5)
        ox = int(px - nx * 5)
        oy = int(py - ny * 5)
        ib = 0
        ob = 0
        for di in range(-2, 3):
            for dj in range(-2, 3):
                ii, ij = ix + di, iy + dj
                oi, oj = ox + di, oy + dj
                if 0 <= ii < sw and 0 <= ij < sh and blue_mask[ij, ii]:
                    ib += 1
                if 0 <= oi < sw and 0 <= oj < sh and blue_mask[oj, oi]:
                    ob += 1
        if ib + ob > 0:
            inside_ct += ib
            outside_ct += ob
            valid += 1
    if valid < 3:
        return False
    return inside_ct > outside_ct


def in_center(x1, y1, x2, y2, sw, sh):
    for t in np.linspace(0, 1, 20):
        x = int(x1 + t * (x2 - x1))
        y = int(y1 + t * (y2 - y1))
        if sw * 0.25 <= x <= sw * 0.75 and sh * 0.25 <= y <= sh * 0.75:
            return True
    return False


CASE_LO = (5, 5, 5)
CASE_HI = (50, 50, 50)


def main():
    for fpath in sorted(DATA_DIR.glob("*.jpg")):
        img = cv2.imread(str(fpath))
        h, w = img.shape[:2]
        dw = 1024
        s = dw / w
        small = cv2.resize(img, (dw, int(h * s)))
        sh, sw = small.shape[:2]

        blue = in_range(small, CASE_LO, CASE_HI)
        blue_mask = blue.astype(np.uint8) * 255
        edges = cv2.Canny(blue_mask, 50, 150)
        k = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        edges_d = cv2.dilate(edges, k, iterations=1)
        lines = cv2.HoughLinesP(edges_d, 1, np.pi / 180, threshold=40,
                                minLineLength=int(sw * 0.05), maxLineGap=30)
        if lines is None:
            continue
        lines = lines.reshape(-1, 4)

        lh = []
        lv = []
        for x1, y1, x2, y2 in lines:
            dx, dy = abs(x2 - x1), abs(y2 - y1)
            if dx < 1e-6 and dy < 1e-6:
                continue
            if in_center(x1, y1, x2, y2, sw, sh):
                continue
            angle = abs(np.arctan2(dy, dx) * 180 / np.pi)
            if angle < 30 or angle > 150:
                lh.append((x1, y1, x2, y2))
            elif 60 < angle < 120:
                lv.append((x1, y1, x2, y2))

        mh, mv = merge_lines(lh, lv)
        long_h = [l for l in mh if abs(l[2] - l[0]) > sw * 0.40]
        long_v = [l for l in mv if abs(l[3] - l[1]) > sh * 0.40]

        long_h_f = [l for l in long_h if is_inside_blue(l, blue_mask, sw, sh,
                    'top' if (l[1] + l[3]) / 2 < sh / 2 else 'bottom')]
        long_v_f = [l for l in long_v if is_inside_blue(l, blue_mask, sw, sh,
                    'left' if (l[0] + l[2]) / 2 < sw / 2 else 'right')]

        top_c = [l for l in long_h_f if (l[1] + l[3]) / 2 < sh * 0.45]
        bot_c = [l for l in long_h_f if (l[1] + l[3]) / 2 > sh * 0.55]
        left_c = [l for l in long_v_f if (l[0] + l[2]) / 2 < sw * 0.45]
        right_c = [l for l in long_v_f if (l[0] + l[2]) / 2 > sw * 0.55]

        img_top = (0, 0, sw, 0)
        img_bot = (0, sh, sw, sh)
        img_lft = (0, 0, 0, sh)
        img_rgt = (sw, 0, sw, sh)
        if not top_c:
            top_c = [img_top]
        if not bot_c:
            bot_c = [img_bot]
        if not left_c:
            left_c = [img_lft]
        if not right_c:
            right_c = [img_rgt]

        total_blue = blue.sum()
        best = None
        best_blue = 0
        best_info = ''

        for top, bot, left, right in product(top_c, bot_c, left_c, right_c):
            tl = intersect(top, left)
            tr = intersect(top, right)
            br = intersect(bot, right)
            bl = intersect(bot, left)
            if tl is None or tr is None or br is None or bl is None:
                continue
            pts_a = np.array([tl, tr, br, bl], np.float32).reshape(-1, 1, 2)
            area = cv2.contourArea(pts_a)
            area_pct = area / (sw * sh) * 100
            if area_pct < 55 or area_pct > 85:
                continue
            n_blue = blue_in_quad(tl, tr, br, bl, blue_mask)
            if n_blue > best_blue:
                best_blue = n_blue
                best = [tl, tr, br, bl]
                best_info = 'area=%.0f%% blue=%.0f/%d=%.1f%%' % (
                    area_pct, n_blue, total_blue,
                    n_blue / max(total_blue, 1) * 100,
                )

        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        vis = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        vis[blue_mask > 0] = (255, 0, 0)
        cv2.rectangle(vis, (int(sw * .25), int(sh * .25)),
                      (int(sw * .75), int(sh * .75)), (0, 0, 255), 1)
        for l in long_h:
            cv2.line(vis, (l[0], l[1]), (l[2], l[3]), (128, 128, 0), 1, cv2.LINE_AA)
        for l in long_v:
            cv2.line(vis, (l[0], l[1]), (l[2], l[3]), (128, 0, 128), 1, cv2.LINE_AA)
        for l in long_h_f:
            cv2.line(vis, (l[0], l[1]), (l[2], l[3]), (0, 255, 255), 2, cv2.LINE_AA)
        for l in long_v_f:
            cv2.line(vis, (l[0], l[1]), (l[2], l[3]), (255, 0, 255), 2, cv2.LINE_AA)
        if best is not None:
            pts = np.array(best, np.int32)
            cv2.polylines(vis, [pts], True, (0, 255, 0), 2)
            inv = 1.0 / s
            cv2.putText(vis, best_info, (10, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
            cv2.putText(vis,
                        f'H:{len(long_h)}->{len(long_h_f)} V:{len(long_v)}->{len(long_v_f)}',
                        (10, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            print(f'{fpath.name}: H={len(long_h)}->{len(long_h_f)} '
                  f'V={len(long_v)}->{len(long_v_f)}  {best_info}')
            print(f'  orig TL=({best[0][0]*inv:.0f},{best[0][1]*inv:.0f}) '
                  f'BR=({best[2][0]*inv:.0f},{best[2][1]*inv:.0f})')
        else:
            cv2.putText(vis, 'NO OPTIMAL QUAD', (10, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            print(f'{fpath.name}: H={len(long_h)}->{len(long_h_f)} '
                  f'V={len(long_v)}->{len(long_v_f)}  NO QUAD')

        vis_out = cv2.resize(vis, (1200, int(1200 * sh / sw)))
        cv2.imwrite(str(OUT_DIR / f'{fpath.stem}_optimal.jpg'), vis_out)
        print()


if __name__ == "__main__":
    main()
