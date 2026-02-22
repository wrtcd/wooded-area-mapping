# Re-rasterize reference labels – checklist

Use this when your `*_reference_wooded.tif` was not properly rasterized. Goal: **0** = non-wooded, **1** = wooded, **NoData** = unlabeled (no polygon).

---

## Requirements

- **Values:** Only **0** and **1** for labeled pixels. **NoData** for everywhere you didn’t draw a polygon.
- **Alignment:** Same extent, CRS, and pixel size as the scene’s SR image (`{scene_id}_3B_AnalyticMS_SR.tif`).
- **Format:** Single-band GeoTIFF (e.g. Byte/uint8).

---

## In QGIS

### 1. One polygon layer with a `wooded` field

- **Wooded polygons:** add integer field `wooded` = **1**
- **Non-wooded polygons:** add integer field `wooded` = **0**
- **Merge** both into one layer (Vector → Data Management Tools → Merge Vector Layers). That layer must have attribute **wooded** with values 1 and 0 only.

### 2. Rasterize (Vector to Raster)

- **Input layer:** merged polygon layer (with field `wooded`).
- **Field to use for burn-in value:** `wooded`.
- **Output raster size:** use **Reference layer** = the SR image for this scene  
  e.g. `20240821_165518_26_2498_3B_AnalyticMS_SR.tif`  
  so extent and resolution match exactly.
- **Initial value / pre-initialize:** **255** (or another value you will set as NoData).  
  This makes “no polygon” pixels 255 instead of 0.
- **NoData value:** **255** (same as initial).  
  So: unlabeled = 255 = NoData; labeled = 0 or 1.
- **Output:** `{scene_id}_reference_wooded.tif` (e.g. `20240821_165518_26_2498_reference_wooded.tif`).

### 3. If your Rasterize tool has no “initial value”

- Rasterize as usual (field = `wooded`, reference = SR).
- Then use **Raster → Conversion → Translate** and set **NoData value** to the value used for “no polygon” (e.g. 255). If the tool wrote 0 for unlabeled, you’ll need to re-rasterize with **init 255** (e.g. via gdal_rasterize) so unlabeled is 255 and 0 is only non-wooded.

---

## Command line (gdal_rasterize)

Same idea: unlabeled = 255 = NoData, burn 0 and 1 from the vector.

```bash
# Replace paths and scene_id as needed. -init 255 so unlabeled pixels are 255.
gdal_rasterize -init 255 -a wooded -a_nodata 255 \
  -te <xmin> <ymin> <xmax> <ymax> -tr <pixel_width> <pixel_height> \
  -ot Byte \
  merged_labels.shp 20240821_165518_26_2498_reference_wooded.tif
```

Or use **-l** (layer) and match the SR extent/resolution from the SR file (e.g. with `gdalinfo`).

---

## Quick check before upload

- Open the reference in QGIS and compare to the SR: same extent, same resolution, lines up.
- **Unique values:** only **0**, **1**, and **NoData** (e.g. 255). No other values.
- **0** = non-wooded, **1** = wooded, **NoData** = unlabeled.

Then upload to your bucket (e.g. same prefix as SRs):

```text
gsutil cp .../20240821_165518_26_2498_reference_wooded.tif gs://ps4-woodedarea/2024/
```

Training will use only pixels where the reference is 0 or 1; NoData pixels are ignored.
