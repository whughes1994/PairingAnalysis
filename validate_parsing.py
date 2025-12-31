#!/usr/bin/env python3
"""
Comprehensive validation framework for pairing PDF parsing.

This script validates parsed data against the source PDF to ensure accuracy.
Run after parsing to verify data integrity.
"""

import json
import sys
from pathlib import Path
import pdfplumber
from collections import defaultdict
from typing import Dict, List, Tuple
import re


class ParsingValidator:
    """Validates parsed pairing data against source PDF."""

    def __init__(self, pdf_path: str, json_path: str):
        self.pdf_path = Path(pdf_path)
        self.json_path = Path(json_path)
        self.errors = []
        self.warnings = []
        self.stats = defaultdict(int)

    def run_validation(self) -> bool:
        """Run all validation checks."""
        print("=" * 80)
        print("PAIRING PARSING VALIDATION")
        print("=" * 80)
        print(f"\nPDF: {self.pdf_path.name}")
        print(f"JSON: {self.json_path.name}\n")

        # Load parsed data
        with open(self.json_path, 'r') as f:
            raw_data = json.load(f)

        # Handle both old and new JSON structures
        if 'data' in raw_data:
            # New structure: {"data": [...], "metadata": {...}}
            self.parsed_data = {
                'bid_periods': raw_data['data'],
                'base': raw_data['data'][0].get('base') if raw_data['data'] else None,
                'month': raw_data['data'][0].get('bid_month_year') if raw_data['data'] else None
            }
        else:
            # Old structure: {"bid_periods": [...], "base": "...", "month": "..."}
            self.parsed_data = raw_data

        # Extract text from PDF
        with pdfplumber.open(self.pdf_path) as pdf:
            self.pdf_text = '\n'.join([page.extract_text() or '' for page in pdf.pages])

        # Run validation checks
        checks = [
            ("Header Validation", self._validate_header),
            ("Bid Period Count", self._validate_bid_period_count),
            ("Fleet Assignment", self._validate_fleet_assignments),
            ("Pairing Count", self._validate_pairing_counts),
            ("Totals Validation", self._validate_totals),
            ("Pairing Structure", self._validate_pairing_structure),
            ("Time Format Validation", self._validate_time_formats),
            ("Station Codes", self._validate_station_codes),
            ("Data Completeness", self._validate_completeness),
        ]

        all_passed = True
        for check_name, check_func in checks:
            print(f"\n{'=' * 80}")
            print(f"CHECK: {check_name}")
            print('=' * 80)
            try:
                passed = check_func()
                if not passed:
                    all_passed = False
                    print(f"❌ FAILED: {check_name}")
                else:
                    print(f"✅ PASSED: {check_name}")
            except Exception as e:
                all_passed = False
                self.errors.append(f"{check_name}: {str(e)}")
                print(f"❌ ERROR in {check_name}: {e}")

        # Print summary
        self._print_summary()

        return all_passed

    def _validate_header(self) -> bool:
        """Validate base and month from header."""
        print("\nValidating header information...")

        base = self.parsed_data.get('base')
        month = self.parsed_data.get('month')

        if not base:
            self.errors.append("Base not found in parsed data")
            return False

        if not month:
            self.warnings.append("Month not found in parsed data")

        # Check if base appears in PDF
        if base not in self.pdf_text:
            self.errors.append(f"Base '{base}' not found in PDF text")
            return False

        print(f"  Base: {base} ✓")
        if month:
            print(f"  Month: {month} ✓")

        return True

    def _validate_bid_period_count(self) -> bool:
        """Validate number of bid periods."""
        print("\nValidating bid period count...")

        bid_periods = self.parsed_data.get('bid_periods', [])
        num_bid_periods = len(bid_periods)

        # Count fleet totals in PDF (better pattern)
        totals_pattern = re.compile(r'[A-Z]{3}\s+[0-9]{2,3}[A-Z]?\s+FTM-\s*[\d:,]+\s+TTL-\s*[\d:,]+')
        ftm_count = len(totals_pattern.findall(self.pdf_text))

        print(f"  Parsed bid periods: {num_bid_periods}")
        print(f"  Expected (from PDF): {ftm_count}")

        if num_bid_periods != ftm_count:
            self.warnings.append(
                f"Bid period count mismatch: parsed {num_bid_periods}, expected {ftm_count}"
            )
            return False

        return True

    def _validate_fleet_assignments(self) -> bool:
        """Validate fleet assignments for all bid periods."""
        print("\nValidating fleet assignments...")

        all_valid = True
        bid_periods = self.parsed_data.get('bid_periods', [])

        fleet_pattern = re.compile(r'\b([A-Z]{3})\s+([0-9]{2,3}[A-Z]?)\s+FTM-')
        pdf_fleets = fleet_pattern.findall(self.pdf_text)

        print(f"  Found {len(pdf_fleets)} fleet indicators in PDF")

        for idx, bp in enumerate(bid_periods):
            fleet = bp.get('fleet')
            if not fleet:
                self.errors.append(f"Bid period {idx} missing fleet assignment")
                all_valid = False
            else:
                print(f"  Bid period {idx}: Fleet {fleet}")

        # Check for duplicate fleets
        parsed_fleets = [bp.get('fleet') for bp in bid_periods if bp.get('fleet')]
        if len(parsed_fleets) != len(set(parsed_fleets)):
            self.warnings.append("Duplicate fleet assignments found")

        return all_valid

    def _validate_pairing_counts(self) -> bool:
        """Validate pairing counts per bid period."""
        print("\nValidating pairing counts...")

        all_valid = True
        bid_periods = self.parsed_data.get('bid_periods', [])

        for idx, bp in enumerate(bid_periods):
            fleet = bp.get('fleet', f'BP{idx}')
            pairings = bp.get('pairings', [])
            pairing_count = len(pairings)

            print(f"  Fleet {fleet}: {pairing_count} pairings")

            if pairing_count == 0:
                self.errors.append(f"Fleet {fleet} has 0 pairings")
                all_valid = False
            elif pairing_count < 10:
                self.warnings.append(f"Fleet {fleet} has unusually few pairings ({pairing_count})")

            self.stats[f'fleet_{fleet}_pairings'] = pairing_count

        return all_valid

    def _validate_totals(self) -> bool:
        """Validate FTM/TTL totals match."""
        print("\nValidating bid period totals...")

        all_valid = True
        bid_periods = self.parsed_data.get('bid_periods', [])

        # Extract totals from PDF
        totals_pattern = re.compile(
            r'([A-Z]{3})\s+([0-9]{2,3}[A-Z]?)\s+FTM-\s*([\d:,]+)\s+TTL-\s*([\d:,]+)'
        )
        pdf_totals = totals_pattern.findall(self.pdf_text)

        print(f"  Found {len(pdf_totals)} totals lines in PDF")

        for idx, (base, fleet, ftm, ttl) in enumerate(pdf_totals):
            print(f"\n  PDF Total {idx + 1}:")
            print(f"    Fleet: {fleet}")
            print(f"    FTM: {ftm}")
            print(f"    TTL: {ttl}")

            # Find matching bid period
            matching_bp = None
            for bp in bid_periods:
                if bp.get('fleet') == fleet:
                    matching_bp = bp
                    break

            if matching_bp:
                parsed_ftm = matching_bp.get('ftm', '')
                parsed_ttl = matching_bp.get('ttl', '')

                print(f"    Parsed FTM: {parsed_ftm}")
                print(f"    Parsed TTL: {parsed_ttl}")

                if parsed_ftm != ftm or parsed_ttl != ttl:
                    self.errors.append(
                        f"Fleet {fleet} totals mismatch: "
                        f"PDF FTM={ftm} TTL={ttl}, "
                        f"Parsed FTM={parsed_ftm} TTL={parsed_ttl}"
                    )
                    all_valid = False
                else:
                    print("    ✓ Match")
            else:
                self.errors.append(f"No parsed bid period found for fleet {fleet}")
                all_valid = False

        return all_valid

    def _validate_pairing_structure(self) -> bool:
        """Validate pairing structure consistency."""
        print("\nValidating pairing structure...")

        all_valid = True
        sample_count = 0
        max_samples = 5

        bid_periods = self.parsed_data.get('bid_periods', [])

        for bp in bid_periods:
            # In new structure, fleet and base are at bid period level
            bp_fleet = bp.get('fleet')
            bp_base = bp.get('base')

            for pairing in bp.get('pairings', []):
                if sample_count >= max_samples:
                    break

                pairing_id = pairing.get('id')
                duty_periods = pairing.get('duty_periods', [])
                days = pairing.get('days')

                print(f"\n  Checking pairing {pairing_id}:")
                print(f"    Fleet: {bp_fleet}")
                print(f"    Base: {bp_base}")
                print(f"    Days: {days}")
                print(f"    Duty periods: {len(duty_periods)}")

                # Validate required fields (fleet/base can be at bid period level)
                required_fields = ['id', 'days', 'credit_minutes']
                missing_fields = [f for f in required_fields if not pairing.get(f)]

                # Check fleet/base either in pairing or bid period
                if not pairing.get('fleet') and not bp_fleet:
                    missing_fields.append('fleet')
                if not pairing.get('base') and not bp_base:
                    missing_fields.append('base')

                if missing_fields:
                    self.errors.append(
                        f"Pairing {pairing_id} missing fields: {missing_fields}"
                    )
                    all_valid = False

                # Validate duty periods
                for dp_idx, dp in enumerate(duty_periods):
                    legs = dp.get('legs', [])
                    if not legs:
                        self.warnings.append(
                            f"Pairing {pairing_id} duty period {dp_idx} has no legs"
                        )

                sample_count += 1

        return all_valid

    def _validate_time_formats(self) -> bool:
        """Validate time format consistency."""
        print("\nValidating time formats...")

        all_valid = True
        time_pattern = re.compile(r'^\d{2}:\d{2}$')
        sample_count = 0
        max_samples = 10

        bid_periods = self.parsed_data.get('bid_periods', [])

        for bp in bid_periods:
            for pairing in bp.get('pairings', []):
                if sample_count >= max_samples:
                    break

                for dp in pairing.get('duty_periods', []):
                    for leg in dp.get('legs', []):
                        # Check time formats
                        dep_time = leg.get('departure_time_formatted')
                        arr_time = leg.get('arrival_time_formatted')

                        if dep_time and not time_pattern.match(dep_time):
                            self.warnings.append(
                                f"Invalid departure time format: {dep_time} in pairing {pairing.get('id')}"
                            )
                            all_valid = False

                        if arr_time and not time_pattern.match(arr_time):
                            self.warnings.append(
                                f"Invalid arrival time format: {arr_time} in pairing {pairing.get('id')}"
                            )
                            all_valid = False

                sample_count += 1

        print(f"  Checked {sample_count} pairings for time format validity")
        return all_valid

    def _validate_station_codes(self) -> bool:
        """Validate airport station codes."""
        print("\nValidating station codes...")

        all_valid = True
        station_pattern = re.compile(r'^[A-Z]{3}$')
        invalid_stations = set()

        bid_periods = self.parsed_data.get('bid_periods', [])

        for bp in bid_periods:
            for pairing in bp.get('pairings', []):
                for dp in pairing.get('duty_periods', []):
                    for leg in dp.get('legs', []):
                        dep_station = leg.get('departure_station')
                        arr_station = leg.get('arrival_station')

                        if dep_station and not station_pattern.match(dep_station):
                            invalid_stations.add(dep_station)

                        if arr_station and not station_pattern.match(arr_station):
                            invalid_stations.add(arr_station)

        if invalid_stations:
            self.errors.append(f"Invalid station codes found: {invalid_stations}")
            all_valid = False
        else:
            print("  All station codes valid (3-letter format)")

        return all_valid

    def _validate_completeness(self) -> bool:
        """Validate data completeness."""
        print("\nValidating data completeness...")

        all_valid = True
        total_pairings = 0
        total_legs = 0

        bid_periods = self.parsed_data.get('bid_periods', [])

        for bp in bid_periods:
            pairings = bp.get('pairings', [])
            total_pairings += len(pairings)

            for pairing in pairings:
                for dp in pairing.get('duty_periods', []):
                    legs = dp.get('legs', [])
                    total_legs += len(legs)

        print(f"  Total bid periods: {len(bid_periods)}")
        print(f"  Total pairings: {total_pairings}")
        print(f"  Total legs: {total_legs}")

        if total_pairings == 0:
            self.errors.append("No pairings parsed")
            all_valid = False

        if total_legs == 0:
            self.errors.append("No legs parsed")
            all_valid = False

        avg_legs_per_pairing = total_legs / total_pairings if total_pairings > 0 else 0
        print(f"  Average legs per pairing: {avg_legs_per_pairing:.1f}")

        if avg_legs_per_pairing < 2:
            self.warnings.append(
                f"Unusually low average legs per pairing: {avg_legs_per_pairing:.1f}"
            )

        return all_valid

    def _print_summary(self):
        """Print validation summary."""
        print("\n" + "=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)

        if not self.errors and not self.warnings:
            print("\n✅ ALL VALIDATION CHECKS PASSED!")
        else:
            if self.errors:
                print(f"\n❌ ERRORS ({len(self.errors)}):")
                for i, error in enumerate(self.errors, 1):
                    print(f"  {i}. {error}")

            if self.warnings:
                print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
                for i, warning in enumerate(self.warnings, 1):
                    print(f"  {i}. {warning}")

        print("\nSTATISTICS:")
        for key, value in sorted(self.stats.items()):
            print(f"  {key}: {value}")


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print("Usage: python3 validate_parsing.py <pdf_file> <json_file>")
        print("\nExample:")
        print("  python3 validate_parsing.py ORDDSL.pdf output/ORD.json")
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

    # Run validation
    validator = ParsingValidator(pdf_path, json_path)
    passed = validator.run_validation()

    # Exit with appropriate code
    sys.exit(0 if passed else 1)


if __name__ == '__main__':
    main()
