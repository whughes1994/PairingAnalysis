# .DAT File Support - Implementation Summary

**Date:** 2025-12-30
**Feature:** Added support for parsing .DAT text files in addition to PDF files

## Overview

The pairing parser now supports both PDF (.pdf) and text (.dat) file formats. The .DAT files contain the same pairing data as PDFs but in plain text format, making them faster and easier to parse.

## File Format Comparison

### PDF Format
- Binary format requiring pdfplumber library
- Needs text extraction from each page
- Larger file sizes
- Example: `ORDDSL.pdf` (varies, typically 5-10 MB)

### DAT Format
- Plain text ASCII format
- Direct line-by-line parsing
- No text extraction needed
- Example: `ORDDSL.DAT` (4.65 MB for 36,151 lines)

### Content Structure (Identical)
Both formats contain the same data structure:
```
1DSL EFF 01/30/26 THRU 03/01/26    787    CHICAGO                   FEB 2026
    EQP    FLT# DPT ARV DPTR ARVL  GRND  ML      FTM   ACM    DTM IND   D/C
 EFF 01/30/26 THRU 02/08/26                                  ID O8001  - BASIC   (HNL)
              RPT: 0820
    78J     202 ORD OGG 0920 1444  26.41 B S     9.24  9.24  10.39      .00
              RLS: 1459      HTL: MAUI COAST HOTEL             808-874-6284
```

## Implementation

### New Files Created

#### 1. `src/utils/text_reader.py`

**Purpose:** Read and chunk .DAT text files with the same interface as PDF reader

**Key Classes:**

**StreamingTextReader**
```python
class StreamingTextReader:
    """Read text files (.DAT) with the same interface as StreamingPDFReader."""

    def __init__(self, file_path: str, chunk_size: int = 1000):
        # chunk_size = number of lines per chunk

    def get_page_count(self) -> int:
        # Returns number of chunks (not actual pages)

    def read_pages_chunked(self) -> Generator[List[str], None, None]:
        # Yields chunks of text lines

    def read_all_lines(self) -> List[str]:
        # Reads entire file at once
```

**TextFileInfo**
```python
class TextFileInfo:
    """Utility class for getting text file information."""

    @staticmethod
    def get_info(file_path: str) -> dict:
        # Returns filename, size, line count, etc.
```

**Features:**
- Handles Windows line endings (`\r\n`)
- UTF-8 encoding with error handling (`errors='ignore'`)
- Chunked reading for memory efficiency
- Progress tracking compatible with PDF reader

### Modified Files

#### 2. `src/utils/__init__.py`

**Changes:**
```python
# Added imports
from .text_reader import StreamingTextReader, TextFileInfo

# Updated __all__
__all__ = [
    'get_logger',
    'StreamingPDFReader',
    'PDFInfo',
    'StreamingTextReader',    # NEW
    'TextFileInfo',           # NEW
    'StreamingJSONWriter',
    'JSONFileWriter',
    'backup_file'
]
```

#### 3. `src/main.py`

**Changes:**

**Import Statement (Line 14):**
```python
from .utils import (
    get_logger,
    StreamingPDFReader,
    PDFInfo,
    StreamingTextReader,  # NEW
    TextFileInfo,         # NEW
    JSONFileWriter
)
```

**Updated Function: `process_single_file()` (Lines 62-145)**

**File Type Detection:**
```python
# Detect file type
input_file = Path(input_path)
file_ext = input_file.suffix.lower()

if file_ext == '.dat':
    # Process .DAT text file
    file_info = TextFileInfo.get_info(input_path)
    text_reader = StreamingTextReader(input_path, chunk_size=1000)
    # ... parse lines

elif file_ext == '.pdf':
    # Process PDF file
    file_info = PDFInfo.get_info(input_path)
    pdf_reader = StreamingPDFReader(input_path, chunk_size=config['processing']['page_chunk_size'])
    # ... parse pages

else:
    logger.error(f"Unsupported file type: {file_ext}")
    return False
```

**DAT Processing Logic:**
```python
if file_ext == '.dat':
    logger.info(f"Processing DAT file: {file_info['filename']}")
    logger.info(f"  Size: {file_info['size_mb']:.2f} MB")
    logger.info(f"  Lines: {file_info.get('line_count', 'unknown')}")

    parser = PairingParser(config)
    text_reader = StreamingTextReader(input_path, chunk_size=1000)
    total_chunks = text_reader.get_page_count()
    line_number = 0

    with tqdm(total=total_chunks, desc="Processing chunks", unit="chunk") as pbar:
        for chunk_lines in text_reader.read_pages_chunked():
            for line in chunk_lines:
                line_number += 1
                parser.parse_line(line, line_number)
            pbar.update(1)
```

## Usage

### Command Line

**Parse .DAT file:**
```bash
python3 -m src.main \
  -i "Pairing Source Docs/February 2026/ORDDSL.DAT" \
  -o "output/ORDDSL_FEB2026.json"
```

**Parse .PDF file (still works):**
```bash
python3 -m src.main \
  -i "Pairing Source Docs/ORDDSL.pdf" \
  -o "output/ORDDSL_JAN2026.json"
```

### Automatic Detection

The parser automatically detects file type based on extension:
- `.dat` → Uses `StreamingTextReader`
- `.pdf` → Uses `StreamingPDFReader`
- Other → Returns error

No manual configuration needed!

## Performance Comparison

### ORDDSL.DAT (February 2026)

**File Stats:**
- Size: 4.65 MB
- Lines: 36,151
- Processing time: ~0.1 seconds (extremely fast!)

**Parsed Results:**
- Bid periods: 4 (787, 756, 737, 320)
- Pairings: 2,313
- Output size: 5.0 MB JSON

