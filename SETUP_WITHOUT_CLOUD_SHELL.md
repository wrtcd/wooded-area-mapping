# Setting Up GCP VM Without Cloud Shell

**Good news:** You don't need Cloud Shell! You can do everything from your local Windows machine.

## ⚠️ Cost lesson

Previous VM instances were left running and cost ~$20; they have been shut down and deleted. **Always stop or delete the VM when you finish work** (see "Stop VM" in this doc).

## Prerequisites

You need the **Google Cloud SDK (gcloud CLI)** installed on your local machine.

### Install gcloud CLI on Windows

1. **Download Google Cloud SDK:**
   - Go to: https://cloud.google.com/sdk/docs/install
   - Download the Windows installer
   - Run the installer and follow the prompts

2. **Initialize gcloud:**
   ```powershell
   gcloud init
   ```
   - Sign in with your Google account
   - Select your project: `wooded-488021`
   - Choose default region/zone (e.g., `us-central1-a`)

3. **Verify installation:**
   ```powershell
   gcloud --version
   gcloud config list
   ```

## Complete Setup Process (No Cloud Shell Needed)

### Step 1: Set project and create VM

Open **PowerShell** or **Command Prompt** and run:

```powershell
# Use the project where your bucket lives
gcloud config set project wooded-488021

# Create VM (200GB disk avoids I/O warning)
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

**Note:** Use backticks (`) for line continuation in PowerShell. If you get "project not found", make sure you set `wooded-488021` (or your actual project ID).

### Step 2: Upload Project Files

**Option A: Using the upload script (Easiest)**

```powershell
# Make sure you're in the project directory
cd "C:\Users\aeaturu\Desktop\WORK 2026 February\wooded area\wooded-area-mapping\wooded-area-mapping"

# Run upload script
.\upload_to_vm.ps1
```

**Option B: Manual upload using gcloud scp**

```powershell
# Create a zip/tar archive of your project (excluding venv)
# Note: Windows doesn't have tar by default, so you can:
# 1. Use 7-Zip or WinRAR to create a .tar.gz, OR
# 2. Upload files individually

# Upload key files one by one:
gcloud compute scp requirements.txt wooded-mapping-vm:~/wooded-area-mapping/ --zone=us-central1-a
gcloud compute scp setup_vm.sh wooded-mapping-vm:~/wooded-area-mapping/ --zone=us-central1-a
gcloud compute scp list_timeseries_dates.py wooded-mapping-vm:~/wooded-area-mapping/ --zone=us-central1-a
# ... etc for all .py files
```

**Option C: Use GCP Console to upload files**

1. Go to [GCP Console](https://console.cloud.google.com/compute/instances)
2. Click "SSH" next to your VM
3. Use the browser-based SSH terminal
4. Create files directly using `nano` or `vim`, or use the upload feature in the browser SSH

**Option D: Use Git (if your project is in a repo)**

```powershell
# On VM (via SSH):
git clone <your-repo-url> ~/wooded-area-mapping
```

### Step 3: SSH into VM

From your local PowerShell:

```powershell
gcloud compute ssh wooded-mapping-vm --zone=us-central1-a
```

This opens an SSH session directly in your terminal - **no Cloud Shell needed!**

### Step 4: Run Setup on VM

Once SSH'd into the VM:

```bash
# Navigate to project directory
cd ~/wooded-area-mapping

# Make setup script executable
chmod +x setup_vm.sh

# Run setup
./setup_vm.sh
```

## Alternative: Use GCP Console Web UI

You can also do many operations through the web interface:

### Create VM via Web UI

1. Go to: https://console.cloud.google.com/compute/instances
2. Click "Create Instance"
3. Configure:
   - **Name:** `wooded-mapping-vm`
   - **Region/Zone:** `us-central1-a`
   - **Machine type:** `n1-standard-4`
   - **GPU:** Add NVIDIA T4
   - **Boot disk:** Ubuntu 22.04 LTS, 50GB
   - **Access scopes:** Allow full access to Cloud APIs
4. Click "Create"

### SSH via Web UI

1. Go to VM instances page
2. Click "SSH" button next to your VM
3. Browser-based SSH terminal opens (no Cloud Shell needed!)

### Upload Files via Web UI SSH

1. SSH into VM via web UI
2. Click the gear icon (⚙️) in the SSH window
3. Select "Upload file"
4. Upload your project files

## Complete Workflow Summary

### From Your Local Windows Machine:

```powershell
# 1. Create VM
gcloud compute instances create wooded-mapping-vm --zone=us-central1-a --machine-type=n1-standard-4 --accelerator=type=nvidia-tesla-t4,count=1 --image-family=ubuntu-2204-lts --image-project=ubuntu-os-cloud --boot-disk-size=50GB --scopes=https://www.googleapis.com/auth/cloud-platform

# 2. Upload files (using script)
.\upload_to_vm.ps1

# 3. SSH into VM
gcloud compute ssh wooded-mapping-vm --zone=us-central1-a

# 4. On VM, run setup
cd ~/wooded-area-mapping
chmod +x setup_vm.sh
./setup_vm.sh
```

## What You CAN'T Do Without Cloud Shell

Actually, **nothing critical!** Cloud Shell is just a convenience tool. Everything can be done from:
- Your local machine (with gcloud CLI)
- GCP Console web UI
- Direct SSH into the VM

## Troubleshooting

### "gcloud command not found"

**Solution:** Install Google Cloud SDK from https://cloud.google.com/sdk/docs/install

### "Permission denied" when uploading files

**Solution:** Make sure you're authenticated:
```powershell
gcloud auth login
gcloud config set project wooded-488021
```

### Can't SSH into VM

**Solution:** Check firewall rules or use web-based SSH from GCP Console

### Files not uploading

**Solution:** Use web-based SSH and upload files manually, or use Git if your project is in a repository

## Quick Reference

**All commands run from your local Windows PowerShell:**

```powershell
# Create VM
gcloud compute instances create wooded-mapping-vm --zone=us-central1-a --machine-type=n1-standard-4 --accelerator=type=nvidia-tesla-t4,count=1 --image-family=ubuntu-2204-lts --image-project=ubuntu-os-cloud --boot-disk-size=50GB --scopes=https://www.googleapis.com/auth/cloud-platform

# Upload files
.\upload_to_vm.ps1

# SSH into VM
gcloud compute ssh wooded-mapping-vm --zone=us-central1-a

# Stop VM (save money!)
gcloud compute instances stop wooded-mapping-vm --zone=us-central1-a

# Start VM
gcloud compute instances start wooded-mapping-vm --zone=us-central1-a
```

## Summary

✅ **You DON'T need Cloud Shell**
✅ Use `gcloud` CLI from your local machine
✅ Or use GCP Console web UI
✅ Everything works the same way!

The only difference is you run commands from PowerShell instead of Cloud Shell. Everything else is identical.
