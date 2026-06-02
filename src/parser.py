import argparse
import re
from typing import Dict, Optional, Set, Tuple, List

from src.models import MapData, ZoneData, ConnectionData


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fly-In: Route drones from start to end in fewest turns.",
    )
    parser.add_argument(
        "--map",
        type=str,
        default="maps/challenger/01_the_impossible_dream.txt",
        help="Path to map description file."
    )
    return parser.parse_args()


_META_RE = re.compile(r"\[([^\]]*)\]")


def _parse_metadata(raw_meta: str, line_number: int) -> Dict[str, str]:
    result: Dict[str, str] = {}

    for meta_data in raw_meta.split():
        if "=" not in meta_data:
            raise ValueError(
                f"Line {line_number}: Invalid metadata token '{meta_data}' "
                f"(expected key=value)"
            )
        key, value = meta_data.split("=")
        if not key or not value:
            raise ValueError(
                f"Line {line_number}: Malformed metadata '{meta_data}'"
            )
        if key in result:
            raise ValueError(
                f"Line {line_number}: Duplicate metadata '{key}'"
            )

    return result


def _parse_zone(prefix: str, raw_val: str, line_number: int) -> ZoneData:
    meta_match = _META_RE.search(raw_val)
    metadata: Dict[str, str] = {}
    if meta_match:
        metadata = _parse_metadata(meta_match.group(1).strip(), line_number)
        raw_val = raw_val[: meta_match.start()].strip()

    zone_data = raw_val.split()
    if len(zone_data) != 3:
        raise ValueError(
            f"Line {line_number}: Expected '<name> <x> <y>' after '{prefix}:' "
            f"but got: '{raw_val}'"
        )
    name, x, y = zone_data

    if "-" in name:
        raise ValueError(
            f"Line {line_number}: Zone name '{name}' must not contain dashes"
        )

    zone_type = metadata.get("zone", "normal")
    if zone_type not in {"normal", "blocked", "restricted", "priority"}:
        raise ValueError(
            f"Line {line_number}: Unknown zone type '{zone_type}'"
        )

    color: Optional[str] = metadata.get("color", None)

    max_drones = int(metadata.get("max_drones", "1"))
    if max_drones < 1:
        raise ValueError(
            f"Line {line_number}: max_drones must be >= 1, got {max_drones}"
        )

    return ZoneData(
        name=name,
        x=int(x),
        y=int(y),
        zone_type=zone_type,
        color=color,
        max_drones=max_drones,
        is_start=(prefix == "start_hub"),
        is_end=(prefix == "end_hub"),
    )


def _parse_connection(raw_val: str, line_number: int) -> ConnectionData:
    meta_match = _META_RE.search(raw_val)
    metadata: Dict[str, str] = {}

    if meta_match:
        metadata = _parse_metadata(meta_match.group(1).strip(), line_number)
        raw_val = raw_val[: meta_match.start()].strip()

    dash_count = raw_val.count("-")
    if dash_count != 1:
        raise ValueError(
            f"Line {line_number}: Connection must be '<zone_a>-<zone_b>', "
            f"got '{raw_val}'"
        )

    zone_a, zone_b = raw_val.strip().split("-", 1)
    if not zone_a or not zone_b:
        raise ValueError(
            f"Line {line_number}: Empty zone name in connection '{raw_val}'"
        )

    capacity = int(metadata.get("max_link_capacity", "1"))
    if capacity < 1:
        raise ValueError(
            f"Line {line_number}: max_link_capacity must be >= 1, "
            f"got {capacity}"
        )

    return ConnectionData(
        zone_a=zone_a,
        zone_b=zone_b,
        max_link_capacity=capacity
    )


def parse_file(filepath: str) -> MapData:
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            raw_lines = file.readlines()
    except FileNotFoundError:
        raise FileNotFoundError("The file does not exist.")
    except OSError as e:
        raise OSError(f"System error reading file: {e}")

    nb_drones: int = 1
    zone_list: List[ZoneData] = []
    connection_list: List[ConnectionData] = []

    zone_names: Set[str] = set()
    seen_connection: Set[Tuple[str, str]] = set()

    nb_drones_seen = False
    start_seen = False
    end_seen = False

    for i, raw_line in enumerate(raw_lines, start=1):
        line = raw_line.strip()

        # Check comments
        if not line or line.startswith("#"):
            continue

        # Check nb_drones
        if line.startswith("nb_drones:"):
            if nb_drones_seen:
                raise ValueError(f"Line {i}: Duplicate nb_drones.")
            _, raw_val_nb_drones = line.split(":", 1)
            nb_drones = int(raw_val_nb_drones.strip())
            nb_drones_seen = True
            continue

        if not nb_drones_seen:
            raise ValueError("First line must be 'nb_drones: <number>'.")

        # Check hub
        if line.startswith(("start_hub:", "hub:", "end_hub:")):
            prefix, raw_val_hub = line.split(":", 1)

            if prefix == "start_hub":
                if start_seen:
                    raise ValueError(
                        f"Line {i}: More than one start_hub defined"
                    )
                start_seen = True

            if prefix == "end_hub":
                if end_seen:
                    raise ValueError(
                        f"Line {i}: More than one end_hub defined"
                    )
                end_seen = True

            zone = _parse_zone(prefix, raw_val_hub, i)

            if zone_names in zone_names:
                raise ValueError(
                    f"Line {i}: Duplicate zone name '{zone.name}'"
                )
            zone_names.add(zone.name)
            zone_list.append(zone)
            continue

        # Check connection
        if line.startswith("connection:"):
            _, raw_val_connection = line.split(":", 1)
            connection = _parse_connection(raw_val_connection, i)

            for zone_name in (connection.zone_a, connection.zone_b):
                if zone_name not in zone_names:
                    raise ValueError(
                        f"Line {i}: Connection references unknown "
                        f"zone '{zone_name}'"
                    )

            sorted_connection = sorted([connection.zone_a, connection.zone_b])
            conn: Tuple[str, str] = (sorted_connection[0], sorted_connection[1])

            if conn in seen_connection:
                raise ValueError(
                    f"Line {i}: Duplicate connection between "
                    f"'{connection.zone_a}' and '{connection.zone_b}'"
                )
            seen_connection.add(conn)

            connection_list.append(connection)
            continue

        raise ValueError(
            f"Line {i}: Unrecognised line format: '{line}'"
        )

    if not nb_drones_seen:
        raise ValueError("Map file is empty or missing nb_drones declaration")

    if not start_seen:
        raise ValueError("Map file has no start_hub")

    if not end_seen:
        raise ValueError("Map file has no end_hub")

    return MapData(
        nb_drones=nb_drones,
        zones=zone_list,
        connections=connection_list
    )
