# Virtual Environment Setup

This project requires **Python 3.7 or higher**. Python 3.5.2 is not supported due to compatibility issues with required packages.

## Quick Setup

### Windows (PowerShell)
```powershell
.\setup_venv.ps1
```

### Linux/Mac (Bash)
```bash
chmod +x setup_venv.sh
./setup_venv.sh
```

### Manual Setup

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   # or
   python3 -m venv venv
   ```

2. **Activate virtual environment:**
   - **Windows (PowerShell):**
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - **Windows (CMD):**
     ```cmd
     venv\Scripts\activate.bat
     ```
   - **Linux/Mac:**
     ```bash
     source venv/bin/activate
     ```

3. **Upgrade pip:**
   ```bash
   pip install --upgrade pip
   ```

4. **Install requirements:**
   ```bash
   pip install -r requirements.txt
   ```

## Verify Installation

After setup, verify that packages are installed:
```bash
python -c "import torch; import rasterio; import numpy; print('All packages installed successfully!')"
```

## Troubleshooting

### Python Version Issues
If you see errors about Python version, check your Python version:
```bash
python --version
```

You need Python 3.7 or higher. If you have an older version:
- **Windows:** Download from [python.org](https://www.python.org/downloads/)
- **Linux:** Use `python3` instead of `python`, or install Python 3.7+
- **Mac:** Use Homebrew: `brew install python3`

### Path Issues
If activation fails, make sure you're in the project root directory and the `venv` folder exists.

### Permission Issues (Linux/Mac)
If you get permission errors, you may need to use `python3` instead of `python`:
```bash
python3 -m venv venv
source venv/bin/activate
```
