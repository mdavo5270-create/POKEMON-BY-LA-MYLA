"""Player entity — spritesheet optimisé (cache + 25×32) + animation temps réel."""
from __future__ import annotations

import pygame

from pokemon_game.core.controller import Controller
from pokemon_game.core.keylistener import KeyListener
from pokemon_game.core.screen import Screen
from pokemon_game.core.spritesheet import SpriteSheet
from pokemon_game.core.switch import Switch
from pokemon_game.entities.entity import Entity

_ANIM_FILES = {
    "walk": "hero_01_red_m_walk.png",
    "run": "hero_01_red_m_run.png",
    "bike": "hero_01_red_m_cycle_wheel.png",
    "surf": "hero_01_red_m_surf.png",
}

# Fallback touches (QWERTY + flèches) en plus du controller AZERTY
_DIR_FALLBACKS = {
    "up": (pygame.K_UP, pygame.K_w),
    "down": (pygame.K_DOWN, pygame.K_s),  # S déjà AZERTY down
    "left": (pygame.K_LEFT, pygame.K_a),
    "right": (pygame.K_RIGHT, pygame.K_d),  # D déjà AZERTY right
}


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
        self.animation_timer = 0.0
        self.animation_interval = 0.12
        self.pending_switch: Switch | None = None
        self._dialogue_lock = False
        self.team: list = []
        self.inventory = None  # set by Game (Inventory)
        self._moving = False  # pour l'anim même si collision bloque un axe

        self._load_sprites()
        self.rect = self.image.get_rect(topleft=(x, y))
        self.align_hitbox()

    def _load_sprites(self) -> None:
        self.sheets: dict[str, SpriteSheet] = {}
        for key, filename in _ANIM_FILES.items():
            try:
                self.sheets[key] = SpriteSheet.load(filename)
            except Exception as exc:
                print(f"[SPRITE] Impossible de charger {filename}: {exc}")

        if not self.sheets:
            dummy = SpriteSheet.__new__(SpriteSheet)
            dummy._make_dummy()
            self.sheets["walk"] = dummy

        self.current_anim = "walk"
        self.current_sheet = self.sheets.get("walk") or next(iter(self.sheets.values()))
        self.images = self.current_sheet.frames
        self.image = self.current_sheet.image
        fw, fh = self.current_sheet.frame_size
        print(f"[SPRITE] Joueur prêt — anim={list(self.sheets.keys())} frame={fw}x{fh}")

    def set_animation(self, name: str) -> None:
        if name not in self.sheets or name == self.current_anim:
            return
        self.current_anim = name
        self.current_sheet = self.sheets[name]
        self.images = self.current_sheet.frames
        self.animation_index = 0
        self.animation_timer = 0.0
        frames = self.images.get(self.direction) or self.images.get("down")
        if frames:
            self.image = frames[0]

    def add_collisions(self, collisions: list) -> None:
        self.collisions = collisions or []

    def add_switchs(self, switchs: list) -> None:
        self.switchs = [s for s in (switchs or []) if s.name.lower() != "spawn"]
        print(f"[SWITCH] {len(self.switchs)} switch(es) chargés pour le joueur (spawn exclus)")
        for s in self.switchs:
            print(f"         → {s.name} port={s.port} rect={s.hitbox}")

    def switch_bike(self, force: bool | None = None) -> None:
        if force is not None:
            self.on_bike = force
        else:
            self.on_bike = not self.on_bike
        self.speed = 2 if self.on_bike else 1
        self.set_animation("bike" if self.on_bike else "walk")

    def unlock(self) -> None:
        """Force la libération des locks (dialogue / menu)."""
        self._dialogue_lock = False
        self.menu_option = False

    def _key_dir(self, direction: str) -> bool:
        """True si la direction est pressée (controller + fallbacks flèches/WASD)."""
        kl = self.keylistener
        primary = self.controller.get_key(direction)
        if kl.key_pressed(primary):
            return True
        for k in _DIR_FALLBACKS.get(direction, ()):
            if kl.key_pressed(k):
                return True
        return False

    def update(self, *args, **kwargs) -> None:
        self.handle_input()
        self._animate()
        super().update()

    def _animate(self) -> None:
        # Anime si intention de bouger (touches) OU si on a réellement bougé
        moving = self._moving or any(
            self._key_dir(d) for d in ("up", "down", "left", "right")
        )
        dt = (self.screen.get_delta_time() or 16.0) / 1000.0

        if moving and not self._dialogue_lock and not self.menu_option:
            self.animation_timer += dt
            if self.animation_timer >= self.animation_interval:
                self.animation_timer = 0.0
                frames = self.images.get(self.direction) or self.images.get(
                    "down", [self.image]
                )
                self.animation_index = (self.animation_index + 1) % max(len(frames), 1)
        else:
            self.animation_index = 0
            self.animation_timer = 0.0

        frames = self.images.get(self.direction) or self.images.get("down", [self.image])
        if frames:
            self.image = frames[self.animation_index % len(frames)]

    def handle_input(self) -> None:
        self._moving = False

        if self._dialogue_lock or self.menu_option:
            return

        kl = self.keylistener
        c = self.controller

        if kl.key_pressed(c.get_key("bike")):
            self.switch_bike()
            kl.remove_key(c.get_key("bike"))

        running = kl.key_pressed(c.get_key("run")) and not self.on_bike
        if running:
            self.speed = 2
            self.set_animation("run")
        elif not self.on_bike:
            self.speed = 1
            self.set_animation("walk")

        dx = dy = 0
        if self._key_dir("up"):
            dy = -self.speed
            self.direction = "up"
        elif self._key_dir("down"):
            dy = self.speed
            self.direction = "down"
        elif self._key_dir("left"):
            dx = -self.speed
            self.direction = "left"
        elif self._key_dir("right"):
            dx = self.speed
            self.direction = "right"

        if not (dx or dy):
            return

        self._moving = True  # intention : anime les pieds même si mur

        # 1) SWITCHES : uniquement si on ENTRE dans le switch
        test_full = self.hitbox.move(dx, dy)
        for switch in self.switchs:
            if switch.check_collision(test_full) and not switch.check_collision(
                self.hitbox
            ):
                self.pending_switch = switch
                return

        # 2) Collision par axe (glisse le long des murs au lieu de tout bloquer)
        moved = False
        if dx:
            test_x = self.hitbox.move(dx, 0)
            if not any(test_x.colliderect(col) for col in self.collisions):
                self.position.x += dx
                moved = True
        if dy:
            # realigner hitbox après éventuel move X
            self.rect.topleft = (int(self.position.x), int(self.position.y))
            self.align_hitbox()
            test_y = self.hitbox.move(0, dy)
            if not any(test_y.colliderect(col) for col in self.collisions):
                self.position.y += dy
                moved = True

        if moved:
            self.rect.topleft = (int(self.position.x), int(self.position.y))
            self.align_hitbox()
