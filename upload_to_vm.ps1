# PowerShell script to upload project files to GCP VM
# Usage: .\upload_to_vm.ps1

param(
    [string]$VMName = "wooded-mapping-vm",
    [string]$Zone = "us-central1-a",
    [string]$RemotePath = "~/wooded-area-mapping"
)

Write-Host "=== Uploading Project Files to GCP VM ===" -ForegroundColor Green
Write-Host "VM: $VMName" -ForegroundColor Yellow
Write-Host "Zone: $Zone" -ForegroundColor Yellow
Write-Host "Remote Path: $RemotePath" -ForegroundColor Yellow
Write-Host ""

# Get current directory (project root)
$ProjectRoot = $PSScriptRoot
if (-not $ProjectRoot) {
    $ProjectRoot = Get-Location
}

Write-Host "Project root: $ProjectRoot" -ForegroundColor Cyan
Write-Host ""

# Files to upload (excluding venv, cache, etc.)
$FilesToUpload = @(
    "*.py",
    "*.md",
    "*.txt",
    "*.sh"
)

Write-Host "Creating temporary archive..." -ForegroundColor Green

# Create temp directory
$TempDir = [System.IO.Path]::GetTempPath()
$ArchiveName = "wooded-area-mapping-$(Get-Date -Format 'yyyyMMdd-HHmmss').tar.gz"
$ArchivePath = Join-Path $TempDir $ArchiveName

# Note: On Windows, we'll need to use WSL or tar.exe (Windows 10+)
# For now, let's try using gcloud compute scp with individual files

Write-Host "Uploading files to VM..." -ForegroundColor Green
Write-Host "Note: This may take a few minutes..." -ForegroundColor Yellow

# Upload key files
$KeyFiles = @(
    "requirements.txt",
    "setup_vm.sh",
    "list_timeseries_dates.py",
    "train_wooded_multi_scene_gcs.py",
    "predict_wooded_batch_gcs.py",
    "predict_wooded_dl.py",
    "compute_features.py",
    "compute_temporal_features.py",
    "accuracy_metrics.py",
    "model_unet.py",
    "gcs_utils.py",
    "README.md",
    "GETTING_STARTED.md",
    "GCP_VM_SETUP_GUIDE.md",
    "vm_workflow.md",
    "WOODED_AREA_DEFINITION.md"
)

foreach ($file in $KeyFiles) {
    $LocalPath = Join-Path $ProjectRoot $file
    if (Test-Path $LocalPath) {
        Write-Host "Uploading $file..." -ForegroundColor Cyan
        gcloud compute scp $LocalPath "${VMName}:${RemotePath}/" --zone=$Zone
    } else {
        Write-Host "Skipping $file (not found)" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "=== Upload Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. SSH into VM: gcloud compute ssh $VMName --zone=$Zone" -ForegroundColor Cyan
Write-Host "2. Navigate to: cd $RemotePath" -ForegroundColor Cyan
Write-Host "3. Run setup: chmod +x setup_vm.sh && ./setup_vm.sh" -ForegroundColor Cyan
