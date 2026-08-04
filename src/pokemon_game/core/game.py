"""Game class - main loop and orchestration."""
import pygame

from pokemon_game.core.controller import Controller
from pokemon_game.core.keylistener import KeyListener
from pokemon_game.core.map import Map
from pokemon_game.core.screen import Screen
from pokemon_game.core.switch import Switch
from pokemon_game.entities.player import Player
from pokemon_game.systems.dialogue import Dialogue
from pokemon_game.systems.option import Option
from pokemon_game.systems.save import Save


class Game:
    """Game class to manage the game."""

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

        # Cooldown anti-boucle de maps (en frames)
        self.switch_cooldown: int = 0
        # Cooldown interaction E (évite double-trigger)
        self.interact_cooldown: int = 0

        # Charger la map de départ + ajouter le joueur
        self._start_map()

        # Si save avait une map pending, on la charge
        pending = getattr(self.save, "_pending_map", None)
        if pending and pending != "map_0":
            try:
                self.map.load_map(pending)
            except Exception as e:
                print(f"[SAVE] Map {pending} non rechargée: {e}")

    def _start_map(self) -> None:
        """Charge la map initiale et place le joueur."""
        try:
            self.map.add_player(self.player)
            self.map.load_map("map_0")
            self.switch_cooldown = 30  # évite un switch immédiat au spawn
        except Exception as e:
            print(f"[WARN] Impossible de charger map_0: {e}")
            print("Vérifie que assets/map/map_0.tmx existe.")
            self._no_map = True
        else:
            self._no_map = False

    def run(self) -> None:
        """Run the game loop."""
        while self.running:
            self.handle_input()

            if self.switch_cooldown > 0:
                self.switch_cooldown -= 1
            if self.interact_cooldown > 0:
                self.interact_cooldown -= 1

            # Changement de map demandé par le joueur
            if (
                getattr(self.player, "pending_switch", None)
                and self.switch_cooldown <= 0
            ):
                switch = self.player.pending_switch
                self.player.pending_switch = None
                try:
                    self.map.switch_map(switch)
                    self.switch_cooldown = 45  # ~0.75s à 60 FPS
                    print(f"[MAP] Passage vers {switch.name} (port {switch.port})")
                except Exception as e:
                    print(f"[ERREUR] Impossible de charger {switch.name}: {e}")
                    self.switch_cooldown = 45

            # ESC → menu pause
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

                # Interaction E avec dialogues / NPCs de la map
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
                # Menu ouvert : on dessine quand même la map en fond (optionnel)
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
        """Cherche un dialogue ou NPC proche du joueur et le déclenche."""
        if not self.player or not self.map:
            return

        # Zone d'interaction : devant le joueur + un peu autour
        hit = self.player.hitbox.inflate(24, 24)
        direction = getattr(self.player, "direction", "down")
        offset = {
            "up": (0, -20),
            "down": (0, 20),
            "left": (-20, 0),
            "right": (20, 0),
        }.get(direction, (0, 0))
        front = hit.move(*offset)

        # 1) Dialogues placés sur la map
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

        # 2) NPCs → dialogue via propriété ou id dans le nom
        for npc in getattr(self.map, "npcs", []) or []:
            rect = npc.get("rect")
            if rect and (front.colliderect(rect) or hit.colliderect(rect)):
                props = npc.get("properties") or {}
                did = props.get("dialogue_id") or props.get("dialogue")
                if did is None:
                    # "npc 1001" → 1001
                    parts = (npc.get("name") or "").split()
                    for p in parts[1:]:
                        try:
                            did = int(p)
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
                # Fallback : message générique
                self.dialogue.pages = [
                    {"name": None, "text": "..."}
                ]
                self.dialogue.page_index = 0
                self.dialogue.active = True
                setattr(self.player, "_dialogue_lock", True)
                return

        # 3) Rien à proximité → pas de dialogue de test hardcodé
        print("[INTERACT] Rien à proximité")

    def dialogue_controller(self) -> None:
        """Manage active dialogues."""
        if getattr(self.dialogue, "active", False):
            self.dialogue.update()
            action_key = self.controller.get_key("action")
            if self.keylistener.key_pressed(action_key):
                self.dialogue.action()
                self.keylistener.remove_key(action_key)

    def handle_input(self) -> None:
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self.keylistener.add_key(event.key)
            elif event.type == pygame.KEYUP:
                self.keylistener.remove_key(event.key)
