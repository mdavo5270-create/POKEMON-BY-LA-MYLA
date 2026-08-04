"""NPC entity — même apparence que le joueur, cerveau local (IA gratuite)."""
from __future__ import annotations

import pygame

from pokemon_game.core.spritesheet import SpriteSheet
from pokemon_game.entities.entity import Entity
from pokemon_game.systems.living_ai import LivingBrain


class NPC(Entity):
    """Personnage non-joueur : vraie silhouette joueur + IA locale."""

    # Même spritesheet que le héros (aspect identique)
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
    ) -> None:
        super().__init__(x, y)
        self.name = name
        self.dialogue_id = dialogue_id
        self.direction = direction
        self.personality = personality
        self.role = role
        self.building = building
        self.use_ai = use_ai
        self.properties: dict = {"dialogue_id": dialogue_id}

        self.brain = LivingBrain(name, personality, role) if use_ai else None

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
        except Exception as e:
            print(f"[NPC] Sprite {filename}: {e}")
            self.image = pygame.Surface((25, 32), pygame.SRCALPHA)
            self.image.fill((200, 60, 60))
            self._sheet = None

    def face_player(self, player_direction: str) -> None:
        opposite = {
            "up": "down",
            "down": "up",
            "left": "right",
            "right": "left",
        }
        new_dir = opposite.get(player_direction, "down")
        if new_dir == self.direction:
            return
        self.direction = new_dir
        if self._sheet:
            frames = self._sheet.frames.get(new_dir) or self._sheet.frames.get("down")
            if frames:
                self.image = frames[0].copy()

    def speak(
        self,
        map_name: str,
        team_names: list[str],
        avg_level: float = 5.0,
        lang: str = "fr",
    ) -> list[dict]:
        """Génère des pages de dialogue via l'IA locale (ou fallback)."""
        if self.brain and self.use_ai:
            return self.brain.reply(map_name, team_names, avg_level, lang)
        return [
            {
                "name": self.name,
                "text": "…",
            }
        ]

    def update(self, *args, **kwargs) -> None:
        self.rect.topleft = (int(self.position.x), int(self.position.y))
        self.align_hitbox()
