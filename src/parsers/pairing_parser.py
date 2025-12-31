"""
Main pairing parser implementation.
"""
import re
from typing import Dict, Any, Optional
from .base_parser import BaseParser
from ..models import Leg, DutyPeriod, Pairing, BidPeriod, MasterData


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

    def is_leg_line(self, line: str) -> bool:
        """
        Detect if line contains leg data.

        Handles both:
        - Equipment-based legs: "78J 202 ORD OGG..." (starts with 2 digits + letter)
        - DH/UX deadheads: "DH 3707..." or "UX 3707..." (starts with DH or UX)

        Note: .DAT files have leading spaces, so we strip before checking
        """
        if len(line) < 2:
            return False

        # Strip leading whitespace for .DAT file compatibility
        stripped = line.lstrip()

        if len(stripped) < 2:
            return False

        # Check for equipment code format (2 digits + letter)
        if len(stripped) >= 3 and stripped[0:2].isdigit() and stripped[2].isalpha():
            return True

        # Check for specific deadhead markers: DH or UX
        if stripped.startswith('DH ') or stripped.startswith('UX '):
            return True

        return False

    def _parse_leg(self, line: str):
        """Parse flight leg data.

        Format: Equipment [DH] FlightNum Dept Arr DepTime ArrTime GroundTime MealCode(s) FlightTime AccumFlightTime AccumDutyTime

        Examples:
        - 73G 123 ORD LAX 0800 1030 2:15 B L 4:30 4:30 6:45
        - 78J DH 456 LAX SFO 1245 1415 0 7:45 12:15 14:30
        - 37K 789 SFO ORD 1415 2030 0 B D 4:15 16:30 18:45
        """
        if not self.current_duty_period:
            self.current_duty_period = DutyPeriod()

        leg = Leg()

        # Remove calendar dates (everything after |)
        main_part = line.split('|')[0] if '|' in line else line
        fields = main_part.split()

        if len(fields) < 6:
            return

        # Field index tracker
        idx = 0

        # Check if first field is a deadhead marker (UX, DH, etc.) without equipment code
        # Deadhead markers are 2-letter uppercase codes
        if len(fields[idx]) == 2 and fields[idx].isupper() and fields[idx].isalpha():
            leg.deadhead = True
            leg.equipment = None  # No equipment code for UX deadheads
            idx += 1
        else:
            # Normal leg: equipment code comes first
            leg.equipment = fields[idx]
            idx += 1

            # Check for deadhead marker after equipment (e.g., "20S DH 1124...")
            if idx < len(fields) and len(fields[idx]) == 2 and fields[idx].isupper() and fields[idx].isalpha():
                leg.deadhead = True
                idx += 1
            else:
                leg.deadhead = False

        # 3. Flight number
        if idx < len(fields):
            leg.flight_number = fields[idx]
            idx += 1

        # 4. Departure station
        if idx < len(fields):
            leg.departure_station = fields[idx]
            idx += 1

        # 5. Arrival station
        if idx < len(fields):
            leg.arrival_station = fields[idx]
            idx += 1

        # 6. Departure time (HHMM format)
        if idx < len(fields):
            leg.departure_time = fields[idx]
            idx += 1

        # 7. Arrival time (HHMM format)
        if idx < len(fields):
            leg.arrival_time = fields[idx]
            idx += 1

        # 8. Ground time (H:MM or HH:MM or may be missing)
        # Ground time is a time format (contains : or is numeric like "0")
        if idx < len(fields):
            field = fields[idx]
            # Check if this looks like a time (contains : or is "0" or numeric)
            if ':' in field or field == '0' or (field.replace('.', '').replace(':', '').isdigit()):
                leg.ground_time = self.convert_time(field)
                idx += 1
            # Otherwise, no ground time present, this is meal code

        # 9. Meal code(s) - 0 to 3 letters (B, L, D, S), space-separated
        # Meal codes are single uppercase letters, collect all of them
        meal_codes = []
        while idx < len(fields):
            field = fields[idx]
            # Meal code is 1 letter A-Z
            if len(field) == 1 and field.isalpha() and field.isupper():
                meal_codes.append(field)
                idx += 1
            else:
                break

        if meal_codes:
            leg.meal_code = ' '.join(meal_codes)

        # 10. Flight time (H:MM or HH:MM)
        if idx < len(fields):
            leg.flight_time = self.convert_time(fields[idx])
            idx += 1

        # 11. Accumulated flight time (H:MM or HH:MM)
        if idx < len(fields):
            leg.accumulated_flight_time = self.convert_time(fields[idx])
            idx += 1

        # 12. Accumulated duty time (H:MM or HH:MM)
        if idx < len(fields):
            leg.duty_time = self.convert_time(fields[idx])
            idx += 1

        # 13. D/C (deadhead credit) - optional field, only present on some deadhead legs
        if idx < len(fields):
            field = fields[idx]
            # Check if it's a time format (H:MM, HH:MM, or decimal like .00)
            if ':' in field or '.' in field or field.replace('.', '').replace(':', '').isdigit():
                leg.d_c = self.convert_time(field)
                idx += 1

        # Any remaining fields before calendar dates are ignored
        # (calendar dates start after duty time)

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
            # Set layover_station values based on business rules
            self._set_layover_stations(self.current_pairing)

            self.current_bid_period.pairings.append(self.current_pairing)
            self.stats['pairings_parsed'] += 1
            self.logger.debug(f"Finalized pairing: {self.current_pairing.id}")
            self.current_pairing = None

    def _set_layover_stations(self, pairing):
        """Set layover_station values based on business rules.

        Rules:
        - 1-day trips: No layover stations (all None)
        - Multi-day trips: Layover for intermediate days only, None for last day
        """
        if not pairing.duty_periods:
            return

        num_days = len(pairing.duty_periods)

        # For 1-day trips, all layover_stations should be None
        if num_days == 1 or pairing.days == "1":
            for duty_period in pairing.duty_periods:
                duty_period.layover_station = None
            return

        # For multi-day trips:
        # - Set layover_station for intermediate duty periods (not the last one)
        # - Last duty period gets None (returning to base)
        for i, duty_period in enumerate(pairing.duty_periods):
            if i == num_days - 1:
                # Last duty period - no layover
                duty_period.layover_station = None
            else:
                # Intermediate duty period - set to arrival station of last leg
                if duty_period.legs and len(duty_period.legs) > 0:
                    duty_period.layover_station = duty_period.legs[-1].arrival_station
                else:
                    duty_period.layover_station = None

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
