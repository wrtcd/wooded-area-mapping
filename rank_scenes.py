#!/usr/bin/env python3
"""
Rank scenes by cloud-free % and mean NDVI to pick the best image for wooded mapping.

Use on a **local directory** that contains multiple scenes (each with
*_3B_AnalyticMS_SR.tif and *_3B_udm2.tif). Optionally reads *_metadata.json
for cloud_percent / clear_percent when present (Planet metadata).

Output: table of scenes ranked by clear % then mean NDVI; recommends the best scene.
"""

import argparse
import json
import re
from pathlib import Path

import numpy as np
import rasterio

# Planet 3B: B, G, R, NIR
BAND_RED, BAND_NIR = 2, 3


def scene_id_from_path(p: Path) -> str | None:
    name = p.name
    m = re.match(r"^(.+)_3B_(?:AnalyticMS_SR|udm2)\.tif$", name, re.IGNORECASE)
    return m.group(1) if m else None


def date_from_scene_id(sid: str) -> str:
    """Extract YYYY-MM-DD from e.g. 20240110_162648_67_247d."""
    m = re.match(r"^(\d{4})(\d{2})(\d{2})", sid)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return sid


def clear_percent_from_udm2(udm_path: Path) -> float | None:
    """Compute % of valid (clear) pixels from UDM2. 0 = invalid, non-zero = valid."""
    try:
        with rasterio.open(udm_path) as src:
            data = src.read(1)
        valid = (data != 0).sum()
        total = data.size
        return 100.0 * valid / total if total else 0.0
    except Exception:
        return None


def cloud_or_clear_from_metadata(meta_path: Path) -> tuple[float | None, float | None]:
    """Read cloud_percent and/or clear_percent from Planet-style metadata JSON."""
    cloud_pct, clear_pct = None, None
    try:
        with open(meta_path, encoding="utf-8") as f:
            d = json.load(f)
        # Planet API / STAC style
        if isinstance(d, dict):
            cloud_pct = d.get("cloud_cover") or d.get("cloud_percent")
            clear_pct = d.get("clear_percent")
        return cloud_pct, clear_pct
    except Exception:
        return None, None


def mean_ndvi_from_sr(sr_path: Path, max_pixels: int = 2_000_000) -> float | None:
    """Compute mean NDVI from SR image, optionally subsampling to cap memory."""
    try:
        with rasterio.open(sr_path) as src:
            h, w = src.height, src.width
            n = h * w
            if n > max_pixels:
                # Read a window (center crop or strided) to stay under max_pixels
                step = int((n / max_pixels) ** 0.5) + 1
                rows = slice(0, h, step)
                cols = slice(0, w, step)
                red = src.read(BAND_RED + 1, window=(rows, cols))
                nir = src.read(BAND_NIR + 1, window=(rows, cols))
            else:
                red = src.read(BAND_RED + 1)
                nir = src.read(BAND_NIR + 1)
        red = np.squeeze(red).astype(np.float64)
        nir = np.squeeze(nir).astype(np.float64)
        denom = nir + red
        valid = denom != 0
        if not valid.any():
            return None
        ndvi = np.where(valid, (nir - red) / denom, np.nan)
        return float(np.nanmean(ndvi))
    except Exception:
        return None


def find_scene_pairs(root: Path) -> list[tuple[str, Path, Path, Path | None]]:
    """Return list of (scene_id, sr_path, udm2_path, metadata_path)."""
    root = root.resolve()
    sr_files = list(root.glob("*_3B_AnalyticMS_SR.tif")) + list(root.glob("*_3B_AnalyticMS_SR.TIF"))
    pairs = []
    for sr_path in sr_files:
        sid = scene_id_from_path(sr_path)
        if not sid:
            continue
        udm2 = root / f"{sid}_3B_udm2.tif"
        if not udm2.is_file():
            udm2 = root / f"{sid}_3B_udm2.TIF"
        if not udm2.is_file():
            continue
        meta = root / f"{sid}_metadata.json"
        if not meta.is_file():
            meta = None
        pairs.append((sid, sr_path, udm2, meta))
    return pairs


