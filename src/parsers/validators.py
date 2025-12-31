"""
Data validation utilities.
"""
from typing import List, Dict, Any
import logging
from ..models import Pairing, DutyPeriod, BidPeriod


class PairingValidator:
    """Validate parsed pairing data."""

    def __init__(self, strict_mode: bool = False):
        """
        Initialize validator.

        Args:
            strict_mode: If True, raise exceptions on validation errors
        """
        self.strict_mode = strict_mode
        self.logger = logging.getLogger(__name__)
        self.issues: List[str] = []

    def validate_pairing(self, pairing: Pairing) -> bool:
        """
        Validate a single pairing.

        Args:
            pairing: Pairing to validate

        Returns:
            True if valid, False otherwise
        """
        is_valid = True
        self.issues.clear()

        # Check required fields
        if not pairing.id:
            self.issues.append("Missing pairing ID")
            is_valid = False

        if not pairing.duty_periods:
            self.issues.append(f"Pairing {pairing.id} has no duty periods")
            is_valid = False

        # Validate duty periods
        for i, dp in enumerate(pairing.duty_periods):
            if not self._validate_duty_period(dp, i):
                is_valid = False

        # Validate metrics
        if not pairing.flight_time:
            self.issues.append(f"Pairing {pairing.id} missing flight time")
            is_valid = False

        if self.issues:
            for issue in self.issues:
                self.logger.warning(f"Validation issue: {issue}")

        if not is_valid and self.strict_mode:
            raise ValueError(f"Pairing validation failed: {', '.join(self.issues)}")

        return is_valid

    def _validate_duty_period(self, duty_period: DutyPeriod, index: int) -> bool:
        """Validate a duty period."""
        is_valid = True

        if not duty_period.report_time:
            self.issues.append(f"Duty period {index} missing report time")
            is_valid = False

        if not duty_period.release_time:
            self.issues.append(f"Duty period {index} missing release time")
            is_valid = False

        if not duty_period.legs:
            self.issues.append(f"Duty period {index} has no legs")
            is_valid = False

        return is_valid

    def validate_bid_period(self, bid_period: BidPeriod) -> bool:
        """
        Validate a bid period.

        Args:
            bid_period: Bid period to validate

        Returns:
            True if valid
        """
        is_valid = True

        if not bid_period.bid_month_year:
            self.logger.warning("Bid period missing month/year")
            is_valid = False

        if not bid_period.fleet:
            self.logger.warning("Bid period missing fleet")
            is_valid = False

        if not bid_period.base:
            self.logger.warning("Bid period missing base")
            is_valid = False

        # Validate all pairings
        for pairing in bid_period.pairings:
            if not self.validate_pairing(pairing):
                is_valid = False

        return is_valid

    def get_issues(self) -> List[str]:
        """Get list of validation issues."""
        return self.issues.copy()


class TimeValidator:
    """Validate time-related data."""

    @staticmethod
    def is_valid_time(time_str: str) -> bool:
        """
        Check if time string is valid HH:MM format.

        Args:
            time_str: Time string to validate

        Returns:
            True if valid
        """
        if not time_str or time_str == "0":
            return True

        if ':' not in time_str:
            return False

        parts = time_str.split(':')
        if len(parts) != 2:
            return False

        try:
            hours = int(parts[0])
            minutes = int(parts[1])
            return 0 <= hours <= 99 and 0 <= minutes <= 59
        except ValueError:
            return False

    @staticmethod
    def check_time_sequence(times: List[str]) -> bool:
        """
        Check if times are in sequential order.

        Args:
            times: List of time strings

        Returns:
            True if sequential
        """
        # Simplified check - in reality would need date context
        return True  # TODO: Implement proper time sequence checking
