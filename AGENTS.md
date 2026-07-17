# AGENTS.md — TiO2 Chemistry Experiments

## Architecture

This is NOT a uv workspace. Each of the 4 packages is an **independent uv project**
with its own `.venv` and `uv.lock`. You must `cd` into each directory and run
`uv sync` separately.

```
sem_analysis/          library (no CLI) — SEM image homography, segmentation, measurement
sem_pipeline/          CLI pipeline — depends on sem_analysis (editable path dep)
xrd_pipeline/          CLI pipeline — standalone XRD phase ID + plotting
degradation_pipeline/  CLI pipeline — standalone RhB degradation kinetics
```

The **only cross-package dependency** is `sem_pipeline → sem_analysis`.

## Commands

### Setup (run in each package dir)
```bash
cd <pkg> && uv sync
```

### Run pipelines
```bash
cd sem_pipeline && uv run sem-pipeline              # batch all images
cd sem_pipeline && uv run sem-pipeline --image 01   # single image
cd sem_pipeline && uv run sem-pipeline cumulative   # cumulative ECD plot

cd xrd_pipeline && uv run xrd-pipeline              # batch all samples
cd xrd_pipeline && uv run xrd-pipeline --diagnose sample_01

cd degradation_pipeline && uv run degradation-pipeline
```

### Run the only test
```bash
cd sem_pipeline && uv run python tests/test_homography.py
```

### Interactive tools (sem_pipeline)
```bash
cd sem_pipeline && uv run python tools/viewer.py
cd sem_pipeline && uv run python tools/calib_bar.py
cd sem_pipeline && uv run python tools/optimize.py
```

### sem_analysis (library, no CLI entrypoints)
```bash
cd sem_analysis && uv run python -m sem_analysis.annotator <image.jpg>
cd sem_analysis && uv run python -m sem_analysis.train_scorer
```

## Gotchas

- **No test framework, no CI, no lint config.** The only meaningful test is
  `sem_pipeline/tests/test_homography.py` (a standalone script, not pytest).

- **Aliyun PyPI mirror** is the default index in every `pyproject.toml`. If
  packages fail to resolve, the mirror may need adjustment.

- **All pipelines use `matplotlib.use("Agg")`** for headless rendering.
  Interactive tools use OpenCV windows instead.

- **degradation_pipeline has hardcoded data** in `kinetics.py`. The `data/`
  directory is empty. No input files needed.

- **XRD only parses Rigaku `.txt` format.** `.mdi` files in `xrd_pipeline/data/`
  are ignored.

- **Image scale factors are hardcoded** in `sem_pipeline/src/sem_pipeline/config.py`
  and `sem_analysis/src/sem_analysis/scale_bar.py`. Adding new SEM images requires
  updating both.

- **Output directories** (`*/output/`) are gitignored — all outputs are
  regeneratable by re-running the pipelines.

- **Python >= 3.13** required (`.python-version` says `3.13`).

- **Docs are in Chinese**: `docs/SEM_report.md` and `docs/XRD_report.md`.
