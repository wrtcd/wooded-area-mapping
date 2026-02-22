#!/usr/bin/env python3
"""
Download one or more scenes from GCS to a local folder for manual labeling.

Use this to pull SR + UDM2 (and existing reference if any) so you can open
them in QGIS/ArcGIS, create reference_wooded.tif, then upload back to GCS.

Example:
  # List available scenes (see what's in the bucket)
  python list_timeseries_dates.py --bucket ps4-woodedarea --prefix 2024/ --detailed

  # Download specific scenes for labeling
  python download_scenes_for_labeling.py --bucket ps4-woodedarea --prefix 2024/ --scene SCENE_ID1 --scene SCENE_ID2 --out ./data/labeling

  # Download first 3 scenes (by listing then passing)
  python download_scenes_for_labeling.py --bucket ps4-woodedarea --prefix 2024/ --out ./data/labeling --max-scenes 3
"""

import argparse
from pathlib import Path

from gcs_utils import (
    list_scenes,
    check_scene_exists,
    download_scene_to_local,
)


def main():
    parser = argparse.ArgumentParser(
        description="Download scenes from GCS for manual labeling (wooded/non-wooded)."
    )
    parser.add_argument("--bucket", default="ps4-woodedarea", help="GCS bucket name")
    parser.add_argument(
        "--prefix",
        default="2024/",
        help="Prefix in bucket (e.g. 2024/ or scenes/)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("./data/labeling"),
        help="Local directory to save downloaded scenes",
    )
    parser.add_argument(
        "--scene",
        action="append",
        dest="scenes",
        help="Scene ID to download (e.g. 20240110_162648_67_247d). Can be repeated.",
    )
    parser.add_argument(
        "--max-scenes",
        type=int,
        default=None,
        help="If no --scene given, download first N scenes from the bucket (by sorted ID).",
    )
    args = parser.parse_args()

    bucket = args.bucket
    prefix = args.prefix
    out_dir = args.out
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.scenes:
        scene_ids = list(dict.fromkeys(args.scenes))  # preserve order, no dupes
    else:
        all_ids = list_scenes(bucket, prefix)
        if not all_ids:
            print(f"No scenes found in gs://{bucket}/{prefix}")
            return
        n = args.max_scenes if args.max_scenes is not None else len(all_ids)
        scene_ids = all_ids[:n]
        print(f"Using first {len(scene_ids)} scene(s) from bucket (total {len(all_ids)}).")

    for scene_id in scene_ids:
        exists = check_scene_exists(bucket, scene_id, prefix)
        if not exists["sr"]:
            print(f"Skip {scene_id}: no SR image in bucket.")
            continue
        # Download to a subfolder per scene so multiple scenes don't overwrite
        scene_out = out_dir / scene_id
        download_scene_to_local(bucket, scene_id, scene_out, prefix)
        print(f"Scene {scene_id} -> {scene_out}")
        if exists["reference"]:
            print(f"  (reference already in bucket; re-downloaded for editing)")

    print(f"\nDone. Open the SR GeoTIFFs in QGIS/ArcGIS and create:")
    print(f"  {{scene_id}}_reference_wooded.tif  (1=wooded, 0=non-wooded, NoData=unlabeled)")
    print(f"Then upload: gsutil cp .../{{scene_id}}_reference_wooded.tif gs://{bucket}/{prefix}")


if __name__ == "__main__":
    main()
