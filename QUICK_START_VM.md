# Quick Start: GCP VM Setup

## ⚠️ Cost lesson

Previous VMs were left running and cost ~$20; they have been shut down and deleted. **Always stop the VM when not in use** (see Cost Management below).

## 🚀 Fast Track Setup (5 Steps)

### 1. Set project and create VM
```powershell
# Use the project where your bucket lives (wooded-488021)
gcloud config set project wooded-488021

# Create VM (200GB disk avoids I/O warning; use 50GB if you prefer)
gcloud compute instances create wooded-mapping-vm `
    --project=wooded-488021 `
    --zone=us-central1-a `
    --machine-type=n1-standard-4 `
    --accelerator=type=nvidia-tesla-t4,count=1 `
    --image-family=ubuntu-2204-lts `
    --image-project=ubuntu-os-cloud `
    --boot-disk-size=200GB `
    --scopes=https://www.googleapis.com/auth/cloud-platform
```

### 2. Upload Project Files

**Option A: Using upload script (Linux/Mac)**
```bash
chmod +x upload_to_vm.sh
./upload_to_vm.sh
```

**Option B: Using upload script (Windows PowerShell)**
```powershell
.\upload_to_vm.ps1
```

**Option C: Manual upload**
```bash
# From your local machine, create archive:
tar -czf project.tar.gz --exclude='venv' --exclude='__pycache__' .

# Upload:
gcloud compute scp project.tar.gz wooded-mapping-vm:~/ --zone=us-central1-a
```

### 3. SSH into VM
```bash
gcloud compute ssh wooded-mapping-vm --zone=us-central1-a
```

### 4. Extract Files (if uploaded as archive)
```bash
cd ~
tar -xzf project.tar.gz -C wooded-area-mapping/  # or wherever you uploaded
cd wooded-area-mapping
```

### 5. Run Setup
```bash
chmod +x setup_vm.sh
./setup_vm.sh
```

## ✅ Verify Setup

```bash
# Activate venv
source venv/bin/activate

# Test GCS access
python list_timeseries_dates.py --bucket ps4-woodedarea --prefix 2024/
```

## 💰 Cost Management

**Stop VM when not in use:**
```bash
gcloud compute instances stop wooded-mapping-vm --zone=us-central1-a
```

**Start VM when needed:**
```bash
gcloud compute instances start wooded-mapping-vm --zone=us-central1-a
```

**Cost:** ~$0.35/hour (~$8.40/day if running 24/7)
- **Always stop (or delete) the VM when done – leaving it running cost ~$20 previously.**
- Disk storage: ~$0.17/month for 50GB

## 📋 Common Commands

**SSH into VM:**
```bash
gcloud compute ssh wooded-mapping-vm --zone=us-central1-a
```

**Activate virtual environment:**
```bash
source venv/bin/activate
```

**List timeseries dates:**
```bash
python list_timeseries_dates.py --bucket ps4-woodedarea --prefix 2024/
```

**Train model:**
```bash
python train_wooded_multi_scene_gcs.py \
    --bucket ps4-woodedarea \
    --prefix 2024/ \
    --epochs 50 \
    --output wooded_model.pt
```

**Run inference:**
```bash
python predict_wooded_batch_gcs.py \
    --bucket ps4-woodedarea \
    --prefix 2024/ \
    --model wooded_model.pt \
    --output-prefix predictions/
```

## 🆘 Troubleshooting

**GCS authentication error:**
```bash
gcloud auth application-default login
```

**GPU not detected:**
```bash
nvidia-smi  # Check GPU status
```

**Reinstall dependencies:**
```bash
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 📚 Full Documentation

- **Detailed setup:** See `GCP_VM_SETUP_GUIDE.md`
- **VM workflow:** See `vm_workflow.md`
- **Getting started:** See `GETTING_STARTED.md`
