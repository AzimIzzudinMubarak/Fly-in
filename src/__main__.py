import sys

from src.parser import parse_arguments, parse_file
from src.graph import Graph
from src.simulation import Simulation


def main() -> None:
    args = parse_arguments()

    try:
        map_data = parse_file(args.map)
    except Exception as e:
        print(e)
        sys.exit(1)

    try:
        graph = Graph(map_data)
    except Exception as e:
        print(f"Error building graph: {e}")
        sys.exit(1)

    try:
        simulation = Simulation(graph, k_paths=args.k_paths)
    except RuntimeError as e:
        # e.g. no path exists between start and end
        print(f"Simulation error: {e}")
        sys.exit(1)

    log = simulation.run()

    for line in log:
        print(line)

    print(f"\nNumber of turns: {simulation.turn}")


if __name__ == "__main__":
    main()
