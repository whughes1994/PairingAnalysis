"""
Base parser class with core parsing logic.
"""
import re
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
import logging


class BaseParser(ABC):
    """Abstract base parser class."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize parser with configuration.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Compile regex patterns once
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile all regex patterns from config."""
        self.patterns = {}
        pattern_config = self.config.get('parser', {}).get('patterns', {})

        for name, pattern in pattern_config.items():
            try:
                self.patterns[name] = re.compile(pattern)
            except re.error as e:
                self.logger.warning(f"Invalid regex pattern '{name}': {e}")

    @abstractmethod
    def parse_line(self, line: str, line_number: int) -> Optional[Dict]:
        """
        Parse a single line.

        Args:
            line: Text line to parse
            line_number: Line number for error reporting

        Returns:
            Parsed data or None
        """
        pass

    @abstractmethod
    def finalize(self) -> Any:
        """
        Finalize parsing and return results.

        Returns:
            Complete parsed data structure
        """
        pass

    def extract_field(self, line: str, start: int, end: int, strip: bool = True) -> str:
        """
        Extract field from fixed-width line.

        Args:
            line: Source line
            start: Start column (0-indexed)
            end: End column (exclusive)
            strip: Whether to strip whitespace

        Returns:
            Extracted field value
        """
        if len(line) < end:
            return ""

        value = line[start:end]
        return value.strip() if strip else value

    def convert_time(self, time_str: str) -> str:
        """
        Convert time format from decimal to HH:MM.

        Args:
            time_str: Time string (e.g., "9.24" or ".00")

        Returns:
            Formatted time string
        """
        if not time_str or time_str == ".00":
            return "0"

        # Replace decimal point with colon for time format
        if '.' in time_str:
            return time_str.replace('.', ':')

        return time_str

    def is_leg_line(self, line: str) -> bool:
        """
        Detect if line contains leg data.

        Args:
            line: Text line to check

        Returns:
            True if line contains leg data
        """
        # Check if positions 0-2 contain equipment code (2 digits + letter)
        # Format: "78J 202 ORD OGG..."
        if len(line) < 3:
            return False

        return line[0:2].isdigit() and line[2].isalpha()

    def extract_report_time(self, line: str) -> Optional[str]:
        """Extract report time from line."""
        match = self.patterns.get('report_time', re.compile(r'RPT:\s*(\d+)')).search(line)
        return match.group(1) if match else None

    def extract_release_time(self, line: str) -> Optional[str]:
        """Extract release time from line."""
        match = self.patterns.get('release_time', re.compile(r'RLS:\s*(\d+)')).search(line)
        return match.group(1) if match else None

    def extract_hotel_info(self, line: str) -> Dict[str, Optional[str]]:
        """
        Extract hotel information from line.

        Returns:
            Dictionary with hotel name and phone
        """
        hotel_info = {'name': None, 'phone': None, 'operator_phone': None}

        if 'HTL:' not in line:
            return hotel_info

        # Extract hotel name and phone
        # Format: HTL: HOTEL NAME phone OP=> operator_phone
        hotel_match = re.search(r'HTL:\s*([A-Z\s]+?)\s+(\d[\d\-]+)', line)
        if hotel_match:
            hotel_info['name'] = hotel_match.group(1).strip()
            hotel_info['phone'] = hotel_match.group(2).strip()

        # Extract operator phone
        op_match = re.search(r'OP=>\s*([\d\-]+)', line)
        if op_match:
            hotel_info['operator_phone'] = op_match.group(1).strip()

        return hotel_info

    def extract_ground_transport(self, line: str) -> Optional[str]:
        """Extract ground transportation info."""
        # Look for common transport indicators
        transport_pattern = re.compile(
            r'(VIP|AIRLINE|CONNECT|TAXI|TOURING|HANATOURS|VIACAO|AUTOBUS)\s+[A-Z\s]+'
            r'\s*(\d[\d\-]+)',
            re.IGNORECASE
        )
        match = transport_pattern.search(line)
        return match.group(0).strip() if match else None
