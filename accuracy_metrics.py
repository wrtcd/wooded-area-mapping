#!/usr/bin/env python3
"""
Compute classification accuracy metrics when you have a reference (ground truth) raster.

Compares predicted binary raster (e.g. from wooded_map_single_image.py) to a
reference raster with the same extent. Both use 1 = wooded, 0 = non-wooded;
NoData is ignored. Outputs confusion matrix, accuracy, precision, recall, F1, Kappa.
"""

import argparse
import numpy as np
import rasterio
from pathlib import Path


def compute_accuracy_metrics(predicted_path: str, reference_path: str, pred_nodata: int = 255, ref_nodata: int | None = None) -> dict:
    """
    Compute accuracy metrics for predicted vs reference binary raster.
    
    Returns dict with: accuracy, precision, recall, f1, kappa, confusion_matrix (tp, tn, fp, fn).
    """
    pred_path = Path(predicted_path)
    ref_path = Path(reference_path)
    if not pred_path.is_file():
        raise FileNotFoundError(f"Predicted not found: {pred_path}")
    if not ref_path.is_file():
        raise FileNotFoundError(f"Reference not found: {ref_path}")

    with rasterio.open(pred_path) as pred_src, rasterio.open(ref_path) as ref_src:
        pred = pred_src.read(1)
        ref = ref_src.read(1)
        ref_nodata_val = ref_nodata if ref_nodata is not None else ref_src.nodata

    pred = np.squeeze(pred).astype(np.int64)
    ref = np.squeeze(ref).astype(np.int64)

    if pred.shape != ref.shape:
        raise ValueError("Predicted and reference rasters must have the same shape.")

    # Valid mask: both have a valid class (0 or 1), not NoData
    valid_ref = (ref == 0) | (ref == 1)
    if ref_nodata_val is not None:
        valid_ref &= ref != ref_nodata_val
    valid_pred = (pred == 0) | (pred == 1)
    valid = valid_ref & valid_pred

    y_true = ref[valid]
    y_pred = pred[valid]
    n_valid = int(valid.sum())
    n_skip = int((~valid).sum())

    # Confusion matrix: rows = true, cols = pred; order 0 (non-wooded), 1 (wooded)
    # tn, fp, fn, tp
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())

    accuracy = (tp + tn) / n_valid if n_valid else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    # Cohen's Kappa
    po = accuracy
    pe = ((tp + fp) * (tp + fn) + (fn + tn) * (fp + tn)) / (n_valid * n_valid) if n_valid else 0.0
    kappa = (po - pe) / (1 - pe) if (1 - pe) != 0 else 0.0

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "kappa": kappa,
        "confusion_matrix": {"tp": tp, "tn": tn, "fp": fp, "fn": fn},
        "n_valid": n_valid,
        "n_skip": n_skip,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Accuracy metrics for predicted vs reference binary raster."
    )
    parser.add_argument("--predicted", required=True, help="Predicted binary GeoTIFF (1=wooded, 0=non-wooded)")
    parser.add_argument("--reference", required=True, help="Reference (ground truth) binary GeoTIFF, same extent")
    parser.add_argument("--pred-nodata", type=int, default=255, help="NoData value in predicted raster")
    parser.add_argument("--ref-nodata", type=int, default=None, help="NoData value in reference (default: read from file)")
    args = parser.parse_args()

    metrics = compute_accuracy_metrics(args.predicted, args.reference, args.pred_nodata, args.ref_nodata)
    cm = metrics["confusion_matrix"]

    print("Valid pixels (used for metrics):", metrics["n_valid"])
    print("Pixels skipped (NoData or invalid):", metrics["n_skip"])
    print()
    print("Confusion matrix (rows = reference, cols = predicted)")
    print("                    Pred 0 (non-wooded)  Pred 1 (wooded)")
    print("Ref 0 (non-wooded)       TN =", cm["tn"], "            FP =", cm["fp"])
    print("Ref 1 (wooded)           FN =", cm["fn"], "            TP =", cm["tp"])
    print()
    print("Metrics:")
    print(f"  Accuracy:  {metrics['accuracy']:.4f}")
    print(f"  Precision (wooded): {metrics['precision']:.4f}  (TP / (TP+FP))")
    print(f"  Recall (wooded):     {metrics['recall']:.4f}  (TP / (TP+FN))")
    print(f"  F1 (wooded):         {metrics['f1']:.4f}")
    print(f"  Kappa:               {metrics['kappa']:.4f}")


if __name__ == "__main__":
    main()
