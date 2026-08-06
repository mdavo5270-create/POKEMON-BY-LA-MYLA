"""3D game state - overworld + warps + battle + shared systems."""
from __future__ import annotations

import random

from ursina import Text, camera, time, held_keys

from pokemon_game.entities.pokemon import Pokemon
from pokemon_game.render3d.battle3d import Battle3D
from pokemon_game.render3d.map_builder import build_world_entities
from pokemon_game.systems.inventory import Inventory
from pokemon_game.systems.save_io import save_slot, load_slot


class Game3D:
    def __init__(self) -> None:
        self.world = None
        self.player = None
        self.tiles = []
        self.team = []
        self.inventory = Inventory.starter()
        self.status_text = None
        self.hint_text = None
        self.map_name = "map_0"
        self.battle = None
        self._warp_pads = []
        self._warp_cd = 0.0
        self._step_acc = 0.0
        self._load_or_create_team()

    def _load_or_create_team(self) -> None:
        blob = load_slot("save_3d")
        if blob and blob.get("team"):
            try:
                self.team = [Pokemon.from_dict(p) for p in blob["team"]]
                if blob.get("inventory"):
                    self.inventory = Inventory.from_dict(blob["inventory"])
                print(f"[3D] Equipe chargee ({len(self.team)})")
                return
            except Exception as e:
                print(f"[3D] Save illisible: {e}")
        choice = random.choice(["bulbasaur", "charmander", "squirtle"])
        self.team = [Pokemon.create_pokemon(choice, level=5)]
        print(f"[3D] Starter: {choice}")

    def build_map(self, map_name: str = "map_0", port: int = 0) -> None:
        build_world_entities(self, map_name, port=port)
        self._restore_overworld_camera()
        self._warp_cd = 0.8
        self._refresh_hud()

    def _restore_overworld_camera(self) -> None:
        if not self.player:
            return
        camera.parent = self.player.camera_pivot
        camera.position = (0, 2.5, -7)
        camera.rotation = (20, 0, 0)

    def _refresh_hud(self) -> None:
        if self.status_text and self.team:
            m = self.team[0]
            self.status_text.text = (
                f"POKEMON 3D | {self.map_name} | {m.dbSymbol} "
                f"Lv{m.level} | HP {m.hp}/{m.maxhp}"
            )
        if self.hint_text and not self.battle:
            self.hint_text.text = (
                "WASD: bouger | E: combat/warp | F5: save | F6: heal | Tab: map"
            )

    def update(self) -> None:
        dt = time.dt
        if self._warp_cd > 0:
            self._warp_cd -= dt
        if self.battle and self.battle.active:
            self.battle.update(dt)
            return
        if not self.player or not self.world:
            return
        moving = any(
            held_keys[k]
            for k in ("w", "a", "s", "d", "up arrow", "down arrow", "left arrow", "right arrow")
        )
        if moving and self.map_name.startswith("map"):
            self._step_acc += dt
            if self._step_acc > 2.5:
                self._step_acc = 0.0
                if random.random() < 0.12:
                    self.start_wild_battle()
        if self._warp_cd <= 0:
            gx, gy = self.world.world_to_grid(self.player.x, self.player.z)
            for winfo in self.world.warps:
                if winfo["gx"] == gx and winfo["gy"] == gy:
                    self.warp_to(winfo["target"], winfo["port"])
                    break

    def warp_to(self, target: str, port: int = 0) -> None:
        if self.battle and self.battle.active:
            return
        print(f"[3D] Warp -> {target} port={port}")
        if self.hint_text:
            self.hint_text.text = f"Transition vers {target}..."
        self.build_map(target, port=port)

    def interact(self) -> None:
        if self.battle and self.battle.active:
            return
        if self.player and self.world and self._warp_cd <= 0:
            gx, gy = self.world.world_to_grid(self.player.x, self.player.z)
            for winfo in self.world.warps:
                if abs(winfo["gx"] - gx) <= 1 and abs(winfo["gy"] - gy) <= 1:
                    self.warp_to(winfo["target"], winfo["port"])
                    return
        self.start_wild_battle()

    def start_wild_battle(self) -> None:
        if not self.team or (self.battle and self.battle.active):
            return
        if self.team[0].hp <= 0:
            if self.hint_text:
                self.hint_text.text = "Pokemon KO - F6 pour soigner"
            return
        names = ["rattata", "pidgey", "weedle", "caterpie", "zigzagoon"]
        name = random.choice(names)
        try:
            enemy = Pokemon.create_pokemon(name, level=max(2, self.team[0].level - 1))
        except Exception:
            enemy = Pokemon.create_pokemon("rattata", 3)
        if self.player:
            self.player.locked = True
            for t in self.tiles:
                t.visible = False
            self.player.visible = False
        self.battle = Battle3D(self, self.team[0], enemy, is_wild=True)
        if self.hint_text:
            self.hint_text.text = "Combat! Entree confirmer | Fleches menu"

    def end_battle(self, result: str) -> None:
        if self.battle:
            self.battle.destroy()
            self.battle = None
        if self.player:
            self.player.locked = False
            self.player.visible = True
        for t in self.tiles:
            t.visible = True
        self._restore_overworld_camera()
        if result == "win":
            self.team[0].xp = getattr(self.team[0], "xp", 0) + 8
            msg = "Victoire! +XP"
        elif result == "caught":
            msg = "Capture (prototype)"
        elif result == "ran":
            msg = "Fuite reussie"
        elif result == "lose":
            self.team[0].hp = max(1, self.team[0].maxhp // 2)
            msg = "Defaite... HP a moitie"
        else:
            msg = f"Fin combat ({result})"
        if self.hint_text:
            self.hint_text.text = msg
        self._refresh_hud()
        self._warp_cd = 0.5
        print(f"[3D] Fin combat: {result}")

    def heal_team(self) -> None:
        for m in self.team:
            m.hp = m.maxhp
            m.status = ""
        if self.hint_text:
            self.hint_text.text = "Equipe soignee!"
        self._refresh_hud()

    def save_game(self) -> None:
        class _FakePos:
            def __init__(self, x, y):
                self.x, self.y = x, y

        class _FakePlayer:
            def __init__(self, game):
                p = game.player
                self.position = _FakePos(p.x if p else 0, p.z if p else 0)
                self.on_bike = False
                self.team = game.team
                self.inventory = game.inventory

        class _FakeMap:
            def __init__(self, name):
                self.map_name = name
                self.current_map = None

        save_slot("save_3d", _FakePlayer(self), _FakeMap(self.map_name))
        print("[3D] Sauvegarde save_3d")
        if self.hint_text:
            self.hint_text.text = "Sauvegarde OK (save_3d)"
