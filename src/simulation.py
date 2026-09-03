from dataclasses import dataclass
from typing import Dict, List, Tuple

from src.graph import Graph
from src.pathfinder import compute_distances


def _edge_label(a: str, b: str) -> str:
    return f"{a}-{b}"


def _edge_key(a: str, b: str) -> str:
    parts = sorted([a, b])
    return f"{parts[0]}-{parts[1]}"


@dataclass
class DroneData:
    """
    Runtime state for a single drone.
    """
    drone_id: int
    current_zone: str
    transit_turns_left: int = 0
    transit_destination: str = ""
    transit_edge: str = ""
    delivered: bool = False

    def in_transit(self) -> bool:
        return self.transit_turns_left > 0


class Simulation:
    def __init__(self, graph: Graph) -> None:
        self.graph = graph
        self.turn: int = 0
        self.log: List[str] = []

        self.dist: Dict[str, float] = compute_distances(
            graph, graph.end
        )

        if self.dist[graph.start] == float("inf"):
            raise RuntimeError(
                f"No path found from '{graph.start}' to '{graph.end}'"
            )

        self.drones: List[DroneData] = [
            DroneData(drone_id=i + 1, current_zone=graph.start)
            for i in range(graph.nb_drones)
        ]

    def run(self) -> List[str]:
        """Run until all drones are delivered. Returns the turn log."""
        while not self.finished():
            self.step()
        return self.log

    def finished(self) -> bool:
        return all(d.delivered for d in self.drones)

    def _ranked_candidates(self, zone_name: str) -> List[Tuple[str, int]]:
        current_dist = self.dist[zone_name]
        candidates = [
            (neighbor, cap)
            for neighbor, cap in self.graph.adjacency[zone_name]
            if self.dist[neighbor] != float("inf")
            and self.dist[neighbor] < current_dist
        ]
        candidates.sort(key=lambda nc: self.dist[nc[0]])
        return candidates

    def step(self) -> str:
        self.turn += 1

        zone_occupancy: Dict[str, List[int]] = {}
        edge_occupancy: Dict[str, int] = {}

        for d in self.drones:
            if not d.delivered and not d.in_transit():
                if d.current_zone not in zone_occupancy:
                    zone_occupancy[d.current_zone] = []
                zone_occupancy[d.current_zone].append(d.drone_id)

        movements: List[Tuple[int, str]] = []
        resolved_transit: set[int] = set()

        # --- Phase 1: finish in-transit drones ---
        for d in self.drones:
            if d.delivered or not d.in_transit():
                continue
            d.transit_turns_left -= 1
            if d.transit_turns_left == 0:
                dest = d.transit_destination
                if dest not in zone_occupancy:
                    zone_occupancy[dest] = []
                zone_occupancy[dest].append(d.drone_id)
                d.current_zone = dest
                movements.append((d.drone_id, dest))
                resolved_transit.add(d.drone_id)
                if dest == self.graph.end:
                    d.delivered = True

        # --- Phase 2: grounded drones pick their next hop live ---
        for d in self.drones:
            already_resolved = d.drone_id in resolved_transit
            if d.delivered or d.in_transit() or already_resolved:
                continue

            if d.current_zone == self.graph.end:
                d.delivered = True
                continue

            candidates = self._ranked_candidates(d.current_zone)

            for next_zone, _ in candidates:
                cost = self.graph.movement_cost(next_zone)
                edge = _edge_label(d.current_zone, next_zone)
                edge_key = _edge_key(d.current_zone, next_zone)

                # Zone capacity check
                if next_zone != self.graph.end:
                    zone = self.graph.zones[next_zone]
                    zone_count = len(zone_occupancy.get(next_zone, []))
                    if zone_count >= zone.max_drones:
                        continue

                # Link capacity check
                edge_count = edge_occupancy.get(edge_key, 0)
                link_cap = next(
                    cap
                    for neighbor, cap in self.graph.adjacency[d.current_zone]
                    if neighbor == next_zone
                )
                if edge_count >= link_cap:
                    continue

                # This candidate works — commit the move.
                if d.current_zone in zone_occupancy:
                    zone_occupancy[d.current_zone] = [
                        droneid for droneid in zone_occupancy[d.current_zone]
                        if droneid != d.drone_id
                    ]
                edge_occupancy[edge_key] = edge_count + 1

                if next_zone not in zone_occupancy:
                    zone_occupancy[next_zone] = []
                zone_occupancy[next_zone].append(d.drone_id)

                if cost == 1:
                    d.current_zone = next_zone
                    movements.append((d.drone_id, next_zone))
                    if next_zone == self.graph.end:
                        d.delivered = True
                else:
                    d.transit_turns_left = 1
                    d.transit_destination = next_zone
                    d.transit_edge = edge
                    movements.append((d.drone_id, edge))

                break

        # print(f"\nTurn {self.turn}")

        # for name, zone in self.graph.zones.items():
        #     used = len(zone_occupancy.get(name, []))
        #     print(f"Zone {name}: {used}/{zone.max_drones} drones")
        # print()

        # seen = set()

        # for start, neighbors in self.graph.adjacency.items():
        #     for end, capacity in neighbors:
        #         key = tuple(sorted((start, end)))

        #         if key in seen:
        #             continue

        #         seen.add(key)

        #         edge_name = f"{key[0]}-{key[1]}"
        #         used = edge_occupancy.get(edge_name, 0)
        #         print(f"Connection {edge_name}: {used}/{capacity} "
        #               "capacity used")

        movements.sort(key=lambda m: m[0])
        line = " ".join(f"D{id}-{label}" for id, label in movements)
        self.log.append(line)
        return line
