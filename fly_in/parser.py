"""Parser of the map files."""

import re
from typing import Optional

from fly_in.errors import ParseError
from fly_in.models import Connection, DroneMap, Zone, ZoneType

ZONE_KEYS = frozenset({"zone", "color", "max_drones"})
CONNECTION_KEYS = frozenset({"max_link_capacity"})
INTEGER = re.compile(r"-?[0-9]+")


class MapParser:
    """Reads a map file and builds a DroneMap.

    The parser stops at the first problem and raises a ParseError that
    tells the line and the cause.
    """

    def __init__(self) -> None:
        self._reset()

    def _reset(self) -> None:
        """Forget everything read so far, to start a new file."""
        self._nb_drones: Optional[int] = None
        self._zones: dict[str, Zone] = {}
        self._connections: list[Connection] = []
        self._link_keys: set[frozenset[str]] = set()
        self._start: Optional[str] = None
        self._end: Optional[str] = None

    def parse_file(self, path: str) -> DroneMap:
        """Read a map file and return the network it describes.

        Args:
            path: Path of the map file.

        Raises:
            ParseError: If the file cannot be read or is invalid.
        """
        try:
            with open(path, encoding="utf-8") as handle:
                text = handle.read()
        except OSError as error:
            reason = error.strerror or str(error)
            raise ParseError(f"cannot read '{path}': {reason}") from error
        except UnicodeDecodeError as error:
            raise ParseError(f"'{path}' is not a valid text file") from error
        return self.parse_text(text)

    def parse_text(self, text: str) -> DroneMap:
        """Parse the content of a map and return the network.

        Args:
            text: Whole content of the map file.

        Raises:
            ParseError: If the content is invalid.
        """
        self._reset()
        for number, raw in enumerate(text.splitlines(), start=1):
            line = raw.split("#", 1)[0].strip()
            if line:
                self._parse_line(line, number)
        return self._build()

    def _parse_line(self, line: str, number: int) -> None:
        """Send one meaningful line to the right method."""
        keyword, separator, value = line.partition(":")
        keyword = keyword.strip()
        value = value.strip()
        if not separator:
            raise ParseError("expected '<keyword>: <value>'", number)
        if self._nb_drones is None and keyword != "nb_drones":
            raise ParseError("the first line must define nb_drones", number)
        if keyword == "nb_drones":
            self._parse_nb_drones(value, number)
        elif keyword in ("start_hub", "end_hub", "hub"):
            self._parse_zone(keyword, value, number)
        elif keyword == "connection":
            self._parse_connection(value, number)
        else:
            raise ParseError(f"unknown keyword '{keyword}'", number)

    def _parse_nb_drones(self, value: str, number: int) -> None:
        """Handle the 'nb_drones' line."""
        if self._nb_drones is not None:
            raise ParseError("nb_drones is defined twice", number)
        self._nb_drones = self._positive_int(value, "nb_drones", number)

    def _parse_zone(self, keyword: str, value: str, number: int) -> None:
        """Handle a 'start_hub', 'end_hub' or 'hub' line."""
        head, meta = self._split_metadata(value, ZONE_KEYS, number)
        fields = head.split()
        if len(fields) != 3:
            raise ParseError("expected '<name> <x> <y> [metadata]'", number)
        name, x_text, y_text = fields
        if "-" in name:
            raise ParseError(
                f"zone name '{name}' must not contain a dash", number)
        if name in self._zones:
            raise ParseError(f"zone '{name}' is defined twice", number)
        zone = Zone(
            name=name,
            x=self._integer(x_text, "x coordinate", number),
            y=self._integer(y_text, "y coordinate", number),
            zone_type=self._zone_type(meta.get("zone", "normal"), number),
            color=meta.get("color"),
            max_drones=self._positive_int(
                meta.get("max_drones", "1"), "max_drones", number),
        )
        if keyword == "start_hub":
            if self._start is not None:
                raise ParseError("there is more than one start_hub", number)
            self._start = name
        elif keyword == "end_hub":
            if self._end is not None:
                raise ParseError("there is more than one end_hub", number)
            self._end = name
        self._zones[name] = zone

    def _parse_connection(self, value: str, number: int) -> None:
        """Handle a 'connection' line."""
        head, meta = self._split_metadata(value, CONNECTION_KEYS, number)
        names = head.split("-")
        if len(head.split()) != 1 or len(names) != 2 or not all(names):
            raise ParseError(
                f"invalid connection '{head}', expected '<zone1>-<zone2>' "
                "(zone names cannot contain dashes)", number)
        zone_a, zone_b = names
        for name in names:
            if name not in self._zones:
                raise ParseError(
                    f"connection uses the undefined zone '{name}'", number)
        if zone_a == zone_b:
            raise ParseError("a zone cannot be connected to itself", number)
        key = frozenset(names)
        if key in self._link_keys:
            raise ParseError(f"duplicate connection '{head}'", number)
        capacity = self._positive_int(
            meta.get("max_link_capacity", "1"), "max_link_capacity", number)
        self._link_keys.add(key)
        self._connections.append(Connection(zone_a, zone_b, capacity))

    def _build(self) -> DroneMap:
        """Check the file as a whole and build the DroneMap."""
        if self._nb_drones is None:
            raise ParseError("the file does not define nb_drones")
        if self._start is None:
            raise ParseError("there is no start_hub")
        if self._end is None:
            raise ParseError("there is no end_hub")
        for name in (self._start, self._end):
            if self._zones[name].zone_type is ZoneType.BLOCKED:
                raise ParseError(
                    f"zone '{name}' is blocked, but it is the start or "
                    "the end of the route")
        return DroneMap(self._nb_drones, self._zones, self._connections,
                        self._start, self._end)

    @staticmethod
    def _split_metadata(value: str, allowed: frozenset[str],
                        number: int) -> tuple[str, dict[str, str]]:
        """Separate the text before '[...]' from the key=value pairs."""
        if "[" not in value and "]" not in value:
            return value, {}
        opening = value.find("[")
        if (opening == -1 or not value.endswith("]")
                or value.count("[") != 1 or value.count("]") != 1):
            raise ParseError(
                "invalid metadata block, expected [key=value ...] "
                "at the end of the line", number)
        meta: dict[str, str] = {}
        for item in value[opening + 1:-1].split():
            key, separator, content = item.partition("=")
            if not separator or not key or not content or "=" in content:
                raise ParseError(
                    f"invalid metadata '{item}', expected key=value", number)
            if key not in allowed:
                raise ParseError(f"unknown metadata key '{key}'", number)
            if key in meta:
                raise ParseError(f"metadata key '{key}' repeated", number)
            meta[key] = content
        return value[:opening].strip(), meta

    @staticmethod
    def _integer(text: str, what: str, number: int) -> int:
        """Convert text to an integer (it may be negative)."""
        if not INTEGER.fullmatch(text):
            raise ParseError(
                f"{what} must be an integer, got '{text}'", number)
        return int(text)

    @staticmethod
    def _positive_int(text: str, what: str, number: int) -> int:
        """Convert text to an integer that is at least 1."""
        if not INTEGER.fullmatch(text) or int(text) < 1:
            raise ParseError(
                f"{what} must be a positive integer, got '{text}'", number)
        return int(text)

    @staticmethod
    def _zone_type(text: str, number: int) -> ZoneType:
        """Convert text to a ZoneType."""
        try:
            return ZoneType(text)
        except ValueError:
            raise ParseError(
                f"unknown zone type '{text}' "
                "(expected normal, blocked, restricted or priority)",
                number) from None
