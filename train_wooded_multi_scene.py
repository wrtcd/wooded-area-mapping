#!/usr/bin/env python3
"""
Train a U-Net for wooded/non-wooded segmentation using manual labels from multiple scenes.

Reads multiple Planet 3B AnalyticMS SR images with their reference rasters (manual labels),
extracts patches from all scenes, and trains a U-Net on the combined dataset.
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

from model_unet import UNet
from compute_features import compute_features


class MultiScenePatchDataset(Dataset):
    """
    Dataset that extracts patches from multiple scenes.
    
    Each scene has:
    - features: (C, H, W) multi-channel image (bands + indices)
    - label: (H, W) binary reference raster (1=wooded, 0=non-wooded)
    - valid: (H, W) boolean mask (True = valid pixel)
    """
    
    def __init__(
        self,
        scenes: list[dict],
        patch_size: int,
        n_patches_per_epoch: int,
        augment: bool = True,
    ):
        """
        Args:
            scenes: List of dicts with keys: 'features', 'label', 'valid' (all numpy arrays)
            patch_size: Size of patches to extract (e.g., 64)
            n_patches_per_epoch: Number of patches to sample per epoch
            augment: Apply data augmentation (flips, rotations)
        """
        self.scenes = scenes
        self.patch_size = patch_size
        self.n_patches_per_epoch = n_patches_per_epoch
        self.augment = augment
        
        # Validate all scenes have same number of channels
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
        # Randomly select a scene
        scene = random.choice(self.scenes)
        features = scene['features']  # (C, H, W)
        label = scene['label']  # (H, W)
        valid = scene['valid']  # (H, W)
        
        H, W = label.shape
        p = self.patch_size
        
        # Random crop
        r = np.random.randint(0, max(1, H - p + 1))
        c = np.random.randint(0, max(1, W - p + 1))
        
        feat_patch = features[:, r:r+p, c:c+p]  # (C, p, p)
        lab_patch = label[r:r+p, c:c+p]  # (p, p)
        valid_patch = valid[r:r+p, c:c+p]  # (p, p)
        
        # Data augmentation
        if self.augment:
            # Random horizontal flip
            if random.random() < 0.5:
                feat_patch = np.flip(feat_patch, axis=2)
                lab_patch = np.flip(lab_patch, axis=1)
                valid_patch = np.flip(valid_patch, axis=1)
            
            # Random vertical flip
            if random.random() < 0.5:
                feat_patch = np.flip(feat_patch, axis=1)
                lab_patch = np.flip(lab_patch, axis=0)
                valid_patch = np.flip(valid_patch, axis=0)
            
            # Random rotation (90°, 180°, 270°)
            k = random.randint(0, 3)
            if k > 0:
                feat_patch = np.rot90(feat_patch, k=k, axes=(1, 2))
                lab_patch = np.rot90(lab_patch, k=k)
                valid_patch = np.rot90(valid_patch, k=k)
        
        # Mask invalid pixels in label
        lab_patch[~valid_patch] = 0
        
        # Convert to tensors
        x = torch.from_numpy(feat_patch.copy())
        y = torch.from_numpy(lab_patch.copy()).unsqueeze(0)  # (1, p, p)
        mask = torch.from_numpy(valid_patch.copy()).unsqueeze(0)  # (1, p, p)
        
        return x, y, mask


def load_scene(
    image_path: Path,
    reference_path: Path,
    udm_path: Path | None = None,
    include_ndvi: bool = True,
    include_evi: bool = True,
) -> dict:
    """
    Load a scene with features and labels.
    
    Returns dict with keys: 'features', 'label', 'valid'
    """
    # Compute features (bands + indices)
    features, _ = compute_features(
        image_path,
        include_ndvi=include_ndvi,
        include_evi=include_evi,
        normalize=True,
    )
    
    # Load reference label
    with rasterio.open(reference_path) as src:
        label = src.read(1).astype(np.float32)
        h, w = label.shape
    
    # Ensure label matches feature dimensions
    if label.shape != (features.shape[1], features.shape[2]):
        raise ValueError(
            f"Label shape {label.shape} doesn't match image shape "
            f"({features.shape[1]}, {features.shape[2]})"
        )
    
    # Create valid mask
    valid = np.ones((h, w), dtype=bool)
    
    # Mask NoData in label
    with rasterio.open(reference_path) as src:
        if src.nodata is not None:
            valid &= label != src.nodata
    
    # Mask invalid pixels (not 0 or 1)
    valid &= (label == 0) | (label == 1)
    
    # Apply UDM2 mask if provided
    if udm_path and udm_path.is_file():
        with rasterio.open(udm_path) as udm_src:
            udm = udm_src.read(1, out_shape=(h, w), resampling=rasterio.enums.Resampling.nearest)
        valid &= udm != 0
    
    return {
        'features': features,
        'label': label,
        'valid': valid,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Train U-Net on multiple scenes with manual labels."
    )
    parser.add_argument(
        "--scenes-dir",
        required=True,
        help="Directory containing scenes (each scene: *_3B_AnalyticMS_SR.tif, *_reference_wooded.tif)"
    )
    parser.add_argument(
        "--scene-ids",
        nargs="+",
        default=None,
        help="Specific scene IDs to use (default: auto-detect all scenes with reference rasters)"
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
        default="wooded_model_multi_scene.pt",
        help="Output model path (default: wooded_model_multi_scene.pt)"
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

    scenes_dir = Path(args.scenes_dir)
    if not scenes_dir.is_dir():
        raise FileNotFoundError(f"Scenes directory not found: {scenes_dir}")

    # Find scenes with reference rasters
    if args.scene_ids:
        scene_ids = args.scene_ids
    else:
        # Auto-detect: find all SR images, check for matching reference
        sr_files = list(scenes_dir.glob("*_3B_AnalyticMS_SR.tif"))
        scene_ids = []
        for sr_file in sr_files:
            # Extract scene ID (e.g., "20240110_162648_67_247d" from "20240110_162648_67_247d_3B_AnalyticMS_SR.tif")
            scene_id = sr_file.stem.replace("_3B_AnalyticMS_SR", "")
            ref_file = scenes_dir / f"{scene_id}_reference_wooded.tif"
            if ref_file.is_file():
                scene_ids.append(scene_id)
    
    if not scene_ids:
        raise ValueError("No scenes with reference rasters found!")

    print(f"Found {len(scene_ids)} scenes with reference rasters:")
    for sid in scene_ids:
        print(f"  - {sid}")

    # Load all scenes
    print("\nLoading scenes...")
    scenes = []
    for scene_id in scene_ids:
        image_path = scenes_dir / f"{scene_id}_3B_AnalyticMS_SR.tif"
        reference_path = scenes_dir / f"{scene_id}_reference_wooded.tif"
        udm_path = scenes_dir / f"{scene_id}_3B_udm2.tif"
        
        if not image_path.is_file():
            print(f"Warning: Image not found for {scene_id}, skipping")
            continue
        if not reference_path.is_file():
            print(f"Warning: Reference not found for {scene_id}, skipping")
            continue
        
        try:
            scene_data = load_scene(
                image_path,
                reference_path,
                udm_path if udm_path.is_file() else None,
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
            opt.zero_grad()
            logits = model(x)
            loss_per_px = criterion(logits, y)
            loss = (loss_per_px * mask).sum() / (mask.sum() + 1e-8)
            loss.backward()
            opt.step()
            running_loss += loss.item()
            n_batches += 1

        avg_loss = running_loss / max(n_batches, 1)
        
        # Early stopping check
        improved = avg_loss < best_loss
        if improved:
            best_loss = avg_loss
            patience_counter = 0
            # Save best model
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
