#!/bin/bash
# Setup script for GCP VM to run wooded area mapping pipeline
# Run this on a fresh Ubuntu/Debian VM instance

set -e

echo "=== Setting up GCP VM for Wooded Area Mapping ==="

# Update system
echo "Updating system packages..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv git

# Install CUDA (if GPU VM)
if lspci | grep -i nvidia > /dev/null; then
    echo "NVIDIA GPU detected, installing CUDA..."
    # Note: For GCP, CUDA drivers are usually pre-installed on GPU images
    # If not, follow: https://cloud.google.com/compute/docs/gpus/install-drivers-gpu
    echo "CUDA installation skipped (assumes pre-installed drivers)"
else
    echo "No GPU detected, using CPU"
fi

# Create project directory
PROJECT_DIR="$HOME/wooded-area-mapping"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Clone repository (or copy files)
echo "Setting up project directory..."
# If using git:
# git clone <your-repo-url> .
# Or copy files manually

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Install Google Cloud SDK (if not already installed)
if ! command -v gcloud &> /dev/null; then
    echo "Installing Google Cloud SDK..."
    curl https://sdk.cloud.google.com | bash
    exec -l $SHELL
    gcloud init
fi

# Authenticate with GCS (if needed)
echo "Setting up GCS authentication..."
# Option 1: Use service account key file
# export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
# Option 2: Use gcloud auth application-default login
# gcloud auth application-default login

# Test GCS access
echo "Testing GCS access..."
python3 -c "from google.cloud import storage; client = storage.Client(); print('GCS access OK')" || echo "Warning: GCS authentication may be needed"

echo ""
echo "=== Setup Complete ==="
echo "Next steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Configure GCS credentials (see vm_workflow.md)"
echo "3. Run training: python train_wooded_multi_scene_gcs.py --bucket YOUR_BUCKET --scene-ids SCENE1 SCENE2 ..."
