#!/usr/bin/env python3
"""Debug duty period parsing."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import pdfplumber
from parsers.pairing_parser import PairingParser

# Minimal config
config = {
    'processing': {'skip_on_error': True},
    'parser': {'leg_columns': {}, 'patterns': {}}
}

parser = PairingParser(config)

# Read first page and process line by line
with pdfplumber.open('ORDDSLMini.pdf') as pdf:
    first_page = pdf.pages[0]
    lines = first_page.extract_text().splitlines()

    print("Processing first pairing (lines 4-12):")
    print("=" * 80)

    for line_num in range(3, 13):
        if line_num >= len(lines):
            break

        line = lines[line_num]
        print(f"\nLine {line_num+1}: {line}")

        # Call parse_line
        parser.parse_line(line, line_num + 1)

        # Show state
        if parser.current_pairing:
            print(f"  Current pairing: {parser.current_pairing.id}")
            print(f"  Duty periods so far: {len(parser.current_pairing.duty_periods)}")

        if parser.current_duty_period:
            print(f"  Current duty period:")
            print(f"    Report time: {parser.current_duty_period.report_time}")
            print(f"    Release time: {parser.current_duty_period.release_time}")
            print(f"    Legs: {len(parser.current_duty_period.legs)}")
        else:
            print(f"  No current duty period")

# Finalize
result = parser.finalize()
print("\n" + "=" * 80)
print("FINAL RESULT:")
if result.data and result.data[0].pairings:
    p = result.data[0].pairings[0]
    print(f"Pairing {p.id} has {len(p.duty_periods)} duty periods")
    for i, dp in enumerate(p.duty_periods, 1):
        print(f"  DP{i}: RPT {dp.report_time}, {len(dp.legs)} legs, RLS {dp.release_time}")
