"""Options / menu system (stub)."""
from __future__ import annotations


class Option:
    def __init__(self, screen, controller, map_obj, lang, save, keylistener, dialogue) -> None:
        self.screen = screen
        self.controller = controller
        self.map = map_obj
        self.lang = lang
        self.save = save
        self.keylistener = keylistener
        self.dialogue = dialogue

    def update(self) -> None:
        pass

    def check_inputs(self) -> None:
        pass
