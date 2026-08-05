"""Save system — JSON slot under <project>/saves/."""
from __future__ import annotations

import json

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
        """Load slot using centralized save_io; applies to player, inventory, team and pending map."""
        try:
            from pokemon_game.systems.save_io import load_slot

            blob = load_slot(self.slot)
            if not blob:
                return
            data = blob
            if self.player:
                if "x" in data and "y" in data:
                    try:
                        self.player.position.x = float(data["x"])
                        self.player.position.y = float(data["y"])
                    except Exception:
                        pass
                if data.get("on_bike") and hasattr(self.player, "switch_bike"):
                    try:
                        self.player.switch_bike(force=True)
                    except Exception:
                        pass
                # Team (si présente)
                if "team" in data and isinstance(data["team"], list):
                    try:
                        from pokemon_game.entities.pokemon import Pokemon

                        self.player.team = [
                            Pokemon.from_dict(p) for p in data["team"]
                        ]
                    except Exception as e:
                        print(f"[SAVE] Team non chargée: {e}")
                if "inventory" in data:
                    try:
                        from pokemon_game.systems.inventory import Inventory

                        self.player.inventory = Inventory.from_dict(data["inventory"])
                    except Exception as e:
                        print(f"[SAVE] Inventaire non chargé: {e}")
            # Map (rechargée après add_player dans Game)
            if "map" in data and self.map:
                setattr(self, "_pending_map", data["map"])
        except Exception as e:
            print(f"[SAVE] Load échoué: {e}")

    def save(self) -> None:
        """Save current slot using centralized save_io (atomic, backup, schema).

        Keeps previous dialogue feedback behaviour.
        """
        try:
            from pokemon_game.systems.save_io import save_slot

            # Delegate serialization and IO to save_io
            save_slot(self.slot, self.player, self.map, encrypt=False, password=None)
            print(f"[SAVE] Écrit → {getattr(self, 'path', self.slot)}")
            # Feedback dialogue si dispo
            if self.dialogue and not self.dialogue.active:
                try:
                    self.dialogue.load_data(100, 0)
                except Exception:
                    pass
        except Exception as e:
            print(f"[SAVE] Échec écriture: {e}")
