"""Tests for the reservation table."""

import pytest

from fly_in.models import Connection, DroneMap
from fly_in.parser import MapParser
from fly_in.reservations import Reservations

TEXT = """\
nb_drones: 3
start_hub: a 0 0
hub: b 1 0 [max_drones=2]
hub: d 1 1
end_hub: c 2 0
connection: a-b [max_link_capacity=2]
connection: b-c
connection: a-d
"""


def build() -> tuple[DroneMap, Reservations]:
    """Return a small map and an empty reservation table for it."""
    drone_map = MapParser().parse_text(TEXT)
    return drone_map, Reservations(drone_map)


def link(drone_map: DroneMap, zone_a: str, zone_b: str) -> Connection:
    """Return the connection between two zones (it must exist)."""
    found = drone_map.connection_between(zone_a, zone_b)
    assert found is not None
    return found


def test_zone_capacity_is_counted_per_turn() -> None:
    """A zone with max_drones=2 accepts two drones, per turn."""
    _, reservations = build()
    reservations.reserve_zone("b", 1)
    assert reservations.zone_has_room("b", 1)
    reservations.reserve_zone("b", 1)
    assert not reservations.zone_has_room("b", 1)
    assert reservations.zone_has_room("b", 2)


def test_default_zone_holds_one_drone() -> None:
    """Without max_drones a zone holds a single drone."""
    _, reservations = build()
    reservations.reserve_zone("d", 3)
    assert not reservations.zone_has_room("d", 3)


def test_start_and_end_have_no_limit() -> None:
    """The start and the end zone accept any number of drones."""
    _, reservations = build()
    for _ in range(10):
        reservations.reserve_zone("a", 0)
        reservations.reserve_zone("c", 5)
    assert reservations.zone_has_room("a", 0)
    assert reservations.zone_use("c", 5) == 10


def test_link_capacity_is_counted_per_turn() -> None:
    """A link with max_link_capacity=1 allows one crossing per turn."""
    drone_map, reservations = build()
    connection = link(drone_map, "b", "c")
    reservations.reserve_link(connection, 2)
    assert not reservations.link_has_room(connection, 2)
    assert reservations.link_has_room(connection, 3)


def test_both_directions_share_the_link() -> None:
    """The same connection is found from both of its ends."""
    drone_map, _ = build()
    assert link(drone_map, "b", "c") is link(drone_map, "c", "b")


def test_reserving_a_full_zone_is_refused() -> None:
    """Reserving beyond the capacity is a bug and raises an error."""
    _, reservations = build()
    reservations.reserve_zone("d", 1)
    with pytest.raises(ValueError, match="full"):
        reservations.reserve_zone("d", 1)
