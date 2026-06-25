from ursina import *


class DualLaser(Entity):
    """Clase que representa un disparo láser individual (Tiro Recto / Paralelo)"""

    def __init__(self, ship_position, ship_rotation, ship_forward, ship_right, ship_up, offset_x, offset_y, offset_z,
                 **kwargs):
        super().__init__(
            model='cube',
            color=color.red,
            scale=(0.1, 0.1, 4),  # Largo y delgado
            collider='box',
            **kwargs
        )

        # Origen físico del láser (Las alas de tu nave)
        self.position = ship_position + (ship_right * offset_x) + (ship_up * offset_y) + (ship_forward * offset_z)

        # ROTACIÓN PARALELA: El láser copia exactamente la rotación de la nave
        self.rotation = ship_rotation

        self.speed = 300
        self.lifetime = 1.5

        destroy(self, delay=self.lifetime)

    def update(self):
        # El láser viaja en línea recta hacia adelante basándose en su propia rotación
        self.position += self.forward * self.speed * time.dt

        hit_info = self.intersects()

        if hit_info.hit:
            if hasattr(hit_info.entity, 'is_asteroid'):
                destroy(hit_info.entity)
                destroy(self)