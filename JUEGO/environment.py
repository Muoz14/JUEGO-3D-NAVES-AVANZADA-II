from ursina import *
import random


class Asteroid(Entity):
    """Asteroide orgánico con protuberancias, variaciones de color, textura y lógica de destrucción"""

    def __init__(self, manager, pos, tier=1):
        self.manager = manager
        self.tier = tier

        # Paleta de colores base espaciales
        base_colors = ['#4a4543', '#5e5855', '#736c68', '#8c8581', '#3d3632', '#4a3f39']
        hex_color = random.choice(base_colors)

        # Variación aleatoria RGB para que no haya dos rocas idénticas
        c_rgb = color.hex(hex_color)
        c_final = color.rgb(
            clamp(c_rgb.r * random.uniform(0.8, 1.2), 0, 255),
            clamp(c_rgb.g * random.uniform(0.8, 1.2), 0, 255),
            clamp(c_rgb.b * random.uniform(0.8, 1.2), 0, 255)
        )

        # Definir tamaño base según el nivel
        if tier == 1:
            base_size = random.uniform(8, 12)
        elif tier == 2:
            base_size = random.uniform(4, 6)
        elif tier == 3:
            base_size = random.uniform(2, 3)
        else:
            base_size = random.uniform(0.8, 1.5)

        # Deformación inicial
        deformed_scale = Vec3(
            base_size,
            base_size * random.uniform(0.7, 1.2),
            base_size * random.uniform(0.7, 1.2)
        )

        super().__init__(
            model='sphere',
            texture='noise',
            color=c_final,
            scale=deformed_scale,
            position=pos,
            collider='sphere'
        )
        self.is_asteroid = True

        # Protuberancias físicas (bultos)
        if tier < 4:
            for _ in range(random.randint(3, 7)):
                offset_dir = Vec3(random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)).normalized()
                Entity(
                    parent=self,
                    model='sphere',
                    texture='noise',
                    color=c_final * random.uniform(0.6, 1.1),
                    scale=random.uniform(0.2, 0.55),
                    position=offset_dir * 0.45
                )

        self.velocity = Vec3(random.uniform(-1, 1), random.uniform(-1, 1),
                             random.uniform(-1, 1)).normalized() * random.uniform(2, 6)
        self.rotation_speed = Vec3(random.uniform(-15, 15), random.uniform(-15, 15), random.uniform(-15, 15))

    def update(self):
        self.position += self.velocity * time.dt
        self.rotation += self.rotation_speed * time.dt

        # Rebote suave entre asteroides
        hit = self.intersects(ignore=(self,))
        if hit.hit and hasattr(hit.entity, 'is_asteroid'):
            bounce_dir = (self.position - hit.entity.position).normalized()
            self.velocity = bounce_dir * (self.velocity.length() * 0.8)
            self.position += bounce_dir * self.scale_x * 0.05

            # Reciclaje si se alejan demasiado
        if not self.manager.player: return
        dist = distance(self.position, self.manager.player.position)
        if dist > self.manager.despawn_radius:
            if self.tier == 1:
                spawn_dir = (self.manager.player.forward + Vec3(random.uniform(-0.8, 0.8), random.uniform(-0.8, 0.8),
                                                                random.uniform(-0.8, 0.8))).normalized()
                self.position = self.manager.player.position + (spawn_dir * (self.manager.despawn_radius - 20))
            else:
                if self in self.manager.asteroids: self.manager.asteroids.remove(self)
                destroy(self)

    def split(self):
        """Lógica de división: 1->2, 2->3, 3->4, 4->Destrucción"""
        if self.tier == 1:
            pieces = 2; next_tier = 2
        elif self.tier == 2:
            pieces = 3; next_tier = 3
        elif self.tier == 3:
            pieces = 4; next_tier = 4
        else:
            pieces = 0

        for _ in range(pieces):
            offset = Vec3(random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)).normalized() * (
                        self.scale_x * 0.4)
            new_ast = Asteroid(self.manager, self.position + offset, tier=next_tier)
            new_ast.velocity = self.velocity + (offset.normalized() * random.uniform(1.5, 4.0))
            self.manager.asteroids.append(new_ast)

        if self in self.manager.asteroids: self.manager.asteroids.remove(self)
        destroy(self)


class AsteroidManager(Entity):
    def __init__(self, player, count=60, radius=300, despawn_radius=500, **kwargs):
        super().__init__(**kwargs)
        self.player = player
        self.count = count
        self.spawn_radius = radius
        self.despawn_radius = despawn_radius
        self.asteroids = []
        self.spawn_initial_asteroids()

    def spawn_initial_asteroids(self):
        for _ in range(self.count):
            pos = self.player.position + Vec3(
                random.uniform(-self.spawn_radius, self.spawn_radius),
                random.uniform(-self.spawn_radius, self.spawn_radius),
                random.uniform(-self.spawn_radius, self.spawn_radius)
            )
            ast = Asteroid(self, pos, tier=random.randint(1, 4))
            self.asteroids.append(ast)

    def clear_and_respawn(self):
        for a in self.asteroids:
            if a in scene.entities: destroy(a)
        self.asteroids.clear()
        self.spawn_initial_asteroids()


class SpaceGrid(Entity):
    def __init__(self, size=1000):
        super().__init__()
        self.grid_plane = Entity(
            model=Grid(size, size),
            scale=size,
            rotation_x=90,
            position=(0, -15, 0),
            color=color.rgba(0, 0, 150, 100)
        )


class SpaceDustManager(Entity):
    def __init__(self, player, count=300, radius=60, **kwargs):
        super().__init__(**kwargs)
        self.player = player
        self.radius = radius
        self.particles = []
        for _ in range(count):
            p = Entity(model='sphere', color=color.rgba(255, 255, 255, 60),
                       scale=random.uniform(0.04, 0.12), position=self.player.position + Vec3(
                    random.uniform(-radius, radius), random.uniform(-radius, radius), random.uniform(-radius, radius)))
            self.particles.append(p)

    def reset_particles(self):
        for p in self.particles:
            p.position = self.player.position + Vec3(random.uniform(-self.radius, self.radius),
                                                     random.uniform(-self.radius, self.radius),
                                                     random.uniform(-self.radius, self.radius))

    def update(self):
        if not self.player or self.player not in scene.entities: return
        player_velocity = self.player.forward * self.player.current_speed
        if getattr(self.player, 'is_dashing', False):
            player_velocity += self.player.right * self.player.dash_direction * getattr(self.player, 'dash_speed', 180)
        for p in self.particles:
            p.position -= player_velocity * time.dt
            if distance(p.position, self.player.position) > self.radius:
                p.position = (
                            self.player.position + self.player.forward * random.uniform(self.radius * 0.5, self.radius)
                            + self.player.right * random.uniform(-self.radius, self.radius)
                            + self.player.up * random.uniform(-self.radius, self.radius))