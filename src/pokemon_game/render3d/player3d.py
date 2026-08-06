"""Third-person player — 2D sprite billboard with walk cycle."""
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
    """Trainer billboard using hero walk sprites from the 2D game."""

    def __init__(self, world: WorldGrid, **kwargs):
        super().__init__(model=None, collider="box", scale=(1, 1, 1), **kwargs)
        self.world = world
        self.speed = 5.2
        self.y = 0.0
        self.locked = False
        self._facing = "down"
        self._frame = 0
        self._frame_t = 0.0
        self._moving = False

        self.sprite = Entity(
            parent=self,
            model="quad",
            texture=_tex("hero_down.png"),
            scale=(0.95, 1.2),
            position=(0, 0.75, 0),
            double_sided=True,
            color=color.white,
        )
        self.shadow = Entity(
            parent=self,
            model="circle",
            color=color.rgba(0, 0, 0, 100),
            scale=0.75,
            position=(0, 0.03, 0),
            rotation_x=90,
        )

        self.camera_pivot = Entity(parent=self, y=1.5)
        camera.parent = self.camera_pivot
        camera.position = (0, 4.2, -9.5)
        camera.rotation_x = 28
        camera.fov = 62

    def _apply_frame(self) -> None:
        if self._moving:
            name = f"hero_{self._facing}_{self._frame}.png"
            tex = _tex(name) or _tex(f"hero_{self._facing}.png")
        else:
            tex = _tex(f"hero_{self._facing}.png")
        if tex is not None:
            self.sprite.texture = tex

    def _set_facing(self, direction: Vec3) -> None:
        if abs(direction.x) > abs(direction.z):
            self._facing = "right" if direction.x > 0 else "left"
        else:
            self._facing = "down" if direction.z > 0 else "up"
        self._apply_frame()

    def update(self):
        if self.sprite:
            self.sprite.look_at(camera.world_position)
            self.sprite.rotation_x = 0
            self.sprite.rotation_z = 0

        if self.locked or not self.world:
            self._moving = False
            return

        move = Vec3(
            held_keys["d"] - held_keys["a"] + held_keys["right arrow"] - held_keys["left arrow"],
            0,
            held_keys["w"] - held_keys["s"] + held_keys["up arrow"] - held_keys["down arrow"],
        )
        if move.length() <= 0:
            self._moving = False
            self._frame = 0
            self._apply_frame()
            return
        self._moving = True
        self._frame_t += time.dt
        if self._frame_t >= 0.12:
            self._frame_t = 0.0
            self._frame = (self._frame + 1) % 4

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
