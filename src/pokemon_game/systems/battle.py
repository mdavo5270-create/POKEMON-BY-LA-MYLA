"""Combat tour par tour : attaque, changement, capture, fuite."""
from __future__ import annotations

import random
from enum import Enum, auto
from typing import Callable

import pygame

from pokemon_game.core.tool import asset_path
from pokemon_game.entities.pokemon import Pokemon
from pokemon_game.entities.move import Move


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
    "ghost": {"normal": 0.0, "psychic": 2.0, "ghost": 2.0, "dark": 0.5},
    "dragon": {"dragon": 2.0, "steel": 0.5, "fairy": 0.0},
    "dark": {
        "fighting": 0.5, "psychic": 2.0, "ghost": 2.0, "dark": 0.5, "fairy": 0.5,
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
    atk_types = [t.lower() for t in (attacker.type or [])]
    move_type = (move.type or "normal").lower()
    stab = 1.5 if move_type in atk_types else 1.0
    type_mult = type_effectiveness(move_type, getattr(defender, "type", None) or ["normal"])
    crit = random.random() < 0.0625
    crit_mult = 1.5 if crit else 1.0
    rand = random.uniform(0.85, 1.0)
    base = ((2 * level / 5 + 2) * power * (atk / dfe)) / 50 + 2
    damage = int(base * stab * type_mult * crit_mult * rand)
    return max(1, damage) if type_mult > 0 else 0, type_mult, crit


def catch_rate(enemy: Pokemon, ball_mod: float = 1.0) -> float:
    """Probabilité de capture simplifiée (0–1)."""
    maxhp = max(1, enemy.maxhp)
    hp = max(0, enemy.hp)
    # Formule allégée : plus de PV restants = plus dur
    a = ((3 * maxhp - 2 * hp) * 45 * ball_mod) / (3 * maxhp)
    a = max(1.0, min(255.0, a))
    # 3 shake check approx → une seule proba
    return min(0.95, (a / 255.0) ** 0.75)


class BattleState(Enum):
    INTRO = auto()
    MENU = auto()
    MOVES = auto()
    PARTY = auto()
    BAG = auto()
    RESOLVE = auto()
    ENEMY_TURN = auto()
    WIN = auto()
    LOSE = auto()
    RAN = auto()
    CAUGHT = auto()


class Battle:
    """Combat 1v1 avec équipe, sac (balls) et capture."""

    MENU_OPTS = ["Attaquer", "Pokémon", "Sac", "Fuir"]

    def __init__(
        self,
        screen,
        controller,
        keylistener,
        player_pokemon: Pokemon,
        enemy_pokemon: Pokemon,
        enemy_name: str = "Pokémon sauvage",
        can_run: bool = True,
        is_wild: bool = False,
        team: list | None = None,
        inventory=None,
        on_end: Callable[[str], None] | None = None,
    ) -> None:
        self.screen = screen
        self.controller = controller
        self.keylistener = keylistener
        self.player_mon = player_pokemon
        self.enemy_mon = enemy_pokemon
        self.enemy_name = enemy_name
        self.can_run = can_run
        self.is_wild = is_wild
        self.team = team or [player_pokemon]
        self.inventory = inventory
        self.on_end = on_end

        self.active = True
        self.state = BattleState.INTRO
        self.menu_index = 0
        self.move_index = 0
        self.party_index = 0
        self.bag_index = 0
        self.messages: list[str] = []
        self._msg_index = 0
        self._cooldown = 12
        self._font = None
        self._font_sm = None
        self._load_fonts()

        if is_wild:
            self.messages = [
                f"Un {self._name(enemy_pokemon)} sauvage apparaît !",
                f"En avant, {self._name(player_pokemon)} !",
            ]
        else:
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

    def _alive_team(self) -> list:
        return [m for m in self.team if getattr(m, "hp", 0) > 0]

    def update(self) -> None:
        if not self.active:
            return
        if self._cooldown > 0:
            self._cooldown -= 1
        self._draw()
        if self._cooldown <= 0:
            self._handle_input()

    def _clear(self, *keys) -> None:
        for k in keys:
            if k in self.keylistener.keys:
                self.keylistener.remove_key(k)

    def _handle_input(self) -> None:
        kl = self.keylistener
        c = self.controller
        action_k = c.get_key("action")
        up_k = c.get_key("up")
        down_k = c.get_key("down")
        up = kl.key_pressed(up_k) or kl.key_pressed(pygame.K_UP)
        down = kl.key_pressed(down_k) or kl.key_pressed(pygame.K_DOWN)
        action = kl.key_pressed(action_k) or kl.key_pressed(pygame.K_RETURN)

        msg_states = (
            BattleState.INTRO, BattleState.RESOLVE, BattleState.ENEMY_TURN,
            BattleState.WIN, BattleState.LOSE, BattleState.RAN, BattleState.CAUGHT,
        )
        if self.state in msg_states:
            if action:
                self._clear(action_k, pygame.K_RETURN)
                self._advance_message()
            return

        if self.state == BattleState.MENU:
            n = len(self.MENU_OPTS)
            if up:
                self.menu_index = (self.menu_index - 1) % n
                self._clear(up_k, pygame.K_UP)
                self._cooldown = 8
            elif down:
                self.menu_index = (self.menu_index + 1) % n
                self._clear(down_k, pygame.K_DOWN)
                self._cooldown = 8
            elif action:
                self._clear(action_k, pygame.K_RETURN)
                self._menu_action()
                self._cooldown = 10
            return

        if self.state == BattleState.MOVES:
            moves = self.player_mon.moves or []
            n = max(len(moves), 1)
            if up:
                self.move_index = (self.move_index - 1) % n
                self._clear(up_k, pygame.K_UP)
                self._cooldown = 8
            elif down:
                self.move_index = (self.move_index + 1) % n
                self._clear(down_k, pygame.K_DOWN)
                self._cooldown = 8
            elif action and moves:
                self._clear(action_k, pygame.K_RETURN)
                self._player_attack(moves[self.move_index])
                self._cooldown = 10
            return

        if self.state == BattleState.PARTY:
            alive = self._alive_team()
            n = max(len(self.team), 1)
            if up:
                self.party_index = (self.party_index - 1) % n
                self._clear(up_k, pygame.K_UP)
                self._cooldown = 8
            elif down:
                self.party_index = (self.party_index + 1) % n
                self._clear(down_k, pygame.K_DOWN)
                self._cooldown = 8
            elif action:
                self._clear(action_k, pygame.K_RETURN)
                self._try_switch()
                self._cooldown = 10
            return

        if self.state == BattleState.BAG:
            balls = self._ball_list()
            n = max(len(balls), 1)
            if up:
                self.bag_index = (self.bag_index - 1) % n
                self._clear(up_k, pygame.K_UP)
                self._cooldown = 8
            elif down:
                self.bag_index = (self.bag_index + 1) % n
                self._clear(down_k, pygame.K_DOWN)
                self._cooldown = 8
            elif action:
                self._clear(action_k, pygame.K_RETURN)
                if balls:
                    self._try_catch(balls[self.bag_index][0])
                else:
                    self.messages = ["Pas de Ball dans le sac !"]
                    self.state = BattleState.RESOLVE
                    self._msg_index = 0
                self._cooldown = 10
            return

    def _menu_action(self) -> None:
        opt = self.MENU_OPTS[self.menu_index]
        if opt == "Attaquer":
            moves = self.player_mon.moves or []
            if not moves:
                self.messages = [f"{self._name(self.player_mon)} n'a aucune capacité !"]
                self.state = BattleState.RESOLVE
                self._msg_index = 0
            else:
                self.state = BattleState.MOVES
                self.move_index = 0
        elif opt == "Pokémon":
            if len(self.team) <= 1:
                self.messages = ["Tu n'as qu'un seul Pokémon !"]
                self.state = BattleState.RESOLVE
                self._msg_index = 0
            else:
                self.state = BattleState.PARTY
                self.party_index = 0
        elif opt == "Sac":
            if not self.is_wild:
                self.messages = ["On ne capture pas le Pokémon d'un dresseur !"]
                self.state = BattleState.RESOLVE
                self._msg_index = 0
            else:
                self.state = BattleState.BAG
                self.bag_index = 0
        elif opt == "Fuir":
            if self.can_run:
                # Fuite basée sur vitesse
                if random.random() < 0.75 or self.player_mon.spd >= self.enemy_mon.spd:
                    self.messages = ["Tu prends la fuite !"]
                    self.state = BattleState.RAN
                else:
                    self.messages = ["Impossible de fuir !"]
                    self.state = BattleState.RESOLVE
                self._msg_index = 0
            else:
                self.messages = ["Impossible de fuir !"]
                self.state = BattleState.RESOLVE
                self._msg_index = 0

    def _ball_list(self) -> list[tuple[str, int]]:
        if not self.inventory:
            return []
        out = []
        for bid in ("pokeball", "great_ball"):
            q = self.inventory.count(bid)
            if q > 0:
                out.append((bid, q))
        return out

    def _try_catch(self, ball_id: str) -> None:
        if not self.inventory or self.inventory.count(ball_id) <= 0:
            self.messages = ["Plus de Ball !"]
            self.state = BattleState.RESOLVE
            self._msg_index = 0
            return
        self.inventory.remove(ball_id, 1)
        ball_mod = 1.5 if ball_id == "great_ball" else 1.0
        ball_name = "Super Ball" if ball_id == "great_ball" else "Poké Ball"
        rate = catch_rate(self.enemy_mon, ball_mod)
        msgs = [f"Tu lances une {ball_name} !"]
        if random.random() < rate:
            msgs.append(f"Gotcha ! {self._name(self.enemy_mon)} a été capturé !")
            # Ajouter à l'équipe si place
            if len(self.team) < 6:
                self.team.append(self.enemy_mon)
                msgs.append(f"{self._name(self.enemy_mon)} rejoint l'équipe !")
            else:
                msgs.append("Équipe pleine — le Pokémon est envoyé au PC (simulation).")
            self.messages = msgs
            self.state = BattleState.CAUGHT
            self._msg_index = 0
        else:
            msgs.append("Le Pokémon s'est libéré !")
            self.messages = msgs
            self.state = BattleState.RESOLVE
            self._msg_index = 0

    def _after_player_faint(self) -> None:
        alive = self._alive_team()
        if not alive:
            self._on_lose()
            return
        # Force switch
        self.messages = [
            f"{self._name(self.player_mon)} est K.O. !",
            "Choisis un autre Pokémon.",
        ]
        self.state = BattleState.PARTY
        self.party_index = 0
        self._msg_index = 0
        # After party select, _try_switch will set RESOLVE with _switched
        # but if forced, skip enemy turn after switch: handle by not setting _switched for forced?
        # Actually after KO, enemy already acted - so switch should go to MENU not enemy turn
        self._force_switch = True

    def _try_switch(self) -> None:
        mon = self.team[self.party_index]
        if mon is self.player_mon and not getattr(self, "_force_switch", False):
            self.messages = [f"{self._name(mon)} combat déjà !"]
            self.state = BattleState.RESOLVE
            self._msg_index = 0
            return
        if mon.hp <= 0:
            self.messages = [f"{self._name(mon)} est K.O. !"]
            # stay in party if force
            if not getattr(self, "_force_switch", False):
                self.state = BattleState.RESOLVE
                self._msg_index = 0
            return
        old = self._name(self.player_mon)
        self.player_mon = mon
        self.messages = [f"{old}, reviens !", f"En avant, {self._name(mon)} !"]
        self._msg_index = 0
        if getattr(self, "_force_switch", False):
            self._force_switch = False
            self.state = BattleState.INTRO  # reuse advance → go MENU after msgs
            # Actually set to a path that goes to MENU
            self.state = BattleState.RESOLVE
            self._switched = False  # no enemy turn
            # After messages, RESOLVE with enemy alive player alive and not _switched → enemy attack
            # BAD. Need flag _skip_enemy
            self._skip_enemy = True
        else:
            self.state = BattleState.RESOLVE
            self._switched = True

    def _player_attack(self, move: Move) -> None:
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
        needed = getattr(self.player_mon, "xp_to_next_level", 0) or 0
        if needed and self.player_mon.xp >= needed and self.player_mon.level < 100:
            self.player_mon.level += 1
            self.player_mon.maxhp = self.player_mon.update_stats("hp")
            self.player_mon.hp = self.player_mon.maxhp
            for st in ("atk", "dfe", "ats", "dfs", "spd"):
                setattr(self.player_mon, st, self.player_mon.update_stats(st))
            try:
                self.player_mon.xp_to_next_level = self.player_mon.compute_xp_to_next_level()
            except Exception:
                pass
            msgs.append(f"{self._name(self.player_mon)} monte au N.{self.player_mon.level} !")
        # Argent
        if self.inventory is not None:
            gain = self.enemy_mon.level * 20
            self.inventory.money += gain
            msgs.append(f"Tu gagnes {gain} ₽ !")
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
        if self.state == BattleState.WIN:
            result = "win"
        elif self.state == BattleState.RAN:
            result = "ran"
        elif self.state == BattleState.CAUGHT:
            result = "caught"
        else:
            result = "lose"
        if self.on_end:
            self.on_end(result)

    # Fix advance_message for skip enemy after forced switch
    def _advance_message(self) -> None:
        self._msg_index += 1
        if self._msg_index < len(self.messages):
            return

        if self.state == BattleState.INTRO:
            self.state = BattleState.MENU
            self.messages = []
        elif self.state == BattleState.RESOLVE:
            if getattr(self, "_skip_enemy", False):
                self._skip_enemy = False
                self.state = BattleState.MENU
                self.messages = []
            elif getattr(self, "_switched", False):
                self._switched = False
                if self.enemy_mon.hp > 0 and self.player_mon.hp > 0:
                    self._enemy_attack()
                elif self.player_mon.hp <= 0:
                    self._after_player_faint()
                else:
                    self._on_win()
            elif self.enemy_mon.hp <= 0:
                self._on_win()
            elif self.player_mon.hp <= 0:
                self._after_player_faint()
            else:
                self._enemy_attack()
        elif self.state == BattleState.ENEMY_TURN:
            if self.player_mon.hp <= 0:
                self._after_player_faint()
            elif self.enemy_mon.hp <= 0:
                self._on_win()
            else:
                self.state = BattleState.MENU
                self.messages = []
        elif self.state in (BattleState.WIN, BattleState.LOSE, BattleState.RAN, BattleState.CAUGHT):
            self._finish()

    def _draw(self) -> None:
        display = self.screen.get_display()
        if display is None:
            return
        w, h = display.get_size()
        overlay = pygame.Surface((w, h))
        overlay.fill((30, 50, 80) if self.is_wild else (40, 35, 55))
        display.blit(overlay, (0, 0))

        self._draw_mon_panel(display, 40, 40, 400, 100, self.enemy_mon, self.enemy_name, True)
        self._draw_mon_panel(
            display, w - 440, h - 280, 400, 100, self.player_mon, "Toi", False
        )

        box_h = 150
        box = pygame.Surface((w - 80, box_h), pygame.SRCALPHA)
        box.fill((20, 25, 40, 240))
        pygame.draw.rect(box, (220, 220, 255), box.get_rect(), 3)
        display.blit(box, (40, h - box_h - 20))

        if self.messages and self._msg_index < len(self.messages):
            msg = self.messages[self._msg_index]
            self._blit_text(display, msg, 60, h - box_h, w - 120)
            if self._font_sm:
                display.blit(self._font_sm.render("E ▼", True, (180, 180, 100)), (w - 80, h - 50))
        elif self.state == BattleState.MENU:
            for i, opt in enumerate(self.MENU_OPTS):
                color = (255, 255, 100) if i == self.menu_index else (220, 220, 220)
                prefix = "▶ " if i == self.menu_index else "  "
                self._blit_text(display, f"{prefix}{opt}", 60, h - box_h + 8 + i * 30, w - 120, color)
        elif self.state == BattleState.MOVES:
            moves = self.player_mon.moves or []
            for i, m in enumerate(moves[:4]):
                color = (255, 255, 100) if i == self.move_index else (220, 220, 220)
                prefix = "▶ " if i == self.move_index else "  "
                pp = f"PP {m.pp}/{m.maxpp}" if m.maxpp else ""
                label = f"{prefix}{(m.dbSymbol or '?').upper()}  {pp}"
                self._blit_text(display, label, 60, h - box_h + 8 + i * 30, w - 120, color)
        elif self.state == BattleState.PARTY:
            for i, mon in enumerate(self.team[:6]):
                color = (255, 255, 100) if i == self.party_index else (220, 220, 220)
                prefix = "▶ " if i == self.party_index else "  "
                status = "K.O." if mon.hp <= 0 else f"{mon.hp}/{mon.maxhp}"
                label = f"{prefix}{self._name(mon)} N.{mon.level}  {status}"
                self._blit_text(display, label, 60, h - box_h + 6 + i * 24, w - 120, color)
        elif self.state == BattleState.BAG:
            balls = self._ball_list()
            if not balls:
                self._blit_text(display, "Pas de Ball…", 60, h - box_h + 20, w - 120)
            for i, (bid, qty) in enumerate(balls):
                color = (255, 255, 100) if i == self.bag_index else (220, 220, 220)
                prefix = "▶ " if i == self.bag_index else "  "
                name = "Super Ball" if bid == "great_ball" else "Poké Ball"
                self._blit_text(display, f"{prefix}{name} ×{qty}", 60, h - box_h + 10 + i * 30, w - 120, color)

    def _draw_mon_panel(self, display, x, y, pw, ph, mon, label, enemy) -> None:
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((15, 20, 35, 220))
        pygame.draw.rect(panel, (100, 160, 220) if enemy else (100, 200, 120), panel.get_rect(), 2)
        display.blit(panel, (x, y))
        name = f"{self._name(mon)}  N.{mon.level}"
        if self._font:
            display.blit(self._font.render(name, True, (255, 255, 255)), (x + 12, y + 10))
            if self._font_sm:
                display.blit(self._font_sm.render(label, True, (180, 180, 200)), (x + 12, y + 36))
        maxhp = max(1, mon.maxhp)
        ratio = max(0.0, min(1.0, mon.hp / maxhp))
        bar_w, bar_h = pw - 40, 14
        bx, by = x + 20, y + ph - 30
        pygame.draw.rect(display, (40, 40, 40), (bx, by, bar_w, bar_h))
        color = (80, 200, 80) if ratio > 0.5 else ((220, 180, 40) if ratio > 0.2 else (220, 60, 60))
        pygame.draw.rect(display, color, (bx, by, int(bar_w * ratio), bar_h))
        if self._font_sm:
            display.blit(self._font_sm.render(f"{mon.hp}/{mon.maxhp}", True, (230, 230, 230)), (bx, by - 18))

    def _blit_text(self, display, text, x, y, max_w, color=(240, 240, 240)) -> None:
        if not self._font:
            return
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
            display.blit(self._font.render(line, True, color), (x, y + i * 26))
