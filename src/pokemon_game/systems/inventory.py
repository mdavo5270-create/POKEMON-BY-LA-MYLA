"""Système d'inventaire — objets, sac, utilisation, UI."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import pygame

from pokemon_game.core.tool import asset_path


@dataclass
class ItemDef:
    id: str
    name_fr: str
    name_en: str
    category: str  # item | medicine | ball | key
    description_fr: str
    description_en: str
    usable: bool = True
    battle_ok: bool = False
    price: int = 0  # 0 = non achetable / clé


# Catalogue de base
ITEM_CATALOG: dict[str, ItemDef] = {
    "potion": ItemDef(
        "potion", "Potion", "Potion", "medicine",
        "Restaure 20 PV d'un Pokémon.", "Restores 20 HP.",
        usable=True, battle_ok=True, price=200,
    ),
    "super_potion": ItemDef(
        "super_potion", "Super Potion", "Super Potion", "medicine",
        "Restaure 50 PV d'un Pokémon.", "Restores 50 HP.",
        usable=True, battle_ok=True, price=700,
    ),
    "hyper_potion": ItemDef(
        "hyper_potion", "Hyper Potion", "Hyper Potion", "medicine",
        "Restaure 200 PV d'un Pokémon.", "Restores 200 HP.",
        usable=True, battle_ok=True, price=1500,
    ),
    "full_restore": ItemDef(
        "full_restore", "Guérison", "Full Restore", "medicine",
        "Restaure tous les PV.", "Fully restores HP.",
        usable=True, battle_ok=True, price=3000,
    ),
    "pokeball": ItemDef(
        "pokeball", "Poké Ball", "Poké Ball", "ball",
        "Permet de capturer un Pokémon sauvage.", "Catch wild Pokémon.",
        usable=False, battle_ok=True, price=200,
    ),
    "great_ball": ItemDef(
        "great_ball", "Super Ball", "Great Ball", "ball",
        "Ball améliorée pour capturer.", "Better catch rate.",
        usable=False, battle_ok=True, price=600,
    ),
    "antidote": ItemDef(
        "antidote", "Antidote", "Antidote", "medicine",
        "Soigne l'empoisonnement.", "Cures poison.",
        usable=True, battle_ok=True, price=100,
    ),
    "paralyze_heal": ItemDef(
        "paralyze_heal", "Anti-Para", "Paralyze Heal", "medicine",
        "Soigne la paralysie.", "Cures paralysis.",
        usable=True, battle_ok=True, price=200,
    ),
    "repel": ItemDef(
        "repel", "Repousse", "Repel", "item",
        "Repousse les Pokémon sauvages un moment.", "Repels wild Pokémon.",
        usable=True, battle_ok=False, price=350,
    ),
    "town_map": ItemDef(
        "town_map", "Carte", "Town Map", "key",
        "Carte de la région.", "A map of the region.",
        usable=True, battle_ok=False, price=0,
    ),
}


class Inventory:
    """Sac du joueur : {item_id: quantity} + argent."""

    def __init__(self) -> None:
        self.items: dict[str, int] = {}
        self.money: int = 3000

    def add(self, item_id: str, qty: int = 1) -> None:
        if item_id not in ITEM_CATALOG:
            print(f"[INV] Objet inconnu: {item_id}")
            return
        self.items[item_id] = self.items.get(item_id, 0) + qty

    def remove(self, item_id: str, qty: int = 1) -> bool:
        have = self.items.get(item_id, 0)
        if have < qty:
            return False
        self.items[item_id] = have - qty
        if self.items[item_id] <= 0:
            del self.items[item_id]
        return True

    def count(self, item_id: str) -> int:
        return self.items.get(item_id, 0)

    def list_items(self, category: str | None = None) -> list[tuple[ItemDef, int]]:
        result = []
        for iid, qty in sorted(self.items.items()):
            if qty <= 0:
                continue
            defn = ITEM_CATALOG.get(iid)
            if not defn:
                continue
            if category and defn.category != category:
                continue
            result.append((defn, qty))
        return result

    def can_afford(self, price: int) -> bool:
        return self.money >= price

    def buy(self, item_id: str, qty: int = 1) -> bool:
        defn = ITEM_CATALOG.get(item_id)
        if not defn or defn.price <= 0:
            return False
        total = defn.price * qty
        if not self.can_afford(total):
            return False
        self.money -= total
        self.add(item_id, qty)
        return True

    def use_on_pokemon(self, item_id: str, pokemon) -> tuple[bool, str]:
        """Utilise un objet sur un Pokémon. Retourne (ok, message)."""
        defn = ITEM_CATALOG.get(item_id)
        if not defn or not defn.usable:
            return False, "Impossible d'utiliser cet objet."
        if self.count(item_id) <= 0:
            return False, "Tu n'en as plus."

        msg = ""
        if item_id == "potion":
            if pokemon.hp >= pokemon.maxhp:
                return False, "PV déjà au maximum."
            heal = min(20, pokemon.maxhp - pokemon.hp)
            pokemon.hp += heal
            msg = f"{getattr(pokemon, 'dbSymbol', 'Pokémon').capitalize()} récupère {heal} PV !"
        elif item_id == "super_potion":
            if pokemon.hp >= pokemon.maxhp:
                return False, "PV déjà au maximum."
            heal = min(50, pokemon.maxhp - pokemon.hp)
            pokemon.hp += heal
            msg = f"Récupère {heal} PV !"
        elif item_id == "hyper_potion":
            if pokemon.hp >= pokemon.maxhp:
                return False, "PV déjà au maximum."
            heal = min(200, pokemon.maxhp - pokemon.hp)
            pokemon.hp += heal
            msg = f"Récupère {heal} PV !"
        elif item_id == "full_restore":
            if pokemon.hp >= pokemon.maxhp and not getattr(pokemon, "status", ""):
                return False, "Déjà en pleine forme."
            pokemon.hp = pokemon.maxhp
            pokemon.status = ""
            msg = "PV et statut restaurés !"
        elif item_id == "antidote":
            if getattr(pokemon, "status", "") != "poison":
                return False, "Pas empoisonné."
            pokemon.status = ""
            msg = "Poison soigné !"
        elif item_id == "paralyze_heal":
            if getattr(pokemon, "status", "") != "paralyze":
                return False, "Pas paralysé."
            pokemon.status = ""
            msg = "Paralysie soignée !"
        elif item_id == "repel":
            msg = "Les Pokémon sauvages resteront à distance un moment."
        elif item_id == "town_map":
            msg = "Tu consultes la carte de la région…"
        else:
            return False, "Effet non implémenté."

        self.remove(item_id, 1)
        return True, msg

    def to_dict(self) -> dict:
        return {"items": dict(self.items), "money": self.money}

    @classmethod
    def from_dict(cls, data: dict) -> "Inventory":
        inv = cls()
        inv.items = dict(data.get("items") or {})
        inv.money = int(data.get("money", 0))
        return inv

    @classmethod
    def starter(cls) -> "Inventory":
        """Inventaire de départ."""
        inv = cls()
        inv.money = 3000
        inv.add("potion", 5)
        inv.add("pokeball", 5)
        inv.add("antidote", 2)
        inv.add("town_map", 1)
        return inv


class BagUI:
    """Interface du sac (ouvert depuis le menu pause)."""

    CATEGORIES = [
        ("all", "Tous"),
        ("medicine", "Soins"),
        ("ball", "Balls"),
        ("item", "Objets"),
        ("key", "Clés"),
    ]

    def __init__(self, screen, controller, keylistener, inventory: Inventory, player) -> None:
        self.screen = screen
        self.controller = controller
        self.keylistener = keylistener
        self.inventory = inventory
        self.player = player
        self.open = False
        self.cat_index = 0
        self.item_index = 0
        self.mode = "list"  # list | target | message
        self.message = ""
        self._target_index = 0
        self._font = None
        self._font_sm = None
        self._cooldown = 0
        self._load_fonts()

    def _load_fonts(self) -> None:
        try:
            path = asset_path("fonts", "OakSans-Regular.ttf")
            self._font = pygame.font.Font(path, 20)
            self._font_sm = pygame.font.Font(path, 16)
        except Exception:
            self._font = pygame.font.SysFont(None, 22)
            self._font_sm = pygame.font.SysFont(None, 18)

    def open_bag(self) -> None:
        self.open = True
        self.mode = "list"
        self.item_index = 0
        self.cat_index = 0
        self._cooldown = 10
        if self.player:
            self.player.menu_option = True
            setattr(self.player, "_dialogue_lock", True)

    def close_bag(self) -> None:
        self.open = False
        self.mode = "list"
        if self.player:
            self.player.menu_option = False
            setattr(self.player, "_dialogue_lock", False)

    def _filtered(self) -> list[tuple]:
        cat = self.CATEGORIES[self.cat_index][0]
        if cat == "all":
            return self.inventory.list_items()
        return self.inventory.list_items(cat)

    def update(self) -> None:
        if not self.open:
            return
        if self._cooldown > 0:
            self._cooldown -= 1
        self._draw()
        if self._cooldown <= 0:
            self._inputs()

    def _inputs(self) -> None:
        kl = self.keylistener
        c = self.controller
        up = kl.key_pressed(c.get_key("up")) or kl.key_pressed(pygame.K_UP)
        down = kl.key_pressed(c.get_key("down")) or kl.key_pressed(pygame.K_DOWN)
        left = kl.key_pressed(c.get_key("left")) or kl.key_pressed(pygame.K_LEFT)
        right = kl.key_pressed(c.get_key("right")) or kl.key_pressed(pygame.K_RIGHT)
        action = kl.key_pressed(c.get_key("action")) or kl.key_pressed(pygame.K_RETURN)
        menu = kl.key_pressed(c.get_key("menu"))

        def clear(k):
            if k in kl.keys:
                kl.remove_key(k)

        if menu:
            clear(c.get_key("menu"))
            self.close_bag()
            return

        if self.mode == "message":
            if action:
                clear(c.get_key("action"))
                clear(pygame.K_RETURN)
                self.mode = "list"
                self._cooldown = 8
            return

        if self.mode == "target":
            team = getattr(self.player, "team", []) or []
            n = max(len(team), 1)
            if up:
                self._target_index = (self._target_index - 1) % n
                clear(c.get_key("up")); clear(pygame.K_UP)
                self._cooldown = 8
            elif down:
                self._target_index = (self._target_index + 1) % n
                clear(c.get_key("down")); clear(pygame.K_DOWN)
                self._cooldown = 8
            elif action and team:
                clear(c.get_key("action")); clear(pygame.K_RETURN)
                items = self._filtered()
                if 0 <= self.item_index < len(items):
                    defn, _ = items[self.item_index]
                    ok, msg = self.inventory.use_on_pokemon(defn.id, team[self._target_index])
                    self.message = msg
                    self.mode = "message"
                self._cooldown = 10
            return

        # mode list
        items = self._filtered()
        n = max(len(items), 1)
        if left:
            self.cat_index = (self.cat_index - 1) % len(self.CATEGORIES)
            self.item_index = 0
            clear(c.get_key("left")); clear(pygame.K_LEFT)
            self._cooldown = 8
        elif right:
            self.cat_index = (self.cat_index + 1) % len(self.CATEGORIES)
            self.item_index = 0
            clear(c.get_key("right")); clear(pygame.K_RIGHT)
            self._cooldown = 8
        elif up:
            self.item_index = (self.item_index - 1) % n
            clear(c.get_key("up")); clear(pygame.K_UP)
            self._cooldown = 8
        elif down:
            self.item_index = (self.item_index + 1) % n
            clear(c.get_key("down")); clear(pygame.K_DOWN)
            self._cooldown = 8
        elif action and items:
            clear(c.get_key("action")); clear(pygame.K_RETURN)
            defn, _ = items[self.item_index]
            if defn.usable and defn.category == "medicine":
                self.mode = "target"
                self._target_index = 0
            elif defn.usable:
                ok, msg = self.inventory.use_on_pokemon(defn.id, None) if False else (False, "")
                # objets non-médecine sans cible
                team = getattr(self.player, "team", []) or []
                mon = team[0] if team else None
                if mon and defn.id in ("repel", "town_map"):
                    ok, msg = self.inventory.use_on_pokemon(defn.id, mon)
                    self.message = msg
                    self.mode = "message"
                else:
                    self.message = defn.description_fr
                    self.mode = "message"
            else:
                self.message = defn.description_fr
                self.mode = "message"
            self._cooldown = 10

    def _draw(self) -> None:
        display = self.screen.get_display()
        if display is None or not self._font:
            return
        w, h = display.get_size()
        # overlay
        ov = pygame.Surface((w, h), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 160))
        display.blit(ov, (0, 0))

        panel_w, panel_h = 520, 420
        px = (w - panel_w) // 2
        py = (h - panel_h) // 2
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((18, 28, 48, 245))
        pygame.draw.rect(panel, (100, 160, 255), panel.get_rect(), 3)
        display.blit(panel, (px, py))

        title = self._font.render(f"Sac  —  {self.inventory.money} ₽", True, (255, 220, 80))
        display.blit(title, (px + 20, py + 16))

        # catégories
        cat_x = px + 20
        for i, (_, label) in enumerate(self.CATEGORIES):
            col = (255, 255, 120) if i == self.cat_index else (180, 180, 200)
            t = self._font_sm.render(label, True, col)
            display.blit(t, (cat_x, py + 50))
            cat_x += t.get_width() + 16

        items = self._filtered()
        if self.mode == "list":
            if not items:
                t = self._font.render("Sac vide.", True, (200, 200, 200))
                display.blit(t, (px + 30, py + 100))
            for i, (defn, qty) in enumerate(items[:10]):
                col = (255, 255, 100) if i == self.item_index else (230, 230, 230)
                prefix = "▶ " if i == self.item_index else "  "
                line = f"{prefix}{defn.name_fr}  ×{qty}"
                display.blit(self._font.render(line, True, col), (px + 30, py + 90 + i * 28))
            if items and 0 <= self.item_index < len(items):
                desc = items[self.item_index][0].description_fr
                display.blit(self._font_sm.render(desc[:50], True, (160, 180, 200)), (px + 30, py + panel_h - 50))
        elif self.mode == "target":
            display.blit(self._font.render("Sur quel Pokémon ?", True, (255, 255, 255)), (px + 30, py + 90))
            team = getattr(self.player, "team", []) or []
            for i, mon in enumerate(team):
                col = (255, 255, 100) if i == self._target_index else (220, 220, 220)
                prefix = "▶ " if i == self._target_index else "  "
                name = getattr(mon, "dbSymbol", "?").capitalize()
                line = f"{prefix}{name}  {mon.hp}/{mon.maxhp} PV"
                display.blit(self._font.render(line, True, col), (px + 30, py + 130 + i * 32))
        elif self.mode == "message":
            display.blit(self._font.render(self.message[:48], True, (255, 255, 255)), (px + 30, py + 160))
            display.blit(self._font_sm.render("E pour continuer", True, (180, 180, 100)), (px + 30, py + 200))

        hint = self._font_sm.render("←→ catégories  Z/S liste  E utiliser  ESC fermer", True, (140, 150, 170))
        display.blit(hint, (px + 20, py + panel_h - 28))
