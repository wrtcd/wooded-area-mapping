# Start Today: Collecting Training Samples (Labeled Data)

This guide gets you from zero to **creating labeled wooded / non-wooded training data** in one session.

**Recommended approach:** Start with **one season** (e.g. 2 summer scenes in August). Label them, train the model, run the full pipeline, and inspect results. Once you see it working, add another season’s scenes and compare performance. This way you keep control over what’s right or wrong and how the model is influenced by new data.

---

## 1. Know the definition (5 min)

Read **[WOODED_AREA_DEFINITION.md](WOODED_AREA_DEFINITION.md)** so labels are consistent.

**Short version:**

- **Wooded (1):** Trees ≥5 m tall, forest patches, tree clusters, orchards (if trees ≥5 m). Include tree shadows on ground/grass.
- **Non-wooded (0):** Shrubs (&lt;3 m), crops, grassland, water, roads, urban. Tree shadows on water/roads = 0.
- **NoData:** Unlabeled / uncertain; clouds (use UDM2 mask instead).

**Coverage:**

- **Wooded:** Aim for **near-full coverage** — label every identifiable wooded patch.
- **Non-wooded:** **Representative sampling** (about 20–70%) of different types (roads, water, crops, urban).

---

## 2. See what scenes you have (2 min)

List scenes and dates in your bucket so you can pick 3–10 across seasons:

```powershell
# From project root, with venv activated
python list_timeseries_dates.py --bucket ps4-woodedarea --prefix 2024/ --detailed
```

If your data is under a different prefix (e.g. `scenes/`), use that instead of `2024/`.  
Pick at least one scene per season if possible (winter ~Jan–Feb, spring ~Apr–May, summer ~Jun–Aug, fall ~Oct).

---

## 3. Get scenes for labeling

Download the SR image and UDM2 (cloud mask) for each scene **manually** (e.g. from GCP Console, `gsutil cp`, or your usual workflow). You need per scene:

- `{scene_id}_3B_AnalyticMS_SR.tif`
- `{scene_id}_3B_udm2.tif`

Put them in a folder you’ll use for labeling (e.g. `./data/labeling/<scene_id>/`). Optional: use `download_scenes_for_labeling.py` if you prefer a script.

---

## 4. Label in QGIS (or ArcGIS)

1. **Open QGIS** and add the PlanetScope scene:
   - Add the **SR GeoTIFF**: `.../data/labeling/<scene_id>/<scene_id>_3B_AnalyticMS_SR.tif`
   - Optionally add **UDM2** to see cloud/valid pixels.

2. **Add a basemap** (e.g. Google Satellite) to help identify trees vs crops/grass.

3. **Create a new polygon layer** for labels:
   - Layer → Create Layer → New Shapefile Layer (or Geopackage).
   - Add an integer attribute: `wooded` (value 1 or 0).

4. **Digitize polygons:**
   - **Wooded (1):** Draw polygons around all wooded patches (trees ≥5 m). Include tree shadows on ground.
   - **Non-wooded (0):** Draw polygons for a representative set of non-wooded areas (roads, water, fields, urban).
   - Save edits.

5. **Rasterize to reference GeoTIFF:**
   - Raster → Conversion → Rasterize.
   - Input: your polygon layer.
   - Field: `wooded`.
   - Output extent and resolution: **same as the PlanetScope SR scene** (critical).
   - Output: `./data/labeling/<scene_id>/<scene_id>_reference_wooded.tif`
   - Values: **1** = wooded, **0** = non-wooded, **NoData** = unlabeled.

**Check:** The reference raster must have the same CRS, extent, and pixel grid as the SR image so training scripts can align them.

---

## 5. Upload reference rasters to GCS

After saving each `*_reference_wooded.tif`:

```powershell
gsutil cp ./data/labeling/<scene_id>/<scene_id>_reference_wooded.tif gs://ps4-woodedarea/2024/
```

Use the same prefix as in step 2 (e.g. `2024/` or `scenes/`).

---

## 6. How many scenes?

- **To start:** 2 scenes from **one season** (e.g. 2 August summer scenes) are enough to train and run the full pipeline. You get a result, verify the pipeline, and see how the model performs.
- **Next:** Add another season’s scenes, retrain, and compare performance. Repeat as you add more data. This keeps control over what’s right or wrong and how the model is influenced.
- **Later:** 3–10+ scenes across seasons improve generalization; see **GETTING_STARTED.md** Step 2 (train with `train_wooded_multi_scene_gcs.py`).

---

## Quick reference

| Step            | Action |
|-----------------|--------|
| Define wooded   | [WOODED_AREA_DEFINITION.md](WOODED_AREA_DEFINITION.md) |
| List scenes     | `python list_timeseries_dates.py --bucket ps4-woodedarea --prefix 2024/ --detailed` (pick e.g. 2 August scenes) |
| Get scenes      | Download SR + UDM2 manually (or use `download_scenes_for_labeling.py` if you prefer) |
| Label           | QGIS: polygons → rasterize → `{scene_id}_reference_wooded.tif` (1/0/NoData) |
| Upload          | `gsutil cp .../reference_wooded.tif gs://ps4-woodedarea/2024/` |

**Project/bucket:** `wooded-488021` / `ps4-woodedarea` (see [BEFORE_YOU_PROCEED.md](BEFORE_YOU_PROCEED.md)).
