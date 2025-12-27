# Quick Installation Fix

## You're almost there! Just need to install dependencies.

### Run these commands:

```bash
cd "/Users/williamhughes/Library/CloudStorage/GoogleDrive-william.hughes1994@gmail.com/My Drive/Pairing Parser"

# Install dependencies
pip3 install -r requirements.txt

# Or if you want a virtual environment (recommended):
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Then test again:

```bash
python3 test_installation.py
```

### Quick Process Test:

```bash
python3 src/main.py -i ORDDSLMini.pdf -o output/test.json -v
```

---

## If you get "command not found: python"

That's normal - use `python3` instead:

```bash
# Instead of: python
# Use: python3

python3 test_installation.py
python3 src/main.py -i ORDDSLMini.pdf -o output/test.json
```

---

## Expected Success Output:

```
============================================================
Pairing Parser - Installation Test
============================================================

Testing imports...
  ✓ pdfplumber
  ✓ pydantic
  ✓ click
  ✓ pyyaml
  ✓ tqdm

Testing parser modules...
  ✓ utils
  ✓ parsers
  ✓ models

Testing sample PDF processing...
  ✓ Found sample PDF: ORDDSLMini.pdf
    Size: 0.12 MB
    Pages: 10

============================================================
✓ Installation test successful!
============================================================
```

---

## Next Steps After Installation:

1. **Process test file:**
   ```bash
   python3 src/main.py -i ORDDSLMini.pdf -o output/test.json -v
   ```

2. **Process all PDFs:**
   ```bash
   ./process_all.sh
   # Or: python3 src/main.py --input-dir "Pairing Source Docs" --output-dir output
   ```

3. **Check results:**
   ```bash
   ls -lh output/
   cat output/test.json | python3 -m json.tool | less
   ```

---

Everything is set up correctly - you just need to install the Python packages!
