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
        "green": 34,
        "yellow": 226,
        "red": 196,
        "blue": 33,
        "orange": 208,
        "cyan": 51,
        "purple": 129,
        "magenta": 201,
        "gold": 220,
        "brown": 94,
        "maroon": 88,
        "darkred": 124,
        "crimson": 161,
        "violet": 135,
        "black": 240,
    }

    def code_for(self, color_name: Optional[str]) -> Optional[int]:
        """Return the xterm-256 code for a zone's color"""
        if not color_name:
            return None

        normalized = color_name.strip().lower()
        if normalized in self._NAMED_CODES:
            return self._NAMED_CODES[normalized]
        else:
            return None

    def colorize(self, text: str, color_name: Optional[str]) -> str:
        """Wrap `text` in the ANSI escape for `color_name`."""
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
    ) -> None:
        self.graph = graph
        self.palette = ColorPalette()
        self.enabled = self._color_enabled()

        self._rainbow_codes = [196, 208, 220, 34, 33, 129, 201]

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

    def _apply_rainbow_text(self, text: str) -> str:
        """Applies a character-by-character rainbow color sequence."""
        rainbow_chars = []
        for i, char in enumerate(text):
            if char.isspace():
                rainbow_chars.append(char)
                continue
            code = self._rainbow_codes[i % len(self._rainbow_codes)]
            rainbow_chars.append(f"\033[38;5;{code}m{char}")
        return "".join(rainbow_chars) + "\033[0m"

    def _render_zone(self, zone_name: str) -> str:
        if not self.enabled:
            return zone_name
        zone: Optional[ZoneData] = self.graph.zones.get(zone_name)
        color = zone.color if zone is not None else None

        if color == "rainbow":
            return self._apply_rainbow_text(zone_name)

        return self.palette.colorize(zone_name, color)

    def print_all_zones(self) -> None:
        """
        Print every zone once, colored, before the turn log.
        """
        print("Zones:")
        for name, zone in sorted(self.graph.zones.items()):
            label = f"{name} ({zone.zone_type})"
            if self.enabled:
                if zone.color == "rainbow":
                    label = self._apply_rainbow_text(label)
                label = self.palette.colorize(label, zone.color)
            print(f"  {label}")
        print()
