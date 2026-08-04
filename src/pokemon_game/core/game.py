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

        # Charger la map de départ + ajouter le joueur
        self._start_map()

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

                # Test dialogue (E) — à remplacer plus tard par interaction NPC/objets
                action_key = self.controller.get_key("action")
                if (
                    self.keylistener.key_pressed(action_key)
                    and not getattr(self.dialogue, "active", False)
                ):
                    self.dialogue.load_data(1001, 0)
                    self.keylistener.remove_key(action_key)

                self.dialogue_controller()
            else:
                self.option.update()
                self.dialogue_controller()
                self.option.check_inputs()

            try:
                self.screen.update()
            except pygame.error:
                self.running = False
                break

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
