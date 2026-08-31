from typing import Dict

from src.graph import Graph


def compute_distances(graph: Graph, end: str) -> Dict[str, float]:
    dist: Dict[str, float] = {z: float("inf") for z in graph.zones}
    dist[end] = 0

    unvisited: set[str] = set(graph.zones)

    while unvisited:
        current = min(unvisited, key=lambda z: dist[z])

        if dist[current] == float("inf"):
            break

        unvisited.remove(current)

        for neighbor, _ in graph.adjacency[current]:
            if neighbor not in unvisited:
                continue

            cost = graph.pathfinding_weight(current)
            new_dist = dist[current] + cost
            if new_dist < dist[neighbor]:
                dist[neighbor] = new_dist

    return dist
