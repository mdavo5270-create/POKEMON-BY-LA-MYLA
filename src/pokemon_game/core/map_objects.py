"""Helpers for standardized Tiled Object Layers.

Convention (see docs/TILED_WORKFLOW.md):
- collision  → name="collision"  type="collision"
- switch     → name="switch <map> <port>"  type="switch"
- spawn      → name="spawn <from_map> <port>"  type="spawn"
- dialogue   → name="dialogue <id>"  type="dialogue"
- npc        → name="npc <id>"  type="npc"
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pygame
import pytmx

from pokemon_game.core.switch import Switch


@dataclass
class MapObjects:
    """Container for all parsed objects of a map."""
    collisions: list[pygame.Rect] = field(default_factory=list)
    switches: list[Switch] = field(default_factory=list)
    spawns: dict[str, pygame.math.Vector2] = field(default_factory=dict)
    dialogues: list[dict[str, Any]] = field(default_factory=list)
    npcs: list[dict[str, Any]] = field(default_factory=list)
    triggers: list[dict[str, Any]] = field(default_factory=list)
    stairs: dict[str, pygame.Rect] = field(default_factory=dict)


def parse_objects(tmx_data: pytmx.TiledMap) -> MapObjects:
    """Parse all objects from a Tiled map using the project naming convention."""
    result = MapObjects()

    for obj in tmx_data.objects:
        name = (obj.name or "").strip()
        obj_type = (getattr(obj, "type", None) or "").strip().lower()

        # Fallback: deduce type from name prefix
        if not obj_type and name:
            obj_type = name.split(" ")[0].lower()

        rect = pygame.Rect(obj.x, obj.y, obj.width or 16, obj.height or 16)
        props = dict(obj.properties) if hasattr(obj, "properties") else {}

        if obj_type == "collision" or name == "collision":
            result.collisions.append(rect)

        elif obj_type == "switch" or name.startswith("switch "):
            parts = name.split()
            # Expected: switch <map_name> <port>
            if len(parts) >= 3:
                map_name = parts[1]
                try:
                    port = int(parts[-1])
                except ValueError:
                    port = 0
                result.switches.append(Switch("switch", map_name, rect, port))
            else:
                # Use properties if available
                map_name = props.get("map_target", parts[1] if len(parts) > 1 else "map_0")
                port = int(props.get("port", 0))
                result.switches.append(Switch("switch", map_name, rect, port))

        elif obj_type == "spawn" or name.startswith("spawn "):
            parts = name.split()
            key = name  # keep full name as key
            result.spawns[key] = pygame.math.Vector2(obj.x, obj.y)

        elif obj_type == "dialogue" or name.startswith("dialogue "):
            dialogue_id = props.get("dialogue_id")
            if dialogue_id is None and len(name.split()) > 1:
                try:
                    dialogue_id = int(name.split()[1])
                except ValueError:
                    dialogue_id = 0
            result.dialogues.append({
                "id": dialogue_id,
                "rect": rect,
                "properties": props,
            })

        elif obj_type == "npc" or name.startswith("npc "):
            result.npcs.append({
                "name": name,
                "rect": rect,
                "properties": props,
            })

        elif obj_type in ("trigger", "item", "warp"):
            result.triggers.append({
                "type": obj_type,
                "name": name,
                "rect": rect,
                "properties": props,
            })

        elif obj_type == "stairs" or name.startswith("stairs "):
            key = name.split()[-1] if " " in name else name
            result.stairs[key] = rect

    return result
