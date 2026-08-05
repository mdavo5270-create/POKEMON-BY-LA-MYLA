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
from pokemon_game.systems.inventory import Inventory, BagUI
from pokemon_game.systems.dialogue import Dialogue
from pokemon_game.systems.option import Option
from pokemon_game.systems.save import Save
from pokemon_game.systems.society import CITIZENS, SOCIETY_RULES, PLACES, BUILDINGS


class Game:
    """Game class to manage the game."""

    # Portes : zones larges + entrée aussi possible avec E (voir _try_enter_building)
    DOORS: list[dict] = [
        # Zones calées sur switches Tiled + pieds du sprite (hitbox midbottom)
        {"rect": pygame.Rect(496, 248, 48, 56), "target": "house_0", "port": 0, "label": "Maison d'Aria"},
        {"rect": pygame.Rect(544, 248, 56, 56), "target": "house_1", "port": 0, "label": "Maison du Rival"},
        {"rect": pygame.Rect(432, 248, 56, 56), "target": "labo_0", "port": 0, "label": "Laboratoire"},
        {"rect": pygame.Rect(384, 248, 48, 56), "target": "pokecenter", "port": 0, "label": "Centre Pokémon"},
        {"rect": pygame.Rect(336, 248, 48, 56), "target": "pokeshop", "port": 0, "label": "Boutique"},
        {"rect": pygame.Rect(608, 280, 56, 56), "target": "inter_0", "port": 0, "label": "Maison du village"},
        {"rect": pygame.Rect(720, 128, 48, 56), "target": "map_1", "port": 0, "label": "Route de l'Est"},
    ]

    VIRTUAL_WARPS: dict[str, list[tuple]] = {
        "map_0": [
            (pygame.Rect(496, 248, 48, 56), "house_0", 0),
            (pygame.Rect(544, 248, 56, 56), "house_1", 0),
            (pygame.Rect(432, 248, 56, 56), "labo_0", 0),
            (pygame.Rect(384, 248, 48, 56), "pokecenter", 0),
            (pygame.Rect(336, 248, 48, 56), "pokeshop", 0),
            (pygame.Rect(608, 280, 56, 56), "inter_0", 0),
            (pygame.Rect(720, 128, 48, 56), "map_1", 0),
        ],
        "house_0": [(pygame.Rect(400, 400, 80, 48), "map_0", 0)],
        "house_1": [(pygame.Rect(80, 200, 80, 40), "map_0", 0)],
        "labo_0": [(pygame.Rect(100, 140, 80, 40), "map_0", 0)],
        "pokecenter": [(pygame.Rect(90, 280, 80, 48), "map_0", 0)],
        "pokeshop": [(pygame.Rect(40, 120, 80, 40), "map_0", 0)],
        "inter_0": [(pygame.Rect(40, 120, 80, 40), "map_0", 0)],
        "map_1": [(pygame.Rect(0, 100, 48, 80), "map_0", 0)],
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
        # Inventaire
        if not getattr(self.player, "inventory", None):
            self.player.inventory = Inventory.starter()
            print("[INV] Sac de depart pret")
        self.bag = BagUI(
            self.screen, self.controller, self.keylistener,
            self.player.inventory, self.player,
        )
        self.battle: Battle | None = None
        self.wild_cooldown: int = 0
        self._pending_battle: str | None = None

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
        # PNJ près de LEUR bâtiment (pas dispersés)
        layouts: dict[str, list[dict]] = {
            "map_0": [
                {"key": "aria", "x": 520, "y": 280, "dir": "down", "radius": 48},
                {"key": "rival", "x": 580, "y": 280, "dir": "down", "radius": 40},
                {"key": "chen", "x": 460, "y": 280, "dir": "down", "radius": 40},
                {"key": "joelle", "x": 410, "y": 280, "dir": "down", "radius": 36},
                {"key": "marchand", "x": 360, "y": 280, "dir": "down", "radius": 36},
                {"key": "hugo", "x": 640, "y": 310, "dir": "down", "radius": 40},
                {"key": "lea", "x": 600, "y": 300, "dir": "left", "radius": 48},
                {"key": "tom", "x": 220, "y": 400, "dir": "down", "radius": 56},
                {"key": "garde", "x": 730, "y": 160, "dir": "down", "radius": 40},
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
                wander_radius=float(spec.get("radius", 48)),
            )
            # Travail = devant sa porte (pas l'autre bout de la map)
            wx = cit.work_x or spec["x"]
            wy = cit.work_y or (spec["y"] + 20)
            if hasattr(npc, "set_work"):
                npc.set_work(wx, wy)
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
        """Warp si le joueur entre dans la zone porte (edge) OU reste 12 frames dedans."""
        if self.switch_cooldown > 0 or not self.player:
            return
        if getattr(self.player, "_dialogue_lock", False) or getattr(
            self.player, "menu_option", False
        ):
            return
        if getattr(self.player, "pending_switch", None):
            return
        map_name = getattr(self.map, "map_name", None) or "map_0"
        warps = self.VIRTUAL_WARPS.get(map_name, [])
        self.player.rect.topleft = (int(self.player.position.x), int(self.player.position.y))
        self.player.align_hitbox()
        hit = self.player.hitbox
        prev = getattr(self, "_prev_player_hitbox", None)
        self._prev_player_hitbox = hit.copy()
        inside = None
        for rect, target, port in warps:
            now_in = hit.colliderect(rect)
            was_in = prev.colliderect(rect) if prev is not None else False
            if now_in and not was_in:
                self.player.pending_switch = Switch("switch", target, rect, port)
                print(f"[WARP] {map_name} → {target} (port {port})")
                self._warp_stand_frames = 0
                return
            if now_in:
                inside = (rect, target, port)
        # Rester sur la porte (si edge a raté)
        if inside:
            self._warp_stand_frames = getattr(self, "_warp_stand_frames", 0) + 1
            if self._warp_stand_frames >= 20:
                rect, target, port = inside
                self.player.pending_switch = Switch("switch", target, rect, port)
                print(f"[WARP] stand → {target}")
                self._warp_stand_frames = 0
        else:
            self._warp_stand_frames = 0

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

            # ── Sac ──
            if getattr(self.player, "_open_bag", False):
                self.player._open_bag = False
                self.bag.inventory = self.player.inventory
                self.bag.open_bag()
            if self.bag and self.bag.open:
                if not getattr(self, "_no_map", False):
                    try:
                        self.map.update()
                    except Exception:
                        pass
                self.bag.update()
                try:
                    self.screen.update()
                except pygame.error:
                    self.running = False
                    break
                continue

            self._check_virtual_warps()
            self._check_wild_encounter()

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


    def _try_enter_building(self) -> bool:
        """Devant une porte + E → entrer (plus fiable que marcher dessus)."""
        if not self.player:
            return False
        map_name = getattr(self.map, "map_name", None) or "map_0"
        # Sync rect depuis position (évite hitbox décalée)
        self.player.rect.topleft = (int(self.player.position.x), int(self.player.position.y))
        self.player.align_hitbox()
        hit = self.player.hitbox.inflate(24, 24)
        if map_name == "map_0":
            for door in self.DOORS:
                if hit.colliderect(door["rect"]):
                    self.player.pending_switch = Switch(
                        "switch", door["target"], door["rect"], door["port"]
                    )
                    print(f"[PORTE] Entrée → {door['label']} ({door['target']})")
                    return True
        # Sortie intérieur
        for rect, target, port in self.VIRTUAL_WARPS.get(map_name, []):
            if hit.colliderect(rect) and target == "map_0":
                self.player.pending_switch = Switch("switch", target, rect, port)
                print(f"[PORTE] Sortie → {target}")
                return True
        return False

    def _try_interact(self) -> None:
        if not self.player or not self.map:
            return
        # E devant une porte = entrer / sortir
        if self._try_enter_building():
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
                    # Boutique
                    if getattr(ent, "personality", "") == "commercial_honnête":
                        inv = getattr(self.player, "inventory", None)
                        if inv:
                            bought = []
                            if inv.buy("potion", 1):
                                bought.append("Potion")
                            if inv.buy("pokeball", 1):
                                bought.append("Poke Ball")
                            if bought:
                                self.dialogue.load_pages([
                                    {"name": ent.name, "text": f"Voici : {', '.join(bought)} !"},
                                    {"name": ent.name, "text": f"Il te reste {inv.money} pieces. Reviens !"},
                                ])
                            else:
                                self.dialogue.load_pages([
                                    {"name": ent.name, "text": f"Pas assez d'argent ({inv.money})."},
                                    {"name": ent.name, "text": "Potion=200, Poke Ball=200."},
                                ])
                            print("[SHOP] Achat")
                            return
                    # Rival : dialogue puis combat
                    if getattr(ent, "personality", "") == "compétitif":
                        team = getattr(self.player, "team", None) or []
                        if team and team[0].hp > 0:
                            self.dialogue.load_pages([
                                {"name": ent.name, "text": "Toi ! On se bat, maintenant !"},
                            ])
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

        inv = getattr(self.player, "inventory", None)
        self.player._dialogue_lock = True
        self.battle = Battle(
            self.screen,
            self.controller,
            self.keylistener,
            player_mon,
            enemy,
            enemy_name="Rival",
            can_run=True,
            is_wild=False,
            team=team,
            inventory=inv,
            on_end=_on_end,
        )
        print("[BATTLE] Combat vs Rival démarré !")

    def _check_wild_encounter(self) -> None:
        """Rencontres sauvages sur map_1 (Route Est)."""
        if self.battle and self.battle.active:
            return
        if getattr(self.player, "menu_option", False):
            return
        if getattr(self.player, "_dialogue_lock", False):
            return
        if self.wild_cooldown > 0:
            self.wild_cooldown -= 1
            return
        map_name = getattr(self.map, "map_name", "") or ""
        if map_name != "map_1":
            return
        # Seulement si le joueur bouge
        moving = getattr(self.player, "is_moving", False) or getattr(self.player, "direction", None)
        # chance ~8% par frame quand on marche — trop haut. Utiliser un timer via step
        # Détection simple : si position a changé
        pos = (int(self.player.position.x), int(self.player.position.y))
        last = getattr(self, "_last_wild_pos", None)
        if last == pos:
            return
        self._last_wild_pos = pos
        if random.random() > 0.12:
            return
        species_pool = ["caterpie", "ekans", "diglett", "bellsprout", "abra", "cubone"]
        species = random.choice(species_pool)
        team = getattr(self.player, "team", None) or []
        level = 3
        if team:
            level = max(2, min(8, team[0].level - 1 + random.randint(0, 2)))
        self.wild_cooldown = 180  # ~3s à 60fps
        print(f"[WILD] Rencontre {species} N.{level}")
        self.start_wild_battle(species, level)

    def start_wild_battle(self, species: str = "caterpie", level: int = 3) -> None:
        """Combat sauvage."""
        team = getattr(self.player, "team", None) or []
        if not team:
            return
        # Premier Pokémon vivant
        player_mon = None
        for m in team:
            if m.hp > 0:
                player_mon = m
                break
        if not player_mon:
            return
        try:
            enemy = Pokemon.create_pokemon(species, level=level)
        except Exception:
            try:
                enemy = Pokemon.create_pokemon("caterpie", level=level)
            except Exception as e:
                print(f"[BATTLE] Wild fail: {e}")
                return

        def _on_end(result: str) -> None:
            b = self.battle
            if b and getattr(b, "team", None):
                self.player.team = list(b.team)
            self.battle = None
            self.player._dialogue_lock = False
            self.player.menu_option = False
            if result == "lose":
                self._heal_team()
            print(f"[BATTLE] Fin wild — {result}")

        inv = getattr(self.player, "inventory", None)
        self.player._dialogue_lock = True
        self.battle = Battle(
            self.screen, self.controller, self.keylistener,
            player_mon, enemy, enemy_name="Pokémon sauvage",
            can_run=True, is_wild=True, team=team, inventory=inv,
            on_end=_on_end,
        )

    def handle_input(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self.keylistener.add_key(event.key)
            elif event.type == pygame.KEYUP:
                self.keylistener.remove_key(event.key)
