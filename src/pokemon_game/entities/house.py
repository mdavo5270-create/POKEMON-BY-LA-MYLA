from __future__ import annotations

import pygame
from pathlib import Path
from typing import Any, Dict, List, Optional

from pokemon_game.core.spritesheet import SpriteSheet


class House(pygame.sprite.Sprite):
    """House entity: autonomous animated sprite with interaction and serialization.

    Minimal responsibilities:
    - load sprite / spritesheet (via SpriteSheet.load)
    - animate frames with interval
    - provide draw(surface) and update(dt)
    - interact(player) -> returns dict with action (e.g., enter interior)
    - to_dict / from_dict for saves and map metadata
    """

    def __init__(
        self,
        id: str,
        asset: str,
        x: int,
        y: int,
        interior_map: Optional[str] = None,
        anim_frames: int = 1,
        anim_interval: float = 0.5,
    ) -> None:
        super().__init__()
        self.id = id
        self.asset = asset
        self.x = int(x)
        self.y = int(y)
        self.interior_map = interior_map
        self.anim_frames = int(anim_frames)
        self.anim_interval = float(anim_interval)

        self.images: List[pygame.Surface] = []
        self.animation_index = 0
        self.animation_timer = 0.0

        self._load_images()

    def _load_images(self) -> None:
        """Try to load a SpriteSheet; fall back to a single Surface placeholder."""
        try:
            sheet = SpriteSheet.load(self.asset)
            # SpriteSheet.frames is a dict (direction -> list) in player use; try to flatten
            frames = []
            if isinstance(sheet.frames, dict):
                for v in sheet.frames.values():
                    frames.extend(v)
            else:
                frames = getattr(sheet, "frames", []) or [sheet.image]
            if frames:
                self.images = frames[: self.anim_frames] or [frames[0]]
            else:
                self.images = [sheet.image]
        except Exception:
            # Fallback: single plain surface
            surf = pygame.Surface((32, 32), pygame.SRCALPHA)
            surf.fill((150, 100, 80))
            self.images = [surf]
        self.image = self.images[0]
        self.rect = self.image.get_rect(topleft=(self.x, self.y))

    def update(self, dt: float) -> None:
        """Update animation. dt in seconds."""
        if len(self.images) <= 1:
            return
        self.animation_timer += dt
        if self.animation_timer >= self.anim_interval:
            self.animation_timer = 0.0
            self.animation_index = (self.animation_index + 1) % len(self.images)
            self.image = self.images[self.animation_index]

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.image, (self.x, self.y))

    def interact(self, player: Any) -> Dict[str, Any]:
        """Called when player interacts (presses action near entrance).

        Returns a dict describing the action to the game (e.g., {'enter': True, 'interior': '...'}).
        """
        return {"enter": True, "interior": self.interior_map}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "asset": self.asset,
            "x": self.x,
            "y": self.y,
            "interior_map": self.interior_map,
            "anim_frames": self.anim_frames,
            "anim_interval": self.anim_interval,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "House":
        return House(
            id=data.get("id", "house"),
            asset=data.get("asset", ""),
            x=int(data.get("x", 0)),
            y=int(data.get("y", 0)),
            interior_map=data.get("interior_map"),
            anim_frames=int(data.get("anim_frames", 1)),
            anim_interval=float(data.get("anim_interval", 0.5)),
        )
