# ZombieGame

Top-down zombies in pygame.

## Run

```
python main.py
```

(or hit F5 in VS Code on `main.py` after selecting the `.venv` interpreter)

## Project layout

```
main.py              entry point
settings.py          tunable constants
assets/              images + sounds
maps/                .pkl map files (saved by the in-game Map Maker)
game/
  app.py             main loop + state machine
  camera.py
  assets.py          cached image / sound loader
  utils.py
  states/            menu, map_select, play, game_over, mapmaking
  entities/          player, zombie, bullet, grenade, wall, effects
  systems/           pathfinding, collision, round_manager, input
  weapons/           data-driven gun definitions + Weapon + Inventory
  pickups/           pickup + effect registry
  stats/             ModifierStack (foundation for perks)
  ui/                HUD, menu widgets, map-maker toolbar
  world/             TileType, map_loader
_playtest.py         headless regression harness (run with python _playtest.py)
```

## Adding a new weapon

Add an entry to `WEAPON_DEFS` in [game/weapons/definitions.py](game/weapons/definitions.py),
drop the shoot sound in `assets/sounds/`, and call `player.inventory.add("YourGun")`
wherever you want it picked up.

## Adding a new pickup

Write a function in [game/pickups/effects.py](game/pickups/effects.py) and tag it
with `@effect("name", weight=1.0)`. Drop a matching `name.png` in `assets/images/`.
