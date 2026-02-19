# Getting Started Guide

## Quick Start: Where to Begin

You've already set up your GCS bucket with timeseries data. Here's your step-by-step workflow:

---

## Step 1: Manual Labeling (First Priority)

Before training, you need to create **reference rasters** (ground truth labels) for 3-10 scenes.

### 1.1 Select Scenes to Label

Choose **3-10 scenes** spanning different seasons (e.g., January, April, July, October) from your timeseries:
- **Goal**: Capture seasonal variation (deciduous vs evergreen, leaf-on vs leaf-off)
- **Selection criteria**: Cloud-free scenes with good visibility

### 1.2 Download Selected Scenes Locally (for labeling)

You can download scenes from GCS for labeling:

```bash
# Option 1: Use gsutil (if you have it installed)
gsutil -m cp gs://your-bucket/scenes/20240110_162648_67_247d_3B_AnalyticMS_SR.tif ./data/
gsutil -m cp gs://your-bucket/scenes/20240110_162648_67_247d_3B_udm2.tif ./data/

# Option 2: Use Python script (create a simple download script)
python -c "
from gcs_utils import download_scene_to_local
files = download_scene_to_local('your-bucket-name', '20240110_162648_67_247d', './data', 'scenes/')
"
```

### 1.3 Label in QGIS/ArcGIS

**IMPORTANT**: Before labeling, read **[WOODED_AREA_DEFINITION.md](WOODED_AREA_DEFINITION.md)** for the complete definition of "wooded areas" and detailed labeling guidelines.

**Quick summary**:
1. **Open PlanetScope scene** in QGIS (or ArcGIS)
2. **Add high-res basemap** (Google Earth/Maxar) as reference layer
3. **Define "wooded"**: Trees ≥5m tall (see definition document for details)
4. **Digitize polygons**:
   - Create new polygon layer
   - **For wooded areas (label = 1)**: Draw polygons around **all identifiable wooded patches** - aim for near-full coverage of wooded areas in the scene
   - **For non-wooded areas (label = 0)**: Draw polygons around **diverse representative samples** (20-70% coverage) of different non-wooded types (urban, roads, water, crops, shrubs)
   - Attribute: `wooded = 1` (inside wooded polygons), `wooded = 0` (inside non-wooded polygons)
   - **Include**: Tree shadows, forest patches, tree clusters
   - **Exclude**: Shrubs (<3m), crops, urban infrastructure
   - **Note**: Since polygons rasterize to fill their entire area, full coverage of wooded areas ensures complete ground truth, while diverse sampling of non-wooded types provides sufficient negative examples
5. **Rasterize polygons**:
   - Use QGIS Rasterize tool or `gdal_rasterize`
   - Output: `{scene_id}_reference_wooded.tif`
   - Same extent/CRS as PlanetScope scene
   - Values: `1` = wooded, `0` = non-wooded, `NoData` = unlabeled

**See [WOODED_AREA_DEFINITION.md](WOODED_AREA_DEFINITION.md) for**:
- Complete definition and edge cases (shadows, crops, shrubs, etc.)
- PlanetScope 3m resolution considerations
- County Line Road area specifics
- Labeling examples and quality checks
- **Labeling coverage strategy** (full coverage for wooded vs representative sampling for non-wooded)

### 1.4 Upload Reference Rasters to GCS

```bash
# Upload reference raster to GCS
gsutil cp ./data/20240110_162648_67_247d_reference_wooded.tif gs://your-bucket/scenes/
```

**Repeat for all selected scenes** (3-10 scenes total).

---

## Step 2: Set Up Compute Environment

### Option A: Google Colab Free (Start Here)

1. **Open Colab**: https://colab.research.google.com/
2. **Enable GPU**: Runtime → Change runtime type → GPU (T4)
3. **Upload repository** or clone from GitHub
4. **Install dependencies**:
   ```python
   !pip install -r requirements.txt
   ```
5. **Authenticate with GCS**:
   ```python
   from google.colab import auth
   auth.authenticate_user()
   ```

### Option B: GCP VM (If Colab is too slow)

See `vm_workflow.md` for detailed setup instructions.

**Quick setup**:
```bash
# Create VM with GPU
gcloud compute instances create wooded-mapping-vm \
    --zone=us-central1-a \
    --machine-type=n1-standard-4 \
    --accelerator=type=nvidia-tesla-t4,count=1 \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud

# SSH into VM
gcloud compute ssh wooded-mapping-vm --zone=us-central1-a

# Run setup script
./setup_vm.sh
```

---

## Step 3: Train the Model

Once you have **3-10 labeled scenes** in your GCS bucket, train the model:

### On Colab or VM:

