#!/usr/bin/env python3
"""
Train a U-Net for wooded/non-wooded segmentation using manual labels from multiple scenes in GCS.

Streams scenes from Google Cloud Storage, extracts patches, and trains a U-Net.
Uses feature engineering (NDVI, EVI) for better input representation.
"""

import argparse
import numpy as np
import rasterio
from pathlib import Path
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import random
import tempfile

from model_unet import UNet
from compute_features import compute_features
from gcs_utils import (
    list_scenes,
    stream_raster_from_gcs,
    check_scene_exists,
    download_scene_to_local,
)


class MultiScenePatchDataset(Dataset):
    """Dataset that extracts patches from multiple scenes (same as local version)."""
    
    def __init__(
        self,
        scenes: list[dict],
        patch_size: int,
        n_patches_per_epoch: int,
        augment: bool = True,
    ):
        self.scenes = scenes
        self.patch_size = patch_size
        self.n_patches_per_epoch = n_patches_per_epoch
        self.augment = augment
        
        if scenes:
            n_channels = scenes[0]['features'].shape[0]
            for i, scene in enumerate(scenes):
                if scene['features'].shape[0] != n_channels:
                    raise ValueError(
                        f"Scene {i} has {scene['features'].shape[0]} channels, "
                        f"expected {n_channels}"
                    )
            self.n_channels = n_channels
    
    def __len__(self):
        return self.n_patches_per_epoch
    
    def __getitem__(self, _):
        scene = random.choice(self.scenes)
        features = scene['features']
        label = scene['label']
        valid = scene['valid']
        
        H, W = label.shape
        p = self.patch_size
        
        r = np.random.randint(0, max(1, H - p + 1))
        c = np.random.randint(0, max(1, W - p + 1))
        
        feat_patch = features[:, r:r+p, c:c+p]
        lab_patch = label[r:r+p, c:c+p]
        valid_patch = valid[r:r+p, c:c+p]
        
        if self.augment:
            if random.random() < 0.5:
                feat_patch = np.flip(feat_patch, axis=2)
                lab_patch = np.flip(lab_patch, axis=1)
                valid_patch = np.flip(valid_patch, axis=1)
            if random.random() < 0.5:
                feat_patch = np.flip(feat_patch, axis=1)
                lab_patch = np.flip(lab_patch, axis=0)
                valid_patch = np.flip(valid_patch, axis=0)
            k = random.randint(0, 3)
            if k > 0:
                feat_patch = np.rot90(feat_patch, k=k, axes=(1, 2))
                lab_patch = np.rot90(lab_patch, k=k)
                valid_patch = np.rot90(valid_patch, k=k)
        
        lab_patch[~valid_patch] = 0
        
        x = torch.from_numpy(feat_patch.copy())
        y = torch.from_numpy(lab_patch.copy()).unsqueeze(0)
        mask = torch.from_numpy(valid_patch.copy()).unsqueeze(0)
        
        return x, y, mask


