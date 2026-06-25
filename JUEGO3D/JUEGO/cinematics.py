from ursina import *
import random
import math


class IntroCinematic(Entity):
    """Director de Fotografía: Cinemática pausada, cámaras cercanas y corrección absoluta de partículas"""

    def __init__(self, player, **kwargs):
        super().__init__(ignore_paused=True, **kwargs)
        self.player = player
        self.is_playing = False
        self.camera_shake = 0.0
        self.base_cam_pos = Vec3(0, 0, 0)

        # 1. FORMATO CINEMATOGRÁFICO: Cintas negras (Letterbox)
        self.top_bar = Entity(parent=camera.ui, model='quad', color=color.black, scale=(2, 0.15), position=(0, 0.44),
                              enabled=False, z=-5)
        self.bottom_bar = Entity(parent=camera.ui, model='quad', color=color.black, scale=(2, 0.15),
                                 position=(0, -0.44), enabled=False, z=-5)

        # Subtítulos de diálogo en blanco puro integrados en la banda inferior
        self.subtitle = Text(parent=camera.ui, text='', origin=(0, 0), position=(0, -0.38), scale=1.3,
                             color=color.white, enabled=False, z=-6)

        # 2. ACTOR DOBLE (DUMMY): Nave falsa para la intro cinemática
        self.dummy_ship = Entity(model='assets/nave1/SpaceShip.obj', color=color.white, scale=(0.2, 0.2, 0.2),
                                 enabled=False)

        # Propulsores de plasma de alta potencia del clon
        self.dummy_thrusters = []
        for offset_x in [-0.6, 0.6]:
            t = Entity(parent=self.dummy_ship, model='sphere', color=color.cyan, scale=(0.3, 0.3, 3.5),
                       position=(offset_x, -0.15, 1.1))
            self.dummy_thrusters.append(t)

        # 3. PORTAL HEXAGONAL
        self.portal = Entity(model=Cylinder(resolution=6), color=color.rgba(0, 255, 255, 180), scale=(0, 0.01, 0),
                             rotation_x=90, unlit=True, enabled=False)
        self.portal_inner = Entity(parent=self.portal, model=Cylinder(resolution=6), color=color.white,
                                   scale=(0.8, 1.1, 0.8), unlit=True)

    def play(self):
        self.is_playing = True
        self.player.is_cinematic = True

        # Desactivamos temporalmente al jugador real para no sobrecargar la escena
        self.player.enabled = False
        self.player.hud_container.disable()

        # Desplegamos la interfaz cinemática
        self.top_bar.enabled = True
        self.bottom_bar.enabled = True
        self.subtitle.enabled = True
        self.dummy_ship.enabled = True
        self.portal.enabled = True

        # ==========================================================
        # CRONOGRAMA DE MONTAJE (LÍNEA DE TIEMPO EXTENDIDA)
        # ==========================================================
        self.execute_shot_1()
        invoke(self.execute_shot_2, delay=3.5)  # Tiempo óptimo para leer el primer diálogo
        invoke(self.execute_shot_3, delay=7.0)  # Tiempo óptimo para el segundo diálogo
        invoke(self.execute_shot_4, delay=9.5)  # Transición al plano de escaneo táctico
        invoke(self.end_cinematic, delay=15.0)  # Fin total de la secuencia cinemática

    def execute_shot_1(self):
        """PLANO 1: Salida del portal lejano"""
        if not self.is_playing: return

        self.portal.position = (0, 0, -200)
        self.portal.scale = (0, 0.01, 0)
        self.portal.animate_scale(Vec3(35, 0.01, 35), duration=0.8, curve=curve.out_back)

        self.dummy_ship.position = (0, 0, -205)
        self.dummy_ship.rotation = (0, 0, 0)

        camera.parent = scene
        self.base_cam_pos = Vec3(18, 5, -180)
        camera.position = self.base_cam_pos
        camera.look_at((0, 0, -195))
        camera.fov = 85

        self.subtitle.text = "[SISTEMA]: Núcleo de salto cuántico en línea. Abriendo horizonte de sucesos..."

        # Vuelo lineal inicial saliendo del portal
        self.dummy_ship.animate_position((0, 0, -120), duration=2.5, curve=curve.out_quad)

    def execute_shot_2(self):
        """PLANO 2: Fly-by cercano a gran velocidad"""
        if not self.is_playing: return

        self.dummy_ship.position = (0, 0, -115)

        # Cámara posicionada muy cerca del paso físico de la trayectoria de la nave
        self.base_cam_pos = Vec3(-6, -1.5, -60)
        camera.position = self.base_cam_pos
        camera.look_at((0, 0, -25))

        self.subtitle.text = "[PILOTO]: Airavando cuadrante ciego. Compresión de espacio-tiempo al 92%."

        # Cruza la pantalla de forma majestuosa
        self.dummy_ship.animate_position((0, 0, -10), duration=2.5, curve=curve.linear)

    def execute_shot_3(self):
        """PLANO 3: Vista frontal íntima y frenazo cinético violento"""
        if not self.is_playing: return

        self.portal.position = (0, 0, -90)
        self.portal.scale = Vec3(35, 0.01, 35)

        self.dummy_ship.position = (0, 0, -85)

        # Cámara frontal fija a corta distancia esperando la nave
        self.base_cam_pos = Vec3(0, 1.5, 14)
        camera.position = self.base_cam_pos
        camera.look_at((0, 0.5, 0))

        self.subtitle.text = "[SISTEMA]: Destino alcanzado. Aplicando contrapeso y frenos magnéticos."

        # Movimiento final con desaceleración fuerte al origen
        self.dummy_ship.animate_position((0, 0, 0), duration=1.5, curve=curve.out_expo)

        invoke(self.slam_brakes, delay=1.2)

    def slam_brakes(self):
        if not self.is_playing: return
        self.camera_shake = 1.9  # Gran impacto visual en pantalla
        self.portal.animate_scale(Vec3(0, 0.01, 0), duration=0.4, curve=curve.in_back)

    def execute_shot_4(self):
        """PLANO 4: Limpieza de UI cine, inicialización de HUD y Misión superior"""
        if not self.is_playing: return

        # Ocultamos por completo las cintas de formato cinematográfico y subtítulos inferiores
        self.top_bar.enabled = False
        self.bottom_bar.enabled = False
        self.subtitle.enabled = False

        self.dummy_ship.enabled = False
        self.portal.enabled = False

        # Encendemos y restauramos la nave de juego real en la posición final de frenado
        self.player.position = (0, 0, 0)
        self.player.rotation = (0, 0, 0)
        self.player.enabled = True
        self.player.hud_container.enable()
        self.player.is_cinematic = True

        # Devolvemos la cámara al pivote en tercera persona del jugador
        camera.parent = self.player.camera_pivot
        camera.position = self.player.camera_modes[self.player.current_cam_index]
        camera.rotation = (0, 0, 0)
        camera.fov = self.player.base_fov

        self.cinematic_scan()

    def cinematic_scan(self):
        # Desplegamos las directrices de misión en la parte superior del HUD en blanco puro
        self.player.cine_text.text = 'ESTAMOS A 4.2 AÑOS LUZ DE LA TIERRA...\nCONSIGUE MINERALES Y DESTRUYE TODO LO QUE VEAS'
        self.player.cine_text.enabled = True
        self.player.cine_text.color = color.rgba(255, 255, 255, 0)
        self.player.cine_text.animate_color(color.white, duration=0.5)

        # Coreografía de paneo de escaneo táctico automático de la IA
        self.player.animate('rotation_y', 20, duration=0.6, curve=curve.in_out_sine)
        invoke(self.player.animate, 'rotation_y', -20, delay=0.7, duration=1.2, curve=curve.in_out_sine)
        invoke(self.player.animate, 'rotation_y', 0, delay=2.0, duration=0.6, curve=curve.in_out_sine)

    def end_cinematic(self):
        # Desvanecer el texto superior de la misión y soltar controles
        self.player.cine_text.animate_color(color.rgba(255, 255, 255, 0), duration=1.0)
        invoke(self.give_control, delay=1.0)

    def give_control(self):
        self.player.is_cinematic = False
        self.player.cine_text.enabled = False
        self.is_playing = False

    def stop_and_clear(self):
        self.is_playing = False
        self.dummy_ship.enabled = False
        self.portal.enabled = False
        self.top_bar.enabled = False
        self.bottom_bar.enabled = False
        self.subtitle.enabled = False
        self.player.is_cinematic = False

    def update(self):
        if not self.is_playing: return

        # Animación giratoria continua del portal hexagonal
        if self.portal.enabled and self.portal.scale_x > 0:
            self.portal.rotation_y += 140 * time.dt
            self.portal_inner.rotation_y -= 280 * time.dt

        # MANEJO VISUAL DE EFECTOS EN EL ACTOR DOBLE
        if self.dummy_ship.enabled:
            # Parpadeo de propulsores cromáticos
            for t in self.dummy_thrusters:
                t.scale_z = random.uniform(3.5, 5.0)

                # Forzar la generación continua de líneas de velocidad blancas/cian en pantalla
            if random.random() < 0.6:
                from player import SpeedLine
                SpeedLine()

            # CORRECCIÓN ABSOLUTA DEL BUG DE FANTASMA:
            # Calculamos de forma manual la posición exacta en base a las coordenadas locales de la nave clon,
            # saltándonos por completo el bug de caché de 'world_position' de Ursina durante las interpolaciones.
            if random.random() < 0.4:
                for offset_x in [-0.6, 0.6]:
                    # Fórmula trigonométrica de offset local a global frame a frame
                    p_pos = (self.dummy_ship.position +
                             (self.dummy_ship.right * offset_x) +
                             (self.dummy_ship.up * -0.15) +
                             (self.dummy_ship.forward * 1.1))

                    p = Entity(model='sphere', color=color.rgba(0, 255, 255, 120), scale=random.uniform(0.08, 0.25),
                               position=p_pos)
                    p.animate_scale((0, 0, 0), duration=0.25)
                    destroy(p, delay=0.3)

        # Manejo del temblor dinámico de cámara cinemática fija en escena
        if self.camera_shake > 0:
            self.camera_shake -= time.dt * 6.0
            self.camera_shake = max(0.0, self.camera_shake)
            if camera.parent == scene:
                camera.x = self.base_cam_pos.x + random.uniform(-self.camera_shake, self.camera_shake)
                camera.y = self.base_cam_pos.y + random.uniform(-self.camera_shake, self.camera_shake)