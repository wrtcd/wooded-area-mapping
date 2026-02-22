# Labeling Plan: 2 Summer Scenes (August)

Plan for creating wooded (1) and non-wooded (0) training samples for your two August scenes.

**Scenes:**  
- `20240821_165518_26_2498`  
- `20240821_165520_08_2498`

**Setup:** Two polygon shapefiles in QGIS — one for wooded, one for non-wooded. NIR-RED-GREEN for vegetation (red), Google Satellite for checking. Merge the two layers only after you finish collecting samples.

---

## 1. Definition (quick reference)

Full rules: **[WOODED_AREA_DEFINITION.md](WOODED_AREA_DEFINITION.md)**.

| Label | Include | Exclude |
|-------|--------|---------|
| **Wooded (1)** | Trees ≥5 m, forest patches, tree clusters, wooded corridors, orchards (if trees ≥5 m). Include tree shadows on ground/grass. | — |
| **Non-wooded (0)** | — | Shrubs (&lt;3 m), crops, grassland, water, roads, urban, bare ground. Tree shadows on water/roads = 0. |
| **Unlabeled** | Leave as NoData (no polygon). | Cloud shadows (use UDM2 later); uncertain areas. |

**Shadows:** Tree shadow on vegetation/ground → inside wooded polygon. Tree shadow on water/road/pavement → non-wooded polygon (don’t extend wooded over them).

---

## 2. Coverage strategy

- **Wooded:** Near-full coverage. Draw a polygon around every identifiable wooded patch in the scene so the model sees the full range of wooded patterns.
- **Non-wooded:** Representative sampling (about 20–70%). Include a variety: roads, water, crops, urban, grassland. You don’t need to label every non-wooded pixel.

---

## 3. Suggested order of work

**Option A – By scene (recommended)**  
- Finish all labeling for scene 1, then do scene 2. Keeps one scene’s extent in mind and avoids mixing up scenes.

**Option B – By theme**  
- Digitize all wooded polygons for both scenes, then all non-wooded for both. Use the same rules in both scenes.

**Per scene:**

1. Load that scene’s SR (and UDM2 if you use it) + Google Satellite.
2. **Wooded first:** Add polygons to the **wooded** shapefile for every wooded patch (trees ≥5 m). Use Google Satellite to confirm height/canopy where needed.
3. **Non-wooded next:** Add polygons to the **non-wooded** shapefile for a representative set of roads, water, crops, urban, grass, etc.
4. Quick check: no crops/shrubs in wooded; shadows on ground in wooded, on water/roads in non-wooded.
5. Save both shapefiles, then move to the other scene (or other theme).

---

## 4. Per-scene checklist

Before you consider a scene done:

- [ ] Wooded polygons: only trees ≥5 m (checked with Google Satellite where needed).
- [ ] No crops, grassland, or shrubs in wooded layer.
- [ ] Tree shadows on ground/vegetation included in wooded; on water/roads drawn as non-wooded.
- [ ] Non-wooded layer has a mix of types (roads, water, crops, urban, etc.).
- [ ] No cloud-covered areas labeled (or note for UDM2 at training time).
- [ ] Both shapefiles saved.

Repeat for the second scene.

---

## 5. Resolution and boundaries

- Draw at **PlanetScope scale** (patch level), not individual 3 m pixels.
- Minimum patch size ~3–5 pixels (single large tree scale).
- Polygon boundary: follow canopy edge; include shadow on ground/grass; exclude shadow on water/roads.

---

## 6. After labeling

1. **Merge:** Add field `wooded` (1 in wooded layer, 0 in non-wooded). Merge the two layers into one.
2. **Rasterize:** Create one reference raster per scene, aligned to that scene’s SR (extent, CRS, resolution). Output: `{scene_id}_reference_wooded.tif` with 1 / 0 / NoData.
3. **Upload:**  
   `gsutil cp .../20240821_165518_26_2498_reference_wooded.tif gs://ps4-woodedarea/2024/`  
   (and the same for the second scene).

Step-by-step rasterize and NoData: **[QGIS_REFERENCE_RASTER_STEPS.md](QGIS_REFERENCE_RASTER_STEPS.md)**.

---

## 7. Summary

| Step | Action |
|------|--------|
| Define | Wooded = trees ≥5 m; non-wooded = crops, grass, water, roads, urban, etc. Shadows: on ground = wooded, on water/road = non-wooded. |
| Scope | 2 scenes: 20240821_165518_26_2498, 20240821_165520_08_2498. |
| Wooded | Near-full coverage of wooded patches per scene. |
| Non-wooded | 20–70% representative mix of types. |
| Then | Merge → rasterize (1 per scene) → upload to GCS. |
