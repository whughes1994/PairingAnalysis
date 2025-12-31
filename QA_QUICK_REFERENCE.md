# QA Tools Quick Reference

## One-Liners

### Validate a parsed file
```bash
python3 validate_parsing.py "Pairing Source Docs/ORDDSL.pdf" output/ORD.json
```

### Quick totals check
```bash
python3 quick_compare.py "Pairing Source Docs/ORDDSL.pdf" output/ORD.json totals
```

### Check specific pairing
```bash
python3 quick_compare.py "Pairing Source Docs/ORDDSL.pdf" output/ORD.json pairing O8001
```

### Search for value
```bash
python3 quick_compare.py "Pairing Source Docs/ORDDSL.pdf" output/ORD.json search "ORD"
```

### Launch unified dashboard (Recommended)
```bash
# All-in-one: Pairing Explorer + QA Workbench
python3 -m streamlit run unified_dashboard.py

# Or use launcher menu
./launch.sh
```

### Launch standalone tools
```bash
# QA Workbench only
python3 -m streamlit run qa_workbench.py

# Annotations only
python3 -m streamlit run qa_annotations.py

# Original dashboard
python3 -m streamlit run dashboard_with_maps.py
```

## File Locations

| File | Purpose |
|------|---------|
| `validate_parsing.py` | Automated validation script |
| `qa_workbench.py` | Interactive comparison tool |
| `qa_annotations.py` | Issue tracking & annotation |
| `quick_compare.py` | Fast command-line comparison |
| `QA_GUIDE.md` | Complete QA documentation |
| `qa_annotations/` | Stored annotations (gitignored) |

## Common Checks

### ✅ Pre-Import Checklist
```bash
# 1. Parse
python3 main.py --input "Pairing Source Docs/ORDDSL.pdf" --output output/ORD.json

# 2. Validate
python3 validate_parsing.py "Pairing Source Docs/ORDDSL.pdf" output/ORD.json

# 3. Quick totals check
python3 quick_compare.py "Pairing Source Docs/ORDDSL.pdf" output/ORD.json totals

# 4. If all pass, import
python3 mongodb_import.py --connection "$MONGO_URI" --file output/ORD.json --clear
```

### 🔍 Investigating Issues
```bash
# Find pairing in both sources
python3 quick_compare.py PDF.pdf output.json search "O8001"

# Compare specific pairing
python3 quick_compare.py PDF.pdf output.json pairing O8001

# Deep dive with workbench
streamlit run qa_workbench.py
```

### 📝 Documenting Issues
```bash
# Launch annotations tool
streamlit run qa_annotations.py

# Add annotation manually
# Export report when done
```

## Severity Levels

| Level | When to Use | Example |
|-------|-------------|---------|
| 🔴 **Critical** | Data corruption, missing fleets | Entire fleet missing |
| 🟠 **High** | Wrong totals, missing flights | FTM mismatch |
| 🟡 **Medium** | Incorrect times, wrong equipment | Departure time off by hour |
| 🟢 **Low** | Formatting, minor inconsistencies | Station code lowercase |

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | All checks passed |
| `1` | Validation failed or issues found |

## URLs (when running)

| Tool | URL |
|------|-----|
| Main Dashboard | http://localhost:8501 |
| QA Workbench | http://localhost:8501 |
| QA Annotations | http://localhost:8501 |

Note: Only one Streamlit app can run at a time on port 8501

## Stopping Streamlit

### Quick Commands

```bash
# Method 1: Kill by port (recommended)
kill $(lsof -ti:8501)

# Method 2: Kill all streamlit processes
pkill -f streamlit

# Method 3: Interactive script
./stop_streamlit.sh

# Method 4: Force kill if needed
kill -9 $(lsof -ti:8501)
```

## Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| "No matches found" | Check PDF text extraction in Overview mode |
| "0 pairings" | Wrong JSON structure or file path |
| Port 8501 in use | Run: `kill $(lsof -ti:8501)` or `./stop_streamlit.sh` |
| Annotations not saving | Check `qa_annotations/` directory exists |
| `streamlit: command not found` | Use: `python3 -m streamlit run <file>` |

## Getting Help

1. Read [QA_GUIDE.md](QA_GUIDE.md) for detailed workflows
2. Check [README.md](README.md) for general setup
3. Report issues at https://github.com/whughes1994/PairingAnalysis/issues
