# Automapping Rules - POKEMON BY LA MYLA

## Comment créer une règle

1. Dans Tiled → File → New → Map (même taille de tile 16x16)
2. Crée un layer nommé **input_*** (ex: `input_ground`)
3. Place les tiles "input" (les motifs à détecter)
4. Crée un ou plusieurs layers **output_*** (ex: `output_decoration`)
5. Place les tiles qui doivent être placés automatiquement
6. Enregistre dans `assets/map/rules/`
7. Ajoute le nom du fichier dans `rules.txt`

## Exemple simple : bords d'herbe

- input_ground : tiles d'herbe
- output_decoration : tiles de bordure automatique

Documentation officielle :
https://doc.mapeditor.org/en/stable/manual/automapping/
