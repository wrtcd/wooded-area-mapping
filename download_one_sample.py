#!/usr/bin/env python3
"""
Download one sample scene (1 SR TIF + 1 UDM2 TIF) from the shared Google Drive folder.

Uses gdown to list folder contents (first 50 files) and download only one scene's
*_3B_AnalyticMS_SR.tif and *_3B_udm2.tif. No manual picking in Drive needed.

Requires: pip install gdown
"""

import re
import os
from pathlib import Path

try:
    import gdown
except ImportError:
    raise SystemExit("Install gdown first: pip install gdown")

# Your shared folder
FOLDER_ID = "12-tmwMfB5P7AYhsh2yHAPcyYTYfMUIsC"
FOLDER_URL = f"https://drive.google.com/drive/folders/{FOLDER_ID}"


def scene_id_from_filename(name: str) -> str | None:
    """Extract scene base ID, e.g. 20240110_162648_67_247d from ..._3B_AnalyticMS_SR.tif."""
    # Pattern: YYYYMMDD_HHMMSS_*_*  before _3B_
    m = re.match(r"^(.+)_3B_(?:AnalyticMS_SR|udm2)\.tif$", name, re.IGNORECASE)
    return m.group(1) if m else None


def main():
    out_dir = Path(__file__).resolve().parent / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    print("Listing folder contents (first 50 files)...")
    try:
        files = gdown.download_folder(
            id=FOLDER_ID,
            skip_download=True,
            quiet=True,
            remaining_ok=True,
        )
    except Exception as e:
        print(f"Failed to list folder: {e}")
        print("Ensure the folder is shared with 'Anyone with the link' (viewer).")
        raise SystemExit(1)

    if not files:
        print("No files found in folder.")
        raise SystemExit(1)

    # Build: scene_id -> { 'sr': (id, name), 'udm2': (id, name) }
    by_scene = {}
    for f in files:
        name = os.path.basename(f.path)
        sid = scene_id_from_filename(name)
        if not sid:
            continue
        if sid not in by_scene:
            by_scene[sid] = {}
        if "_3B_AnalyticMS_SR.tif" in name:
            by_scene[sid]["sr"] = (f.id, name)
        if "_3B_udm2.tif" in name:
            by_scene[sid]["udm2"] = (f.id, name)

    # Pick first scene that has both
    chosen_sr = chosen_udm2 = None
    for sid, parts in by_scene.items():
        if "sr" in parts and "udm2" in parts:
            chosen_sr = parts["sr"]
            chosen_udm2 = parts["udm2"]
            print(f"Using scene: {sid}")
            break

    if not chosen_sr or not chosen_udm2:
        print("No complete scene (SR + UDM2) found in the first 50 files.")
        print("Try sharing the folder as 'Anyone with the link' or run again.")
        raise SystemExit(1)

    sr_id, sr_name = chosen_sr
    udm_id, udm_name = chosen_udm2

    sr_path = out_dir / sr_name
    udm_path = out_dir / udm_name

    print(f"Downloading 1) {sr_name} ...")
    gdown.download(id=sr_id, output=str(sr_path), quiet=False, fuzzy=True)
    if not sr_path.is_file():
        print("SR download failed.")
        raise SystemExit(1)

    print(f"Downloading 2) {udm_name} ...")
    gdown.download(id=udm_id, output=str(udm_path), quiet=False, fuzzy=True)
    if not udm_path.is_file():
        print("UDM2 download failed.")
        raise SystemExit(1)

    print("Done. Sample files:")
    print(f"  {sr_path}")
    print(f"  {udm_path}")
    print("\nRun wooded map:")
    print(f'  python wooded_map_single_image.py --image "{sr_path}" --udm "{udm_path}" --output wooded_binary.tif')


if __name__ == "__main__":
    main()
