#!/usr/bin/env python3
"""
Validate JSON output against source PDF to verify parsing accuracy.

Usage:
    python3 validate_output.py --pdf ORDDSLMini.pdf --json output/test.json
    python3 validate_output.py --pdf ORDDSL.pdf --json output/ORD.json --sample 10
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import pdfplumber
import re


class ParsingValidator:
    """Validate parsed JSON against source PDF."""

    def __init__(self, pdf_path: str, json_path: str):
        self.pdf_path = pdf_path
        self.json_path = json_path
        self.issues = []
        self.warnings = []
        self.stats = {
            'pairings_checked': 0,
            'legs_checked': 0,
            'critical_errors': 0,
            'warnings': 0
        }

    def validate(self, sample_size: int = None) -> Dict:
        """Run all validation checks."""
        print(f"\n{'='*80}")
        print("VALIDATION REPORT")
        print(f"{'='*80}")
        print(f"PDF: {self.pdf_path}")
        print(f"JSON: {self.json_path}")
        print(f"{'='*80}\n")

        # Load JSON
        with open(self.json_path) as f:
            data = json.load(f)

        # Load PDF text for reference
        pdf_text = self._load_pdf_text()

        # Run checks
        self._check_pairing_counts(data, pdf_text)
        self._check_data_quality(data, sample_size)
        self._check_field_consistency(data)
        self._spot_check_pairings(data, pdf_text, sample_size)

        # Print results
        self._print_report()

        return {
            'issues': self.issues,
            'warnings': self.warnings,
            'stats': self.stats
        }

    def _load_pdf_text(self) -> str:
        """Extract all text from PDF."""
        print("Loading PDF...")
        with pdfplumber.open(self.pdf_path) as pdf:
            pages = []
            for page in pdf.pages:
                pages.append(page.extract_text())
        return '\n'.join(pages)

    def _check_pairing_counts(self, data: Dict, pdf_text: str):
        """Verify pairing count matches PDF."""
        print("Checking pairing counts...")

        # Count pairing headers in PDF
        pdf_pairing_count = len(re.findall(r'EFF.*? ID [A-Z0-9]+', pdf_text))

        # Count in JSON
        json_pairing_count = sum(
            len(bp['pairings']) for bp in data['data']
        )

        self.stats['pairings_in_pdf'] = pdf_pairing_count
        self.stats['pairings_in_json'] = json_pairing_count

        if pdf_pairing_count != json_pairing_count:
            diff = abs(pdf_pairing_count - json_pairing_count)
            pct = (diff / pdf_pairing_count) * 100
            self.issues.append({
                'type': 'COUNT_MISMATCH',
                'severity': 'CRITICAL' if pct > 5 else 'WARNING',
                'message': f"Pairing count mismatch: PDF has {pdf_pairing_count}, JSON has {json_pairing_count} (diff: {diff}, {pct:.1f}%)"
            })
            self.stats['critical_errors'] += 1
        else:
            print(f"  ✓ Pairing count matches: {json_pairing_count}")

    def _check_data_quality(self, data: Dict, sample_size: int = None):
        """Check for data quality issues."""
        print("\nChecking data quality...")

        all_pairings = []
        for bp in data['data']:
            all_pairings.extend(bp['pairings'])

        if sample_size:
            import random
            all_pairings = random.sample(all_pairings, min(sample_size, len(all_pairings)))

        self.stats['pairings_checked'] = len(all_pairings)

        for pairing in all_pairings:
            pairing_id = pairing.get('id', 'UNKNOWN')

            # Check for missing critical fields
            if not pairing.get('id'):
                self._add_issue('MISSING_ID', 'CRITICAL', f"Pairing missing ID")

            if not pairing.get('pairing_category'):
                self._add_warning('MISSING_CATEGORY', f"Pairing {pairing_id} missing category")

            # Check duty periods
            for dp_idx, dp in enumerate(pairing.get('duty_periods', [])):
                # Check for empty duty periods
                if not dp.get('legs'):
                    self._add_warning('EMPTY_DUTY_PERIOD',
                                    f"Pairing {pairing_id} DP{dp_idx+1} has no legs")

                # Check each leg
                for leg_idx, leg in enumerate(dp.get('legs', [])):
                    self.stats['legs_checked'] += 1
                    self._validate_leg(leg, pairing_id, dp_idx, leg_idx)

        print(f"  Checked {self.stats['pairings_checked']} pairings")
        print(f"  Checked {self.stats['legs_checked']} legs")

    def _validate_leg(self, leg: Dict, pairing_id: str, dp_idx: int, leg_idx: int):
        """Validate individual leg data."""
        leg_ref = f"{pairing_id} DP{dp_idx+1} Leg{leg_idx+1}"

        # Critical checks
        if not leg.get('departure_station'):
            self._add_issue('MISSING_STATION', 'CRITICAL',
                          f"{leg_ref}: Missing departure station")

        if not leg.get('arrival_station'):
            self._add_issue('MISSING_STATION', 'CRITICAL',
                          f"{leg_ref}: Missing arrival station")

        # Check for misaligned data (common parsing error)
        flight_time = leg.get('flight_time', '0')
        duty_time = leg.get('duty_time', '0')

        # Flight legs should have flight_time > 0
        if not leg.get('deadhead', False):
            if flight_time == '0' or not flight_time:
                self._add_issue('ZERO_FLIGHT_TIME', 'CRITICAL',
                              f"{leg_ref}: Non-deadhead leg has zero flight time "
                              f"({leg.get('departure_station')}->{leg.get('arrival_station')})")

            if duty_time == '0' or not duty_time:
                self._add_issue('ZERO_DUTY_TIME', 'CRITICAL',
                              f"{leg_ref}: Leg has zero duty time")

        # Check time format consistency
        if flight_time and flight_time != '0':
            if ':' not in flight_time:
                self._add_issue('INVALID_TIME_FORMAT', 'CRITICAL',
                              f"{leg_ref}: Invalid flight_time format: {flight_time}")

        # Check for suspicious ground_time values
        ground_time = leg.get('ground_time', '0')
        if ground_time and ':' in ground_time:
            try:
                hours, mins = map(int, ground_time.split(':'))
                total_minutes = hours * 60 + mins
                # Ground time > 24 hours is suspicious
                if total_minutes > 1440:
                    self._add_warning('SUSPICIOUS_GROUND_TIME',
                                    f"{leg_ref}: Very long ground time: {ground_time}")
            except ValueError:
                pass

        # Check meal_code isn't a number (common field misalignment)
        meal_code = leg.get('meal_code')
        if meal_code:
            try:
                float(meal_code)
                # If it's a number, it's probably misaligned
                self._add_issue('INVALID_MEAL_CODE', 'CRITICAL',
                              f"{leg_ref}: Meal code appears to be a number: {meal_code} "
                              f"(likely field misalignment)")
            except ValueError:
                # Good - meal codes should be letters
                pass

    def _check_field_consistency(self, data: Dict):
        """Check for field consistency across all records."""
        print("\nChecking field consistency...")

        # Collect all unique equipment codes
        equipment_codes = set()
        station_codes = set()

        for bp in data['data']:
            for pairing in bp['pairings']:
                for dp in pairing.get('duty_periods', []):
                    for leg in dp.get('legs', []):
                        if leg.get('equipment'):
                            equipment_codes.add(leg['equipment'])
                        if leg.get('departure_station'):
                            station_codes.add(leg['departure_station'])
                        if leg.get('arrival_station'):
                            station_codes.add(leg['arrival_station'])

        print(f"  Found {len(equipment_codes)} unique equipment types")
        print(f"  Found {len(station_codes)} unique stations")

        # Check for suspicious codes (too short/long)
        for code in equipment_codes:
            if len(code) < 2 or len(code) > 4:
                self._add_warning('SUSPICIOUS_EQUIPMENT',
                                f"Unusual equipment code: '{code}'")

        for code in station_codes:
            if len(code) != 3:
                self._add_warning('SUSPICIOUS_STATION',
                                f"Unusual station code: '{code}' (should be 3 letters)")

    def _spot_check_pairings(self, data: Dict, pdf_text: str, sample_size: int = None):
        """Spot check specific pairings against PDF."""
        print("\nSpot checking pairings against PDF...")

        all_pairings = []
        for bp in data['data']:
            all_pairings.extend(bp['pairings'])

        # Check first, middle, and last pairing
        check_indices = [0]
        if len(all_pairings) > 2:
            check_indices.append(len(all_pairings) // 2)
            check_indices.append(len(all_pairings) - 1)

        for idx in check_indices:
            pairing = all_pairings[idx]
            pairing_id = pairing.get('id', 'UNKNOWN')

            # Find pairing in PDF
            pattern = rf'ID {pairing_id}\b'
            if re.search(pattern, pdf_text):
                print(f"  ✓ Pairing {pairing_id} found in PDF")

                # Extract the section around this pairing
                match = re.search(pattern, pdf_text)
                if match:
                    start = max(0, match.start() - 100)
                    end = min(len(pdf_text), match.end() + 500)
                    section = pdf_text[start:end]

                    # Verify category
                    category = pairing.get('pairing_category', '')
                    if category and category not in section:
                        self._add_warning('CATEGORY_MISMATCH',
                                        f"Pairing {pairing_id} category '{category}' not found near ID in PDF")
            else:
                self._add_issue('PAIRING_NOT_IN_PDF', 'CRITICAL',
                              f"Pairing {pairing_id} not found in PDF")

    def _add_issue(self, issue_type: str, severity: str, message: str):
        """Add an issue to the list."""
        self.issues.append({
            'type': issue_type,
            'severity': severity,
            'message': message
        })
        if severity == 'CRITICAL':
            self.stats['critical_errors'] += 1

    def _add_warning(self, warning_type: str, message: str):
        """Add a warning to the list."""
        self.warnings.append({
            'type': warning_type,
            'message': message
        })
        self.stats['warnings'] += 1

    def _print_report(self):
        """Print validation report."""
        print(f"\n{'='*80}")
        print("VALIDATION SUMMARY")
        print(f"{'='*80}")

        print(f"\nStatistics:")
        print(f"  Pairings in PDF:  {self.stats.get('pairings_in_pdf', 'N/A')}")
        print(f"  Pairings in JSON: {self.stats.get('pairings_in_json', 'N/A')}")
        print(f"  Pairings checked: {self.stats['pairings_checked']}")
        print(f"  Legs checked:     {self.stats['legs_checked']}")

        # Critical errors
        critical_issues = [i for i in self.issues if i['severity'] == 'CRITICAL']
        if critical_issues:
            print(f"\n❌ CRITICAL ERRORS ({len(critical_issues)}):")
            for issue in critical_issues[:20]:  # Show first 20
                print(f"  • {issue['message']}")
            if len(critical_issues) > 20:
                print(f"  ... and {len(critical_issues) - 20} more")
        else:
            print(f"\n✓ No critical errors found")

        # Warnings
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings[:10]:  # Show first 10
                print(f"  • {warning['message']}")
            if len(self.warnings) > 10:
                print(f"  ... and {len(self.warnings) - 10} more")
        else:
            print(f"\n✓ No warnings")

        # Overall result
        print(f"\n{'='*80}")
        if critical_issues:
            print(f"❌ VALIDATION FAILED - {len(critical_issues)} critical errors found")
            print(f"\nRecommendation: Review parsing logic for legs with zero flight time")
        elif self.warnings:
            print(f"⚠️  VALIDATION PASSED WITH WARNINGS - {len(self.warnings)} warnings")
        else:
            print(f"✅ VALIDATION PASSED - No errors or warnings")
        print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(description="Validate parsed JSON against source PDF")
    parser.add_argument('--pdf', type=str, required=True, help="Source PDF file")
    parser.add_argument('--json', type=str, required=True, help="Parsed JSON file")
    parser.add_argument('--sample', type=int, help="Number of pairings to sample for detailed checks")
    parser.add_argument('--output', type=str, help="Save detailed report to file")

    args = parser.parse_args()

    # Check files exist
    if not Path(args.pdf).exists():
        print(f"Error: PDF file not found: {args.pdf}")
        sys.exit(1)

    if not Path(args.json).exists():
        print(f"Error: JSON file not found: {args.json}")
        sys.exit(1)

    # Run validation
    validator = ParsingValidator(args.pdf, args.json)
    result = validator.validate(sample_size=args.sample)

    # Save detailed report if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Detailed report saved to: {args.output}")

    # Exit code based on critical errors
    sys.exit(1 if result['stats']['critical_errors'] > 0 else 0)


if __name__ == '__main__':
    main()