```bash
# Auto-detect all scenes with reference rasters and train
python train_wooded_multi_scene_gcs.py \
    --bucket your-bucket-name \
    --prefix scenes/ \
    --epochs 50 \
    --batch-size 16 \
    --output wooded_model.pt
```

**Or specify scenes manually**:
```bash
python train_wooded_multi_scene_gcs.py \
    --bucket your-bucket-name \
    --prefix scenes/ \
    --scene-ids 20240110_162648_67_247d 20240415_162648_67_247d 20240720_162648_67_247d \
    --epochs 50 \
    --batch-size 16 \
    --output wooded_model.pt
```

**What happens**:
- Script downloads scenes from GCS (or uses cache)
- Computes features (B, G, R, NIR, NDVI, EVI = 6 channels)
- Extracts patches from all scenes
- Trains U-Net on combined dataset
- Saves model checkpoint: `wooded_model.pt`

**Training time**: ~1-3 hours on T4 GPU (depends on number of scenes, epochs, patch count)

---

## Step 4: Run Inference on New Scenes

Once you have a trained model, run inference on any scene:

### Batch Inference (All Scenes):

```bash
python predict_wooded_batch_gcs.py \
    --bucket your-bucket-name \
    --prefix scenes/ \
    --model wooded_model.pt \
    --output-prefix predictions/ \
    --compute-metrics
```

**What happens**:
- Processes all scenes in bucket
- Generates binary wooded maps
- Uploads predictions to `gs://your-bucket/predictions/`
- Computes accuracy metrics if reference rasters available

### Single Scene (Local):

```bash
# Download scene locally first
gsutil cp gs://your-bucket/scenes/20240110_162648_67_247d_3B_AnalyticMS_SR.tif ./data/
gsutil cp gs://your-bucket/scenes/20240110_162648_67_247d_3B_udm2.tif ./data/

# Run inference
python predict_wooded_dl.py \
    --image ./data/20240110_162648_67_247d_3B_AnalyticMS_SR.tif \
    --model wooded_model.pt \
    --udm ./data/20240110_162648_67_247d_3B_udm2.tif \
    --output ./data/wooded_binary.tif
```

---

## Step 5: Optional Enhancements

### Add Temporal Features (Timeseries Integration)

Extract temporal statistics from your timeseries:

```bash
python compute_temporal_features.py \
    --bucket your-bucket-name \
    --prefix scenes/ \
    --output-dir temporal_features/
```

This creates additional channels (mean NDVI, max NDVI, min NDVI, std NDVI, day-of-year for max NDVI) that can improve classification.

**Then retrain** with temporal features integrated (requires modifying training script to include temporal channels).

---

## Troubleshooting

### "No scenes with reference rasters found"

**Solution**: Make sure you've:
1. Created reference rasters (`{scene_id}_reference_wooded.tif`)
2. Uploaded them to GCS bucket
3. Used correct `--prefix` (e.g., `scenes/`)

### "GCS authentication error"

**Solution**:
- **Colab**: Run `auth.authenticate_user()`
- **VM**: Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable or run `gcloud auth application-default login`

### "Out of memory" during training

**Solution**:
- Reduce `--batch-size` (e.g., from 16 to 8)
- Reduce `--patch-size` (e.g., from 64 to 32)
- Use fewer scenes initially

### "Model not found" during inference

**Solution**: Make sure model file (`wooded_model.pt`) is in the current directory or provide full path with `--model`

---

## Next Steps

1. ✅ **You've done**: Created GCS bucket, uploaded timeseries data
2. 🔄 **Next**: Label 3-10 scenes (Step 1)
3. 🔄 **Then**: Train model (Step 3)
4. 🔄 **Finally**: Run inference on all scenes (Step 4)

---

## Quick Reference

**Your GCS bucket structure should be**:
```
gs://your-bucket/
└── scenes/
    ├── 20240110_162648_67_247d_3B_AnalyticMS_SR.tif
    ├── 20240110_162648_67_247d_3B_udm2.tif
    ├── 20240110_162648_67_247d_reference_wooded.tif  ← You create this
    ├── 20240415_162648_67_247d_3B_AnalyticMS_SR.tif
    ├── 20240415_162648_67_247d_3B_udm2.tif
    ├── 20240415_162648_67_247d_reference_wooded.tif  ← You create this
    └── ... (more scenes)
```

**After training and inference**:
```
gs://your-bucket/
├── scenes/ (original data)
├── predictions/ (generated binary maps)
│   ├── 20240110_162648_67_247d_wooded_binary.tif
│   └── ...
└── wooded_model.pt (trained model)
```

---

## Need Help?

- **README.md**: Full documentation
- **vm_workflow.md**: VM setup details
- **Scripts**: All scripts have `--help` flag for usage information
