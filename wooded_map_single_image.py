#!/usr/bin/env python3
"""
Create a binary wooded/non-wooded map from a single Planet 3B Analytic MS SR image.

Uses NDVI (vegetation index) and an optional UDM2 mask. Output is a single-band
GeoTIFF: 1 = wooded, 0 = non-wooded, NoData = masked (e.g. clouds).
"""

import argparse
import numpy as np
import rasterio
from rasterio.enums import Resampling
from pathlib import Path


# Planet 3B AnalyticMS SR 4-band order: Blue, Green, Red, NIR (0, 1, 2, 3)
BAND_RED = 2   # 0-based
BAND_NIR = 3


def load_udm2_valid_mask(udm_path: Path, reference_shape: tuple, reference_transform, reference_crs) -> np.ndarray:
    """
    Load UDM2 and return a boolean mask where True = valid (clear) pixel.
    Resamples to match reference grid if needed.
    """
    with rasterio.open(udm_path) as src:
        # UDM2: typically 0 = invalid (cloud, shadow, etc.), non-zero = valid
        data = src.read(
            1,
            out_shape=reference_shape,
            resampling=Resampling.nearest
        )
        # Consider valid where value != 0 (adjust if your UDM2 encoding differs)
        return data != 0


def compute_ndvi(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """NDVI = (NIR - Red) / (NIR + Red). Returns float array, invalid -> np.nan."""
    red = np.asarray(red, dtype=np.float64)
    nir = np.asarray(nir, dtype=np.float64)
    denom = nir + red
    ndvi = np.full_like(red, np.nan)
    valid = denom != 0
    ndvi[valid] = (nir[valid] - red[valid]) / denom[valid]
    return ndvi


def main():
    parser = argparse.ArgumentParser(
        description="Create binary wooded map from one Planet 3B AnalyticMS SR image."
    )
    parser.add_argument(
        "--image",
        required=True,
        help="Path to *_3B_AnalyticMS_SR.tif",
    )
    parser.add_argument(
        "--udm",
        default=None,
        help="Path to matching *_3B_udm2.tif (optional; masks clouds/invalid)",
    )
    parser.add_argument(
        "--output",
        default="wooded_binary.tif",
        help="Output GeoTIFF path (default: wooded_binary.tif)",
    )
    parser.add_argument(
        "--ndvi-threshold",
        type=float,
        default=0.4,
        help="NDVI above this = wooded (default: 0.4). Increase for stricter woodland.",
    )
    parser.add_argument(
        "--no-udm",
        action="store_true",
        help="Do not use UDM2 even if --udm is provided (for testing).",
    )
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")

    with rasterio.open(image_path) as src:
        meta = src.meta.copy()
        red = src.read(BAND_RED + 1)   # 1-based band index
        nir = src.read(BAND_NIR + 1)
        transform = src.transform
        crs = src.crs
        shape = red.shape

    red = np.squeeze(red)
    nir = np.squeeze(nir)

    ndvi = compute_ndvi(red, nir)

    # Binary: 1 = wooded (NDVI > threshold), 0 = non-wooded
    wooded = (ndvi > args.ndvi_threshold).astype(np.uint8)

    # Apply UDM2 if provided
    if args.udm and not args.no_udm:
        udm_path = Path(args.udm)
        if udm_path.is_file():
            valid = load_udm2_valid_mask(udm_path, shape, transform, crs)
            wooded[~valid] = meta.get("nodata", 255)
            # Use 255 as NoData for byte output if not set
            if "nodata" not in meta or meta["nodata"] is None:
                meta["nodata"] = 255
        else:
            print(f"Warning: UDM2 file not found: {udm_path}, proceeding without mask.")

    # Where NDVI was invalid (NaN), set to NoData
    invalid_ndvi = np.isnan(ndvi)
    nodata_val = meta.get("nodata", 255)
    if nodata_val is None:
        nodata_val = 255
        meta["nodata"] = nodata_val
    wooded[invalid_ndvi] = nodata_val

    meta.update(
        count=1,
        dtype=wooded.dtype,
        compress="lzw",
    )

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(out_path, "w", **meta) as dst:
        dst.write(wooded, 1)

    n_wooded = int((wooded == 1).sum())
    n_nonwooded = int((wooded == 0).sum())
    n_nodata = int((wooded == nodata_val).sum())

    # Pixel area in map units (m² if CRS is in metres, e.g. UTM)
    pixel_area_linear = abs(transform.a * transform.e)
    # If CRS is geographic (deg), linear units are deg²; we still report "area" for reference
    wooded_area_linear = n_wooded * pixel_area_linear
    try:
        if crs and crs.is_projected:
            # Assume metres
            area_m2 = wooded_area_linear
            area_ha = area_m2 / 10_000
            area_km2 = area_m2 / 1_000_000
            print(f"Wrote binary wooded map: {out_path}")
            print(f"  Wooded (1): {n_wooded} px; Non-wooded (0): {n_nonwooded} px; NoData: {n_nodata} px")
            print(f"  Wooded area: {area_ha:.2f} ha  ({area_km2:.4f} km²)")
        else:
            print(f"Wrote binary wooded map: {out_path}")
            print(f"  Wooded (1): {n_wooded} px; Non-wooded (0): {n_nonwooded} px; NoData: {n_nodata} px")
            print(f"  Wooded area: {wooded_area_linear:.2f} (map-unit²; CRS is geographic — for ha/km² use a projected CRS)")
    except Exception:
        print(f"Wrote binary wooded map: {out_path}")
        print(f"  Wooded (1): {n_wooded} px; Non-wooded (0): {n_nonwooded} px; NoData: {n_nodata} px")
        print(f"  Wooded area (map-unit²): {wooded_area_linear:.2f}")


if __name__ == "__main__":
    main()
