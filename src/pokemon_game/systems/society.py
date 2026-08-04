"""Société du village — bâtiments, habitants, règles.

Système 100 % local, sans API payante.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Building:
    map_name: str
    label: str
    owner: str
    role: str
    public: bool = True  # si False → entrée réservée / règles strictes
    description: str = ""


@dataclass
class Citizen:
    name: str
    building: str  # map_name du bâtiment attribué
    role: str
    personality: str  # trait principal pour l'IA locale
    home_x: float = 0
    home_y: float = 0


# ── Bâtiments du monde ──────────────────────────────────────────────
BUILDINGS: dict[str, Building] = {
    "house_0": Building(
        "house_0",
        "Maison d'Aria",
        "Maître Aria",
        "habitation",
        public=True,
        description="Maison du maître qui a tout maîtrisé. Ouverte aux dresseurs sérieux.",
    ),
    "house_1": Building(
        "house_1",
        "Maison du rival",
        "Rival",
        "habitation",
        public=True,
        description="Petite maison du rival. On peut y entrer, mais respectez les lieux.",
    ),
    "labo_0": Building(
        "labo_0",
        "Laboratoire Pokémon",
        "Professeur Chen",
        "laboratoire",
        public=True,
        description="Labo de recherche. Les dresseurs y reçoivent leurs premiers conseils.",
    ),
    "pokecenter": Building(
        "pokecenter",
        "Centre Pokémon",
        "Infirmière Joelle",
        "soins",
        public=True,
        description="Soins gratuits pour tous les Pokémon. Ouvert en permanence.",
    ),
    "pokeshop": Building(
        "pokeshop",
        "Boutique Pokémon",
        "Marchand",
        "commerce",
        public=True,
        description="Objets, Poké Balls et provisions. Paiement obligatoire.",
    ),
    "inter_0": Building(
        "inter_0",
        "Maison intérieure",
        "Villageois",
        "habitation",
        public=True,
        description="Intérieur d'une maison du village.",
    ),
}

# ── Citoyens ────────────────────────────────────────────────────────
CITIZENS: dict[str, Citizen] = {
    "aria": Citizen(
        "Maître Aria",
        "house_0",
        "maître absolu",
        "perfectionniste_sage",
    ),
    "rival": Citizen(
        "Rival",
        "house_1",
        "rival",
        "compétitif",
    ),
    "chen": Citizen(
        "Professeur Chen",
        "labo_0",
        "professeur",
        "savant_bienveillant",
    ),
    "joelle": Citizen(
        "Infirmière Joelle",
        "pokecenter",
        "infirmière",
        "douce_professionnelle",
    ),
    "marchand": Citizen(
        "Marchand",
        "pokeshop",
        "vendeur",
        "commercial_honnête",
    ),
}

# ── Règles de société (affichables + appliquées en jeu) ─────────────
SOCIETY_RULES: list[str] = [
    "1. Chaque bâtiment a un propriétaire. Entrer chez quelqu'un, c'est accepter ses règles.",
    "2. Le Centre Pokémon soigne gratuitement : on n'y combat pas.",
    "3. La Boutique exige un échange honnête : pas de vol.",
    "4. Le Laboratoire est un lieu de savoir : on y respecte le Professeur.",
    "5. La maison d'Aria est ouverte, mais le Maître exige respect et sérieux.",
    "6. On ne bloque pas les portes ni les passages des autres dresseurs.",
    "7. Les Pokémon ne s'utilisent pas pour détruire le mobilier des maisons.",
    "8. Un dresseur responsable soigne son équipe avant de défier un rival.",
]


def get_building(map_name: str) -> Building | None:
    return BUILDINGS.get(map_name)


def get_owner_of(map_name: str) -> str | None:
    b = BUILDINGS.get(map_name)
    return b.owner if b else None


def rules_text(lang: str = "fr") -> str:
    if lang == "en":
        return "Society rules are enforced in this village. Respect buildings and their owners."
    return "\n".join(SOCIETY_RULES)
