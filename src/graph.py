from typing import Dict, List, Tuple

from src.models import MapData, ZoneData


class Graph:
    def __init__(self, map_data: MapData) -> None:
        self.zones: Dict[str, ZoneData] = {
            z.name: z for z in map_data.zones
        }
        self.adjacency: Dict[str, List[Tuple[str, int]]] = {
            z.name: [] for z in map_data.zones
        }
        for conn in map_data.connections:
            capacity = conn.max_link_capacity
            self.adjacency[conn.zone_a].append((conn.zone_b, capacity))
            self.adjacency[conn.zone_b].append((conn.zone_a, capacity))

        self.start: str = next(z.name for z in map_data.zones if z.is_start)
        self.end: str = next(z.name for z in map_data.zones if z.is_end)
        self.nb_drones: int = map_data.nb_drones

    def movement_cost(self, destination: str) -> int:
        zone_type = self.zones[destination].zone_type
        if zone_type == "blocked":
            raise ValueError(
                "Cannot compute movement cost for blocked zone "
                f"'{destination}'"
            )
        if zone_type == "restricted":
            return 2
        return 1

    def pathfinding_weight(self, destination: str) -> float:
        if self.zones[destination].zone_type == "priority":
            return 0.99
        return self.movement_cost(destination)

    def neighbors(self, zone_name: str) -> List[Tuple[str, int]]:
        return [
            (neighbor, cap)
            for neighbor, cap in self.adjacency[zone_name]
            if self.zones[neighbor].zone_type != "blocked"
        ]
