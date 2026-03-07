#!/bin/bash
# Setup script for ChatVLMLLM project

set -euo pipefail

echo "=================================="
echo "ChatVLMLLM Setup Script"
echo "=================================="
echo ""

# Check Python version
echo "[1/5] Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.10+ is required. Found: $python_version"
    exit 1
fi
echo "✅ Python $python_version"
echo ""

# Create virtual environment
echo "[2/5] Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists"
else
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi
echo ""

# Activate virtual environment
echo "[3/5] Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Upgrade pip
echo "[4/5] Upgrading pip..."
pip install --upgrade pip --quiet
echo "✅ Pip upgraded"
echo ""

# Install dependencies
echo "[5/5] Installing dependencies..."
echo "This may take 5-10 minutes..."
pip install -r requirements.txt --quiet
echo "✅ Dependencies installed"
echo ""

echo "=================================="
echo "Setup completed successfully! 🎉"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Run the application: streamlit run app.py"
echo "3. Open browser: http://localhost:8501"
echo ""
echo "For more information, see README.md"
echo ""