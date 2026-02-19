#!/usr/bin/env python3
"""
Google Cloud Storage (GCS) utilities for streaming PlanetScope scenes.

Provides efficient data access without downloading entire files.
"""

import numpy as np
import rasterio
from pathlib import Path
from typing import Optional
from google.cloud import storage
from google.cloud.storage import Blob
import io


def get_gcs_client() -> storage.Client:
    """Get authenticated GCS client."""
    return storage.Client()


def list_scenes(bucket_name: str, prefix: str = "") -> list[str]:
    """
    List all scene IDs in a GCS bucket.
    
    Args:
        bucket_name: GCS bucket name
        prefix: Optional prefix to filter (e.g., "scenes/")
    
    Returns:
        List of scene IDs (without file extensions)
    """
    client = get_gcs_client()
    bucket = client.bucket(bucket_name)
    
    # List all SR files
    blobs = bucket.list_blobs(prefix=prefix)
    scene_ids = set()
    
    for blob in blobs:
        name = blob.name
        if "_3B_AnalyticMS_SR.tif" in name:
            # Extract scene ID (e.g., "20240110_162648_67_247d" from path)
            parts = name.split("/")
            filename = parts[-1]
            scene_id = filename.replace("_3B_AnalyticMS_SR.tif", "")
            scene_ids.add(scene_id)
    
    return sorted(list(scene_ids))


def download_blob_to_memory(bucket_name: str, blob_path: str) -> bytes:
    """
    Download a blob from GCS to memory.
    
    Args:
        bucket_name: GCS bucket name
        blob_path: Path to blob in bucket (e.g., "scenes/20240110_162648_67_247d_3B_AnalyticMS_SR.tif")
    
    Returns:
        Blob contents as bytes
    """
    client = get_gcs_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    return blob.download_as_bytes()


def stream_raster_from_gcs(
    bucket_name: str,
    blob_path: str,
    window: Optional[rasterio.windows.Window] = None,
) -> tuple[np.ndarray, dict]:
    """
    Stream a raster from GCS, optionally reading only a window.
    
    Args:
        bucket_name: GCS bucket name
        blob_path: Path to GeoTIFF in bucket
        window: Optional rasterio window to read (default: entire image)
    
    Returns:
        Tuple of (data array, metadata dict)
    """
    # Download blob to memory
    blob_bytes = download_blob_to_memory(bucket_name, blob_path)
    
    # Open from memory using rasterio
    with rasterio.io.MemoryFile(blob_bytes) as memfile:
        with memfile.open() as src:
            if window is None:
                data = src.read()
                meta = src.meta.copy()
            else:
                data = src.read(window=window)
                meta = src.meta.copy()
                # Update transform for window
                meta['transform'] = rasterio.windows.transform(window, src.transform)
                meta['width'] = window.width
                meta['height'] = window.height
    
    return data, meta


def stream_window_from_gcs(
    bucket_name: str,
    blob_path: str,
    row_start: int,
    col_start: int,
    row_size: int,
    col_size: int,
) -> tuple[np.ndarray, dict]:
    """
    Stream a specific window from a raster in GCS.
    
    Args:
        bucket_name: GCS bucket name
        blob_path: Path to GeoTIFF in bucket
        row_start: Starting row index
        col_start: Starting column index
        row_size: Number of rows to read
        col_size: Number of columns to read
    
    Returns:
        Tuple of (data array, metadata dict)
    """
    window = rasterio.windows.Window(col_start, row_start, col_size, row_size)
    return stream_raster_from_gcs(bucket_name, blob_path, window)


def download_scene_to_local(
    bucket_name: str,
    scene_id: str,
    output_dir: Path,
    prefix: str = "",
) -> dict[str, Path]:
    """
    Download a complete scene (SR, UDM2, reference if available) to local directory.
    
    Args:
        bucket_name: GCS bucket name
        scene_id: Scene ID (e.g., "20240110_162648_67_247d")
        output_dir: Local directory to save files
        prefix: Optional prefix in bucket (e.g., "scenes/")
    
    Returns:
        Dict mapping file type to local path:
        {
            'sr': Path(...),
            'udm2': Path(...),
            'reference': Path(...) or None
        }
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    client = get_gcs_client()
    bucket = client.bucket(bucket_name)
    
    files = {}
    
    # Download SR image
    sr_blob_path = f"{prefix}{scene_id}_3B_AnalyticMS_SR.tif".lstrip("/")
    sr_blob = bucket.blob(sr_blob_path)
    if sr_blob.exists():
        sr_local = output_dir / f"{scene_id}_3B_AnalyticMS_SR.tif"
        sr_blob.download_to_filename(str(sr_local))
        files['sr'] = sr_local
        print(f"Downloaded SR: {sr_local}")
    
    # Download UDM2
    udm_blob_path = f"{prefix}{scene_id}_3B_udm2.tif".lstrip("/")
    udm_blob = bucket.blob(udm_blob_path)
    if udm_blob.exists():
        udm_local = output_dir / f"{scene_id}_3B_udm2.tif"
        udm_blob.download_to_filename(str(udm_local))
        files['udm2'] = udm_local
        print(f"Downloaded UDM2: {udm_local}")
    
    # Download reference if available
    ref_blob_path = f"{prefix}{scene_id}_reference_wooded.tif".lstrip("/")
    ref_blob = bucket.blob(ref_blob_path)
    if ref_blob.exists():
        ref_local = output_dir / f"{scene_id}_reference_wooded.tif"
        ref_blob.download_to_filename(str(ref_local))
        files['reference'] = ref_local
        print(f"Downloaded reference: {ref_local}")
    else:
        files['reference'] = None
    
    return files


def upload_file_to_gcs(
    local_path: Path,
    bucket_name: str,
    blob_path: str,
) -> None:
    """
    Upload a local file to GCS.
    
    Args:
        local_path: Path to local file
        bucket_name: GCS bucket name
        blob_path: Destination path in bucket
    """
    client = get_gcs_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    blob.upload_from_filename(str(local_path))
    print(f"Uploaded {local_path} to gs://{bucket_name}/{blob_path}")


def check_scene_exists(
    bucket_name: str,
    scene_id: str,
    prefix: str = "",
) -> dict[str, bool]:
    """
    Check which files exist for a scene in GCS.
    
    Returns:
        Dict with keys 'sr', 'udm2', 'reference' and boolean values
    """
    client = get_gcs_client()
    bucket = client.bucket(bucket_name)
    
    result = {'sr': False, 'udm2': False, 'reference': False}
    
    sr_blob = bucket.blob(f"{prefix}{scene_id}_3B_AnalyticMS_SR.tif".lstrip("/"))
    result['sr'] = sr_blob.exists()
    
    udm_blob = bucket.blob(f"{prefix}{scene_id}_3B_udm2.tif".lstrip("/"))
    result['udm2'] = udm_blob.exists()
    
    ref_blob = bucket.blob(f"{prefix}{scene_id}_reference_wooded.tif".lstrip("/"))
    result['reference'] = ref_blob.exists()
    
    return result
