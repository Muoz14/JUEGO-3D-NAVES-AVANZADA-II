from ursina import *
import random


class ExplosionParticle(Entity):
    """Partícula individual que sale disparada de manera tridimensional al estallar un asteroide"""

    def __init__(self, pos, **kwargs):
        super().__init__(
            model='sphere',
            # Selector aleatorio de colores incandescentes y restos de roca gris
            color=random.choice([color.orange, color.yellow, color.rgb(255, 100, 0), color.dark_gray]),
            scale=random.uniform(0.15, 0.45),
            position=pos,
            **kwargs
        )
        # Generamos un vector de dirección 3D completamente aleatorio y lo normalizamos
        self.direction = Vec3(
            random.uniform(-1, 1),
            random.uniform(-1, 1),
            random.uniform(-1, 1)
        ).normalized()

        # Parámetros físicos individuales de la partícula
        self.speed = random.uniform(15, 45)
        self.lifetime = random.uniform(0.2, 0.5)
        self.initial_lifetime = self.lifetime

    def update(self):
        # Desplazamiento en el espacio según su dirección y velocidad
        self.position += self.direction * self.speed * time.dt

        # Reducción lineal de escala simulando desintegración térmica
        self.scale -= Vec3(1, 1, 1) * (time.dt / self.initial_lifetime) * 0.4

        # Control del ciclo de vida
        self.lifetime -= time.dt
        if self.lifetime <= 0 or self.scale_x <= 0:
            destroy(self)


class DualLaser(Entity):
    """Clase que representa un disparo láser individual con detección de impactos avanzada"""

    def __init__(self, ship_position, ship_rotation, ship_forward, ship_right, ship_up, offset_x, offset_y, offset_z,
                 **kwargs):
        super().__init__(
            model='cube',
            color=color.red,
            scale=(0.1, 0.1, 4),
            collider='box',
            **kwargs
        )

        self.position = ship_position + (ship_right * offset_x) + (ship_up * offset_y) + (ship_forward * offset_z)
        self.rotation = ship_rotation
        self.speed = 300
        self.lifetime = 1.5

        destroy(self, delay=self.lifetime)

    def update(self):
        self.position += self.forward * self.speed * time.dt
        hit_info = self.intersects()

        if hit_info.hit:
            if hasattr(hit_info.entity, 'is_asteroid'):
                # Guardamos la posición del asteroide antes de destruirlo
                impact_position = hit_info.entity.position

                # CREAR LA EXPLOSIÓN: Instanciamos un grupo de partículas en el punto de impacto
                # Puedes ajustar el rango (ej. de 15 a 25) según qué tan densa quieras la explosión
                for _ in range(random.randint(15, 25)):
                    ExplosionParticle(pos=impact_position)

                # Destruimos el asteroide y el láser
                destroy(hit_info.entity)
                destroy(self)