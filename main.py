"""Entry point of the Fly-in drone simulation."""

import sys

from fly_in.errors import FlyInError
from fly_in.parser import MapParser


def main() -> int:
    """Read the map given on the command line and describe it.

    Returns:
        The exit code of the program: 0 on success, 1 on a map error and
        2 on a wrong command line.
    """
    if len(sys.argv) != 2:
        print("usage: python main.py <map_file>", file=sys.stderr)
        return 2
    try:
        drone_map = MapParser().parse_file(sys.argv[1])
    except FlyInError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"{drone_map.nb_drones} drones, {len(drone_map.zones)} zones, "
          f"{len(drone_map.connections)} connections")
    print(f"route: {drone_map.start} -> {drone_map.end}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
