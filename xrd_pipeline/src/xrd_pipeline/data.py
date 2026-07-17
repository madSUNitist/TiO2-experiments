"""XRD data file parsing."""

from __future__ import annotations

from pathlib import Path

import numpy as np


def parse_xrd_file(filepath: str | Path) -> tuple[np.ndarray, np.ndarray, str]:
    """Parse a Rigaku .txt XRD file. Returns (two_theta, intensity, sample_name)."""
    two_theta: list[float] = []
    intensity: list[float] = []
    sample_name = ""
    in_data = False

    with open(filepath, encoding="utf-8") as fh:
        for line in fh:
            stripped = line.strip()
            if stripped.startswith("Data"):
                sample_name = stripped.split(":")[-1].strip()
                continue
            if stripped.startswith("<2Theta>"):
                in_data = True
                continue
            if in_data:
                parts = stripped.split()
                if len(parts) >= 2:
                    try:
                        two_theta.append(float(parts[0]))
                        intensity.append(float(parts[1]))
                    except ValueError:
                        break
    return np.array(two_theta), np.array(intensity), sample_name


def clean_sample_label(raw: str) -> str:
    """Trim timestamp / hash suffixes from the sample name."""
    return raw.split("#")[0].strip()
