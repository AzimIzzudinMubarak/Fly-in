import sys

from src.parser import parse_arguments, parse_file


def main() -> None:

    args = parse_arguments()

    try:
        map_data = parse_file(args.map)
    except Exception as e:
        print(e)
        sys.exit(1)

    print(f"[DEBUG] Parsed map: {len(map_data.zones)} zones, "
          f"{len(map_data.connections)} connections, "
          f"{map_data.nb_drones} drones")


if __name__ == "__main__":
    main()
