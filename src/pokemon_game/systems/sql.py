"""Map name helper."""
from __future__ import annotations


class SQL:
    def __init__(self) -> None:
        self.names = {
            "map_0": "Bourg Palette",
            "map_1": "Route 1",
            "pokecenter": "Centre Pokémon",
            "pokeshop": "Boutique",
        }

    def get_name_map(self, map_name: str) -> str:
        return self.names.get(map_name, map_name)
