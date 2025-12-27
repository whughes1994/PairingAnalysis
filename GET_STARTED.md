# Getting Started with the Pairing Parser

## 🎯 Quick Overview

This tool converts large airline pairing PDF files into structured JSON data. It's designed to handle files of any size efficiently and robustly.

**You have 11 PDF files ready to process** in the `Pairing Source Docs/` folder:
- ORDDSL.pdf (1.1MB) - Chicago
- DENDSL.pdf (1.0MB) - Denver
- IAHDSL.pdf (978KB) - Houston
- EWRDSL.pdf (873KB) - Newark
- DCADSL.pdf (560KB) - Washington
- SFODSL.pdf (544KB) - San Francisco
- MCODSL.pdf (333KB) - Orlando
- LAXDSL.pdf (329KB) - Los Angeles
- CLEDSL.pdf (254KB) - Cleveland
- LASDSL.pdf (157KB) - Las Vegas
- GUMDSL.pdf (70KB) - Guam

Plus **ORDDSLMini.pdf** (116KB) for testing.

---

## 📋 Prerequisites

- Python 3.8 or higher
- About 5 minutes for setup

---

## 🚀 Installation (5 Steps)

### Step 1: Open Terminal
Navigate to the project directory:
```bash
cd "/Users/williamhughes/Library/CloudStorage/GoogleDrive-william.hughes1994@gmail.com/My Drive/Pairing Parser"
```

### Step 2: Create Virtual Environment (Recommended)
```bash
python3 -m venv venv
source venv/bin/activate
```
You should see `(venv)` in your terminal prompt.

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

This installs:
- pdfplumber - PDF reading
- pydantic - Data validation
- click - CLI framework
- tqdm - Progress bars
- pyyaml - Configuration
- colorlog - Colored logging

### Step 4: Verify Installation
```bash
python test_installation.py
```

You should see:
```
==========================================
Pairing Parser - Installation Test
==========================================

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

==========================================
✓ Installation test successful!
==========================================
```

### Step 5: Test with Sample File
```bash
python src/main.py -i ORDDSLMini.pdf -o output/test.json -v
```

Expected output:
```
2025-12-25 20:00:00 - PairingParser - INFO - Processing: ORDDSLMini.pdf
  Size: 0.12 MB
  Pages: 10
Processing pages: 100%|████████████| 10/10 [00:03<00:00]
2025-12-25 20:00:03 - PairingParser - INFO - Parsing complete: 39 pairings, 0 errors
============================================================
Processing Complete!
  Total lines processed: 542
  Pairings parsed: 39
  Errors: 0
  Processing time: 3.24s
  Output file: output/test.json
============================================================
```

✅ **Installation complete!** You're ready to process files.

---

## 💡 Usage Examples

### Example 1: Process a Single File
```bash
python src/main.py \
    --input "Pairing Source Docs/ORDDSL.pdf" \
    --output "output/ORD.json"
```

### Example 2: Process All Files at Once
```bash
./process_all.sh
```

Or manually:
```bash
python src/main.py \
    --input-dir "Pairing Source Docs" \
    --output-dir "output"
```

### Example 3: Process with Verbose Logging
```bash
python src/main.py \
    -i "Pairing Source Docs/DENDSL.pdf" \
    -o "output/DEN.json" \
    --verbose
```

### Example 4: Process Specific Bases
```bash
# Just the big ones
python src/main.py -i "Pairing Source Docs/ORDDSL.pdf" -o "output/ORD.json"
python src/main.py -i "Pairing Source Docs/DENDSL.pdf" -o "output/DEN.json"
python src/main.py -i "Pairing Source Docs/IAHDSL.pdf" -o "output/IAH.json"
```

---

## 📊 Understanding the Output

### Output Location
All JSON files are saved to: `output/`

### Output Structure
Each JSON file contains:

```json
{
  "data": [
    {
      "bid_month_year": "JAN 2026",
      "fleet": "787",
      "base": "CHICAGO",
      "effective_date": "12/30/25",
      "through_date": "01/29/26",
      "pairings": [
        {
          "id": "O8001",
          "pairing_category": "BASIC (HNL)",
          "is_first_officer": false,
          "effective_date": "12/30/25",
          "through_date": "01/04/26",
          "date_instances": ["30", "31", "1", "2", "3", "4"],
          "duty_periods": [
            {
              "report_time": "0820",
              "legs": [
                {
                  "equipment": "78J",
                  "deadhead": false,
                  "flight_number": "202",
                  "departure_station": "ORD",
                  "arrival_station": "OGG",
                  "departure_time": "0920",
                  "arrival_time": "1444",
                  "ground_time": "26:31",
                  "meal_code": "B",
                  "flight_time": "9:24",
                  "accumulated_flight_time": "9:24",
                  "duty_time": "10:39",
                  "d_c": "0"
                }
              ],
              "release_time": "1459",
              "hotel": "MAUI COAST HOTEL 808-874-6284 OP=> 808-871-0445"
            }
          ],
          "days": "3",
          "credit": "17.23",
          "flight_time": "17.23",
          "time_away_from_base": "45.09",
          "international_flight_time": "0",
          "nte": "6.14",
          "meal_money": "159.83",
          "t_c": "0"
        }
      ],
      "ftm": "13,578:02",
      "ttl": "14,387:35"
    }
  ],
  "metadata": {
    "source_file": "ORDDSL.pdf",
    "page_count": 150,
    "processing_time_seconds": 42.5,
    "total_pairings": 245
  }
}
```

