"""NPC entity — même apparence que le joueur, IA locale + déplacement autonome."""
from __future__ import annotations

import random

import pygame

from pokemon_game.core.spritesheet import SpriteSheet
from pokemon_game.entities.entity import Entity
from pokemon_game.systems.living_ai import LivingBrain


class NPC(Entity):
    """Personnage non-joueur : marche seul, rentre chez lui, parle avec IA."""

    DEFAULT_SPRITE = "hero_01_red_m_walk.png"

    def __init__(
        self,
        x: float,
        y: float,
        name: str = "NPC",
        dialogue_id: int = 0,
        sprite_file: str | None = None,
        direction: str = "down",
        personality: str = "neutre",
        role: str = "villageois",
        building: str = "",
        use_ai: bool = True,
        can_walk: bool = True,
    ) -> None:
        super().__init__(x, y)
        self.name = name
        self.dialogue_id = dialogue_id
        self.direction = direction
        self.personality = personality
        self.role = role
        self.building = building
        self.use_ai = use_ai
        self.can_walk = can_walk
        self.properties: dict = {"dialogue_id": dialogue_id}

        self.home = pygame.math.Vector2(x, y)
        self.work = pygame.math.Vector2(x, y)
        self.speed = 0.55
        self.brain = LivingBrain(name, personality, role) if use_ai else None

        # IA de déplacement
        self._state = "idle"  # idle | walk | pause | home
        self._timer = random.uniform(0.5, 2.0)
        self._walk_dx = 0.0
        self._walk_dy = 0.0
        self._anim_timer = 0.0
        self._anim_index = 0
        self._pause_until_talk = False  # freeze pendant dialogue

        self._load_sprite(sprite_file or self.DEFAULT_SPRITE)
        self.rect = self.image.get_rect(topleft=(int(x), int(y)))
        self.align_hitbox()

    def _load_sprite(self, filename: str) -> None:
        try:
            sheet = SpriteSheet.load(filename)
            frames = sheet.frames.get(self.direction) or sheet.frames.get("down")
            if frames:
                self.image = frames[0].copy()
            else:
                self.image = sheet.image.copy()
            self._sheet = sheet
            self._frames = sheet.frames
        except Exception as e:
            print(f"[NPC] Sprite {filename}: {e}")
            self.image = pygame.Surface((25, 32), pygame.SRCALPHA)
            self.image.fill((200, 60, 60))
            self._sheet = None
            self._frames = {}

    def face_player(self, player_direction: str) -> None:
        opposite = {
            "up": "down",
            "down": "up",
            "left": "right",
            "right": "left",
        }
        new_dir = opposite.get(player_direction, "down")
        self._set_direction(new_dir)

    def _set_direction(self, new_dir: str) -> None:
        if new_dir == self.direction:
            return
        self.direction = new_dir
        frames = self._frames.get(new_dir) or self._frames.get("down")
        if frames:
            self.image = frames[self._anim_index % len(frames)].copy()

    def speak(
        self,
        map_name: str,
        team_names: list[str],
        avg_level: float = 5.0,
        lang: str = "fr",
    ) -> list[dict]:
        self._pause_until_talk = True
        self._state = "idle"
        self._walk_dx = self._walk_dy = 0
        if self.brain and self.use_ai:
            return self.brain.reply(map_name, team_names, avg_level, lang)
        return [{"name": self.name, "text": "…"}]

    def resume_after_talk(self) -> None:
        self._pause_until_talk = False
        self._timer = random.uniform(1.0, 3.0)

    def set_collisions(self, collisions: list) -> None:
        self._collisions = collisions or []

    def update(self, *args, **kwargs) -> None:
        dt = 1 / 60
        # delta time from screen if available
        for a in args:
            if hasattr(a, "get_delta_time"):
                dt = (a.get_delta_time() or 16.0) / 1000.0
                break

        if self.can_walk and not self._pause_until_talk:
            self._ai_move(dt)

        self.rect.topleft = (int(self.position.x), int(self.position.y))
        self.align_hitbox()
        self._animate(dt)

    def set_work(self, x: float, y: float) -> None:
        self.work = pygame.math.Vector2(x, y)

    def _go_toward(self, target: pygame.math.Vector2, collisions: list) -> bool:
        """Marche vers target. Retourne True si arrivé."""
        dx = target.x - self.position.x
        dy = target.y - self.position.y
        dist = (dx * dx + dy * dy) ** 0.5
        if dist < 6:
            return True
        step_x = (dx / dist) * self.speed
        step_y = (dy / dist) * self.speed
        if abs(step_x) > abs(step_y):
            self._set_direction("right" if step_x > 0 else "left")
        elif step_y != 0:
            self._set_direction("down" if step_y > 0 else "up")
        self._try_step(step_x, step_y, collisions)
        return False

    def _ai_move(self, dt: float) -> None:
        """Routine type grand jeu : idle, patrouille, travail, maison."""
        self._timer -= dt
        collisions = getattr(self, "_collisions", [])

        if self._state == "idle":
            if self._timer <= 0:
                r = random.random()
                if r < 0.45:
                    self._state = "walk"
                    angle = random.choice(
                        [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, 1), (1, -1), (-1, -1)]
                    )
                    self._walk_dx = angle[0] * self.speed
                    self._walk_dy = angle[1] * self.speed
                    if abs(self._walk_dx) > abs(self._walk_dy):
                        self._set_direction("right" if self._walk_dx > 0 else "left")
                    elif self._walk_dy != 0:
                        self._set_direction("down" if self._walk_dy > 0 else "up")
                    self._timer = random.uniform(1.2, 3.5)
                elif r < 0.7:
                    self._state = "work"
                    self._timer = 8.0
                elif r < 0.9:
                    self._state = "home"
                    self._timer = 8.0
                else:
                    self._timer = random.uniform(1.5, 3.0)

        elif self._state == "walk":
            self._try_step(self._walk_dx, self._walk_dy, collisions)
            if self._timer <= 0:
                self._state = "idle"
                self._walk_dx = self._walk_dy = 0
                self._timer = random.uniform(0.8, 2.5)

        elif self._state == "home":
            if self._go_toward(self.home, collisions) or self._timer <= 0:
                self._state = "idle"
                self._timer = random.uniform(2.0, 5.0)

        elif self._state == "work":
            if self._go_toward(self.work, collisions) or self._timer <= 0:
                self._state = "idle"
                self._timer = random.uniform(2.0, 4.0)

    def _try_step(self, dx: float, dy: float, collisions: list) -> None:
        if dx:
            test = self.hitbox.move(dx, 0)
            if not any(test.colliderect(c) for c in collisions):
                self.position.x += dx
        if dy:
            self.rect.topleft = (int(self.position.x), int(self.position.y))
            self.align_hitbox()
            test = self.hitbox.move(0, dy)
            if not any(test.colliderect(c) for c in collisions):
                self.position.y += dy

    def _animate(self, dt: float) -> None:
        walking = self._state in ("walk", "home", "work") and not self._pause_until_talk
        frames = self._frames.get(self.direction) or self._frames.get("down") or [self.image]
        if walking:
            self._anim_timer += dt
            if self._anim_timer >= 0.15:
                self._anim_timer = 0.0
                self._anim_index = (self._anim_index + 1) % max(len(frames), 1)
        else:
            self._anim_index = 0
        if frames:
            self.image = frames[self._anim_index % len(frames)].copy()
