#!/bin/bash
# One-command installation script

echo "=============================================="
echo "Installing Pairing Parser Dependencies"
echo "=============================================="
echo ""

# Change to script directory
cd "$(dirname "$0")"

# Install dependencies
echo "Installing Python packages..."
pip3 install --user -r requirements.txt

echo ""
echo "=============================================="
echo "✓ Installation complete!"
echo "=============================================="
echo ""
echo "Now run:"
echo "  python3 test_installation.py"
echo ""
echo "Then process PDFs:"
echo "  python3 src/main.py -i ORDDSLMini.pdf -o output/test.json -v"
echo ""
