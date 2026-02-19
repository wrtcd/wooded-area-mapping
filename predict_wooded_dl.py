#!/usr/bin/env python3
"""
Predict wooded/non-wooded map using a trained U-Net. Outputs binary GeoTIFF.
Automatically computes accuracy metrics if reference data is provided.
"""

import argparse
import numpy as np
import rasterio
from pathlib import Path
import torch

from model_unet import UNet


def main():
    parser = argparse.ArgumentParser(description="Predict wooded map with trained U-Net.")
    parser.add_argument("--image", required=True, help="Path to *_3B_AnalyticMS_SR.tif")
    parser.add_argument("--model", default="wooded_unet.pt", help="Path to trained model")
    parser.add_argument("--udm", default=None, help="Path to *_3B_udm2.tif (mask NoData)")
    parser.add_argument("--output", default="wooded_dl_binary.tif", help="Output binary GeoTIFF")
    parser.add_argument("--reference", default=None, help="Path to reference raster (for accuracy metrics). Auto-detected if {scene_id}_reference_wooded.tif exists.")
    parser.add_argument("--batch-size", type=int, default=8)
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")
    if not Path(args.model).is_file():
        raise FileNotFoundError(f"Model not found: {args.model}")

    ckpt = torch.load(args.model, map_location="cpu")
    patch_size = ckpt.get("patch_size", 64)
    n_channels = ckpt.get("n_channels", 4)  # Support models with different channel counts
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = UNet(in_channels=n_channels, num_classes=1, base=32).to(device)
    model.load_state_dict(ckpt["state_dict"])
    model.eval()

    with rasterio.open(image_path) as src:
        meta = src.meta.copy()
        img = src.read()
        transform = src.transform
        crs = src.crs
        h, w = img.shape[1], img.shape[2]

    # Use compute_features if model expects more than 4 channels
    if n_channels > 4:
        from compute_features import compute_features
        img, _ = compute_features(
            image_path,
            include_ndvi=True,
            include_evi=True,
            normalize=True,
        )
        if img.shape[0] != n_channels:
            raise ValueError(
                f"Feature channels ({img.shape[0]}) don't match model ({n_channels}). "
                f"Use --no-ndvi or --no-evi if model was trained without indices."
            )
    else:
        # Legacy: 4-band processing
        img = np.squeeze(img).astype(np.float32)
        if img.ndim == 2:
            img = np.stack([img] * 4, axis=0)
        elif img.shape[0] != 4:
            raise ValueError("Expected 4 bands (B,G,R,NIR).")
        for i in range(4):
            band = img[i]
            lo, hi = np.nanpercentile(band, (1, 99))
            if hi > lo:
                img[i] = np.clip((band - lo) / (hi - lo), 0, 1).astype(np.float32)
            else:
                img[i] = np.clip(band, 0, 1).astype(np.float32)

    valid_mask = np.ones((h, w), dtype=bool)
    if args.udm and Path(args.udm).is_file():
        with rasterio.open(args.udm) as udm_src:
            udm = udm_src.read(1, out_shape=(h, w), resampling=rasterio.enums.Resampling.nearest)
        valid_mask = udm != 0

    stride = max(1, patch_size // 2)
    prob = np.zeros((h, w), dtype=np.float32)
    count = np.zeros((h, w), dtype=np.float32)

    def get_patch(ro, co):
        r0 = max(0, ro)
        r1 = min(h, ro + patch_size)
        c0 = max(0, co)
        c1 = min(w, co + patch_size)
        pad_r0, pad_r1 = ro - r0, (ro + patch_size) - r1
        pad_c0, pad_c1 = co - c0, (co + patch_size) - c1
        patch = img[:, r0:r1, c0:c1]
        if pad_r0 > 0 or pad_r1 > 0 or pad_c0 > 0 or pad_c1 > 0:
            patch = np.pad(patch, ((0, 0), (pad_r0, pad_r1), (pad_c0, pad_c1)), mode="edge")
        return patch, r0, r1, c0, c1

    batches = []
    batch_boxes = []
    for ro in range(0, h, stride):
        for co in range(0, w, stride):
            patch, r0, r1, c0, c1 = get_patch(ro, co)
            batches.append(patch)
            batch_boxes.append((r0, r1, c0, c1))
            if len(batches) >= args.batch_size:
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

    meta.update(count=1, dtype=np.uint8, nodata=255, compress="lzw")
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(out_path, "w", **meta) as dst:
        dst.write(binary, 1)

    n_wooded = int((binary == 1).sum())
    n_non = int((binary == 0).sum())
    n_nodata = int((binary == 255).sum())
    print(f"Wrote binary map: {out_path}")
    print(f"  Wooded (1): {n_wooded} px; Non-wooded (0): {n_non} px; NoData: {n_nodata} px")

    # Auto-compute accuracy metrics if reference is available
    ref_path = args.reference
    if ref_path is None:
        # Try to auto-detect reference: same directory as image, {scene_id}_reference_wooded.tif
        scene_id = image_path.stem.replace("_3B_AnalyticMS_SR", "").replace("_3B_AnalyticMS", "")
        ref_candidate = image_path.parent / f"{scene_id}_reference_wooded.tif"
        if ref_candidate.is_file():
            ref_path = ref_candidate
            print(f"Auto-detected reference: {ref_path}")

    if ref_path and Path(ref_path).is_file():
        print("\nComputing accuracy metrics...")
        from accuracy_metrics import compute_accuracy_metrics
        metrics = compute_accuracy_metrics(str(out_path), str(ref_path))
        cm = metrics["confusion_matrix"]
        print(f"Valid pixels: {metrics['n_valid']}, Skipped: {metrics['n_skip']}")
        print("Confusion matrix (rows = reference, cols = predicted):")
        print("                    Pred 0 (non-wooded)  Pred 1 (wooded)")
        print(f"Ref 0 (non-wooded)       TN = {cm['tn']:6d}            FP = {cm['fp']:6d}")
        print(f"Ref 1 (wooded)           FN = {cm['fn']:6d}            TP = {cm['tp']:6d}")
        print("\nMetrics:")
        print(f"  Accuracy:  {metrics['accuracy']:.4f}")
        print(f"  Precision (wooded): {metrics['precision']:.4f}  (TP / (TP+FP))")
        print(f"  Recall (wooded):     {metrics['recall']:.4f}  (TP / (TP+FN))")
        print(f"  F1 (wooded):         {metrics['f1']:.4f}")
        print(f"  Kappa:               {metrics['kappa']:.4f}")


if __name__ == "__main__":
    main()
