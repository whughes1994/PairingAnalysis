#!/usr/bin/env python3
"""Test layover_station logic for 1-day and multi-day trips."""

from src.models.schemas import Pairing, DutyPeriod, Leg


def test_1_day_trip():
    """Test that 1-day trips have no layover stations."""
    # Create a 1-day trip with 3 legs
    leg1 = Leg(
        equipment="73G",
        flight_number="123",
        departure_station="ORD",
        arrival_station="LAX",
        departure_time="0800",
        arrival_time="1030"
    )
    leg2 = Leg(
        equipment="73G",
        flight_number="456",
        departure_station="LAX",
        arrival_station="SFO",
        departure_time="1200",
        arrival_time="1330"
    )
    leg3 = Leg(
        equipment="73G",
        flight_number="789",
        departure_station="SFO",
        arrival_station="ORD",
        departure_time="1500",
        arrival_time="2100"
    )

    duty_period = DutyPeriod(
        report_time="0730",
        legs=[leg1, leg2, leg3],
        release_time="2130"
    )

    pairing = Pairing(
        id="TEST001",
        days="1",
        duty_periods=[duty_period]
    )

    # Check that layover_station is None for 1-day trip
    assert pairing.duty_periods[0].layover_station is None, \
        f"Expected None, got {pairing.duty_periods[0].layover_station}"

    print("✅ 1-day trip test PASSED: layover_station is None")


def test_4_day_trip():
    """Test that multi-day trips have layovers only for intermediate days."""
    # Day 1: ORD → LAX → SFO
    leg1_1 = Leg(equipment="73G", flight_number="101",
                 departure_station="ORD", arrival_station="LAX",
                 departure_time="0800", arrival_time="1030")
    leg1_2 = Leg(equipment="73G", flight_number="102",
                 departure_station="LAX", arrival_station="SFO",
                 departure_time="1200", arrival_time="1330")
    duty1 = DutyPeriod(report_time="0730", legs=[leg1_1, leg1_2], release_time="1400")

    # Day 2: SFO → SEA → PDX
    leg2_1 = Leg(equipment="73G", flight_number="201",
                 departure_station="SFO", arrival_station="SEA",
                 departure_time="0900", arrival_time="1100")
    leg2_2 = Leg(equipment="73G", flight_number="202",
                 departure_station="SEA", arrival_station="PDX",
                 departure_time="1230", arrival_time="1400")
    duty2 = DutyPeriod(report_time="0830", legs=[leg2_1, leg2_2], release_time="1430")

    # Day 3: PDX → DEN → PHX
    leg3_1 = Leg(equipment="73G", flight_number="301",
                 departure_station="PDX", arrival_station="DEN",
                 departure_time="0800", arrival_time="1200")
    leg3_2 = Leg(equipment="73G", flight_number="302",
                 departure_station="DEN", arrival_station="PHX",
                 departure_time="1400", arrival_time="1630")
    duty3 = DutyPeriod(report_time="0730", legs=[leg3_1, leg3_2], release_time="1700")

    # Day 4: PHX → DFW → ORD
    leg4_1 = Leg(equipment="73G", flight_number="401",
                 departure_station="PHX", arrival_station="DFW",
                 departure_time="0900", arrival_time="1300")
    leg4_2 = Leg(equipment="73G", flight_number="402",
                 departure_station="DFW", arrival_station="ORD",
                 departure_time="1500", arrival_time="1900")
    duty4 = DutyPeriod(report_time="0830", legs=[leg4_1, leg4_2], release_time="1930")

    # Create 4-day pairing
    pairing = Pairing(
        id="TEST002",
        days="4",
        duty_periods=[duty1, duty2, duty3, duty4]
    )

    # Verify layover logic
    assert pairing.duty_periods[0].layover_station == "SFO", \
        f"Day 1: Expected 'SFO', got {pairing.duty_periods[0].layover_station}"

    assert pairing.duty_periods[1].layover_station == "PDX", \
        f"Day 2: Expected 'PDX', got {pairing.duty_periods[1].layover_station}"

    assert pairing.duty_periods[2].layover_station == "PHX", \
        f"Day 3: Expected 'PHX', got {pairing.duty_periods[2].layover_station}"

    assert pairing.duty_periods[3].layover_station is None, \
        f"Day 4: Expected None, got {pairing.duty_periods[3].layover_station}"

    print("✅ 4-day trip test PASSED:")
    print(f"   Day 1 layover: {pairing.duty_periods[0].layover_station}")
    print(f"   Day 2 layover: {pairing.duty_periods[1].layover_station}")
    print(f"   Day 3 layover: {pairing.duty_periods[2].layover_station}")
    print(f"   Day 4 layover: {pairing.duty_periods[3].layover_station} (returning to base)")


def test_2_day_trip():
    """Test 2-day trip: Day 1 has layover, Day 2 has None."""
    # Day 1: ORD → LAX
    leg1 = Leg(equipment="73G", flight_number="101",
               departure_station="ORD", arrival_station="LAX",
               departure_time="0800", arrival_time="1030")
    duty1 = DutyPeriod(report_time="0730", legs=[leg1], release_time="1100")

    # Day 2: LAX → ORD
    leg2 = Leg(equipment="73G", flight_number="201",
               departure_station="LAX", arrival_station="ORD",
               departure_time="1200", arrival_time="1800")
    duty2 = DutyPeriod(report_time="1130", legs=[leg2], release_time="1830")

    pairing = Pairing(
        id="TEST003",
        days="2",
        duty_periods=[duty1, duty2]
    )

    assert pairing.duty_periods[0].layover_station == "LAX", \
        f"Day 1: Expected 'LAX', got {pairing.duty_periods[0].layover_station}"

    assert pairing.duty_periods[1].layover_station is None, \
        f"Day 2: Expected None, got {pairing.duty_periods[1].layover_station}"

    print("✅ 2-day trip test PASSED:")
    print(f"   Day 1 layover: {pairing.duty_periods[0].layover_station}")
    print(f"   Day 2 layover: {pairing.duty_periods[1].layover_station} (returning to base)")


if __name__ == "__main__":
    print("Testing layover_station logic...\n")

    test_1_day_trip()
    print()

    test_2_day_trip()
    print()

    test_4_day_trip()
    print()

    print("=" * 60)
    print("All layover_station logic tests PASSED! ✅")
    print("=" * 60)
