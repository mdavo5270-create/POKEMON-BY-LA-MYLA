import pygame


class Controller:
    """Controller class to manage the keys."""

    def __init__(self):
        self.keys: dict[str, int] = {
            "up": pygame.K_z,
            "down": pygame.K_s,
            "left": pygame.K_q,
            "right": pygame.K_d,
            "action": pygame.K_e,
            "bike": pygame.K_b,
            "run": pygame.K_LSHIFT,
            "menu": pygame.K_ESCAPE,
            "quit": pygame.K_ESCAPE,
        }

    def get_key(self, key: str) -> int:
        return self.keys[key]

    def add_key(self, key: str, value: int) -> None:
        self.keys[key] = value
