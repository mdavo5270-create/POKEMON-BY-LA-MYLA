"""Entry point for POKEMON BY LA MYLA (2D Pygame or 3D Ursina)."""
from __future__ import annotations

import argparse
import os
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description="POKEMON BY LA MYLA")
    parser.add_argument(
        "--3d",
        dest="mode_3d",
        action="store_true",
        help="Lancer le prototype 3D (Ursina)",
    )
    parser.add_argument(
        "--2d",
        dest="mode_2d",
        action="store_true",
        help="Lancer le jeu 2D classique (Pygame) — défaut",
    )
    args, _unknown = parser.parse_known_args()

    use_3d = args.mode_3d or os.environ.get("POKEMON_RENDER", "").lower() in ("3d", "ursina")
    if use_3d and not args.mode_2d:
        try:
            from pokemon_game.render3d import run_3d
        except ImportError as e:
            print(
                "Mode 3D indisponible. Installe les deps :\n"
                "  pip install -e \".[3d]\"\n"
                f"Détail: {e}",
                file=sys.stderr,
            )
            sys.exit(1)
        run_3d()
        return

    import pygame
    from pokemon_game.core.game import Game

    pygame.init()
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
