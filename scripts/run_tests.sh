#!/bin/bash
# Run tests with coverage

set -euo pipefail

echo "=================================="
echo "Running ChatVLMLLM Tests"
echo "=================================="
echo ""

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install test dependencies
echo "Installing test dependencies..."
pip install pytest pytest-cov --quiet
echo ""

# Run tests
echo "Running tests..."
pytest tests/ -v --cov=models --cov=utils --cov-report=term --cov-report=html

echo ""
echo "=================================="
echo "Tests completed!"
echo "=================================="
echo ""
echo "Coverage report saved to: htmlcov/index.html"
echo "Open it in your browser to see detailed coverage"
echo ""