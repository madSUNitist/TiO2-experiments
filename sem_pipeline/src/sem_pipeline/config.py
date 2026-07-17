"""SEM pipeline configuration."""

from pathlib import Path

_PKG = Path(__file__).resolve().parent.parent.parent
DATA_DIR = _PKG / "data"
OUTPUT_DIR = _PKG / "output"

OUTPUT_SUBDIRS = {
    "corrected": OUTPUT_DIR / "corrected",
    "annotated": OUTPUT_DIR / "annotated",
    "histograms": OUTPUT_DIR / "histograms",
    "data": OUTPUT_DIR / "data",
}

SCALE: dict[str, float] = {
    "01": 3000 / 165,
    "02": 3000 / 166,
    "03": 3000 / 166,
    "06": 5000 / 148.6,
    "07": 5000 / 161,
    "08": 5000 / 162,
    "09": 5000 / 134,
    "11": 5000 / 145,
    "12": 5000 / 144,
}

STACK_GROUPS: list[tuple[str, list[str]]] = [
    ("01-03", ["01", "02", "03"]),
    ("06", ["06"]),
    ("07-08", ["07", "08"]),
    ("09", ["09"]),
    ("11", ["11"]),
    ("12", ["12"]),
]

GROUP_COLORS = ["#2166ac", "#b2182b", "#4daf4a", "#ff7f00", "#984ea3", "#a65628"]

KEYS = list(SCALE.keys())
