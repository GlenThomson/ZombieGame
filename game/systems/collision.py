"""Wall/hitbox collision helpers used by movable entities."""
import pygame


def _collide_hit_box(sprite1, sprite2):
    return sprite1.hit_box.colliderect(sprite2.rect)


def resolve_wall_collision(sprite, wall_group, axis: str) -> bool:
    """Push `sprite` out of any wall in `wall_group` along the given axis.
    `axis` is 'x' or 'y'. Returns True if a collision was resolved."""
    hits = pygame.sprite.spritecollide(sprite, wall_group, False, _collide_hit_box)
    if not hits:
        return False

    wall = hits[0]
    if axis == "x":
        if wall.rect.centerx > sprite.hit_box.centerx:
            sprite.pos.x = wall.rect.left - sprite.hit_box.width / 2.0
        else:
            sprite.pos.x = wall.rect.right + sprite.hit_box.width / 2.0
        sprite.vel.x = 0
        sprite.hit_box.centerx = sprite.pos.x
    elif axis == "y":
        if wall.rect.centery > sprite.hit_box.centery:
            sprite.pos.y = wall.rect.top - sprite.hit_box.height / 2.0
        else:
            sprite.pos.y = wall.rect.bottom + sprite.hit_box.height / 2.0
        sprite.vel.y = 0
        sprite.hit_box.centery = sprite.pos.y
    return True
