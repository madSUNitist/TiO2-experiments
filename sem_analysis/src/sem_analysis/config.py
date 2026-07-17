"""Centralised configuration for SEM image analysis."""

from __future__ import annotations

HOMOGRAPHY: dict = {
    # --- blue-mask line detection ---
    "downscale_max_width": 1024,
    "long_ratio": 0.30,
    "cand_split": 0.45,
    "area_min": 55,
    "area_max": 85,
    # --- output ---
    "target_width": 1920,
}

SCALE_BAR: dict = {
    "search_region_fraction": 0.12,    # search bottom 12% of image
    "min_bar_length_ratio": 0.08,      # bar must span >8% of width
    "manual_scale_nm_per_px": 0.0,     # set >0 to override auto-detection
    "expected_units": ["nm", "μm", "um", "mm"],
}

PREPROCESS: dict = {
    "clahe_clip_limit": 2.0,
    "clahe_tile_size": (8, 8),
    "bilateral_d": 7,
    "bilateral_sigma_color": 50,
    "bilateral_sigma_space": 50,
    "crop_margin_pct": 0.02,           # crop 2% from edges (remove SEM UI)
}

SEGMENT: dict = {
    "adaptive_block_size": 51,         # must be odd
    "adaptive_C": 5,
    "morph_close_iters": 2,
    "morph_open_iters": 2,
    "morph_kernel_size": 3,
    "min_object_area_px": 20,          # ignore objects smaller than this
    "watershed_footprint_radius": 5,   # local-max search radius
    "watershed_min_distance": 8,       # min px between markers
}

FILTER: dict = {
    "circularity_min": 0.15,           # reject overly irregular shapes
    "solidity_min": 0.55,              # reject hollow/porous objects
    "max_relative_area": 8.0,          # reject objects >8× median area (agglomerates)
    "aspect_ratio_max": 4.0,           # reject very elongated objects
}

MEASURE: dict = {
    "feret_angles": 36,               # number of angles for Feret sweep
}

STATS: dict = {
    "percentiles": [10, 25, 50, 75, 90],
}

VISUALIZE: dict = {
    "figsize_annotated": (16, 10),
    "figsize_histogram": (10, 6),
    "dpi": 200,
    "particle_outline_color": (0, 255, 0),
    "agglomerate_outline_color": (255, 0, 0),
    "particle_label_color": (0, 200, 0),
    "histogram_color": "#2166ac",
    "histogram_bins": 40,
}
