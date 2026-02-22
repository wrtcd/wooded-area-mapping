# Syncing Workspace Across Computers

This guide explains how to access your workspace on multiple computers.

## Option 1: Git + GitHub (Recommended for Code)

**Best for**: Code, scripts, documentation, configuration files  
**Not ideal for**: Large data files (TIFFs, model checkpoints)

**Important**: Git syncs **code files only**. The following are **NOT synced**:
- ❌ Cursor agent conversation history (stored locally per machine)
- ❌ Cursor settings/preferences (stored locally)
- ❌ Python virtual environments (`.venv/` - recreate on each machine)
- ❌ Large data files (use GCS instead)

### Setup (One-time)

1. **Initialize Git repository** (if not already done):
   ```bash
   cd "c:\Users\aeaturu\Desktop\WORK 2026 February\wooded area mapping"
   git init
   git add .
   git commit -m "Initial commit"
   ```

2. **Create GitHub repository**:
   - Go to https://github.com/new
   - Create a new repository (e.g., `wooded-area-mapping`)
   - **Don't** initialize with README (you already have files)

3. **Connect and push**:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/wooded-area-mapping.git
   git branch -M main
   git push -u origin main
   ```

### On Your Desktop Computer

1. **Clone the repository**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/wooded-area-mapping.git
   cd wooded-area-mapping
   ```

2. **Set up Python environment**:
   ```bash
   python -m venv .venv
   .venv\Scripts\Activate.ps1  # Windows PowerShell
   pip install -r requirements.txt
   ```

3. **Sync changes**:
   ```bash
   # Pull latest changes
   git pull
   
   # Push your changes
   git add .
   git commit -m "Description of changes"
   git push
   ```

**Note**: Large files (`.tif`, `.pt`) are already in `.gitignore` and won't be synced via Git. Use GCS for data files.

---

## Option 2: Cloud Storage (Google Drive / OneDrive / Dropbox)

**Best for**: Everything including data files, if you have enough storage  
**Limitations**: May be slow for large files, version conflicts possible

### Setup

1. **Install cloud storage client** on both computers:
   - Google Drive: https://www.google.com/drive/download/
   - OneDrive: Usually pre-installed on Windows
   - Dropbox: https://www.dropbox.com/download

2. **Move workspace to cloud folder**:
   - Copy entire workspace folder to your cloud storage folder
   - Example: `C:\Users\aeaturu\OneDrive\wooded area mapping`

3. **Access on desktop**:
   - Cloud folder syncs automatically
   - Open workspace from cloud folder location

**Note**: Large TIFF files may take time to sync. Consider excluding `data/` folder if files are already in GCS.

---

## Option 3: GCS for Data + Git for Code (Hybrid - Recommended)

**Best approach**: Use Git for code/docs, GCS for data files

### Setup

1. **Code**: Use Git + GitHub (see Option 1)
2. **Data**: Keep data files in GCS bucket (already set up)
3. **Local data**: Don't commit `data/` folder to Git (already in `.gitignore`)

### Workflow

**On any computer**:
1. Clone Git repository → Get all code/scripts
2. Download data from GCS as needed:
   ```bash
   gsutil -m cp gs://ps4-woodedarea/2024/*.tif ./data/
   ```
3. Run scripts → Results stay local or upload to GCS

**Benefits**:
- Code synced via Git (fast, version controlled)
- Data in GCS (accessible from anywhere, no local storage needed)
- No need to sync large files

---

## Option 4: Remote Access (SSH / Remote Desktop)

**Best for**: Accessing one computer from another

### Windows Remote Desktop

1. **Enable Remote Desktop** on your laptop:
   - Settings → System → Remote Desktop → Enable
   - Note your computer name

2. **Connect from desktop**:
   - Open Remote Desktop Connection
   - Enter laptop computer name
   - Sign in with your Windows credentials

**Note**: Both computers must be on the same network (or use VPN).

---

## Recommended Setup

**For your workflow**:

1. **Initialize Git repository** (one-time):
   ```bash
   cd "c:\Users\aeaturu\Desktop\WORK 2026 February\wooded area mapping"
   git init
   git add .
   git commit -m "Initial commit"
   ```

2. **Create GitHub repository** and push:
   ```bash
   # After creating repo on GitHub
   git remote add origin https://github.com/YOUR_USERNAME/wooded-area-mapping.git
   git push -u origin main
   ```

3. **On desktop computer**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/wooded-area-mapping.git
   cd wooded-area-mapping
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

4. **Keep data in GCS** (already set up):
   - Download scenes as needed: `gsutil cp gs://ps4-woodedarea/2024/*.tif ./data/`
   - Upload results: `gsutil cp ./results/*.tif gs://ps4-woodedarea/results/`

---

## Quick Start: Initialize Git Now

Run these commands to set up Git:

```bash
cd "c:\Users\aeaturu\Desktop\WORK 2026 February\wooded area mapping"
git init
git add .
git commit -m "Initial commit"
```

Then create a GitHub repository and push:
```bash
git remote add origin https://github.com/YOUR_USERNAME/wooded-area-mapping.git
git branch -M main
git push -u origin main
```

---

## Troubleshooting

### Git authentication issues
- Use GitHub Personal Access Token instead of password
- Or use SSH keys: https://docs.github.com/en/authentication/connecting-to-github-with-ssh

### Large files in Git
- Check `.gitignore` includes `*.tif`, `*.pt`, `data/`
- If accidentally committed: `git rm --cached large_file.tif`

### Cloud sync conflicts
- Use Git for code to avoid conflicts
- Keep data in GCS, not in cloud storage folder

### Python environment differences
- Always use `requirements.txt` to ensure same packages
- Virtual environments are local to each computer (not synced)

### Cursor Agent Conversations
- **Agent conversations are NOT synced** - they're stored locally on each machine
- Each computer has its own conversation history
- If you need to reference past conversations, they're stored in:
  - Windows: `C:\Users\YOUR_USERNAME\.cursor\projects\...\agent-transcripts\`
  - These are local files, not synced through Git
- **Solution**: Important decisions/conversations should be documented in:
  - `README.md` - Project documentation
  - `GETTING_STARTED.md` - Workflow guides
  - Code comments - Implementation details
