# VM Workflow Guide

Guide for deploying and running the wooded area mapping pipeline on Google Cloud Platform (GCP) Virtual Machines.

## ⚠️ Cost lesson – always stop or delete VMs

**Previous VM instances were left running by mistake and cost about $20. Those instances have been shut down and deleted.** When using GCP VMs:

- **Always stop** the VM when you finish: `gcloud compute instances stop wooded-mapping-vm --zone=us-central1-a`
- Or **delete** the VM when done to avoid ongoing disk cost and accidental charges
- Set billing alerts in [GCP Billing](https://console.cloud.google.com/billing)

## Prerequisites

- Google Cloud Platform account
- GCS bucket with PlanetScope scenes uploaded
- Basic familiarity with GCP and command-line tools

## VM Setup Options

### Option 1: Google Colab Free (Recommended for Start)

**Pros:**
- Free GPU (NVIDIA T4)
- No setup required
- Good for prototyping

**Cons:**
- 12-hour session limit
- Limited storage
- Less control

**Steps:**
1. Open Google Colab: https://colab.research.google.com/
2. Upload this repository or clone from GitHub
3. Install dependencies:
   ```python
   !pip install -r requirements.txt
   ```
4. Authenticate with GCS:
   ```python
   from google.colab import auth
   auth.authenticate_user()
   ```
5. Run training/inference scripts

### Option 2: GCP VM with GPU (Recommended for Production)

**VM Configuration:**
- **Machine type:** `n1-standard-4` (4 vCPU, 15GB RAM)
- **GPU:** NVIDIA T4 (1 GPU)
- **OS:** Ubuntu 20.04 LTS or 22.04 LTS
- **Boot disk:** 50GB SSD

**Estimated Cost:** ~$0.35/hour (~$250/month if running 24/7)

**Steps:**

#### 1. Create VM Instance

```bash
gcloud compute instances create wooded-mapping-vm \
    --zone=us-central1-a \
    --machine-type=n1-standard-4 \
    --accelerator=type=nvidia-tesla-t4,count=1 \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --maintenance-policy=TERMINATE \
    --boot-disk-size=50GB \
    --boot-disk-type=pd-ssd
```

#### 2. SSH into VM

```bash
gcloud compute ssh wooded-mapping-vm --zone=us-central1-a
```

#### 3. Run Setup Script

```bash
# Clone or upload repository
git clone <your-repo-url> wooded-area-mapping
cd wooded-area-mapping

# Run setup script
chmod +x setup_vm.sh
./setup_vm.sh
```

#### 4. Configure GCS Authentication

**Option A: Service Account Key (Recommended for automation)**

1. Create service account in GCP Console
2. Grant "Storage Object Viewer" and "Storage Object Creator" roles
3. Download JSON key file
4. Upload to VM:
   ```bash
   scp service-account-key.json user@vm-ip:~/
   ```
5. Set environment variable:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="$HOME/service-account-key.json"
   ```

**Option B: Application Default Credentials**

```bash
gcloud auth application-default login
```

#### 5. Test Setup

```bash
source venv/bin/activate
python -c "from google.cloud import storage; client = storage.Client(); print('GCS OK')"
```

## Running Training

### Local Training (if scenes downloaded)

```bash
python train_wooded_multi_scene.py \
    --scenes-dir ./data \
    --epochs 50 \
    --batch-size 16 \
    --output wooded_model.pt
```

### GCS Training (Recommended)

```bash
python train_wooded_multi_scene_gcs.py \
    --bucket ps4-woodedarea \
    --prefix 2024/ \
    --scene-ids 20240110_162648_67_247d 20240415_162648_67_247d \
    --epochs 50 \
    --batch-size 16 \
    --output wooded_model.pt
```

**Auto-detect scenes with reference rasters:**
```bash
python train_wooded_multi_scene_gcs.py \
    --bucket ps4-woodedarea \
    --prefix 2024/ \
    --epochs 50 \
    --output wooded_model.pt
```

## Running Batch Inference

```bash
python predict_wooded_batch_gcs.py \
    --bucket ps4-woodedarea \
    --prefix 2024/ \
    --model wooded_model.pt \
    --output-prefix predictions/ \
    --compute-metrics
```

## Cost Optimization

### Use Preemptible VMs

Preemptible VMs cost ~70% less but can be terminated:

```bash
gcloud compute instances create wooded-mapping-vm-preemptible \
    --preemptible \
    --zone=us-central1-a \
    --machine-type=n1-standard-4 \
    --accelerator=type=nvidia-tesla-t4,count=1 \
    ...
```

**Note:** Save checkpoints frequently when using preemptible VMs.

### Stop VM When Not in Use

```bash
# Stop VM (preserves disk, no charges for compute)
gcloud compute instances stop wooded-mapping-vm --zone=us-central1-a

# Start VM when needed
gcloud compute instances start wooded-mapping-vm --zone=us-central1-a
```

### Use Spot VMs (Alternative to Preemptible)

Similar to preemptible but with different pricing model.

## Monitoring

### Check GPU Usage

```bash
nvidia-smi
```

### Monitor Training Progress

Use TensorBoard or simple logging:
```bash
tail -f training.log
```

## Troubleshooting

### GPU Not Detected

```bash
# Check NVIDIA drivers
nvidia-smi

# If not installed, install drivers
sudo apt-get install -y nvidia-driver-470
sudo reboot
```

### Out of Memory Errors

- Reduce `--batch-size` (e.g., from 16 to 8)
- Reduce `--patch-size` (e.g., from 64 to 32)
- Use gradient accumulation

### GCS Authentication Errors

```bash
# Re-authenticate
gcloud auth application-default login

# Or set service account key
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
```

## Next Steps

1. Start with Colab Free for initial testing
2. Move to GCP VM with GPU for full training
3. Use preemptible VMs for cost savings
4. Scale up to multiple VMs for parallel processing if needed
