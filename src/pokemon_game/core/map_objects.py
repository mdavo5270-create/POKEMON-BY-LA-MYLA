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
        obj_type = (
            getattr(obj, "type", None) or getattr(obj, "class", None) or ""
        ).strip().lower()
        props = dict(obj.properties) if hasattr(obj, "properties") else {}

        # Fallback: deduce type from name prefix
        if not obj_type and name:
            first = name.split(" ")[0].lower()
            obj_type = first

        rect = pygame.Rect(
            int(obj.x), int(obj.y), int(obj.width or 16), int(obj.height or 16)
        )
        name_low = name.lower()

        # --- Collisions ---
        if (
            obj_type == "collision"
            or name_low == "collision"
            or name_low.startswith("collision")
        ):
            result.collisions.append(rect)
            continue

        # --- Spawns (AVANT les switches : "spawn house_0 0" contient "house_") ---
        if obj_type == "spawn" or name_low.startswith("spawn"):
            result.spawns[name] = pygame.math.Vector2(obj.x, obj.y)
            continue

        # --- Switches / Warps ---
        is_switch = (
            obj_type in ("switch", "warp", "door", "teleport", "passage")
            or name_low.startswith("switch")
            or name_low.startswith("warp")
            or name_low.startswith("door")
            or "map_" in name_low
            or "house_" in name_low
            or "labo" in name_low
            or "pokecenter" in name_low
            or "pokeshop" in name_low
            or "inter_" in name_low
        )

        if is_switch:
            parts = name.split()
            map_name = props.get("map_target") or props.get("map") or props.get("target")
            port = props.get("port", props.get("spawn", 0))

            if map_name is None:
                if len(parts) >= 3 and parts[0].lower() in ("switch", "warp", "door"):
                    map_name = parts[1]
                    try:
                        port = int(parts[2])
                    except ValueError:
                        port = 0
                elif len(parts) >= 2:
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
                map_name = (
                    str(map_name).replace("switch", "").replace("warp", "").strip()
                )
                # Ne jamais enregistrer un switch nommé "spawn"
                if map_name.lower() == "spawn":
                    continue
                try:
                    port = int(port)
                except (ValueError, TypeError):
                    port = 0
                result.switches.append(Switch("switch", map_name, rect, port))
            continue

        # --- Dialogues ---
        if obj_type == "dialogue" or name_low.startswith("dialogue"):
            dialogue_id = props.get("dialogue_id")
            if dialogue_id is None and len(name.split()) > 1:
                try:
                    dialogue_id = int(name.split()[1])
                except ValueError:
                    dialogue_id = 0
            result.dialogues.append(
                {"id": dialogue_id, "rect": rect, "properties": props}
            )
            continue

        # --- NPCs ---
        if obj_type == "npc" or name_low.startswith("npc"):
            result.npcs.append(
                {"name": name, "rect": rect, "properties": props}
            )
            continue

        # --- Triggers / items ---
        if obj_type in ("trigger", "item", "event"):
            result.triggers.append(
                {
                    "type": obj_type,
                    "name": name,
                    "rect": rect,
                    "properties": props,
                }
            )
            continue

        # --- Stairs ---
        if obj_type == "stairs" or name_low.startswith("stairs"):
            key = name.split()[-1] if " " in name else name
            result.stairs[key] = rect

    print(
        f"[MAP_OBJECTS] collisions={len(result.collisions)}  "
        f"switches={len(result.switches)}  "
        f"spawns={len(result.spawns)}  dialogues={len(result.dialogues)}"
    )
    for s in result.switches:
        print(f"             switch → {s.name} port={s.port}")

    return result
