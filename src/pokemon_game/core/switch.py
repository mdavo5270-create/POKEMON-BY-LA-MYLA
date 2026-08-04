import pygame


class Switch:
    """Switch class to manage map transitions."""

    def __init__(self, type: str, name: str, hitbox: pygame.Rect, port: int):
        self.type: str = type
        self.name: str = name
        self.hitbox: pygame.Rect = hitbox
        self.port: int = port

    def check_collision(self, temp_hitbox) -> bool:
        return self.hitbox.colliderect(temp_hitbox)
