import sys

from src.parser import parse_file
from src.graph import Graph
from src.simulation import Simulation
from src.display import SimulationRenderer


def main() -> None:
    print(
        "Choose map:\n"
        " Easy\n"
        "  1 - Linear Path\n"
        "  2 - Simple Fork\n"
        "  3 - Basic Capacity\n"
        " Medium\n"
        "  4 - Dead End Trap\n"
        "  5 - Circular Loop\n"
        "  6 - Priority Puzzle\n"
        " Hard\n"
        "  7 - Maze Nightmare\n"
        "  8 - Capacity Hell\n"
        "  9 - Ultimate Challange\n"
        " Challanger\n"
        "  0 - The Impossible Dream\n"
    )

    choice = input("Enter choice: ").strip().lower()

    match choice:
        case "1":
            selected_map = "maps/easy/01_linear_path.txt"
        case "2":
            selected_map = "maps/easy/02_simple_fork.txt"
        case "3":
            selected_map = "maps/easy/03_basic_capacity.txt"
        case "4":
            selected_map = "maps/medium/01_dead_end_trap.txt"
        case "5":
            selected_map = "maps/medium/02_circular_loop.txt"
        case "6":
            selected_map = "maps/medium/03_priority_puzzle.txt"
        case "7":
            selected_map = "maps/hard/01_maze_nightmare.txt"
        case "8":
            selected_map = "maps/hard/02_capacity_hell.txt"
        case "9":
            selected_map = "maps/hard/03_ultimate_challenge.txt"
        case "0":
            selected_map = "maps/challenger/01_the_impossible_dream.txt"
        case _:
            print("\nInvalid choice. Please choose a valid number.\n")
            sys.exit(0)

    try:
        map_data = parse_file(selected_map)
    except Exception as e:
        print(e)
        sys.exit(0)

    try:
        graph = Graph(map_data)
    except Exception as e:
        print(f"Error building graph: {e}")
        sys.exit(0)

    try:
        simulation = Simulation(graph)
    except RuntimeError as e:
        print(f"Simulation error: {e}")
        sys.exit(0)

    log = simulation.run()

    renderer = SimulationRenderer(graph)

    print("\n------------------------------\n")
    renderer.print_all_zones()
    print("Result: ")
    for line in log:
        print(renderer.render_line(line))

    print(f"\nNumber of turns: {len(log)}")
    print("------------------------------")

    # watch = input(
    #     "\nWatch this as an animated pygame window? (y/n): "
    # ).strip().lower()
    # if watch == "y":
    #     try:
    #         from src.app import SimulationApp
    #     except ImportError:
    #         print("pygame-ce isn't installed. Run: pip install pygame-ce")
    #     else:
    #         SimulationApp(graph, log).run()


if __name__ == "__main__":
    main()
