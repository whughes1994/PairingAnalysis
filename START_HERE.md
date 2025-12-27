# 🎯 START HERE - Pairing Parser

## Welcome! 👋

This is a complete, production-ready system for parsing airline pairing PDF files into structured JSON data.

---

## ⚡ Quick Start (3 Commands)

```bash
# 1. Install dependencies
make install

# 2. Test installation
make test

# 3. Process all PDFs
make process-all
```

**That's it!** Your JSON files will be in the `output/` folder.

---

## 📚 Documentation Guide

Choose your path based on what you need:

### 🎯 **I want to start using it NOW**
→ Read: **[GET_STARTED.md](GET_STARTED.md)**
- Step-by-step installation
- First test run
- Common commands
- Quick troubleshooting

### 📖 **I need a command reference**
→ Read: **[QUICK_START.md](QUICK_START.md)**
- All CLI commands
- Configuration options
- Usage examples
- Common tasks

### 🔍 **I want to understand how it works**
→ Read: **[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)**
- Architecture details
- Parsing algorithm
- Data structures
- Performance characteristics

### 🏗️ **I'm a developer wanting to extend it**
→ Read: **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)**
- Code structure
- Module descriptions
- Extension points
- Development workflow

### ✅ **I want to see what was delivered**
→ Read: **[PROJECT_COMPLETE.md](PROJECT_COMPLETE.md)**
- Complete feature list
- All deliverables
- Performance specs
- Success metrics

### 📋 **I want the full documentation**
→ Read: **[README.md](README.md)**
- Complete reference
- Installation guide
- All features
- API documentation

---

## 🎬 Your First Session

### 1. Open Terminal
```bash
cd "/Users/williamhughes/Library/CloudStorage/GoogleDrive-william.hughes1994@gmail.com/My Drive/Pairing Parser"
```

### 2. Create Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install
```bash
pip install -r requirements.txt
```

### 4. Verify
```bash
python test_installation.py
```

### 5. Test
```bash
python src/main.py -i ORDDSLMini.pdf -o output/test.json -v
```

### 6. Process All
```bash
./process_all.sh
```

---

## 📊 What You're Processing

### 11 PDF Files Ready
Located in `Pairing Source Docs/`:

| File | Size | Estimated Pairings |
|------|------|--------------------|
| ORDDSL.pdf | 1.1MB | ~245 |
| DENDSL.pdf | 1.0MB | ~230 |
| IAHDSL.pdf | 978KB | ~220 |
| EWRDSL.pdf | 873KB | ~195 |
| DCADSL.pdf | 560KB | ~125 |
| SFODSL.pdf | 544KB | ~120 |
| MCODSL.pdf | 333KB | ~75 |
| LAXDSL.pdf | 329KB | ~73 |
| CLEDSL.pdf | 254KB | ~55 |
| LASDSL.pdf | 157KB | ~35 |
| GUMDSL.pdf | 70KB | ~15 |

**Total:** ~1,380 pairings

---

## 🎮 Useful Commands

### Using Makefile (Easiest)
```bash
make help            # Show all commands
make install         # Install dependencies
make test            # Verify installation
make process-test    # Test with sample file
make process-all     # Process everything
make clean           # Clean output/logs
make show-files      # List PDFs
make show-output     # List JSON files
```

### Using Python Directly
```bash
# Single file
python src/main.py -i "Pairing Source Docs/ORDDSL.pdf" -o output/ORD.json

# With verbose logging
python src/main.py -i input.pdf -o output.json --verbose

# Batch processing
python src/main.py --input-dir "Pairing Source Docs" --output-dir output
```

### Using Bash Script
```bash
./process_all.sh
```

---

## 🎯 Expected Results

### After Processing
```
output/
├── ORD.json  (~500KB)
├── DEN.json  (~480KB)
├── IAH.json  (~450KB)
├── EWR.json  (~410KB)
├── DCA.json  (~265KB)
├── SFO.json  (~255KB)
├── MCO.json  (~155KB)
├── LAX.json  (~150KB)
├── CLE.json  (~120KB)
├── LAS.json  (~75KB)
└── GUM.json  (~35KB)

logs/
└── pairing_parser.log
```

### JSON Structure
Each file contains:
- Bid period info (month, fleet, base)
- All pairings with:
  - ID and category
  - Duty periods
  - Flight legs
  - Hotels
  - Summary metrics

---

## 🔍 Checking Your Work

### View a JSON File
```bash
# Pretty print
python -m json.tool output/ORD.json | less

# Count pairings
cat output/ORD.json | jq '.metadata.total_pairings'
```

### Check Logs
```bash
# Latest entries
tail -20 logs/pairing_parser.log

# Search for errors
grep ERROR logs/pairing_parser.log
```

### Verify Stats
```bash
# Show all output files
ls -lh output/

# Count total size
du -sh output/
```

