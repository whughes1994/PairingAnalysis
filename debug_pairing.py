#!/usr/bin/env python3
"""Debug pairing detection."""
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

# Read only first page
with pdfplumber.open('ORDDSLMini.pdf') as pdf:
    first_page = pdf.pages[0]
    lines = first_page.extract_text().splitlines()

    print("Testing pairing detection on first page:")
    print("=" * 80)

    for line_num, line in enumerate(lines, 1):
        # Check pairing condition
        if 'EFF' in line and ' ID ' in line:
            print(f'\nLine {line_num}: PAIRING CONDITION MET')
            print(f'  Content: {line}')

            # Call parse_line
            parser.parse_line(line, line_num)

            print(f'  Current pairing object: {parser.current_pairing}')
            if parser.current_pairing:
                print(f'  Pairing ID: {parser.current_pairing.id}')
                print(f'  Category: {parser.current_pairing.pairing_category}')

# Finalize
result = parser.finalize()
print("\n" + "=" * 80)
print(f'Total bid periods: {len(result.data)}')
if result.data:
    print(f'Total pairings in bid period: {len(result.data[0].pairings)}')
    if result.data[0].pairings:
        print(f'First pairing: {result.data[0].pairings[0].id}')
