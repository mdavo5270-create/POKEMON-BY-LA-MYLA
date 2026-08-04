"""Options / pause menu system.

Touche ESC → ouvre le menu.
Navigation Z/S (ou flèches via controller) + E pour valider.
"""
from __future__ import annotations

import pygame

from pokemon_game.core.tool import asset_path
from pathlib import Path


class Option:
    LABELS = {
        "fr": ["Continuer", "Sauvegarder", "Règles de société", "Quitter"],
        "en": ["Resume", "Save", "Society rules", "Quit"],
    }

    def __init__(self, screen, controller, map_obj, lang, save, keylistener, dialogue) -> None:
        self.screen = screen
        self.controller = controller
        self.map = map_obj
        self.lang = lang if lang in self.LABELS else "fr"
        self.save = save
        self.keylistener = keylistener
        self.dialogue = dialogue
        self.player = None  # set later if needed

        self.selected = 0
        self._font: pygame.font.Font | None = None
        self._font_title: pygame.font.Font | None = None
        self._panel: pygame.Surface | None = None
        self._load_assets()

    def _load_assets(self) -> None:
        try:
            font_path = asset_path("fonts", "pokemon.ttf")
            if not Path(font_path).exists():
                font_path = asset_path("fonts", "Roboto-Regular.ttf")
            exists = Path(font_path).exists()
            self._font = pygame.font.Font(font_path if exists else None, 28)
            self._font_title = pygame.font.Font(font_path if exists else None, 36)
        except Exception:
            self._font = pygame.font.SysFont(None, 30)
            self._font_title = pygame.font.SysFont(None, 40)

        # Panel semi-transparent
        self._panel = pygame.Surface((360, 320), pygame.SRCALPHA)
        self._panel.fill((15, 20, 40, 230))
        pygame.draw.rect(self._panel, (255, 255, 255), self._panel.get_rect(), 3)

    def open(self, player=None) -> None:
        if player is not None:
            self.player = player
            player.menu_option = True
            setattr(player, "_dialogue_lock", True)
        self.selected = 0

    def close(self) -> None:
        if self.player is not None:
            self.player.menu_option = False
            setattr(self.player, "_dialogue_lock", False)

    def update(self) -> None:
        self._draw()

    def check_inputs(self) -> None:
        kl = self.keylistener
        c = self.controller

        n = len(self.LABELS[self.lang])
        if kl.key_pressed(c.get_key("up")):
            self.selected = (self.selected - 1) % n
            kl.remove_key(c.get_key("up"))
        elif kl.key_pressed(c.get_key("down")):
            self.selected = (self.selected + 1) % n
            kl.remove_key(c.get_key("down"))
        elif kl.key_pressed(c.get_key("action")):
            self._activate()
            kl.remove_key(c.get_key("action"))
        elif kl.key_pressed(c.get_key("menu")):
            self.close()
            kl.remove_key(c.get_key("menu"))

    def _activate(self) -> None:
        labels = self.LABELS[self.lang]
        choice = labels[self.selected]
        if choice in ("Continuer", "Resume"):
            self.close()
        elif choice in ("Sauvegarder", "Save"):
            if self.save:
                self.save.save()
            self.close()
        elif choice in ("Règles de société", "Society rules"):
            from pokemon_game.systems.society import SOCIETY_RULES
            pages = [{"name": "Société", "text": r} for r in SOCIETY_RULES]
            if hasattr(self.dialogue, "load_pages"):
                self.dialogue.load_pages(pages)
            self.close()
        elif choice in ("Quitter", "Quit"):
            pygame.event.post(pygame.event.Event(pygame.QUIT))

    def _draw(self) -> None:
        display = self.screen.get_display()
        if display is None or self._panel is None:
            return

        # Overlay sombre
        overlay = pygame.Surface(display.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        display.blit(overlay, (0, 0))

        sw, sh = display.get_size()
        pw, ph = self._panel.get_size()
        px = (sw - pw) // 2
        py = (sh - ph) // 2
        display.blit(self._panel, (px, py))

        labels = self.LABELS[self.lang]
        title = "Menu" if self.lang == "en" else "Menu"
        if self._font_title:
            tsurf = self._font_title.render(title, True, (255, 220, 80))
            display.blit(tsurf, (px + (pw - tsurf.get_width()) // 2, py + 24))

        if self._font:
            for i, label in enumerate(labels):
                color = (255, 255, 100) if i == self.selected else (220, 220, 220)
                prefix = "▶ " if i == self.selected else "  "
                surf = self._font.render(f"{prefix}{label}", True, color)
                display.blit(surf, (px + 60, py + 90 + i * 48))

            hint = "Z/S · E" if self.lang == "fr" else "Z/S · E"
            hsurf = self._font.render(hint, True, (140, 140, 160))
            display.blit(hsurf, (px + (pw - hsurf.get_width()) // 2, py + ph - 40))
