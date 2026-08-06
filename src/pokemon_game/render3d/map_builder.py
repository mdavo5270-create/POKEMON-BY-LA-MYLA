"""Build 3D map visuals from WorldGrid + baked TMX texture."""
from __future__ import annotations

from ursina import Entity, color, destroy, load_texture

from pokemon_game.core.tool import ASSETS
from pokemon_game.render3d.player3d import Player3D
from pokemon_game.render3d.textures import bake_map_texture
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
    world_w, world_h = w * ts, h * ts

    baked = bake_map_texture(map_name)
    if baked and baked.exists():
        ground = Entity(
            model="plane",
            scale=(world_w, 1, world_h),
            color=color.white,
            texture=load_texture(str(baked)),
            texture_scale=(1, 1),
            collider="box",
            position=(world_w / 2, 0, world_h / 2),
        )
        game.tiles.append(ground)
        print(f"[3D] Sol = texture baked {baked.name}")
    else:
        tex_name = "grass.png" if is_outdoor else "floor_interior.png"
        tex_path = ASSETS / "render3d" / tex_name
        ground_tex = load_texture(str(tex_path)) if tex_path.exists() else "white_cube"
        ground = Entity(
            model="plane",
            scale=(world_w, 1, world_h),
            color=color.white if tex_path.exists() else color.rgb(55, 130, 65),
            texture=ground_tex,
            texture_scale=(max(w // 2, 1), max(h // 2, 1)),
            collider="box",
            position=(world_w / 2, 0, world_h / 2),
        )
        game.tiles.append(ground)

    if not baked:
        blocked = list(game.world.blocked)
        step = 1 if len(blocked) < 1200 else 2
        for gx, gy in blocked[::step]:
            wx, wz = game.world.grid_to_world(gx, gy)
            wall = Entity(
                model="cube",
                color=color.rgb(40, 100, 45) if is_outdoor else color.rgb(140, 120, 100),
                scale=(0.95 * step, 0.55 if is_outdoor else 1.4, 0.95 * step),
                position=(wx, 0.28 if is_outdoor else 0.7, wz),
                collider="box",
            )
            game.tiles.append(wall)

    for winfo in game.world.warps:
        gx, gy = winfo["gx"], winfo["gy"]
        target, port_w = winfo["target"], winfo["port"]
        wx, wz = game.world.grid_to_world(gx, gy)
        pad = Entity(
            model="cube",
            color=color.rgb(255, 230, 60),
            scale=(0.85, 0.08, 0.85),
            position=(wx, 0.05, wz),
        )
        beam = Entity(
            model="cube",
            color=color.rgba(255, 240, 100, 60),
            scale=(0.4, 1.2, 0.4),
            position=(wx, 0.7, wz),
        )
        game.tiles.extend([pad, beam])
        game._warp_pads.append((pad, target, port_w))
        if is_outdoor and not target.startswith("map"):
            col = BUILDING_COLORS.get(target, color.rgb(160, 140, 120))
            flag = Entity(
                model="cube",
                color=col,
                scale=(0.35, 2.5, 0.35),
                position=(wx, 1.4, wz - 1.2),
            )
            game.tiles.append(flag)

    spawn_pos = None
    for key, pos in game.world.spawns.items():
        if str(port) in key.split() or spawn_pos is None:
            spawn_pos = pos
    if spawn_pos is None:
        spawn_pos = game.world.grid_to_world(w // 2, h // 2)
    sx, sz = spawn_pos
    game.player = Player3D(game.world, position=(sx, 0.0, sz))
    print(f"[3D] Map {map_name} blocked={len(game.world.blocked)} warps={len(game.world.warps)}")
