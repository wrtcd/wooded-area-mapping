# PowerShell script to set up virtual environment
# Requires Python 3.7 or higher

Write-Host "Creating virtual environment..." -ForegroundColor Green
python -m venv venv

Write-Host "Activating virtual environment..." -ForegroundColor Green
& .\venv\Scripts\Activate.ps1

Write-Host "Upgrading pip..." -ForegroundColor Green
python -m pip install --upgrade pip

Write-Host "Installing requirements..." -ForegroundColor Green
pip install -r requirements.txt

Write-Host "`nVirtual environment setup complete!" -ForegroundColor Green
Write-Host "To activate the venv in the future, run: .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
