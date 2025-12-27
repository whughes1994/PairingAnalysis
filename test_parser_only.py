#!/usr/bin/env python3
"""Quick parser test without full dependencies."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("Testing parser with ORDDSLMini.pdf...")
print("=" * 60)

try:
    import pdfplumber
    from parsers.pairing_parser import PairingParser

    # Minimal config
    config = {
        'processing': {'skip_on_error': True},
        'parser': {'leg_columns': {}, 'patterns': {}}
    }

    parser = PairingParser(config)

    # Read PDF
    with pdfplumber.open('ORDDSLMini.pdf') as pdf:
        line_num = 0
        for page in pdf.pages:
            lines = page.extract_text().splitlines()
            for line in lines:
                line_num += 1
                parser.parse_line(line, line_num)

    # Finalize
    result = parser.finalize()
    stats = parser.get_stats()

    print(f"\n✓ Parsing complete!")
    print(f"  Lines processed: {stats['total_lines']}")
    print(f"  Pairings found: {stats['pairings_parsed']}")
    print(f"  Errors: {stats['errors']}")

    if result.data:
        bp = result.data[0]
        print(f"\n  Bid Period: {bp.bid_month_year}")
        print(f"  Fleet: {bp.fleet}")
        print(f"  Base: {bp.base}")
        print(f"  Pairings: {len(bp.pairings)}")

        if bp.pairings:
            p = bp.pairings[0]
            print(f"\n  First Pairing:")
            print(f"    ID: {p.id}")
            print(f"    Category: {p.pairing_category}")
            print(f"    Days: {p.days}")
            print(f"    Duty Periods: {len(p.duty_periods)}")
    else:
        print("\n✗ No data extracted - check parser logic")

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("=" * 60)
