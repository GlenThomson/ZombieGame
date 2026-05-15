"""Data-driven weapon stats. Add a new gun by adding an entry here."""
from dataclasses import dataclass


@dataclass(frozen=True)
class WeaponDef:
    name: str
    bullet_speed: float
    bullet_spread: float       # degrees
    fire_rate: float           # shots per second
    damage: int
    penetration: int           # zombies a single bullet passes through
    magazine_size: int
    reload_time: float         # seconds
    pellets_per_shot: int = 1  # >1 for shotguns
    shoot_sound: str = "pistol_shot.mp3"


WEAPON_DEFS: dict[str, WeaponDef] = {
    "Pistol": WeaponDef(
        name="Pistol",
        bullet_speed=25,
        bullet_spread=3,
        fire_rate=4,
        damage=1,
        penetration=2,
        magazine_size=10,
        reload_time=2,
        shoot_sound="pistol_shot.mp3",
    ),
    "Shotgun": WeaponDef(
        name="Shotgun",
        bullet_speed=15,
        bullet_spread=12,
        fire_rate=1,
        damage=3,
        penetration=2,
        magazine_size=5,
        reload_time=3,
        pellets_per_shot=15,
        shoot_sound="shotgun_sound.mp3",
    ),
    "AK74u": WeaponDef(
        name="AK74u",
        bullet_speed=28,
        bullet_spread=4,
        fire_rate=12,
        damage=2,
        penetration=2,
        magazine_size=30,
        reload_time=2.4,
        shoot_sound="pistol_shot.mp3",
    ),
    "Galil": WeaponDef(
        name="Galil",
        bullet_speed=30,
        bullet_spread=3,
        fire_rate=10,
        damage=3,
        penetration=3,
        magazine_size=35,
        reload_time=3.0,
        shoot_sound="pistol_shot.mp3",
    ),
    "SMG": WeaponDef(
        name="SMG",
        bullet_speed=24,
        bullet_spread=6,
        fire_rate=18,
        damage=1,
        penetration=1,
        magazine_size=40,
        reload_time=2.0,
        shoot_sound="pistol_shot.mp3",
    ),
    "LMG": WeaponDef(
        name="LMG",
        bullet_speed=27,
        bullet_spread=5,
        fire_rate=10,
        damage=4,
        penetration=4,
        magazine_size=100,
        reload_time=5.5,
        shoot_sound="pistol_shot.mp3",
    ),
    "Sniper": WeaponDef(
        name="Sniper",
        bullet_speed=40,
        bullet_spread=0,
        fire_rate=1.2,
        damage=20,
        penetration=6,
        magazine_size=5,
        reload_time=3.5,
        shoot_sound="pistol_shot.mp3",
    ),
    "Ray Gun": WeaponDef(
        name="Ray Gun",
        bullet_speed=35,
        bullet_spread=0,
        fire_rate=2.5,
        damage=50,
        penetration=8,
        magazine_size=20,
        reload_time=4.0,
        shoot_sound="pistol_shot.mp3",
    ),
}


# Subset that the Mystery Box can roll. Pistol is excluded (it's the
# starting weapon). Shotgun/AK74u/etc. are wall-buy candidates so they're
# also valid mystery-box drops.
MYSTERY_BOX_POOL: tuple[str, ...] = (
    "Shotgun",
    "AK74u",
    "Galil",
    "SMG",
    "LMG",
    "Sniper",
    "Ray Gun",
)
