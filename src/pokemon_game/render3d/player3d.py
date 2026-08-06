"""Third-person player controller for the 3D overworld."""
from __future__ import annotations

from ursina import Entity, Vec3, held_keys, time, color, camera


from pokemon_game.render3d.world import WorldGrid


class Player3D(Entity):
    """Capsule-like trainer (body + head) with camera rig."""

    def __init__(self, world: WorldGrid, **kwargs):
        super().__init__(
            model=None,
            collider="box",
            scale=(0.7, 1.0, 0.7),
            **kwargs,
        )
        self.world = world
        self.speed = 5.0
        self.y = 0.0
        self.locked = False  # True during battle / dialogue

        # Visual hierarchy (procedural "model")
        self.body = Entity(
            parent=self,
            model="cube",
            color=color.rgb(40, 120, 220),
            scale=(0.55, 0.85, 0.4),
            position=(0, 0.55, 0),
        )
        self.head = Entity(
            parent=self,
            model="sphere",
            color=color.rgb(255, 210, 180),
            scale=(0.35, 0.35, 0.35),
            position=(0, 1.15, 0),
        )
        self.hat = Entity(
            parent=self.head,
            model="cube",
            color=color.rgb(200, 40, 40),
            scale=(1.2, 0.25, 1.2),
            position=(0, 0.35, 0),
        )

        self.camera_pivot = Entity(parent=self, y=1.5)
        camera.parent = self.camera_pivot
        camera.position = (0, 2.5, -7)
        camera.rotation_x = 20
        camera.fov = 70

    def update(self):
        if self.locked or not self.world:
            return
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
        self.look_at(Vec3(self.x + direction.x, self.y, self.z + direction.z))
