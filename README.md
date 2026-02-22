# Wooded Area Mapping with Deep Learning

Produce **binary maps** (wooded vs non-wooded) from PlanetScope 3B Analytic MS Surface Reflectance imagery using a generalizable deep learning model trained on multiple manually-labeled scenes.

## Your data

### Cloud Storage (Recommended)

- **GCS Bucket**: Data is hosted in Google Cloud Storage
- **Structure**: `gs://your-bucket/scenes/{scene_id}_3B_AnalyticMS_SR.tif`, `{scene_id}_3B_udm2.tif`, etc.
- **Per scene** you have:
  - `*_3B_AnalyticMS_SR.tif` — multispectral image (B, G, R, NIR)
  - `*_3B_udm2.tif` — Usable Data Mask (cloud, cloud shadow, etc.)
  - `*_metadata.json` / `*_metadata.xml` — metadata
  - `*_reference_wooded.tif` — manual labels (after labeling)

### Local Testing (Legacy)

- **Google Drive**: [2024 - Google Drive](https://drive.google.com/drive/folders/12-tmwMfB5P7AYhsh2yHAPcyYTYfMUIsC?usp=sharing)
- For local testing, you can still download scenes from Google Drive using `download_one_sample.py`

## Workflow Overview

**Primary Workflow**: Multi-scene training with manual labels → Generalizable model → Batch inference

**Deployment**: Cloud-first (GCS + VM/Colab) with local option for testing

---

## Multi-Scene Deep Learning Workflow (Recommended)

### Phase 1: Manual Labeling

**IMPORTANT**: Before labeling, read **[WOODED_AREA_DEFINITION.md](WOODED_AREA_DEFINITION.md)** for the complete definition of "wooded areas" and detailed labeling guidelines.

Label **3-10 scenes** spanning different seasons (e.g., one per season at peak: winter ~Jan–Feb, spring ~Apr–May, summer ~Jul–Aug, fall ~Oct; see **GETTING_STARTED.md** for date ranges).

1. Use high-resolution imagery (Google Earth/Maxar, 0.3-0.7m) as reference
2. Define "wooded" as **trees ≥5m tall** (see definition document for complete criteria)
3. Digitize polygons directly on PlanetScope (3m) or transfer from high-res
4. Rasterize polygons → `{scene_id}_reference_wooded.tif` (1=wooded, 0=non-wooded, NoData=unlabeled)

**Tools**: QGIS, ArcGIS, or web-based (Label Studio, Roboflow)

**Definition Summary**:
- **Include**: Trees ≥5m, forest patches (>10% canopy), tree clusters, orchards (if trees ≥5m)
- **Exclude**: Shrubs (<3m), crops, grassland, urban infrastructure, water bodies
- **Edge cases**: Include tree shadows, exclude cloud shadows (use UDM2), verify height with high-res imagery

**Labeling Coverage Strategy**:
- **Wooded areas**: Aim for **near-full coverage** - label every identifiable wooded patch/polygon
- **Non-wooded areas**: Aim for **representative sampling** (20-70% coverage) of diverse non-wooded types
- **Rationale**: Polygons rasterize to fill areas, so full coverage of wooded areas ensures complete ground truth, while diverse sampling of non-wooded types provides sufficient negative examples

**See [WOODED_AREA_DEFINITION.md](WOODED_AREA_DEFINITION.md) for complete guidelines** including PlanetScope 3m resolution considerations, County Line Road area specifics, labeling examples, quality checks, and detailed coverage strategy.

### Phase 2: Multi-Scene Training

Train a U-Net model on multiple labeled scenes with feature engineering (NDVI, EVI):

**Local Training:**
```bash
python train_wooded_multi_scene.py \
    --scenes-dir ./data \
    --epochs 50 \
    --batch-size 16 \
    --output wooded_model.pt
```

**GCS Training (Recommended):**
```bash
python train_wooded_multi_scene_gcs.py \
    --bucket your-bucket-name \
    --prefix scenes/ \
    --scene-ids 20240110_162648_67_247d 20240415_162648_67_247d \
    --epochs 50 \
    --output wooded_model.pt
```

**Auto-detect scenes with reference rasters:**
```bash
python train_wooded_multi_scene_gcs.py \
    --bucket your-bucket-name \
    --prefix scenes/ \
    --epochs 50 \
    --output wooded_model.pt
```

**Features**: By default, uses 6 channels (B, G, R, NIR, NDVI, EVI). Use `--no-ndvi` or `--no-evi` to exclude indices.

### Phase 3: Batch Inference

Run the trained model on new scenes:

**Single Scene (Local):**
```bash
python predict_wooded_dl.py \
    --image data/20240110_162648_67_247d_3B_AnalyticMS_SR.tif \
    --model wooded_model.pt \
    --udm data/20240110_162648_67_247d_3B_udm2.tif \
    --output wooded_binary.tif
```

**Batch Inference (GCS):**
```bash
python predict_wooded_batch_gcs.py \
    --bucket your-bucket-name \
    --prefix scenes/ \
    --model wooded_model.pt \
    --output-prefix predictions/ \
    --compute-metrics
```

**Output**: Binary GeoTIFF (1=wooded, 0=non-wooded, 255=NoData) with automatic accuracy metrics if reference available.

---

## Feature Engineering

### Vegetation Indices

Compute NDVI, EVI, and other indices:

```bash
python compute_features.py \
    --image data/20240110_162648_67_247d_3B_AnalyticMS_SR.tif \
    --output features.tif
```

**Available indices**: NDVI (default), EVI (default), SAVI (`--savi`), NDWI (`--ndwi`)

### Temporal Features (Timeseries Integration)

Extract temporal statistics from timeseries:

```bash
python compute_temporal_features.py \
    --bucket your-bucket-name \
    --prefix scenes/ \
    --output-dir temporal_features/
```

**Features**: Mean NDVI, Max NDVI, Min NDVI, Std NDVI, Day-of-year for max NDVI

**Integration**: Add temporal features as additional channels (9 channels total: 4 bands + NDVI + EVI + 5 temporal).

---

## Cloud Workflow (GCS + Colab/VM)

### Setup: Start with Free Tier

**Phase 1: Google Colab (Free)**
- **Cost**: $0/month
- **GPU**: Free T4 GPU (with usage limits)
- **Setup**: 
  1. Open [Google Colab](https://colab.research.google.com/)
  2. Enable GPU: Runtime → Change runtime type → GPU (T4)
  3. Install dependencies: `!pip install -r requirements.txt`
  4. Authenticate with GCS: `from google.colab import auth; auth.authenticate_user()`
  5. Upload this repo or clone from GitHub
  6. Run training/inference scripts
- **Limitations**: 12-hour sessions, GPU availability varies, usage quotas

**Phase 2: Upgrade to Paid VM (if needed)**
- **When**: If Colab free is too slow or hits limits
- **GCP VM with GPU**: 
  - T4 GPU: ~$0.35/hour (shut down when not in use)
  - L4 GPU: ~$1/hour (faster, better for large-scale)
- **Setup**: See `vm_workflow.md` for detailed VM setup guide
- **Cost optimization**: Only pay when VM is running; shut down after jobs complete

### VM Setup

1. **Create VM** (see `vm_workflow.md` for details):
   ```bash
   gcloud compute instances create wooded-mapping-vm \
       --zone=us-central1-a \
       --machine-type=n1-standard-4 \
       --accelerator=type=nvidia-tesla-t4,count=1 \
       --image-family=ubuntu-2204-lts \
       --image-project=ubuntu-os-cloud
   ```

2. **SSH and setup**:
   ```bash
   gcloud compute ssh wooded-mapping-vm --zone=us-central1-a
   ./setup_vm.sh
   ```

3. **Configure GCS authentication** (see `vm_workflow.md`)

4. **Run training/inference** (see commands above)

---

## Legacy: Single Image Workflow (NDVI Thresholding)

For quick single-image mapping without training:

### 1. Download one or a few scenes (Legacy)

- **Option A – Manual**: In the Drive folder, pick one scene and download:
  - The `*_3B_AnalyticMS_SR.tif`
  - The matching `*_3B_udm2.tif`  
  (same scene ID, e.g. `20240110_162648_67_247d`).
- **Option B – Command line**: If you use `gdown` (e.g. `pip install gdown`), you can download the folder:
  ```bash
  gdown --folder https://drive.google.com/drive/folders/12-tmwMfB5P7AYhsh2yHAPcyYTYfMUIsC
  ```
  Then move one scene's `.tif` pair into a working folder (e.g. `data/`).

### 2. Choose the "best" image (NDVI + cloud-free)

The folder has scenes from **January to December** (seasonal change). The best image for wooded mapping is:

1. **Cloud-free (or nearly)** — cloud percent close to 0.  
2. **Highest NDVI** — strongest vegetation signal (e.g. leaf-on summer).

**Recommended: rank all scenes locally**

- Download **multiple** scenes (or the whole folder) into one directory (e.g. `data/`).
- Run the ranking script on that directory. It computes **clear %** (from UDM2, and optionally from `*_metadata.json` if present) and **mean NDVI** per scene, then recommends the best:

```bash
# Rank scenes in data/ (clear % and mean NDVI); recommends best scene
python rank_scenes.py data

# Require at least 80% clear pixels; use metadata cloud/clear when available
python rank_scenes.py data --min-clear 80 --use-metadata-cloud
```

- **Clear %**: From UDM2 (valid vs invalid pixels). Optionally, Planet's `*_metadata.json` can contain `cloud_percent` / `clear_percent`; use `--use-metadata-cloud` to prefer those when present.
- **Cloud in metadata**: The TIF's embedded metadata (e.g. in QGIS) often has atmospheric correction only; the separate `*_metadata.json` files (if you download them) may have `cloud_cover` or `cloud_percent`. Use **cloud percent close to 0** where available.
- Use the printed "Recommended" scene for the next step.

### 3. Create the binary wooded map

Use the script in this repo to read that one scene and output a binary wooded raster:

```bash
python wooded_map_single_image.py --image path/to/SCENE_3B_AnalyticMS_SR.tif --udm path/to/SCENE_3B_udm2.tif --output wooded_binary.tif
```

- The script uses **NDVI** and an optional **UDM2** mask, then thresholds NDVI to get **wooded (1) vs non-wooded (0)**.
- You can tune the NDVI threshold (default 0.4) with `--ndvi-threshold` if your area needs it (e.g. 0.35 for more woodland, 0.5 for stricter).

### 4. Optional: inspect metadata for cloud

If you have `*_metadata.json` next to each scene (from Planet or your export), it may include **cloud_percent** / **clear_percent**. Use `rank_scenes.py --use-metadata-cloud` so the script uses those values when present. The TIF's own metadata (e.g. in QGIS) often has atmospheric correction fields but not always cloud %; the JSON metadata is the right place to check for cloud cover.

---

## Scripts Reference

### Core Scripts

| Script | Purpose |
|------|--------|
| `train_wooded_multi_scene.py` | Multi-scene training with manual labels (local) |
| `train_wooded_multi_scene_gcs.py` | Multi-scene training with manual labels (GCS) |
| `predict_wooded_dl.py` | Single-scene inference (local) |
| `predict_wooded_batch_gcs.py` | Batch inference on multiple scenes (GCS) |
| `compute_features.py` | Compute vegetation indices (NDVI, EVI, etc.) |
| `compute_temporal_features.py` | Extract temporal statistics from timeseries |
| `accuracy_metrics.py` | Compute accuracy metrics (confusion matrix, accuracy, precision, recall, F1, Kappa) |
| `model_unet.py` | U-Net architecture (configurable input channels) |
| `gcs_utils.py` | GCS streaming utilities |

### Legacy Scripts (Single Image, NDVI Proxy)

| Script | Purpose |
|------|--------|
| `train_wooded_dl.py` | Single-scene training with NDVI proxy labels (legacy) |
| `wooded_map_single_image.py` | NDVI thresholding for single image (legacy) |
| `rank_scenes.py` | Rank scenes by clear % and mean NDVI |

---


---

## Output

- **wooded_binary.tif**: single-band GeoTIFF, same extent/crs as the input image.
  - `1` = wooded (vegetation above threshold)
  - `0` = non-wooded
  - NoData where the script masks (e.g. clouds from UDM2, or invalid NDVI).

You can open this in QGIS or any GIS to overlay on basemaps or compute area (e.g. pixel count × pixel area).

## Classification vs regression

What we did is **classification**: each pixel gets a discrete label (wooded = 1, non-wooded = 0). We did **not** predict a continuous value (that would be regression). So this is a **binary image classification** (or semantic segmentation) problem.

---

## What are we actually mapping?

Right now we are **not** validating that "wooded" means trees. We use **NDVI > threshold** as a **proxy for vegetation**. So we effectively map "vegetated vs non-vegetated"; crops, grass, and shrubs can be labelled "wooded" too. To truly map **woodland** you need either:

- A **definition** (e.g. tree cover above a height/canopy density), and
- **Reference data** (ground truth) to train or validate against.

So: current map = "vegetation proxy"; calling it "wooded" is a naming choice. For real woodland mapping, combine with reference labels or a model trained on "wooded" vs "not wooded" (e.g. DL or extra indices/features).

---

## Accuracy metrics

- **Accuracy metrics** (accuracy, precision, recall, F1, Kappa, confusion matrix) require **reference data**: a raster or points where you know the true class (e.g. from fieldwork, photo interpretation, or an existing land-cover product). With that, you can compare predicted vs reference and compute all standard metrics.
- **Automatic computation**: `predict_wooded_dl.py` automatically computes accuracy metrics if a reference raster is available (auto-detected as `{scene_id}_reference_wooded.tif` or provided via `--reference`).

---

## Using deep learning for better performance

The repo includes a **U-Net** pipeline (see **Deep learning classification** above): train with NDVI proxy labels, then predict to get a binary map. Accuracy metrics are automatically computed if reference data is available. For better discrimination (e.g. trees vs crops vs grass):

- **Labels**: Add real reference rasters or point labels ("wooded" vs "non-wooded") and retrain or fine-tune.
- **Validation**: Use `accuracy_metrics.py` against held-out reference data.

---

## Computing accuracy when you have reference data

If you have a **reference raster** (same extent as your prediction) with 1 = wooded, 0 = non-wooded, and NoData where you don't have labels, run:

```bash
python accuracy_metrics.py --predicted wooded_binary.tif --reference path/to/reference_wooded.tif
```

This prints a confusion matrix, accuracy, precision, recall, F1, and Kappa. See `accuracy_metrics.py` for details.

---

## Dependencies

See `requirements.txt`: `numpy`, `rasterio`, `gdown`, `torch`, `google-cloud-storage`, `google-cloud-auth`. Install with:

```bash
pip install -r requirements.txt
```

## Additional Resources

- **Getting Started**: See `GETTING_STARTED.md` for step-by-step workflow guide
- **VM Setup Guide**: See `vm_workflow.md` for detailed GCP VM deployment instructions
- **GCS Utilities**: See `gcs_utils.py` for streaming functions
- **Feature Engineering**: See `compute_features.py` for vegetation index computation
