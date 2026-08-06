"""Build a simple 3D overworld from TMX collision data (grid of tiles)."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import pytmx


@dataclass
class WorldGrid:
    """Logical grid: walkable cells + building markers."""

    width: int
    height: int
    tile_size: float = 1.0
    blocked: set[tuple[int, int]] = field(default_factory=set)
    warps: list[dict] = field(default_factory=list)
    spawns: dict[str, tuple[float, float]] = field(default_factory=dict)
    name: str = "map_0"

    def is_blocked(self, gx: int, gy: int) -> bool:
        if gx < 0 or gy < 0 or gx >= self.width or gy >= self.height:
            return True
        return (gx, gy) in self.blocked

    def world_to_grid(self, x: float, z: float) -> tuple[int, int]:
        return int(x // self.tile_size), int(z // self.tile_size)

    def grid_to_world(self, gx: int, gy: int) -> tuple[float, float]:
        return (gx + 0.5) * self.tile_size, (gy + 0.5) * self.tile_size


def load_world_from_tmx(path: Path, map_name: str = "map_0") -> WorldGrid:
    """Parse TMX: block cells that intersect collision objects; collect switches."""
    tmx = pytmx.TiledMap(str(path))
    tw = float(tmx.tilewidth or 16)
    th = float(tmx.tileheight or 16)
    scale = 1.0
    grid = WorldGrid(
        width=int(tmx.width),
        height=int(tmx.height),
        tile_size=scale,
        name=map_name,
    )

    def cell_range(x: float, y: float, w: float, h: float) -> Iterable[tuple[int, int]]:
        x0 = int(x // tw)
        y0 = int(y // th)
        x1 = int((x + max(w, 1) - 1) // tw)
        y1 = int((y + max(h, 1) - 1) // th)
        for gy in range(y0, y1 + 1):
            for gx in range(x0, x1 + 1):
                yield gx, gy

    for obj in tmx.objects or []:
        name = (obj.name or "").strip().lower()
        props = {k: v for k, v in (obj.properties or {}).items()}
        ox, oy = float(obj.x), float(obj.y)
        ow = float(getattr(obj, "width", tw) or tw)
        oh = float(getattr(obj, "height", th) or th)

        if name.startswith("collision") or props.get("type") == "collision" or name in (
            "wall",
            "solid",
        ):
            for gx, gy in cell_range(ox, oy, ow, oh):
                grid.blocked.add((gx, gy))
            continue

        if name.startswith("switch") or props.get("type") == "switch":
            parts = name.split()
            target = props.get("map") or props.get("target")
            port = props.get("port", None)
            if target is None and len(parts) >= 2:
                target = parts[1]
            if port is None and len(parts) >= 3:
                try:
                    port = int(parts[2])
                except ValueError:
                    port = 0
            target = str(target or "map_0").strip()
            port = int(port or 0)
            gx = int((ox + ow / 2) // tw)
            gy = int((oy + oh / 2) // th)
            grid.warps.append({"gx": gx, "gy": gy, "target": target, "port": port})
            continue

        if name.startswith("spawn"):
            key = name
            grid.spawns[key] = ((ox + ow / 2) / tw * scale, (oy + oh / 2) / th * scale)

    return grid
