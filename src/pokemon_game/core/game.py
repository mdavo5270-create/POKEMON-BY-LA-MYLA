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
from pokemon_game.systems.battle import Battle
from pokemon_game.systems.dialogue import Dialogue
from pokemon_game.systems.option import Option
from pokemon_game.systems.save import Save
from pokemon_game.systems.society import CITIZENS, SOCIETY_RULES, PLACES, BUILDINGS


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
            # Maison village (Hugo)
            (pygame.Rect(624, 288, 48, 40), "inter_0", 0),
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
        self.battle: Battle | None = None

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

        # Positions outdoor (map_0) + intérieur = propriétaire chez lui
        layouts: dict[str, list[dict]] = {
            "map_0": [
                {"key": "aria", "x": 520, "y": 300, "dir": "down"},
                {"key": "rival", "x": 600, "y": 300, "dir": "left"},
                {"key": "chen", "x": 480, "y": 300, "dir": "down"},
                {"key": "joelle", "x": 430, "y": 300, "dir": "down"},
                {"key": "marchand", "x": 380, "y": 300, "dir": "right"},
                {"key": "hugo", "x": 650, "y": 320, "dir": "down"},
                {"key": "lea", "x": 550, "y": 340, "dir": "left"},
                {"key": "tom", "x": 200, "y": 400, "dir": "down"},
                {"key": "garde", "x": 720, "y": 160, "dir": "down"},
            ],
            "house_0": [{"key": "aria", "x": 200, "y": 200, "dir": "down"}],
            "house_1": [
                {"key": "rival", "x": 120, "y": 100, "dir": "down"},
                {"key": "lea", "x": 160, "y": 120, "dir": "left"},
            ],
            "labo_0": [{"key": "chen", "x": 130, "y": 80, "dir": "down"}],
            "pokecenter": [{"key": "joelle", "x": 120, "y": 100, "dir": "down"}],
            "pokeshop": [{"key": "marchand", "x": 80, "y": 70, "dir": "down"}],
            "inter_0": [{"key": "hugo", "x": 80, "y": 80, "dir": "down"}],
            "map_1": [{"key": "garde", "x": 40, "y": 100, "dir": "down"}],
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
                can_walk=True,
            )
            if hasattr(npc, "set_work") and (cit.work_x or cit.work_y):
                npc.set_work(cit.work_x, cit.work_y)
            if hasattr(npc, "set_collisions"):
                npc.set_collisions(list(getattr(self.map, "collisions", []) or []))
            self.map.add_npc(npc)

        if map_name == "map_0":
            n = len(getattr(self.map, "npc_entities", []) or [])
            print(f"[SOCIÉTÉ] {n} habitants actifs sur map_0.")
            print("[SOCIÉTÉ] Bâtiments:", ", ".join(
                f"{b.label} ({b.owner})" for b in BUILDINGS.values() if b.role != "route"
            ))

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

            # ── Combat prioritaire ──
            if self.battle and self.battle.active:
                self.battle.update()
                try:
                    self.screen.update()
                except pygame.error:
                    self.running = False
                    break
                continue

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
                    # Centre Pokémon : soigner
                    if getattr(ent, "personality", "") == "douce_professionnelle":
                        self._heal_team()
                        self.dialogue.load_pages([
                            {"name": ent.name, "text": "Tes Pokémon sont en pleine forme !"},
                            {"name": ent.name, "text": "Reviens quand tu veux."},
                        ])
                        print("[SOIN] Équipe soignée au Centre Pokémon")
                        return
                    # Rival : dialogue puis combat
                    if getattr(ent, "personality", "") == "compétitif":
                        team = getattr(self.player, "team", None) or []
                        if team and team[0].hp > 0:
                            self.dialogue.load_pages([
                                {"name": ent.name, "text": "Toi ! On se bat, maintenant !"},
                            ])
                            # Marquer un combat en attente après le dialogue
                            self._pending_battle = "rival"
                            print("[INTERACT] Rival → combat imminent")
                            return
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


        # 3) Lieux d'intérêt (panneaux, étang, banc…)
        for place in PLACES:
            prect = pygame.Rect(place.x, place.y, place.w, place.h)
            if front.colliderect(prect) or hit.colliderect(prect):
                pages = [
                    {"name": place.label, "text": place.description_fr},
                ]
                b = BUILDINGS.get(place.id)
                self.dialogue.load_pages(pages)
                print(f"[INTERACT] Lieu → {place.label}")
                return

        print("[INTERACT] Rien à proximité")

    def dialogue_controller(self) -> None:
        if getattr(self.dialogue, "active", False):
            self.dialogue.update()
            action_key = self.controller.get_key("action")
            if self.keylistener.key_pressed(action_key):
                self.dialogue.action()
                self.keylistener.remove_key(action_key)
                if not getattr(self.dialogue, "active", False):
                    for ent in getattr(self.map, "npc_entities", []) or []:
                        if hasattr(ent, "resume_after_talk"):
                            ent.resume_after_talk()
                    # Combat en attente (Rival)
                    if getattr(self, "_pending_battle", None) == "rival":
                        self._pending_battle = None
                        self.start_battle_rival()


    def _heal_team(self) -> None:
        for mon in getattr(self.player, "team", []) or []:
            mon.hp = mon.maxhp
            for move in getattr(mon, "moves", []) or []:
                if hasattr(move, "maxpp") and move.maxpp:
                    move.pp = move.maxpp

    def start_battle_rival(self) -> None:
        """Démarre un combat contre le Rival."""
        team = getattr(self.player, "team", None) or []
        if not team:
            print("[BATTLE] Pas de Pokémon — pas de combat")
            return
        player_mon = team[0]
        if player_mon.hp <= 0:
            player_mon.hp = player_mon.maxhp
        try:
            enemy = Pokemon.create_pokemon("charmander", level=max(3, player_mon.level))
            # Si joueur a charmander, ennemi = bulbasaur / squirtle
            if (player_mon.dbSymbol or "").lower() == "charmander":
                enemy = Pokemon.create_pokemon("squirtle", level=max(3, player_mon.level))
            elif (player_mon.dbSymbol or "").lower() == "squirtle":
                enemy = Pokemon.create_pokemon("bulbasaur", level=max(3, player_mon.level))
        except Exception as e:
            print(f"[BATTLE] Impossible de créer l'ennemi: {e}")
            return

        def _on_end(result: str) -> None:
            self.battle = None
            self.player._dialogue_lock = False
            self.player.menu_option = False
            if result == "lose":
                self._heal_team()
                self.dialogue.load_pages([
                    {"name": None, "text": "Tes Pokémon ont été soignés… Reviens plus fort."},
                ])
            elif result == "win":
                self.dialogue.load_pages([
                    {"name": "Rival", "text": "Tss… Tu as gagné cette fois. On se reverra !"},
                ])
            print(f"[BATTLE] Fin — {result}")

        self.player._dialogue_lock = True
        self.battle = Battle(
            self.screen,
            self.controller,
            self.keylistener,
            player_mon,
            enemy,
            enemy_name="Rival",
            can_run=True,
            on_end=_on_end,
        )
        print("[BATTLE] Combat vs Rival démarré !")

    def start_wild_battle(self, species: str = "rattata", level: int = 3) -> None:
        """Combat sauvage (pour tests / herbe plus tard)."""
        team = getattr(self.player, "team", None) or []
        if not team:
            return
        player_mon = team[0]
        try:
            enemy = Pokemon.create_pokemon(species, level=level)
        except Exception:
            try:
                enemy = Pokemon.create_pokemon("pidgey", level=level)
            except Exception as e:
                print(f"[BATTLE] Wild fail: {e}")
                return

        def _on_end(result: str) -> None:
            self.battle = None
            self.player._dialogue_lock = False
            self.player.menu_option = False
            if result == "lose":
                self._heal_team()

        self.player._dialogue_lock = True
        self.battle = Battle(
            self.screen, self.controller, self.keylistener,
            player_mon, enemy, enemy_name="Pokémon sauvage",
            can_run=True, on_end=_on_end,
        )

    def handle_input(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self.keylistener.add_key(event.key)
            elif event.type == pygame.KEYUP:
                self.keylistener.remove_key(event.key)
