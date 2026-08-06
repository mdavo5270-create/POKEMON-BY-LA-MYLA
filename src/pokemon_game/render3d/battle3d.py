"""Simple 3D battle arena + HUD using shared damage math."""
from __future__ import annotations
import random
import math
import time as pytime
from enum import Enum, auto
from ursina import Entity, Text, color, camera, destroy, Vec3, scene
from pokemon_game.entities.pokemon import Pokemon
from pokemon_game.systems.battle import calc_damage

class BattlePhase(Enum):
    INTRO = auto(); MENU = auto(); MOVES = auto()
    RESOLVE = auto(); ENEMY = auto(); END = auto()

class Battle3D:
    MENU = ["Attaquer", "Sac", "Fuir"]
    def __init__(self, game, player_mon: Pokemon, enemy: Pokemon, is_wild: bool = True):
        self.game, self.player_mon, self.enemy = game, player_mon, enemy
        self.is_wild, self.active = is_wild, True
        self.phase = BattlePhase.INTRO
        self.menu_i = self.move_i = self.msg_i = 0
        self.cooldown = 0.4
        self.messages = []
        self.result = None
        self.entities, self.hud = [], []
        self.messages = (
            [f"Un {enemy.dbSymbol} sauvage apparait !", f"En avant, {player_mon.dbSymbol} !"]
            if is_wild else [f"Adversaire envoie {enemy.dbSymbol} !"]
        )
        self._build_arena()

    def _build_arena(self) -> None:
        self.entities.append(Entity(model="plane", scale=(14, 1, 14),
            color=color.rgb(70, 110, 60), position=(0, 0, 0),
            texture="white_cube", texture_scale=(8, 8)))
        self.entities.append(Entity(model="circle", scale=6,
            color=color.rgba(255, 255, 255, 40), position=(0, 0.02, 0), rotation_x=90))
        self.player_ent = Entity(model="sphere", color=color.rgb(80, 180, 255),
            scale=1.4, position=(-3.2, 0.9, 1.5))
        self.enemy_ent = Entity(model="sphere", color=color.rgb(255, 100, 90),
            scale=1.4, position=(3.2, 0.9, -1.0))
        self.entities.extend([self.player_ent, self.enemy_ent])
        self.title = Text(text="COMBAT", position=(-0.1, 0.45), scale=1.4, background=True)
        self.log = Text(text=self.messages[0], position=(-0.8, -0.28), scale=1.0, background=True)
        self.menu_txt = Text(text="", position=(-0.8, -0.38), scale=0.95, background=True)
        self.hp_txt = Text(text=self._hp_line(), position=(-0.8, 0.38), scale=0.95, background=True)
        self.hud.extend([self.title, self.log, self.menu_txt, self.hp_txt])
        camera.parent = scene
        camera.position = (0, 6, -11)
        camera.rotation_x = 28
        camera.look_at(Vec3(0, 0.5, 0))

    def _hp_line(self) -> str:
        p, e = self.player_mon, self.enemy
        return f"TOI {p.dbSymbol} {p.hp}/{p.maxhp}  |  ENNEMI {e.dbSymbol} {e.hp}/{e.maxhp}"

    def destroy(self) -> None:
        for e in self.entities: destroy(e)
        for t in self.hud: destroy(t)
        self.entities.clear(); self.hud.clear()

    def update(self, dt: float) -> None:
        if not self.active: return
        if self.cooldown > 0: self.cooldown -= dt
        self.hp_txt.text = self._hp_line()
        t = pytime.time()
        self.player_ent.y = 0.9 + 0.05 * math.sin(t * 3)
        self.enemy_ent.y = 0.9 + 0.05 * math.sin(t * 3 + 1)

    def on_key(self, key: str) -> None:
        if not self.active or self.cooldown > 0: return
        conf = key in ("enter", "space", "e", "z")
        if self.phase == BattlePhase.INTRO:
            if conf:
                self.msg_i += 1
                if self.msg_i >= len(self.messages):
                    self.phase = BattlePhase.MENU; self._show_menu()
                else:
                    self.log.text = self.messages[self.msg_i]
                self.cooldown = 0.2
            return
        if self.phase == BattlePhase.MENU:
            if key in ("up arrow", "w"): self.menu_i = (self.menu_i - 1) % 3; self._show_menu()
            elif key in ("down arrow", "s"): self.menu_i = (self.menu_i + 1) % 3; self._show_menu()
            elif conf: self._menu_action()
            self.cooldown = 0.15; return
        if self.phase == BattlePhase.MOVES:
            moves = self.player_mon.moves or []
            n = max(len(moves), 1)
            if key in ("up arrow", "w"): self.move_i = (self.move_i - 1) % n; self._show_moves()
            elif key in ("down arrow", "s"): self.move_i = (self.move_i + 1) % n; self._show_moves()
            elif conf: self._do_player_attack()
            elif key in ("escape", "backspace"): self.phase = BattlePhase.MENU; self._show_menu()
            self.cooldown = 0.15; return
        if self.phase in (BattlePhase.RESOLVE, BattlePhase.ENEMY, BattlePhase.END) and conf:
            self._advance_resolve(); self.cooldown = 0.15

    def _show_menu(self) -> None:
        self.menu_txt.text = "  ".join(
            f"{'>' if i == self.menu_i else ' '} {o}" for i, o in enumerate(self.MENU)
        )
        self.log.text = "Que faire ?"

    def _show_moves(self) -> None:
        moves = self.player_mon.moves or []
        self.menu_txt.text = " | ".join(
            f"{'>' if i == self.move_i else ' '} {getattr(m,'name',None) or m.dbSymbol}"
            for i, m in enumerate(moves)
        ) or "Aucune capacite"
        self.log.text = "Capacite (Esc=retour)"

    def _menu_action(self) -> None:
        opt = self.MENU[self.menu_i]
        if opt == "Attaquer":
            if not self.player_mon.moves:
                self.messages = ["Pas de capacite !"]; self.msg_i = 0
                self.phase = BattlePhase.RESOLVE; self.log.text = self.messages[0]
            else:
                self.phase = BattlePhase.MOVES; self.move_i = 0; self._show_moves()
        elif opt == "Sac":
            if not self.is_wild:
                self.messages = ["Pas de capture contre un dresseur !"]
                self.phase = BattlePhase.RESOLVE
            elif random.random() < 0.45:
                self.messages = [f"Capture de {self.enemy.dbSymbol} !"]
                self.result = "caught"; self.phase = BattlePhase.END
            else:
                self.messages = ["La Ball a rate..."]; self.phase = BattlePhase.ENEMY
                self._enemy_turn()
            self.msg_i = 0; self.log.text = self.messages[0]; self.menu_txt.text = ""
        elif opt == "Fuir":
            if random.random() < 0.7:
                self.messages = ["Tu prends la fuite !"]; self.result = "ran"; self.phase = BattlePhase.END
            else:
                self.messages = ["Impossible de fuir !"]; self.phase = BattlePhase.ENEMY
                self._enemy_turn()
            self.msg_i = 0; self.log.text = self.messages[0]; self.menu_txt.text = ""

    def _do_player_attack(self) -> None:
        moves = self.player_mon.moves or []
        if not moves: return
        move = moves[self.move_i]
        dmg, mult, crit = calc_damage(self.player_mon, self.enemy, move)
        self.enemy.hp = max(0, self.enemy.hp - dmg)
        name = getattr(move, "name", None) or move.dbSymbol
        msg = f"{self.player_mon.dbSymbol} utilise {name} ! -> {dmg}"
        if crit: msg += " (CRIT)"
        if mult > 1: msg += " Super efficace!"
        elif 0 < mult < 1: msg += " Peu efficace..."
        self.messages = [msg]
        if self.enemy.hp <= 0:
            self.messages.append(f"{self.enemy.dbSymbol} est KO !")
            self.result = "win"; self.phase = BattlePhase.END
        else:
            self.phase = BattlePhase.ENEMY; self._enemy_turn()
        self.msg_i = 0; self.log.text = self.messages[0]; self.menu_txt.text = ""
        self.enemy_ent.x += 0.15

    def _enemy_turn(self) -> None:
        if self.enemy.hp <= 0: return
        moves = self.enemy.moves or []
        if not moves:
            self.messages.append(f"{self.enemy.dbSymbol} attend..."); self.phase = BattlePhase.RESOLVE; return
        move = random.choice(moves)
        dmg, _, _ = calc_damage(self.enemy, self.player_mon, move)
        self.player_mon.hp = max(0, self.player_mon.hp - dmg)
        name = getattr(move, "name", None) or move.dbSymbol
        self.messages.append(f"{self.enemy.dbSymbol} utilise {name} ! -> {dmg}")
        if self.player_mon.hp <= 0:
            self.messages.append(f"{self.player_mon.dbSymbol} est KO...")
            self.result = "lose"; self.phase = BattlePhase.END
        else:
            self.phase = BattlePhase.RESOLVE
        self.player_ent.x -= 0.15

    def _advance_resolve(self) -> None:
        self.msg_i += 1
        if self.msg_i < len(self.messages):
            self.log.text = self.messages[self.msg_i]; return
        if self.phase == BattlePhase.END or self.result:
            self.active = False
            self.game.end_battle(self.result or "win"); return
        self.messages = []; self.msg_i = 0
        self.phase = BattlePhase.MENU; self._show_menu()
