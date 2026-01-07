#!/usr/bin/env python3
"""
Batch Process Pairing Files

This script processes all .DAT and .PDF files in a specified folder,
parses them into JSON, and imports them into MongoDB.

Output files are named with parent folder prefix by default:
    "February 2026/ORDDSL.DAT" -> "February_2026_ORDDSL.json"

Usage:
    python3 batch_process.py --folder "Pairing Source Docs/February 2026"
    python3 batch_process.py --folder "Pairing Source Docs/February 2026" --no-import
    python3 batch_process.py --folder "Pairing Source Docs" --recursive
    python3 batch_process.py --folder "Pairing Source Docs/February 2026" --no-parent-folder
"""

import argparse
import sys
from pathlib import Path
import subprocess
import json
from datetime import datetime


def find_pairing_files(folder: Path, recursive: bool = False) -> list:
    """Find all .DAT and .PDF files in the specified folder."""
    files = []

    if recursive:
        # Search recursively
        dat_files = list(folder.rglob('*.DAT')) + list(folder.rglob('*.dat'))
        pdf_files = list(folder.rglob('*.pdf')) + list(folder.rglob('*.PDF'))
    else:
        # Search only in the specified folder
        dat_files = list(folder.glob('*.DAT')) + list(folder.glob('*.dat'))
        pdf_files = list(folder.glob('*.pdf')) + list(folder.glob('*.PDF'))

    files = dat_files + pdf_files

    # Sort by name for consistent processing order
    files.sort(key=lambda x: x.name)

    return files


