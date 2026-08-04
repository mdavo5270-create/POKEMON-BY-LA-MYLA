"""Player entity - sprite robuste + switches prioritaires + debug."""
from __future__ import annotations
import pygame
from pathlib import Path
from pokemon_game.entities.entity import Entity
from pokemon_game.core.screen import Screen
from pokemon_game.core.controller import Controller
from pokemon_game.core.keylistener import KeyListener
from pokemon_game.core.tool import asset_path, Tool, ASSETS
from pokemon_game.core.switch import Switch


class Player(Entity):
    def __init__(
        self,
        screen: Screen,
        controller: Controller,
        x: float,
        y: float,
        keylistener: KeyListener,
    ) -> None:
        super().__init__(x, y)
        self.screen = screen
        self.controller = controller
        self.keylistener = keylistener
        self.menu_option = False
        self.collisions: list[pygame.Rect] = []
        self.switchs: list[Switch] = []
        self.speed = 1
        self.on_bike = False
        self.animation_index = 0
        self.animation_timer = 0
        self.animation_speed = 8
        self.pending_switch: Switch | None = None

        self._load_sprites()
        self.rect = self.image.get_rect(topleft=(x, y))
        self.align_hitbox()

    def _load_sprites(self) -> None:
        """Charge le spritesheet avec plusieurs chemins possibles + debug."""
        candidates = [
            asset_path("sprite", "hero_01_red_m_walk.png"),
            asset_path("sprites", "hero_01_red_m_walk.png"),
            asset_path("sprite", "player.png"),
            asset_path("sprite", "hero.png"),
            str(ASSETS / "sprite" / "hero_01_red_m_walk.png"),
        ]

        # Cherche aussi récursivement dans assets/
        sprite_dir = ASSETS / "sprite"
        if sprite_dir.exists():
            for p in sprite_dir.rglob("*.png"):
                if "hero" in p.name.lower() or "red" in p.name.lower() or "walk" in p.name.lower():
                    candidates.append(str(p))

        sheet = None
        used_path = None
        for path in candidates:
            if Path(path).exists():
                try:
                    sheet = pygame.image.load(path).convert_alpha()
                    used_path = path
                    break
                except Exception as e:
                    print(f"[SPRITE] Échec chargement {path}: {e}")

        if sheet is None:
            print("[SPRITE] AUCUN spritesheet trouvé ! Fallback rouge.")
            print(f"[SPRITE] Dossier assets = {ASSETS}")
            if (ASSETS / "sprite").exists():
                print(f"[SPRITE] Fichiers dans assets/sprite : {[p.name for p in (ASSETS / 'sprite').iterdir()]}")
            else:
                print("[SPRITE] Le dossier assets/sprite n'existe pas.")
            dummy = pygame.Surface((16, 24), pygame.SRCALPHA)
            dummy.fill((220, 40, 40))
            self.images = {d: [dummy] * 4 for d in ("down", "left", "right", "up")}
            self.image = dummy
            return

        w, h = sheet.get_size()
        print(f"[SPRITE] Chargé : {used_path} ({w}x{h})")

        # Essai de layouts courants (16x24 par frame)
        layouts = [
            # rows = directions (down, left, right, up), cols = frames
            {"fw": 16, "fh": 24, "order": ["down", "left", "right", "up"]},
            {"fw": 16, "fh": 24, "order": ["down", "up", "left", "right"]},
            {"fw": 16, "fh": 32, "order": ["down", "left", "right", "up"]},
            {"fw": 32, "fh": 32, "order": ["down", "left", "right", "up"]},
        ]

        self.images = {}
        loaded = False
        for layout in layouts:
            fw, fh = layout["fw"], layout["fh"]
            order = layout["order"]
            if w >= fw * 3 and h >= fh * 3:  # au moins 3 frames x 3 dirs
                try:
                    for row, direction in enumerate(order):
                        frames = []
                        for col in range(min(4, w // fw)):
                            frames.append(Tool.split_image(sheet, col * fw, row * fh, fw, fh))
                        if frames:
                            self.images[direction] = frames
                    if len(self.images) >= 4:
                        loaded = True
                        print(f"[SPRITE] Layout utilisé : {fw}x{fh} order={order}")
                        break
                except Exception:
                    self.images = {}
                    continue

        if not loaded:
            # Dernier recours : prendre juste le coin haut-gauche
            print("[SPRITE] Layout non reconnu, utilisation de la première frame uniquement.")
            frame = Tool.split_image(sheet, 0, 0, min(16, w), min(24, h))
            self.images = {d: [frame] * 4 for d in ("down", "left", "right", "up")}

        self.image = self.images.get("down", list(self.images.values())[0])[0]

    def add_collisions(self, collisions: list) -> None:
        self.collisions = collisions or []

    def add_switchs(self, switchs: list) -> None:
        # Ignore les faux switches nommés "spawn" (ce sont des points d'apparition, pas des téléports)
        self.switchs = [s for s in (switchs or []) if s.name.lower() != "spawn"]
        print(f"[SWITCH] {len(self.switchs)} switch(es) chargés pour le joueur (spawn exclus)")
        for s in self.switchs:
            print(f"         → {s.name} port={s.port} rect={s.hitbox}")

    def switch_bike(self, force: bool | None = None) -> None:
        if force is not None:
            self.on_bike = force
        else:
            self.on_bike = not self.on_bike
        self.speed = 2 if self.on_bike else 1

    def update(self, *args, **kwargs) -> None:
        self.handle_input()
        self._animate()
        super().update()

    def _animate(self) -> None:
        moving = any(
            self.keylistener.key_pressed(self.controller.get_key(k))
            for k in ("up", "down", "left", "right")
        )
        if moving:
            self.animation_timer += 1
            if self.animation_timer >= self.animation_speed:
                self.animation_timer = 0
                frames = self.images.get(self.direction, self.images.get("down", [self.image]))
                self.animation_index = (self.animation_index + 1) % len(frames)
        else:
            self.animation_index = 0

        frames = self.images.get(self.direction, self.images.get("down", [self.image]))
        self.image = frames[self.animation_index % len(frames)]

    def handle_input(self) -> None:
        dx = dy = 0
        kl = self.keylistener
        c = self.controller

        if kl.key_pressed(c.get_key("up")):
            dy = -self.speed
            self.direction = "up"
        elif kl.key_pressed(c.get_key("down")):
            dy = self.speed
            self.direction = "down"
        elif kl.key_pressed(c.get_key("left")):
            dx = -self.speed
            self.direction = "left"
        elif kl.key_pressed(c.get_key("right")):
            dx = self.speed
            self.direction = "right"

        if not (dx or dy):
            return

        test = self.hitbox.move(dx, dy)

        # 1) SWITCHES : déclenche uniquement si on ENTRE dans le switch
        #    (collision sur la position future, pas sur la position actuelle).
        #    Ça évite le blocage total quand le spawn est pile sur un switch,
        #    et permet de sortir d'une zone de téléportation.
        for switch in self.switchs:
            if switch.check_collision(test) and not switch.check_collision(self.hitbox):
                self.pending_switch = switch
                return

        # 2) Collisions murs
        if any(test.colliderect(col) for col in self.collisions):
            return

        # 3) Mouvement OK
        self.position += pygame.math.Vector2(dx, dy)
