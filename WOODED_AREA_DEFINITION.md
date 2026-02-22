# Wooded Area Definition and Labeling Guidelines

## Purpose

Define "wooded areas" for manual labeling to ensure consistent ground truth data for training the deep learning model. This document addresses:
- Standard definitions from forestry/remote sensing literature
- Adaptation to PlanetScope 3m resolution
- Specific guidance for County Line Road area
- Edge cases: trees, shrubs, bushes, crops, shadows

---

## Standard Definitions

### FAO Forest Definition (Most Widely Used)

**Forest**: Land spanning more than 0.5 hectares with:
- **Trees higher than 5 meters**
- **Canopy cover of more than 10%**
- Excludes land predominantly under agricultural or urban use

### US Forest Service Tree Cover Definition

**Tree Cover**: Woody vegetation with:
- **Height ≥ 5 meters**
- **Canopy density ≥ 20-30%** (varies by system)

### Trees vs. Shrubs

- **Trees**: Woody plants **>5 meters** tall
- **Shrubs**: Woody plants **<3 meters** tall
- **Intermediate (3-5m)**: Classify as trees if they have clear tree-like physiognomy

---

## Definition for Your Project

### Recommended Definition: "Wooded Areas"

**Include as "wooded" (label = 1)**:
- **Trees ≥ 5 meters tall** with visible canopy
- **Tree clusters/groves** where individual trees may be hard to distinguish but canopy is continuous
- **Forest patches** (natural or semi-natural) with >10% canopy cover
- **Wooded corridors** along roads/streams (if trees meet height threshold)
- **Orchards** (if trees meet height threshold and are not actively managed crops)

**Exclude from "wooded" (label = 0)**:
- **Shrubs** (<3m height) - even if dense
- **Bushes** (<3m height)
- **Crops** (agricultural fields, row crops, pastures)
- **Grassland** (even if dense)
- **Urban areas** (buildings, roads, parking lots)
- **Water bodies**
- **Bare ground**

**Edge Cases - How to Handle**:

1. **Shadows**:
   - **Tree shadows**: Include the shadow area as part of the wooded polygon when the shadow falls on **ground, grass, or vegetated area** (shadows indicate trees).
   - **Tree shadows on water, roads, driveways, or pavement**: Label as **non-wooded (0)**. Follow the underlying surface: do not extend the wooded polygon over water bodies, roads, or driveways. This keeps ground truth consistent (water stays water, road stays road) and avoids teaching the model that "dark = wooded" over non-vegetated surfaces.
   - **Cloud shadows**: Exclude (use UDM2 mask)
   - **Building shadows**: Exclude

2. **Mixed Vegetation**:
   - If area has **trees ≥5m** mixed with shrubs/crops: **Include** if trees dominate (>50% of area)
   - If shrubs dominate: **Exclude**

3. **Crops vs. Trees**:
   - **Orchards** (fruit trees, nut trees): **Include** if trees ≥5m
   - **Row crops** (corn, soybeans, cotton): **Exclude**
   - **Tree plantations** (timber): **Include** if trees ≥5m

4. **Small Patches**:
   - **Individual trees** visible in PlanetScope (3m): **Include** if ≥5m height
   - **Very small patches** (<0.5 hectares): Still include if they meet tree height threshold

5. **Seasonal Variation**:
   - **Deciduous trees** (leaf-off in winter): **Include** if you can identify tree structure/trunks
   - If completely bare and indistinguishable from shrubs: **Exclude** (or use leaf-on season for labeling)

---

## PlanetScope 3m Resolution Considerations

### What You Can See at 3m Resolution

**Visible**:
- Individual large trees (>5m)
- Tree clusters and groves
- Forest patches
- Canopy structure and texture
- Shadows cast by trees

**Challenging**:
- Very small individual trees (<5m)
- Distinguishing shrubs from small trees (use height reference)
- Fine details within dense canopies

### Labeling Strategy for 3m Resolution

