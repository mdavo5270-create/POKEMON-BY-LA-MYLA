"""Système de combat tour par tour — logique + UI simple.

Formule de dégâts simplifiée (Gen 3+ allégée) :
  damage = ((2*L/5 + 2) * Power * A/D / 50 + 2) * STAB * Type * random(0.85–1.0)
"""
from __future__ import annotations

import random
from enum import Enum, auto
from typing import Callable

import pygame

from pokemon_game.core.tool import asset_path
from pokemon_game.entities.pokemon import Pokemon
from pokemon_game.entities.move import Move


# ── Table de types (efficacité) ─────────────────────────────────────
# Clé = type attaque, valeur = {type défense: multiplicateur}
TYPE_CHART: dict[str, dict[str, float]] = {
    "normal": {"rock": 0.5, "ghost": 0.0, "steel": 0.5},
    "fire": {
        "fire": 0.5, "water": 0.5, "grass": 2.0, "ice": 2.0,
        "bug": 2.0, "rock": 0.5, "dragon": 0.5, "steel": 2.0,
    },
    "water": {
        "fire": 2.0, "water": 0.5, "grass": 0.5, "ground": 2.0,
        "rock": 2.0, "dragon": 0.5,
    },
    "electric": {
        "water": 2.0, "electric": 0.5, "grass": 0.5, "ground": 0.0,
        "flying": 2.0, "dragon": 0.5,
    },
    "grass": {
        "fire": 0.5, "water": 2.0, "grass": 0.5, "poison": 0.5,
        "ground": 2.0, "flying": 0.5, "bug": 0.5, "rock": 2.0,
        "dragon": 0.5, "steel": 0.5,
    },
    "ice": {
        "fire": 0.5, "water": 0.5, "grass": 2.0, "ice": 0.5,
        "ground": 2.0, "flying": 2.0, "dragon": 2.0, "steel": 0.5,
    },
    "fighting": {
        "normal": 2.0, "ice": 2.0, "poison": 0.5, "flying": 0.5,
        "psychic": 0.5, "bug": 0.5, "rock": 2.0, "ghost": 0.0,
        "dark": 2.0, "steel": 2.0, "fairy": 0.5,
    },
    "poison": {
        "grass": 2.0, "poison": 0.5, "ground": 0.5, "rock": 0.5,
        "ghost": 0.5, "steel": 0.0, "fairy": 2.0,
    },
    "ground": {
        "fire": 2.0, "electric": 2.0, "grass": 0.5, "poison": 2.0,
        "flying": 0.0, "bug": 0.5, "rock": 2.0, "steel": 2.0,
    },
    "flying": {
        "electric": 0.5, "grass": 2.0, "fighting": 2.0, "bug": 2.0,
        "rock": 0.5, "steel": 0.5,
    },
    "psychic": {
        "fighting": 2.0, "poison": 2.0, "psychic": 0.5, "dark": 0.0,
        "steel": 0.5,
    },
    "bug": {
        "fire": 0.5, "grass": 2.0, "fighting": 0.5, "poison": 0.5,
        "flying": 0.5, "psychic": 2.0, "ghost": 0.5, "dark": 2.0,
        "steel": 0.5, "fairy": 0.5,
    },
    "rock": {
        "fire": 2.0, "ice": 2.0, "fighting": 0.5, "ground": 0.5,
        "flying": 2.0, "bug": 2.0, "steel": 0.5,
    },
    "ghost": {
        "normal": 0.0, "psychic": 2.0, "ghost": 2.0, "dark": 0.5,
    },
    "dragon": {"dragon": 2.0, "steel": 0.5, "fairy": 0.0},
    "dark": {
        "fighting": 0.5, "psychic": 2.0, "ghost": 2.0, "dark": 0.5,
        "fairy": 0.5,
    },
    "steel": {
        "fire": 0.5, "water": 0.5, "electric": 0.5, "ice": 2.0,
        "rock": 2.0, "steel": 0.5, "fairy": 2.0,
    },
    "fairy": {
        "fire": 0.5, "fighting": 2.0, "poison": 0.5, "dragon": 2.0,
        "dark": 2.0, "steel": 0.5,
    },
}


