"""Save system."""
from __future__ import annotations
import json
from pathlib import Path


class Save:
    def __init__(self, slot: str, map_obj, player, keylistener, dialogue) -> None:
        self.slot = slot
        self.map = map_obj
        self.player = player
        self.keylistener = keylistener
        self.dialogue = dialogue
        self.path = Path("saves") / f"{slot}.json"

    def load(self) -> None:
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                if self.player and "x" in data:
                    self.player.position.x = data["x"]
                    self.player.position.y = data["y"]
            except Exception:
                pass

    def save(self) -> None:
        self.path.parent.mkdir(exist_ok=True)
        data = {
            "x": getattr(self.player.position, "x", 0),
            "y": getattr(self.player.position, "y", 0),
            "map": getattr(self.map.current_map, "name", "map_0") if self.map.current_map else "map_0",
        }
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
