from ursina import *
import random


class ExplosionParticle(Entity):
    """Partículas de altísimo rendimiento: Animación delegada al backend de C++, sin bucle Update"""

    def __init__(self, pos, **kwargs):
        super().__init__(
            model='sphere',
            color=random.choice([color.orange, color.yellow, color.rgb(255, 100, 0), color.dark_gray]),
            scale=random.uniform(0.15, 0.45),
            position=pos,
            **kwargs
        )

        direction = Vec3(random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)).normalized()
        speed = random.uniform(15, 45)
        lifetime = random.uniform(0.2, 0.5)

        # Calculamos dónde terminará la partícula
        target_pos = self.position + (direction * speed * lifetime)

        # Delegamos la animación directamente al motor interno (Cero lag de Python)
        self.animate_position(target_pos, duration=lifetime, curve=curve.out_expo)
        self.animate_scale(Vec3(0, 0, 0), duration=lifetime, curve=curve.out_expo)

        # Se autodestruye al terminar
        destroy(self, delay=lifetime)


class DualLaser(Entity):
    """Clase que representa un disparo láser individual con detección de impactos avanzada"""

    def __init__(self, ship_position, ship_rotation, ship_forward, ship_right, ship_up, offset_x, offset_y, offset_z,
                 **kwargs):
        super().__init__(
            model='cube',
            color=color.red,       # Regresamos al rojo puro original
            unlit=True,            # ¡Clave! Evita que las luces del juego lo vuelvan blanco o gris
            scale=(0.2, 0.2, 2),   # Mantenemos el tamaño masivo que le pusimos
            collider='box',
            **kwargs
        )

        self.position = ship_position + (ship_right * offset_x) + (ship_up * offset_y) + (ship_forward * offset_z)
        self.rotation = ship_rotation
        self.speed = 120
        self.lifetime = 2.0

        destroy(self, delay=self.lifetime)

    def update(self):
        # Calculamos cuánto va a avanzar el láser en este exacto frame
        distancia_avance = self.speed * time.dt

        # RAYCASTING: Disparamos un rayo invisible hacia adelante para ver si golpearemos algo
        hit_info = raycast(self.position, self.forward, distance=distancia_avance + (self.scale_z / 2), ignore=(self,))

        if hit_info.hit and hasattr(hit_info.entity, 'is_asteroid'):
            impact_position = hit_info.entity.position

            from weapons import ExplosionParticle
            for _ in range(random.randint(15, 25)):
                ExplosionParticle(pos=impact_position)

            hit_info.entity.split()
            destroy(self)
        else:
            # Si no hay nada en el camino, avanzamos de forma normal
            self.position += self.forward * distancia_avance