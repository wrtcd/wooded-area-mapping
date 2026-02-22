#!/bin/bash
# Bash script to set up virtual environment
# Requires Python 3.7 or higher

echo "Creating virtual environment..."
python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing requirements..."
pip install -r requirements.txt

echo ""
echo "Virtual environment setup complete!"
echo "To activate the venv in the future, run: source venv/bin/activate"
