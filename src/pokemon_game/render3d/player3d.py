"""Third-person player controller for the 3D overworld."""
from __future__ import annotations

from ursina import Entity, Vec3, held_keys, time, color, camera

from pokemon_game.render3d.world import WorldGrid


class Player3D(Entity):
    def __init__(self, world: WorldGrid, **kwargs):
        super().__init__(
            model="cube",
            color=color.azure,
            scale=(0.6, 1.2, 0.6),
            origin_y=-0.5,
            collider="box",
            **kwargs,
        )
        self.world = world
        self.speed = 4.5
        self.y = 0.6
        self.camera_pivot = Entity(parent=self, y=1.4)
        camera.parent = self.camera_pivot
        camera.position = (0, 2.2, -6)
        camera.rotation_x = 18
        camera.fov = 70

    def input(self, key):
        pass

    def update(self):
        move = Vec3(
            held_keys["d"] - held_keys["a"] + held_keys["right arrow"] - held_keys["left arrow"],
            0,
            held_keys["w"] - held_keys["s"] + held_keys["up arrow"] - held_keys["down arrow"],
        )
        if move.length() > 0:
            move = move.normalized()
            forward = Vec3(camera.forward.x, 0, camera.forward.z)
            if forward.length() > 0:
                forward = forward.normalized()
            right = Vec3(camera.right.x, 0, camera.right.z)
            if right.length() > 0:
                right = right.normalized()
            direction = forward * move.z + right * move.x
            if direction.length() > 0:
                direction = direction.normalized()
                nx = self.x + direction.x * self.speed * time.dt
                nz = self.z + direction.z * self.speed * time.dt
                gx, gy = self.world.world_to_grid(nx, nz)
                if not self.world.is_blocked(gx, gy):
                    self.x = nx
                    self.z = nz
                self.look_at(Vec3(self.x + direction.x, self.y, self.z + direction.z))
