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
}
