"""Bookkeeping of which zones and links are in use, turn by turn."""

from fly_in.models import Connection, DroneMap


class Reservations:
    """Remembers how many drones use each zone and each link per turn.

    Turn 0 is the starting situation and turn 1 is the first line of the
    output. The two kinds of use are counted differently:

    * a zone is used on turn t when a drone is inside it at the END of
      turn t;
    * a link is used on turn t when a drone STARTS to cross it during
      turn t (a drone that arrives on turn t has already left the link).

    The start and end zones have no limit.

    Args:
        drone_map: The network whose capacities are checked.
    """

    def __init__(self, drone_map: DroneMap) -> None:
        self._map = drone_map
        self._zone_use: dict[tuple[str, int], int] = {}
        self._link_use: dict[tuple[str, int], int] = {}

    def zone_use(self, zone: str, turn: int) -> int:
        """Return how many drones are in the zone at the end of a turn."""
        return self._zone_use.get((zone, turn), 0)

    def zone_has_room(self, zone: str, turn: int) -> bool:
        """Tell if one more drone fits in the zone at the end of a turn."""
        if zone in (self._map.start, self._map.end):
            return True
        return self.zone_use(zone, turn) < self._map.zones[zone].max_drones

    def link_has_room(self, connection: Connection, turn: int) -> bool:
        """Tell if one more drone may start crossing the link on a turn."""
        used = self._link_use.get((connection.name, turn), 0)
        return used < connection.max_link_capacity

    def reserve_zone(self, zone: str, turn: int) -> None:
        """Record one drone in the zone at the end of a turn.

        Raises:
            ValueError: If the zone is already full on that turn.
        """
        if not self.zone_has_room(zone, turn):
            raise ValueError(f"zone {zone} is full on turn {turn}")
        key = (zone, turn)
        self._zone_use[key] = self._zone_use.get(key, 0) + 1

    def reserve_link(self, connection: Connection, turn: int) -> None:
        """Record one drone starting to cross the link on a turn.

        Raises:
            ValueError: If the link is already full on that turn.
        """
        if not self.link_has_room(connection, turn):
            raise ValueError(f"link {connection.name} is full on turn {turn}")
        key = (connection.name, turn)
        self._link_use[key] = self._link_use.get(key, 0) + 1
