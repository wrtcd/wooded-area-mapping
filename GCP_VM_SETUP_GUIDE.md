# GCP VM Setup Guide - Step by Step

Complete guide to set up your GCP VM for the wooded area mapping project.

## ⚠️ Cost lesson – always stop or delete VMs

**Previous VM instances were left running by mistake and cost about $20. Those instances have been shut down and deleted.** Before you create any new VMs:

- **Always stop** the VM when you finish work: `gcloud compute instances stop wooded-mapping-vm --zone=us-central1-a`
- Or **delete** the VM when the project phase is done to avoid disk and accidental start costs
- Set billing alerts in GCP so you get notified if spend grows

## Prerequisites

- Google Cloud Platform account with billing enabled
- `gcloud` CLI installed on your local machine (**Cloud Shell is NOT required**)
- Your GCS bucket: `ps4-woodedarea`

**Note:** Cloud Shell is optional. You can do everything from your local machine using `gcloud` CLI or the GCP Console web UI. See `SETUP_WITHOUT_CLOUD_SHELL.md` for details.

## Before you proceed – verify project and bucket

Confirm you are using the **intended GCP project and bucket** (new account/bucket). Run:

```powershell
# Active GCP project (should match where your bucket lives)
gcloud config get-value project

# List buckets in that project (should include your data bucket)
gcloud storage buckets list
# Or: gsutil ls
```

**Current project, bucket, and account used in this guide:**

| What        | Value                    |
|------------|---------------------------|
| GCP project| `wooded-488021`           |
| GCS bucket | `ps4-woodedarea`          |
| Account    | `mindisemptea@gmail.com`  |

Verify account: `gcloud config get-value account`  
If your project, bucket, or account differ, use your values everywhere this guide says the above.

## Step 1: Set the Correct GCP Project

Your bucket `ps4-woodedarea` is in project **wooded-488021**. gcloud must use this project:

```powershell
# Set active project (use the project where your bucket lives)
gcloud config set project wooded-488021

# Verify
gcloud config get-value project
```

If you see a different project, the VM would be created in the wrong project. Always set `wooded-488021` before creating the VM.

## Step 2: Create VM Instance

### Option A: Using gcloud CLI (from your local machine)

```powershell
gcloud compute instances create wooded-mapping-vm `
    --project=wooded-488021 `
    --zone=us-central1-a `
    --machine-type=n1-standard-4 `
    --accelerator=type=nvidia-tesla-t4,count=1 `
    --image-family=ubuntu-2204-lts `
    --image-project=ubuntu-os-cloud `
    --maintenance-policy=TERMINATE `
    --boot-disk-size=200GB `
    --boot-disk-type=pd-ssd `
    --scopes=https://www.googleapis.com/auth/cloud-platform
```

**Notes:**
- `--project=wooded-488021` ensures the VM is in the same project as your bucket.
- `--boot-disk-size=200GB` avoids the "poor I/O performance" warning (50GB is fine too if you prefer lower disk cost).
- `--scopes` gives the VM access to GCS automatically.
- Cost: ~$0.35/hour (~$8.40/day if running 24/7).
- **Important:** Stop the VM when not in use to save costs!

### Option B: Using GCP Console (Web UI)

