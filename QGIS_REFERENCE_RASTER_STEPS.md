# QGIS: From Wooded / Non-wooded Polygons to Reference Rasters

**Workflow:** Digitize in two layers (wooded polygons in one shapefile, non-wooded in another). When you’ve finished collecting samples, merge them and then rasterize (steps below).

Use this when you have two polygon layers (wooded and non-wooded) and need one reference GeoTIFF **per scene** with values 1 = wooded, 0 = non-wooded, NoData = unlabeled.

**Your two scenes:**  
`20240821_165518_26_2498` and `20240821_165520_08_2498`

---

## 1. One polygon layer with a "wooded" field (1 or 0)

You have two shapefiles: wooded polygons and non-wooded polygons.

**Option A – Add field and merge in one go**

1. In **wooded** layer: Field calculator → add integer field `wooded` = **1**. Save.
2. In **non-wooded** layer: Field calculator → add integer field `wooded` = **0**. Save.
3. **Vector → Data Management Tools → Merge Vector Layers**: add both layers → output one merged layer (e.g. `labels_merged`). It should have a column `wooded` with values 1 or 0.

**Option B – Append and set field**

1. Add integer field `wooded` to the wooded layer = 1. Save.
2. Add integer field `wooded` to the non-wooded layer = 0. Save.
3. Use **Vector → Merge Vector Layers** (or “Append” in Processing) so you have a single layer with `wooded` = 1 or 0.

Result: one polygon layer with attribute **wooded** (1 or 0). Use this for rasterizing.

---

## 2. Rasterize to match each scene (one reference per scene)

You need **two** reference rasters (one per scene), same extent and resolution as the corresponding SR image.

For **each** scene do the following (replace `SCENE_ID` with that scene’s ID).

### Scene 1: `20240821_165518_26_2498`

1. **Raster → Conversion → Rasterize (Vector to Raster)**.
2. **Input layer:** your merged polygon layer (with field `wooded`).
3. **Field to use for a burn-in value:** `wooded`.
4. **Output raster size:**  
   - Either **Reference layer:** the SR image for this scene  
     `...20240821_165518_26_2498_3B_AnalyticMS_SR.tif`  
   - Or set **Width / Height** and **Extent** manually to match that SR (right‑click SR → Layer extent; use same CRS and pixel size).
5. **Output:**  
   `20240821_165518_26_2498_reference_wooded.tif`  
   (save in the same folder as the SR, or where you keep references.)
6. **NoData value:** set to a value that will mean “unlabeled”, e.g. **255** or **-9999**.  
   - In the Rasterize dialog, if there is “Output no data value” or “Assign a specified nodata value”, set it (e.g. 255).  
   - Pixels that don’t intersect any polygon should get this value so the training script treats them as NoData.
7. Run. Then **check**:  
   - Raster values should be **0**, **1**, and your NoData value (e.g. 255).  
   - If the tool doesn’t set unburned pixels to NoData, use **Raster → Conversion → Translate** and set “NoData value” to 255 (or whatever you used) so that value is written as the raster’s NoData.

### Scene 2: `20240821_165520_08_2498`

Repeat the same steps, but:

- **Reference layer:**  
  `...20240821_165520_08_2498_3B_AnalyticMS_SR.tif`
- **Output:**  
  `20240821_165520_08_2498_reference_wooded.tif`

So you end up with:

- `20240821_165518_26_2498_reference_wooded.tif`
- `20240821_165520_08_2498_reference_wooded.tif`

---

## 3. If “unlabeled” pixels are still 0

Some rasterize tools write 0 for pixels that don’t intersect any polygon. The training script expects **NoData** for unlabeled areas, not 0.

**Fix:**

1. In QGIS: **Raster → Raster Calculator**  
   - Expression: e.g. `("reference_wooded@1" = 0) AND (no polygon coverage)` is not direct. Easier: use **Raster → Conversion → Translate** and set **NoData value** to a number you didn’t use (e.g. 255), then in a second step set only “no polygon” pixels to 255 (e.g. by masking).  
   - Simpler approach: when rasterizing, if the tool has “Initial value” or “Pre-initialize with value”, set it to 255 and set NoData = 255; then burn 0 and 1 from the vector. Unburned pixels stay 255 = NoData.

2. Or in **gdal_rasterize** (Processing / console):  
   - `-init 255`  
   - `-a wooded`  
   - `-a_nodata 255`  
   so unlabeled = 255 and the raster’s NoData = 255.

---

## 4. Quick check before upload

- Both reference rasters open in QGIS and align with their SR image (same extent, same CRS).
- Value 1 = wooded (red in typical single-band color ramp), 0 = non-wooded, NoData = unlabeled (transparent or distinct).
- Filenames exactly:  
  `20240821_165518_26_2498_reference_wooded.tif` and  
  `20240821_165520_08_2498_reference_wooded.tif`

Then upload to GCS (same prefix as your SRs, e.g. `2024/`):

```text
gsutil cp .../20240821_165518_26_2498_reference_wooded.tif gs://ps4-woodedarea/2024/
gsutil cp .../20240821_165520_08_2498_reference_wooded.tif gs://ps4-woodedarea/2024/
```

After that you can run training with `--bucket ps4-woodedarea --prefix 2024/` (and optionally limit to these two scenes if your bucket has others).
