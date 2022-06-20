# `cartographer` 🗺️🌎

Map makers toolkit

## Sections of a `RMS` Script

```
1. <PLAYER_SETUP>
2. <LAND_GENERATION>
3. <ELEVATION_GENERATION>
4. <CLIFF_GENERATION>
5. <TERRAIN_GENERATION>
6. <OBJECTS_GENERATION>
```

Sections are not required to be in order, and not all sections are required for map generation.

## Script location

Steam:
`steamapps\common\AoE2DE\resources\_common\random-map-scripts`  
Local (for me):
`G:\Games\steamapps\common\AoE2DE\resources\_common\random-map-scripts`

Default rms scripts are in:  
`steamapps\common\AoE2DE\resources\_common\drs\gamedata_x2`

### Sym Link scripts from git repo to game folder

`mklink "G:\Games\steamapps\common\AoE2DE\resources\_common\random-map-scripts\Cartographer.rms" "D:\python\cartographer\maps\Cartographer.rms"`

mklink "G:\Games\steamapps\common\AoE2DE\resources_common\random-map-scripts\Arena.rms" "D:\python\cartographer\maps\Arena.rms"

### Where to find Standard Random Map Scripts
**DE (Steam):** `AoE2DE\resources\_common\drs\gamedata_x2`

## References

- Guide https://docs.google.com/document/d/1jnhZXoeL9mkRUJxcGlKnO98fIwFKStP_OBozpr0CHXo/edit#
- VScode extension https://marketplace.visualstudio.com/items?itemName=anda.rms-check-vscode
- RMS Scripts https://github.com/Naramsim/AoE2-random-map-scripts/tree/master/The%20forgotten

## Dire Straits

> Combining `direct_placement` with offline out-of-engine map generation and validation (by bizs)

> Explores the trade-offs between randomness and map balance.

https://docs.google.com/document/d/1E_Si9iXmzUqFuptkW-8F6XdmoxDXNUG36XIhnh86krU/edit
