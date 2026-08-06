# POKEMON BY LA MYLA

Fan-game Pokémon **2D (Pygame)** + **prototype 3D (Ursina)**.

## Installation

```bash
git clone https://github.com/mdavo5270-create/POKEMON-BY-LA-MYLA.git
cd POKEMON-BY-LA-MYLA
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Lancer 2D (defaut)

```bash
python -m pokemon_game
```

## Mode 3D (Ursina)

```bash
pip install -e ".[3d]"
python -m pokemon_game --3d
```

### Controles 3D

| Touche | Action |
|--------|--------|
| WASD / fleches | Deplacement |
| E / Espace | Interagir / combat (confirmer en combat) |
| Pads jaunes | Warps (marcher dessus ou E a cote) |
| F5 | Sauvegarde (`save_3d`) |
| F6 | Soigner equipe (debug) |
| Tab | map_0 / map_1 |
| Esc | Quitter (fuite si en combat) |

### Combat 3D

Menu **Attaquer / Sac / Fuir**, choix des capacites, degats via `systems.battle.calc_damage`.

### Architecture 3D

```
src/pokemon_game/render3d/
  app.py         # boucle Ursina
  game3d.py      # orchestration
  map_builder.py # sol, murs, batiments, warps
  player3d.py    # dresseur + camera
  battle3d.py    # arene + HUD combat
  world.py       # grille depuis TMX
```

Systemes partages: Pokemon, Battle, Inventory, Save.

MIT License — La Myla
