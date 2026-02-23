# Novel direction: possibilities map

Notes from boss feedback and next-step options. Focus: **scale (e.g. whole Alabama), efficient pipelines, GEE, lightweight methods, novel angle** — not per-scene U-Net unless we add something new.

---

## 1. What you already have (current project)

- PlanetScope 3m → manual labels → U-Net → binary wooded maps.
- Boss: “heading in the right direction” but wants **more novel/challenging** (e.g. whole Alabama; Landsat/Sentinel; scaling, optimization, lightweight; GEE).

---

## 2. Data & scale choices

| Source | Resolution | Cost | GEE? | Notes |
|--------|------------|------|------|--------|
| **Sentinel-2** | 10m (B2,B3,B4,B8) | Free | ✅ | Good for LULC/forest; seasonal composites often beat simple percentiles. |
| **Landsat 8/9** | 30m | Free | ✅ | Long archive; fusion with GEDI at 30m is standard. |
| **PlanetScope 3m** | 3m | Paid | ❌ in GEE | You already use it; radiometrically ~10m equivalent to Sentinel in some studies. |
| **GEDI** | ~25m footprints | Free | ✅ | Canopy height (e.g. RH95); ideal for **height** and fusion with optical. |
| **NLCD Tree Canopy Cover** | 30m | Free | Via MRLC/USFS | % tree cover, CONUS; 2011–2021; good **reference/labels** for Alabama. |
| **USFS/NLCD** | 30m | Free | Download | Tree canopy, land cover; FIA-calibrated models (Landsat + Sentinel-2). |

**Alabama-specific**: NLCD, USFS TCC, and FIA all cover Alabama. GEDI covers 52°N–52°S (Alabama included). Sentinel-2 and Landsat are global in GEE.

---

## 3. Novel / challenging directions (pick one or combine)

### A. Spatial scale: whole Alabama on GEE

- **Goal**: Map wooded (or tree cover / forest) for **all of Alabama** in GEE; export mosaics (tiled if needed).
- **Data**: Sentinel-2 and/or Landsat in GEE; optional elevation.
- **Method**: Lightweight (e.g. RF or simple indices + thresholds) to avoid heavy DL; focus on **pipeline**: composite → features → classify → tile → export.
- **Why novel**: End-to-end statewide pipeline on GEE; clear scaling and export strategy (tiling, batch tasks); no per-scene manual workflow.

### B. Temporal dimension

- **Goal**: Use **time series** (phenology, change) rather than single-date imagery.
- **Data**: Sentinel-2 / Landsat composites (seasonal or multi-date metrics) in GEE.
- **Method**: Temporal features (e.g. mean/max/min NDVI, date of max, trend) → classifier; or change detection (forest loss/gain).
- **Why novel**: Moves from “one scene” to “temporal signature”; GEE makes this tractable at scale.

### C. GEDI + optical fusion (height-aware “wooded”)

- **Goal**: Use **GEDI canopy height** (e.g. RH95) as target or covariate so “wooded” is height-aware (e.g. trees ≥5 m), not just “green.”
- **Data**: GEDI L2A in GEE + Landsat (and/or Sentinel-2) for 30m wall-to-wall prediction.
- **Method**: GEDI as labels or calibration; train a model (e.g. RF or light DL) on optical + terrain to predict height or binary wooded at 30m; run statewide in GEE.
- **Why novel**: Uses spaceborne lidar; addresses “vegetation vs trees” by bringing in height; well-documented fusion at 30m (e.g. Global Forest Canopy Height, GEDI–Landsat).

### D. Other datasets to plug in

- **GEDI**: Tree/canopy height (best single extra dataset for “forest” vs “low vegetation”).
- **NLCD / USFS TCC**: Use as **reference labels** for training or validation (no need to label Alabama by hand).
- **Elevation / slope**: In GEE; helps with terrain and confusion (e.g. shadows).
- **Land use / boundaries**: To mask urban, water, or to stratify accuracy.

---

## 4. Scaling & bottlenecks (GEE, export, pipelines)

