#!/usr/bin/env python3
"""
Quick installation test script.
Processes the ORDDSLMini.pdf sample file.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("=" * 60)
print("Pairing Parser - Installation Test")
print("=" * 60)
print()

# Test imports
print("Testing imports...")
try:
    import pdfplumber
    print("  ✓ pdfplumber")
except ImportError as e:
    print(f"  ✗ pdfplumber - {e}")
    print("\nPlease run: pip install -r requirements.txt")
    sys.exit(1)

try:
    from pydantic import BaseModel
    print("  ✓ pydantic")
except ImportError as e:
    print(f"  ✗ pydantic - {e}")
    sys.exit(1)

try:
    import click
    print("  ✓ click")
except ImportError:
    print("  ✗ click")
    sys.exit(1)

try:
    import yaml
    print("  ✓ pyyaml")
except ImportError:
    print("  ✗ pyyaml")
    sys.exit(1)

try:
    from tqdm import tqdm
    print("  ✓ tqdm")
except ImportError:
    print("  ✗ tqdm")
    sys.exit(1)

print()
print("Testing parser modules...")

try:
    from utils import get_logger, StreamingPDFReader
    print("  ✓ utils")
except ImportError as e:
    print(f"  ✗ utils - {e}")
    sys.exit(1)

try:
    from parsers import PairingParser
    print("  ✓ parsers")
except ImportError as e:
    print(f"  ✗ parsers - {e}")
    sys.exit(1)

try:
    from models import MasterData, Pairing, Leg
    print("  ✓ models")
except ImportError as e:
    print(f"  ✗ models - {e}")
    sys.exit(1)

print()
print("Testing sample PDF processing...")

# Test with ORDDSLMini.pdf
test_pdf = Path(__file__).parent / "ORDDSLMini.pdf"

if not test_pdf.exists():
    print(f"  ✗ Sample PDF not found: {test_pdf}")
    sys.exit(1)

print(f"  ✓ Found sample PDF: {test_pdf.name}")

try:
    from utils import PDFInfo
    info = PDFInfo.get_info(str(test_pdf))
    print(f"    Size: {info['size_mb']:.2f} MB")
    print(f"    Pages: {info.get('page_count', 'unknown')}")
except Exception as e:
    print(f"  ✗ Error reading PDF: {e}")
    sys.exit(1)

print()
print("=" * 60)
print("✓ Installation test successful!")
print("=" * 60)
print()
print("Next steps:")
print("  1. Run: python src/main.py -i ORDDSLMini.pdf -o output/test.json")
print("  2. Check output/test.json")
print("  3. Process full files with: ./process_all.sh")
print()
