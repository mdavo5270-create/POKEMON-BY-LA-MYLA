"""3D game state - overworld + shared gameplay systems."""
from __future__ import annotations

import random

from ursina import Entity, color, destroy, Text

from pokemon_game.core.tool import ASSETS
from pokemon_game.entities.pokemon import Pokemon
from pokemon_game.render3d.player3d import Player3D
from pokemon_game.render3d.world import WorldGrid, load_world_from_tmx
from pokemon_game.systems.inventory import Inventory
from pokemon_game.systems.save_io import save_slot, load_slot


class Game3D:
    """Orchestrates 3D overworld + retained systems (team, inv, save)."""

    def __init__(self) -> None:
        self.world: WorldGrid | None = None
        self.player: Player3D | None = None
        self.tiles: list[Entity] = []
        self.team: list[Pokemon] = []
        self.inventory = Inventory.starter()
        self.status_text: Text | None = None
        self.hint_text: Text | None = None
        self.map_name = "map_0"
        self._load_or_create_team()

    def _load_or_create_team(self) -> None:
        blob = load_slot("save_3d")
        if blob and blob.get("team"):
            try:
                self.team = [Pokemon.from_dict(p) for p in blob["team"]]
                if blob.get("inventory"):
                    self.inventory = Inventory.from_dict(blob["inventory"])
                print(f"[3D] Charge equipe ({len(self.team)}) depuis save_3d")
                return
            except Exception as e:
                print(f"[3D] Save illisible: {e}")
        starters = ["bulbasaur", "charmander", "squirtle"]
        choice = random.choice(starters)
        self.team = [Pokemon.create_pokemon(choice, level=5)]
        print(f"[3D] Starter: {choice}")

    def build_map(self, map_name: str = "map_0") -> None:
        for t in self.tiles:
            destroy(t)
        self.tiles.clear()
        if self.player:
            destroy(self.player)
            self.player = None

        path = ASSETS / "map" / f"{map_name}.tmx"
        if not path.exists():
            path = ASSETS / "map" / "map_0.tmx"
            map_name = "map_0"
        self.map_name = map_name
        self.world = load_world_from_tmx(path, map_name)

        ground = Entity(
            model="plane",
            scale=(
                self.world.width * self.world.tile_size,
                1,
                self.world.height * self.world.tile_size,
            ),
            color=color.rgb(60, 140, 70),
            texture="white_cube",
            texture_scale=(self.world.width, self.world.height),
            collider="box",
            position=(
                self.world.width * self.world.tile_size / 2,
                0,
                self.world.height * self.world.tile_size / 2,
            ),
        )
        self.tiles.append(ground)

        for gx, gy in self.world.blocked:
            wx, wz = self.world.grid_to_world(gx, gy)
            wall = Entity(
                model="cube",
                color=color.rgb(90, 90, 95),
                scale=(0.95, 1.2, 0.95),
                position=(wx, 0.6, wz),
                collider="box",
            )
            self.tiles.append(wall)

        for w in self.world.warps:
            wx, wz = self.world.grid_to_world(w["gx"], w["gy"])
            pad = Entity(
                model="cube",
                color=color.yellow,
                scale=(0.9, 0.08, 0.9),
                position=(wx, 0.05, wz),
            )
            self.tiles.append(pad)

        if self.world.spawns:
            sx, sz = next(iter(self.world.spawns.values()))
        else:
            sx, sz = self.world.grid_to_world(
                self.world.width // 2, self.world.height // 2
            )
        self.player = Player3D(self.world, position=(sx, 0.6, sz))
        self._refresh_hud()

    def _refresh_hud(self) -> None:
        if not self.status_text or not self.team:
            return
        m = self.team[0]
        self.status_text.text = (
            f"POKEMON 3D | {self.map_name} | {m.dbSymbol} "
            f"Lv{m.level} | HP {m.hp}/{m.maxhp}"
        )

    def save_game(self) -> None:
        class _FakePos:
            def __init__(self, x, y):
                self.x = x
                self.y = y

        class _FakePlayer:
            def __init__(self, game: "Game3D"):
                p = game.player
                self.position = _FakePos(p.x if p else 0, p.z if p else 0)
                self.on_bike = False
                self.team = game.team
                self.inventory = game.inventory

        class _FakeMap:
            def __init__(self, name: str):
                self.map_name = name
                self.current_map = None

        save_slot("save_3d", _FakePlayer(self), _FakeMap(self.map_name))
        print("[3D] Sauvegarde -> save_3d")
        if self.hint_text:
            self.hint_text.text = "Partie sauvegardee (save_3d)"

    def try_wild_battle(self) -> None:
        from pokemon_game.systems.battle import calc_damage

        if not self.team:
            return
        wild_names = ["rattata", "pidgey", "weedle", "caterpie", "zigzagoon"]
        name = random.choice(wild_names)
        try:
            enemy = Pokemon.create_pokemon(name, level=max(2, self.team[0].level - 1))
        except Exception:
            enemy = Pokemon.create_pokemon("rattata", 3)
        player = self.team[0]
        if not player.moves:
            print("[3D] Pas de moves - skip combat")
            return
        move = player.moves[0]
        dmg, mult, crit = calc_damage(player, enemy, move)
        enemy.hp = max(0, enemy.hp - dmg)
        msg = (
            f"Wild {name}! {player.dbSymbol} uses "
            f"{getattr(move, 'name', move.dbSymbol)} -> {dmg} dmg"
        )
        if crit:
            msg += " (CRIT)"
        if enemy.hp <= 0:
            msg += f" | {name} KO!"
            player.xp = getattr(player, "xp", 0) + 5
        elif enemy.moves:
            edmg, _, _ = calc_damage(enemy, player, enemy.moves[0])
            player.hp = max(0, player.hp - edmg)
            msg += f" | {name} hits {edmg}. HP {player.hp}/{player.maxhp}"
        print(f"[3D BATTLE] {msg}")
        if self.hint_text:
            self.hint_text.text = msg[:80]
        self._refresh_hud()
