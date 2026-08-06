"""Ursina application entry - 3D overworld + battle."""
from __future__ import annotations

from ursina import (
    Ursina,
    Sky,
    DirectionalLight,
    AmbientLight,
    color,
    Text,
    window,
    application,
    mouse,
    Entity,
)

from pokemon_game.render3d.game3d import Game3D


def run_app() -> None:
    app = Ursina(
        title="POKEMON BY LA MYLA - 3D",
        borderless=False,
        fullscreen=False,
        development_mode=False,
        vsync=True,
    )
    window.color = color.rgb(30, 40, 55)
    Sky(color=color.rgb(120, 180, 255))
    DirectionalLight(direction=(0.5, -1, -0.3), shadows=True)
    AmbientLight(color=color.rgba(130, 130, 150, 0.65))

    game = Game3D()
    game.status_text = Text(
        text="POKEMON 3D",
        position=(-0.85, 0.45),
        scale=1.0,
        background=True,
    )
    game.hint_text = Text(
        text="Chargement...",
        position=(-0.85, -0.45),
        scale=0.9,
        background=True,
    )
    game.build_map("map_0")
    mouse.locked = False

    def on_key(key: str) -> None:
        if game.battle and game.battle.active:
            game.battle.on_key(key)
            if key == "escape":
                game.battle.result = "ran"
                game.battle.active = False
                game.end_battle("ran")
            return

        if key == "escape":
            application.quit()
        elif key == "f5":
            game.save_game()
        elif key == "f6":
            game.heal_team()
        elif key in ("e", "space"):
            game.interact()
        elif key == "tab":
            maps = ["map_0", "map_1"]
            try:
                i = maps.index(game.map_name)
            except ValueError:
                i = 0
            game.build_map(maps[(i + 1) % len(maps)])

    class InputSink(Entity):
        def input(self, key):
            on_key(key)

        def update(self):
            game.update()

    InputSink()
    app.run()
