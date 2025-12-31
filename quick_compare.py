#!/usr/bin/env python3
"""
Quick Compare Tool

Fast command-line tool to compare specific values between PDF and parsed JSON.
Useful for quick spot-checks without launching the full workbench.
"""

import sys
import json
import pdfplumber
import re
from pathlib import Path
from typing import Tuple, List

def load_data(pdf_path: str, json_path: str) -> Tuple[str, dict]:
    """Load PDF text and parsed JSON."""
    # Load PDF
    with pdfplumber.open(pdf_path) as pdf:
        pdf_text = '\n'.join([page.extract_text() or '' for page in pdf.pages])

    # Load JSON
    with open(json_path, 'r') as f:
        raw_data = json.load(f)

    # Normalize structure
    if 'data' in raw_data:
        parsed_data = {
            'bid_periods': raw_data['data'],
            'base': raw_data['data'][0].get('base') if raw_data['data'] else None,
            'month': raw_data['data'][0].get('bid_month_year') if raw_data['data'] else None
        }
    else:
        parsed_data = raw_data

    return pdf_text, parsed_data

def compare_totals(pdf_text: str, parsed_data: dict):
    """Compare FTM/TTL totals."""
    print("\n" + "=" * 80)
    print("FTM/TTL TOTALS COMPARISON")
    print("=" * 80 + "\n")

    # Extract from PDF
    totals_pattern = re.compile(
        r'([A-Z]{3})\s+([0-9]{2,3}[A-Z]?)\s+FTM-\s*([\d:,]+)\s+TTL-\s*([\d:,]+)'
    )
    pdf_totals = totals_pattern.findall(pdf_text)

    bid_periods = parsed_data.get('bid_periods', [])

    for base, fleet, ftm, ttl in pdf_totals:
        # Find matching bid period
        matching_bp = next((bp for bp in bid_periods if bp.get('fleet') == fleet), None)

        if matching_bp:
            parsed_ftm = matching_bp.get('ftm', 'N/A')
            parsed_ttl = matching_bp.get('ttl', 'N/A')

            ftm_match = (parsed_ftm == ftm)
            ttl_match = (parsed_ttl == ttl)

            status = "✅ MATCH" if (ftm_match and ttl_match) else "❌ MISMATCH"

            print(f"Fleet {fleet}:")
            print(f"  PDF: FTM={ftm}, TTL={ttl}")
            print(f"  Parsed: FTM={parsed_ftm}, TTL={parsed_ttl}")
            print(f"  {status}\n")
        else:
            print(f"Fleet {fleet}:")
            print(f"  PDF: FTM={ftm}, TTL={ttl}")
            print(f"  ❌ NOT FOUND in parsed data\n")

def compare_pairing(pairing_id: str, pdf_text: str, parsed_data: dict):
    """Compare a specific pairing."""
    print("\n" + "=" * 80)
    print(f"PAIRING {pairing_id} COMPARISON")
    print("=" * 80 + "\n")

    # Find in PDF
    lines = pdf_text.split('\n')
    pdf_matches = []

    for i, line in enumerate(lines):
        if pairing_id in line:
            start = max(0, i - 2)
            end = min(len(lines), i + 5)
            pdf_matches.append('\n'.join(lines[start:end]))

    # Find in parsed data
    bid_periods = parsed_data.get('bid_periods', [])
    parsed_pairing = None

    for bp in bid_periods:
        for pairing in bp.get('pairings', []):
            if pairing.get('id') == pairing_id:
                parsed_pairing = pairing
                break
        if parsed_pairing:
            break

    # Display
    print("PDF SOURCE:")
    print("-" * 80)
    if pdf_matches:
        print(pdf_matches[0])
    else:
        print(f"Pairing {pairing_id} not found in PDF")

    print("\n" + "=" * 80)
    print("PARSED DATA:")
    print("-" * 80)

    if parsed_pairing:
        print(f"ID: {parsed_pairing.get('id')}")
        print(f"Days: {parsed_pairing.get('days')}")
        print(f"Category: {parsed_pairing.get('pairing_category')}")
        print(f"Credit: {parsed_pairing.get('credit_minutes', 0) / 60:.1f}h")
        print(f"Flight Time: {parsed_pairing.get('flight_time_minutes', 0) / 60:.1f}h")

        duty_periods = parsed_pairing.get('duty_periods', [])
        print(f"\nDuty Periods: {len(duty_periods)}")

        for dp_idx, dp in enumerate(duty_periods):
            legs = dp.get('legs', [])
            print(f"\n  Day {dp_idx + 1}: {len(legs)} legs")
            print(f"    Report: {dp.get('report_time_formatted', dp.get('report_time'))}")
            print(f"    Release: {dp.get('release_time_formatted', dp.get('release_time'))}")
            print(f"    Layover: {dp.get('layover_station', 'None')}")

            for leg_idx, leg in enumerate(legs):
                dh = "DH " if leg.get('deadhead') else ""
                print(f"    Leg {leg_idx + 1}: {dh}{leg.get('departure_station')} → {leg.get('arrival_station')}, "
                      f"FL{leg.get('flight_number')}, {leg.get('departure_time_formatted')}-{leg.get('arrival_time_formatted')}")
    else:
        print(f"Pairing {pairing_id} not found in parsed data")

