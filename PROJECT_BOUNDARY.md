# Project boundary: what we do and what we don't

Use this to keep the project aligned with the novel direction and to avoid drifting back to older workflows.

---

## What this project DOES

- **Google Earth Engine** as the primary platform (composites, features, export).
- **Sentinel-2 and/or Landsat** as main optical inputs (free, good calibration, global).
- **Alabama** as the target geography (state-level scale).
- **Lightweight methods**: e.g. Random Forest, indices + thresholds, or small ML models; pipeline-first (composite → features → classify → tiled export).
- **Free reference data** where possible: NLCD Tree Canopy Cover, USFS TCC, GEDI (height), FIA for validation.
- **Optional**: GEDI fusion (height-aware "wooded"), temporal features (phenology, change), elevation/slope.

---

## What this project does NOT do

- **PlanetScope** (or other paid commercial 3m) as the primary or only input.
- **Per-scene U-Net** (or similar heavy per-scene DL) as the core workflow.
- **Manual polygon labeling at scale** as the main source of training labels (use NLCD/GEDI instead).
- **Manual download/upload** of thousands of scenes; compute and export from GEE.
- **Single-scene, small-area-only** products without a path to statewide/tiled export.

---

## If you're unsure

Ask: "Does this rely on GEE + free global data + Alabama scale + lightweight pipeline?" If yes, it's in scope. If it depends on Planet, per-scene DL, or hand-labeling at scale, treat it as out of scope for this project.
