"""Third-person player — 2D sprite billboard (same art as the 2D game)."""
from __future__ import annotations

from ursina import Entity, Vec3, held_keys, time, color, camera, load_texture

from pokemon_game.core.tool import ASSETS
from pokemon_game.render3d.world import WorldGrid


def _tex(name: str):
    path = ASSETS / "render3d" / name
    if path.exists():
        return load_texture(str(path))
    return None


class Player3D(Entity):
    """Trainer as upright billboard using hero walk sprites from 2D assets."""

    def __init__(self, world: WorldGrid, **kwargs):
        super().__init__(model=None, collider="box", scale=(1, 1, 1), **kwargs)
        self.world = world
        self.speed = 5.0
        self.y = 0.0
        self.locked = False
        self._facing = "down"
        self._bob = 0.0

        self.sprite = Entity(
            parent=self,
            model="quad",
            texture=_tex("hero_down.png"),
            scale=(0.9, 1.15),
            position=(0, 0.7, 0),
            double_sided=True,
            color=color.white,
        )
        self.shadow = Entity(
            parent=self,
            model="circle",
            color=color.rgba(0, 0, 0, 90),
            scale=0.7,
            position=(0, 0.02, 0),
            rotation_x=90,
        )

        self.camera_pivot = Entity(parent=self, y=1.4)
        camera.parent = self.camera_pivot
        camera.position = (0, 3.0, -8)
        camera.rotation_x = 22
        camera.fov = 65

    def _set_facing(self, direction: Vec3) -> None:
        if abs(direction.x) > abs(direction.z):
            self._facing = "right" if direction.x > 0 else "left"
        else:
            self._facing = "down" if direction.z > 0 else "up"
        tex = _tex(f"hero_{self._facing}.png")
        if tex is not None:
            self.sprite.texture = tex

    def update(self):
        if self.locked or not self.world:
            return
        if self.sprite:
            self.sprite.look_at(camera.world_position)
            self.sprite.rotation_x = 0
            self.sprite.rotation_z = 0

        move = Vec3(
            held_keys["d"] - held_keys["a"] + held_keys["right arrow"] - held_keys["left arrow"],
            0,
            held_keys["w"] - held_keys["s"] + held_keys["up arrow"] - held_keys["down arrow"],
        )
        if move.length() <= 0:
            return
        move = move.normalized()
        forward = Vec3(camera.forward.x, 0, camera.forward.z)
        if forward.length() > 0:
            forward = forward.normalized()
        right = Vec3(camera.right.x, 0, camera.right.z)
        if right.length() > 0:
            right = right.normalized()
        direction = forward * move.z + right * move.x
        if direction.length() <= 0:
            return
        direction = direction.normalized()
        nx = self.x + direction.x * self.speed * time.dt
        nz = self.z + direction.z * self.speed * time.dt
        gx, gy = self.world.world_to_grid(nx, nz)
        if not self.world.is_blocked(gx, gy):
            self.x = nx
            self.z = nz
        self._set_facing(direction)
        self._bob += time.dt * 10
        self.sprite.y = 0.7 + 0.03 * __import__("math").sin(self._bob)
