#!/usr/bin/env python3
"""
Train a U-Net for wooded/non-wooded segmentation using NDVI-threshold proxy labels.

Reads one (or more) Planet 3B AnalyticMS SR images, builds labels from NDVI > threshold
and optional UDM2 mask, extracts patches, and trains a small U-Net. Saves the best model
for use with predict_wooded_dl.py.
"""

import argparse
import numpy as np
import rasterio
from pathlib import Path
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

from model_unet import UNet

# Planet 3B: B, G, R, NIR (0,1,2,3)
BAND_RED, BAND_NIR = 2, 3


def compute_ndvi(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
    red = np.asarray(red, dtype=np.float64)
    nir = np.asarray(nir, dtype=np.float64)
    denom = nir + red
    ndvi = np.full_like(red, np.nan)
    valid = denom != 0
    ndvi[valid] = (nir[valid] - red[valid]) / denom[valid]
    return ndvi


def load_valid_mask(udm_path: Path, shape: tuple) -> np.ndarray:
    with rasterio.open(udm_path) as src:
        data = src.read(1, out_shape=shape, resampling=rasterio.enums.Resampling.nearest)
    return data != 0


class PatchDataset(Dataset):
    def __init__(self, image: np.ndarray, label: np.ndarray, valid: np.ndarray, patch_size: int, n_patches: int):
        # image: (C, H, W), label/valid: (H, W)
        self.image = np.asarray(image, dtype=np.float32)
        self.label = np.asarray(label, dtype=np.float32)
        self.valid = np.asarray(valid, dtype=bool)
        self.patch_size = patch_size
        self.n_patches = n_patches
        self.H, self.W = label.shape

    def __len__(self):
        return self.n_patches

    def __getitem__(self, _):
        p = self.patch_size
        # Random crop; ensure we stay in bounds
        r = np.random.randint(0, max(1, self.H - p + 1))
        c = np.random.randint(0, max(1, self.W - p + 1))
        img = self.image[:, r : r + p, c : c + p]
        lab = self.label[r : r + p, c : c + p]
        v = self.valid[r : r + p, c : c + p]
        # Only use patches that have some valid pixels and both classes if possible
        if not v.any():
            lab = np.zeros_like(lab)
        else:
            lab[~v] = 0  # ignore invalid in loss via mask
        x = torch.from_numpy(img)
        y = torch.from_numpy(lab).unsqueeze(0)
        return x, y, torch.from_numpy(v).unsqueeze(0)


def main():
    parser = argparse.ArgumentParser(description="Train U-Net for wooded map (NDVI proxy labels).")
    parser.add_argument("--image", required=True, help="Path to *_3B_AnalyticMS_SR.tif")
    parser.add_argument("--udm", default=None, help="Path to *_3B_udm2.tif (optional)")
    parser.add_argument("--ndvi-threshold", type=float, default=0.4)
    parser.add_argument("--patch-size", type=int, default=64)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--patches-per-epoch", type=int, default=500)
    parser.add_argument("--output", default="wooded_unet.pt", help="Output model path")
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")

    with rasterio.open(image_path) as src:
        img = src.read()  # (C, H, W)
        h, w = img.shape[1], img.shape[2]

    # Normalize to 0–1 (reflectance often in 0–1 or 0–1e4; clip and scale)
    img = np.squeeze(img).astype(np.float32)
    if img.ndim == 2:
        img = img[np.newaxis, ...]
    for i in range(img.shape[0]):
        band = img[i]
        lo, hi = np.nanpercentile(band, (1, 99))
        if hi > lo:
            img[i] = np.clip((band - lo) / (hi - lo), 0, 1).astype(np.float32)
        else:
            img[i] = np.clip(band, 0, 1).astype(np.float32)

    red = img[BAND_RED]
    nir = img[BAND_NIR]
    ndvi = compute_ndvi(red, nir)
    label = (ndvi > args.ndvi_threshold).astype(np.float32)
    label[np.isnan(ndvi)] = 0

    valid = np.ones((h, w), dtype=bool)
    if args.udm:
        udm_path = Path(args.udm)
        if udm_path.is_file():
            valid = load_valid_mask(udm_path, (h, w))

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    dataset = PatchDataset(
        img, label, valid,
        patch_size=args.patch_size,
        n_patches=args.patches_per_epoch,
    )
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True, num_workers=0, pin_memory=(device.type == "cuda"))

    model = UNet(in_channels=4, num_classes=1, base=32).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    criterion = nn.BCEWithLogitsLoss(reduction="none")

    best_loss = float("inf")
    for epoch in range(args.epochs):
        model.train()
        running = 0.0
        n = 0
        for x, y, mask in loader:
            x, y, mask = x.to(device), y.to(device), mask.to(device)
            opt.zero_grad()
            logits = model(x)
            loss_per_px = criterion(logits, y)
            loss = (loss_per_px * mask).sum() / (mask.sum() + 1e-8)
            loss.backward()
            opt.step()
            running += loss.item()
            n += 1
        avg = running / max(n, 1)
        if avg < best_loss:
            best_loss = avg
            torch.save({"state_dict": model.state_dict(), "patch_size": args.patch_size}, args.output)
        print(f"Epoch {epoch+1}/{args.epochs}  loss={avg:.4f}  best={best_loss:.4f}")

    print(f"Saved best model to {args.output}")


if __name__ == "__main__":
    main()
