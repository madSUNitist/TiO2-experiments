"""XRD data processing: baseline correction, smoothing, peak detection."""

from __future__ import annotations

import numpy as np
from scipy.signal import savgol_filter
from scipy.sparse import spdiags
from scipy.sparse.linalg import spsolve

from .config import (
    ANATASE_REF, RUTILE_REF, CONFIG,
    SCHERRER_K, WAVELENGTH_NM, INSTRUMENTAL_FWHM_DEG,
)


def als_baseline(
    y: np.ndarray,
    lam: float = 1e6,
    p: float = 0.001,
    niter: int = 10,
) -> tuple[np.ndarray, np.ndarray]:
    """Asymmetric Least Squares baseline correction.

    Returns (baseline, corrected).
    """
    L = len(y)
    diags_data = np.array([np.ones(L), -2 * np.ones(L), np.ones(L)])
    D2 = spdiags(diags_data, np.array([0, 1, 2]), L, L - 2)
    D = D2.dot(D2.transpose()).tocsc()
    w = np.ones(L)
    z = y.copy()
    for _ in range(niter):
        W = spdiags(w, 0, L, L, format="csc")
        Z = W + lam * D
        z = spsolve(Z, w * y)
        w = np.where(y > z, p, 1.0 - p)
    return z, y - z


