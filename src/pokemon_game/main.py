"""Entry point for POKEMON BY LA MYLA."""
import pygame
from pokemon_game.core.game import Game

def main() -> None:
    pygame.init()
    game = Game()
    game.run()

if __name__ == "__main__":
    main()
