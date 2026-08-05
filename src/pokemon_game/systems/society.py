"""Société du village — bâtiments, habitants, lieux, règles.

Les maisons viennent des maps Tiled du projet (house_0, house_1, labo_0,
pokecenter, pokeshop, inter_0, map_1…). Chaque bâtiment a un propriétaire.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Building:
    map_name: str
    label: str
    owner: str
    role: str
    public: bool = True
    description: str = ""
    door_x: float = 0
    door_y: float = 0


@dataclass
class Citizen:
    name: str
    building: str
    role: str
    personality: str
    home_x: float = 0
    home_y: float = 0
    work_x: float = 0
    work_y: float = 0


@dataclass
class PlaceOfInterest:
    id: str
    label: str
    x: float
    y: float
    w: float = 48
    h: float = 40
    description_fr: str = ""
    description_en: str = ""


BUILDINGS: dict[str, Building] = {
    "house_0": Building(
        "house_0", "Maison d'Aria", "Maître Aria", "habitation",
        description="Maison du maître. Ouverte aux dresseurs sérieux.",
        door_x=512, door_y=256,
    ),
    "house_1": Building(
        "house_1", "Maison du Rival", "Rival", "habitation",
        description="Chez le rival. Respectez les lieux.",
        door_x=580, door_y=256,
    ),
    "labo_0": Building(
        "labo_0", "Laboratoire Pokémon", "Professeur Chen", "laboratoire",
        description="Recherche et conseils aux jeunes dresseurs.",
        door_x=472, door_y=256,
    ),
    "pokecenter": Building(
        "pokecenter", "Centre Pokémon", "Infirmière Joelle", "soins",
        description="Soins gratuits. Ouvert en permanence.",
        door_x=424, door_y=256,
    ),
    "pokeshop": Building(
        "pokeshop", "Boutique Pokémon", "Marchand Leo", "commerce",
        description="Balls, potions, provisions.",
        door_x=376, door_y=256,
    ),
    "inter_0": Building(
        "inter_0", "Maison du village", "Campeur Hugo", "habitation",
        description="Petite maison d'un villageois.",
        door_x=640, door_y=300,
    ),
    "map_1": Building(
        "map_1", "Route de l'Est", "—", "route",
        description="Chemin hors du village.",
        door_x=736, door_y=144,
    ),
    "house_2": Building(
        "house_2", "Pension de Maya", "Éleveuse Maya", "habitation",
        description="Une pension isolée où les Pokémon fatigués se reposent.",
        door_x=1016, door_y=456,
    ),
}

CITIZENS: dict[str, Citizen] = {
    "aria": Citizen(
        "Maître Aria", "house_0", "maître absolu", "perfectionniste_sage",
        work_x=520, work_y=300,
    ),
    "rival": Citizen(
        "Rival", "house_1", "rival", "compétitif",
        work_x=600, work_y=300,
    ),
    "chen": Citizen(
        "Professeur Chen", "labo_0", "professeur", "savant_bienveillant",
        work_x=480, work_y=300,
    ),
    "joelle": Citizen(
        "Infirmière Joelle", "pokecenter", "infirmière", "douce_professionnelle",
        work_x=430, work_y=300,
    ),
    "marchand": Citizen(
        "Marchand Leo", "pokeshop", "vendeur", "commercial_honnête",
        work_x=380, work_y=300,
    ),
    "hugo": Citizen(
        "Campeur Hugo", "inter_0", "campeur", "aventurier",
        work_x=650, work_y=320,
    ),
    "lea": Citizen(
        "Léa", "house_1", "villageoise", "curieuse",
        work_x=550, work_y=340,
    ),
    "tom": Citizen(
        "Tom le pêcheur", "map_0", "pêcheur", "calme",
        work_x=200, work_y=400,
    ),
    "garde": Citizen(
        "Garde Milo", "map_1", "garde", "strict",
        work_x=720, work_y=160,
    ),
    "maya": Citizen(
        "Éleveuse Maya", "house_2", "éleveuse", "chaleureuse",
        work_x=1016, work_y=490,
    ),
}

PLACES: list[PlaceOfInterest] = [
    PlaceOfInterest(
        "place_mairie", "Place du village", 512, 320, 64, 48,
        "Le cœur du village. Les dresseurs s'y croisent souvent.",
        "The heart of the village.",
    ),
    PlaceOfInterest(
        "etang", "Étang calme", 200, 400, 64, 48,
        "Un étang tranquille. On dit que des Pokémon d'eau s'y cachent.",
        "A quiet pond. Water Pokémon may hide here.",
    ),
    PlaceOfInterest(
        "panneau_est", "Panneau Route Est", 720, 160, 48, 40,
        "Route de l'Est → Hors du village. Attention aux Pokémon sauvages.",
        "East Route → Outside the village.",
    ),
    PlaceOfInterest(
        "banc", "Banc public", 560, 340, 40, 32,
        "Un banc à l'ombre. Les villageois s'y reposent.",
        "A bench in the shade.",
    ),
    PlaceOfInterest(
        "jardin", "Petit jardin", 450, 350, 48, 40,
        "Des fleurs soignées. Quelqu'un aime ce village.",
        "Well-kept flowers.",
    ),
]

SOCIETY_RULES: list[str] = [
    "1. Chaque bâtiment a un propriétaire. Entrer, c'est accepter ses règles.",
    "2. Le Centre Pokémon soigne gratuitement : on n'y combat pas.",
    "3. La Boutique exige un échange honnête : pas de vol.",
    "4. Le Laboratoire est un lieu de savoir : respectez le Professeur.",
    "5. La maison d'Aria est ouverte, mais le Maître exige sérieux et respect.",
    "6. On ne bloque pas les portes ni les passages.",
    "7. Les Pokémon ne servent pas à détruire le mobilier.",
    "8. Soigne ton équipe avant de défier un rival.",
    "9. La Route de l'Est est libre, mais reste vigilant.",
    "10. Les villageois ont leur routine : ne les dérange pas sans raison.",
]


def get_building(map_name: str) -> Building | None:
    return BUILDINGS.get(map_name)


def get_owner_of(map_name: str) -> str | None:
    b = BUILDINGS.get(map_name)
    return b.owner if b else None
