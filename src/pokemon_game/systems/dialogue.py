"""Dialogue system (stub - to be expanded)."""
from __future__ import annotations


class Dialogue:
    def __init__(self, player, screen) -> None:
        self.player = player
        self.screen = screen
        self.active = False
        self.data = None

    def load_data(self, dialogue_id: int, index: int = 0) -> None:
        self.active = True
        self.data = {"id": dialogue_id, "index": index}

    def update(self) -> None:
        pass

    def action(self) -> None:
        self.active = False
