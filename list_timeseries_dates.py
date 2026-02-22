#!/usr/bin/env python3
"""
List PlanetScope timeseries files from GCS bucket and create a monthly summary table.
Standalone script that doesn't depend on gcs_utils.py for Python 3.5 compatibility.
"""

import argparse
from collections import defaultdict
from datetime import datetime
import re

try:
    from google.cloud import storage
except ImportError:
    print("ERROR: google-cloud-storage package not installed.")
    print("Please install it with: pip install google-cloud-storage")
    exit(1)


def get_gcs_client():
    """Get authenticated GCS client."""
    return storage.Client()


def list_all_blobs(bucket_name, prefix=""):
    """
    List all blob names in a GCS bucket with given prefix.
    
    Args:
        bucket_name: GCS bucket name
        prefix: Optional prefix to filter (e.g., "2024/")
    
    Returns:
        List of blob names
    """
    client = get_gcs_client()
    bucket = client.bucket(bucket_name)
    
    blobs = bucket.list_blobs(prefix=prefix)
    return [blob.name for blob in blobs]


def extract_date_from_filename(filename):
    """
    Extract date from filename.
    
    Looks for patterns like:
    - 20240102 (YYYYMMDD)
    - 20240102_162648_67_247d (scene ID format)
    
    Args:
        filename: Blob name or filename
    
    Returns:
        Tuple of (date_string, datetime_object) or None if no date found
    """
    # Pattern: YYYYMMDD (8 digits)
    date_pattern = r'(\d{8})'
    match = re.search(date_pattern, filename)
    
    if match:
        date_str = match.group(1)
        try:
            date_obj = datetime.strptime(date_str, '%Y%m%d')
            return date_str, date_obj
        except ValueError:
            return None
    
    return None


def create_monthly_summary(bucket_name, prefix=""):
    """
    Create monthly summary of images in GCS bucket.
    
    Args:
        bucket_name: GCS bucket name
        prefix: Optional prefix (e.g., "2024/")
    
    Returns:
        Dict with monthly counts and details
    """
    print("Listing files in gs://{}/{}...".format(bucket_name, prefix))
    blob_names = list_all_blobs(bucket_name, prefix)
    
    print("Found {} files".format(len(blob_names)))
    
    # Group by month
    monthly_counts = defaultdict(int)
    monthly_files = defaultdict(list)
    all_dates = []
    
    for blob_name in blob_names:
        result = extract_date_from_filename(blob_name)
        if result:
            date_str, date_obj = result
            month_key = date_obj.strftime('%Y-%m')
            monthly_counts[month_key] += 1
            monthly_files[month_key].append({
                'filename': blob_name.split('/')[-1],  # Just filename, not full path
                'date': date_str,
                'datetime': date_obj
            })
            all_dates.append(date_obj)
    
    # Sort months
    sorted_months = sorted(monthly_counts.keys())
    
    return {
        'monthly_counts': dict(monthly_counts),
        'monthly_files': dict(monthly_files),
        'sorted_months': sorted_months,
        'total_files': len(blob_names),
        'files_with_dates': len(all_dates),
        'date_range': (min(all_dates), max(all_dates)) if all_dates else None
    }


def print_summary_table(summary):
    """Print a formatted table of monthly counts."""
    print("\n" + "="*60)
    print("MONTHLY SUMMARY TABLE")
    print("="*60)
    print("{:<15} {:<20}".format('Month', 'Number of Images'))
    print("-"*60)
    
    for month in summary['sorted_months']:
        count = summary['monthly_counts'][month]
        print("{:<15} {:<20}".format(month, count))
    
    print("-"*60)
    print("{:<15} {:<20}".format('TOTAL', summary['files_with_dates']))
    print("="*60)
    
    if summary['date_range']:
        start_date, end_date = summary['date_range']
        print("\nDate range: {} to {}".format(
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        ))
    
    print("\nTotal files found: {}".format(summary['total_files']))
    print("Files with parseable dates: {}".format(summary['files_with_dates']))
    print("Files without dates: {}".format(summary['total_files'] - summary['files_with_dates']))


def print_detailed_monthly_info(summary):
    """Print detailed information for each month."""
    print("\n" + "="*60)
    print("DETAILED MONTHLY INFORMATION")
    print("="*60)
    
    for month in summary['sorted_months']:
        files = summary['monthly_files'][month]
        print("\n{} ({} images):".format(month, len(files)))
        print("-" * 60)
        
        # Sort files by date
        files_sorted = sorted(files, key=lambda x: x['datetime'])
        
        # Show first 5 and last 5 if there are many
        if len(files_sorted) <= 10:
            for f in files_sorted:
                print("  {} - {}".format(f['date'], f['filename']))
        else:
            print("  First 5:")
            for f in files_sorted[:5]:
                print("    {} - {}".format(f['date'], f['filename']))
            print("  ...")
            print("  Last 5:")
            for f in files_sorted[-5:]:
                print("    {} - {}".format(f['date'], f['filename']))


def main():
    parser = argparse.ArgumentParser(
        description="List PlanetScope timeseries files and create monthly summary."
    )
    parser.add_argument(
        "--bucket",
        required=True,
        help="GCS bucket name (e.g., 'ps4-woodedarea')"
    )
    parser.add_argument(
        "--prefix",
        default="2024/",
        help="Prefix in bucket (e.g., '2024/')"
    )
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed file listing for each month"
    )
    args = parser.parse_args()
    
    summary = create_monthly_summary(args.bucket, args.prefix)
    print_summary_table(summary)
    
    if args.detailed:
        print_detailed_monthly_info(summary)


if __name__ == "__main__":
    main()
