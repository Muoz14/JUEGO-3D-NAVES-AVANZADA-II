from ursina import *
import random


class Asteroid(Entity):
    def __init__(self, manager, pos, tier=1, material_data=None):
        self.manager = manager
        self.tier = tier

        if material_data is None:
            materials = [
                {'name': 'HIERRO (Fe)', 'color': '#a14d26', 'desc': 'Uso Estructural'},
                {'name': 'COBRE (Cu)', 'color': '#28795c', 'desc': 'Conductor Eléctrico'},
                {'name': 'TITANIO (Ti)', 'color': '#5a6578', 'desc': 'Blindaje Pesado'},
                {'name': 'ORO (Au)', 'color': '#c4a627', 'desc': 'Microtecnología'},
                {'name': 'URANIO (U)', 'color': '#4d821a', 'desc': 'Núcleo Combustible'}
            ]
            self.mat_data = random.choice(materials)
        else:
            self.mat_data = material_data

        self.material_name = self.mat_data['name']
        self.material_desc = self.mat_data['desc']

        c_rgb = color.hex(self.mat_data['color'])
        c_final = color.rgb(
            clamp(c_rgb.r * random.uniform(0.8, 1.2), 0, 255),
            clamp(c_rgb.g * random.uniform(0.8, 1.2), 0, 255),
            clamp(c_rgb.b * random.uniform(0.8, 1.2), 0, 255)
        )

        if tier == 1:
            base_size = random.uniform(8, 12)
        elif tier == 2:
            base_size = random.uniform(4, 6)
        else:
            base_size = random.uniform(1.5, 3)

        deformed_scale = Vec3(base_size, base_size * random.uniform(0.7, 1.2), base_size * random.uniform(0.7, 1.2))

        super().__init__(
            model='sphere',
            texture='noise',
            color=c_final,
            scale=deformed_scale,
            position=pos,
            collider='sphere'
        )
        self.is_asteroid = True

        if tier < 3:
            for _ in range(random.randint(4, 7)):
                offset_dir = Vec3(random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)).normalized()
                Entity(parent=self, model='sphere', texture='noise', color=c_final * random.uniform(0.7, 1.1),
                       scale=random.uniform(0.25, 0.45), position=offset_dir * 0.45)

        self.velocity = Vec3(random.uniform(-1, 1), random.uniform(-1, 1),
                             random.uniform(-1, 1)).normalized() * random.uniform(2, 5)
        self.rotation_speed = Vec3(random.uniform(-10, 10), random.uniform(-10, 10), random.uniform(-10, 10))

    def update(self):
        self.position += self.velocity * time.dt
        self.rotation += self.rotation_speed * time.dt

        if not getattr(self.manager, 'player', None): return
        dist = distance(self.position, self.manager.player.position)

        if dist > self.manager.despawn_radius:
            if self.tier == 1:
                spawn_dir = (self.manager.player.forward + Vec3(random.uniform(-0.5, 0.5), 0,
                                                                random.uniform(-0.5, 0.5))).normalized()
                self.position = self.manager.player.position + (spawn_dir * (self.manager.despawn_radius - 50))
            else:
                if self in self.manager.asteroids: self.manager.asteroids.remove(self)
                destroy(self)

    def split(self):
        if self.tier == 1:
            next_tier = 2; pieces = 2
        elif self.tier == 2:
            next_tier = 3; pieces = 3
        else:
            pieces = 0

        for _ in range(pieces):
            offset = Vec3(random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)).normalized() * (
                        self.scale_x * 0.35)
            new_ast = Asteroid(self.manager, self.position + offset, tier=next_tier, material_data=self.mat_data)
            new_ast.velocity = self.velocity + (offset.normalized() * random.uniform(1.5, 3.5))
            self.manager.asteroids.append(new_ast)

        if self in self.manager.asteroids: self.manager.asteroids.remove(self)
        destroy(self)


