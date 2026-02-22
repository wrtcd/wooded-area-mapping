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

# Determine project directory
# If script is run from project directory, use current directory
# Otherwise, create/use ~/wooded-area-mapping
if [ -f "requirements.txt" ] && [ -f "setup_vm.sh" ]; then
    PROJECT_DIR="$(pwd)"
    echo "Using current directory as project directory: $PROJECT_DIR"
else
    PROJECT_DIR="$HOME/wooded-area-mapping"
    mkdir -p "$PROJECT_DIR"
    echo "Project directory: $PROJECT_DIR"
    echo "Note: Make sure project files (requirements.txt, *.py) are in this directory"
    echo "You can upload files using: gcloud compute scp <files> $USER@wooded-mapping-vm:$PROJECT_DIR/"
fi
cd "$PROJECT_DIR"

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
if python3 -c "from google.cloud import storage; client = storage.Client(); buckets = list(client.list_buckets()); print('GCS access OK! Found', len(buckets), 'buckets')" 2>/dev/null; then
    echo "✓ GCS authentication successful"
else
    echo "⚠ Warning: GCS authentication may be needed"
    echo "Run: gcloud auth application-default login"
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Project directory: $PROJECT_DIR"
echo ""
echo "Next steps:"
echo "1. Activate virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Test GCS access (if not already working):"
echo "   gcloud auth application-default login"
echo ""
echo "3. List timeseries dates:"
echo "   python list_timeseries_dates.py --bucket ps4-woodedarea --prefix 2024/"
echo ""
echo "4. Train model (after labeling scenes):"
echo "   python train_wooded_multi_scene_gcs.py --bucket ps4-woodedarea --prefix 2024/ --epochs 50 --output wooded_model.pt"
echo ""
echo "See GCP_VM_SETUP_GUIDE.md for detailed instructions."
