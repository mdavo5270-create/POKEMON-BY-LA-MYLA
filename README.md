# POKEMON BY LA MYLA 🎮

> Version finale propre du fan-game Pokémon 2D en Python + Pygame.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Architecture (propre & finale)

```
src/pokemon_game/
├── core/       # Game, Screen, Map, Controller, KeyListener, Switch, Tool
├── entities/   # Entity, Player, Pokemon, Move
├── systems/    # Dialogue, Save, Option, SQL
├── render3d/   # Prototype 3D Ursina
└── ui/         # (futur)
assets/         # maps, sprites, json, fonts, interfaces
tests/
docs/
```

Les anciens épisodes (EP1→EP9) ont été **fusionnés** dans cette structure propre.  
Plus de dossiers EP* dans le code de production.

## Installation

```bash
git clone https://github.com/mdavo5270-create/POKEMON-BY-LA-MYLA.git
cd POKEMON-BY-LA-MYLA
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Lancer le jeu

```bash
python -m pokemon_game
# ou après install
pokemon-game
```

## Développement

- Branch `develop` pour les features
- PR vers `main`
- CI déjà configurée

## Features

- Déplacement tile-based + collisions
- Changement de map
- Vélo
- Système Pokémon (stats, moves, IVs, XP)
- Dialogues
- Sauvegarde
- Menus / Options

## Crédits

Basé sur le travail original d’Arnaud Michel.  
Version propre et finale par **La Myla**.

MIT License

## Mode 3D (prototype Ursina)

Le jeu 2D Pygame reste le mode par défaut. Un **prototype 3D** réutilise les mêmes données Pokémon, inventaire et sauvegarde.

### Installation 3D

```bash
pip install -e ".[3d]"
```

### Lancer

```bash
python -m pokemon_game --3d
# ou
POKEMON_RENDER=3d python -m pokemon_game
```

### Contrôles 3D

| Touche | Action |
|--------|--------|
| WASD / flèches | Déplacement |
| E / Espace | Combat sauvage test (calculs Battle existants) |
| F5 | Sauvegarde (`save_3d`) |
| Tab | Changer de carte (map_0 / map_1) |
| Esc | Quitter |

### Architecture

```
src/pokemon_game/render3d/
├── app.py       # Boucle Ursina + HUD
├── player3d.py  # Contrôleur 3e personne
└── world.py     # Grille 3D depuis TMX (collisions / warps)
```

Les systèmes `entities/pokemon`, `systems/battle`, `systems/inventory`, `systems/save_io` sont **partagés** avec le mode 2D.
