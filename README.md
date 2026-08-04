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
