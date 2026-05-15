# Roadmap — Path to top-down CoD Zombies

The post-restructure foundation supports each item below. Anything tagged
**hooks ready** has the architecture in place — implementing it is mostly
plugging in data + a handler. Anything tagged **needs new system** is a bigger
build.

Key questions before each feature: how much does it change the **feel** of
playing? How much does it open up **future** features? That's how the
priority tiers below are ordered.

---

## Tier 0 — Quality-of-life polish (1–2 hours total)

These don't add features but make the game feel finished. Worth doing first.

- **Player walking animation** — 4-frame sprite sheet, swap frames while
  moving. Currently the player slides like a hovercraft.
- **Muzzle flash** — single-frame sprite at the barrel position when shooting.
- **Bullet hit visual** — small particle/spark on zombie hit (we already have
  blood; this would be lighter feedback for non-fatal hits).
- **Sound polish** — pickup pickup-sfx, footstep loop while moving, low-health
  heartbeat.

---

## Tier 1 — Points system + minimum-viable CoD loop  (2–3 hours)

This is the single biggest gameplay shift. Without points, zombies are an
arena shooter. With points, the loop becomes the CoD loop: kill → earn →
spend → kill harder zombies → repeat.

### 1.1 Points

- **Add `player.points: int = 500`** (CoD starting points).
- **+10 per hit, +50 per kill, +100 for headshots** (later).
- **Display in HUD** (gold text bottom-left, beside Round/Kills).
- *Hooks ready:* HUD has the panel; `Zombie.take_damage` is the one place to
  award hit + kill points.

### 1.2 Doors

