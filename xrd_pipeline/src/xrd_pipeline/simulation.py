"""Load and manage simulated XRD reference patterns.

Patterns are pre-computed via ``tools/simulate_ref.py --export`` and cached as
.npz files in the output directory.  If a cache file is missing the module
falls back to computing the pattern with pymatgen on the fly.

The public API returns discrete peak (2θ, intensity) data for use as
stick patterns in XRD overlay plots.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .config import (
    OUTPUT_DIR, REFS_DIR,
    SIM_WAVELENGTH_A, SIM_TWO_THETA_RANGE,
    SIM_VOLTAGE_KV, SIM_CURRENT_MA,
)

ANATASE_CIF = REFS_DIR / "TiO2-[tI12].cif"
RUTILE_CIF = REFS_DIR / "TiO2-[tP6].cif"
CACHE_ANATASE = OUTPUT_DIR / "TiO2-[tI12]_simulated.npz"
CACHE_RUTILE = OUTPUT_DIR / "TiO2-[tP6]_simulated.npz"

_cache: dict[str, tuple[np.ndarray, np.ndarray]] = {}


def _compute_discrete(cif_path: Path):
    from pymatgen.analysis.diffraction.xrd import XRDCalculator
    from pymatgen.core import Structure

    structure = Structure.from_file(str(cif_path))
    calc = XRDCalculator(wavelength="CuKa", symprec=0.1)
    pattern = calc.get_pattern(structure, two_theta_range=SIM_TWO_THETA_RANGE)
    return pattern.x.astype(np.float64), pattern.y.astype(np.float64)


def _load_discrete(
    cache_path: Path, cif_path: Path, key: str,
) -> tuple[np.ndarray, np.ndarray]:
    if key in _cache:
        return _cache[key]

    if cache_path.exists():
        data = np.load(cache_path)
        tt = data["two_theta"].astype(np.float64)
        intens = data["intensity"].astype(np.float64)
    else:
        tt, intens = _compute_discrete(cif_path)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            cache_path,
            two_theta=tt.astype(np.float32),
            intensity=intens.astype(np.float32),
        )

    _cache[key] = (tt, intens)
    return tt, intens


def get_anatase_peaks() -> tuple[np.ndarray, np.ndarray]:
    """Return (two_theta, intensity) of discrete Anatase reference peaks."""
    return _load_discrete(CACHE_ANATASE, ANATASE_CIF, "anatase")


def get_rutile_peaks() -> tuple[np.ndarray, np.ndarray]:
    """Return (two_theta, intensity) of discrete Rutile reference peaks."""
    return _load_discrete(CACHE_RUTILE, RUTILE_CIF, "rutile")
