"""
Unit tests for pairing parser.
"""
import pytest
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from parsers import PairingParser
from models import Pairing, Leg


def get_test_config():
    """Get minimal test configuration."""
    return {
        'processing': {'skip_on_error': True},
        'validation': {'enabled': False},
        'parser': {
            'leg_columns': {},
            'patterns': {
                'report_time': r'RPT:\s*(\d+)',
                'release_time': r'RLS:\s*(\d+)',
            }
        }
    }


class TestPairingParser:
    """Test pairing parser functionality."""

    def test_parser_initialization(self):
        """Test parser initializes correctly."""
        config = get_test_config()
        parser = PairingParser(config)
        assert parser is not None
        assert parser.stats['total_lines'] == 0

    def test_parse_header_line(self):
        """Test parsing header line."""
        config = get_test_config()
        parser = PairingParser(config)

        header_line = "EFF 12/30/25 THRU 01/29/26 787 CHICAGO JAN 2026 12/30/25 1DSL"
        parser.parse_line(header_line, 1)

        assert parser.current_bid_period is not None
        assert parser.current_bid_period.fleet == "787"

    def test_parse_leg_line(self):
        """Test parsing leg data."""
        config = get_test_config()
        parser = PairingParser(config)

        # Start duty period first
        parser.parse_line("RPT: 0820", 1)

        # Parse leg
        leg_line = "78J 202 ORD OGG 0920 1444 26.31 B S 9.24 9.24 10.39 .00"
        parser.parse_line(leg_line, 2)

        assert parser.current_duty_period is not None
        assert len(parser.current_duty_period.legs) == 1

        leg = parser.current_duty_period.legs[0]
        assert leg.equipment == "78J"
        assert leg.departure_station == "ORD"
        assert leg.arrival_station == "OGG"

    def test_time_conversion(self):
        """Test time format conversion."""
        config = get_test_config()
        parser = PairingParser(config)

        assert parser.convert_time("9.24") == "9:24"
        assert parser.convert_time(".00") == "0"
        assert parser.convert_time("") == "0"

    def test_is_leg_line(self):
        """Test leg line detection."""
        config = get_test_config()
        parser = PairingParser(config)

        # Valid leg line
        assert parser.is_leg_line("78J 202 ORD OGG 0920 1444") == True

        # Invalid leg line
        assert parser.is_leg_line("RPT: 0820") == False
        assert parser.is_leg_line("DAYS- 3") == False


class TestPairingModel:
    """Test pairing data models."""

    def test_leg_creation(self):
        """Test leg model creation."""
        leg = Leg(
            equipment="78J",
            flight_number="202",
            departure_station="ORD",
            arrival_station="OGG"
        )

        assert leg.equipment == "78J"
        assert leg.flight_number == "202"

    def test_pairing_creation(self):
        """Test pairing model creation."""
        pairing = Pairing(
            id="O8001",
            pairing_category="BASIC (HNL)"
        )

        assert pairing.id == "O8001"
        assert len(pairing.duty_periods) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
