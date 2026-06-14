from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from src.graph import Graph
from src.pathfinder import find_k_shortest_paths


def _edge_label(a: str, b: str) -> str:
    return f"{a}-{b}"


def _edge_key(a: str, b: str) -> str:
    parts = sorted([a, b])
    return f"{parts[0]}-{parts[1]}"


@dataclass
class DroneState:
    drone_id: int
    path: List[str]
    path_index: int = 0
    transit_turns_left: int = 0
    transit_destination: str = ""
    transit_edge: str = ""
    delivered: bool = False

    @property
    def current_zone(self) -> str:
        return self.path[self.path_index]

    @property
    def next_zone(self) -> Optional[str]:
        if self.path_index + 1 < len(self.path):
            return self.path[self.path_index + 1]
        return None

    @property
    def in_transit(self) -> bool:
        return self.transit_turns_left > 0


class Simulation:
    def __init__(self, graph: Graph, k_paths: int = 3) -> None:
        self.graph = graph
        self.turn: int = 0
        self.log: List[str] = []

        paths = find_k_shortest_paths(graph, graph.start, graph.end, k_paths)
        if not paths:
            raise RuntimeError(
                f"No path found from '{graph.start}' to '{graph.end}'"
            )

        self.drones: List[DroneState] = []
        for i in range(graph.nb_drones):
            assigned_path = paths[i % len(paths)]
            self.drones.append(DroneState(
                drone_id=i + 1,
                path=assigned_path,
            ))

    def run(self) -> List[str]:
        while not self.finished:
            self.step()
        return self.log

    @property
    def finished(self) -> bool:
        return all(d.delivered for d in self.drones)

    def step(self) -> str:
        self.turn += 1

        zone_occupancy: Dict[str, List[int]] = {}
        edge_occupancy: Dict[str, int] = {}


        for d in self.drones:
            if not d.delivered and not d.in_transit:
                zone_occupancy.setdefault(d.current_zone, []).append(d.drone_id)

        movements: List[Tuple[int, str]] = []

        resolved_transit: set[int] = set()

        for d in self.drones:
            if d.delivered or not d.in_transit:
                continue
            d.transit_turns_left -= 1
            if d.transit_turns_left == 0:
                dest = d.transit_destination
                zone_occupancy.setdefault(dest, []).append(d.drone_id)
                d.path_index += 1
                movements.append((d.drone_id, dest))
                resolved_transit.add(d.drone_id)
                if dest == self.graph.end:
                    d.delivered = True

        for d in self.drones:
            if d.delivered or d.in_transit or d.drone_id in resolved_transit:
                continue

            next_zone = d.next_zone
            if next_zone is None:
                d.delivered = True
                continue

            cost = self.graph.movement_cost(next_zone)
            edge = _edge_label(d.current_zone, next_zone)
            edge_key = _edge_key(d.current_zone, next_zone)
            if next_zone != self.graph.end:
                zone = self.graph.zones[next_zone]
                current_count = len(zone_occupancy.get(next_zone, []))
                if current_count >= zone.max_drones:
                    continue

            edge_count = edge_occupancy.get(edge_key, 0)
            link_cap = next(
                cap for neighbor, cap in self.graph.adjacency[d.current_zone]
                if neighbor == next_zone
            )
            if edge_count >= link_cap:
                continue

            if d.current_zone in zone_occupancy:
                zone_occupancy[d.current_zone] = [
                    did for did in zone_occupancy[d.current_zone]
                    if did != d.drone_id
                ]

            edge_occupancy[edge_key] = edge_count + 1

            if cost == 1:
                zone_occupancy.setdefault(next_zone, []).append(d.drone_id)
                d.path_index += 1
                movements.append((d.drone_id, next_zone))
                if next_zone == self.graph.end:
                    d.delivered = True
            else:
                d.transit_turns_left = 1
                d.transit_destination = next_zone
                d.transit_edge = edge
                movements.append((d.drone_id, edge))

        movements.sort(key=lambda m: m[0])
        line = " ".join(f"D{did}-{label}" for did, label in movements)
        self.log.append(line)
        return line