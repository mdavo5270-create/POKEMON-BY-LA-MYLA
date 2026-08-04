# Guide rapide pour les mappeurs

1. Ouvre **Tiled 1.12+**
2. File → Open Project → `assets/map/POKEMON-BY-LA-MYLA.tiled-project`
3. Respecte strictement les conventions de nommage (voir [TILED_WORKFLOW.md](TILED_WORKFLOW.md))
4. Layers de tiles : `ground`, `decoration`, `water`, `above_player`…
5. Objects : toujours remplir `name` + `type`
6. Teste dans le jeu après chaque map importante

### Exemple d’objet switch
- name : `switch map_1 0`
- type : `switch`

### Exemple d’objet collision
- name : `collision`
- type : `collision`

### Exemple d’objet dialogue
- name : `dialogue 1001`
- type : `dialogue`
