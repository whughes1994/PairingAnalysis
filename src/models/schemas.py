"""
Data models using Pydantic for validation and serialization.
"""
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, computed_field
from datetime import datetime


class Leg(BaseModel):
    """Individual flight leg."""
    equipment: Optional[str] = None
    deadhead: bool = False
    flight_number: Optional[str] = None
    departure_station: Optional[str] = None
    arrival_station: Optional[str] = None
    departure_time: Optional[str] = None  # Original HHMM format
    arrival_time: Optional[str] = None    # Original HHMM format
    ground_time: Optional[str] = "0"      # Original H:MM or HH:MM format
    meal_code: Optional[str] = None
    flight_time: Optional[str] = "0"      # Original H:MM or HH:MM format
    accumulated_flight_time: Optional[str] = "0"
    duty_time: Optional[str] = "0"
    d_c: Optional[str] = "0"

    @field_validator('ground_time', 'flight_time', 'accumulated_flight_time', 'duty_time', 'd_c')
    @classmethod
    def validate_time_format(cls, v):
        """Ensure time values are in HH:MM format or 0."""
        if v is None or v == "0" or v == ".00":
            return "0"
        return v

    @computed_field
    @property
    def departure_time_formatted(self) -> Optional[str]:
        """Convert HHMM to HH:MM format."""
        if not self.departure_time or len(self.departure_time) != 4:
            return None
        return f"{self.departure_time[:2]}:{self.departure_time[2:]}"

    @computed_field
    @property
    def arrival_time_formatted(self) -> Optional[str]:
        """Convert HHMM to HH:MM format."""
        if not self.arrival_time or len(self.arrival_time) != 4:
            return None
        return f"{self.arrival_time[:2]}:{self.arrival_time[2:]}"

    @computed_field
    @property
    def departure_time_minutes(self) -> Optional[int]:
        """Convert departure time to minutes since midnight."""
        if not self.departure_time or len(self.departure_time) != 4:
            return None
        try:
            hours = int(self.departure_time[:2])
            minutes = int(self.departure_time[2:])
            return hours * 60 + minutes
        except ValueError:
            return None

    @computed_field
    @property
    def arrival_time_minutes(self) -> Optional[int]:
        """Convert arrival time to minutes since midnight."""
        if not self.arrival_time or len(self.arrival_time) != 4:
            return None
        try:
            hours = int(self.arrival_time[:2])
            minutes = int(self.arrival_time[2:])
            return hours * 60 + minutes
        except ValueError:
            return None

    @computed_field
    @property
    def ground_time_minutes(self) -> int:
        """Convert ground time to total minutes."""
        return self._time_to_minutes(self.ground_time)

    @computed_field
    @property
    def flight_time_minutes(self) -> int:
        """Convert flight time to total minutes."""
        return self._time_to_minutes(self.flight_time)

    @computed_field
    @property
    def accumulated_flight_time_minutes(self) -> int:
        """Convert accumulated flight time to total minutes."""
        return self._time_to_minutes(self.accumulated_flight_time)

    @computed_field
    @property
    def duty_time_minutes(self) -> int:
        """Convert duty time to total minutes."""
        return self._time_to_minutes(self.duty_time)

    @computed_field
    @property
    def d_c_minutes(self) -> int:
        """Convert D/C time to total minutes."""
        return self._time_to_minutes(self.d_c)

    @staticmethod
    def _time_to_minutes(time_str: Optional[str]) -> int:
        """Convert H:MM or HH:MM format to total minutes."""
        if not time_str or time_str == "0":
            return 0
        try:
            if ':' in time_str:
                parts = time_str.split(':')
                hours = int(parts[0])
                minutes = int(parts[1])
                return hours * 60 + minutes
            return 0
        except (ValueError, IndexError):
            return 0


class DutyPeriod(BaseModel):
    """A duty period containing multiple legs."""
    report_time: Optional[str] = None  # Original HHMM format
    legs: List[Leg] = Field(default_factory=list)
    release_time: Optional[str] = None  # Original HHMM format
    hotel: Optional[str] = None
    hotel_phone: Optional[str] = None
    ground_transport: Optional[str] = None
    layover_station: Optional[str] = None  # Set by Pairing.model_post_init()

    @computed_field
    @property
    def report_time_formatted(self) -> Optional[str]:
        """Convert HHMM to HH:MM format."""
        if not self.report_time or len(self.report_time) != 4:
            return None
        return f"{self.report_time[:2]}:{self.report_time[2:]}"

    @computed_field
    @property
    def release_time_formatted(self) -> Optional[str]:
        """Convert HHMM to HH:MM format."""
        if not self.release_time or len(self.release_time) != 4:
            return None
        return f"{self.release_time[:2]}:{self.release_time[2:]}"

    @computed_field
    @property
    def report_time_minutes(self) -> Optional[int]:
        """Convert report time to minutes since midnight."""
        if not self.report_time or len(self.report_time) != 4:
            return None
        try:
            hours = int(self.report_time[:2])
            minutes = int(self.report_time[2:])
            return hours * 60 + minutes
        except ValueError:
            return None

    @computed_field
    @property
    def release_time_minutes(self) -> Optional[int]:
        """Convert release time to minutes since midnight."""
        if not self.release_time or len(self.release_time) != 4:
            return None
        try:
            hours = int(self.release_time[:2])
            minutes = int(self.release_time[2:])
            return hours * 60 + minutes
        except ValueError:
            return None

    @computed_field
    @property
    def origin_station(self) -> Optional[str]:
        """Get the origin station (first leg's departure station)."""
        if self.legs and len(self.legs) > 0:
            return self.legs[0].departure_station
        return None