1. **Use High-Resolution Reference**:
   - Always reference Google Earth/Maxar (0.3-0.7m) to verify tree height where possible
   - PlanetScope alone may not show enough detail for height estimation
   - **Where height is hard to verify** (e.g. in QGIS, or when 3D is not available): using **satellite imagery** (e.g. Google Satellite view) to distinguish **forest vs grassland or other cover types** is an acceptable proxy for "trees ≥5 m" — label as wooded where you clearly see forest canopy/structure, and as non-wooded where you see grassland, crops, or low vegetation

2. **Label at PlanetScope Resolution**:
   - Draw polygons on PlanetScope imagery (3m)
   - Use high-res imagery to verify what you're labeling
   - Don't try to label individual pixels - label patches/areas

3. **Minimum Mapping Unit**:
   - **Minimum patch size**: ~3-5 pixels (9-15m²) - roughly equivalent to a single large tree
   - Smaller features may be too noisy at 3m resolution

---

## County Line Road Area Specifics

### Context
- **Area**: County Line Road and surrounding area
- **Scene size**: ~16×24 km (PlanetScope typical coverage)
- **Location**: Huntsville, Alabama area

### Expected Vegetation Types

**Likely to Encounter**:
- **Deciduous forests** (oak, hickory, maple) - seasonal variation
- **Pine forests** (evergreen) - year-round green
- **Mixed forests** (deciduous + evergreen)
- **Riparian corridors** (trees along streams/rivers)
- **Agricultural fields** (row crops, pastures)
- **Urban/suburban** (residential areas with trees)
- **Shrubland** (if present)

### Labeling Priorities

1. **Primary Focus**: Natural/semi-natural forest patches with trees ≥5m
2. **Secondary**: Urban trees (if they meet height threshold and are not isolated)
3. **Exclude**: Agricultural fields, even if they have scattered trees

---

## Practical Labeling Guidelines

### Step-by-Step Labeling Process

1. **Open PlanetScope Scene** in QGIS/ArcGIS
2. **Add High-Resolution Basemap** (Google Earth/Maxar) as reference
3. **For Each Potential Wooded Area**:
   - Check high-res imagery: Are there trees ≥5m tall?
   - If yes: Draw polygon around the area
   - If no: Skip or label as non-wooded

4. **Polygon Boundaries**:
   - **Include**: Tree canopy extent + tree shadows on ground/vegetation (exclude shadow on water, roads, driveways)
   - **Exclude**: Gaps between trees (if gap is >10m wide)
   - **Edge**: Follow canopy edge, not individual tree trunks

5. **Uncertain Areas**:
   - If uncertain (e.g., shrubs vs. small trees): Use high-res imagery to verify height
   - If still uncertain: Label as **NoData** (unlabeled) rather than guessing

### Quality Checks

