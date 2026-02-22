#!/bin/bash
# Bash script to upload project files to GCP VM
# Usage: ./upload_to_vm.sh

VM_NAME="${1:-wooded-mapping-vm}"
ZONE="${2:-us-central1-a}"
REMOTE_PATH="${3:-~/wooded-area-mapping}"

echo "=== Uploading Project Files to GCP VM ==="
echo "VM: $VM_NAME"
echo "Zone: $ZONE"
echo "Remote Path: $REMOTE_PATH"
echo ""

# Get project root directory
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
echo "Project root: $PROJECT_ROOT"
echo ""

# Create temporary archive (excluding venv, cache, etc.)
ARCHIVE_NAME="wooded-area-mapping-$(date +%Y%m%d-%H%M%S).tar.gz"
ARCHIVE_PATH="/tmp/$ARCHIVE_NAME"

echo "Creating archive (excluding venv, __pycache__, .git)..."
tar -czf "$ARCHIVE_PATH" \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='*.log' \
    -C "$PROJECT_ROOT" .

echo "Uploading archive to VM..."
gcloud compute scp "$ARCHIVE_PATH" "${VM_NAME}:${REMOTE_PATH}/" --zone="$ZONE"

echo ""
echo "=== Upload Complete ==="
echo ""
echo "Next steps:"
echo "1. SSH into VM: gcloud compute ssh $VM_NAME --zone=$ZONE"
echo "2. Extract archive: cd $REMOTE_PATH && tar -xzf $ARCHIVE_NAME"
echo "3. Run setup: chmod +x setup_vm.sh && ./setup_vm.sh"
echo ""
echo "Archive will be extracted automatically when you run setup_vm.sh"