def parse_file(input_file: Path, output_dir: Path, include_parent_folder: bool = True) -> tuple:
    """
    Parse a pairing file to JSON.

    Returns:
        tuple: (success: bool, output_file: Path, error_message: str)
    """
    # Generate output filename with parent folder name
    if include_parent_folder and input_file.parent.name:
        # Include parent folder name in output filename
        # e.g., "February 2026/ORDDSL.DAT" -> "February_2026_ORDDSL.json"
        parent_name = input_file.parent.name.replace(' ', '_')
        output_filename = f"{parent_name}_{input_file.stem}.json"
    else:
        output_filename = input_file.stem + '.json'

    output_path = output_dir / output_filename

    # Build parser command
    cmd = [
        'python3', '-m', 'src.main',
        '-i', str(input_file),
        '-o', str(output_path)
    ]

    try:
        print(f"\n{'='*80}")
        print(f"Parsing: {input_file.name}")
        print(f"Output:  {output_path.name}")
        print(f"{'='*80}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode == 0:
            print(f"✓ Successfully parsed {input_file.name}")
            return (True, output_path, None)
        else:
            error_msg = result.stderr or result.stdout
            print(f"✗ Failed to parse {input_file.name}")
            print(f"Error: {error_msg}")
            return (False, None, error_msg)

    except subprocess.TimeoutExpired:
        error_msg = "Parsing timeout (5 minutes exceeded)"
        print(f"✗ {error_msg}")
        return (False, None, error_msg)
    except Exception as e:
        error_msg = str(e)
        print(f"✗ Unexpected error: {error_msg}")
        return (False, None, error_msg)


def import_to_mongodb(json_file: Path) -> tuple:
    """
    Import a JSON file to MongoDB.

    Returns:
        tuple: (success: bool, error_message: str)
    """
    cmd = [
        'python3', 'mongodb_import.py',
        '--file', str(json_file)
    ]

    try:
        print(f"\n{'='*80}")
        print(f"Importing to MongoDB: {json_file.name}")
        print(f"{'='*80}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode == 0:
            print(f"✓ Successfully imported {json_file.name}")
            return (True, None)
        else:
            error_msg = result.stderr or result.stdout
            print(f"✗ Failed to import {json_file.name}")
            print(f"Error: {error_msg}")
            return (False, error_msg)

    except subprocess.TimeoutExpired:
        error_msg = "Import timeout (5 minutes exceeded)"
        print(f"✗ {error_msg}")
        return (False, error_msg)
    except Exception as e:
        error_msg = str(e)
        print(f"✗ Unexpected error: {error_msg}")
        return (False, error_msg)


def main():
    parser = argparse.ArgumentParser(
        description='Batch process pairing files and import to MongoDB',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all files in February 2026 folder
  python3 batch_process.py --folder "Pairing Source Docs/February 2026"

  # Process files but don't import to MongoDB
  python3 batch_process.py --folder "Pairing Source Docs/February 2026" --no-import

  # Process all files in all subdirectories
  python3 batch_process.py --folder "Pairing Source Docs" --recursive

  # Custom output directory
  python3 batch_process.py --folder "Pairing Source Docs/February 2026" --output "output/feb2026"
        """
    )

    parser.add_argument(
        '--folder',
        type=str,
        required=True,
        help='Folder containing pairing files (.DAT or .PDF)'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='output',
        help='Output directory for JSON files (default: output/)'
    )

    parser.add_argument(
        '--recursive',
        action='store_true',
        help='Search for files recursively in subdirectories'
    )

    parser.add_argument(
        '--no-import',
        action='store_true',
        help='Parse files but do not import to MongoDB'
    )

    parser.add_argument(
        '--no-parent-folder',
        action='store_true',
        help='Do not include parent folder name in output filenames'
    )

    args = parser.parse_args()

    # Validate input folder
    input_folder = Path(args.folder)
    if not input_folder.exists():
        print(f"Error: Folder not found: {args.folder}")
        sys.exit(1)

    if not input_folder.is_dir():
        print(f"Error: Not a directory: {args.folder}")
        sys.exit(1)

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all pairing files
    print(f"\nSearching for pairing files in: {input_folder}")
    if args.recursive:
        print("(Recursive search enabled)")

    files = find_pairing_files(input_folder, args.recursive)

    if not files:
        print("\n⚠️  No pairing files found (.DAT or .PDF)")
        sys.exit(0)

    print(f"\nFound {len(files)} file(s) to process:")
    for f in files:
        print(f"  - {f.relative_to(input_folder.parent)}")

    # Process each file
    results = {
        'total': len(files),
        'parsed': 0,
        'parse_failed': 0,
        'imported': 0,
        'import_failed': 0,
        'errors': []
    }

    start_time = datetime.now()

    for input_file in files:
        # Parse file (include parent folder name unless --no-parent-folder is set)
        include_parent = not args.no_parent_folder
        success, output_file, error = parse_file(input_file, output_dir, include_parent)

        if success:
            results['parsed'] += 1

            # Import to MongoDB (unless --no-import)
            if not args.no_import:
                import_success, import_error = import_to_mongodb(output_file)

                if import_success:
                    results['imported'] += 1
                else:
                    results['import_failed'] += 1
                    results['errors'].append({
                        'file': input_file.name,
                        'stage': 'import',
                        'error': import_error
                    })
        else:
            results['parse_failed'] += 1
            results['errors'].append({
                'file': input_file.name,
                'stage': 'parse',
                'error': error
            })

    # Print summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print(f"\n{'='*80}")
    print("BATCH PROCESSING COMPLETE")
    print(f"{'='*80}")
    print(f"Total files:           {results['total']}")
    print(f"Successfully parsed:   {results['parsed']}")
    print(f"Parse failures:        {results['parse_failed']}")

    if not args.no_import:
        print(f"Successfully imported: {results['imported']}")
        print(f"Import failures:       {results['import_failed']}")
    else:
        print(f"Import:                Skipped (--no-import)")

    print(f"\nDuration: {duration:.1f} seconds")
    print(f"Output directory: {output_dir.absolute()}")

    # Print errors if any
    if results['errors']:
        print(f"\n{'='*80}")
        print("ERRORS")
        print(f"{'='*80}")
        for idx, err in enumerate(results['errors'], 1):
            print(f"\n{idx}. {err['file']} ({err['stage']} stage)")
            print(f"   {err['error']}")

    # Exit with appropriate code
    if results['parse_failed'] > 0 or results['import_failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