**Before Finalizing Labels**:
- [ ] All polygons represent trees ≥5m (verified with high-res imagery)
- [ ] No crops or agricultural fields included
- [ ] No shrubs/bushes included (unless they're clearly trees 3-5m with tree-like structure)
- [ ] Shadows from trees are included in polygons
- [ ] Cloud shadows are excluded (use UDM2 mask)
- [ ] Consistent labeling across all scenes

### Labeling Coverage Strategy

**Important**: The extent of labeling differs for wooded vs non-wooded areas:

**Wooded Areas (label = 1)**:
- **Aim for near-full coverage**: Label **every identifiable wooded patch/polygon** in the scene
- **Rationale**: Since polygons rasterize to fill areas, full coverage ensures complete ground truth for the positive class
- **Goal**: Capture all wooded areas so the model learns the full diversity of wooded patterns

**Non-Wooded Areas (label = 0)**:
- **Aim for representative sampling**: Label **diverse examples** covering approximately 20-70% of non-wooded types
- **Include diverse examples**: Urban areas, roads, water bodies, crops, grassland, shrubs
- **Rationale**: Diverse sampling provides sufficient negative examples without requiring exhaustive labeling of every non-wooded pixel
- **Goal**: Ensure the model sees enough variety in non-wooded classes to distinguish them from wooded areas

**Why This Matters**:
- Polygons rasterize to fill their entire area, so labeling all wooded patches ensures comprehensive positive training data
- Non-wooded areas are typically more homogeneous and diverse sampling is sufficient for effective model training
- This strategy balances labeling effort with model performance

---

## Examples: What to Label

### Example 1: Dense Forest Patch
- **What**: Large patch of trees, canopy is continuous
- **Label**: **Wooded (1)**
- **Reason**: Trees clearly ≥5m, canopy cover >10%

### Example 2: Individual Large Trees
- **What**: Scattered large trees in a field
- **Label**: **Wooded (1)** - draw polygon around each tree + shadow
- **Reason**: Individual trees ≥5m still count as wooded

### Example 3: Shrubland
- **What**: Dense shrubs, <3m height
- **Label**: **Non-wooded (0)**
- **Reason**: Below height threshold

### Example 4: Agricultural Field
- **What**: Corn/soybean field, even if it has scattered trees
- **Label**: **Non-wooded (0)** for field, **Wooded (1)** for individual trees if ≥5m
- **Reason**: Agricultural use excludes the field; trees within can be labeled separately

### Example 5: Orchard
- **What**: Fruit trees in rows, trees ≥5m
- **Label**: **Wooded (1)** - include entire orchard area
- **Reason**: Trees meet height threshold

### Example 6: Deciduous Forest (Winter)
- **What**: Forest patch, trees bare (no leaves)
- **Label**: **Wooded (1)** if tree structure/trunks visible
- **Reason**: Trees still present, just leaf-off

---

## Consistency Across Scenes

### Important: Label Consistently

Since you're labeling **3-10 scenes spanning different seasons**, ensure consistency:

1. **Same Definition**: Use the same height threshold (≥5m) and criteria across all scenes
2. **Seasonal Awareness**: 
   - Label leaf-on scenes (summer) first - easier to identify trees
   - Use leaf-on scenes as reference for leaf-off scenes
3. **Document Decisions**: Note any edge cases or ambiguous areas for reference

**Peak-of-season dates (Alabama / Northern Hemisphere)** for choosing scenes:
- **Winter**: ~Jan 20 – Feb 10 (dormant, leaf-off)
- **Spring**: ~Apr 25 – May 10 (green-up)
- **Summer**: ~Jul 15 – Aug 1 (full leaf-on, peak biomass)
- **Fall**: ~Oct 15 – Oct 30 (fall color, senescence)

See **GETTING_STARTED.md** (Step 1.1) for full date ranges and selection tips.

---

## Output Format

### Reference Raster Specifications

- **File naming**: `{scene_id}_reference_wooded.tif`
- **Values**:
  - `1` = wooded (trees ≥5m)
  - `0` = non-wooded
  - `NoData` = unlabeled/uncertain
- **Spatial properties**: Same extent, CRS, and resolution as PlanetScope scene
- **Format**: GeoTIFF, single band, uint8

---

## Questions to Resolve Before Labeling

Before you start labeling, decide:

1. **Height Threshold**: Use ≥5m (standard) or adjust for your area?
2. **Minimum Patch Size**: Include individual trees or only patches?
3. **Urban Trees**: Include trees in residential/urban areas?
4. **Orchards**: Include or exclude?
5. **Riparian Corridors**: Include trees along streams/rivers?

**Recommendation**: Start with standard definition (≥5m trees, >10% canopy), label 1-2 test scenes, review results, then adjust if needed.

---

## Quick Reference Summary

**Label as WOODED (1)**:
- Trees ≥5m tall
- Forest patches with >10% canopy cover
- Tree clusters/groves
- Orchards (if trees ≥5m)
- Include tree shadows on ground/vegetation (not on water, roads, driveways)
- **Coverage**: Aim for near-full coverage - label every identifiable wooded patch/polygon

**Label as NON-WOODED (0)**:
- Shrubs/bushes <3m
- Crops/agricultural fields
- Grassland
- Urban infrastructure
- Water bodies
- **Coverage**: Aim for representative sampling (20-70% coverage) of diverse non-wooded types

**Label as NODATA (unlabeled)**:
- Uncertain areas (verify with high-res imagery first)
- Cloud shadows (use UDM2 mask instead)

**Key Rule**: When in doubt, verify tree height using high-resolution imagery (Google Earth/Maxar) before labeling.