class AsteroidManager(Entity):
    def __init__(self, player, count=60, radius=300, despawn_radius=1200, **kwargs):
        super().__init__(**kwargs)
        self.player = player
        self.count = count
        self.spawn_radius = radius
        self.despawn_radius = despawn_radius
        self.asteroids = []
        self.spawn_initial_asteroids()

    def spawn_initial_asteroids(self):
        for _ in range(self.count):
            pos = Vec3(random.uniform(-1, 1), random.uniform(-1, 1),
                       random.uniform(-1, 1)).normalized() * random.uniform(100, self.spawn_radius)
            self.asteroids.append(Asteroid(self, pos, tier=random.randint(1, 3)))

    def clear_and_respawn(self):
        for a in self.asteroids:
            if a in scene.entities: destroy(a)
        self.asteroids.clear()
        self.spawn_initial_asteroids()


class ShatteredPlanet(Entity):
    """Planeta fracturado masivo, gris negroso con tintes de magma y textura de asteroide"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.is_planet = True

        # 1. EL NÚCLEO (Gris/negro con un toque rojo/naranja quemado + textura de asteroide)
        # El color oscuro evita que el 'noise' se rompa en cuadros blancos gigantes.
        self.core = Entity(
            parent=self,
            model='sphere',
            texture='noise',  # Recuperamos la textura de los asteroides
            color=color.hex('#4a2217'),  # Gris/marrón muy oscuro con tinte de magma
            scale=1200,
            collider='sphere',
            is_planet=True
        )

        # (¡Eliminadas las pelotas rojas de sarampión!)

        # 2. LOS ESCOMBROS GIGANTES
        self.chunks = Entity(parent=self)
        # Tonos gris/negrosos con levísimos toques rojizos para que hagan juego
        crust_colors = ['#1f1a19', '#2b211f', '#171413', '#362826']

        for _ in range(60):
            dist = random.uniform(700, 1300)
            dir_v = Vec3(random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)).normalized()

            c_size = random.uniform(60, 220)
            chunk_scale = Vec3(c_size, c_size * random.uniform(0.5, 1.4), c_size * random.uniform(0.5, 1.4))

            Entity(
                parent=self.chunks,
                model='sphere',
                texture='noise',
                color=color.hex(random.choice(crust_colors)),
                scale=chunk_scale,
                position=dir_v * dist,
                rotation=(random.uniform(0, 360), random.uniform(0, 360), random.uniform(0, 360)),
                collider='sphere',
                is_planet=True
            )

    def update(self):
        self.core.rotation_y += 1.5 * time.dt
        self.chunks.rotation_y -= 0.8 * time.dt
        self.chunks.rotation_x += 0.4 * time.dt

class CosmicBackground(Entity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stars = Entity(parent=self)
        for _ in range(350):
            pos = Vec3(random.uniform(-1, 1), random.uniform(-1, 1),
                       random.uniform(-1, 1)).normalized() * random.uniform(2500, 3000)
            Entity(parent=self.stars, model='quad', color=color.white, scale=random.uniform(4.0, 9.0), position=pos,
                   billboard=True, unlit=True)

        # Lo centramos casi al frente del jugador (300 en X en lugar de 1200) y a 2200 metros de profundidad.
        self.planet = ShatteredPlanet(parent=self, position=(300, 200, 2200))

class SpaceDustManager(Entity):
    def __init__(self, player, count=200, radius=60, **kwargs):
        super().__init__(**kwargs)
        self.player = player
        self.radius = radius
        self.particles = [Entity(model='sphere', color=color.rgba(255, 255, 255, 50), scale=0.08,
                                 position=self.player.position + Vec3(random.uniform(-radius, radius),
                                                                      random.uniform(-radius, radius),
                                                                      random.uniform(-radius, radius))) for _ in
                          range(count)]

    def reset_particles(self):
        for p in self.particles:
            p.position = self.player.position + Vec3(random.uniform(-self.radius, self.radius),
                                                     random.uniform(-self.radius, self.radius),
                                                     random.uniform(-self.radius, self.radius))

    def update(self):
        if not self.player or self.player not in scene.entities: return
        vel = self.player.forward * self.player.current_speed
        for p in self.particles:
            p.position -= vel * time.dt
            if distance(p.position, self.player.position) > self.radius:
                p.position = self.player.position + self.player.forward * self.radius + Vec3(random.uniform(-30, 30),
                                                                                             random.uniform(-30, 30), 0)