- **New TileType.DOOR_CLOSED, DOOR_OPEN** (slots already reserved).
- Doors block movement + pathfinding when closed.
- Player can hold **F** while standing near to spend N points to open.
- Once open, the tile becomes EMPTY for both player and zombies.
- Cost stored alongside the door tile (a parallel "door cost grid" or a
  per-tile metadata dict — we'll pick when implementing).
- *Needs:* MapMaker UI to place doors + set their cost. Pathfinding already
  reads `TileType.is_blocking` so just include closed doors there.

### 1.3 Window barriers

- **New TileType.WINDOW.** Acts like a wall but with HP.
- Zombies near a window break planks at intervals; once HP=0 it becomes empty.
- Player near it can hold **F** to repair (rebuild planks), earns points.
- *Needs:* Window entity (small, with HP bar), zombie AI nudge to prefer
  windows when one is in their path.

### 1.4 Wall buys

- A weapon listed on a wall — walk near, hold **F**, pay N points → weapon
  added to inventory (or ammo refilled if already owned).
- **New TileType.WALL_BUY** with weapon name + price metadata.
- *Hooks ready:* `Inventory.add` and `WEAPON_DEFS` already do everything we
  need.

**Why this tier first:** Doors + window barriers + wall buys all share the
same "interact key (F) + spend points" mechanic. Build them together; one
input system serves all three.

---

## Tier 2 — Variety + core CoD systems  (3–5 hours)

### 2.1 Zombie variants  *(hooks ready)*

- **Crawler** — slow, low HP, Tier 1.5+
- **Runner** — fast, low HP, scary in groups, Tier 3+
- **Hellhound** — special round only; very fast; runs straight at you
  ignoring path; bursts into electricity on death (drops max-ammo)
- *Implementation:* subclass `Zombie`, override `image_name`, `speed_base`,
  `health` multipliers. RoundManager gets a `_choose_zombie_class()` based on
  current round + RNG.

### 2.2 Mystery Box

- Tile that, when activated for 950 points, plays the spinning-gun animation
  and gives the player a random weapon from a wider pool.
- After ~5 uses, the box "moves" to another mystery-box tile on the map (CoD
  staple — keeps the box from being a permanent location).
- **New WeaponDefs**: AK74u, Ray Gun, Galil, Crossbow, etc.
- *Needs:* a `MysteryBox` entity (sprite + animation + cost), an "active box
  pool" managed by a new `MysteryBoxSystem` that picks the location.

### 2.3 Pack-a-Punch  *(hooks ready)*

- Tile that takes the equipped gun + 5000 points and returns an upgraded
  version (more damage, larger mag, sometimes new effect).
- *Implementation:* `WeaponDef.upgraded_to: str | None` field referencing
  another def. Or, since `ModifierStack` already exists, "upgraded" is just a
  set of modifiers tagged `"PaP"`.

### 2.4 Perks  *(hooks ready — `ModifierStack` was built for this)*

| Perk            | Modifier                        | Cost  |
|-----------------|----------------------------------|-------|
| Juggernog       | `max_health × 2.5`              | 2500  |
| Speed Cola      | `reload_time × 0.5`             | 3000  |
| Double Tap      | `fire_rate × 1.33`, `damage × 2`| 2000  |
| Stamin-Up       | `speed × 1.4`                   | 2000  |
| Quick Revive    | revive teammate faster (MP only)| 500/1500 |
| Mule Kick       | `inventory.MAX_SLOTS = 3`       | 4000  |

- Perks are bought from labelled tiles. Each perk plays a stinger sound +
  shows an icon in the HUD.
- *Implementation:* `Perk` dataclass: `name`, `cost`, `apply(player)`,
  `sound_name`. A `PerkSystem` tracks owned perks, draws icons in HUD.
- Lose all perks on death (CoD rule).

### 2.5 Power-ups (drop variety)

We already have instant-kill and nuke. Add:

- **Max Ammo** — refills all guns to full (incl. reserve when we add reserves)
- **Carpenter** — repairs all window barriers, awards 200 points
- **Fire Sale** — mystery box drops to 10 points for 30 seconds
- **Double Points** — points x2 for 30 seconds
- *Hooks ready:* one `@effect("name")` per power-up, drop the PNG, done.

---

## Tier 3 — Full content pass  (5–8 hours)

### 3.1 More weapons

Each is a single `WeaponDef` entry + sound + icon. Suggested set:

- SMG (high fire rate, low damage)
- LMG (huge mag, slow reload)
- Sniper (one-shot most rounds, slow)
- Crossbow (one-shot + zombies attack the bolt)
- Ray Gun (high damage, splash)
- Wonder weapon (Wunderwaffe-equivalent, lightning chain)

### 3.2 Reserve ammo

Today guns hold 1 magazine. Add `reserve_ammo` per weapon, refilled by Max
Ammo + when buying from wall buy.

### 3.3 Round-3-or-9 special rounds

RoundManager picks a "dogs round" every Nth round — only Hellhounds spawn,
fewer of them, all on the player. End-of-round Max Ammo guaranteed.

### 3.4 Down state + revive (foundation for MP)

- When health hits 0: player goes "down" — can't move, has pistol only,
  bleeds out over 30 seconds.
- In single player today, that means death (no one to revive). Build the
  state anyway — it's the seam multiplayer needs.

---

## Tier 4 — Local co-op multiplayer  (4–6 hours)

This is where the Player class really starts to need its own input source
abstraction (we sketched `InputSnapshot` but it's still global).

### 4.1 Split inputs

- **Player 1**: WASD + mouse (existing)
- **Player 2**: arrows + numpad-Enter (or controller via pygame.joystick)
- Each `Player` gets its own input source object.

### 4.2 Camera

- Two players share one screen (CoD doesn't split-screen for top-down). Camera
  follows the **midpoint** of the players, zooms out if they spread too far.

### 4.3 Revives

- Hold F next to a downed teammate to revive (3 seconds).
- If both players are down → game over.

### 4.4 Networked online (later, if you want it)

This is a much bigger lift — authoritative server, state sync, lag
compensation. Local co-op gets you 90% of the social experience without the
headache. If you want to go online later, the state-sync layer is the work;
the entity model itself doesn't need to change much because of how we
already separated systems.

---

## Suggested implementation order

1. **Tier 1 entirely** (points + doors + windows + wall buys) — biggest feel
   change for the effort.
2. **Tier 2.1 + 2.4** (zombie variants + perks) — both are mostly data-driven
   given current architecture.
3. **Tier 2.2 + 2.3** (mystery box + pack-a-punch) — content-heavy, needs
   asset sourcing.
4. **Tier 0 polish** — by now the game has enough mass to deserve animation +
   audio investment.
5. **Tier 3** — tune content variety once core is fun.
6. **Tier 4** — add second player.

---

## Asset sourcing checklist

Before each tier:

- **Tier 1**: door sprite (closed/open), window+plank sprites, wall-buy gun
  icons. **Source:** Kenney "Top-Down Shooter" pack (CC0).
- **Tier 2.1**: hellhound sprite (4-frame run anim ideal). **Source:** Kenney
  "Animal" pack or similar.
- **Tier 2.4**: perk machine icons (6 of them). **Source:** AI generation
  (DALL-E / Stable Diffusion) for unique CoD-styled icons; I'll write the
  prompts.
- **Tier 2.5**: power-up icons (max ammo / carpenter / fire-sale / double
  points). **Source:** AI generation.
- **Tier 3**: gun icons + shoot sounds for each new weapon. **Source:**
  Freesound (CC0) for sounds, AI for icons.

---

## Out-of-scope ideas (parking lot)

- **Easter-egg main quest** (CoD's signature) — way too big for now.
- **Boss zombies** (Brutus, Margwa) — fun but huge art lift.
- **Mod support / Lua scripting** — interesting but distracts from gameplay.
- **In-game leaderboard** — needs a backend.