def search_value(search_term: str, pdf_text: str, parsed_data: dict):
    """Search for a value in both sources."""
    print("\n" + "=" * 80)
    print(f"SEARCH: '{search_term}'")
    print("=" * 80 + "\n")

    # Search PDF
    lines = pdf_text.split('\n')
    pdf_matches = []

    for i, line in enumerate(lines):
        if search_term.upper() in line.upper():
            pdf_matches.append((i + 1, line.strip()))

    print(f"PDF MATCHES: {len(pdf_matches)}")
    print("-" * 80)
    for line_num, line in pdf_matches[:10]:  # First 10
        print(f"Line {line_num}: {line}")

    # Search parsed data
    parsed_str = json.dumps(parsed_data, indent=2)
    parsed_lines = parsed_str.split('\n')
    parsed_matches = []

    for i, line in enumerate(parsed_lines):
        if search_term.upper() in line.upper():
            parsed_matches.append((i + 1, line.strip()))

    print(f"\nPARSED DATA MATCHES: {len(parsed_matches)}")
    print("-" * 80)
    for line_num, line in parsed_matches[:10]:  # First 10
        print(f"Line {line_num}: {line}")

def show_summary(pdf_text: str, parsed_data: dict):
    """Show quick summary."""
    print("\n" + "=" * 80)
    print("QUICK SUMMARY")
    print("=" * 80 + "\n")

    bid_periods = parsed_data.get('bid_periods', [])

    print(f"Base: {parsed_data.get('base', 'N/A')}")
    print(f"Month: {parsed_data.get('month', 'N/A')}")
    print(f"Bid Periods: {len(bid_periods)}\n")

    total_pairings = 0

    for bp in bid_periods:
        fleet = bp.get('fleet')
        pairings = bp.get('pairings', [])
        pairing_count = len(pairings)
        total_pairings += pairing_count

        print(f"Fleet {fleet}: {pairing_count} pairings, FTM={bp.get('ftm')}, TTL={bp.get('ttl')}")

    print(f"\nTotal Pairings: {total_pairings}")

def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print("Usage: python3 quick_compare.py <pdf_file> <json_file> [command] [args]")
        print("\nCommands:")
        print("  summary              - Show quick summary (default)")
        print("  totals               - Compare FTM/TTL totals")
        print("  pairing <ID>         - Compare specific pairing")
        print("  search <term>        - Search for value in both sources")
        print("\nExamples:")
        print("  python3 quick_compare.py ORDDSL.pdf output/ORD.json")
        print("  python3 quick_compare.py ORDDSL.pdf output/ORD.json totals")
        print("  python3 quick_compare.py ORDDSL.pdf output/ORD.json pairing O8001")
        print("  python3 quick_compare.py ORDDSL.pdf output/ORD.json search 'ORD'")
        sys.exit(1)

    pdf_path = sys.argv[1]
    json_path = sys.argv[2]

    # Check files exist
    if not Path(pdf_path).exists():
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)

    if not Path(json_path).exists():
        print(f"Error: JSON file not found: {json_path}")
        sys.exit(1)

    # Load data
    print("Loading data...")
    pdf_text, parsed_data = load_data(pdf_path, json_path)

    # Parse command
    command = sys.argv[3] if len(sys.argv) > 3 else 'summary'

    if command == 'summary':
        show_summary(pdf_text, parsed_data)

    elif command == 'totals':
        compare_totals(pdf_text, parsed_data)

    elif command == 'pairing':
        if len(sys.argv) < 5:
            print("Error: Pairing ID required")
            print("Usage: python3 quick_compare.py <pdf> <json> pairing <pairing_id>")
            sys.exit(1)

        pairing_id = sys.argv[4]
        compare_pairing(pairing_id, pdf_text, parsed_data)

    elif command == 'search':
        if len(sys.argv) < 5:
            print("Error: Search term required")
            print("Usage: python3 quick_compare.py <pdf> <json> search <term>")
            sys.exit(1)

        search_term = sys.argv[4]
        search_value(search_term, pdf_text, parsed_data)

    else:
        print(f"Unknown command: {command}")
        print("Valid commands: summary, totals, pairing, search")
        sys.exit(1)

if __name__ == '__main__':
    main()
