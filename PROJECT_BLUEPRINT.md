# Wooded Area Mapping — Project Blueprint

High-level architecture and structure of the **wooded-area-mapping** codebase.

---

## 1. Purpose & Goals

- **Output**: Binary maps (wooded = 1, non-wooded = 0) from PlanetScope 3B Analytic MS Surface Reflectance imagery.
- **Method**: Generalizable U-Net trained on multiple manually labeled scenes, with optional vegetation indices (NDVI, EVI) and temporal features.
- **Deployment**: Cloud-first (GCS + VM/Colab), with local paths for testing.

---

## 2. Data Model

### Inputs (per scene)

| Asset | Description |
|-------|-------------|
| `*_3B_AnalyticMS_SR.tif` | Multispectral image (B, G, R, NIR) |
| `*_3B_udm2.tif` | Usable Data Mask (cloud, shadow, invalid) |
| `*_metadata.json` / `*_metadata.xml` | Metadata (optional; used for cloud % when available) |
| `*_reference_wooded.tif` | Manual labels (1=wooded, 0=non-wooded, NoData=unlabeled) — required for training / metrics |

### GCS layout (recommended)

```
gs://<bucket>/<prefix>/
  <scene_id>_3B_AnalyticMS_SR.tif
  <scene_id>_3B_udm2.tif
  <scene_id>_metadata.json
  <scene_id>_reference_wooded.tif   # after labeling
```

### Outputs

- **Prediction**: Single-band GeoTIFF, same extent/CRS as input. Values: `1` = wooded, `0` = non-wooded, `255` = NoData (masked).
- **Model checkpoint**: `.pt` file with `state_dict`, `patch_size`, `n_channels`, etc.

---

## 3. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FEATURE ENGINEERING                                 │
│  compute_features.py: B,G,R,NIR → NDVI, EVI (optional SAVI, NDWI)             │
│  compute_temporal_features.py: timeseries → mean/max/min/std NDVI, doy       │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  model_unet.py — U-Net                                                        │
│  Configurable in_channels (4, 6, or 9+ with temporal). base=32, 3 levels.    │
└─────────────────────────────────────────────────────────────────────────────┘
         │                                              │
         ▼                                              ▼
┌──────────────────────┐                    ┌──────────────────────┐
│  TRAINING             │                    │  INFERENCE           │
│  Multi-scene patches  │                    │  Sliding window      │
│  (MultiScenePatchDataset)                  │  + UDM2 → NoData     │
│  BCE + valid mask     │                    │  Optional metrics    │
└──────────────────────┘                    └──────────────────────┘
```

- **Training**: Load multiple scenes (local or GCS), compute features per scene, sample random patches from all scenes, train U-Net (BCE, masked). Implemented in `train_wooded_multi_scene.py` (local) and `train_wooded_multi_scene_gcs.py` (GCS).
- **Inference**: Load image (+ optional feature computation), run U-Net in patches, apply UDM2 as NoData, write GeoTIFF. Optionally compare to `*_reference_wooded.tif` and run `accuracy_metrics.py`.

---

## 4. Script Inventory

### Core (multi-scene DL workflow)

| Script | Role |
|--------|------|
| `model_unet.py` | U-Net definition (imported by train/predict). |
| `compute_features.py` | Vegetation indices from SR bands; used by training and prediction when `n_channels > 4`. |
| `train_wooded_multi_scene.py` | Multi-scene training (local paths). |
| `train_wooded_multi_scene_gcs.py` | Multi-scene training (GCS; can auto-detect scenes with reference rasters). |
| `predict_wooded_dl.py` | Single-scene inference (local); can compute metrics if reference present. |
| `predict_wooded_batch_gcs.py` | Batch inference on GCS scenes; optional `--compute-metrics`. |
| `compute_temporal_features.py` | Temporal stats from timeseries (for extra channels). |
| `accuracy_metrics.py` | Compare predicted vs reference raster (confusion matrix, accuracy, precision, recall, F1, Kappa). |
| `gcs_utils.py` | GCS client, list scenes, download/stream rasters (used by GCS training/inference). |

### Utilities & data prep

| Script | Role |
|--------|------|
| `download_one_sample.py` | Download one scene from Google Drive (legacy). |
| `download_scenes_for_labeling.py` | Get scenes from GCS for labeling. |
| `list_timeseries_dates.py` | List dates/timeseries for a scene or bucket. |
| `rank_scenes.py` | Rank scenes by clear % and mean NDVI (choose “best” image). |

### Legacy (single-image / NDVI proxy)

| Script | Role |
|--------|------|
| `wooded_map_single_image.py` | NDVI thresholding, single image, no model. |
| `train_wooded_dl.py` | Single-scene training with NDVI proxy labels (legacy). |

---

## 5. Dependencies

- **Python**: 3.7+
- **Core**: `numpy`, `rasterio`, `torch`
- **Cloud**: `google-cloud-storage`, `google-cloud-auth`
- **Utils**: `gdown` (Drive download)

See `requirements.txt`.

---

## 6. Workflow Phases (summary)

1. **Labeling** — Define “wooded” (see `WOODED_AREA_DEFINITION.md`). Label 3–10 scenes; produce `*_reference_wooded.tif` per scene.
2. **Training** — Run `train_wooded_multi_scene.py` (local) or `train_wooded_multi_scene_gcs.py` (GCS); output `.pt` model.
3. **Inference** — Run `predict_wooded_dl.py` (single) or `predict_wooded_batch_gcs.py` (batch); optional metrics via reference rasters.
4. **Evaluation** — Use `accuracy_metrics.py` when reference is available.

---

## 7. Key Documentation

| Document | Content |
|----------|---------|
| `README.md` | Main usage, workflow, script reference. |
| `WOODED_AREA_DEFINITION.md` | Definition of “wooded” and labeling guidelines. |
| `GETTING_STARTED.md` | Step-by-step workflow. |
| `BEFORE_YOU_PROCEED.md` | Project/bucket/VM cost checks. |
| `vm_workflow.md` | GCP VM setup and run. |
| `RE_RASTERIZE_CHECKLIST.md` | Rasterize/labeling checklist. |
| `PROJECT_BLUEPRINT.md` | This file — high-level project structure. |

---

## 8. Conventions

- **Scene ID**: e.g. `20240110_162648_67_247d`; used to match SR, UDM2, metadata, and reference files.
- **Channels**: Default 6 (B, G, R, NIR, NDVI, EVI). Can be 4 (bands only) or 9+ with temporal features; must match between training and inference.
- **NoData**: Prediction uses 255 where UDM2 or invalid; reference uses NoData for unlabeled. Metrics ignore NoData / invalid.
