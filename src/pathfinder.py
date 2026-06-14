import heapq
from typing import Dict, List, Optional

from src.graph import Graph


def find_shortest_path(graph: Graph, start: str, end: str) -> List[str]:
    dist: Dict[str, int] = {start: 0}
    prev: Dict[str, Optional[str]] = {start: None}
    heap: List[tuple[int, str]] = [(0, start)]

    while heap:
        current_cost, current = heapq.heappop(heap)
        if current_cost > dist.get(current, float("inf")):
            continue

        if current == end:
            break

        for neighbor, _link_cap in graph.neighbors(current):
            cost = graph.movement_cost(neighbor)
            new_dist = current_cost + cost
            if new_dist < dist.get(neighbor, float("inf")):
                dist[neighbor] = new_dist
                prev[neighbor] = current
                heapq.heappush(heap, (new_dist, neighbor))

    if end not in prev:
        return []

    path: List[str] = []
    node: Optional[str] = end
    while node is not None:
        path.append(node)
        node = prev[node]
    path.reverse()
    return path


def find_k_shortest_paths(graph: Graph, start: str, end: str, k: int = 3) -> List[List[str]]:
    if k < 1:
        raise ValueError("k must be >= 1")

    first = find_shortest_path(graph, start, end)
    if not first:
        return []

    a: List[List[str]] = [first]
    b: List[tuple[int, List[str]]] = []

    for _ in range(k - 1):
        prev_path = a[-1]

        for i in range(len(prev_path) - 1):
            spur_node = prev_path[i]
            root_path = prev_path[: i + 1]

            removed_edges: List[tuple[str, str]] = []
            for confirmed in a:
                if confirmed[: i + 1] == root_path and i + 1 < len(confirmed):
                    u = confirmed[i]
                    v = confirmed[i + 1]
                    graph.adjacency[u] = [
                        e for e in graph.adjacency[u] if e[0] != v
                    ]
                    graph.adjacency[v] = [
                        e for e in graph.adjacency[v] if e[0] != u
                    ]
                    removed_edges.append((u, v))

            removed_root_zones: Dict[str, List[tuple[str, int]]] = {}
            for root_node in root_path[:-1]:
                removed_root_zones[root_node] = graph.adjacency[root_node]
                graph.adjacency[root_node] = []

            spur_path = find_shortest_path(graph, spur_node, end)

            for u, v in removed_edges:
                original_cap = next(
                    (cap for name, cap in graph.adjacency[u] if name == v),
                    1
                )
                graph.adjacency[u].append((v, original_cap))
                graph.adjacency[v].append((u, original_cap))

            for root_node, edges in removed_root_zones.items():
                graph.adjacency[root_node] = edges

            if spur_path:
                total_path = root_path[:-1] + spur_path
                cost = sum(
                    graph.movement_cost(total_path[j + 1])
                    for j in range(len(total_path) - 1)
                )
                if (cost, total_path) not in [
                    (c, p) for c, p in b
                ]:
                    heapq.heappush(b, (cost, total_path))

        if not b:
            break

        _, next_path = heapq.heappop(b)
        a.append(next_path)

    return a
