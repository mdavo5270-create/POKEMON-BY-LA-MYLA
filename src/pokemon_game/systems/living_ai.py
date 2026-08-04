"""IA locale gratuite pour les PNJ « vivants ».

Aucune API externe, aucun coût. Mémoire + contexte joueur + personnalité.
Ce n'est pas un LLM cloud : c'est un cerveau procédural qui réagit vraiment
à l'état du jeu (équipe, lieu, nombre de visites, etc.).
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass
class Memory:
    visits: int = 0
    last_team_names: list[str] = field(default_factory=list)
    last_map: str = ""
    talked_about_rules: bool = False
    player_was_rude: int = 0  # compteur simple


class LivingBrain:
    """Cerveau d'un PNJ : choisit des répliques selon le contexte."""

    def __init__(self, name: str, personality: str, role: str) -> None:
        self.name = name
        self.personality = personality
        self.role = role
        self.memory = Memory()

    def remember_visit(self, map_name: str, team_names: list[str]) -> None:
        self.memory.visits += 1
        self.memory.last_map = map_name
        self.memory.last_team_names = list(team_names)

    def reply(
        self,
        map_name: str,
        team_names: list[str],
        player_level_avg: float = 5.0,
        lang: str = "fr",
    ) -> list[dict]:
        """Retourne une liste de pages {name, text} adaptées au contexte."""
        self.remember_visit(map_name, team_names)
        pages: list[dict] = []

        if self.personality == "perfectionniste_sage":
            pages = self._aria(map_name, team_names, player_level_avg, lang)
        elif self.personality == "compétitif":
            pages = self._rival(team_names, player_level_avg, lang)
        elif self.personality == "savant_bienveillant":
            pages = self._chen(team_names, lang)
        elif self.personality == "douce_professionnelle":
            pages = self._joelle(team_names, lang)
        elif self.personality == "commercial_honnête":
            pages = self._marchand(lang)
        else:
            pages = [
                {
                    "name": self.name,
                    "text": "Bonjour." if lang == "fr" else "Hello.",
                }
            ]
        return pages

    # ── Personnalités ───────────────────────────────────────────────

    def _aria(
        self,
        map_name: str,
        team: list[str],
        avg: float,
        lang: str,
    ) -> list[dict]:
        n = self.name
        v = self.memory.visits
        team_str = ", ".join(t.capitalize() for t in team) if team else (
            "aucun Pokémon" if lang == "fr" else "no Pokémon"
        )

        if lang == "fr":
            greetings = [
                f"Encore toi. Visite n°{v}. J'espère que tu as progressé.",
                f"Te revoilà. Je me souviens de ta dernière visite.",
                f"Ah. Le dresseur au regard déterminé. Visite {v}.",
            ]
            if v == 1:
                open_ = (
                    "Je suis Aria. J'ai maîtrisé chaque type, chaque stratégie, "
                    "chaque capacité. Rien n'échappe à mon analyse."
                )
            else:
                open_ = random.choice(greetings)

            if not team:
                body = (
                    "Tu n'as même pas de Pokémon ? Reviens quand tu auras "
                    "commencé à comprendre ce monde."
                )
            elif avg < 8:
                body = (
                    f"Ton équipe ({team_str}) est encore fragile. "
                    "La maîtrise ne s'improvise pas. Entraîne-toi."
                )
            elif avg < 20:
                body = (
                    f"({team_str})… Correct. Mais loin de la perfection. "
                    "Observe, adapte, ne te repose jamais sur un seul type."
                )
            else:
                body = (
                    f"({team_str}). Tu commences à approcher d'un vrai niveau. "
                    "Continue. Quand tu seras prêt, je te montrerai la vraie maîtrise."
                )

            rules = (
                "Rappel : chaque maison a un propriétaire. "
                "Respecte les lieux, soigne ton équipe, ne bloque jamais une porte. "
                "Ce sont les règles de notre société."
            )
            end = (
                "Va. Et reviens meilleur — ou ne reviens pas."
                if avg < 15
                else "Je t'observe. Ne me déçois pas."
            )

            pages = [
                {"name": n, "text": open_},
                {"name": n, "text": body},
            ]
            if v == 1 or not self.memory.talked_about_rules:
                pages.append({"name": n, "text": rules})
                self.memory.talked_about_rules = True
            pages.append({"name": n, "text": end})
            return pages

        # English fallback
        return [
            {"name": n, "text": f"I am Aria. Visit #{v}. I master everything."},
            {"name": n, "text": f"Your team: {team_str}. Keep training."},
        ]

    def _rival(self, team: list[str], avg: float, lang: str) -> list[dict]:
        n = self.name
        if lang != "fr":
            return [{"name": n, "text": "I'll beat you next time."}]
        if not team:
            t = "Tss, même pas un Pokémon ? Pathétique."
        elif avg < 10:
            t = f"Avec {', '.join(team)} tu ne me battras jamais. Entraîne-toi !"
        else:
            t = "Hmm… tu t'améliores. La prochaine fois, c'est moi qui gagne."
        return [
            {"name": n, "text": f"Toi encore ? Visite {self.memory.visits}."},
            {"name": n, "text": t},
        ]

    def _chen(self, team: list[str], lang: str) -> list[dict]:
        n = self.name
        if lang != "fr":
            return [{"name": n, "text": "Study hard, young trainer."}]
        if not team:
            t = "Prends d'abord un starter, puis reviens me voir."
        else:
            t = (
                f"Ton équipe ({', '.join(team)}) a du potentiel. "
                "Observe la nature, note les comportements."
            )
        return [
            {"name": n, "text": "Bienvenue au laboratoire."},
            {"name": n, "text": t},
            {"name": n, "text": "Le savoir est la vraie force d'un dresseur."},
        ]

    def _joelle(self, team: list[str], lang: str) -> list[dict]:
        n = self.name
        if lang != "fr":
            return [{"name": n, "text": "Your Pokémon are fully healed!"}]
        return [
            {"name": n, "text": "Bienvenue au Centre Pokémon."},
            {
                "name": n,
                "text": (
                    "Tes Pokémon sont en pleine forme."
                    if team
                    else "Reviens quand tu auras des Pokémon à soigner."
                ),
            },
            {"name": n, "text": "Prends soin d'eux. C'est la règle ici."},
        ]

    def _marchand(self, lang: str) -> list[dict]:
        n = self.name
        if lang != "fr":
            return [{"name": n, "text": "Welcome! Take a look around."}]
        return [
            {"name": n, "text": "Bienvenue à la boutique !"},
            {"name": n, "text": "Poké Balls, potions… tout a un prix. Pas de vol ici."},
            {"name": n, "text": "Reviens quand tu auras des sous."},
        ]
