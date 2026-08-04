"""Game class - main loop and orchestration."""
from __future__ import annotations

import random

import pygame

from pokemon_game.core.controller import Controller
from pokemon_game.core.keylistener import KeyListener
from pokemon_game.core.map import Map
from pokemon_game.core.screen import Screen
from pokemon_game.core.switch import Switch
from pokemon_game.entities.npc import NPC
from pokemon_game.entities.player import Player
from pokemon_game.entities.pokemon import Pokemon
from pokemon_game.systems.dialogue import Dialogue
from pokemon_game.systems.option import Option
from pokemon_game.systems.save import Save
from pokemon_game.systems.society import CITIZENS, SOCIETY_RULES


class Game:
    """Game class to manage the game."""

    VIRTUAL_WARPS: dict[str, list[tuple]] = {
        "map_0": [
            # Maison d'Aria (porte Tiled ~512,256) — zone large
            (pygame.Rect(496, 240, 48, 40), "house_0", 0),
            # Maison du Rival
            (pygame.Rect(560, 240, 48, 40), "house_1", 0),
            # Laboratoire
            (pygame.Rect(448, 240, 48, 40), "labo_0", 0),
            # Centre Pokémon
            (pygame.Rect(400, 240, 48, 40), "pokecenter", 0),
            # Boutique
            (pygame.Rect(352, 240, 48, 40), "pokeshop", 0),
        ],
        "house_0": [(pygame.Rect(400, 400, 64, 40), "map_0", 0)],
        "house_1": [(pygame.Rect(88, 200, 64, 40), "map_0", 0)],
        "labo_0": [(pygame.Rect(104, 144, 64, 40), "map_0", 0)],
        "pokecenter": [(pygame.Rect(96, 288, 64, 40), "map_0", 0)],
        "pokeshop": [(pygame.Rect(48, 128, 64, 40), "map_0", 0)],
        "inter_0": [(pygame.Rect(48, 128, 64, 40), "map_0", 0)],
    }

    def __init__(self) -> None:
        self.running: bool = True
        self.screen: Screen = Screen()
        self.controller = Controller()
        self.map: Map = Map(self.screen, self.controller)
        self.keylistener: KeyListener = KeyListener()
        self.player: Player = Player(
            self.screen, self.controller, 512, 288, self.keylistener
        )
        self.dialogue: Dialogue = Dialogue(self.player, self.screen, lang="fr")
        self.save: Save = Save(
            "save_0", self.map, self.player, self.keylistener, self.dialogue
        )
        self.save.load()
        self.option: Option = Option(
            self.screen,
            self.controller,
            self.map,
            "fr",
            self.save,
            self.keylistener,
            self.dialogue,
        )

        self.switch_cooldown: int = 0
        self.interact_cooldown: int = 0

        self._give_starter_if_needed()
        self._start_map()

        pending = getattr(self.save, "_pending_map", None)
        if pending and pending != "map_0":
            try:
                self.map.load_map(pending)
            except Exception as e:
                print(f"[SAVE] Map {pending} non rechargée: {e}")

        self._spawn_citizens()
        # S'assurer que le joueur peut bouger
        if hasattr(self.player, "unlock"):
            self.player.unlock()
        else:
            self.player._dialogue_lock = False
            self.player.menu_option = False

    def _give_starter_if_needed(self) -> None:
        if getattr(self.player, "team", None) and len(self.player.team) > 0:
            print(f"[TEAM] Équipe déjà présente ({len(self.player.team)} Pokémon)")
            return
        starters = ["bulbasaur", "charmander", "squirtle"]
        choice = random.choice(starters)
        try:
            mon = Pokemon.create_pokemon(choice, level=5)
            self.player.team = [mon]
            print(f"[STARTER] Tu as reçu {choice.capitalize()} Niv.5 !")
        except Exception as e:
            print(f"[STARTER] Impossible de créer le starter ({e}). Essai Pikachu…")
            try:
                mon = Pokemon.create_pokemon("pikachu", level=5)
                self.player.team = [mon]
                print("[STARTER] Tu as reçu Pikachu Niv.5 !")
            except Exception as e2:
                print(f"[STARTER] Échec total: {e2}")
                self.player.team = []

    def _start_map(self) -> None:
        try:
            self.map.add_player(self.player)
            self.map.load_map("map_0")
            self.switch_cooldown = 30
        except Exception as e:
            print(f"[WARN] Impossible de charger map_0: {e}")
            print("Vérifie que assets/map/map_0.tmx existe.")
            self._no_map = True
        else:
            self._no_map = False

    def _spawn_citizens(self) -> None:
        if not self.player or not self.map:
            return
        map_name = getattr(self.map, "map_name", None) or "map_0"

        layouts: dict[str, list[dict]] = {
            "map_0": [
                {
                    "key": "aria",
                    "x": self.player.position.x + 80,
                    "y": self.player.position.y + 16,
                    "dir": "left",
                },
                {"key": "rival", "x": 580, "y": 280, "dir": "down"},
                {"key": "chen", "x": 500, "y": 280, "dir": "down"},
            ],
            "house_0": [{"key": "aria", "x": 200, "y": 200, "dir": "down"}],
            "house_1": [{"key": "rival", "x": 120, "y": 100, "dir": "down"}],
            "labo_0": [{"key": "chen", "x": 130, "y": 80, "dir": "down"}],
            "pokecenter": [{"key": "joelle", "x": 120, "y": 100, "dir": "down"}],
            "pokeshop": [{"key": "marchand", "x": 80, "y": 70, "dir": "down"}],
        }

        for spec in layouts.get(map_name, []):
            cit = CITIZENS.get(spec["key"])
            if not cit:
                continue
            npc = NPC(
                x=spec["x"],
                y=spec["y"],
                name=cit.name,
                dialogue_id=0,
                sprite_file=NPC.DEFAULT_SPRITE,
                direction=spec.get("dir", "down"),
                personality=cit.personality,
                role=cit.role,
                building=cit.building,
                use_ai=True,
            )
            # PNJ respectent les murs de la map
            if hasattr(npc, "set_collisions"):
                npc.set_collisions(list(getattr(self.map, "collisions", []) or []))
            self.map.add_npc(npc)

        if map_name == "map_0":
            print("[SOCIÉTÉ] Village peuplé — chaque bâtiment a un propriétaire.")
            for r in SOCIETY_RULES[:3]:
                print(f"         {r}")

    def _check_virtual_warps(self) -> None:
        """Warp uniquement à l'ENTRÉE dans la zone (comme les switches Tiled)."""
        if self.switch_cooldown > 0 or not self.player:
            return
        if getattr(self.player, "_dialogue_lock", False) or getattr(
            self.player, "menu_option", False
        ):
            return
        map_name = getattr(self.map, "map_name", None) or "map_0"
        warps = self.VIRTUAL_WARPS.get(map_name, [])
        hit = self.player.hitbox
        # Position précédente approximative (avant ce frame) pour détecter l'entrée
        prev = getattr(self, "_prev_player_hitbox", None)
        self._prev_player_hitbox = hit.copy()
        for rect, target, port in warps:
            now_in = hit.colliderect(rect)
            was_in = prev.colliderect(rect) if prev is not None else False
            if now_in and not was_in:
                if getattr(self.player, "pending_switch", None):
                    return
                self.player.pending_switch = Switch("switch", target, rect, port)
                print(f"[WARP] {map_name} → {target} (port {port})")
                return

    def run(self) -> None:
        while self.running:
            self.handle_input()

            if self.switch_cooldown > 0:
                self.switch_cooldown -= 1
            if self.interact_cooldown > 0:
                self.interact_cooldown -= 1

            self._check_virtual_warps()

            if (
                getattr(self.player, "pending_switch", None)
                and self.switch_cooldown <= 0
            ):
                switch = self.player.pending_switch
                self.player.pending_switch = None
                try:
                    self.map.switch_map(switch)
                    self.switch_cooldown = 45
                    print(f"[MAP] Passage vers {switch.name} (port {switch.port})")
                    self._spawn_citizens()
                except Exception as e:
                    print(f"[ERREUR] Impossible de charger {switch.name}: {e}")
                    self.switch_cooldown = 45

            menu_key = self.controller.get_key("menu")
            if (
                self.keylistener.key_pressed(menu_key)
                and not getattr(self.dialogue, "active", False)
            ):
                if not self.player.menu_option:
                    self.option.open(self.player)
                else:
                    self.option.close()
                self.keylistener.remove_key(menu_key)

            if not getattr(self.player, "menu_option", False):
                if getattr(self, "_no_map", False):
                    self.screen.get_display().fill((34, 139, 34))
                    font = pygame.font.SysFont(None, 36)
                    txt = font.render(
                        "POKEMON BY LA MYLA - map manquante", True, (255, 255, 255)
                    )
                    self.screen.get_display().blit(txt, (40, 40))
                    self.player.update()
                    self.screen.get_display().blit(self.player.image, self.player.rect)
                else:
                    try:
                        self.map.update()
                    except pygame.error as e:
                        print(f"[WARN] Erreur d'affichage: {e}")
                        self.running = False
                        break

                action_key = self.controller.get_key("action")
                if (
                    self.keylistener.key_pressed(action_key)
                    and not getattr(self.dialogue, "active", False)
                    and self.interact_cooldown <= 0
                ):
                    self._try_interact()
                    self.keylistener.remove_key(action_key)
                    self.interact_cooldown = 20

                self.dialogue_controller()
            else:
                if not getattr(self, "_no_map", False):
                    try:
                        self.map.update()
                    except pygame.error:
                        pass
                self.option.update()
                self.dialogue_controller()
                self.option.check_inputs()

            try:
                self.screen.update()
            except pygame.error:
                self.running = False
                break

    def _try_interact(self) -> None:
        if not self.player or not self.map:
            return

        hit = self.player.hitbox.inflate(24, 24)
        direction = getattr(self.player, "direction", "down")
        offset = {
            "up": (0, -20),
            "down": (0, 20),
            "left": (-20, 0),
            "right": (20, 0),
        }.get(direction, (0, 0))
        front = hit.move(*offset)

        for ent in getattr(self.map, "npc_entities", []) or []:
            if hasattr(ent, "hitbox") and (
                front.colliderect(ent.hitbox) or hit.colliderect(ent.hitbox)
            ):
                if hasattr(ent, "face_player"):
                    ent.face_player(self.player.direction)
                if getattr(ent, "use_ai", False) and hasattr(ent, "speak"):
                    team_names = [
                        getattr(p, "dbSymbol", getattr(p, "name", "?"))
                        for p in getattr(self.player, "team", []) or []
                    ]
                    levels = [
                        getattr(p, "level", 5) for p in (self.player.team or [])
                    ]
                    avg = sum(levels) / len(levels) if levels else 5.0
                    map_name = getattr(self.map, "map_name", "") or ""
                    pages = ent.speak(map_name, team_names, avg, lang="fr")
                    self.dialogue.load_pages(pages)
                    print(f"[INTERACT] IA → {ent.name}")
                    return
                did = getattr(ent, "dialogue_id", None)
                if did:
                    self.dialogue.load_data(int(did), 0)
                    return

        for d in getattr(self.map, "dialogues", []) or []:
            rect = d.get("rect")
            if rect and (front.colliderect(rect) or hit.colliderect(rect)):
                did = d.get("id") or 0
                try:
                    did = int(did)
                except (TypeError, ValueError):
                    did = 0
                if did:
                    print(f"[INTERACT] Dialogue {did}")
                    self.dialogue.load_data(did, 0)
                    return

        for npc in getattr(self.map, "npcs", []) or []:
            rect = npc.get("rect")
            if rect and (front.colliderect(rect) or hit.colliderect(rect)):
                props = npc.get("properties") or {}
                did = props.get("dialogue_id") or props.get("dialogue")
                if did is None:
                    parts = (npc.get("name") or "").split()
                    for part in parts[1:]:
                        try:
                            did = int(part)
                            break
                        except ValueError:
                            continue
                if did:
                    try:
                        did = int(did)
                    except (TypeError, ValueError):
                        did = 0
                if did:
                    print(f"[INTERACT] NPC → dialogue {did}")
                    self.dialogue.load_data(did, 0)
                    return
                self.dialogue.pages = [{"name": None, "text": "..."}]
                self.dialogue.page_index = 0
                self.dialogue.active = True
                setattr(self.player, "_dialogue_lock", True)
                return

        print("[INTERACT] Rien à proximité")

    def dialogue_controller(self) -> None:
        if getattr(self.dialogue, "active", False):
            self.dialogue.update()
            action_key = self.controller.get_key("action")
            if self.keylistener.key_pressed(action_key):
                self.dialogue.action()
                self.keylistener.remove_key(action_key)
                # Si dialogue terminé → PNJ reprennent leur vie
                if not getattr(self.dialogue, "active", False):
                    for ent in getattr(self.map, "npc_entities", []) or []:
                        if hasattr(ent, "resume_after_talk"):
                            ent.resume_after_talk()

    def handle_input(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self.keylistener.add_key(event.key)
            elif event.type == pygame.KEYUP:
                self.keylistener.remove_key(event.key)
