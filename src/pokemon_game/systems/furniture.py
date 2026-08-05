"""Mobilier procédural pour les intérieurs (sans assets Tiled manquants).

Ajoute collisions + dessin simple (lit, table, comptoir, étagère, PC…).
"""
from __future__ import annotations

import pygame


# Définitions par map : liste de (x, y, w, h, label, color)
FURNITURE: dict[str, list[tuple]] = {
    "house_0": [
        (80, 80, 48, 32, "Lit", (80, 100, 160)),
        (160, 80, 40, 24, "Table", (140, 100, 60)),
        (200, 80, 16, 16, "Chaise", (120, 80, 40)),
        (80, 140, 64, 20, "Étagère", (100, 70, 40)),
        (180, 140, 32, 28, "PC", (60, 60, 80)),
        (100, 200, 48, 24, "Canapé", (160, 60, 60)),
    ],
    "house_1": [
        (40, 40, 40, 28, "Lit", (80, 100, 160)),
        (100, 40, 36, 24, "Table", (140, 100, 60)),
        (40, 100, 48, 20, "Étagère", (100, 70, 40)),
        (120, 100, 28, 24, "Coffre", (150, 110, 50)),
    ],
    "labo_0": [
        (40, 40, 80, 24, "Paillasse", (180, 180, 190)),
        (140, 40, 60, 24, "Paillasse", (180, 180, 190)),
        (40, 90, 32, 40, "Étagère livres", (120, 80, 50)),
        (200, 90, 40, 32, "PC labo", (50, 50, 70)),
        (100, 90, 48, 24, "Microscope", (140, 140, 150)),
    ],
    "pokecenter": [
        (60, 40, 80, 28, "Comptoir", (220, 80, 100)),
        (160, 40, 40, 48, "Machine soins", (100, 200, 220)),
        (40, 120, 48, 24, "Banc", (160, 120, 80)),
        (160, 120, 48, 24, "Banc", (160, 120, 80)),
        (100, 160, 32, 32, "Plante", (60, 140, 60)),
    ],
    "pokeshop": [
        (20, 20, 100, 24, "Comptoir", (100, 140, 200)),
        (20, 60, 40, 48, "Étagère", (140, 100, 60)),
        (70, 60, 40, 48, "Étagère", (140, 100, 60)),
        (120, 40, 28, 32, "Caisse", (80, 80, 100)),
    ],
    "inter_0": [
        (30, 30, 40, 28, "Lit", (80, 100, 160)),
        (90, 30, 36, 24, "Table", (140, 100, 60)),
        (30, 80, 48, 20, "Étagère", (100, 70, 40)),
        (100, 80, 28, 24, "Sac", (100, 80, 50)),
    ],
    "house_2": [
        (40, 40, 40, 24, "Panier Pokémon", (200, 150, 90)),
        (100, 40, 32, 24, "Gamelle", (120, 180, 200)),
        (40, 100, 48, 20, "Étagère soins", (100, 70, 40)),
        (120, 100, 28, 24, "Coffre", (150, 110, 50)),
        (170, 40, 36, 28, "Panier Pokémon", (200, 150, 90)),
    ],
}


def get_furniture_rects(map_name: str) -> list[pygame.Rect]:
    items = FURNITURE.get(map_name, [])
    return [pygame.Rect(x, y, w, h) for x, y, w, h, _, _ in items]


def draw_furniture(display: pygame.Surface, map_name: str, font: pygame.font.Font | None = None) -> None:
    items = FURNITURE.get(map_name, [])
    for x, y, w, h, label, color in items:
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        surf.fill((*color, 230))
        pygame.draw.rect(surf, (255, 255, 255, 80), surf.get_rect(), 1)
        display.blit(surf, (x, y))
        if font and w >= 28:
            txt = font.render(label[:8], True, (255, 255, 255))
            display.blit(txt, (x + 2, y + max(0, h // 2 - 6)))
