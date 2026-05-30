# ZombieGame

Top-down zombies in pygame. Single-player or LAN multiplayer (up to 4).
Runs on Windows, macOS, and Linux.

## Run

### Pre-built binaries (easiest — no Python needed)
Grab the build for your OS from the
[Releases page](../../releases/latest):

- **Windows**: download `Zombies-Windows.exe`, double-click.
  (Windows SmartScreen may show "Unrecognized publisher" on first run —
  click "More info" → "Run anyway".)
- **macOS**: download `Zombies-macOS`. First run only, you may need to
  right-click → Open (Gatekeeper blocks unsigned binaries by default),
  then "Open" in the dialog that appears.
- **Linux**: download `Zombies-Linux`, then in a terminal:
  `chmod +x Zombies-Linux && ./Zombies-Linux`

These are auto-built by GitHub Actions on every push, so the latest
Release always matches the latest code.

### Windows (from source)
Double-click `run.bat`. First run creates a `.venv` and installs pygame;
subsequent runs just launch the game.

### macOS / Linux (from source)
In Terminal, from the repo root:

```
./run.sh
```

(Needs Python 3.10+ on your PATH. If `./run.sh` says permission denied,
do `chmod +x run.sh` first.)

### Multiplayer notes
- Same-network play: click HOST on one PC, click JOIN on the other —
  the game will show up in the discovered-games list automatically.
- Cross-network play: easiest is installing [Tailscale](https://tailscale.com)
  on both PCs. The game thinks it's on a LAN and discovery still works.
- Windows + Mac players can play together; the protocol is platform-agnostic.

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
