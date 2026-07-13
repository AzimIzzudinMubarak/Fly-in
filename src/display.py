import os
import sys
from typing import Dict, Optional

from src.graph import Graph
from src.models import ZoneData


class ColorPalette:
    """
    Maps a zone's `color` metadata to a terminal color.
    """

    _NAMED_CODES: Dict[str, int] = {
        "black": 240,
        "white": 255,
        "gray": 245,
        "grey": 245,
        "red": 196,
        "green": 34,
        "blue": 33,
        "yellow": 226,
        "orange": 208,
        "purple": 129,
        "magenta": 201,
        "cyan": 51,
        "brown": 94,
        "maroon": 88,
        "darkred": 124,
        "gold": 220,
        "crimson": 161,
        "violet": 135,
        "lime": 118,
        "pink": 213,
        "teal": 30,
        "tan": 180,
        "silver": 250,
    }

    def code_for(self, color_name: Optional[str]) -> Optional[int]:
        """Return the xterm-256 code for a zone's color, or None if
        no color was specified for that zone."""
        if not color_name:
            return None

        normalized = color_name.strip().lower()
        if normalized in self._NAMED_CODES:
            return self._NAMED_CODES[normalized]

    def colorize(self, text: str, color_name: Optional[str]) -> str:
        """Wrap `text` in the ANSI escape for `color_name`, if any."""
        code = self.code_for(color_name)
        if code is None:
            return text
        return f"\033[38;5;{code}m{text}\033[0m"


class SimulationRenderer:
    """
    Turns the plain-text turn log produced by Simulation into colored
    terminal output, and prints a one-time legend of zone colors.
    """

    def __init__(
        self,
        graph: Graph,
        palette: Optional[ColorPalette] = None,
    ) -> None:
        self.graph = graph
        self.palette = palette if palette is not None else ColorPalette()
        self.enabled = self._color_enabled()

    @staticmethod
    def _color_enabled() -> bool:
        if os.environ.get("NO_COLOR") is not None:
            return False
        return sys.stdout.isatty()

    def render_line(self, line: str) -> str:
        """Colorize one turn's log line, token by token."""
        if not line:
            return line
        return " ".join(
            self._render_token(token) for token in line.split(" ")
        )

    def _render_token(self, token: str) -> str:
        parts = token.split("-")
        drone_part, zone_parts = parts[0], parts[1:]
        colored_zones = [self._render_zone(name) for name in zone_parts]
        return "-".join([drone_part, *colored_zones])

    def _render_zone(self, zone_name: str) -> str:
        if not self.enabled:
            return zone_name
        zone: Optional[ZoneData] = self.graph.zones.get(zone_name)
        color = zone.color if zone is not None else None
        return self.palette.colorize(zone_name, color)

    def print_legend(self) -> None:
        """
        Print every zone once, colored, before the turn log.
        """
        print("Zone legend:")
        for name, zone in sorted(self.graph.zones.items()):
            label = f"{name} ({zone.zone_type})"
            if self.enabled:
                label = self.palette.colorize(label, zone.color)
            print(f"  {label}")
        print()
