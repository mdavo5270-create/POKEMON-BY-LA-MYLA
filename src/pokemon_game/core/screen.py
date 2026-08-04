import pygame
from pokemon_game.core.tool import asset_path


class Screen:
    """Screen class to manage the display."""

    def __init__(self) -> None:
        self.display = pygame.display.set_mode((1280, 720))
        pygame.display.set_caption("POKEMON BY LA MYLA")
        try:
            pygame.display.set_icon(pygame.image.load(asset_path("app", "logo_projet_pokemon.png")))
        except Exception:
            pass
        self.imagescreen: pygame.Surface = self.display.copy()
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.framerate: int = 144
        self.deltatime: float = 0.0

    def update(self) -> None:
        pygame.display.flip()
        self.clock.tick(self.framerate)
        self.imagescreen = self.display.copy()
        self.display.fill((0, 0, 0))
        self.deltatime = self.clock.get_time()

    def get_delta_time(self) -> float:
        return self.deltatime

    def get_size(self) -> tuple[int, int]:
        return self.display.get_size()

    def get_display(self):
        return self.display

    def image_screen(self):
        return self.imagescreen