def main():
    parser = argparse.ArgumentParser(
        description="Rank scenes by clear % and mean NDVI; pick best for wooded mapping."
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default="data",
        help="Directory containing scene TIFs (default: data)",
    )
    parser.add_argument(
        "--min-clear",
        type=float,
        default=50.0,
        help="Minimum clear %% to consider (default: 50). Use 0 to include all.",
    )
    parser.add_argument(
        "--use-metadata-cloud",
        action="store_true",
        help="Prefer cloud_percent/clear_percent from *_metadata.json when present.",
    )
    parser.add_argument(
        "--no-ndvi",
        action="store_true",
        help="Skip NDVI computation (rank by clear %% only).",
    )
    args = parser.parse_args()

    root = Path(args.directory)
    if not root.is_dir():
        raise SystemExit(f"Not a directory: {root}")

    pairs = find_scene_pairs(root)
    if not pairs:
        print(f"No scene pairs (SR + UDM2) found in {root}")
        raise SystemExit(1)

    print(f"Found {len(pairs)} scene(s). Computing clear %% and mean NDVI...")
    rows = []
    for sid, sr_path, udm2_path, meta_path in pairs:
        date_str = date_from_scene_id(sid)
        clear_udm = clear_percent_from_udm2(udm2_path)
        cloud_meta, clear_meta = None, None
        if args.use_metadata_cloud and meta_path and meta_path.is_file():
            cloud_meta, clear_meta = cloud_or_clear_from_metadata(meta_path)
        # Prefer metadata clear % if available and we asked for it; else UDM2
        if clear_meta is not None and args.use_metadata_cloud:
            clear_pct = clear_meta
            source = "metadata"
        else:
            clear_pct = clear_udm
            source = "UDM2"
        mean_ndvi = None if args.no_ndvi else mean_ndvi_from_sr(sr_path)
        rows.append({
            "scene_id": sid,
            "date": date_str,
            "clear_pct": clear_pct,
            "clear_source": source,
            "cloud_meta": cloud_meta,
            "mean_ndvi": mean_ndvi,
        })

    # Filter by min clear
    eligible = [r for r in rows if r["clear_pct"] is not None and r["clear_pct"] >= args.min_clear]
    if not eligible:
        print(f"No scenes with clear %% >= {args.min_clear}. Showing all.")
        eligible = rows

    # Sort: mean NDVI descending (best vegetation first), then clear % descending (tie-break)
    def key(r):
        ndvi = r["mean_ndvi"] if r["mean_ndvi"] is not None else -2.0
        return (ndvi, r["clear_pct"] or 0)

    eligible.sort(key=key, reverse=True)

    print()
    print("Scene ranking (clear % and mean NDVI):")
    print("-" * 80)
    for r in eligible:
        ndvi_str = f"{r['mean_ndvi']:.3f}" if r["mean_ndvi"] is not None else "—"
        cloud_str = f"  cloud_meta={r['cloud_meta']:.1f}%" if r["cloud_meta"] is not None else ""
        print(f"  {r['date']}  {r['scene_id']}  clear={r['clear_pct']:.1f}% ({r['clear_source']})  mean_NDVI={ndvi_str}{cloud_str}")
    print("-" * 80)

    best = eligible[0]
    print(f"\nRecommended (best): {best['scene_id']}")
    print(f"  Date: {best['date']}  Clear: {best['clear_pct']:.1f}%  Mean NDVI: {best['mean_ndvi']}")
    print(f"\nUse this scene for mapping:")
    print(f"  --image {args.directory}/{best['scene_id']}_3B_AnalyticMS_SR.tif --udm {args.directory}/{best['scene_id']}_3B_udm2.tif")
    if best.get("cloud_meta") is not None:
        print(f"  (Metadata cloud_percent: {best['cloud_meta']:.1f}%)")


if __name__ == "__main__":
    main()
