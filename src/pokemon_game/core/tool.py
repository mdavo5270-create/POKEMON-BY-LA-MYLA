"""Utility helpers."""
from pathlib import Path
import pygame

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
ASSETS = _PROJECT_ROOT / "assets"


def asset_path(*parts: str) -> str:
    """Return absolute path to an asset."""
    return str(ASSETS.joinpath(*parts))


class Tool:
    @staticmethod
    def split_image(spritesheet: pygame.Surface, x: int, y: int, width: int, height: int) -> pygame.Surface:
        return spritesheet.subsurface(pygame.Rect(x, y, width, height))

    @staticmethod
    def blur(background, param) -> pygame.Surface:
        for _ in range(param):
            background = pygame.transform.smoothscale(
                background, (background.get_width() // 2, background.get_height() // 2)
            )
            background = pygame.transform.smoothscale(
                background, (background.get_width() * 2, background.get_height() * 2)
            )
        return background

    @staticmethod
    def create_text(
        text: str, size: int, color: tuple[int, int, int], font: str = "Roboto-Light", bold: bool = False
    ) -> pygame.Surface:
        font_path = asset_path("fonts", f"{font}.ttf")
        font_obj = pygame.font.Font(font_path if Path(font_path).exists() else None, size)
        if bold:
            font_obj.set_bold(True)
        return font_obj.render(text, True, color)

    @staticmethod
    def add_text_to_surface(surface, text, x, y) -> None:
        surface.blit(text, (x, y))
