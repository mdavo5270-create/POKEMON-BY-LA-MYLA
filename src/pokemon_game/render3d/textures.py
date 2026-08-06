"""Build 3D textures from existing 2D game assets (no extra binary pack)."""
from __future__ import annotations

from pathlib import Path

from pokemon_game.core.tool import ASSETS

_CACHE = ASSETS / "render3d"
_READY = False


def ensure_textures() -> Path:
    """Crop hero frames + grass/floor samples into assets/render3d/ once."""
    global _READY
    if _READY and (_CACHE / "hero_down.png").exists():
        return _CACHE
    try:
        from PIL import Image
    except ImportError:
        return _CACHE

    _CACHE.mkdir(parents=True, exist_ok=True)

    hero_path = ASSETS / "sprite" / "hero_01_red_m_walk.png"
    if hero_path.exists():
        hero = Image.open(hero_path).convert("RGBA")
        fw, fh = 25, 32
        for row, name in enumerate(["down", "left", "right", "up"]):
            fr = hero.crop((0, row * fh, fw, row * fh + fh))
            fr = fr.resize((fw * 3, fh * 3), Image.NEAREST)
            fr.save(_CACHE / f"hero_{name}.png")

    ts_path = ASSETS / "map" / "tileset" / "tileset_pokemon_sdk.png"
    if ts_path.exists():
        ts = Image.open(ts_path).convert("RGBA")
        best_y, best = 0, -1.0
        for y in range(0, min(2000, ts.height - 32), 16):
            c = ts.crop((0, y, 32, y + 32))
            px = list(c.getdata())
            if not px:
                continue
            g = sum(p[1] for p in px) / len(px)
            r = sum(p[0] for p in px) / len(px)
            if g > r and g > best:
                best, best_y = g, y
        tile = ts.crop((0, best_y, 32, best_y + 32)).resize((64, 64), Image.NEAREST)
        sheet = Image.new("RGBA", (256, 256))
        for y in range(0, 256, 64):
            for x in range(0, 256, 64):
                sheet.paste(tile, (x, y))
        sheet.save(_CACHE / "grass.png")

    inter = ASSETS / "map" / "tileset" / "TransparentHGSSRippedInterior.png"
    if inter.exists():
        im = Image.open(inter).convert("RGBA")
        im.crop((0, 0, min(128, im.width), min(128, im.height))).resize(
            (128, 128), Image.NEAREST
        ).save(_CACHE / "floor_interior.png")

    poke = ASSETS / "settings" / "pokemon.png"
    if poke.exists():
        Image.open(poke).convert("RGBA").resize((128, 128), Image.NEAREST).save(
            _CACHE / "poke_icon.png"
        )

    _READY = True
    print("[3D] Textures generees depuis assets 2D ->", _CACHE)
    return _CACHE
