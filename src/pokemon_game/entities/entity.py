"""Base Entity."""
from __future__ import annotations
import pygame


class Entity(pygame.sprite.Sprite):
    def __init__(self, x: float, y: float) -> None:
        super().__init__()
        self.position = pygame.math.Vector2(x, y)
        # Taille par défaut alignée sur les frames hero (25×32)
        self.image = pygame.Surface((25, 32), pygame.SRCALPHA)
        self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect(topleft=(x, y))
        # Hitbox plus étroite pour les collisions tile 16×16
        self.hitbox = self.rect.inflate(-8, -12)
        self.speed = 1
        self.direction = "down"
        self.step = 16

    def align_hitbox(self) -> None:
        self.hitbox.midbottom = self.rect.midbottom

    def update(self, *args, **kwargs) -> None:
        self.rect.topleft = (int(self.position.x), int(self.position.y))
        self.align_hitbox()