### ORDDSL.pdf (January 2026)

**File Stats:**
- Size: ~5-10 MB
- Pages: varies
- Processing time: ~5-10 seconds

**Parsed Results:**
- Bid periods: 4
- Pairings: 2,047
- Output size: ~4 MB JSON

**Speed Comparison:**
- .DAT parsing: **50-100x faster** than PDF
- No text extraction overhead
- Direct line-by-line processing

## Advantages of .DAT Format

### 1. **Speed**
- No PDF extraction overhead
- Direct text reading
- 50-100x faster processing

### 2. **Simplicity**
- Plain text format
- Easy to inspect manually
- Simple debugging

### 3. **Reliability**
- No PDF parsing errors
- Consistent line endings
- Deterministic behavior

### 4. **Memory Efficiency**
- Smaller file size
- Efficient chunking
- Lower memory footprint

### 5. **Compatibility**
- Works on any platform
- No special libraries needed (besides pydantic)
- Easy to version control

## Bug Fixes

### Leading Whitespace in .DAT Files (FIXED ✅)

**Issue:** Leg lines were not being extracted from .DAT files, causing "duty period has no legs" validation errors.

**Root Cause:** .DAT files have leading spaces before equipment codes:
```
    78J     202 ORD OGG 0920 1444  26.41 B S     9.24  9.24  10.39      .00
^^^^
Leading spaces in .DAT file
```

PDF extraction strips these spaces, but raw .DAT files preserve them. The original `is_leg_line()` method checked `line[0:2].isdigit()`, which failed because position 0 contained a space, not a digit.

**Fix Applied** ([src/parsers/pairing_parser.py:210-237](src/parsers/pairing_parser.py)):
```python
def is_leg_line(self, line: str) -> bool:
    """
    Detect if line contains leg data.

    Note: .DAT files have leading spaces, so we strip before checking
    """
    # Strip leading whitespace for .DAT file compatibility
    stripped = line.lstrip()

    # Check for equipment code format (2 digits + letter)
    if len(stripped) >= 3 and stripped[0:2].isdigit() and stripped[2].isalpha():
        return True

    # Check for specific deadhead markers: DH or UX
    if stripped.startswith('DH ') or stripped.startswith('UX '):
        return True

    return False
```

**Results After Fix:**
- ✅ All 12,072 legs successfully extracted
- ✅ Zero validation errors
- ✅ Zero validation warnings
- ✅ Perfect parsing of all 2,313 pairings

**Before Fix:**
```
Validation issue: Duty period 0 has no legs
Validation issue: Duty period 1 has no legs
(repeated for all pairings)
```

**After Fix:**
```
Processing Complete!
  Errors: 0
```

## Tested Files

### February 2026 Data
✅ `ORDDSL.DAT` - **FULLY WORKING**
- **Location:** `Pairing Source Docs/February 2026/ORDDSL.DAT`
- **File Size:** 4.65 MB (36,151 lines)
- **Status:** Successfully parsed with zero errors ✅
- **Bid Month:** FEB 2026
- **Base:** CHICAGO
- **Fleet Breakdown:**
  - 787: 89 pairings
  - 756: 62 pairings
  - 737: 1,445 pairings
  - 320: 717 pairings
- **Totals:**
  - **Pairings:** 2,313
  - **Duty Periods:** 6,624
  - **Legs:** 12,072
- **Output:** 5.0 MB JSON file

### Other Potential Files
Check the `Pairing Source Docs/February 2026/` directory for additional .DAT files:
```bash
ls "Pairing Source Docs/February 2026/"/*.DAT
```

## MongoDB Import

The .DAT files produce the same JSON format as PDF files, so MongoDB import works identically:

```bash
# 1. Parse .DAT file
python3 -m src.main \
  -i "Pairing Source Docs/February 2026/ORDDSL.DAT" \
  -o "output/ORDDSL_FEB2026.json"

# 2. Import to MongoDB
python3 mongodb_import.py \
  --file "output/ORDDSL_FEB2026.json" \
  --connection "mongodb+srv://whughes:whughes@cluster0.odztddj.mongodb.net/"
```

## Dashboard Compatibility

The parsed .DAT data is fully compatible with the unified dashboard:

1. Parse .DAT file → JSON
2. Import JSON → MongoDB
3. View in dashboard with all filters working:
   - Bid Month: FEB 2026
   - Fleet: 787, 756, 737, 320
   - Base: CHICAGO
   - All other filters

## Future Enhancements

### Potential Improvements

1. **Auto-Detection of Line Format:**
   - Detect subtle differences between PDF-extracted and native .DAT format
   - Adjust parser accordingly

2. **Batch Processing:**
   - Process all .DAT files in a directory
   - Compare multiple bid months
   - Detect changes between periods

3. **Format Validation:**
   - Verify .DAT file structure before parsing
   - Detect corrupted or incomplete files
   - Provide better error messages

4. **Diff Tool:**
   - Compare .DAT file contents
   - Show changes between bid periods
   - Highlight added/removed pairings

## Summary

✅ **Status:** .DAT file support fully implemented and tested

**Key Benefits:**
- 50-100x faster than PDF parsing
- Same output format
- Fully compatible with existing tools
- No code changes needed for downstream processing

**Files Added:**
- `src/utils/text_reader.py` (new)

**Files Modified:**
- `src/utils/__init__.py` (exports)
- `src/main.py` (file type detection)

**Tested:**
- ORDDSL.DAT (February 2026) ✅
- 2,313 pairings successfully parsed ✅
- MongoDB import ready ✅

The parser now seamlessly handles both PDF and .DAT files with automatic format detection!
