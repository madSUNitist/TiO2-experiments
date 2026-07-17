#!/usr/bin/env python3
"""Build full_report.pdf with optional scripts/ appendix images."""
import subprocess
import sys
from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = DOCS_DIR / "scripts"
INCLUDE_FILE = DOCS_DIR / "scripts-images.typ"
TYP_FILE = DOCS_DIR / "full_report.typ"
OUTPUT_PDF = DOCS_DIR / "full_report.pdf"

image_files = sorted(SCRIPTS_DIR.glob("*.jpg")) if SCRIPTS_DIR.is_dir() else []
lines = []
for f in image_files:
    lines.append(f'#image("./scripts/{f.name}")')

INCLUDE_FILE.write_text("\n".join(lines), encoding="utf-8")

subprocess.run(
    ["typst", "compile", "--root", str(DOCS_DIR.parent), str(TYP_FILE), str(OUTPUT_PDF)],
    check=True,
)
print(f"Built: {OUTPUT_PDF}")
