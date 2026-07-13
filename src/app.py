import hashlib
import colorsys
import math
from typing import Dict, List, Optional, Tuple

import pygame

from src.graph import Graph

WINDOW_SIZE = (900, 600)
MARGIN = 60
NODE_RADIUS = 22
DRONE_RADIUS = 8
TURN_DURATION_MS = 900
BACKGROUND = (25, 25, 30)
EDGE_COLOR = (90, 90, 100)
TEXT_COLOR = (220, 220, 220)
DRONE_COLOR = (250, 250, 250)

_NAMED_COLORS: Dict[str, Tuple[int, int, int]] = {
    "black": (60, 60, 60),
    "white": (240, 240, 240),
    "gray": (140, 140, 140),
    "grey": (140, 140, 140),
    "red": (220, 60, 60),
    "green": (70, 170, 90),
    "blue": (80, 130, 220),
    "yellow": (230, 200, 60),
    "orange": (230, 140, 50),
    "purple": (150, 90, 190),
    "magenta": (210, 80, 170),
    "cyan": (80, 190, 210),
    "brown": (140, 100, 70),
}


def color_for(name: Optional[str]) -> Tuple[int, int, int]:
    """
    Turn a zone's `color` metadata into an RGB triple pygame can draw.
    """
    if not name:
        return (200, 200, 200)

    normalized = name.strip().lower()
    if normalized in _NAMED_COLORS:
        return _NAMED_COLORS[normalized]

    digest = hashlib.md5(normalized.encode("utf-8")).hexdigest()
    hue = (int(digest, 16) % 360) / 360
    r, g, b = colorsys.hls_to_rgb(hue, 0.55, 0.55)
    return (int(r * 255), int(g * 255), int(b * 255))


class SimulationApp:
    """Plays a completed Simulation's log back as an animated window."""

    def __init__(self, graph: Graph, log: List[str]) -> None:
        self.graph = graph
        self.log = log
        self.positions = self._layout_zones()
        self.snapshots = self._build_snapshots()
        self.turn = 0

    def _layout_zones(self) -> Dict[str, Tuple[int, int]]:
        """
        Scale each zone's real map (x, y) into pixel coordinates that
        fit the window, with a margin so nothing touches the edge.
        """
        xs = [z.x for z in self.graph.zones.values()]
        ys = [z.y for z in self.graph.zones.values()]
        x_span = max(max(xs) - min(xs), 1)
        y_span = max(max(ys) - min(ys), 1)
        usable_w = WINDOW_SIZE[0] - 2 * MARGIN
        usable_h = WINDOW_SIZE[1] - 2 * MARGIN

        positions = {}
        for name, zone in self.graph.zones.items():
            px = MARGIN + (zone.x - min(xs)) / x_span * usable_w
            py = MARGIN + (1 - (zone.y - min(ys)) / y_span) * usable_h
            positions[name] = (int(px), int(py))
        return positions

    def _build_snapshots(self) -> List[Dict[int, str]]:
        """
        Turn the plain-text log into one {drone_id: zone_name} dict
        per turn, so the render loop never parses strings mid-frame.
        """
        state: Dict[int, str] = {
            drone_id: self.graph.start
            for drone_id in range(1, self.graph.nb_drones + 1)
        }
        snapshots = [dict(state)]
        for line in self.log:
            for token in line.split(" ") if line else []:
                parts = token.split("-")
                drone_id = int(parts[0][1:])
                destination = parts[-1]
                state[drone_id] = destination
            snapshots.append(dict(state))
        return snapshots

    def _drone_positions(
        self, progress: float
    ) -> Dict[int, Tuple[float, float]]:
        """
        Where each drone should be drawn right now: a straight-line
        blend between its previous zone and its current one, `progress`
        (0 to 1) of the way through the current turn's duration.
        """
        previous = self.snapshots[max(self.turn - 1, 0)]
        current = self.snapshots[self.turn]
        positions: Dict[int, Tuple[float, float]] = {}
        for drone_id, zone_name in current.items():
            start = self.positions[previous.get(drone_id, zone_name)]
            end = self.positions[zone_name]
            x = start[0] + (end[0] - start[0]) * progress
            y = start[1] + (end[1] - start[1]) * progress
            positions[drone_id] = (x, y)
        return positions

    def _draw_connections(self, screen: pygame.Surface) -> None:
        drawn = set()
        for name, neighbors in self.graph.adjacency.items():
            for neighbor, _capacity in neighbors:
                key = tuple(sorted([name, neighbor]))
                if key in drawn:
                    continue
                drawn.add(key)
                pygame.draw.line(
                    screen, EDGE_COLOR,
                    self.positions[name], self.positions[neighbor], 2,
                )

    def _draw_zones(
        self, screen: pygame.Surface, font: pygame.font.Font
    ) -> None:
        for name, zone in self.graph.zones.items():
            pos = self.positions[name]
            pygame.draw.circle(screen, color_for(zone.color), pos, NODE_RADIUS)
            pygame.draw.circle(screen, BACKGROUND, pos, NODE_RADIUS, width=2)
            label = font.render(name, True, TEXT_COLOR)
            screen.blit(
                label,
                (pos[0] - label.get_width() // 2, pos[1] + NODE_RADIUS + 4),
            )

    def _draw_drones(self, screen: pygame.Surface, progress: float) -> None:
        groups: Dict[Tuple[int, int], List[int]] = {}
        for drone_id, (x, y) in self._drone_positions(progress).items():
            groups.setdefault((int(x), int(y)), []).append(drone_id)

        for (x, y), drone_ids in groups.items():
            spread = 0 if len(drone_ids) == 1 else 12
            for i, _drone_id in enumerate(drone_ids):
                angle = 2 * math.pi * i / len(drone_ids)
                dx = x + spread * math.cos(angle)
                dy = y + spread * math.sin(angle)
                pygame.draw.circle(screen, DRONE_COLOR, (dx, dy), DRONE_RADIUS)

    def _draw_turn_label(
        self, screen: pygame.Surface, font: pygame.font.Font
    ) -> None:
        text = f"Turn {self.turn} / {len(self.snapshots) - 1}"
        label = font.render(text, True, TEXT_COLOR)
        screen.blit(label, (10, 10))

    def run(self) -> None:
        pygame.init()
        screen = pygame.display.set_mode(WINDOW_SIZE)
        pygame.display.set_caption("Fly-In")
        clock = pygame.time.Clock()
        font = pygame.font.SysFont(None, 20)

        turn_started_at = pygame.time.get_ticks()
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                is_escape = (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_ESCAPE
                )
                if is_escape:
                    running = False

            elapsed = pygame.time.get_ticks() - turn_started_at
            progress = min(elapsed / TURN_DURATION_MS, 1.0)
            if progress >= 1.0 and self.turn < len(self.snapshots) - 1:
                self.turn += 1
                turn_started_at = pygame.time.get_ticks()
                progress = 0.0

            screen.fill(BACKGROUND)
            self._draw_connections(screen)
            self._draw_zones(screen, font)
            self._draw_drones(screen, progress)
            self._draw_turn_label(screen, font)

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()
