#!/usr/bin/env python3
"""
Compute vegetation indices and other features from PlanetScope 3B AnalyticMS SR imagery.

Generates multi-channel feature arrays including:
- Base bands: B, G, R, NIR
- Vegetation indices: NDVI, EVI
- Optional: SAVI, NDWI, etc.

Can be used standalone or imported as a module.
"""

import argparse
import numpy as np
import rasterio
from pathlib import Path
from typing import Optional

# Planet 3B AnalyticMS SR: B, G, R, NIR (bands 0, 1, 2, 3)
BAND_BLUE, BAND_GREEN, BAND_RED, BAND_NIR = 0, 1, 2, 3


def compute_ndvi(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """Compute Normalized Difference Vegetation Index (NDVI)."""
    red = np.asarray(red, dtype=np.float64)
    nir = np.asarray(nir, dtype=np.float64)
    denom = nir + red
    ndvi = np.full_like(red, np.nan)
    valid = denom != 0
    ndvi[valid] = (nir[valid] - red[valid]) / denom[valid]
    return ndvi


def compute_evi(blue: np.ndarray, red: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """
    Compute Enhanced Vegetation Index (EVI).
    
    Formula: EVI = 2.5 * (NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1)
    Better than NDVI in high biomass areas (saturates less).
    """
    blue = np.asarray(blue, dtype=np.float64)
    red = np.asarray(red, dtype=np.float64)
    nir = np.asarray(nir, dtype=np.float64)
    denom = nir + 6 * red - 7.5 * blue + 1
    evi = np.full_like(red, np.nan)
    valid = denom != 0
    evi[valid] = 2.5 * (nir[valid] - red[valid]) / denom[valid]
    return evi


def compute_savi(red: np.ndarray, nir: np.ndarray, l: float = 0.5) -> np.ndarray:
    """
    Compute Soil-Adjusted Vegetation Index (SAVI).
    
    Formula: SAVI = ((NIR - Red) / (NIR + Red + L)) * (1 + L)
    Better than NDVI in sparse vegetation areas.
    """
    red = np.asarray(red, dtype=np.float64)
    nir = np.asarray(nir, dtype=np.float64)
    denom = nir + red + l
    savi = np.full_like(red, np.nan)
    valid = denom != 0
    savi[valid] = ((nir[valid] - red[valid]) / denom[valid]) * (1 + l)
    return savi


def compute_ndwi(green: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """
    Compute Normalized Difference Water Index (NDWI).
    
    Formula: NDWI = (Green - NIR) / (Green + NIR)
    Helps separate water from vegetation.
    """
    green = np.asarray(green, dtype=np.float64)
    nir = np.asarray(nir, dtype=np.float64)
    denom = green + nir
    ndwi = np.full_like(green, np.nan)
    valid = denom != 0
    ndwi[valid] = (green[valid] - nir[valid]) / denom[valid]
    return ndwi


def compute_features(
    image_path: str | Path,
    output_path: Optional[str | Path] = None,
    include_ndvi: bool = True,
    include_evi: bool = True,
    include_savi: bool = False,
    include_ndwi: bool = False,
    normalize: bool = True,
) -> tuple[np.ndarray, dict]:
    """
    Compute features from PlanetScope SR image.
    
    Args:
        image_path: Path to *_3B_AnalyticMS_SR.tif
        output_path: Optional path to save multi-channel GeoTIFF
        include_ndvi: Include NDVI channel
        include_evi: Include EVI channel
        include_savi: Include SAVI channel
        include_ndwi: Include NDWI channel
        normalize: Normalize bands to 0-1 range (recommended for DL)
    
    Returns:
        Tuple of (features array, metadata dict)
        - features: (C, H, W) array where C = 4 base + indices
        - metadata: Rasterio metadata dict
    """
    image_path = Path(image_path)
    if not image_path.is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")

    with rasterio.open(image_path) as src:
        img = src.read()  # (C, H, W)
        meta = src.meta.copy()
        h, w = img.shape[1], img.shape[2]

    # Ensure 4 bands
    img = np.squeeze(img).astype(np.float32)
    if img.ndim == 2:
        img = np.stack([img] * 4, axis=0)
    elif img.shape[0] < 4:
        raise ValueError(f"Expected at least 4 bands, got {img.shape[0]}")
    elif img.shape[0] > 4:
        img = img[:4]  # Use first 4 bands (B, G, R, NIR)

    # Normalize bands to 0-1 range
    if normalize:
        for i in range(4):
            band = img[i]
            lo, hi = np.nanpercentile(band, (1, 99))
            if hi > lo:
                img[i] = np.clip((band - lo) / (hi - lo), 0, 1).astype(np.float32)
            else:
                img[i] = np.clip(band, 0, 1).astype(np.float32)

    blue = img[BAND_BLUE]
    green = img[BAND_GREEN]
    red = img[BAND_RED]
    nir = img[BAND_NIR]

    # Build feature stack
    features_list = [img]  # Start with 4 base bands

    if include_ndvi:
        ndvi = compute_ndvi(red, nir)
        # Normalize NDVI to 0-1 range; fill NaN (e.g. 0/0) with 0 to avoid training NaNs
        ndvi = np.clip((ndvi + 1) / 2, 0, 1).astype(np.float32)
        ndvi = np.nan_to_num(ndvi, nan=0.0, posinf=1.0, neginf=0.0)
        features_list.append(ndvi[np.newaxis, ...])

    if include_evi:
        evi = compute_evi(blue, red, nir)
        # Normalize EVI to 0-1 range; fill NaN with 0 to avoid training NaNs
        evi = np.clip((evi + 1) / 2, 0, 1).astype(np.float32)
        evi = np.nan_to_num(evi, nan=0.0, posinf=1.0, neginf=0.0)
        features_list.append(evi[np.newaxis, ...])

    if include_savi:
        savi = compute_savi(red, nir)
        # Normalize SAVI to 0-1 range (SAVI typically -1 to 1)
        savi = np.clip((savi + 1) / 2, 0, 1).astype(np.float32)
        features_list.append(savi[np.newaxis, ...])

    if include_ndwi:
        ndwi = compute_ndwi(green, nir)
        # Normalize NDWI to 0-1 range (NDWI typically -1 to 1)
        ndwi = np.clip((ndwi + 1) / 2, 0, 1).astype(np.float32)
        features_list.append(ndwi[np.newaxis, ...])

    features = np.concatenate(features_list, axis=0)  # (C, H, W)

    # Update metadata
    meta.update(count=features.shape[0], dtype=np.float32)

    # Save if output path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(output_path, "w", **meta) as dst:
            dst.write(features)
        print(f"Saved features ({features.shape[0]} channels) to {output_path}")

    return features, meta


def main():
    parser = argparse.ArgumentParser(
        description="Compute vegetation indices and features from PlanetScope SR image."
    )
    parser.add_argument("--image", required=True, help="Path to *_3B_AnalyticMS_SR.tif")
    parser.add_argument("--output", default=None, help="Output multi-channel GeoTIFF (optional)")
    parser.add_argument("--no-ndvi", action="store_true", help="Exclude NDVI")
    parser.add_argument("--no-evi", action="store_true", help="Exclude EVI")
    parser.add_argument("--savi", action="store_true", help="Include SAVI")
    parser.add_argument("--ndwi", action="store_true", help="Include NDWI")
    parser.add_argument("--no-normalize", action="store_true", help="Skip band normalization")
    args = parser.parse_args()

    features, meta = compute_features(
        args.image,
        args.output,
        include_ndvi=not args.no_ndvi,
        include_evi=not args.no_evi,
        include_savi=args.savi,
        include_ndwi=args.ndwi,
        normalize=not args.no_normalize,
    )

    print(f"Computed {features.shape[0]} channels: shape {features.shape}")
    print(f"  Channels: B, G, R, NIR", end="")
    if not args.no_ndvi:
        print(", NDVI", end="")
    if not args.no_evi:
        print(", EVI", end="")
    if args.savi:
        print(", SAVI", end="")
    if args.ndwi:
        print(", NDWI", end="")
    print()


if __name__ == "__main__":
    main()
