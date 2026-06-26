from ursina import *
import random
import math


class IntroCinematic(Entity):
    """Director de Fotografía: Cinemática blindada con Control de Sesiones"""

    def __init__(self, player, **kwargs):
        super().__init__(ignore_paused=True, **kwargs)
        self.player = player
        self.is_playing = False
        self.session_id = 0  # NUEVO: Identificador único por cada vez que juegas
        self.camera_shake = 0.0
        self.base_cam_pos = Vec3(0, 0, 0)

        # 1. FORMATO CINEMATOGRÁFICO
        self.top_bar = Entity(parent=camera.ui, model='quad', color=color.black, scale=(2, 0.15), position=(0, 0.44),
                              enabled=False, z=-5)
        self.bottom_bar = Entity(parent=camera.ui, model='quad', color=color.black, scale=(2, 0.15),
                                 position=(0, -0.44), enabled=False, z=-5)

        self.subtitle = Text(parent=camera.ui, text='', origin=(0, 0), position=(0, -0.44), scale=1.3,
                             color=color.white, enabled=False, z=-6)

        # 2. ACTOR DOBLE (DUMMY)
        self.dummy_ship = Entity(model='assets/nave1/SpaceShip.obj', color=color.white, scale=(0.2, 0.2, 0.2),
                                 enabled=False)

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
        self.session_id += 1  # NUEVO: Al iniciar, creamos un nuevo ID
        sid = self.session_id  # Guardamos el ID de esta partida en específico

        self.is_playing = True
        self.player.is_cinematic = True

        self.player.enabled = False
        self.player.hud_container.disable()

        self.top_bar.enabled = True
        self.bottom_bar.enabled = True
        self.subtitle.enabled = True
        self.dummy_ship.enabled = True
        self.portal.enabled = True

        # Pasamos el 'sid' a todas las llamadas futuras
        self.execute_shot_1(sid)
        invoke(self.execute_shot_2, sid, delay=2.8)
        invoke(self.execute_shot_3, sid, delay=6.0)
        invoke(self.execute_shot_4, sid, delay=8.5)
        invoke(self.execute_shot_5, sid, delay=11.0)
        invoke(self.end_cinematic, sid, delay=16.5)

    def execute_shot_1(self, sid):
        if sid != self.session_id or not self.is_playing: return

        self.portal.position = (0, 0, -200)
        self.portal.scale = (0, 0.01, 0)
        self.portal.animate_scale(Vec3(35, 0.01, 35), duration=0.8, curve=curve.out_back)

        self.dummy_ship.enabled = True
        self.dummy_ship.scale = (0.5, 0.5, 0.5)
        self.dummy_ship.position = (0, 0, -260)
        self.dummy_ship.rotation = (0, 0, 0)

        camera.parent = scene
        self.base_cam_pos = Vec3(3, -1.5, -165)
        camera.position = self.base_cam_pos
        camera.look_at((0, 0, -200))
        camera.fov = 70

        self.subtitle.text = "[SISTEMA]: Núcleo cuántico activado. Abriendo horizonte de sucesos..."
        invoke(self.dummy_ship.animate_position, (0, 0, -150), duration=2.3, curve=curve.in_out_expo, delay=0.4)

    def execute_shot_2(self, sid):
        """PLANO 2: Chase Cam en Ángulo Holandés (Persecución a alta velocidad)"""
        if sid != self.session_id or not self.is_playing: return

        # La nave arranca un poco más atrás
        self.dummy_ship.position = (0, 0, -160)

        # Nos colocamos detrás y a la derecha de la nave
        self.base_cam_pos = Vec3(6, 1.5, -175)
        camera.position = self.base_cam_pos

        # Miramos hacia la nave, pero le metemos una inclinación de -15 grados (Dutch Angle)
        # Esto hace que el plano se vea super dinámico y de acción.
        camera.look_at(self.dummy_ship.position)
        camera.rotation_z = -15
        camera.fov = 65

        self.subtitle.text = "[SISTEMA]: Estabilizando campos de inercia espacial..."

        # La cámara y la nave viajan juntas una gran distancia
        self.dummy_ship.animate_position((0, 0, -40), duration=3.0, curve=curve.linear)
        camera.animate_position((6, 1.5, -55), duration=3.0, curve=curve.linear)

    def execute_shot_3(self, sid):
        if sid != self.session_id or not self.is_playing: return

        self.dummy_ship.scale = (0.2, 0.2, 0.2)
        self.dummy_ship.position = (0, 0, -115)
        self.dummy_ship.rotation = (0, 0, 0)

        self.base_cam_pos = Vec3(18, 4, -40)
        camera.position = self.base_cam_pos
        camera.rotation = (10, -60, 0)
        camera.fov = 70

        self.subtitle.text = "[PILOTO]: Atravesando cuadrante ciego. Compresión de espacio-tiempo al 92%."
        self.dummy_ship.animate_position((0, 0, -10), duration=2.5, curve=curve.linear)

    def execute_shot_4(self, sid):
        """PLANO 4: Llegada y frenazo - Vista frontal dramática con portal distante"""
        if sid != self.session_id or not self.is_playing: return

        # Aseguramos que el portal esté activo, pero lo mandamos mucho más lejos
        self.portal.enabled = True
        self.portal.position = (0, 0, -150)  # Originalmente estaba en -90
        self.portal.scale = Vec3(35, 0.01, 35)
        self.portal_inner.color = color.white  # Aseguramos su color original por si acaso

        # La nave arranca su frenazo justo saliendo del portal lejano
        self.dummy_ship.position = (0, 0, -145)  # Originalmente estaba en -85

        # CÁMARA FRONTAL: Ubicada delante del punto de llegada, estable y sin giros locos.
        self.base_cam_pos = Vec3(0, 2.5, 20)
        camera.position = self.base_cam_pos
        camera.rotation = (8, 180, 0)
        camera.fov = 60

        self.subtitle.text = "[SISTEMA]: Destino alcanzado. Aplicando contrapeso y frenos magnéticos."

        # El frenazo se sentirá más rápido porque recorre más distancia en el mismo tiempo
        self.dummy_ship.animate_position((0, 0, 0), duration=1.5, curve=curve.out_expo)

        invoke(self.slam_brakes, sid, delay=1.2)

    def slam_brakes(self, sid):
        if sid != self.session_id or not self.is_playing: return

        # Temblor original y el cierre clásico del portal
        self.camera_shake = 1.9
        self.portal.animate_scale(Vec3(0, 0.01, 0), duration=0.4, curve=curve.in_back)

    def execute_shot_5(self, sid):
        if sid != self.session_id or not self.is_playing: return

        self.top_bar.enabled = False
        self.bottom_bar.enabled = False
        self.subtitle.enabled = False

        self.dummy_ship.enabled = False
        self.portal.enabled = False

        self.player.position = (0, 0, 0)
        self.player.rotation = (0, 0, 0)
        self.player.enabled = True
        self.player.hud_container.enable()
        self.player.is_cinematic = True

        camera.parent = self.player.camera_pivot
        camera.position = self.player.camera_modes[self.player.current_cam_index]
        camera.world_rotation = (0, 0, 0)
        camera.rotation = (0, 0, 0)
        camera.fov = self.player.base_fov

        self.cinematic_scan(sid)

    def cinematic_scan(self, sid):
        if sid != self.session_id or not self.is_playing: return
        self.player.cine_text.text = 'ESTAMOS A 4.2 AÑOS LUZ DE LA TIERRA...\nCONSIGUE MINERALES Y DESTRUYE TODO LO QUE VEAS'
        self.player.cine_text.enabled = True
        self.player.cine_text.color = color.rgba(255, 255, 255, 0)
        self.player.cine_text.animate_color(color.white, duration=0.5)

        self.player.animate('rotation_y', 20, duration=0.6, curve=curve.in_out_sine)
        invoke(self.player.animate, 'rotation_y', -20, delay=0.7, duration=1.2, curve=curve.in_out_sine)
        invoke(self.player.animate, 'rotation_y', 0, delay=2.0, duration=0.6, curve=curve.in_out_sine)

    def end_cinematic(self, sid):
        if sid != self.session_id or not self.is_playing: return
        self.player.cine_text.animate_color(color.rgba(255, 255, 255, 0), duration=1.0)
        invoke(self.give_control, sid, delay=1.0)

    def give_control(self, sid):
        if sid != self.session_id or not self.is_playing: return
        self.player.is_cinematic = False
        self.player.cine_text.enabled = False
        self.is_playing = False

        if hasattr(self.player, 'scanner') and self.player.scanner:
            self.player.scanner.toggle()

    def stop_and_clear(self):
        """Bloquea los invokes y apaga por completo las capas UI para no contaminar el menú"""
        self.session_id += 1  # NUEVO: Al sumar 1, todos los invokes pendientes de la partida anterior mueren automáticamente.

        self.is_playing = False
        self.dummy_ship.enabled = False
        self.portal.enabled = False
        self.top_bar.enabled = False
        self.bottom_bar.enabled = False
        self.subtitle.enabled = False
        self.player.is_cinematic = False

    def update(self):
        if not self.is_playing: return

        if self.portal.enabled and self.portal.scale_x > 0:
            self.portal.rotation_y += 140 * time.dt
            self.portal_inner.rotation_y -= 280 * time.dt

        if self.dummy_ship.enabled:
            for t in self.dummy_thrusters:
                t.scale_z = random.uniform(3.5, 5.0)

            if random.random() < 0.6:
                from player import SpeedLine
                SpeedLine()

            if random.random() < 0.4:
                for offset_x in [-0.6, 0.6]:
                    p_pos = (self.dummy_ship.position +
                             (self.dummy_ship.right * offset_x) +
                             (self.dummy_ship.up * -0.15) +
                             (self.dummy_ship.forward * 1.1))

                    p = Entity(model='sphere', color=color.rgba(0, 255, 255, 120), scale=random.uniform(0.08, 0.25),
                               position=p_pos)
                    p.animate_scale((0, 0, 0), duration=0.25)
                    destroy(p, delay=0.3)

        if self.camera_shake > 0:
            self.camera_shake -= time.dt * 6.0
            self.camera_shake = max(0.0, self.camera_shake)
            if camera.parent == scene:
                camera.x = self.base_cam_pos.x + random.uniform(-self.camera_shake, self.camera_shake)
                camera.y = self.base_cam_pos.y + random.uniform(-self.camera_shake, self.camera_shake)