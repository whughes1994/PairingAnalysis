#!/bin/bash
# Batch process all PDF files in Pairing Source Docs

echo "=========================================="
echo "Airline Pairing Parser - Batch Processing"
echo "=========================================="
echo ""

# Change to script directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check if dependencies are installed
if ! python -c "import pdfplumber" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Process all files
echo ""
echo "Processing all PDF files..."
echo ""

python src/main.py \
    --input-dir "Pairing Source Docs" \
    --output-dir "output" \
    --verbose

echo ""
echo "=========================================="
echo "Batch processing complete!"
echo "Check output/ directory for results"
echo "Check logs/ directory for detailed logs"
echo "=========================================="
