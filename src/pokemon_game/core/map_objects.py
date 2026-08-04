"""Helpers for standardized Tiled Object Layers.

Convention (see docs/TILED_WORKFLOW.md):
- collision  → name="collision"  type="collision"
- switch     → name="switch <map> <port>"  type="switch"
- spawn      → name="spawn <from_map> <port>"  type="spawn"
- dialogue   → name="dialogue <id>"  type="dialogue"
- npc        → name="npc <id>"  type="npc"

Compatible aussi avec les anciens nommages des EP (Arnaud Michel).
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
        obj_type = (getattr(obj, "type", None) or getattr(obj, "class", None) or "").strip().lower()
        props = dict(obj.properties) if hasattr(obj, "properties") else {}

        # Fallback: deduce type from name prefix
        if not obj_type and name:
            first = name.split(" ")[0].lower()
            obj_type = first

        rect = pygame.Rect(int(obj.x), int(obj.y), int(obj.width or 16), int(obj.height or 16))

        # --- Collisions ---
        if obj_type == "collision" or name.lower() == "collision" or name.lower().startswith("collision"):
            result.collisions.append(rect)
            continue

        # --- Switches / Warps (très tolérant) ---
        is_switch = (
            obj_type in ("switch", "warp", "door", "teleport", "passage")
            or name.lower().startswith("switch")
            or name.lower().startswith("warp")
            or name.lower().startswith("door")
            or "map_" in name.lower()
            or "house_" in name.lower()
            or "labo" in name.lower()
            or "pokecenter" in name.lower()
            or "pokeshop" in name.lower()
            or "inter_" in name.lower()
        )

        if is_switch:
            parts = name.split()
            map_name = props.get("map_target") or props.get("map") or props.get("target")
            port = props.get("port", props.get("spawn", 0))

            if map_name is None:
                # Formats : "switch house_0 0" / "house_0 0" / "switch map_1" / juste "house_0"
                if len(parts) >= 3 and parts[0].lower() in ("switch", "warp", "door"):
                    map_name = parts[1]
                    try:
                        port = int(parts[2])
                    except ValueError:
                        port = 0
                elif len(parts) >= 2:
                    # "house_0 0" ou "switch house_0"
                    if parts[0].lower() in ("switch", "warp", "door"):
                        map_name = parts[1]
                        port = 0
                    else:
                        map_name = parts[0]
                        try:
                            port = int(parts[1])
                        except ValueError:
                            port = 0
                elif len(parts) == 1 and parts[0]:
                    map_name = parts[0]
                    port = 0

            if map_name:
                # Nettoie le nom (enlève préfixe switch/warp si encore présent)
                map_name = str(map_name).replace("switch", "").replace("warp", "").strip()
                try:
                    port = int(port)
                except (ValueError, TypeError):
                    port = 0
                result.switches.append(Switch("switch", map_name, rect, port))
            continue

        # --- Spawns ---
        if obj_type == "spawn" or name.lower().startswith("spawn"):
            result.spawns[name] = pygame.math.Vector2(obj.x, obj.y)
            continue

        # --- Dialogues ---
        if obj_type == "dialogue" or name.lower().startswith("dialogue"):
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
            continue

        # --- NPCs ---
        if obj_type == "npc" or name.lower().startswith("npc"):
            result.npcs.append({
                "name": name,
                "rect": rect,
                "properties": props,
            })
            continue

        # --- Triggers / items ---
        if obj_type in ("trigger", "item", "event"):
            result.triggers.append({
                "type": obj_type,
                "name": name,
                "rect": rect,
                "properties": props,
            })
            continue

        # --- Stairs ---
        if obj_type == "stairs" or name.lower().startswith("stairs"):
            key = name.split()[-1] if " " in name else name
            result.stairs[key] = rect

    print(f"[MAP_OBJECTS] collisions={len(result.collisions)}  switches={len(result.switches)}  "
          f"spawns={len(result.spawns)}  dialogues={len(result.dialogues)}")
    for s in result.switches:
        print(f"             switch → {s.name} port={s.port}")

    return result
