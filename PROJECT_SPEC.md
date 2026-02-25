# Project spec: Alabama wooded / tree mapping on GEE

This project focuses on **scale (e.g. whole Alabama), efficient pipelines, GEE, lightweight methods, and a clear novel angle**. Data is free and global (Sentinel-2, Landsat); optional GEDI for height-aware "wooded."

---

## 1. Data & scale choices

| Source | Resolution | Cost | GEE? | Notes |
|--------|------------|------|------|--------|
| **Sentinel-2** | 10m (B2,B3,B4,B8) | Free | ✅ | Good for LULC/forest; seasonal composites often beat simple percentiles. |
| **Landsat 8/9** | 30m | Free | ✅ | Long archive; fusion with GEDI at 30m is standard. |
| **GEDI** | ~25m footprints | Free | ✅ | Canopy height (e.g. RH95); ideal for **height** and fusion with optical. |
| **NLCD Tree Canopy Cover** | 30m | Free | Via MRLC/USFS | % tree cover, CONUS; 2011–2021; good **reference/labels** for Alabama. |
| **USFS/NLCD** | 30m | Free | Download | Tree canopy, land cover; FIA-calibrated models (Landsat + Sentinel-2). |

**Alabama**: NLCD, USFS TCC, and FIA cover Alabama. GEDI covers 52°N–52°S. Sentinel-2 and Landsat are global in GEE.

---

## 2. Novel directions (pick one as main, then extend)

### A. Spatial scale: whole Alabama on GEE

- **Goal**: Map wooded (or tree cover) for **all of Alabama** in GEE; export mosaics (tiled if needed).
- **Data**: Sentinel-2 and/or Landsat in GEE; optional elevation.
- **Method**: Lightweight (e.g. RF or indices + thresholds); pipeline: composite → features → classify → tile → export.
- **Why novel**: End-to-end statewide pipeline on GEE; clear scaling and export strategy.

### B. Temporal dimension

- **Goal**: Use **time series** (phenology, change) rather than single-date imagery.
- **Data**: Sentinel-2 / Landsat composites (seasonal or multi-date metrics) in GEE.
- **Method**: Temporal features (mean/max/min NDVI, date of max, trend) → classifier; or change detection.
- **Why novel**: "Temporal signature" at scale; GEE makes this tractable.

### C. GEDI + optical fusion (height-aware "wooded")

- **Goal**: Use **GEDI canopy height** (e.g. RH95) so "wooded" is height-aware (e.g. trees ≥5 m), not just "green."
- **Data**: GEDI L2A in GEE + Landsat (and/or Sentinel-2) for 30m wall-to-wall prediction.
- **Method**: GEDI as labels or calibration; train (e.g. RF or light DL) on optical + terrain → predict height or binary wooded at 30m; run statewide in GEE.
- **Why novel**: Spaceborne lidar; "trees" vs "any vegetation"; well-documented fusion at 30m.

### D. Other datasets to plug in

- **GEDI**: Tree/canopy height.
- **NLCD / USFS TCC**: Reference labels for training or validation (no hand-labeling Alabama).
- **Elevation / slope**: In GEE; terrain and shadow handling.
- **Land use / boundaries**: Mask urban, water; stratify accuracy.

---

## 3. Scaling & bottlenecks (GEE, export, pipelines)

- **Don't**: Heavy per-scene U-Net on thousands of tiles; manual download/upload.
- **Do**:
  - **Compute in GEE**: Composites, indices, and (if possible) classification on the GEE backend; export only final maps.
  - **Tiled export**: For large areas, export by tiles (e.g. <10k px per side); same CRS/scale; mosaic in post or in GEE.
  - **Lightweight models**: Random forest or simple ML in GEE (or export small samples, train outside); avoid giant DL unless there's a clear novel reason.
  - **Reuse existing products**: NLCD TCC or GEDI-derived height as labels/targets.

---

## 4. Datasets to use (US, especially Alabama)

| Dataset | What it is | Where | Use case |
|---------|------------|--------|----------|
| **NLCD Tree Canopy Cover** | % tree canopy, 30m | [MRLC](https://www.mrlc.gov/data), [USFS](https://data.fs.usda.gov/geodata/rastergateway/treecanopycover/) | Labels, validation |
| **GEDI L2A** | Canopy height (RH metrics) | GEE: `LARSE_GEDI_GEDI02_A_002` | Height target or feature |
| **Global Forest Canopy Height** | 30m height from GEDI+Landsat | [GEE community catalog](https://gee-community-catalog.org/projects/gfch) | Reference or comparison |
| **Sentinel-2** | 10m MS | GEE | Main optical input |
| **Landsat 8/9** | 30m MS | GEE | Alternative or fusion with GEDI |
| **NLCD Land Cover** | Land cover classes | MRLC, GEE | Masking, stratification |
| **FIA** | Plot-level forest inventory | USFS FIA | Validation, calibration |

**Concrete next step**: In GEE, load Alabama boundary; add Sentinel-2, Landsat, GEDI (and optionally NLCD) for a small test region; list assets and resolutions; make one cloud-free composite and one small-tile export. Then decide: **temporal** vs **spatial scale** vs **GEDI fusion** as the main angle.

---

## 5. Use case this project owns

- **Statewide wall-to-wall wooded/tree map for Alabama** using **free, GEE-hosted data** (Sentinel-2 and/or Landsat, optional GEDI), with a **reproducible, tiled pipeline** and **lightweight** method; and/or
- **Height-informed wooded map** (GEDI + optical) so "wooded" ≈ "trees" not "any vegetation"; and/or
- **Temporal woodland product** (e.g. seasonal or change) at state scale.

Pick one as the main novelty (scale vs height vs temporal), then add the others as extensions.

---

## 6. Suggested next steps

1. **Explore in GEE**: Alabama AOI → add Sentinel-2, Landsat, GEDI, (optional) NLCD; one cloud-free composite and one 30m or 10m export for a small tile.
2. **Decide main angle**: (1) Scale (whole Alabama, pipeline, export), (2) Temporal (time series, phenology), or (3) Height (GEDI fusion).
3. **Map the pipeline**: Composite → features (NDVI, EVI, temporal, height if available) → train (e.g. on NLCD TCC or GEDI) → predict → tiled export.
4. **Document**: One-page "Alabama wooded mapping pipeline (GEE)" and a "Datasets we use" table.
5. **Optional**: Draft GEE code for one step (e.g. "Export Alabama by 50km tiles") and a Cursor skill for GEE code style.
