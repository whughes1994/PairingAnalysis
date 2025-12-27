"""
Main pairing parser implementation.
"""
import re
from typing import Dict, Any, Optional
from parsers.base_parser import BaseParser
from models import Leg, DutyPeriod, Pairing, BidPeriod, MasterData


class PairingParser(BaseParser):
    """Parser for airline pairing PDF files."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize pairing parser."""
        super().__init__(config)

        # State tracking
        self.master_data = MasterData()
        self.current_bid_period: Optional[BidPeriod] = None
        self.current_pairing: Optional[Pairing] = None
        self.current_duty_period: Optional[DutyPeriod] = None
        self.current_leg: Optional[Leg] = None

        # Statistics
        self.stats = {
            'total_lines': 0,
            'pairings_parsed': 0,
            'errors': 0,
            'warnings': 0
        }

    def parse_line(self, line: str, line_number: int) -> Optional[Dict]:
        """Parse a single line and update state."""
        self.stats['total_lines'] += 1

        try:
            # Header line (bid period info) - matches "EFF dd/dd/dd THRU dd/dd/dd 787 BASE MONTH YEAR"
            # or contains "1DSL" marker
            # Headers repeat at top of each page, identified by fleet number but no pairing ID
            is_header = ("1DSL" in line or
                        ("EFF" in line and
                         "THRU" in line and
                         " ID " not in line and  # Not a pairing line
                         ("787" in line or "777" in line or "737" in line or "75E" in line or "21N" in line)))  # Has fleet number

            if is_header:
                self._parse_header_line(line)

            # Total FTM/TTL line (end of bid period)
            # Format: "ORD 320 FTM-13,857:51 TTL-14,848:56"
            # NOT the pairing summary which has "DAYS-" at start
            elif "FTM-" in line and "TTL-" in line and "DAYS-" not in line:
                self._parse_totals_line(line)
                self._finalize_bid_period()

            # Pairing start line (has ID and category) - CHECK BEFORE CALENDAR!
            elif "EFF" in line and " ID " in line:
                self._parse_pairing_start(line)

            # Report time (start of duty period) - CHECK BEFORE CALENDAR!
            elif "RPT:" in line:
                self._parse_report_time(line)

            # Release time (end of duty period) - CHECK BEFORE CALENDAR!
            elif "RLS:" in line:
                self._parse_release_time(line)
                # Check if hotel info is on the same line (common in compact format)
                if "HTL:" in line:
                    self._parse_hotel(line)
                self._finalize_duty_period()

            # Flight leg - CHECK BEFORE CALENDAR!
            elif self.is_leg_line(line):
                self._parse_leg(line)

            # Calendar instances (date patterns) - DISABLED for compact format
            # In compact format, calendar dates are on the pairing header line itself
            # elif "|" in line and "SU" not in line and "EQP" not in line:
            #     self._parse_calendar_line(line)

            # Hotel information
            elif "HTL:" in line:
                self._parse_hotel(line)

            # Ground transportation
            elif any(x in line for x in ['VIP', 'AIRLINE', 'CONNECT', 'TAXI', 'TOURING']):
                self._parse_ground_transport(line)

            # Pairing summary (end of pairing)
            elif "DAYS-" in line:
                self._parse_pairing_summary(line)
                self._finalize_pairing()

        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"Error parsing line {line_number}: {line[:80]}... - {e}")

        return None

    def _parse_header_line(self, line: str):
        """Parse bid period header line."""
        # Only create new bid period if we don't have one yet
        # (headers repeat on every page, but represent the same bid period)
        if not self.current_bid_period:
            self.current_bid_period = BidPeriod()

        # Check if this is the compact format (ORDDSLMini) or full format (with 1DSL)
        if "1DSL" in line:
            # Original format: positions from notebook
            self.current_bid_period.bid_month_year = self.extract_field(line, 68, 78)
            self.current_bid_period.fleet = self.extract_field(line, 35, 38)
            self.current_bid_period.base = self.extract_field(line, 42, 55)
            self.current_bid_period.effective_date = self.extract_field(line, 9, 17)
            self.current_bid_period.through_date = self.extract_field(line, 23, 31)
        else:
            # Compact format: "EFF 12/30/25 THRU 01/29/26 787 CHICAGO JAN 2026 12/30/25"
            self.current_bid_period.effective_date = self.extract_field(line, 4, 12)
            self.current_bid_period.through_date = self.extract_field(line, 18, 26)
            self.current_bid_period.fleet = self.extract_field(line, 27, 30)
            self.current_bid_period.base = self.extract_field(line, 31, 38)
            self.current_bid_period.bid_month_year = self.extract_field(line, 39, 47)

        self.logger.debug(
            f"Started bid period: {self.current_bid_period.bid_month_year} "
            f"{self.current_bid_period.fleet} {self.current_bid_period.base}"
        )

    def _parse_totals_line(self, line: str):
        """Parse FTM/TTL totals line.

        Format: "ORD 787 FTM-13,578:02 TTL-14,387:35"
        This is the authoritative source for fleet designation.
        """
        if not self.current_bid_period:
            return

        # Extract fleet from totals line (e.g., "ORD 787 FTM-...")
        # Fleet is between base and FTM
        fleet_pattern = r"([A-Z]{3})\s+([0-9]{2,3}[A-Z]?)\s+FTM-"
        fleet_match = re.search(fleet_pattern, line)
        if fleet_match:
            self.current_bid_period.fleet = fleet_match.group(2)

        # Extract FTM and TTL values
        pattern = r"(FTM|TTL)-\s*(\d{1,}(?:,\d{1,})*:\d{2})"
        matches = re.findall(pattern, line)

        if len(matches) >= 2:
            self.current_bid_period.ftm = matches[0][1]
            self.current_bid_period.ttl = matches[1][1]

    def _parse_calendar_line(self, line: str):
        """Parse calendar date instances."""
        if not self.current_pairing:
            return

        # Extract digits from the calendar section
        calendar_section = line[109:129] if len(line) > 109 else line
        dates = re.findall(r'(\d+)', calendar_section)
        self.current_pairing.date_instances.extend(dates)

    def _parse_pairing_start(self, line: str):
        """Parse pairing start line (EFF line)."""
        # Finalize any previous pairing
        if self.current_pairing:
            self._finalize_pairing()

        self.current_pairing = Pairing()

        # Extract pairing information (use full line, not substring that cuts off 'E')
        pattern = (
            r"EFF (\d{2}/\d{2}/\d{2}) THRU (\d{2}/\d{2}/\d{2}).*?"
            r"(F/O)?\s*ID (\w+)\s+-\s+(\w+)(?:\s+\((\w+)\))?"
        )

        match = re.search(pattern, line)
        if match:
            eff_date, thru_date, fo_presence, id_value, category, optional_content = match.groups()
            self.current_pairing.effective_date = eff_date
            self.current_pairing.through_date = thru_date
            self.current_pairing.is_first_officer = bool(fo_presence)
            self.current_pairing.id = id_value

            # Build category string
            category_str = category
            if optional_content:
                category_str += f" ({optional_content})"
            self.current_pairing.pairing_category = category_str

            # Extract calendar dates from end of line (compact format)
            # Calendar dates appear after the category: "BASIC (HNL) 30 31 1 2| 3"
            # Find everything after the closing paren or category, extract digits
            calendar_part = line.split(')')[-1] if ')' in line else line.split(category_str)[-1]
            dates = re.findall(r'\b(\d{1,2})\b', calendar_part)
            self.current_pairing.date_instances.extend(dates)

            self.logger.debug(f"Started pairing: {id_value} - {category_str}")

    def _parse_report_time(self, line: str):
        """Parse report time and start new duty period."""
        # Finalize previous duty period if exists
        if self.current_duty_period:
            self._finalize_duty_period()

        self.current_duty_period = DutyPeriod()
        report_time = self.extract_report_time(line)
        if report_time:
            self.current_duty_period.report_time = report_time

    def _parse_leg(self, line: str):
        """Parse flight leg data."""
        if not self.current_duty_period:
            self.current_duty_period = DutyPeriod()

        leg = Leg()

        # Split line into fields for variable-width parsing
        # Remove calendar dates (everything after the last digit before |)
        main_part = line.split('|')[0] if '|' in line else line
        fields = main_part.split()

        if len(fields) < 6:
            return

        # Check for deadhead by flight number "DH"
        if fields[1] == 'DH':
            # Deadhead format with DH flight number: eqp DH fltnum dept arr dtime atime gtime d/c dt gtime
            leg.deadhead = True
            leg.equipment = fields[0]
            leg.flight_number = fields[2]  # Actual flight number after DH
            leg.departure_station = fields[3]
            leg.arrival_station = fields[4]
            leg.departure_time = fields[5]
            leg.arrival_time = fields[6]
            if len(fields) >= 11:
                leg.ground_time = self.convert_time(fields[7])
                leg.d_c = self.convert_time(fields[8])
                leg.duty_time = self.convert_time(fields[9])
                leg.flight_time = self.convert_time(fields[10])
                leg.accumulated_flight_time = leg.flight_time
        # Check for deadhead by "D" marker in field[6]
        elif len(fields) > 6 and fields[6] == 'D':
            # Deadhead format with D marker: eqp flt dept arr dtime atime D svc ft accum_ft dt d/c
            leg.deadhead = True
            leg.equipment = fields[0]
            leg.flight_number = fields[1]
            leg.departure_station = fields[2]
            leg.arrival_station = fields[3]
            leg.departure_time = fields[4]
            leg.arrival_time = fields[5]
            if len(fields) >= 12:
                leg.flight_time = self.convert_time(fields[8])
                leg.accumulated_flight_time = self.convert_time(fields[9])
                leg.duty_time = self.convert_time(fields[10])
                leg.d_c = self.convert_time(fields[11])
        else:
            # Normal leg - detect format by checking field[8]
            # Format 1 (787, with service): eqp flt dept arr dtime atime gtime meal svc ft accum_ft dt d/c (13 fields)
            # Format 2 (737, no service):   eqp flt dept arr dtime atime gtime meal ft accum_ft dt ind d/c (12 fields)
            leg.deadhead = False
            leg.equipment = fields[0]
            leg.flight_number = fields[1]
            leg.departure_station = fields[2]
            leg.arrival_station = fields[3]
            leg.departure_time = fields[4]
            leg.arrival_time = fields[5]

            if len(fields) >= 7:
                leg.ground_time = self.convert_time(fields[6])

            # Detect format: if field[8] looks like time (H:MM or H.MM), it's Format 2 (no service code)
            has_service_code = False
            if len(fields) >= 9:
                field8 = fields[8]
                # Service code is a single letter (S, B, D, etc), not a time
                if len(field8) == 1 and field8.isalpha():
                    has_service_code = True

            if has_service_code and len(fields) >= 13:
                # Format 1: 787 format with service code
                # eqp flt dept arr dtime atime gtime meal svc ft accum_ft dt d/c
                leg.meal_code = fields[7]
                # field[8] is service code (S) - skip it
                leg.flight_time = self.convert_time(fields[9])
                leg.accumulated_flight_time = self.convert_time(fields[10])
                leg.duty_time = self.convert_time(fields[11])
                leg.d_c = self.convert_time(fields[12])
            elif not has_service_code and len(fields) >= 9:
                # Format 2: 737 format without service code
                # Two variants:
                # With meal: eqp flt dept arr dtime atime gtime meal ft accum_ft [calendar...]
                # No meal:   eqp flt dept arr dtime atime gtime ft accum_ft d/c [calendar...]

                # Check if field[7] is a meal code (single letter) or a time
                field7 = fields[7]
                if len(field7) == 1 and field7.isalpha():
                    # Has meal code
                    leg.meal_code = field7
                    leg.flight_time = self.convert_time(fields[8])
                    leg.accumulated_flight_time = self.convert_time(fields[9])
                    # Rest is calendar dates
                else:
                    # No meal code - field[7] is FTM
                    leg.flight_time = self.convert_time(field7)
                    leg.accumulated_flight_time = self.convert_time(fields[8])
                    if len(fields) >= 10:
                        leg.d_c = self.convert_time(fields[9])

        self.current_duty_period.legs.append(leg)

    def _parse_release_time(self, line: str):
        """Parse release time."""
        if not self.current_duty_period:
            return

        release_time = self.extract_release_time(line)
        if release_time:
            self.current_duty_period.release_time = release_time

    def _parse_hotel(self, line: str):
        """Parse hotel information."""
        if not self.current_duty_period:
            return

        hotel_info = self.extract_hotel_info(line)
        if hotel_info['name']:
            # Format: "NAME phone OP=> op_phone"
            hotel_str = hotel_info['name']
            if hotel_info['phone']:
                hotel_str += f" {hotel_info['phone']}"
            if hotel_info['operator_phone']:
                hotel_str += f" OP=> {hotel_info['operator_phone']}"

            self.current_duty_period.hotel = hotel_str

    def _parse_ground_transport(self, line: str):
        """Parse ground transportation."""
        if not self.current_duty_period:
            return

        transport = self.extract_ground_transport(line)
        if transport:
            self.current_duty_period.ground_transport = transport

    def _parse_pairing_summary(self, line: str):
        """Parse pairing summary metrics."""
        if not self.current_pairing:
            return

        patterns = {
            "days": r"DAYS-\s*(\d+)",
            "credit": r"CRD-\s*([\d\.]+)",
            "flight_time": r"FTM-\s*([\d\.:]+)",
            "time_away_from_base": r"TAFB-\s*([\d\.:]+)",
            "international_flight_time": r"INT-\s*([\d\.]+)",
            "nte": r"NTE-\s*([\d\.]+)",
            "meal_money": r"M\$-\s*([\d\.]+)",
            "t_c": r"T/C-\s*([\d\.]+)"
        }

        for field, pattern in patterns.items():
            match = re.search(pattern, line)
            if match:
                setattr(self.current_pairing, field, match.group(1))

    def _finalize_duty_period(self):
        """Finalize current duty period."""
        if self.current_duty_period and self.current_pairing:
            self.current_pairing.duty_periods.append(self.current_duty_period)
            self.current_duty_period = None

    def _finalize_pairing(self):
        """Finalize current pairing."""
        if self.current_pairing and self.current_bid_period:
            self.current_bid_period.pairings.append(self.current_pairing)
            self.stats['pairings_parsed'] += 1
            self.logger.debug(f"Finalized pairing: {self.current_pairing.id}")
            self.current_pairing = None

    def _finalize_bid_period(self):
        """Finalize current bid period."""
        if self.current_bid_period:
            self.master_data.data.append(self.current_bid_period)
            self.logger.info(
                f"Finalized bid period: {self.current_bid_period.bid_month_year} "
                f"with {len(self.current_bid_period.pairings)} pairings"
            )
            self.current_bid_period = None

    def finalize(self) -> MasterData:
        """Finalize parsing and return complete data."""
        # Finalize any remaining items
        if self.current_duty_period:
            self._finalize_duty_period()
        if self.current_pairing:
            self._finalize_pairing()
        if self.current_bid_period:
            self._finalize_bid_period()

        self.logger.info(
            f"Parsing complete: {self.stats['pairings_parsed']} pairings, "
            f"{self.stats['errors']} errors"
        )

        return self.master_data

    def get_stats(self) -> Dict[str, int]:
        """Get parsing statistics."""
        return self.stats.copy()
