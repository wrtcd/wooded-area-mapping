#!/usr/bin/env python3
"""
Compute temporal features from PlanetScope timeseries.

Extracts temporal statistics (mean, max, min, std NDVI, phenology metrics) from
multiple scenes and stacks them as additional channels for each scene.
"""

import argparse
import numpy as np
import rasterio
from pathlib import Path
from typing import Optional
from datetime import datetime

from compute_features import compute_ndvi
from gcs_utils import list_scenes, stream_raster_from_gcs, check_scene_exists


def extract_date_from_scene_id(scene_id: str) -> Optional[datetime]:
    """
    Extract date from scene ID (e.g., "20240110_162648_67_247d" -> 2024-01-10).
    
    Returns None if date cannot be parsed.
    """
    try:
        # Try format: YYYYMMDD_HHMMSS_...
        date_str = scene_id[:8]  # First 8 characters
        return datetime.strptime(date_str, "%Y%m%d")
    except:
        return None


def compute_temporal_features(
    scene_ids: list[str],
    bucket_name: str,
    prefix: str = "",
    cache_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> dict[str, np.ndarray]:
    """
    Compute temporal features for each scene from timeseries.
    
    Args:
        scene_ids: List of scene IDs to process
        bucket_name: GCS bucket name
        prefix: Optional prefix in bucket
        cache_dir: Optional local cache directory
        output_dir: Optional directory to save temporal feature rasters
    
    Returns:
        Dict mapping scene_id to temporal features array (5, H, W):
        - mean_ndvi: Mean NDVI across all scenes
        - max_ndvi: Maximum NDVI
        - min_ndvi: Minimum NDVI
        - std_ndvi: Standard deviation of NDVI
        - doy_max_ndvi: Day of year for max NDVI (normalized 0-1)
    """
    print(f"Loading {len(scene_ids)} scenes from GCS...")
    
    # Load all scenes and compute NDVI
    ndvi_scenes = {}
    dates = {}
    
    for scene_id in scene_ids:
        exists = check_scene_exists(bucket_name, scene_id, prefix)
        if not exists['sr']:
            print(f"  Warning: SR not found for {scene_id}, skipping")
            continue
        
        try:
            # Stream scene from GCS
            blob_path = f"{prefix}{scene_id}_3B_AnalyticMS_SR.tif".lstrip("/")
            img, meta = stream_raster_from_gcs(bucket_name, blob_path)
            
            # Ensure 4 bands
            img = np.squeeze(img).astype(np.float32)
            if img.ndim == 2:
                img = np.stack([img] * 4, axis=0)
            elif img.shape[0] < 4:
                continue
            elif img.shape[0] > 4:
                img = img[:4]
            
            # Compute NDVI
            red = img[2]  # BAND_RED
            nir = img[3]  # BAND_NIR
            ndvi = compute_ndvi(red, nir)
            
            ndvi_scenes[scene_id] = ndvi
            date = extract_date_from_scene_id(scene_id)
            dates[scene_id] = date
            
            print(f"  Loaded {scene_id}: shape {ndvi.shape}")
        
        except Exception as e:
            print(f"  Error loading {scene_id}: {e}")
            continue
    
    if not ndvi_scenes:
        raise ValueError("No scenes loaded successfully!")
    
    # Get reference shape (use first scene)
    first_scene_id = list(ndvi_scenes.keys())[0]
    ref_shape = ndvi_scenes[first_scene_id].shape
    
    # Stack all NDVI arrays
    ndvi_stack = []
    for scene_id in scene_ids:
        if scene_id in ndvi_scenes:
            ndvi = ndvi_scenes[scene_id]
            # Resample if needed (should be same resolution, but handle edge cases)
            if ndvi.shape != ref_shape:
                # Simple resampling using rasterio (if shapes don't match, skip or use first shape)
                print(f"  Warning: Shape mismatch for {scene_id}: {ndvi.shape} vs {ref_shape}")
                # For now, skip scenes with mismatched shapes
                continue
            ndvi_stack.append(ndvi)
    
    ndvi_array = np.stack(ndvi_stack, axis=0)  # (T, H, W) where T = number of scenes
    
    # Compute temporal statistics
    print("\nComputing temporal statistics...")
    
    # Mask NaN values
    valid_mask = ~np.isnan(ndvi_array)
    
    mean_ndvi = np.nanmean(ndvi_array, axis=0)
    max_ndvi = np.nanmax(ndvi_array, axis=0)
    min_ndvi = np.nanmin(ndvi_array, axis=0)
    std_ndvi = np.nanstd(ndvi_array, axis=0)
    
    # Day of year for max NDVI
    doy_max_ndvi = np.zeros(ref_shape, dtype=np.float32)
    for i in range(ref_shape[0]):
        for j in range(ref_shape[1]):
            valid_ndvi = ndvi_array[:, i, j]
            if np.any(~np.isnan(valid_ndvi)):
                max_idx = np.nanargmax(valid_ndvi)
                scene_id_max = scene_ids[max_idx]
                date_max = dates.get(scene_id_max)
                if date_max:
                    doy = date_max.timetuple().tm_yday
                    doy_max_ndvi[i, j] = doy / 365.0  # Normalize to 0-1
    
    # Stack temporal features
    temporal_features = np.stack([
        mean_ndvi,
        max_ndvi,
        min_ndvi,
        std_ndvi,
        doy_max_ndvi,
    ], axis=0)  # (5, H, W)
    
    # Normalize to 0-1 range
    temporal_features[0] = np.clip((temporal_features[0] + 1) / 2, 0, 1)  # mean_ndvi
    temporal_features[1] = np.clip((temporal_features[1] + 1) / 2, 0, 1)  # max_ndvi
    temporal_features[2] = np.clip((temporal_features[2] + 1) / 2, 0, 1)  # min_ndvi
    temporal_features[3] = np.clip(temporal_features[3] / 2, 0, 1)  # std_ndvi (typically 0-0.5)
    # doy_max_ndvi already normalized
    
    # Save temporal features for each scene (using reference metadata)
    results = {}
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    for scene_id in scene_ids:
        if scene_id not in ndvi_scenes:
            continue
        
        # Get metadata from first scene
        blob_path = f"{prefix}{scene_id}_3B_AnalyticMS_SR.tif".lstrip("/")
        _, meta = stream_raster_from_gcs(bucket_name, blob_path)
        
        results[scene_id] = temporal_features
        
        if output_dir:
            output_path = output_dir / f"{scene_id}_temporal_features.tif"
            meta.update(count=5, dtype=np.float32)
            with rasterio.open(output_path, "w", **meta) as dst:
                dst.write(temporal_features)
            print(f"  Saved temporal features for {scene_id}: {output_path}")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Compute temporal features from PlanetScope timeseries."
    )
    parser.add_argument(
        "--bucket",
        required=True,
        help="GCS bucket name"
    )
    parser.add_argument(
        "--prefix",
        default="",
        help="Prefix in bucket (e.g., 'scenes/')"
    )
    parser.add_argument(
        "--scene-ids",
        nargs="+",
        default=None,
        help="Specific scene IDs (default: all scenes in bucket)"
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory to save temporal feature rasters (optional)"
    )
    args = parser.parse_args()

    # Get scene IDs
    if args.scene_ids:
        scene_ids = args.scene_ids
    else:
        print(f"Listing scenes in gs://{args.bucket}/{args.prefix}...")
        scene_ids = list_scenes(args.bucket, args.prefix)
    
    if not scene_ids:
        raise ValueError("No scenes found!")
    
    print(f"Processing {len(scene_ids)} scenes...")
    
    # Compute temporal features
    results = compute_temporal_features(
        scene_ids,
        args.bucket,
        args.prefix,
        output_dir=args.output_dir,
    )
    
    print(f"\nComputed temporal features for {len(results)} scenes")
    print("Features: mean_ndvi, max_ndvi, min_ndvi, std_ndvi, doy_max_ndvi")


if __name__ == "__main__":
    main()
