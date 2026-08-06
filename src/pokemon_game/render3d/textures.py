"""Build 3D textures from existing 2D game assets (sprites + TMX bake)."""
from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

from pokemon_game.core.tool import ASSETS

_CACHE = ASSETS / "render3d"
_READY = False


def ensure_textures() -> Path:
    """Crop hero frames + grass/floor samples; call bake per-map separately."""
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
            for col in range(4):
                fr = hero.crop((col * fw, row * fh, col * fw + fw, row * fh + fh))
                fr = fr.resize((fw * 3, fh * 3), Image.NEAREST)
                fr.save(_CACHE / f"hero_{name}_{col}.png")
                if col == 0:
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
        from PIL import Image as _I

        _I.open(poke).convert("RGBA").resize((128, 128), Image.NEAREST).save(
            _CACHE / "poke_icon.png"
        )

    _READY = True
    print("[3D] Textures base generees ->", _CACHE)
    return _CACHE


def _load_tileset_images(tmx_root) -> list:
    from PIL import Image

    result = []
    base = ASSETS / "map"
    for ts in tmx_root.findall("tileset"):
        first = int(ts.attrib.get("firstgid", 1))
        src = ts.attrib.get("source")
        if not src:
            continue
        tsx_path = (base / src).resolve()
        if not tsx_path.exists():
            continue
        tsx = ET.parse(tsx_path).getroot()
        cols = int(tsx.attrib.get("columns", 8))
        tw = int(tsx.attrib.get("tilewidth", 16))
        th = int(tsx.attrib.get("tileheight", 16))
        img_el = tsx.find("image")
        if img_el is None:
            continue
        img_path = tsx_path.parent / img_el.attrib["source"]
        if not img_path.exists():
            continue
        result.append((first, Image.open(img_path).convert("RGBA"), cols, tw, th))
    result.sort(key=lambda x: x[0], reverse=True)
    return result


def _gid_to_tile(gid: int, tilesets):
    if gid <= 0:
        return None
    gid = gid & 0x1FFFFFFF
    for first, img, cols, tw, th in tilesets:
        if gid >= first:
            local = gid - first
            sx = (local % cols) * tw
            sy = (local // cols) * th
            if sx + tw > img.width or sy + th > img.height:
                return None
            return img.crop((sx, sy, sx + tw, sy + th))
    return None


def bake_map_texture(map_name: str, scale: int = 1):
    """Composite Tiled layers into a single ground texture for 3D."""
    from PIL import Image

    ensure_textures()
    tmx_path = ASSETS / "map" / f"{map_name}.tmx"
    if not tmx_path.exists():
        return None
    out = _CACHE / f"baked_{map_name}.png"
    if out.exists() and out.stat().st_mtime >= tmx_path.stat().st_mtime:
        return out

    root = ET.parse(tmx_path).getroot()
    mw = int(root.attrib["width"])
    mh = int(root.attrib["height"])
    tw = int(root.attrib["tilewidth"])
    th = int(root.attrib["tileheight"])
    tilesets = _load_tileset_images(root)
    if not tilesets:
        return None

    canvas = Image.new("RGBA", (mw * tw, mh * th), (40, 90, 50, 255))
    skip = {"player", "entity"}
    for layer in root.iter("layer"):
        name = (layer.attrib.get("name") or "").lower()
        if name in skip:
            continue
        data = layer.find("data")
        if data is None or not (data.text or "").strip():
            continue
        raw = data.text.replace("\n", "").replace(" ", "")
        parts = [p for p in raw.split(",") if p != ""]
        try:
            gids = [int(p) for p in parts]
        except ValueError:
            continue
        if len(gids) < mw * mh:
            gids.extend([0] * (mw * mh - len(gids)))
        for i, gid in enumerate(gids[: mw * mh]):
            tile = _gid_to_tile(gid, tilesets)
            if tile is None:
                continue
            x = (i % mw) * tw
            y = (i // mw) * th
            canvas.alpha_composite(tile, (x, y))

    if scale != 1:
        canvas = canvas.resize(
            (canvas.width * scale, canvas.height * scale), Image.NEAREST
        )
    max_side = 2048
    if max(canvas.size) > max_side:
        ratio = max_side / max(canvas.size)
        canvas = canvas.resize(
            (int(canvas.width * ratio), int(canvas.height * ratio)), Image.NEAREST
        )
    canvas.save(out)
    print(f"[3D] Baked map texture {map_name} -> {out.name} {canvas.size}")
    return out
