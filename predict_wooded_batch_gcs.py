#!/usr/bin/env python3
"""
Batch inference for wooded/non-wooded mapping using a trained U-Net on scenes in GCS.

Streams scenes from GCS, runs inference, and uploads binary predictions back to GCS.
Optionally computes accuracy metrics if reference rasters are available.
"""

import argparse
import numpy as np
import rasterio
from pathlib import Path
import torch
import tempfile

from model_unet import UNet
from compute_features import compute_features
from gcs_utils import (
    list_scenes,
    check_scene_exists,
    download_scene_to_local,
    upload_file_to_gcs,
)
from accuracy_metrics import compute_accuracy_metrics


def predict_scene(
    model: torch.nn.Module,
    features: np.ndarray,
    valid_mask: np.ndarray,
    patch_size: int,
    batch_size: int,
    device: torch.device,
) -> np.ndarray:
    """
    Run inference on a scene using sliding window.
    
    Args:
        model: Trained U-Net model
        features: (C, H, W) feature array
        valid_mask: (H, W) boolean mask
        patch_size: Patch size used during training
        batch_size: Batch size for inference
        device: Device to run on
    
    Returns:
        Binary prediction array (H, W) with 1=wooded, 0=non-wooded, 255=NoData
    """
    model.eval()
    C, H, W = features.shape
    
    stride = max(1, patch_size // 2)
    prob = np.zeros((H, W), dtype=np.float32)
    count = np.zeros((H, W), dtype=np.float32)
    
    def get_patch(ro, co):
        r0 = max(0, ro)
        r1 = min(H, ro + patch_size)
        c0 = max(0, co)
        c1 = min(W, co + patch_size)
        pad_r0, pad_r1 = ro - r0, (ro + patch_size) - r1
        pad_c0, pad_c1 = co - c0, (co + patch_size) - c1
        patch = features[:, r0:r1, c0:c1]
        if pad_r0 > 0 or pad_r1 > 0 or pad_c0 > 0 or pad_c1 > 0:
            patch = np.pad(patch, ((0, 0), (pad_r0, pad_r1), (pad_c0, pad_c1)), mode="edge")
        return patch, r0, r1, c0, c1
    
    batches = []
    batch_boxes = []
    for ro in range(0, H, stride):
        for co in range(0, W, stride):
            patch, r0, r1, c0, c1 = get_patch(ro, co)
            batches.append(patch)
            batch_boxes.append((r0, r1, c0, c1))
            if len(batches) >= batch_size:
                x = torch.from_numpy(np.stack(batches, axis=0)).to(device)
                with torch.no_grad():
                    logits = model(x)
                    pred = torch.sigmoid(logits).cpu().numpy()
                for k, (r0, r1, c0, c1) in enumerate(batch_boxes):
                    dr, dc = r1 - r0, c1 - c0
                    prob[r0:r1, c0:c1] += pred[k, 0, :dr, :dc]
                    count[r0:r1, c0:c1] += 1
                batches, batch_boxes = [], []
    
    if batches:
        x = torch.from_numpy(np.stack(batches, axis=0)).to(device)
        with torch.no_grad():
            logits = model(x)
            pred = torch.sigmoid(logits).cpu().numpy()
        for k, (r0, r1, c0, c1) in enumerate(batch_boxes):
            dr, dc = r1 - r0, c1 - c0
            prob[r0:r1, c0:c1] += pred[k, 0, :dr, :dc]
            count[r0:r1, c0:c1] += 1
    
    count[count == 0] = 1
    prob /= count
    binary = (prob > 0.5).astype(np.uint8)
    binary[~valid_mask] = 255
    
    return binary


def main():
    parser = argparse.ArgumentParser(
        description="Batch inference on scenes in GCS using trained U-Net."
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
        "--model",
        required=True,
        help="Path to trained model checkpoint"
    )
    parser.add_argument(
        "--scene-ids",
        nargs="+",
        default=None,
        help="Specific scene IDs to process (default: all scenes with SR images)"
    )
    parser.add_argument(
        "--output-prefix",
        default="predictions/",
        help="Prefix for output files in bucket (default: 'predictions/')"
    )
    parser.add_argument(
        "--cache-dir",
        default=None,
        help="Local cache directory (default: temp directory)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=8,
        help="Batch size for inference (default: 8)"
    )
    parser.add_argument(
        "--no-ndvi",
        action="store_true",
        help="Exclude NDVI from features (must match training)"
    )
    parser.add_argument(
        "--no-evi",
        action="store_true",
        help="Exclude EVI from features (must match training)"
    )
    parser.add_argument(
        "--compute-metrics",
        action="store_true",
        help="Compute accuracy metrics if reference rasters are available"
    )
    args = parser.parse_args()

    # Load model
    if not Path(args.model).is_file():
        raise FileNotFoundError(f"Model not found: {args.model}")
    
    ckpt = torch.load(args.model, map_location="cpu")
    patch_size = ckpt.get("patch_size", 64)
    n_channels = ckpt.get("n_channels", 4)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    model = UNet(in_channels=n_channels, num_classes=1, base=32).to(device)
    model.load_state_dict(ckpt["state_dict"])
    print(f"Loaded model: {n_channels} channels, patch size {patch_size}")

    # Find scenes to process
    if args.scene_ids:
        scene_ids = args.scene_ids
    else:
        print(f"Listing scenes in gs://{args.bucket}/{args.prefix}...")
        scene_ids = list_scenes(args.bucket, args.prefix)
    
    if not scene_ids:
        raise ValueError("No scenes found!")
    
    print(f"\nProcessing {len(scene_ids)} scenes...")

    # Setup cache directory
    cache_dir = Path(args.cache_dir) if args.cache_dir else Path(tempfile.mkdtemp())
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Process each scene
    for i, scene_id in enumerate(scene_ids):
        print(f"\n[{i+1}/{len(scene_ids)}] Processing {scene_id}...")
        
        # Check if scene exists
        exists = check_scene_exists(args.bucket, scene_id, args.prefix)
        if not exists['sr']:
            print(f"  Warning: SR image not found, skipping")
            continue
        
        try:
            # Download scene files
            files = download_scene_to_local(args.bucket, scene_id, cache_dir, args.prefix)
            
            # Compute features
            features, meta = compute_features(
                files['sr'],
                include_ndvi=not args.no_ndvi,
                include_evi=not args.no_evi,
                normalize=True,
            )
            
            if features.shape[0] != n_channels:
                raise ValueError(
                    f"Feature channels ({features.shape[0]}) don't match model ({n_channels})"
                )
            
            # Create valid mask
            h, w = features.shape[1], features.shape[2]
            valid_mask = np.ones((h, w), dtype=bool)
            
            if files.get('udm2') and files['udm2'].is_file():
                with rasterio.open(files['udm2']) as udm_src:
                    udm = udm_src.read(1, out_shape=(h, w), resampling=rasterio.enums.Resampling.nearest)
                valid_mask = udm != 0
            
            # Run inference
            binary = predict_scene(
                model,
                features,
                valid_mask,
                patch_size,
                args.batch_size,
                device,
            )
            
            # Save prediction locally
            meta.update(count=1, dtype=np.uint8, nodata=255, compress="lzw")
            pred_local = cache_dir / f"{scene_id}_wooded_binary.tif"
            with rasterio.open(pred_local, "w", **meta) as dst:
                dst.write(binary, 1)
            
            # Upload to GCS
            blob_path = f"{args.output_prefix}{scene_id}_wooded_binary.tif".lstrip("/")
            upload_file_to_gcs(pred_local, args.bucket, blob_path)
            
            n_wooded = int((binary == 1).sum())
            n_non = int((binary == 0).sum())
            n_nodata = int((binary == 255).sum())
            print(f"  Wooded: {n_wooded} px, Non-wooded: {n_non} px, NoData: {n_nodata} px")
            
            # Compute accuracy metrics if requested and reference available
            if args.compute_metrics and files.get('reference') and files['reference'].is_file():
                print("  Computing accuracy metrics...")
                try:
                    metrics = compute_accuracy_metrics(str(pred_local), str(files['reference']))
                    cm = metrics["confusion_matrix"]
                    print(f"    Accuracy: {metrics['accuracy']:.4f}")
                    print(f"    Precision: {metrics['precision']:.4f}")
                    print(f"    Recall: {metrics['recall']:.4f}")
                    print(f"    F1: {metrics['f1']:.4f}")
                    print(f"    Kappa: {metrics['kappa']:.4f}")
                except Exception as e:
                    print(f"    Error computing metrics: {e}")
        
        except Exception as e:
            print(f"  Error processing {scene_id}: {e}")
            continue
    
    print(f"\nCompleted processing {len(scene_ids)} scenes")


if __name__ == "__main__":
    main()
