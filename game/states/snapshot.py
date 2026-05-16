"""Build snapshots of a PlayState for network broadcast, and apply received
snapshots to a ClientPlayState's render-only world model.

A snapshot is a plain dict of dicts/tuples — no game-engine objects — so
it's cheap to pickle and so the client doesn't need to instantiate Player /
Zombie / etc. just to draw."""
import pygame

from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    REVIVE_HOLD_MS,
    PLAYER_TINTS,
)
from game.systems.interaction import find_focused
from game.systems.input import InputState


def build_snapshot(scene) -> dict:
    return {
        "type": "snapshot",
        "tick": pygame.time.get_ticks(),
        "players": [_player_dict(p, scene) for p in scene.players],
        "zombies": [
            {
                "type": type(z).__name__,
                "pos": (float(z.pos.x), float(z.pos.y)),
                "angle": float(z.angle),
            }
            for z in scene.zombies
        ],
        "bullets": [
            {"pos": (float(b.pos.x), float(b.pos.y))}
            for b in scene.bullets
        ],
        "pickups": [
            {
                "kind": p.kind,
                "pos": (int(p.rect.x), int(p.rect.y)),
                "visible": bool(p.visible),
            }
            for p in scene.pickups
        ],
        "grenades": [
            {
                "pos": (float(g.pos.x), float(g.pos.y)),
                "exploding": bool(getattr(g, "exploding", False)),
                "frame": int(getattr(g, "frame_index", 0)),
            }
            for g in scene.grenades
        ],
        "monkey_bombs": [
            {"pos": (float(m.pos.x), float(m.pos.y))}
            for m in scene.monkey_bombs
        ],
        "blood": [
            {"pos": (float(b.original_pos.x), float(b.original_pos.y)), "alpha": int(b.alpha)}
            for b in scene.blood_splatters
        ],
        "muzzle": [
            {"pos": (int(m.rect.centerx), int(m.rect.centery))}
            for m in scene.muzzle_flashes
        ],
        "floats": [
            {
                "text": f.text,
                "pos": (float(f.world_pos.x), float(f.world_pos.y)),
                "color": tuple(f.color),
            }
            for f in scene.floating_texts
        ],
        "interactables": _interactables_list(scene),
        "interaction_prompts": {
            p.player_id: (find_focused(
                (p.rect.centerx, p.rect.centery), scene.interactables, 60
            ).get_prompt(p) if find_focused(
                (p.rect.centerx, p.rect.centery), scene.interactables, 60
            ) else None) for p in scene.players
        },
        "round": scene.round_manager.current_round,
        "kill_count": scene.kill_count,
        "round_text_countdown": scene.round_manager.round_text_countdown,
        "damage_flash_alpha": scene.damage_flash_alpha,
        "points_multiplier": scene.points_multiplier,
        "power_on": getattr(scene, "power_on", True),
    }


def _player_dict(player, scene) -> dict:
    weapon = player.weapon
    perks = scene.perk_system_by_player.get(player.player_id)
    return {
        "id": player.player_id,
        "name": player.name,
        "pos": (float(player.pos.x), float(player.pos.y)),
        "angle": float(player.angle),
        "health": float(player.health),
        "max_health": float(player.max_health),
        "points": int(player.points),
        "weapon": weapon.name if weapon else None,
        "weapon_image": "player.png",  # placeholder for muzzle/icon refs
        "ammo": weapon.current_ammo if weapon else 0,
        "mag": weapon.magazine_size if weapon else 0,
        "reserve": weapon.reserve_ammo if weapon else 0,
        "reserve_max": weapon.reserve_max if weapon else 0,
        "is_reloading": bool(weapon.is_reloading) if weapon else False,
        "is_packed": bool(weapon.is_packed) if weapon else False,
        "perks": [(p.name, tuple(p.icon_color)) for p in (perks.owned() if perks else [])],
        "inventory": [s.name if s else None for s in player.inventory.slots],
        "inventory_equipped": player.inventory.equipped_index,
        "is_down": bool(player.is_down),
        "revive_progress_ms": int(player.revive_progress_ms),
        "grenades": int(player.grenade_count),
        "monkey_bombs": int(player.monkey_bomb_count),
        "is_dead": bool(player.is_dead()),
    }


def _interactables_list(scene) -> list[dict]:
    out = []
    for door in scene.doors:
        out.append({
            "type": "door",
            "pos": (door.rect.x, door.rect.y),
            "cost": door.cost,
        })
    for wb in scene.wall_buys:
        out.append({
            "type": "wall_buy",
            "pos": (wb.rect.x, wb.rect.y),
            "weapon": wb.weapon_name,
        })
    for win in scene.windows:
        out.append({
            "type": "window",
            "pos": (win.rect.x, win.rect.y),
            "planks": win.planks,
        })
    for pm in scene.perk_machines:
        out.append({
            "type": "perk_machine",
            "pos": (pm.rect.x, pm.rect.y),
            "perk": pm.perk.name,
            "color": tuple(pm.perk.icon_color),
            "cost": pm.perk.cost,
        })
    for mb in scene.mystery_boxes:
        out.append({
            "type": "mystery_box",
            "pos": (mb.rect.x, mb.rect.y),
            "state": mb.state,
            "label": mb.current_label,
            "weapon": mb.committed_weapon,
            "cost": mb.cost,
        })
    for pap in scene.pack_a_punch_machines:
        out.append({
            "type": "pack_a_punch",
            "pos": (pap.rect.x, pap.rect.y),
            "cost": pap.cost,
        })
    for sw in scene.power_switches:
        out.append({
            "type": "power_switch",
            "pos": (sw.rect.x, sw.rect.y),
            "on": getattr(sw.scene, "power_on", False),
        })
    for t in scene.traps:
        out.append({
            "type": "trap",
            "kind": t.kind,
            "pos": (t.rect.x, t.rect.y),
            "active": t.is_active,
            "cost": t.cost,
        })
    return out
