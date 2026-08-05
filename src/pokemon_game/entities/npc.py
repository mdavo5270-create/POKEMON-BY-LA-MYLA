"""NPC — même sprite joueur, IA locale, chemins (BFS), routines maison/travail."""
from __future__ import annotations

import random
from collections import deque

import pygame

from pokemon_game.core.spritesheet import SpriteSheet
from pokemon_game.entities.entity import Entity
from pokemon_game.systems.living_ai import LivingBrain


class NPC(Entity):
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
        wander_radius: float = 80.0,
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
        self.speed = 0.7
        self.wander_radius = wander_radius
        self.brain = LivingBrain(name, personality, role) if use_ai else None

        self._state = "idle"
        self._timer = random.uniform(1.0, 3.0)
        self._walk_dx = 0.0
        self._walk_dy = 0.0
        self._anim_timer = 0.0
        self._anim_index = 0
        self._pause_until_talk = False
        self._path: list[tuple[float, float]] = []
        self._collisions: list[pygame.Rect] = []

        self._load_sprite(sprite_file or self.DEFAULT_SPRITE)
        self.rect = self.image.get_rect(topleft=(int(x), int(y)))
        self.align_hitbox()

    def _load_sprite(self, filename: str) -> None:
        try:
            sheet = SpriteSheet.load(filename)
            frames = sheet.frames.get(self.direction) or sheet.frames.get("down")
            self.image = (frames[0] if frames else sheet.image).copy()
            self._sheet = sheet
            self._frames = sheet.frames
        except Exception as e:
            print(f"[NPC] Sprite {filename}: {e}")
            self.image = pygame.Surface((25, 32), pygame.SRCALPHA)
            self.image.fill((200, 60, 60))
            self._sheet = None
            self._frames = {}

    def face_player(self, player_direction: str) -> None:
        opposite = {"up": "down", "down": "up", "left": "right", "right": "left"}
        self._set_direction(opposite.get(player_direction, "down"))

    def _set_direction(self, new_dir: str) -> None:
        if new_dir == self.direction:
            return
        self.direction = new_dir
        frames = self._frames.get(new_dir) or self._frames.get("down")
        if frames:
            self.image = frames[self._anim_index % len(frames)].copy()

    def speak(self, map_name: str, team_names: list[str], avg_level: float = 5.0, lang: str = "fr") -> list[dict]:
        self._pause_until_talk = True
        self._state = "idle"
        self._path = []
        if self.brain and self.use_ai:
            return self.brain.reply(map_name, team_names, avg_level, lang)
        return [{"name": self.name, "text": "…"}]

    def resume_after_talk(self) -> None:
        self._pause_until_talk = False
        self._timer = random.uniform(1.0, 2.5)

    def set_collisions(self, collisions: list) -> None:
        self._collisions = collisions or []

    def set_work(self, x: float, y: float) -> None:
        self.work = pygame.math.Vector2(x, y)

    def update(self, *args, **kwargs) -> None:
        dt = 1 / 60
        for a in args:
            if hasattr(a, "get_delta_time"):
                dt = (a.get_delta_time() or 16.0) / 1000.0
                break
        if self.can_walk and not self._pause_until_talk:
            self._ai_move(dt)
        self.rect.topleft = (int(self.position.x), int(self.position.y))
        self.align_hitbox()
        self._animate(dt)

    # ── Pathfinding BFS simple (grille 16px) ─────────────────────────
    def _find_path(self, target: pygame.math.Vector2) -> list[tuple[float, float]]:
        """BFS sur grille 16×16 en évitant les collisions."""
        step = 16
        start = (int(self.position.x // step), int(self.position.y // step))
        goal = (int(target.x // step), int(target.y // step))
        if start == goal:
            return []

        def blocked(gx: int, gy: int) -> bool:
            rect = pygame.Rect(gx * step, gy * step, step, step)
            # ne pas trop s'éloigner de la maison (zone de vie)
            cx = (self.home.x + self.work.x) / 2
            cy = (self.home.y + self.work.y) / 2
            if abs(gx * step - cx) > self.wander_radius * 1.8:
                return True
            if abs(gy * step - cy) > self.wander_radius * 1.8:
                return True
            return any(rect.colliderect(c) for c in self._collisions)

        if blocked(*goal):
            # cible bloquée → voisin libre
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                if not blocked(goal[0] + dx, goal[1] + dy):
                    goal = (goal[0] + dx, goal[1] + dy)
                    break

        q = deque([start])
        came: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
        found = False
        limit = 400
        while q and limit > 0:
            limit -= 1
            cur = q.popleft()
            if cur == goal:
                found = True
                break
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                nxt = (cur[0] + dx, cur[1] + dy)
                if nxt in came or blocked(*nxt):
                    continue
                came[nxt] = cur
                q.append(nxt)

        if not found:
            return []

        path: list[tuple[float, float]] = []
        cur = goal
        while cur is not None and cur != start:
            path.append((cur[0] * step + 4, cur[1] * step + 4))
            cur = came.get(cur)
        path.reverse()
        return path

    def _follow_path(self) -> bool:
        """Suit self._path. True si arrivé."""
        if not self._path:
            return True
        tx, ty = self._path[0]
        dx = tx - self.position.x
        dy = ty - self.position.y
        dist = (dx * dx + dy * dy) ** 0.5
        if dist < 4:
            self._path.pop(0)
            return not self._path
        step_x = (dx / dist) * self.speed
        step_y = (dy / dist) * self.speed
        if abs(step_x) > abs(step_y):
            self._set_direction("right" if step_x > 0 else "left")
        elif step_y != 0:
            self._set_direction("down" if step_y > 0 else "up")
        self._try_step(step_x, step_y, self._collisions)
        return False

    def _go_toward(self, target: pygame.math.Vector2) -> bool:
        if not self._path:
            self._path = self._find_path(target)
            if not self._path:
                # fallback ligne droite
                dx = target.x - self.position.x
                dy = target.y - self.position.y
                dist = (dx * dx + dy * dy) ** 0.5
                if dist < 6:
                    return True
                self._try_step((dx / dist) * self.speed, (dy / dist) * self.speed, self._collisions)
                return False
        return self._follow_path()

    def _ai_move(self, dt: float) -> None:
        self._timer -= dt
        cols = self._collisions

        if self._state == "idle":
            if self._timer <= 0:
                r = random.random()
                if r < 0.35:
                    # petite promenade dans le rayon
                    ang = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
                    tx = self.home.x + ang[0] * random.uniform(20, self.wander_radius * 0.6)
                    ty = self.home.y + ang[1] * random.uniform(20, self.wander_radius * 0.6)
                    self._path = self._find_path(pygame.math.Vector2(tx, ty))
                    self._state = "walk"
                    self._timer = 4.0
                elif r < 0.65:
                    self._path = []
                    self._state = "work"
                    self._timer = 10.0
                elif r < 0.9:
                    self._path = []
                    self._state = "home"
                    self._timer = 10.0
                else:
                    self._timer = random.uniform(2.0, 4.0)

        elif self._state == "walk":
            if self._follow_path() or self._timer <= 0:
                self._state = "idle"
                self._path = []
                self._timer = random.uniform(1.5, 3.5)

        elif self._state == "home":
            if self._go_toward(self.home) or self._timer <= 0:
                self._state = "idle"
                self._path = []
                self._timer = random.uniform(2.0, 5.0)

        elif self._state == "work":
            if self._go_toward(self.work) or self._timer <= 0:
                self._state = "idle"
                self._path = []
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