def load_scene_from_gcs(
    bucket_name: str,
    scene_id: str,
    prefix: str = "",
    cache_dir: Path | None = None,
    include_ndvi: bool = True,
    include_evi: bool = True,
) -> dict:
    """
    Load a scene from GCS with features and labels.
    
    Args:
        bucket_name: GCS bucket name
        scene_id: Scene ID
        prefix: Optional prefix in bucket
        cache_dir: Optional local cache directory (if None, uses temp)
        include_ndvi: Include NDVI channel
        include_evi: Include EVI channel
    
    Returns:
        Dict with keys: 'features', 'label', 'valid'
    """
    # Check what files exist
    exists = check_scene_exists(bucket_name, scene_id, prefix)
    if not exists['sr']:
        raise FileNotFoundError(f"SR image not found for scene {scene_id}")
    if not exists['reference']:
        raise FileNotFoundError(f"Reference raster not found for scene {scene_id}")
    
    # Use cache if provided, otherwise temp directory
    if cache_dir is None:
        cache_dir = Path(tempfile.mkdtemp())
    else:
        cache_dir = Path(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Download scene files to cache
    files = download_scene_to_local(bucket_name, scene_id, cache_dir, prefix)
    
    # Load and compute features
    features, _ = compute_features(
        files['sr'],
        include_ndvi=include_ndvi,
        include_evi=include_evi,
        normalize=True,
    )
    
    # Load reference label
    with rasterio.open(files['reference']) as src:
        label = src.read(1).astype(np.float32)
        h, w = label.shape
    
    if label.shape != (features.shape[1], features.shape[2]):
        raise ValueError(
            f"Label shape {label.shape} doesn't match image shape "
            f"({features.shape[1]}, {features.shape[2]})"
        )
    
    # Create valid mask
    valid = np.ones((h, w), dtype=bool)
    
    with rasterio.open(files['reference']) as src:
        if src.nodata is not None:
            valid &= label != src.nodata
    
    valid &= (label == 0) | (label == 1)
    
    # Apply UDM2 mask if available
    if files.get('udm2') and files['udm2'].is_file():
        with rasterio.open(files['udm2']) as udm_src:
            udm = udm_src.read(1, out_shape=(h, w), resampling=rasterio.enums.Resampling.nearest)
        valid &= udm != 0
    
    return {
        'features': features,
        'label': label,
        'valid': valid,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Train U-Net on multiple scenes from GCS with manual labels."
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
        help="Specific scene IDs to use (default: auto-detect all scenes with reference rasters)"
    )
    parser.add_argument(
        "--cache-dir",
        default=None,
        help="Local cache directory (default: temp directory)"
    )
    parser.add_argument(
        "--patch-size",
        type=int,
        default=64,
        help="Patch size (default: 64)"
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=50,
        help="Number of training epochs (default: 50)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
        help="Batch size (default: 16)"
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=1e-3,
        help="Learning rate (default: 1e-3)"
    )
    parser.add_argument(
        "--patches-per-epoch",
        type=int,
        default=1000,
        help="Patches per epoch (default: 1000)"
    )
    parser.add_argument(
        "--output",
        default="wooded_model_multi_scene_gcs.pt",
        help="Output model path (default: wooded_model_multi_scene_gcs.pt)"
    )
    parser.add_argument(
        "--no-ndvi",
        action="store_true",
        help="Exclude NDVI from features"
    )
    parser.add_argument(
        "--no-evi",
        action="store_true",
        help="Exclude EVI from features"
    )
    parser.add_argument(
        "--no-augment",
        action="store_true",
        help="Disable data augmentation"
    )
    parser.add_argument(
        "--early-stopping",
        type=int,
        default=10,
        help="Early stopping patience (epochs without improvement, default: 10, 0=disabled)"
    )
    args = parser.parse_args()

    # Find scenes with reference rasters
    if args.scene_ids:
        scene_ids = args.scene_ids
    else:
        print(f"Listing scenes in gs://{args.bucket}/{args.prefix}...")
        all_scenes = list_scenes(args.bucket, args.prefix)
        scene_ids = []
        for scene_id in all_scenes:
            exists = check_scene_exists(args.bucket, scene_id, args.prefix)
            if exists['sr'] and exists['reference']:
                scene_ids.append(scene_id)
    
    if not scene_ids:
        raise ValueError("No scenes with reference rasters found!")

    print(f"\nFound {len(scene_ids)} scenes with reference rasters:")
    for sid in scene_ids:
        print(f"  - {sid}")

    # Load all scenes
    print("\nLoading scenes from GCS...")
    scenes = []
    cache_dir = Path(args.cache_dir) if args.cache_dir else None
    
    for scene_id in scene_ids:
        try:
            scene_data = load_scene_from_gcs(
                args.bucket,
                scene_id,
                args.prefix,
                cache_dir,
                include_ndvi=not args.no_ndvi,
                include_evi=not args.no_evi,
            )
            scenes.append(scene_data)
            print(f"  Loaded {scene_id}: features shape {scene_data['features'].shape}, "
                  f"label shape {scene_data['label'].shape}")
        except Exception as e:
            print(f"Error loading {scene_id}: {e}")
            continue

    if not scenes:
        raise ValueError("No scenes loaded successfully!")

    # Determine number of input channels
    n_channels = scenes[0]['features'].shape[0]
    print(f"\nUsing {n_channels} input channels")

    # Create dataset
    dataset = MultiScenePatchDataset(
        scenes,
        patch_size=args.patch_size,
        n_patches_per_epoch=args.patches_per_epoch,
        augment=not args.no_augment,
    )
    loader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=0,
        pin_memory=True,
    )

    # Setup model and training
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    model = UNet(in_channels=n_channels, num_classes=1, base=32).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    criterion = nn.BCEWithLogitsLoss(reduction="none")

    # Training loop
    best_loss = float("inf")
    patience_counter = 0

    for epoch in range(args.epochs):
        model.train()
        running_loss = 0.0
        n_batches = 0

        for x, y, mask in loader:
            x, y, mask = x.to(device), y.to(device), mask.to(device)
            # Skip batches with no valid pixels to avoid NaN loss
            if mask.sum() < 1:
                continue
            opt.zero_grad()
            logits = model(x)
            loss_per_px = criterion(logits, y)
            loss = (loss_per_px * mask).sum() / (mask.sum() + 1e-8)
            if torch.isnan(loss) or torch.isinf(loss):
                continue
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            opt.step()
            running_loss += loss.item()
            n_batches += 1
        if n_batches == 0:
            print(f"Epoch {epoch+1}/{args.epochs}  (no valid batches, skipping)")
            continue

        avg_loss = running_loss / max(n_batches, 1)
        
        improved = avg_loss < best_loss
        if improved:
            best_loss = avg_loss
            patience_counter = 0
            torch.save(
                {
                    "state_dict": model.state_dict(),
                    "patch_size": args.patch_size,
                    "n_channels": n_channels,
                    "epoch": epoch + 1,
                    "loss": avg_loss,
                },
                args.output,
            )
        else:
            patience_counter += 1

        print(
            f"Epoch {epoch+1}/{args.epochs}  loss={avg_loss:.4f}  "
            f"best={best_loss:.4f}  {'*' if improved else ''}"
        )

        if args.early_stopping > 0 and patience_counter >= args.early_stopping:
            print(f"\nEarly stopping triggered after {epoch+1} epochs")
            break

    print(f"\nSaved best model to {args.output}")
    print(f"  Best loss: {best_loss:.4f}")
    print(f"  Input channels: {n_channels}")
    print(f"  Patch size: {args.patch_size}")


if __name__ == "__main__":
    main()
