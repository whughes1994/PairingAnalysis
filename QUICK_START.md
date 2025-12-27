# Quick Start Guide

## Installation

1. **Create a virtual environment (recommended)**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Basic Usage

### Process a Single File

```bash
cd "Pairing Parser"
python src/main.py \
    --input "ORDDSLMini.pdf" \
    --output "output/ORDDSLMini.json"
```

### Process All Files in Directory

```bash
python src/main.py \
    --input-dir "Pairing Source Docs" \
    --output-dir "output"
```

Or use the batch script:
```bash
./process_all.sh
```

### With Verbose Logging

```bash
python src/main.py \
    --input "ORDDSLMini.pdf" \
    --output "output/ORDDSLMini.json" \
    --verbose
```

## Configuration

Edit `config/parser_config.yaml` to customize:

- **Page chunk size**: Reduce if running out of memory
- **Validation settings**: Enable strict mode for data validation
- **Logging level**: DEBUG, INFO, WARNING, ERROR
- **Output format**: Indentation and backup settings

## Output

Processed files are saved to the `output/` directory as JSON.

Each JSON file contains:
- Bid period information (month, fleet, base)
- All pairings with their:
  - ID and category
  - Duty periods
  - Flight legs
  - Hotels and ground transportation
  - Summary metrics (days, credit, flight time, etc.)

## Logs

Detailed logs are saved to `logs/pairing_parser.log`

## Troubleshooting

### Out of Memory
Reduce `page_chunk_size` in `config/parser_config.yaml`:
```yaml
processing:
  page_chunk_size: 5  # Default is 10
```

### Missing Data
1. Check logs for parsing errors
2. Enable verbose mode: `--verbose`
3. Check validation warnings in logs

### Slow Processing
- Large PDFs (>1MB) may take 30-60 seconds
- Processing is single-threaded (multi-threading planned)

## Examples

### Test with Small File
```bash
python src/main.py -i ORDDSLMini.pdf -o output/test.json -v
```

### Process Specific Bases
```bash
# Only ORD and LAX
python src/main.py -i "Pairing Source Docs/ORDDSL.pdf" -o "output/ORD.json"
python src/main.py -i "Pairing Source Docs/LAXDSL.pdf" -o "output/LAX.json"
```

### Run Tests
```bash
python -m pytest tests/ -v
```

## Project Structure

```
├── src/
│   ├── main.py              # CLI entry point
│   ├── models/              # Data schemas
│   ├── parsers/             # Parsing logic
│   └── utils/               # Helper utilities
├── config/                  # Configuration
├── output/                  # Processed JSON files
├── logs/                    # Log files
└── tests/                   # Unit tests
```

## Next Steps

1. Process ORDDSLMini.pdf to verify installation
2. Review output JSON structure
3. Process larger files from "Pairing Source Docs"
4. Integrate JSON data into your application
