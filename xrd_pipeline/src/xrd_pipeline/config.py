"""XRD pipeline configuration."""

from pathlib import Path

_PKG = Path(__file__).resolve().parent.parent.parent
DATA_DIR = _PKG / "data"
OUTPUT_DIR = _PKG / "output"
REFS_DIR = _PKG.parent / "docs" / "refs"

# Simulated reference peak positions (CIF-derived via pymatgen, Cu Kα 10°–80°)
ANATASE_REF = {
    "(101)": 25.32,
    "(103)": 36.98,
    "(004)": 37.82,
    "(112)": 38.60,
    "(200)": 48.08,
    "(105)": 53.93,
    "(211)": 55.11,
    "(213)": 62.16,
    "(204)": 62.74,
    "(116)": 68.82,
    "(220)": 70.35,
    "(215)": 75.12,
    "(301)": 76.10,
}

RUTILE_REF = {
    "(110)": 27.47,
    "(101)": 36.13,
    "(200)": 39.24,
    "(111)": 41.29,
    "(210)": 44.10,
    "(211)": 54.39,
    "(220)": 56.70,
    "(002)": 62.85,
    "(310)": 64.13,
    "(301)": 69.10,
    "(112)": 69.90,
}

# Instrument parameters for simulated patterns
SIM_WAVELENGTH_A = 1.5406
SIM_VOLTAGE_KV = 40.0
SIM_CURRENT_MA = 10.0
SIM_TWO_THETA_RANGE = (10.0, 80.0)

CONFIG: dict = {
    "baseline_lam": 1e6,
    "baseline_p": 0.001,
    "baseline_niter": 10,
    "local_search_window": 0.50,
    "local_base_window": 2.0,
    "local_prominence_min": 0.10,
    "dedup_tolerance": 0.15,
    "sg_window": 7,
    "sg_polyorder": 3,
    "figsize": (18, 6),
    "font_title": 14,
    "font_axis_label": 12,
    "font_tick": 10,
    "font_legend": 8,
    "font_peak_label": 7,
    "font_composition": 9,
}

SCHERRER_K = 0.89
WAVELENGTH_NM = 0.15406
INSTRUMENTAL_FWHM_DEG = 0.01

COLOR_ANATASE = "#2166ac"
COLOR_RUTILE = "#b2182b"
COLOR_PATTERN = "#202020"
COLOR_PEAK = "#333333"
COLOR_BASELINE = "#333333"

PHASE_COLOR = {"Anatase": COLOR_ANATASE, "Rutile": COLOR_RUTILE}
