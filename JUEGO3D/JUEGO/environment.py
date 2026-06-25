from ursina import *
import random


class Asteroid(Entity):
    """Clase individual para un asteroide con hitbox esférica"""

    def __init__(self, pos):
        super().__init__(
            model='sphere',
            color=color.orange,
            scale=random.uniform(1.5, 6),
            position=pos,
            collider='sphere'
        )
        self.rotation = (random.randint(0, 360), random.randint(0, 360), random.randint(0, 360))
        self.is_asteroid = True


class AsteroidManager:
    """Clase encargada de poblar el espacio con obstáculos"""

    def __init__(self, count, radius):
        self.count = count
        self.radius = radius
        self.asteroids = []
        self.spawn_asteroids()

    def spawn_asteroids(self):
        for _ in range(self.count):
            pos = (
                random.randint(-self.radius, self.radius),
                random.randint(-self.radius, self.radius),
                random.randint(-self.radius, self.radius)
            )
            self.asteroids.append(Asteroid(pos))

    def clear_and_respawn(self):
        """NUEVO: Elimina los asteroides actuales de la escena y genera nuevos"""
        for a in self.asteroids:
            if a in scene.entities:
                destroy(a)
        self.asteroids.clear()
        self.spawn_asteroids()


class SpaceGrid:
    """Clase que genera una cuadrícula horizontal de referencia"""

    def __init__(self, size=1000):
        self.grid_plane = Entity(
            model=Grid(size, size),
            scale=size,
            rotation_x=90,
            position=(0, -15, 0),
            color=color.rgba(0, 0, 150, 100)
        )


class SpaceDustManager(Entity):
    """Manejador eficiente de partículas de polvo espacial que orbitan y reaccionan al jugador"""

    def __init__(self, player, count=300, radius=60, **kwargs):
        super().__init__(**kwargs)
        self.player = player
        self.radius = radius
        self.particles = []

        for _ in range(count):
            pos = Vec3(
                random.uniform(-radius, radius),
                random.uniform(-radius, radius),
                random.uniform(-radius, radius)
            )

            p = Entity(
                model='sphere',
                color=color.rgba(255, 255, 255, 60),
                scale=random.uniform(0.04, 0.12),
                position=self.player.position + pos
            )
            self.particles.append(p)

    def reset_particles(self):
        """NUEVO: Reubica de forma instantánea las partículas al reiniciar el juego"""
        for p in self.particles:
            pos = Vec3(
                random.uniform(-self.radius, self.radius),
                random.uniform(-self.radius, self.radius),
                random.uniform(-self.radius, self.radius)
            )
            p.position = self.player.position + pos

    def update(self):
        # Arreglado: Validación nativa de Ursina para verificar si el objeto sigue en escena
        if not self.player or self.player not in scene.entities:
            return

        player_velocity = self.player.forward * self.player.current_speed

        if self.player.is_dashing:
            dash_velocity = self.player.right * self.player.dash_direction * self.player.dash_speed
            player_velocity += dash_velocity

        for p in self.particles:
            p.position -= player_velocity * time.dt

            offset = p.position - self.player.position

            if offset.length() > self.radius:
                random_forward_dist = random.uniform(self.radius * 0.5, self.radius)
                p.position = (self.player.position
                              + self.player.forward * random_forward_dist
                              + self.player.right * random.uniform(-self.radius, self.radius)
                              + self.player.up * random.uniform(-self.radius, self.radius))