- **Don’t**: Run heavy per-scene U-Net on thousands of tiles; manual download/upload.
- **Do**:
  - **Compute in GEE**: Composites, indices, and (if possible) classification on the GEE backend; only export final maps.
  - **Tiled export**: For large areas, export by tiles (e.g. &lt;10k px per side); same CRS/scale; mosaic in post or in GEE.
  - **Lightweight models**: Random forest or simple ML in GEE (or export small samples and train outside); avoid giant DL unless you have a clear novel reason.
  - **Reuse existing products**: NLCD TCC or GEDI-derived height as labels/targets to avoid labeling whole Alabama by hand.

---

## 5. Datasets to “play with” (US, especially Alabama)

| Dataset | What it is | Where | Use case |
|---------|------------|--------|----------|
| **NLCD Tree Canopy Cover** | % tree canopy, 30m | [MRLC](https://www.mrlc.gov/data), [USFS](https://data.fs.usda.gov/geodata/rastergateway/treecanopycover/) | Labels, validation, “ground truth” wooded |
| **GEDI L2A** | Canopy height (RH metrics) | GEE: `LARSE_GEDI_GEDI02_A_002` | Height target or feature |
| **Global Forest Canopy Height** | 30m height from GEDI+Landsat | [GEE community catalog](https://gee-community-catalog.org/projects/gfch) | Pre-made height; compare or use as reference |
| **Sentinel-2** | 10m MS | GEE | Main optical input for Alabama |
| **Landsat 8/9** | 30m MS | GEE | Alternative or fusion with GEDI |
| **NLCD Land Cover** | Land cover classes | MRLC, GEE | Masking, stratification |
| **FIA** | Plot-level forest inventory | USFS FIA | Validation, calibration (point data) |

**Concrete next step**: In GEE, load Alabama boundary; pull Sentinel-2 + Landsat + GEDI (and optionally NLCD) for a small test region; list assets and resolutions; try one composite and one export (small tile). Then decide: **temporal** vs **spatial scale** vs **GEDI fusion** as the main “novel” angle.

---

## 6. Use case that’s “missing” (to frame the project)

- **Existing**: Single-scene or small-area wooded maps; heavy DL; manual labels only; Planet-only.
- **Missing (what you could own)**:
  - **Statewide wall-to-wall wooded/tree map for Alabama** using **free, GEE-hosted data** (Sentinel-2 and/or Landsat, optional GEDI), with a **reproducible, tiled pipeline** and **lightweight** method; and/or
  - **Height-informed wooded map** (GEDI + optical) so “wooded” is closer to “trees” than “any vegetation”; and/or
  - **Temporal woodland product** (e.g. seasonal or change) at state scale.

Pick one as the “main” novelty (scale vs height vs temporal), then add the others as extensions.

---

## 7. Subagents and skills (Cursor)

- **Subagents**: In Cursor, use the **Task** (or “subagent”) tool to hand off a **clear, self-contained task** (e.g. “List all GEE datasets that contain the word GEDI” or “Draft a one-page GEE export workflow for Alabama”). The subagent runs with its own context; you get a result to fold back into your plan.
- **Skills**: **Skills** are stored instructions (e.g. a `SKILL.md`) that tell the AI how to behave in your project (e.g. “When editing GEE code, always use the JavaScript or Python API doc link”). You already have skills under `.cursor/skills-cursor/` (e.g. create-rule, create-skill). To “learn” them: create a small skill (e.g. “When writing GEE scripts, prefer batch export and tiling for areas &gt; 1M km²”) and invoke it when relevant.

---

## 8. Suggested next steps (short)

1. **Explore in GEE**: Alabama AOI → add Sentinel-2, Landsat, GEDI, (optional) NLCD; make one cloud-free composite and one 30m or 10m export for a small tile.
2. **Decide main angle**: (1) **Scale** (whole Alabama, pipeline, export), (2) **Temporal** (time series, phenology), or (3) **Height** (GEDI fusion).
3. **Map the pipeline**: Composite → features (NDVI, EVI, temporal, height if available) → train (e.g. on NLCD TCC or GEDI) → predict → tiled export.
4. **Document**: One-page “Alabama wooded mapping pipeline (GEE)” and a “Datasets we use” table (this doc is a start).
5. **Optional**: Use a **subagent** to draft GEE code for one step (e.g. “Export Alabama by 50km tiles”) and a **skill** to keep GEE code style consistent.

If you tell me which direction you prefer first (scale vs temporal vs GEDI), I can turn this into a concrete GEE script outline or a one-pager for your boss.
