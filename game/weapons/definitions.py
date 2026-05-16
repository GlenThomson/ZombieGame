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
    reserve_max: int = 0       # total spare ammo carried; 0 means "infinite"
    pellets_per_shot: int = 1  # >1 for shotguns
    shoot_sound: str = "pistol_shot.mp3"
    effect_kind: str = "normal"  # "normal" | "chain" | "blast"


WEAPON_DEFS: dict[str, WeaponDef] = {
    # reserve_max = magazine_size * roughly 4..6 for most guns
    "Pistol":  WeaponDef("Pistol",  bullet_speed=25, bullet_spread=3,  fire_rate=4,    damage=1,  penetration=2, magazine_size=10,  reload_time=2,   reserve_max=80,  shoot_sound="pistol_shot.mp3"),
    "Shotgun": WeaponDef("Shotgun", bullet_speed=15, bullet_spread=12, fire_rate=1,    damage=3,  penetration=2, magazine_size=5,   reload_time=3,   reserve_max=30,  pellets_per_shot=15, shoot_sound="shotgun_sound.mp3"),
    "AK74u":   WeaponDef("AK74u",   bullet_speed=28, bullet_spread=4,  fire_rate=12,   damage=2,  penetration=2, magazine_size=30,  reload_time=2.4, reserve_max=180, shoot_sound="pistol_shot.mp3"),
    "Galil":   WeaponDef("Galil",   bullet_speed=30, bullet_spread=3,  fire_rate=10,   damage=3,  penetration=3, magazine_size=35,  reload_time=3.0, reserve_max=210, shoot_sound="pistol_shot.mp3"),
    "SMG":     WeaponDef("SMG",     bullet_speed=24, bullet_spread=6,  fire_rate=18,   damage=1,  penetration=1, magazine_size=40,  reload_time=2.0, reserve_max=240, shoot_sound="pistol_shot.mp3"),
    "LMG":     WeaponDef("LMG",     bullet_speed=27, bullet_spread=5,  fire_rate=10,   damage=4,  penetration=4, magazine_size=100, reload_time=5.5, reserve_max=400, shoot_sound="pistol_shot.mp3"),
    "Sniper":  WeaponDef("Sniper",  bullet_speed=40, bullet_spread=0,  fire_rate=1.2,  damage=20, penetration=6, magazine_size=5,   reload_time=3.5, reserve_max=30,  shoot_sound="pistol_shot.mp3"),
    "Ray Gun": WeaponDef("Ray Gun", bullet_speed=35, bullet_spread=0,  fire_rate=2.5,  damage=50, penetration=8, magazine_size=20,  reload_time=4.0, reserve_max=160, shoot_sound="pistol_shot.mp3"),
    # Last-stand sidearm. Infinite reserve (reserve_max=0 = no reserve concept,
    # so the magazine just refills freely). Underpowered on purpose — you're
    # supposed to crawl to safety, not finish the round from down.
    "M1911": WeaponDef("M1911", bullet_speed=22, bullet_spread=4, fire_rate=3, damage=1, penetration=1, magazine_size=8, reload_time=1.6, reserve_max=0, shoot_sound="pistol_shot.mp3"),
    # Wonder weapons (mystery box only). Wunderwaffe = single very lethal
    # bolt with high penetration. Thundergun = wide cone like a giant
    # shotgun.
    "Wunderwaffe": WeaponDef("Wunderwaffe", bullet_speed=45, bullet_spread=0, fire_rate=1.0, damage=200, penetration=1,  magazine_size=3, reload_time=4.5, reserve_max=15, shoot_sound="pistol_shot.mp3",   effect_kind="chain"),
    "Thundergun":  WeaponDef("Thundergun",  bullet_speed=22, bullet_spread=35, fire_rate=0.8, damage=80, penetration=10, magazine_size=2, reload_time=4.0, reserve_max=10, pellets_per_shot=20, shoot_sound="shotgun_sound.mp3", effect_kind="blast"),
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
    "Wunderwaffe",
    "Thundergun",
)


# CoD's iconic Pack-a-Punch name per base weapon. Used by Weapon.name when
# the weapon is_packed.
PACKED_NAMES: dict[str, str] = {
    "Pistol":      "Mustang & Sally",
    "Shotgun":     "Gut Shot",
    "AK74u":       "AK74fu2",
    "Galil":       "Lamentation",
    "SMG":         "Beat-zerker",
    "LMG":         "Hammer of Thor",
    "Sniper":      "The Armageddon",
    "Ray Gun":     "Porter's X2",
    "Wunderwaffe": "Wunderwaffe DG-3 JZ",
    "Thundergun":  "Zeus Cannon",
    "M1911":       "Mustang & Sally",
}
