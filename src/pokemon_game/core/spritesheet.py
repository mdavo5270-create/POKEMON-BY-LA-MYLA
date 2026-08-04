"""SpriteSheet optimisé — cache global + découpe correcte 25×32."""
from __future__ import annotations

from pathlib import Path

import pygame

from pokemon_game.core.tool import ASSETS, Tool, asset_path

# Layouts prioritaires : les sprites hero_* sont en 100×128 → 4×4 frames de 25×32
_LAYOUTS = [
    (25, 32),   # hero_01_* (walk, run, bike, swamp…)
    (40, 36),   # surf / fish (160×144 → 4×4)
    (16, 24),   # fallback classique
    (16, 32),
    (32, 32),
]

_DIRECTIONS = ("down", "left", "right", "up")


class SpriteSheet:
    """Charge un spritesheet une seule fois et met les frames en cache."""

    _cache: dict[str, SpriteSheet] = {}

    def __init__(
        self,
        path: str,
        frame_w: int | None = None,
        frame_h: int | None = None,
        directions: tuple[str, ...] = _DIRECTIONS,
    ) -> None:
        key = str(Path(path).resolve()) if Path(path).exists() else path
        if key in SpriteSheet._cache:
            cached = SpriteSheet._cache[key]
            self.path = cached.path
            self.frames = cached.frames
            self.frame_size = cached.frame_size
            self.image = cached.image
            return

        self.path = path
        self.frames: dict[str, list[pygame.Surface]] = {}
        self.frame_size = (16, 24)
        self.image: pygame.Surface

        if not Path(path).exists():
            print(f"[SPRITE] Fichier introuvable : {path}")
            self._make_dummy()
            SpriteSheet._cache[key] = self
            return

        try:
            sheet = pygame.image.load(path).convert_alpha()
        except Exception as exc:
            print(f"[SPRITE] Échec load {path}: {exc}")
            self._make_dummy()
            SpriteSheet._cache[key] = self
            return

        w, h = sheet.get_size()
        print(f"[SPRITE] Chargé : {path} ({w}x{h})")

        layouts = []
        if frame_w and frame_h:
            layouts.append((frame_w, frame_h))
        layouts.extend(_LAYOUTS)

        loaded = False
        for fw, fh in layouts:
            if w % fw != 0 or h % fh != 0:
                continue
            cols = w // fw
            rows = h // fh
            if rows < 1 or cols < 1:
                continue
            try:
                order = list(directions)
                # Si moins de 4 lignes, on répète la première direction
                for i, direction in enumerate(order):
                    row = i if i < rows else 0
                    frames: list[pygame.Surface] = []
                    for col in range(cols):
                        frames.append(
                            Tool.split_image(sheet, col * fw, row * fh, fw, fh)
                        )
                    if frames:
                        self.frames[direction] = frames
                if self.frames:
                    self.frame_size = (fw, fh)
                    loaded = True
                    print(
                        f"[SPRITE] Layout {fw}x{fh} ({cols}×{rows}) "
                        f"dirs={list(self.frames.keys())}"
                    )
                    break
            except Exception as exc:
                print(f"[SPRITE] Layout {fw}x{fh} échoué : {exc}")
                self.frames = {}
                continue

        if not loaded:
            print("[SPRITE] Layout non reconnu — frame unique.")
            fw = min(25, w)
            fh = min(32, h)
            frame = Tool.split_image(sheet, 0, 0, fw, fh)
            self.frames = {d: [frame] for d in directions}
            self.frame_size = (fw, fh)

        self.image = self.frames.get("down", next(iter(self.frames.values())))[0]
        SpriteSheet._cache[key] = self

    def _make_dummy(self) -> None:
        dummy = pygame.Surface((25, 32), pygame.SRCALPHA)
        dummy.fill((220, 40, 40))
        self.frames = {d: [dummy] for d in _DIRECTIONS}
        self.frame_size = (25, 32)
        self.image = dummy

    @classmethod
    def load(cls, relative_name: str, **kwargs) -> SpriteSheet:
        """Charge depuis assets/sprite/<relative_name> (avec cache)."""
        path = asset_path("sprite", relative_name)
        return cls(path, **kwargs)

    @classmethod
    def clear_cache(cls) -> None:
        cls._cache.clear()
