"""Map management with Tiled + pyscroll — cache des maps + chargement robuste."""
from __future__ import annotations

from pathlib import Path

import pygame
import pyscroll
import pytmx

from pokemon_game.core.controller import Controller
from pokemon_game.core.map_objects import parse_objects
from pokemon_game.core.screen import Screen
from pokemon_game.core.switch import Switch
from pokemon_game.core.tool import Tool, asset_path
from pokemon_game.systems.furniture import get_furniture_rects, draw_furniture


class Map:
    """Map class to manage the map."""

    # Cache des TiledMap déjà chargés (évite de relire le .tmx à chaque switch)
    _tmx_cache: dict[str, pytmx.TiledMap] = {}

    def __init__(self, screen: Screen, controller: Controller) -> None:
        self.screen = screen
        self.controller = controller
        self.tmx_data: pytmx.TiledMap | None = None
        self.map_layer: pyscroll.BufferedRenderer | None = None
        self.group: pyscroll.PyscrollGroup | None = None

        self.player = None
        self.switchs: list[Switch] = []
        self.collisions: list[pygame.Rect] = []
        self.stairs: dict = {}
        self.dialogues: list = []
        self.npcs: list = []          # données Tiled (dicts)
        self.npc_entities: list = []  # sprites PNJ vivants
        self.triggers: list = []
        self.spawns: dict = {}

        self.current_map: Switch | None = None
        self.map_name: str | None = None
        self.map_name_text = None

        self.animation_change_map = 0
        self.animation_change_map_active = False
        try:
            self.image_change_map = pygame.image.load(
                asset_path("interfaces", "maps", "frame_map.png")
            ).convert_alpha()
        except Exception:
            self.image_change_map = pygame.Surface((215, 53), pygame.SRCALPHA)

    def _load_tmx(self, map_name: str) -> pytmx.TiledMap:
        """Charge un .tmx avec cache en mémoire."""
        if map_name in Map._tmx_cache:
            print(f"[MAP] Cache hit : {map_name}")
            return Map._tmx_cache[map_name]

        path = asset_path("map", f"{map_name}.tmx")
        if not Path(path).exists():
            raise FileNotFoundError(f"Map introuvable : {path}")

        tmx = pytmx.load_pygame(path)
        Map._tmx_cache[map_name] = tmx
        print(f"[MAP] Chargé & mis en cache : {map_name} ({tmx.width}×{tmx.height})")
        return tmx

    def switch_map(self, switch: Switch) -> None:
        if switch.name.lower() == "spawn":
            if self.player:
                self.pose_player(switch)
                self.player.step = 16
                self.player.pending_switch = None
            return

        self.tmx_data = self._load_tmx(switch.name)
        map_data = pyscroll.data.TiledMapData(self.tmx_data)
        # Taille = surface logique (pixel-art net)
        view_size = self.screen.get_size()
        self.map_layer = pyscroll.BufferedRenderer(
            map_data,
            view_size,
            clamp_camera=True,
            tall_sprites=1,
        )
        # Qualité : pas de flou sur les tiles
        try:
            self.map_layer.zoom = 1.0
        except Exception:
            pass
        self.group = pyscroll.PyscrollGroup(map_layer=self.map_layer, default_layer=9)
        self.animation_change_map = 0
        self.animation_change_map_active = False

        # Zoom adapté : outdoor un peu plus dézoomé, intérieur plus proche
        is_outdoor = switch.name.startswith("map")
        try:
            # Zoom net : outdoor lisible, intérieur plus proche (style HGSS/moderne)
            self.map_layer.zoom = 2.75 if is_outdoor else 3.5
        except Exception:
            pass
        if is_outdoor:
            self.set_draw_change_map(switch.name)
        print(f"[MAP] Rendu {switch.name} view={view_size} outdoor={is_outdoor}")

        parsed = parse_objects(self.tmx_data)
        self.switchs = parsed.switches
        self.collisions = parsed.collisions
        self.stairs = parsed.stairs
        self.dialogues = parsed.dialogues
        self.npcs = parsed.npcs
        self.triggers = parsed.triggers
        self.spawns = parsed.spawns

        # Mobilier intérieur (collisions)
        furn = get_furniture_rects(switch.name)
        if furn:
            self.collisions = list(self.collisions) + furn
            print(f"[MAP] {len(furn)} meuble(s) ajoutés dans {switch.name}")

        # Nettoyer anciens PNJ entities au changement de map
        for ent in getattr(self, "npc_entities", []) or []:
            if self.group and ent in self.group:
                self.group.remove(ent)
        self.npc_entities = []

        if self.player:
            self.pose_player(switch)
            self.player.align_hitbox()
            self.player.step = 16
            self.player.pending_switch = None
            self.player.add_switchs(self.switchs)
            self.player.add_collisions(self.collisions)
            self.group.add(self.player)
            if not is_outdoor and hasattr(self.player, "switch_bike"):
                self.player.switch_bike(force=False)

        self.current_map = switch
        self.map_name = switch.name

    def add_player(self, player) -> None:
        self.player = player
        if self.group:
            self.group.add(player)

    def add_npc(self, npc) -> None:
        """Ajoute une entité NPC (sprite) — PAS de collision solide (évite de bloquer le joueur)."""
        if not hasattr(self, "npc_entities"):
            self.npc_entities = []
        self.npc_entities.append(npc)
        if self.group:
            self.group.add(npc)
        # Pas d'ajout aux collisions : le joueur doit pouvoir marcher librement.
        # L'interaction se fait via hitbox dans Game._try_interact.
        print(f"[NPC] {getattr(npc, 'name', 'NPC')} @ ({npc.position.x:.0f}, {npc.position.y:.0f})")

    def update(self) -> None:
        if self.group and self.player:
            # Mettre à jour entités (joueur + PNJ)
            self.group.update(self.screen)
            # Caméra centrée joueur (clamp via BufferedRenderer)
            self.group.center(self.player.rect.center)
            display = self.screen.get_display()
            if display is not None:
                self.group.draw(display)
                # Mobilier
                if self.map_name:
                    try:
                        font = pygame.font.SysFont(None, 14)
                    except Exception:
                        font = None
                    draw_furniture(display, self.map_name, font)
                if (self.map_name or "").startswith("map"):
                    self._draw_ambient(display)
            if self.animation_change_map_active:
                self.draw_change_map()

    def _draw_ambient(self, display: pygame.Surface) -> None:
        """Bandeau d'ambiance haut (ciel) sans cacher le gameplay."""
        w = display.get_width()
        band = pygame.Surface((w, 28), pygame.SRCALPHA)
        for i in range(28):
            a = int(18 * (1 - i / 28))
            band.fill((120, 180, 255, a), (0, i, w, 1))
        display.blit(band, (0, 0))

    def pose_player(self, switch: Switch) -> None:
        """Place le joueur sur le bon spawn."""
        if not self.player or not self.tmx_data:
            return

        port_str = str(switch.port)

        for obj in self.tmx_data.objects:
            name = (obj.name or "").strip().lower()
            if name.startswith("spawn") and port_str in name.split():
                self.player.position = pygame.math.Vector2(obj.x, obj.y)
                print(f"[SPAWN] {name} → ({obj.x}, {obj.y})")
                return

        for key, pos in self.spawns.items():
            if port_str in key.split():
                self.player.position = pos
                print(f"[SPAWN] dict {key} → {pos}")
                return

        for obj in self.tmx_data.objects:
            name = (obj.name or "").strip().lower()
            if name.startswith("spawn"):
                self.player.position = pygame.math.Vector2(obj.x, obj.y)
                print(f"[SPAWN] fallback {name} → ({obj.x}, {obj.y})")
                return

        if self.tmx_data:
            cx = (self.tmx_data.width * self.tmx_data.tilewidth) // 2
            cy = (self.tmx_data.height * self.tmx_data.tileheight) // 2
            self.player.position = pygame.math.Vector2(cx, cy)
            print(f"[SPAWN] centre map → ({cx}, {cy})")

    def set_draw_change_map(self, map_name: str) -> None:
        if not self.animation_change_map_active:
            self.map_name = map_name
            self.animation_change_map_active = True
            self.animation_change_map = 0
            try:
                self.map_name_text = Tool.create_text(self.map_name, 30, (255, 255, 255))
            except Exception:
                self.map_name_text = pygame.Surface((10, 10))

    def get_surface_change_map(self, alpha: int = 0) -> pygame.Surface:
        surface = pygame.Surface((215, 53), pygame.SRCALPHA).convert_alpha()
        surface.blit(self.image_change_map, (0, 0))
        surface.set_alpha(alpha)
        return surface

    def draw_change_map(self) -> None:
        if self.animation_change_map < 255:
            surface = self.get_surface_change_map(self.animation_change_map)
            self.screen.display.blit(
                surface, (self.screen.display.get_width() - self.animation_change_map, 600)
            )
            self.animation_change_map += 5
        elif self.animation_change_map < 1024:
            surface = self.get_surface_change_map(255)
            if self.map_name_text:
                Tool.add_text_to_surface(
                    surface,
                    self.map_name_text,
                    surface.get_width() // 2 - self.map_name_text.get_width() // 2,
                    4,
                )
            self.screen.display.blit(
                surface, (self.screen.display.get_width() - 255, 600)
            )
            self.animation_change_map += 2
        elif self.animation_change_map < 1279:
            surface = self.get_surface_change_map(1279 - self.animation_change_map)
            if self.map_name_text:
                Tool.add_text_to_surface(
                    surface,
                    self.map_name_text,
                    surface.get_width() // 2 - self.map_name_text.get_width() // 2,
                    4,
                )
            self.screen.display.blit(
                surface, (self.screen.display.get_width() - 255, 600)
            )
            self.animation_change_map += 5
        else:
            self.animation_change_map_active = False
            self.animation_change_map = 0

    def load_map(self, map_name: str) -> None:
        self.switch_map(Switch("switch", map_name, pygame.Rect(0, 0, 0, 0), 0))
