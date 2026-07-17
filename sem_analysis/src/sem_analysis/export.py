"""CSV data export."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from numpy.typing import NDArray


def export_particles_csv(
    data: dict[str, NDArray],
    output_path: str | Path,
    *,
    image_name: str = "",
) -> None:
    """Save per-particle measurements to CSV."""
    df = pd.DataFrame(data)
    df.insert(0, "image", image_name)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)


def export_summary_csv(
    per_image_stats: dict[str, dict[str, float]],
    overall_stats: dict[str, float],
    output_path: str | Path,
) -> None:
    """Save summary statistics across all images."""
    rows = []
    for name, stats in per_image_stats.items():
        row = {"image": name}
        row.update({k: round(v, 1) for k, v in stats.items()})
        rows.append(row)

    # add overall row
    overall = {"image": "ALL"}
    overall.update({k: round(v, 1) for k, v in overall_stats.items()})
    rows.append(overall)

    df = pd.DataFrame(rows)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
