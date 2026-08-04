# Guide Tiled – POKEMON BY LA MYLA

## 1. Mise à jour recommandée

Télécharge **Tiled 1.12+** : https://www.mapeditor.org/

Ouvre le projet avec :
`File → Open Project → assets/map/POKEMON-BY-LA-MYLA.tiled-project`

## 2. Organisation standard des Layers

| Layer / Group     | Type          | Rôle                                      |
|-------------------|---------------|-------------------------------------------|
| `ground`          | Tile Layer    | Sol de base                               |
| `path`            | Tile Layer    | Chemins, routes                           |
| `decoration`      | Tile Layer    | Herbe, fleurs, petits détails             |
| `water`           | Tile Layer    | Eau (animée si possible)                  |
| `above_player`    | Tile Layer    | Toits, arbres devant le joueur            |
| `collision`       | Object Layer  | Collisions (rectangles)                   |
| `warps`           | Object Layer  | Switches / portes / téléportations        |
| `spawns`          | Object Layer  | Points d’apparition                       |
| `dialogues`       | Object Layer  | Zones de dialogue / interactions          |
| `npcs`            | Object Layer  | Positions des PNJ                         |
| `triggers`        | Object Layer  | Événements spéciaux                       |

**Règle** : tout ce qui est logique (collision, warp, dialogue…) va dans un **Object Layer**.

## 3. Convention de nommage des Objects (OBLIGATOIRE)

### Collisions
```
name  = collision
type  = collision
```

### Changements de map (warps / switches)
```
name  = switch <map_name> <port>
type  = switch
```
Exemple : `switch map_1 0`

### Spawns
```
name  = spawn <from_map> <port>
type  = spawn
```
Exemple : `spawn map_0 1`

### Dialogues
```
name  = dialogue <id>
type  = dialogue
```
Exemple : `dialogue 1001`

### PNJ
```
name  = npc <id>
type  = npc
```

### Items / Triggers
```
name  = item <id>     ou   trigger <id>
type  = item          ou   trigger
```

## 4. Propriétés personnalisées recommandées

### Sur les Tiles (Tile Properties)
| Propriété     | Type    | Exemple        | Usage dans le code          |
|---------------|---------|----------------|-----------------------------|
| `tile_type`   | enum    | tall_grass     | Chance de combat sauvage    |
| `collision`   | bool    | true           | Collision par tile          |
| `speed_mod`   | float   | 0.5            | Ralentissement (sable, eau) |
| `sound`       | string  | grass_step     | Son de pas                  |

### Sur les Objects
| Propriété     | Type    | Usage                          |
|---------------|---------|--------------------------------|
| `dialogue_id` | int     | ID du dialogue à charger       |
| `map_target`  | string  | Map de destination             |
| `port`        | int     | Port de spawn                  |
| `direction`   | string  | Direction du PNJ               |
| `item_id`     | string  | Item donné                     |

## 5. Automapping

1. Place tes règles dans `assets/map/rules/`
2. Liste-les dans `assets/map/rules/rules.txt`
3. Dans Tiled : `Map → AutoMap` (ou active « AutoMap while drawing »)

## 6. Bonnes pratiques

- Toujours utiliser des **tilesets externes** (`.tsx`)
- Taille de tile standard : **16×16**
- Ne jamais mettre de logique dans les noms de layers de tiles
- Préfixer les groups si besoin (`layer0`, `layer1`…)
- Tester immédiatement après modification avec le jeu

## 7. Chargement dans le code

Voir `src/pokemon_game/core/map.py` et le helper `load_map_objects()` / `parse_objects()`.

Les objets sont automatiquement classés selon leur `type` / `name`.