---

## ⚙️ Configuration

### Main Config File
[config/parser_config.yaml](config/parser_config.yaml)

### Key Settings
```yaml
processing:
  page_chunk_size: 10      # Reduce if low on memory

logging:
  level: "INFO"            # DEBUG for more detail

validation:
  enabled: true
  strict_mode: false       # Set true to fail on errors
```

---

## 🐛 Troubleshooting

### Problem: Installation fails
```bash
# Solution
pip install -r requirements.txt --force-reinstall
```

### Problem: Out of memory
```bash
# Solution: Edit config/parser_config.yaml
# Change: page_chunk_size: 10 → page_chunk_size: 5
```

### Problem: No output files
```bash
# Check logs
cat logs/pairing_parser.log

# Run with verbose
python src/main.py -i input.pdf -o output.json --verbose
```

### Problem: Parse errors
```bash
# Verify installation
python test_installation.py

# Check PDF is correct format
file "Pairing Source Docs/ORDDSL.pdf"
```

---

## 📞 Getting Help

### 1. Check Documentation
- **Quick fix:** [QUICK_START.md](QUICK_START.md)
- **Setup issue:** [GET_STARTED.md](GET_STARTED.md)
- **Technical question:** [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)

### 2. Check Logs
```bash
tail -50 logs/pairing_parser.log
```

### 3. Run Diagnostics
```bash
python test_installation.py
make test
```

### 4. Enable Verbose Logging
```bash
python src/main.py -i input.pdf -o output.json --verbose
```

---

## 🎓 Learning Path

### Beginner
1. ✅ Read this file (you're here!)
2. ⬜ Follow [GET_STARTED.md](GET_STARTED.md)
3. ⬜ Process test file
4. ⬜ Check output JSON
5. ⬜ Process all files

### Intermediate
1. ⬜ Read [QUICK_START.md](QUICK_START.md)
2. ⬜ Customize config
3. ⬜ Write analysis script
4. ⬜ Review logs

### Advanced
1. ⬜ Read [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)
2. ⬜ Review source code
3. ⬜ Run unit tests
4. ⬜ Extend functionality

---

## 🎁 What's Included

### Code (2,500+ lines)
- ✅ Streaming PDF reader
- ✅ State-machine parser
- ✅ Pydantic data models
- ✅ Data validation
- ✅ Error handling
- ✅ Logging system
- ✅ CLI interface
- ✅ Batch processing

### Documentation (5,000+ words)
- ✅ README.md
- ✅ GET_STARTED.md
- ✅ QUICK_START.md
- ✅ PROJECT_OVERVIEW.md
- ✅ IMPLEMENTATION_SUMMARY.md
- ✅ PROJECT_COMPLETE.md
- ✅ This file (START_HERE.md)

### Tools
- ✅ Makefile
- ✅ Batch script
- ✅ Test suite
- ✅ Installation checker
- ✅ Configuration system

---

## 🚀 Ready to Go?

### Option 1: Quick Start (Recommended)
```bash
make install && make test && make process-all
```

### Option 2: Step by Step
```bash
# Install
make install

# Test
make test

# Process sample
make process-test

# Process all
make process-all
```

### Option 3: Manual
```bash
# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run
python src/main.py --input-dir "Pairing Source Docs" --output-dir output
```

---

## ✨ Success Looks Like

You'll know everything is working when you see:

✅ Installation test passes
✅ Progress bars appear during processing
✅ Green "INFO" messages in console
✅ JSON files in `output/` directory
✅ "Processing Complete!" message
✅ No ERROR messages in logs
✅ File statistics displayed

---

## 🎉 Next Steps

After successful processing:

1. **Explore the output**
   ```bash
   python -m json.tool output/ORD.json | less
   ```

2. **Verify data**
   ```bash
   # Count pairings
   cat output/*.json | grep -c '"id"'
   ```

3. **Use the data**
   - Import into your application
   - Build analytics
   - Create reports
   - Analyze patterns

---

## 📝 Quick Reference Card

```bash
# ESSENTIAL COMMANDS

# Setup (one time)
make install
make test

# Process files
make process-test        # Test with sample
make process-all         # All PDFs
make process-ord         # Just Chicago

# Check results
make show-output         # List output files
cat logs/pairing_parser.log  # View logs

# Clean up
make clean              # Remove output/logs

# Get help
make help               # Show all commands
```

---

## 🌟 You're All Set!

Everything you need is ready to go. Pick your next step:

→ **Just want to process files?** Run `make process-all`

→ **Want to learn first?** Read [GET_STARTED.md](GET_STARTED.md)

→ **Need help?** Check logs or run `make test`

→ **Ready to integrate?** Review output JSON structure

**Happy parsing!** ✈️📊

---

*For detailed documentation, see [README.md](README.md)*
