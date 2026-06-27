from ursina import *
import math
import random


class TacticalMap(Entity):
    """Interfaz de Mapa 2D Holográfico interactivo modular"""

    def __init__(self, player, **kwargs):
        # IMPORTANTE: Esta entidad base SIEMPRE está activa para poder leer la tecla 'M'
        # incluso si el juego está pausado por completo.
        super().__init__(parent=camera.ui, ignore_paused=True, z=-20, **kwargs)
        self.player = player
        self.max_radius = 2500
        self.is_open = False

        # CONTENEDOR BASE: Todo lo visual va aquí adentro para ocultarlo/mostrarlo
        self.container = Entity(parent=self, enabled=False)

        self.panel = Entity(parent=self.container, model='quad', color=color.hex('#0a0c12'), alpha=0.95,
                            scale=(0.82, 0.82))
        Entity(parent=self.panel, model='quad', color=color.cyan, scale=(1.01, 1.01), z=0.05)

        Text(parent=self.container, text='> INTERFAZ TACTICA DE NAVEGACION', position=(-0.38, 0.37), scale=1.3,
             color=color.cyan)
        Text(parent=self.container, text='Sector: EXTRACCION ALFA', position=(-0.38, 0.33), scale=0.9,
             color=color.light_gray)

        Entity(parent=self.container, model='circle', color=color.red, scale=0.62, z=-0.1)
        Entity(parent=self.container, model='circle', color=color.hex('#0a0c12'), scale=0.61, z=-0.15)
        Text(parent=self.container, text='[!] UNIVERSO INTERESTELAR', position=(0, -0.36), origin=(0, 0), scale=1.2,
             color=color.red)

        px = (300 / self.max_radius) * 0.30
        py = (2200 / self.max_radius) * 0.30
        self.planet_icon = Entity(parent=self.container, model='circle', color=color.hex('#362826'), scale=0.05,
                                  position=(px, py), z=-0.2)
        Entity(parent=self.planet_icon, model='circle', color=color.hex('#ff3300'), scale=0.4, z=-0.01)
        Text(parent=self.container, text='PLANETA FRACTURADO', position=(px + 0.03, py + 0.01), scale=0.8,
             color=color.hex('#ff6644'))

        for _ in range(35):
            r = random.uniform(200, self.max_radius - 100)
            ang = random.uniform(0, math.tau)
            ax = math.cos(ang) * r
            az = math.sin(ang) * r
            uix = (ax / self.max_radius) * 0.30
            uiy = (az / self.max_radius) * 0.30
            Entity(parent=self.container, model='circle', color=color.rgba(140, 140, 145, 150), scale=0.008,
                   position=(uix, uiy), z=-0.18)

        self.click_area = Entity(parent=self.container, model='quad', scale=(0.60, 0.60), collider='box', alpha=0,
                                 z=-0.25)

        self.map_waypoint = Entity(parent=self.container, model='circle', color=color.yellow, scale=0.015, z=-0.4,
                                   enabled=False)
        Entity(parent=self.map_waypoint, model='circle', color=color.black, scale=0.6, z=-0.01)

        self.waypoint_pos_3d = None

        self.world_waypoint = Entity(model='diamond', color=color.yellow, scale=(10, 40, 10), unlit=True, enabled=False)
        self.world_waypoint.animate_rotation_y(360, duration=3.0, loop=True)

        # EL JUGADOR: Model=Circle(3) crea un triángulo perfecto y visible en la UI.
        self.player_icon = Entity(parent=self.container, model=Circle(3), color=color.cyan, scale=0.025, z=-5,
                                  unlit=True)

        Text(parent=self.container, text='[CLIC] Fija un rumbo  |  [M] Cierra el mapa', position=(0, 0.45),
             origin=(0, 0), color=color.yellow)

    def toggle(self):
        # Evita abrir el mapa si estás muerto o en la cinemática de inicio
        if self.player.is_dead or (self.player.is_cinematic and not self.is_open):
            return

        self.is_open = not self.is_open
        self.container.enabled = self.is_open

        if self.is_open:
            application.paused = True  # Pausa TODO el universo
            mouse.locked = False  # Libera el mouse para el radar
        else:
            application.paused = False  # Reactiva la física del juego
            mouse.locked = True  # Atrapa el mouse de nuevo para la nave

    def input(self, key):
        # El mapa escucha su propia tecla "M" sin depender de la nave
        if key == 'm':
            self.toggle()

        if not self.is_open: return

        if key == 'left mouse down' and mouse.hovered_entity == self.click_area:
            lx = mouse.point.x
            ly = mouse.point.y

            world_x = lx * 2 * self.max_radius
            world_z = ly * 2 * self.max_radius

            self.map_waypoint.x = lx * 0.60
            self.map_waypoint.y = ly * 0.60
            self.map_waypoint.enabled = True

            self.waypoint_pos_3d = Vec3(world_x, 0, world_z)
            self.world_waypoint.position = self.waypoint_pos_3d
            self.world_waypoint.enabled = True

    def clear_waypoint(self):
        self.waypoint_pos_3d = None
        self.map_waypoint.enabled = False
        self.world_waypoint.enabled = False

    def update(self):
        if not self.is_open: return
        pos = self.player.position
        self.player_icon.x = (pos.x / self.max_radius) * 0.30
        self.player_icon.y = (pos.z / self.max_radius) * 0.30
        # Sincronizamos la rotación del triangulo 2D con la brújula real de la nave
        self.player_icon.rotation_z = 90 - self.player.rotation_y