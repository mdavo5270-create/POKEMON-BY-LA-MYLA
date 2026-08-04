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
        self.dialogue: Dialogue = Dialogue(self.player, self.screen)
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

        # Charger la map de départ + ajouter le joueur
        self._start_map()

    def _start_map(self) -> None:
        """Charge la map initiale et place le joueur."""
        try:
            self.map.add_player(self.player)
            self.map.load_map("map_0")
        except Exception as e:
            print(f"[WARN] Impossible de charger map_0: {e}")
            print("Vérifie que assets/map/map_0.tmx existe.")
            # Affiche un fond coloré pour confirmer que le jeu tourne
            self._no_map = True
        else:
            self._no_map = False

    def run(self) -> None:
        """Run the game loop."""
        while self.running:
            self.handle_input()
            if not getattr(self.player, "menu_option", False):
                if getattr(self, "_no_map", False):
                    # Fond vert = le jeu tourne, mais pas de map
                    self.screen.get_display().fill((34, 139, 34))
                    font = pygame.font.SysFont(None, 36)
                    txt = font.render("POKEMON BY LA MYLA - map manquante", True, (255, 255, 255))
                    self.screen.get_display().blit(txt, (40, 40))
                    # Dessine le joueur même sans map
                    self.player.update()
                    self.screen.get_display().blit(self.player.image, self.player.rect)
                else:
                    self.map.update()
                if pygame.K_e in self.keylistener.keys and not getattr(self.dialogue, "active", False):
                    self.dialogue.load_data(1001, 0)
                    self.keylistener.remove_key(pygame.K_e)
                self.dialogue_controller()
            else:
                self.option.update()
                self.dialogue_controller()
                self.option.check_inputs()
            self.screen.update()

    def dialogue_controller(self) -> None:
        """Manage active dialogues."""
        if getattr(self.dialogue, "active", False):
            self.dialogue.update()
            if self.keylistener.key_pressed(self.controller.get_key("action")):
                self.dialogue.action()
                self.keylistener.remove_key(self.controller.get_key("action"))

    def handle_input(self) -> None:
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                pygame.quit()
            elif event.type == pygame.KEYDOWN:
                self.keylistener.add_key(event.key)
            elif event.type == pygame.KEYUP:
                self.keylistener.remove_key(event.key)
