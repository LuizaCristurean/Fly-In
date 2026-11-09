"""Data models describing a network of zones for the drones."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ZoneType(Enum):
    """Kind of a zone. It decides how much it costs to enter it."""

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"

    @property
    def move_cost(self) -> int:
        """Return the number of turns needed to enter this kind of zone.

        A blocked zone can never be entered; its cost is never used.
        """
        if self is ZoneType.RESTRICTED:
            return 2
        return 1


@dataclass(frozen=True)
class Zone:
    """A node of the network.

    Attributes:
        name: Unique name of the zone (no spaces, no dashes).
        x: Integer x coordinate.
        y: Integer y coordinate.
        zone_type: Kind of the zone.
        color: Optional single-word color used for display.
        max_drones: How many drones may be in the zone at the same time.
    """

    name: str
    x: int
    y: int
    zone_type: ZoneType = ZoneType.NORMAL
    color: Optional[str] = None
    max_drones: int = 1


@dataclass(frozen=True)
class Connection:
    """A bidirectional link between two zones.

    Attributes:
        zone_a: Name of one end.
        zone_b: Name of the other end.
        max_link_capacity: How many drones may use the link in one turn.
    """

    zone_a: str
    zone_b: str
    max_link_capacity: int = 1

    @property
    def name(self) -> str:
        """Return the name of the connection, as 'zone_a-zone_b'."""
        return f"{self.zone_a}-{self.zone_b}"

    def other_end(self, zone: str) -> str:
        """Return the zone at the opposite end of the connection.

        Args:
            zone: Name of one of the two ends.

        Raises:
            ValueError: If the zone is not an end of this connection.
        """
        if zone == self.zone_a:
            return self.zone_b
        if zone == self.zone_b:
            return self.zone_a
        raise ValueError(f"{zone} is not an end of {self.name}")


class DroneMap:
    """The whole network: zones, connections and the number of drones.

    Args:
        nb_drones: How many drones start in the start zone.
        zones: All the zones, by name.
        connections: All the connections.
        start: Name of the start zone.
        end: Name of the end zone.
    """

    def __init__(self, nb_drones: int, zones: dict[str, Zone],
                 connections: list[Connection],
                 start: str, end: str) -> None:
        self.nb_drones = nb_drones
        self.zones = zones
        self.connections = connections
        self.start = start
        self.end = end
        self._links: dict[str, list[Connection]] = {
            name: [] for name in zones
        }
        for connection in connections:
            self._links[connection.zone_a].append(connection)
            self._links[connection.zone_b].append(connection)

    def links_of(self, zone: str) -> list[Connection]:
        """Return the connections that touch the given zone."""
        return self._links[zone]

    def connection_between(self, zone_a: str,
                           zone_b: str) -> Optional[Connection]:
        """Return the connection joining two zones, or None if none."""
        for connection in self._links[zone_a]:
            if connection.other_end(zone_a) == zone_b:
                return connection
        return None
