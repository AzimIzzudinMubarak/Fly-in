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

     # 2. Print Detailed Zone Data
    print("=== ZONES ===")
    print(f"{'Name':<20} | {'Type':<12} | {'Coords (X, Y)':<15} | {'Max Drones':<10} | {'Special':<12}")
    print("-" * 70)
    for zone in map_data.zones:
        # Determine if it's a special marker node
        special = "START" if zone.is_start else ("END" if zone.is_end else "Normal")
        coords = f"({zone.x}, {zone.y})"
        
        print(f"{zone.name:<20} | {zone.zone_type:<12} | {coords:<15} | {zone.max_drones:<10} | {special:<12}")

    print("\n")

    # 3. Print Detailed Connection Data
    print("=== CONNECTIONS ===")
    print(f"{'Zone A':<20} <---> {'Zone B':<20} | {'Link Capacity':<15}")
    print("-" * 65)
    for conn in map_data.connections:
        print(f"{conn.zone_a:<20} <---> {conn.zone_b:<20} | {conn.max_link_capacity:<15}")

if __name__ == "__main__":
    main()
