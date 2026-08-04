"""Player entity."""
from __future__ import annotations
import pygame
from pokemon_game.entities.entity import Entity
from pokemon_game.core.screen import Screen
from pokemon_game.core.controller import Controller
from pokemon_game.core.keylistener import KeyListener
from pokemon_game.core.tool import asset_path, Tool


class Player(Entity):
    def __init__(
        self,
        screen: Screen,
        controller: Controller,
        x: float,
        y: float,
        keylistener: KeyListener,
    ) -> None:
        super().__init__(x, y)
        self.screen = screen
        self.controller = controller
        self.keylistener = keylistener
        self.menu_option = False
        self.collisions: list[pygame.Rect] = []
        self.switchs = []
        self.speed = 1
        self.on_bike = False
        try:
            sheet = pygame.image.load(
                asset_path("sprite", "hero_01_red_m_walk.png")
            ).convert_alpha()
            self.image = Tool.split_image(sheet, 0, 0, 16, 24)
        except Exception:
            self.image = pygame.Surface((16, 24))
            self.image.fill((200, 50, 50))
        self.rect = self.image.get_rect(topleft=(x, y))

    def add_collisions(self, collisions: list) -> None:
        self.collisions = collisions or []

    def add_switchs(self, switchs: list) -> None:
        self.switchs = switchs or []

    def switch_bike(self, force: bool | None = None) -> None:
        if force is not None:
            self.on_bike = force
        else:
            self.on_bike = not self.on_bike
        self.speed = 2 if self.on_bike else 1

    def update(self, *args, **kwargs) -> None:
        self.handle_input()
        super().update()

    def handle_input(self) -> None:
        dx = dy = 0
        kl = self.keylistener
        c = self.controller
        if kl.key_pressed(c.get_key("up")):
            dy = -self.speed
            self.direction = "up"
        elif kl.key_pressed(c.get_key("down")):
            dy = self.speed
            self.direction = "down"
        elif kl.key_pressed(c.get_key("left")):
            dx = -self.speed
            self.direction = "left"
        elif kl.key_pressed(c.get_key("right")):
            dx = self.speed
            self.direction = "right"

        if dx or dy:
            new_pos = self.position + pygame.math.Vector2(dx, dy)
            test = self.hitbox.move(dx, dy)
            if not any(test.colliderect(col) for col in self.collisions):
                self.position = new_pos