def process_data(intensity: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """ALS baseline -> Savitzky-Golay smooth.

    Returns (smoothed_baseline_corrected, baseline).
    """
    baseline, corrected = als_baseline(
        intensity,
        lam=CONFIG["baseline_lam"],
        p=CONFIG["baseline_p"],
        niter=CONFIG["baseline_niter"],
    )
    window = CONFIG["sg_window"]
    if window % 2 == 0:
        window += 1
    if len(corrected) <= window:
        window = max(5, len(corrected) // 2 * 2 + 1)
    smoothed = savgol_filter(corrected, window, CONFIG["sg_polyorder"])
    return smoothed, baseline


def find_local_peak(
    ref_tt: float,
    two_theta: np.ndarray,
    smoothed: np.ndarray,
) -> tuple[float, float] | None:
    """Find the real local maximum near a reference 2θ.

    Returns (actual_2theta, intensity) or None.
    """
    n_window = CONFIG["local_search_window"]
    w_window = CONFIG["local_base_window"]

    lo, hi = ref_tt - n_window, ref_tt + n_window
    mask = (two_theta >= lo) & (two_theta <= hi)
    if not mask.any() or mask.sum() < 3:
        return None
    n_indices = np.flatnonzero(mask)
    n_start, n_end = int(n_indices[0]), int(n_indices[-1])
    local_n = smoothed[n_start:n_end + 1]
    i_peak = int(np.argmax(local_n))
    if i_peak == 0 or i_peak == n_end - n_start:
        return None
    global_idx = n_start + i_peak
    peak_h = float(smoothed[global_idx])

    w_lo, w_hi = ref_tt - w_window, ref_tt + w_window
    w_lo = max(w_lo, two_theta[0])
    w_hi = min(w_hi, two_theta[-1])
    mask_w = (two_theta >= w_lo) & (two_theta <= w_hi)
    w_indices = np.flatnonzero(mask_w)
    w_start, w_end = int(w_indices[0]), int(w_indices[-1])
    if w_end - w_start < 3:
        return None

    left_min = float(np.min(smoothed[w_start:global_idx])) if global_idx > w_start else peak_h
    right_min = float(np.min(smoothed[global_idx + 1:w_end + 1])) if global_idx < w_end else peak_h
    prominence = peak_h - max(left_min, right_min)

    wide_range = float(np.max(smoothed[w_start:w_end + 1]) - np.min(smoothed[w_start:w_end + 1]))
    if wide_range <= 0:
        return None
    if prominence < wide_range * CONFIG["local_prominence_min"]:
        return None

    return float(two_theta[global_idx]), peak_h


def estimate_phase_composition(
    two_theta: np.ndarray, intensity: np.ndarray,
) -> tuple[float, float, str]:
    """Estimate Anatase/Rutile ratio using Spurr-Myers formula."""

    def _peak_height(center: float, width: float = 0.15) -> float:
        mask = (two_theta >= center - width) & (two_theta <= center + width)
        if not mask.any():
            return 0.0
        return float(np.max(intensity[mask]))

    i_a = _peak_height(ANATASE_REF["(101)"])
    i_r = _peak_height(RUTILE_REF["(110)"])

    if i_a > 0 and i_r > 0:
        anatase_pct = round(100.0 / (1.0 + 1.26 * i_r / i_a), 1)
        rutile_pct = round(100.0 - anatase_pct, 1)
        return anatase_pct, rutile_pct, ""
    elif i_a > 0:
        return 100.0, 0.0, "pure Anatase"
    elif i_r > 0:
        return 0.0, 100.0, "pure Rutile"
    else:
        return 0.0, 0.0, "no characteristic peaks detected"


def estimate_phase_composition_nnls(
    two_theta: np.ndarray,
    intensity: np.ndarray,
    tt_anatase: np.ndarray,
    intens_anatase: np.ndarray,
    tt_rutile: np.ndarray,
    intens_rutile: np.ndarray,
    *,
    fwhm: float = 1.0,
    tt_mask: tuple[float, float] = (20.0, 65.0),
) -> tuple[float, float, float, str]:
    """Estimate Anatase/Rutile ratio via NNLS full-pattern decomposition.

    Broadens CIF-derived stick peaks onto the experimental 2θ grid,
    then solves  y_exp ≈ w_a·y_anatase + w_r·y_rutile  via non-negative
    least squares (scipy.optimize.nnls).

    Returns (anatase_pct, rutile_pct, r_squared, status).
    """
    from scipy.optimize import nnls

    sigma = fwhm / (2 * np.sqrt(2 * np.log(2)))

    def _broaden(tt_peaks, intens_peaks):
        y = np.zeros_like(two_theta, dtype=np.float64)
        for pos, iv in zip(tt_peaks, intens_peaks):
            y += iv * np.exp(-0.5 * ((two_theta - pos) / sigma) ** 2)
        return y

    y_a = _broaden(tt_anatase, intens_anatase)
    y_r = _broaden(tt_rutile, intens_rutile)

    mask = (two_theta >= tt_mask[0]) & (two_theta <= tt_mask[1])
    if mask.sum() < 10:
        return 0.0, 0.0, 0.0, "mask too narrow"

    y_exp_m = intensity[mask]
    y_a_m = y_a[mask]
    y_r_m = y_r[mask]

    y_a_n = y_a_m / np.max(y_a_m) if np.max(y_a_m) > 0 else y_a_m
    y_r_n = y_r_m / np.max(y_r_m) if np.max(y_r_m) > 0 else y_r_m
    y_exp_n = y_exp_m / np.max(y_exp_m) if np.max(y_exp_m) > 0 else y_exp_m

    A = np.column_stack([y_a_n, y_r_n])
    w, _residual_norm = nnls(A, y_exp_n)
    w_a, w_r = float(w[0]), float(w[1])

    if w_a + w_r > 1e-10:
        anatase_pct = round(100.0 * w_a / (w_a + w_r), 1)
        rutile_pct = round(100.0 * w_r / (w_a + w_r), 1)
    elif w_a > 0:
        anatase_pct, rutile_pct = 100.0, 0.0
    elif w_r > 0:
        anatase_pct, rutile_pct = 0.0, 100.0
    else:
        return 0.0, 0.0, 0.0, "NNLS failed"

    y_recon = A @ w
    ss_res = np.sum((y_exp_n - y_recon) ** 2)
    ss_tot = np.sum((y_exp_n - np.mean(y_exp_n)) ** 2)
    r_squared = round(float(1.0 - ss_res / ss_tot) if ss_tot > 0 else 0.0, 4)

    status = ""
    return anatase_pct, rutile_pct, r_squared, status


def measure_fwhm(
    peak_tt: float,
    two_theta: np.ndarray,
    smoothed: np.ndarray,
    *,
    search_window: float | None = None,
) -> float | None:
    """Measure FWHM of a peak centred at peak_tt on baseline-corrected data.

    Uses linear interpolation to locate the half-maximum crossings.
    Returns FWHM in degrees, or None if the measurement fails.
    """
    if search_window is None:
        search_window = CONFIG["local_base_window"]

    lo, hi = peak_tt - search_window, peak_tt + search_window
    mask = (two_theta >= lo) & (two_theta <= hi)
    if mask.sum() < 5:
        return None
    indices = np.flatnonzero(mask)
    start, end = int(indices[0]), int(indices[-1])

    segment = smoothed[start:end + 1]
    tt_seg = two_theta[start:end + 1]

    i_peak = int(np.argmax(segment))
    if i_peak == 0 or i_peak == end - start:
        return None
    peak_h = float(segment[i_peak])

    half_h = peak_h / 2.0

    left_tt = _interp_crossing(tt_seg, segment, half_h, i_peak, direction=-1)
    right_tt = _interp_crossing(tt_seg, segment, half_h, i_peak, direction=+1)

    if left_tt is None or right_tt is None:
        return None

    return right_tt - left_tt


def _interp_crossing(
    tt: np.ndarray,
    y: np.ndarray,
    threshold: float,
    i_peak: int,
    *,
    direction: int,
) -> float | None:
    """Find the 2θ value where y crosses threshold by linear interpolation.

    direction: -1 for left side, +1 for right side.
    """
    n = len(y)
    i = i_peak
    while 0 <= i + direction < n:
        a, b = i, i + direction
        if (y[a] - threshold) * (y[b] - threshold) <= 0:
            if abs(y[b] - y[a]) < 1e-12:
                return float((tt[a] + tt[b]) / 2.0)
            frac = (threshold - y[a]) / (y[b] - y[a])
            return float(tt[a] + frac * (tt[b] - tt[a]))
        i += direction
    return None


def scherrer_size(fwhm_deg: float, peak_tt_deg: float) -> float:
    """Calculate crystallite size via the Scherrer equation.

    D = K * lambda / (beta * cos(theta))

    Parameters
    ----------
    fwhm_deg : float   measured FWHM in degrees (2θ)
    peak_tt_deg : float peak position in degrees (2θ)

    Returns
    -------
    float   crystallite size in nanometres
    """
    import math

    beta_deg = math.sqrt(
        max(0.0, fwhm_deg**2 - INSTRUMENTAL_FWHM_DEG**2)
    )
    beta_rad = math.radians(beta_deg)
    theta_rad = math.radians(peak_tt_deg / 2.0)

    cos_theta = math.cos(theta_rad)
    if cos_theta <= 0:
        return 0.0

    size_nm = SCHERRER_K * WAVELENGTH_NM / (beta_rad * cos_theta)
    return size_nm
