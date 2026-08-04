"""Dialogue system — load CSV, render message box, multi-page / action to advance.

Format CSV attendu (assets/dialogues/<id>.csv) :
  en,fr
  "texte anglais","texte français"
  ...

Tags supportés dans le texte (simplifiés) :
  :[name=XXX;face=YYY]:  → affiche le nom du locuteur
  [WAIT N]               → pause (ignorée pour l'instant, texte collé)
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

import pygame

from pokemon_game.core.tool import asset_path

# Match :[name=XXX;...] :  — group(1) = speaker name
_NAME_RE = re.compile(r":\[name=([^;\]]+)(?:;[^\]]*)?\]:")
_WAIT_RE = re.compile(r"\[WAIT\s+\d+\]")


class Dialogue:
    def __init__(self, player, screen, lang: str = "fr") -> None:
        self.player = player
        self.screen = screen
        self.lang = lang  # "fr" | "en"
        self.active = False
        self.pages: list[dict] = []  # {"name": str|None, "text": str}
        self.page_index = 0
        self._box: pygame.Surface | None = None
        self._name_box: pygame.Surface | None = None
        self._font: pygame.font.Font | None = None
        self._font_name: pygame.font.Font | None = None
        self._load_assets()

    def _load_assets(self) -> None:
        try:
            self._box = pygame.image.load(
                asset_path("interfaces", "dialogues", "message_box_0.png")
            ).convert_alpha()
        except Exception:
            self._box = pygame.Surface((600, 120), pygame.SRCALPHA)
            self._box.fill((20, 20, 40, 220))
            pygame.draw.rect(self._box, (255, 255, 255), self._box.get_rect(), 3)

        try:
            self._name_box = pygame.image.load(
                asset_path("interfaces", "dialogues", "name_box_0.png")
            ).convert_alpha()
        except Exception:
            self._name_box = pygame.Surface((180, 32), pygame.SRCALPHA)
            self._name_box.fill((40, 40, 80, 230))

        # Scale boxes for 1280×720
        self._box = pygame.transform.scale(self._box, (720, 140))
        self._name_box = pygame.transform.scale(self._name_box, (220, 40))

        try:
            font_path = asset_path("fonts", "pokemon.ttf")
            if not Path(font_path).exists():
                font_path = asset_path("fonts", "Roboto-Regular.ttf")
            self._font = pygame.font.Font(font_path if Path(font_path).exists() else None, 22)
            self._font_name = pygame.font.Font(
                font_path if Path(font_path).exists() else None, 20
            )
        except Exception:
            self._font = pygame.font.SysFont(None, 24)
            self._font_name = pygame.font.SysFont(None, 22)

    def load_data(self, dialogue_id: int, index: int = 0) -> None:
        """Charge un fichier CSV de dialogue et active l'affichage."""
        path = Path(asset_path("dialogues", f"{dialogue_id}.csv"))
        self.pages = []
        self.page_index = max(0, index)

        if not path.exists():
            self.pages = [{"name": None, "text": f"[Dialogue {dialogue_id} manquant]"}]
            self.active = True
            return

        try:
            with path.open(encoding="utf-8") as f:
                reader = csv.DictReader(f)
                col = self.lang if self.lang in (reader.fieldnames or []) else "fr"
                if col not in (reader.fieldnames or ["fr"]):
                    col = (reader.fieldnames or ["fr"])[0]
                for row in reader:
                    raw = (row.get(col) or "").strip()
                    if not raw:
                        continue
                    name, text = self._parse_line(raw)
                    self.pages.append({"name": name, "text": text})
        except Exception as e:
            print(f"[DIALOGUE] Erreur lecture {path}: {e}")
            self.pages = [{"name": None, "text": f"Erreur dialogue {dialogue_id}"}]

        if not self.pages:
            self.pages = [{"name": None, "text": "..."}]

        self.page_index = min(self.page_index, len(self.pages) - 1)
        self.active = True
        if self.player is not None:
            setattr(self.player, "_dialogue_lock", True)

    def _parse_line(self, raw: str) -> tuple[str | None, str]:
        name = None
        m = _NAME_RE.search(raw)
        if m:
            name = m.group(1).strip()
            raw = _NAME_RE.sub("", raw, count=1)
        text = _WAIT_RE.sub("", raw).strip()
        return name, text

    def update(self) -> None:
        if not self.active:
            return
        self._draw()

    def action(self) -> None:
        """Avance d'une page ou ferme le dialogue."""
        if not self.active:
            return
        self.page_index += 1
        if self.page_index >= len(self.pages):
            self.close()

    def close(self) -> None:
        self.active = False
        self.pages = []
        self.page_index = 0
        if self.player is not None:
            setattr(self.player, "_dialogue_lock", False)

    def _draw(self) -> None:
        display = self.screen.get_display()
        if display is None or not self.pages:
            return

        page = self.pages[self.page_index]
        box = self._box
        assert box is not None

        bw, bh = box.get_size()
        sw, sh = display.get_size()
        bx = (sw - bw) // 2
        by = sh - bh - 40

        display.blit(box, (bx, by))

        if page.get("name") and self._name_box and self._font_name:
            nb = self._name_box
            display.blit(nb, (bx + 20, by - 28))
            name_surf = self._font_name.render(str(page["name"]), True, (255, 255, 255))
            display.blit(name_surf, (bx + 32, by - 22))

        if self._font:
            text = page.get("text") or ""
            lines = self._wrap(text, bw - 48)
            y = by + 24
            for line in lines[:5]:
                surf = self._font.render(line, True, (30, 30, 30))
                display.blit(surf, (bx + 24, y))
                y += 26

            hint = "▼" if self.page_index < len(self.pages) - 1 else "×"
            hint_surf = self._font.render(hint, True, (80, 80, 80))
            display.blit(hint_surf, (bx + bw - 36, by + bh - 32))

    def _wrap(self, text: str, max_width: int) -> list[str]:
        if not self._font:
            return [text]
        words = text.split()
        lines: list[str] = []
        current = ""
        for w in words:
            test = f"{current} {w}".strip()
            if self._font.size(test)[0] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = w
        if current:
            lines.append(current)
        return lines or [""]
