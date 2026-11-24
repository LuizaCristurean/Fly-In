"""Tests for the map parser."""

import pytest

from fly_in.errors import ParseError
from fly_in.models import ZoneType
from fly_in.parser import MapParser

HEAD = "nb_drones: 1\nstart_hub: a 0 0\nend_hub: b 1 0\n"

VALID = """\
# a small map
nb_drones: 2
start_hub: a 0 0 [color=green]
hub: b 1 -1 [zone=restricted max_drones=3]
end_hub: c 2 0
connection: a-b [max_link_capacity=2]
connection: b-c
"""


def test_valid_map() -> None:
    """A correct file gives the expected zones and connections."""
    drone_map = MapParser().parse_text(VALID)
    assert drone_map.nb_drones == 2
    assert drone_map.start == "a"
    assert drone_map.end == "c"
    zone = drone_map.zones["b"]
    assert zone.zone_type is ZoneType.RESTRICTED
    assert (zone.x, zone.y, zone.max_drones) == (1, -1, 3)
    connection = drone_map.connection_between("b", "a")
    assert connection is not None
    assert connection.max_link_capacity == 2


def test_capacity_on_start_is_accepted() -> None:
    """max_drones on the start zone is ignored, not an error."""
    text = "nb_drones: 2\nstart_hub: a 0 0 [max_drones=5]\nend_hub: b 1 0\n"
    assert MapParser().parse_text(text).start == "a"


@pytest.mark.parametrize("text, message", [
    ("", "does not define nb_drones"),
    ("hub: a 0 0\n", "first line must define nb_drones"),
    (HEAD + "start_hub: c 2 0\n", "more than one start_hub"),
    (HEAD + "hub: c 2 0 [zone=fast]\n", "unknown zone type"),
    (HEAD + "connection: a-b [max_link_capacity=0]\n", "positive integer"),
    (HEAD + "hub: c-d 2 0\n", "dash"),
    (HEAD + "connection: a-b\nconnection: b-a\n", "duplicate connection"),
    (HEAD + "connection: a-z\n", "undefined zone"),
    ("nb_drones: 1\nstart_hub: a 0 0\n", "no end_hub"),
    (HEAD + "hub: c 0.5 0\n", "must be an integer"),
    (HEAD + "hub: c 2 0 [color=red\n", "invalid metadata block"),
])
def test_invalid_maps(text: str, message: str) -> None:
    """Each broken file raises a ParseError that explains the cause."""
    with pytest.raises(ParseError, match=message):
        MapParser().parse_text(text)


def test_error_tells_the_line() -> None:
    """The error knows the line where the problem is."""
    with pytest.raises(ParseError) as info:
        MapParser().parse_text(HEAD + "hub: c 2 0 [zone=fast]\n")
    assert info.value.line_number == 4


def test_missing_file() -> None:
    """A file that does not exist gives a clear error, not a crash."""
    with pytest.raises(ParseError, match="cannot read"):
        MapParser().parse_file("this_file_does_not_exist.txt")
