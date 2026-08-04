"""Base Entity."""
from __future__ import annotations
import pygame


class Entity(pygame.sprite.Sprite):
    def __init__(self, x: float, y: float) -> None:
        super().__init__()
        self.position = pygame.math.Vector2(x, y)
        self.image = pygame.Surface((16, 24))
        self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.hitbox = self.rect.inflate(-4, -8)
        self.speed = 1
        self.direction = "down"
        self.step = 16

    def align_hitbox(self) -> None:
        self.hitbox.midbottom = self.rect.midbottom

    def update(self, *args, **kwargs) -> None:
        self.rect.topleft = (int(self.position.x), int(self.position.y))
        self.align_hitbox()
