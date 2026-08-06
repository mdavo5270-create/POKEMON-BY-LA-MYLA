"""Build 3D map visuals from WorldGrid."""
from __future__ import annotations

from ursina import Entity, color, destroy

from pokemon_game.core.tool import ASSETS
from pokemon_game.render3d.player3d import Player3D
from pokemon_game.render3d.world import load_world_from_tmx

BUILDING_COLORS = {
    "house_0": color.rgb(200, 160, 120),
    "house_1": color.rgb(180, 140, 100),
    "house_2": color.rgb(190, 150, 110),
    "pokecenter": color.rgb(240, 80, 80),
    "pokeshop": color.rgb(80, 140, 220),
    "labo_0": color.rgb(160, 160, 180),
    "inter_0": color.rgb(170, 150, 130),
}


def clear_tiles(tiles: list) -> None:
    for t in tiles:
        destroy(t)
    tiles.clear()


def build_world_entities(game, map_name: str, port: int = 0):
    """Populate game.tiles, game.world, game.player for map_name."""
    clear_tiles(game.tiles)
    game._warp_pads = []
    if game.player:
        destroy(game.player)
        game.player = None

    path = ASSETS / "map" / f"{map_name}.tmx"
    if not path.exists():
        print(f"[3D] Map manquante {map_name}, fallback map_0")
        path = ASSETS / "map" / "map_0.tmx"
        map_name = "map_0"
    game.map_name = map_name
    game.world = load_world_from_tmx(path, map_name)

    w, h = game.world.width, game.world.height
    ts = game.world.tile_size
    is_outdoor = map_name.startswith("map")
    ground_col = color.rgb(55, 130, 65) if is_outdoor else color.rgb(120, 100, 80)
    ground = Entity(
        model="plane",
        scale=(w * ts, 1, h * ts),
        color=ground_col,
        texture="white_cube",
        texture_scale=(w, h),
        collider="box",
        position=(w * ts / 2, 0, h * ts / 2),
    )
    game.tiles.append(ground)

    blocked = list(game.world.blocked)
    step = 1 if len(blocked) < 1200 else 2
    for gx, gy in blocked[::step]:
        wx, wz = game.world.grid_to_world(gx, gy)
        wall = Entity(
            model="cube",
            color=color.rgb(85, 85, 90) if is_outdoor else color.rgb(100, 90, 80),
            scale=(0.95 * step, 1.1, 0.95 * step),
            position=(wx, 0.55, wz),
            collider="box",
        )
        game.tiles.append(wall)

    for winfo in game.world.warps:
        gx, gy = winfo["gx"], winfo["gy"]
        target, port_w = winfo["target"], winfo["port"]
        wx, wz = game.world.grid_to_world(gx, gy)
        pad = Entity(
            model="cube",
            color=color.rgb(255, 220, 40),
            scale=(0.95, 0.1, 0.95),
            position=(wx, 0.06, wz),
        )
        game.tiles.append(pad)
        game._warp_pads.append((pad, target, port_w))
        if is_outdoor and not target.startswith("map"):
            col = BUILDING_COLORS.get(target, color.rgb(160, 140, 120))
            building = Entity(
                model="cube", color=col, scale=(2.2, 2.0, 2.2),
                position=(wx, 1.0, wz - 1.5),
            )
            roof = Entity(
                model="cube", color=color.rgb(140, 50, 50), scale=(2.5, 0.35, 2.5),
                position=(wx, 2.15, wz - 1.5),
            )
            game.tiles.extend([building, roof])

    spawn_pos = None
    for key, pos in game.world.spawns.items():
        if str(port) in key.split() or spawn_pos is None:
            spawn_pos = pos
    if spawn_pos is None:
        spawn_pos = game.world.grid_to_world(w // 2, h // 2)
    sx, sz = spawn_pos
    game.player = Player3D(game.world, position=(sx, 0.0, sz))
    print(f"[3D] Map {map_name} blocked={len(game.world.blocked)} warps={len(game.world.warps)}")