---

## 🔍 Checking Results

### View Output JSON
```bash
# Pretty print
python -m json.tool output/test.json | less

# Or open in your preferred editor
code output/test.json  # VS Code
open output/test.json  # macOS default
```

### Check Logs
```bash
# View latest log
tail -f logs/pairing_parser.log

# View all logs
cat logs/pairing_parser.log

# Search for errors
grep ERROR logs/pairing_parser.log
```

### Verify Statistics
Each JSON file includes metadata:
```python
import json

with open('output/ORD.json') as f:
    data = json.load(f)

print(f"File: {data['metadata']['source_file']}")
print(f"Pairings: {data['metadata']['total_pairings']}")
print(f"Processing time: {data['metadata']['processing_time_seconds']}s")
```

---

## ⚙️ Configuration

### Adjust Processing Speed vs Memory

Edit `config/parser_config.yaml`:

```yaml
processing:
  page_chunk_size: 10  # Reduce to 5 if low on memory
```

**Recommendation:**
- 16GB+ RAM: Use 10 (default)
- 8GB RAM: Use 5
- 4GB RAM: Use 3

### Change Logging Level

```yaml
logging:
  level: "INFO"  # Options: DEBUG, INFO, WARNING, ERROR
```

---

## 🐛 Troubleshooting

### Problem: "Module not found"
**Solution:**
```bash
pip install -r requirements.txt --force-reinstall
```

### Problem: "Out of memory"
**Solution:** Reduce chunk size in config
```yaml
processing:
  page_chunk_size: 5
```

### Problem: "No pairings found"
**Solution:**
1. Check logs: `cat logs/pairing_parser.log`
2. Enable verbose: `--verbose`
3. Verify PDF is correct format

### Problem: "Permission denied"
**Solution:**
```bash
chmod +x process_all.sh
chmod +x test_installation.py
```

---

## 📈 Performance Guide

### Expected Processing Times

| File Size | Pages | Time | Pairings (est.) |
|-----------|-------|------|-----------------|
| 100KB | ~15 | ~5s | ~30 |
| 500KB | ~70 | ~20s | ~150 |
| 1MB | ~140 | ~45s | ~300 |

### Tips for Faster Processing

1. **Process in parallel** (multiple terminals):
   ```bash
   # Terminal 1
   python src/main.py -i "Pairing Source Docs/ORDDSL.pdf" -o output/ORD.json &

   # Terminal 2
   python src/main.py -i "Pairing Source Docs/DENDSL.pdf" -o output/DEN.json &
   ```

2. **Use SSD storage** for input/output

3. **Close other applications** to free memory

---

## 🎓 Next Steps

### Beginner Path
1. ✅ Install and verify
2. ✅ Process ORDDSLMini.pdf
3. ⬜ Process one large file (ORDDSL.pdf)
4. ⬜ Review JSON output
5. ⬜ Process all files with `./process_all.sh`

### Advanced Path
1. ⬜ Customize `config/parser_config.yaml`
2. ⬜ Write Python script to analyze JSON
3. ⬜ Add custom validators
4. ⬜ Integrate with database
5. ⬜ Create analytics dashboard

---

## 📚 Documentation Reference

- **QUICK_START.md** - Command reference
- **README.md** - Complete documentation
- **PROJECT_OVERVIEW.md** - Technical details
- **IMPLEMENTATION_SUMMARY.md** - Architecture overview

---

## 🎉 Ready to Go!

You're all set! Here's what to do now:

### Process All Files (Recommended)
```bash
./process_all.sh
```

This will:
1. Process all 11 PDF files
2. Save JSON to `output/`
3. Log everything to `logs/`
4. Show progress bars
5. Report statistics

**Estimated total time:** ~5 minutes

### Or Process One at a Time
```bash
# Start with smallest file
python src/main.py -i "Pairing Source Docs/GUMDSL.pdf" -o output/GUM.json

# Then try a large one
python src/main.py -i "Pairing Source Docs/ORDDSL.pdf" -o output/ORD.json
```

---

## 💬 Need Help?

1. Check logs: `logs/pairing_parser.log`
2. Run with verbose: `--verbose`
3. Review documentation in this folder
4. Test installation: `python test_installation.py`

---

## ✨ Success Indicators

You'll know it's working when you see:

✅ Progress bars showing page processing
✅ Green "INFO" messages in console
✅ JSON files appearing in `output/`
✅ "Processing Complete!" message
✅ No ERROR messages in logs

**Happy parsing!** 🚀