class Pairing(BaseModel):
    """A complete pairing sequence."""
    id: Optional[str] = None
    pairing_category: Optional[str] = None
    is_first_officer: bool = False
    effective_date: Optional[str] = None  # Original MM/DD/YY format
    through_date: Optional[str] = None    # Original MM/DD/YY format
    date_instances: List[str] = Field(default_factory=list)
    duty_periods: List[DutyPeriod] = Field(default_factory=list)

    # Summary metrics (original H.MM or HH.MM format)
    days: Optional[str] = None
    credit: Optional[str] = None
    flight_time: Optional[str] = None
    time_away_from_base: Optional[str] = None
    international_flight_time: Optional[str] = None
    nte: Optional[str] = None
    meal_money: Optional[str] = None
    t_c: Optional[str] = None

    @computed_field
    @property
    def effective_date_iso(self) -> Optional[str]:
        """Convert MM/DD/YY to ISO 8601 format (YYYY-MM-DD)."""
        return self._parse_date_to_iso(self.effective_date)

    @computed_field
    @property
    def through_date_iso(self) -> Optional[str]:
        """Convert MM/DD/YY to ISO 8601 format (YYYY-MM-DD)."""
        return self._parse_date_to_iso(self.through_date)

    @computed_field
    @property
    def credit_minutes(self) -> int:
        """Convert credit (H.MM format) to total minutes."""
        return self._decimal_time_to_minutes(self.credit)

    @computed_field
    @property
    def flight_time_minutes(self) -> int:
        """Convert flight time (H.MM format) to total minutes."""
        return self._decimal_time_to_minutes(self.flight_time)

    @computed_field
    @property
    def time_away_from_base_minutes(self) -> int:
        """Convert time away from base (H.MM format) to total minutes."""
        return self._decimal_time_to_minutes(self.time_away_from_base)

    @computed_field
    @property
    def international_flight_time_minutes(self) -> int:
        """Convert international flight time (H.MM format) to total minutes."""
        return self._decimal_time_to_minutes(self.international_flight_time)

    @staticmethod
    def _parse_date_to_iso(date_str: Optional[str]) -> Optional[str]:
        """Convert MM/DD/YY to YYYY-MM-DD format."""
        if not date_str:
            return None
        try:
            # Parse MM/DD/YY format
            dt = datetime.strptime(date_str, "%m/%d/%y")
            return dt.strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def _decimal_time_to_minutes(time_str: Optional[str]) -> int:
        """Convert decimal time format (H.MM or HH.MM) to total minutes."""
        if not time_str:
            return 0
        try:
            # Format is H.MM or HH.MM where .MM represents minutes (not decimal)
            parts = time_str.split('.')
            if len(parts) == 2:
                hours = int(parts[0])
                minutes = int(parts[1])
                return hours * 60 + minutes
            return 0
        except (ValueError, IndexError, AttributeError):
            return 0


class BidPeriod(BaseModel):
    """A monthly bid period containing all pairings."""
    bid_month_year: Optional[str] = None
    fleet: Optional[str] = None
    base: Optional[str] = None
    effective_date: Optional[str] = None  # Original MM/DD/YY format
    through_date: Optional[str] = None    # Original MM/DD/YY format
    pairings: List[Pairing] = Field(default_factory=list)
    ftm: Optional[str] = None  # Total flight time (H,HHH:MM format)
    ttl: Optional[str] = None  # Total time (H,HHH:MM format)

    @computed_field
    @property
    def effective_date_iso(self) -> Optional[str]:
        """Convert MM/DD/YY to ISO 8601 format (YYYY-MM-DD)."""
        if not self.effective_date:
            return None
        try:
            dt = datetime.strptime(self.effective_date, "%m/%d/%y")
            return dt.strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            return None

    @computed_field
    @property
    def through_date_iso(self) -> Optional[str]:
        """Convert MM/DD/YY to ISO 8601 format (YYYY-MM-DD)."""
        if not self.through_date:
            return None
        try:
            dt = datetime.strptime(self.through_date, "%m/%d/%y")
            return dt.strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            return None

    @computed_field
    @property
    def ftm_minutes(self) -> int:
        """Convert total flight time (H,HHH:MM format) to total minutes."""
        return self._comma_time_to_minutes(self.ftm)

    @computed_field
    @property
    def ttl_minutes(self) -> int:
        """Convert total time (H,HHH:MM format) to total minutes."""
        return self._comma_time_to_minutes(self.ttl)

    @staticmethod
    def _comma_time_to_minutes(time_str: Optional[str]) -> int:
        """Convert comma-separated time format (H,HHH:MM) to total minutes."""
        if not time_str:
            return 0
        try:
            # Remove commas and parse HHH:MM
            clean_str = time_str.replace(',', '')
            if ':' in clean_str:
                parts = clean_str.split(':')
                hours = int(parts[0])
                minutes = int(parts[1])
                return hours * 60 + minutes
            return 0
        except (ValueError, IndexError, AttributeError):
            return 0


class MasterData(BaseModel):
    """Root container for all parsed data."""
    data: List[BidPeriod] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)

    def add_metadata(self, source_file: str, page_count: int, processing_time: float):
        """Add parsing metadata."""
        self.metadata = {
            "source_file": source_file,
            "page_count": page_count,
            "processing_time_seconds": round(processing_time, 2),
            "total_bid_periods": len(self.data),
            "total_pairings": sum(len(bp.pairings) for bp in self.data)
        }
