"""Pokemon class - stats, IVs, moveset, XP.

Restauré depuis le projet original (EP7-Pokemon .. EP9-Save) et adapté à la
structure du package (import + chemin des assets via `asset_path`).
"""
from __future__ import annotations

import json
import math
import random

from pokemon_game.core.tool import asset_path
from pokemon_game.entities.move import Move


class Pokemon:
    """Pokémon class to manage the Pokémons."""

    def __init__(self, data: dict, level: int) -> None:
        self.klass = data["klass"]
        self.id = data["id"]
        self.dbSymbol = data["dbSymbol"]
        self.forms = data["forms"]
        self.evolutions = self.forms[0]["evolutions"]
        self.type = self.get_types()
        self.baseHp = self.forms[0]["baseHp"]
        self.baseAtk = self.forms[0]["baseAtk"]
        self.baseDfe = self.forms[0]["baseDfe"]
        self.baseSpd = self.forms[0]["baseSpd"]
        self.baseAts = self.forms[0]["baseAts"]
        self.baseDfs = self.forms[0]["baseDfs"]
        self.evHp = self.forms[0]["evHp"]
        self.evAtk = self.forms[0]["evAtk"]
        self.evDfe = self.forms[0]["evDfe"]
        self.evSpd = self.forms[0]["evSpd"]
        self.evAts = self.forms[0]["evAts"]
        self.evDfs = self.forms[0]["evDfs"]
        self.experienceType = self.forms[0]["experienceType"]
        self.baseExperience = self.forms[0]["baseExperience"]
        self.baseLoyalty = self.forms[0]["baseLoyalty"]
        self.catchRate = self.forms[0]["catchRate"]
        self.femaleRate = self.forms[0]["femaleRate"]
        self.breedGroups = self.forms[0]["breedGroups"]
        self.hatchSteps = self.forms[0]["hatchSteps"]
        self.babyDbSymbol = self.forms[0]["babyDbSymbol"]
        self.babyForm = self.forms[0]["babyForm"]
        self.itemHeld = self.forms[0]["itemHeld"]
        self.abilities = self.forms[0]["abilities"]
        self.frontOffsetY = self.forms[0]["frontOffsetY"]
        self.resources = self.forms[0]["resources"]
        self.moveSet = self.forms[0]["moveSet"]

        self.level = level
        self.gender = "female" if random.randint(1, 100) <= self.femaleRate else "male"
        if self.femaleRate == -1:
            self.gender = "genderless"
        self.ivs = {key: random.randint(0, 31) for key in self.get_base_stats().keys()}
        self.base_stats = self.get_base_stats()

        self.maxhp = self.update_stats("hp")
        self.hp = self.maxhp
        self.atk = self.update_stats("atk")
        self.dfe = self.update_stats("dfe")
        self.ats = self.update_stats("ats")
        self.dfs = self.update_stats("dfs")
        self.spd = self.update_stats("spd")

        # Fan-game rate: 1/512 (plus rare que 1/10, plus accessible que 1/4096)
        self.shiny = "shiny" if random.randint(1, 512) == 1 else ""
        self.xp = 0
        self.points_ev = 0

        self.moves: list[Move] = self.set_moves()
        self.status = ""

        self.xp_to_next_level = self.compute_xp_to_next_level()

        self.evolution = None

    def get_types(self) -> list[str]:
        """Get the types of the Pokémon."""
        type1 = self.forms[0].get("type1") or "normal"
        type2 = self.forms[0].get("type2")
        if not type2 or type2 == "__undef__":
            return [type1]
        return [type1, type2]

    def get_base_stats(self) -> dict:
        """Get the base stats of the Pokémon."""
        return {
            "hp": self.forms[0]["baseHp"],
            "atk": self.forms[0]["baseAtk"],
            "dfe": self.forms[0]["baseDfe"],
            "spd": self.forms[0]["baseSpd"],
            "ats": self.forms[0]["baseAts"],
            "dfs": self.forms[0]["baseDfs"],
        }

    def update_stats(self, stat: str) -> int:
        """Update one stat of the Pokémon from its base/IV/EV/level.

        Formule officielle (Gen 3+) :
          HP  = floor((2*B + IV + floor(EV/4)) * L / 100) + L + 10
          Autres = floor((floor((2*B + IV + floor(EV/4)) * L / 100) + 5) * Nature)
        """
        base_stat = self.get_base_stats()[stat]
        iv = self.ivs[stat]
        ev = self.get_ev()[stat]
        level = self.level
        nature = 1.0
        if stat == "hp":
            return math.floor(
                ((2 * base_stat + iv + math.floor(ev / 4)) * level / 100) + level + 10
            )
        return math.floor(
            (((2 * base_stat + iv + math.floor(ev / 4)) * level / 100) + 5) * nature
        )

    def compute_xp_to_next_level(self):
        """Get the total experience required to reach the *next* level
        (courbe officielle, total XP pour atteindre level+1)."""
        if self.level >= 100:
            return 0
        n = self.level + 1  # XP totale pour atteindre le niveau suivant
        if self.experienceType == 1:  # Fast
            return math.floor((4 * (n ** 3)) / 5)
        elif self.experienceType == 3:  # Medium Slow
            return math.floor(
                ((6 / 5) * (n ** 3)) - (15 * (n ** 2)) + (100 * n) - 140
            )
        elif self.experienceType == 0:  # Medium Fast
            return n ** 3
        elif self.experienceType == 2:  # Slow
            return math.floor(5 * (n ** 3) / 4)
        elif self.experienceType == 4:  # Erratic
            if n <= 50:
                return math.floor((n ** 3) * (100 - n) / 50)
            elif n <= 68:
                return math.floor((n ** 3) * (150 - n) / 100)
            elif n <= 98:
                return math.floor(
                    (n ** 3) * math.floor((1911 - 10 * n) / 3) / 500
                )
            else:
                return math.floor((n ** 3) * (160 - n) / 100)
        return n ** 3

    def set_moves(self) -> list[Move]:
        """Pick a random legal moveset for the current level."""
        list_move: list[dict] = []
        list_attack: list[Move] = []
        for move in self.moveSet:
            try:
                if move["level"] <= self.level:
                    list_move.append(move)
            except (KeyError, TypeError):
                pass
        if not list_move:
            return list_attack
        minimum = min(2, len(list_move))
        maximum = min(4, len(list_move))
        for _ in range(random.randint(minimum, maximum)):
            if not list_move:
                break
            chosen = random.choice(list_move)
            list_move.remove(chosen)
            try:
                list_attack.append(Move.createMove(chosen["move"]))
            except Exception as e:
                print(f"[MOVE] Impossible de charger {chosen.get('move')}: {e}")
        return list_attack

    def get_ev(self) -> dict:
        """Get the effort values of the Pokémon."""
        return {
            "hp": self.forms[0]["evHp"],
            "atk": self.forms[0]["evAtk"],
            "dfe": self.forms[0]["evDfe"],
            "ats": self.forms[0]["evAts"],
            "dfs": self.forms[0]["evDfs"],
            "spd": self.forms[0]["evSpd"],
        }

    def to_dict(self) -> dict:
        """Convertir l'objet Pokémon en dictionnaire sérialisable."""
        return {
            "klass": self.klass,
            "id": self.id,
            "dbSymbol": self.dbSymbol,
            "forms": self.forms,
            "type": self.type,
            "level": self.level,
            "gender": self.gender,
            "ivs": self.ivs,
            "base_stats": self.base_stats,
            "maxhp": self.maxhp,
            "hp": self.hp,
            "atk": self.atk,
            "dfe": self.dfe,
            "ats": self.ats,
            "dfs": self.dfs,
            "spd": self.spd,
            "shiny": self.shiny,
            "xp": self.xp,
            "points_ev": self.points_ev,
            "moves": [move.to_dict() for move in self.moves],
            "status": self.status,
            "xp_to_next_level": self.xp_to_next_level,
            "evolution": self.evolution,
        }

    @staticmethod
    def from_dict(data: dict) -> "Pokemon":
        """Create a Pokémon from a dictionary (ex: sauvegarde JSON)."""
        pokemon = Pokemon.__new__(Pokemon)
        pokemon.__dict__.update(data)
        pokemon.moves = [Move.from_dict(move_data) for move_data in data["moves"]]
        return pokemon

    @staticmethod
    def create_pokemon(name: str, level: int) -> "Pokemon":
        """Create a Pokémon from its dbSymbol/name (looked up in assets/json/pokemon)."""
        path = asset_path("json", "pokemon", f"{name.lower()}.json")
        with open(path, encoding="utf-8") as f:
            return Pokemon(json.load(f), level)
