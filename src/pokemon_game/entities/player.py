"""Player entity - version corrigée (switches + animation)."""
from __future__ import annotations
import pygame
from pokemon_game.entities.entity import Entity
from pokemon_game.core.screen import Screen
from pokemon_game.core.controller import Controller
from pokemon_game.core.keylistener import KeyListener
from pokemon_game.core.tool import asset_path, Tool
from pokemon_game.core.switch import Switch


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
        self.switchs: list[Switch] = []
        self.speed = 1
        self.on_bike = False
        self.animation_index = 0
        self.animation_timer = 0
        self.animation_speed = 8  # frames entre chaque image
        self.pending_switch: Switch | None = None

        # Chargement du spritesheet
        try:
            sheet = pygame.image.load(
                asset_path("sprite", "hero_01_red_m_walk.png")
            ).convert_alpha()
            # Découpe les 4 directions × 4 frames (classique 16×24)
            self.images = {
                "down":  [Tool.split_image(sheet, i * 16, 0,  16, 24) for i in range(4)],
                "left":  [Tool.split_image(sheet, i * 16, 24, 16, 24) for i in range(4)],
                "right": [Tool.split_image(sheet, i * 16, 48, 16, 24) for i in range(4)],
                "up":    [Tool.split_image(sheet, i * 16, 72, 16, 24) for i in range(4)],
            }
        except Exception:
            # Fallback rouge
            dummy = pygame.Surface((16, 24))
            dummy.fill((200, 50, 50))
            self.images = {d: [dummy] * 4 for d in ("down", "left", "right", "up")}

        self.image = self.images["down"][0]
        self.rect = self.image.get_rect(topleft=(x, y))
        self.align_hitbox()

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
        self._animate()
        super().update()

    def _animate(self) -> None:
        """Animation simple quand on bouge."""
        moving = any([
            self.keylistener.key_pressed(self.controller.get_key(k))
            for k in ("up", "down", "left", "right")
        ])
        if moving:
            self.animation_timer += 1
            if self.animation_timer >= self.animation_speed:
                self.animation_timer = 0
                self.animation_index = (self.animation_index + 1) % 4
        else:
            self.animation_index = 0  # frame idle

        self.image = self.images.get(self.direction, self.images["down"])[self.animation_index]

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
            test = self.hitbox.move(dx, dy)

            # Collision murs
            if any(test.colliderect(col) for col in self.collisions):
                return

            # === DÉTECTION DES SWITCHES (portes / maisons) ===
            for switch in self.switchs:
                if switch.check_collision(test):
                    self.pending_switch = switch
                    return

            # Mouvement autorisé
            self.position += pygame.math.Vector2(dx, dy)
