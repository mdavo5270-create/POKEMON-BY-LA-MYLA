"""3D rendering layer (Ursina / Panda3D) for POKEMON BY LA MYLA.

Reuses existing gameplay systems: Pokemon, Battle, Inventory, Save, society data.
The 2D Pygame path remains available via `python -m pokemon_game` (default).
3D path: `python -m pokemon_game --3d` or `POKEMON_RENDER=3d`.
"""

from __future__ import annotations

__all__ = ["run_3d"]


def run_3d() -> None:
    from pokemon_game.render3d.app import run_app

    run_app()