def type_effectiveness(move_type: str, defender_types: list[str]) -> float:
    chart = TYPE_CHART.get((move_type or "normal").lower(), {})
    mult = 1.0
    for t in defender_types or ["normal"]:
        mult *= chart.get(t.lower(), 1.0)
    return mult


def calc_damage(attacker: Pokemon, defender: Pokemon, move: Move) -> tuple[int, float, bool]:
    """Retourne (dégâts, multiplicateur_type, critique)."""
    power = move.power or 0
    if power <= 0:
        return 0, 1.0, False

    level = attacker.level
    category = (move.category or "physical").lower()
    if category in ("special", "s", "special_attack"):
        atk = max(1, attacker.ats)
        dfe = max(1, defender.dfs)
    else:
        atk = max(1, attacker.atk)
        dfe = max(1, defender.dfe)

    # STAB
    atk_types = [t.lower() for t in (attacker.type or [])]
    move_type = (move.type or "normal").lower()
    stab = 1.5 if move_type in atk_types else 1.0

    type_mult = type_effectiveness(move_type, attacker.type and defender.type or [])
    # fix: defender types
    type_mult = type_effectiveness(move_type, getattr(defender, "type", None) or ["normal"])

    crit = random.random() < 0.0625
    crit_mult = 1.5 if crit else 1.0
    rand = random.uniform(0.85, 1.0)

    base = ((2 * level / 5 + 2) * power * (atk / dfe)) / 50 + 2
    damage = int(base * stab * type_mult * crit_mult * rand)
    return max(1, damage) if type_mult > 0 else 0, type_mult, crit


class BattleState(Enum):
    INTRO = auto()
    MENU = auto()          # Attaquer / Fuir
    MOVES = auto()         # Choix de capacité
    RESOLVE = auto()       # Animation / messages
    ENEMY_TURN = auto()
    WIN = auto()
    LOSE = auto()
    RAN = auto()


