#!/bin/bash
# Run parser with virtual environment activated

cd "$(dirname "$0")"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✓ Virtual environment activated"
else
    echo "✗ Virtual environment not found. Run: python3 -m venv venv"
    exit 1
fi

# Run the parser
echo ""
echo "Processing ORDDSLMini.pdf..."
python src/main.py -i ORDDSLMini.pdf -o output/test.json -v

echo ""
echo "Results saved to: output/test.json"