1. Go to [GCP Console](https://console.cloud.google.com/compute/instances)
2. Click "Create Instance"
3. Configure:
   - **Name:** `wooded-mapping-vm`
   - **Region/Zone:** `us-central1-a`
   - **Machine type:** `n1-standard-4` (4 vCPU, 15GB RAM)
   - **GPU:** Add NVIDIA T4 (1 GPU)
   - **Boot disk:** Ubuntu 22.04 LTS, 50GB SSD
   - **Firewall:** Allow HTTP/HTTPS traffic (optional)
   - **Access scopes:** Allow full access to Cloud APIs
4. Click "Create"

## Step 3: SSH into VM

### Option A: Using gcloud CLI

```bash
gcloud compute ssh wooded-mapping-vm --zone=us-central1-a
```

### Option B: Using GCP Console

1. Go to VM instances page
2. Click "SSH" button next to your VM
3. Browser-based SSH terminal will open

## Step 4: Upload Project Files to VM

You have several options:

### Option A: Using gcloud CLI (from your local machine)

```bash
# Create a tarball of your project (excluding venv and large files)
cd "C:\Users\aeaturu\Desktop\WORK 2026 February\wooded area\wooded-area-mapping\wooded-area-mapping"
tar -czf project.tar.gz --exclude='venv' --exclude='*.pyc' --exclude='__pycache__' --exclude='.git' .

# Upload to VM
gcloud compute scp project.tar.gz wooded-mapping-vm:~/ --zone=us-central1-a

# SSH into VM and extract
gcloud compute ssh wooded-mapping-vm --zone=us-central1-a
# Then on VM:
tar -xzf project.tar.gz
```

### Option B: Using Git (if your project is in a repo)

```bash
# On VM:
git clone <your-repo-url> wooded-area-mapping
cd wooded-area-mapping
```

### Option C: Using GCP Console Web UI SSH

1. SSH into VM via GCP Console (click "SSH" button)
2. Use the file upload feature in the browser SSH window
3. Or create files directly using `nano`/`vim` and copy-paste content

### Option D: Direct Copy-Paste (for small files)

You can create files directly on the VM using `nano` or `vim`.

## Step 5: Run Setup Script

Once you're SSH'd into the VM and have the project files:

```bash
# Navigate to project directory
cd ~/wooded-area-mapping  # or wherever you put the files

# Make setup script executable
chmod +x setup_vm.sh

# Run setup script
./setup_vm.sh
```

**What the setup script does:**
- Updates system packages
- Installs Python 3, pip, venv
- Creates virtual environment
- Installs all Python dependencies from `requirements.txt`
- Tests GCS access

## Step 6: Configure GCS Authentication

The VM should already have access via the `--scopes` flag, but verify:

```bash
# Activate virtual environment
source venv/bin/activate

# Test GCS access
python -c "from google.cloud import storage; client = storage.Client(); buckets = list(client.list_buckets()); print('GCS access OK! Found', len(buckets), 'buckets')"
```

If you see an error, authenticate:

```bash
gcloud auth application-default login
```

## Step 7: Verify Setup

```bash
# Activate venv
source venv/bin/activate

# Check Python version (should be 3.8+)
python --version

# Check installed packages
pip list | grep -E "torch|rasterio|numpy|google-cloud"

# Test GPU (if using GPU VM)
nvidia-smi

# Test listing scenes from your bucket
python list_timeseries_dates.py --bucket ps4-woodedarea --prefix 2024/
```

## Step 8: Start Using the VM

### List Timeseries Dates

```bash
source venv/bin/activate
python list_timeseries_dates.py --bucket ps4-woodedarea --prefix 2024/
```

### Train Model

```bash
source venv/bin/activate
python train_wooded_multi_scene_gcs.py \
    --bucket ps4-woodedarea \
    --prefix 2024/ \
    --epochs 50 \
    --batch-size 16 \
    --output wooded_model.pt
```

### Run Inference

```bash
source venv/bin/activate
python predict_wooded_batch_gcs.py \
    --bucket ps4-woodedarea \
    --prefix 2024/ \
    --model wooded_model.pt \
    --output-prefix predictions/ \
    --compute-metrics
```

## Cost Management

### Stop VM When Not in Use

```bash
# From your local machine:
gcloud compute instances stop wooded-mapping-vm --zone=us-central1-a

# Start when needed:
gcloud compute instances start wooded-mapping-vm --zone=us-central1-a
```

**Note:** You only pay for compute time when the VM is running. Disk storage costs ~$0.17/month for 50GB. **Previous VMs were left running and cost ~$20 – always stop or delete when done.**

### Monitor Costs

- Go to [GCP Billing](https://console.cloud.google.com/billing)
- Set up billing alerts
- Check VM usage in Compute Engine dashboard

## Troubleshooting

### GPU Not Detected

```bash
# Check GPU
nvidia-smi

# If not found, install drivers (usually pre-installed on GPU images)
sudo apt-get update
sudo apt-get install -y nvidia-driver-470
sudo reboot
```

### Out of Memory During Training

Reduce batch size:
```bash
python train_wooded_multi_scene_gcs.py ... --batch-size 8  # instead of 16
```

### GCS Authentication Errors

```bash
# Re-authenticate
gcloud auth application-default login

# Or check service account
gcloud config list
```

### Python/Pip Issues

```bash
# Recreate venv
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Quick Reference

**SSH into VM:**
```bash
gcloud compute ssh wooded-mapping-vm --zone=us-central1-a
```

**Stop VM:**
```bash
gcloud compute instances stop wooded-mapping-vm --zone=us-central1-a
```

**Start VM:**
```bash
gcloud compute instances start wooded-mapping-vm --zone=us-central1-a
```

**Delete VM (when done):**
```bash
gcloud compute instances delete wooded-mapping-vm --zone=us-central1-a
```

## Next Steps

1. ✅ Create VM
2. ✅ Upload project files
3. ✅ Run setup script
4. ✅ Test GCS access
5. 🔄 List timeseries dates
6. 🔄 Label 3-10 scenes
7. 🔄 Train model
8. 🔄 Run inference