class Battle:
    """Combat 1v1 joueur vs adversaire."""

    def __init__(
        self,
        screen,
        controller,
        keylistener,
        player_pokemon: Pokemon,
        enemy_pokemon: Pokemon,
        enemy_name: str = "Pokémon sauvage",
        can_run: bool = True,
        on_end: Callable[[str], None] | None = None,
    ) -> None:
        self.screen = screen
        self.controller = controller
        self.keylistener = keylistener
        self.player_mon = player_pokemon
        self.enemy_mon = enemy_pokemon
        self.enemy_name = enemy_name
        self.can_run = can_run
        self.on_end = on_end

        self.active = True
        self.state = BattleState.INTRO
        self.menu_index = 0  # 0 Attaquer, 1 Fuir
        self.move_index = 0
        self.messages: list[str] = []
        self._msg_index = 0
        self._cooldown = 15
        self._font: pygame.font.Font | None = None
        self._font_sm: pygame.font.Font | None = None
        self._load_fonts()

        # Intro
        self.messages = [
            f"{enemy_name} envoie {self._name(enemy_pokemon)} !",
            f"En avant, {self._name(player_pokemon)} !",
        ]
        self._msg_index = 0

    def _load_fonts(self) -> None:
        try:
            path = asset_path("fonts", "OakSans-Regular.ttf")
            self._font = pygame.font.Font(path, 22)
            self._font_sm = pygame.font.Font(path, 18)
        except Exception:
            self._font = pygame.font.SysFont(None, 24)
            self._font_sm = pygame.font.SysFont(None, 20)

    @staticmethod
    def _name(mon: Pokemon) -> str:
        return (getattr(mon, "dbSymbol", None) or "Pokémon").capitalize()

    def update(self) -> None:
        if not self.active:
            return
        if self._cooldown > 0:
            self._cooldown -= 1
        self._draw()
        if self._cooldown <= 0:
            self._handle_input()

    def _handle_input(self) -> None:
        kl = self.keylistener
        c = self.controller
        action = c.get_key("action")
        up = c.get_key("up")
        down = c.get_key("down")
        # flèches aussi
        up_pressed = kl.key_pressed(up) or kl.key_pressed(pygame.K_UP)
        down_pressed = kl.key_pressed(down) or kl.key_pressed(pygame.K_DOWN)
        action_pressed = kl.key_pressed(action) or kl.key_pressed(pygame.K_RETURN)

        if self.state in (BattleState.INTRO, BattleState.RESOLVE, BattleState.ENEMY_TURN):
            if action_pressed:
                kl.remove_key(action)
                if pygame.K_RETURN in kl.keys:
                    kl.remove_key(pygame.K_RETURN)
                self._advance_message()
            return

        if self.state == BattleState.MENU:
            if up_pressed:
                self.menu_index = (self.menu_index - 1) % 2
                kl.remove_key(up)
                if pygame.K_UP in kl.keys:
                    kl.remove_key(pygame.K_UP)
                self._cooldown = 8
            elif down_pressed:
                self.menu_index = (self.menu_index + 1) % 2
                kl.remove_key(down)
                if pygame.K_DOWN in kl.keys:
                    kl.remove_key(pygame.K_DOWN)
                self._cooldown = 8
            elif action_pressed:
                kl.remove_key(action)
                if self.menu_index == 0:
                    moves = self.player_mon.moves or []
                    if not moves:
                        self.messages = [f"{self._name(self.player_mon)} n'a aucune capacité !"]
                        self.state = BattleState.RESOLVE
                        self._msg_index = 0
                    else:
                        self.state = BattleState.MOVES
                        self.move_index = 0
                else:
                    if self.can_run:
                        self.messages = ["Tu prends la fuite !"]
                        self.state = BattleState.RAN
                        self._msg_index = 0
                    else:
                        self.messages = ["Impossible de fuir !"]
                        self.state = BattleState.RESOLVE
                        self._msg_index = 0
                self._cooldown = 10
            return

        if self.state == BattleState.MOVES:
            moves = self.player_mon.moves or []
            n = max(len(moves), 1)
            if up_pressed:
                self.move_index = (self.move_index - 1) % n
                kl.remove_key(up)
                if pygame.K_UP in kl.keys:
                    kl.remove_key(pygame.K_UP)
                self._cooldown = 8
            elif down_pressed:
                self.move_index = (self.move_index + 1) % n
                kl.remove_key(down)
                if pygame.K_DOWN in kl.keys:
                    kl.remove_key(pygame.K_DOWN)
                self._cooldown = 8
            elif action_pressed:
                kl.remove_key(action)
                move = moves[self.move_index]
                self._player_attack(move)
                self._cooldown = 10
            return

        if self.state in (BattleState.WIN, BattleState.LOSE, BattleState.RAN):
            if action_pressed:
                kl.remove_key(action)
                self._finish()

    def _advance_message(self) -> None:
        self._msg_index += 1
        if self._msg_index >= len(self.messages):
            if self.state == BattleState.INTRO:
                self.state = BattleState.MENU
                self.messages = []
            elif self.state == BattleState.RESOLVE:
                # après action joueur → tour ennemi si vivant
                if self.enemy_mon.hp <= 0:
                    self._on_win()
                elif self.player_mon.hp <= 0:
                    self._on_lose()
                else:
                    self._enemy_attack()
            elif self.state == BattleState.ENEMY_TURN:
                if self.player_mon.hp <= 0:
                    self._on_lose()
                elif self.enemy_mon.hp <= 0:
                    self._on_win()
                else:
                    self.state = BattleState.MENU
                    self.messages = []
            elif self.state in (BattleState.WIN, BattleState.LOSE, BattleState.RAN):
                self._finish()
            self._cooldown = 8

    def _player_attack(self, move: Move) -> None:
        # Accuracy
        acc = move.accuracy if move.accuracy not in (None, 0, -1) else 100
        msgs = [f"{self._name(self.player_mon)} utilise {move.dbSymbol} !"]
        if random.randint(1, 100) > acc:
            msgs.append("Mais l'attaque échoue !")
            self.messages = msgs
            self.state = BattleState.RESOLVE
            self._msg_index = 0
            return

        if move.pp is not None and move.pp <= 0:
            msgs.append("Plus de PP !")
            self.messages = msgs
            self.state = BattleState.RESOLVE
            self._msg_index = 0
            return

        if move.pp is not None:
            move.pp = max(0, move.pp - 1)

        dmg, type_m, crit = calc_damage(self.player_mon, self.enemy_mon, move)
        self.enemy_mon.hp = max(0, self.enemy_mon.hp - dmg)
        if dmg == 0 and type_m == 0:
            msgs.append("Ça n'affecte pas l'ennemi…")
        else:
            msgs.append(f"Ça inflige {dmg} PV !")
            if crit:
                msgs.append("Coup critique !")
            if type_m > 1:
                msgs.append("C'est super efficace !")
            elif 0 < type_m < 1:
                msgs.append("Ce n'est pas très efficace…")
        self.messages = msgs
        self.state = BattleState.RESOLVE
        self._msg_index = 0

    def _enemy_attack(self) -> None:
        moves = [m for m in (self.enemy_mon.moves or []) if (m.pp is None or m.pp > 0)]
        if not moves:
            moves = self.enemy_mon.moves or []
        if not moves:
            self.messages = [f"{self._name(self.enemy_mon)} ne peut rien faire !"]
            self.state = BattleState.ENEMY_TURN
            self._msg_index = 0
            return

        move = random.choice(moves)
        msgs = [f"{self._name(self.enemy_mon)} utilise {move.dbSymbol} !"]
        acc = move.accuracy if move.accuracy not in (None, 0, -1) else 100
        if random.randint(1, 100) > acc:
            msgs.append("Mais l'attaque échoue !")
            self.messages = msgs
            self.state = BattleState.ENEMY_TURN
            self._msg_index = 0
            return

        if move.pp is not None:
            move.pp = max(0, move.pp - 1)

        dmg, type_m, crit = calc_damage(self.enemy_mon, self.player_mon, move)
        self.player_mon.hp = max(0, self.player_mon.hp - dmg)
        if dmg == 0 and type_m == 0:
            msgs.append("Ça n'affecte pas…")
        else:
            msgs.append(f"Ça inflige {dmg} PV !")
            if crit:
                msgs.append("Coup critique !")
            if type_m > 1:
                msgs.append("C'est super efficace !")
            elif 0 < type_m < 1:
                msgs.append("Ce n'est pas très efficace…")
        self.messages = msgs
        self.state = BattleState.ENEMY_TURN
        self._msg_index = 0

    def _on_win(self) -> None:
        xp_gain = max(1, self.enemy_mon.level * 5)
        self.player_mon.xp = getattr(self.player_mon, "xp", 0) + xp_gain
        msgs = [
            f"{self._name(self.enemy_mon)} est K.O. !",
            f"{self._name(self.player_mon)} gagne {xp_gain} EXP !",
        ]
        # level up simple
        needed = getattr(self.player_mon, "xp_to_next_level", 0) or 0
        if needed and self.player_mon.xp >= needed and self.player_mon.level < 100:
            self.player_mon.level += 1
            self.player_mon.maxhp = self.player_mon.update_stats("hp")
            self.player_mon.hp = self.player_mon.maxhp
            self.player_mon.atk = self.player_mon.update_stats("atk")
            self.player_mon.dfe = self.player_mon.update_stats("dfe")
            self.player_mon.ats = self.player_mon.update_stats("ats")
            self.player_mon.dfs = self.player_mon.update_stats("dfs")
            self.player_mon.spd = self.player_mon.update_stats("spd")
            try:
                self.player_mon.xp_to_next_level = self.player_mon.compute_xp_to_next_level()
            except Exception:
                pass
            msgs.append(f"{self._name(self.player_mon)} monte au N.{self.player_mon.level} !")
        self.messages = msgs
        self.state = BattleState.WIN
        self._msg_index = 0

    def _on_lose(self) -> None:
        self.messages = [
            f"{self._name(self.player_mon)} est K.O. !",
            "Tu as perdu le combat…",
        ]
        self.state = BattleState.LOSE
        self._msg_index = 0

    def _finish(self) -> None:
        self.active = False
        result = "win" if self.state == BattleState.WIN else (
            "ran" if self.state == BattleState.RAN else "lose"
        )
        if self.on_end:
            self.on_end(result)

    # ── Rendu ───────────────────────────────────────────────────────
    def _draw(self) -> None:
        display = self.screen.get_display()
        if display is None:
            return
        w, h = display.get_size()

        # Fond combat
        overlay = pygame.Surface((w, h))
        overlay.fill((30, 50, 80))
        display.blit(overlay, (0, 0))

        # Zone ennemi (haut)
        self._draw_mon_panel(
            display, 40, 40, 400, 100,
            self.enemy_mon, self.enemy_name, enemy=True,
        )
        # Zone joueur (bas-gauche)
        self._draw_mon_panel(
            display, w - 440, h - 280, 400, 100,
            self.player_mon, "Toi", enemy=False,
        )

        # Boîte messages
        box_h = 140
        box = pygame.Surface((w - 80, box_h), pygame.SRCALPHA)
        box.fill((20, 25, 40, 240))
        pygame.draw.rect(box, (220, 220, 255), box.get_rect(), 3)
        display.blit(box, (40, h - box_h - 20))

        if self.messages and self._msg_index < len(self.messages):
            msg = self.messages[self._msg_index]
            self._blit_text(display, msg, 60, h - box_h, w - 120)
            hint = "E ▼"
            if self._font_sm:
                hs = self._font_sm.render(hint, True, (180, 180, 100))
                display.blit(hs, (w - 80, h - 50))
        elif self.state == BattleState.MENU:
            options = ["Attaquer", "Fuir" if self.can_run else "Fuir (impossible)"]
            for i, opt in enumerate(options):
                color = (255, 255, 100) if i == self.menu_index else (220, 220, 220)
                prefix = "▶ " if i == self.menu_index else "  "
                self._blit_text(display, f"{prefix}{opt}", 60, h - box_h + 10 + i * 36, w - 120, color)
        elif self.state == BattleState.MOVES:
            moves = self.player_mon.moves or []
            for i, m in enumerate(moves[:4]):
                color = (255, 255, 100) if i == self.move_index else (220, 220, 220)
                prefix = "▶ " if i == self.move_index else "  "
                pp = f"PP {m.pp}/{m.maxpp}" if m.maxpp else ""
                label = f"{prefix}{(m.dbSymbol or '?').upper()}  {pp}"
                self._blit_text(display, label, 60, h - box_h + 8 + i * 30, w - 120, color)

    def _draw_mon_panel(
        self, display, x, y, pw, ph, mon: Pokemon, label: str, enemy: bool
    ) -> None:
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((15, 20, 35, 220))
        pygame.draw.rect(panel, (100, 160, 220) if enemy else (100, 200, 120), panel.get_rect(), 2)
        display.blit(panel, (x, y))

        name = f"{self._name(mon)}  N.{mon.level}"
        if self._font:
            ns = self._font.render(name, True, (255, 255, 255))
            display.blit(ns, (x + 12, y + 10))
            ls = self._font_sm.render(label, True, (180, 180, 200)) if self._font_sm else None
            if ls:
                display.blit(ls, (x + 12, y + 36))

        # Barre HP
        maxhp = max(1, mon.maxhp)
        ratio = max(0.0, min(1.0, mon.hp / maxhp))
        bar_w, bar_h = pw - 40, 14
        bx, by = x + 20, y + ph - 30
        pygame.draw.rect(display, (40, 40, 40), (bx, by, bar_w, bar_h))
        color = (80, 200, 80) if ratio > 0.5 else ((220, 180, 40) if ratio > 0.2 else (220, 60, 60))
        pygame.draw.rect(display, color, (bx, by, int(bar_w * ratio), bar_h))
        if self._font_sm:
            hp_txt = self._font_sm.render(f"{mon.hp}/{mon.maxhp}", True, (230, 230, 230))
            display.blit(hp_txt, (bx, by - 18))

    def _blit_text(self, display, text, x, y, max_w, color=(240, 240, 240)) -> None:
        if not self._font:
            return
        # wrap simple
        words = text.split()
        lines, cur = [], ""
        for w in words:
            test = (cur + " " + w).strip()
            if self._font.size(test)[0] <= max_w:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        for i, line in enumerate(lines[:4]):
            surf = self._font.render(line, True, color)
            display.blit(surf, (x, y + i * 26))
