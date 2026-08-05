"""Screen — rendu soigné, compatible UI 1280×720."""
from __future__ import annotations

import pygame

from pokemon_game.core.tool import asset_path


class Screen:
    """Affichage principal.

    - Fenêtre 1280×720 (UI, dialogues, combat)
    - 60 FPS stable
    - Vignette légère + fond letterbox pro
    """

    def __init__(self) -> None:
        self.display = None
        for flags in (
            pygame.DOUBLEBUF | pygame.RESIZABLE,
            pygame.RESIZABLE,
            0,
        ):
            try:
                self.display = pygame.display.set_mode((1280, 720), flags)
                break
            except pygame.error:
                continue
        if self.display is None:
            self.display = pygame.display.set_mode((1280, 720))
        pygame.display.set_caption("POKEMON BY LA MYLA")
        try:
            pygame.display.set_icon(
                pygame.image.load(asset_path("app", "logo_projet_pokemon.png"))
            )
        except Exception:
            pass

        self.imagescreen: pygame.Surface = self.display.copy()
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.framerate: int = 60
        self.deltatime: float = 0.0

        self._vignette: pygame.Surface | None = None
        self._build_vignette(1280, 720)
        self.use_vignette = True

    def _build_vignette(self, w: int, h: int) -> None:
        self._vignette = pygame.Surface((w, h), pygame.SRCALPHA)
        cx, cy = w // 2, h // 2
        max_d = (cx * cx + cy * cy) ** 0.5
        # Vignette par bandes (rapide)
        for y in range(0, h, 2):
            for x in range(0, w, 4):
                dx, dy = x - cx, y - cy
                d = (dx * dx + dy * dy) ** 0.5 / max_d
                alpha = int(min(110, max(0, (d - 0.5) * 220)))
                if alpha:
                    self._vignette.fill((0, 0, 0, alpha), (x, y, 4, 2))

    def update(self) -> None:
        if self.use_vignette and self._vignette is not None:
            # Adapter si resize
            if self._vignette.get_size() != self.display.get_size():
                self._build_vignette(*self.display.get_size())
            self.display.blit(self._vignette, (0, 0))

        pygame.display.flip()
        self.clock.tick(self.framerate)
        self.imagescreen = self.display.copy()
        self.display.fill((12, 16, 24))  # fond pro (pas noir pur)
        self.deltatime = self.clock.get_time()

    def get_delta_time(self) -> float:
        return self.deltatime

    def get_size(self) -> tuple[int, int]:
        return self.display.get_size()

    def get_display(self):
        return self.display

    def image_screen(self):
        return self.imagescreen
