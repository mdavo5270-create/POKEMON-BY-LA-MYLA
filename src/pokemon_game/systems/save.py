"""Save system — JSON slot under <project>/saves/."""
from __future__ import annotations

import json
from pathlib import Path

from pokemon_game.core.tool import ASSETS

# saves/ à la racine du projet (parent de assets/)
_SAVES_DIR = ASSETS.parent / "saves"


class Save:
    def __init__(self, slot: str, map_obj, player, keylistener, dialogue) -> None:
        self.slot = slot
        self.map = map_obj
        self.player = player
        self.keylistener = keylistener
        self.dialogue = dialogue
        self.path = _SAVES_DIR / f"{slot}.json"

    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if self.player:
                if "x" in data and "y" in data:
                    self.player.position.x = float(data["x"])
                    self.player.position.y = float(data["y"])
                if data.get("on_bike") and hasattr(self.player, "switch_bike"):
                    self.player.switch_bike(force=True)
                # Team (si présente)
                if "team" in data and isinstance(data["team"], list):
                    try:
                        from pokemon_game.entities.pokemon import Pokemon

                        self.player.team = [
                            Pokemon.from_dict(p) for p in data["team"]
                        ]
                    except Exception as e:
                        print(f"[SAVE] Team non chargée: {e}")
            # Map (rechargée après add_player dans Game)
            if "map" in data and self.map:
                setattr(self, "_pending_map", data["map"])
        except Exception as e:
            print(f"[SAVE] Load échoué: {e}")

    def save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            team_data = []
            if self.player and getattr(self.player, "team", None):
                team_data = [
                    p.to_dict() if hasattr(p, "to_dict") else p
                    for p in self.player.team
                ]
            data = {
                "x": float(getattr(self.player.position, "x", 0)),
                "y": float(getattr(self.player.position, "y", 0)),
                "map": (
                    getattr(self.map.current_map, "name", "map_0")
                    if self.map and self.map.current_map
                    else getattr(self.map, "map_name", "map_0") or "map_0"
                ),
                "on_bike": bool(getattr(self.player, "on_bike", False)),
                "team": team_data,
            }
            self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            print(f"[SAVE] Écrit → {self.path}")
            # Feedback dialogue si dispo
            if self.dialogue and not self.dialogue.active:
                self.dialogue.load_data(100, 0)
        except Exception as e:
            print(f"[SAVE] Échec écriture: {e}")
