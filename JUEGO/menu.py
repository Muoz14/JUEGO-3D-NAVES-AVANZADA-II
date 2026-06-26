from ursina import *
import random
import math


class MenuSun(Entity):
    """Un sol masivo al fondo con efecto de corona térmica pulsante"""

    def __init__(self, **kwargs):
        super().__init__(
            model='sphere',
            color=color.rgb(255, 230, 150),
            scale=300,
            position=(150, 40, 800),
            **kwargs
        )
        self.glow1 = Entity(parent=self, model='sphere', color=color.rgba(255, 140, 0, 120), scale=1.10)
        self.glow2 = Entity(parent=self, model='sphere', color=color.rgba(255, 60, 0, 60), scale=1.25)

    def update(self):
        self.glow1.scale = 1.10 + math.sin(time.time() * 3) * 0.015
        self.glow2.scale = 1.25 + math.cos(time.time() * 2) * 0.03


class MenuPlanet(Entity):
    """Planetas con rotación lenta y majestuosa en el fondo"""

    def __init__(self, **kwargs):
        super().__init__(model='sphere', **kwargs)
        self.rot_speed = random.uniform(1.0, 2.5)

    def update(self):
        self.rotation_y += self.rot_speed * time.dt


class MenuMeteor(Entity):
    """Rocas rojizas/marrones que viajan desde muy lejos hacia la cámara"""

    def __init__(self, **kwargs):
        super().__init__(model='sphere', color=color.rgb(80, 55, 45), **kwargs)
        self.reset_meteor()

    def reset_meteor(self):
        self.position = (random.uniform(-150, 150), random.uniform(-60, 60), random.uniform(400, 600))
        target_pos = Vec3(random.uniform(-20, 20), random.uniform(-10, 10), -10)
        self.direction = (target_pos - self.position).normalized()
        self.speed = random.uniform(15, 40)
        self.rot_speed = Vec3(random.uniform(-40, 40), random.uniform(-40, 40), random.uniform(-40, 40))
        self.scale = random.uniform(1.0, 4.0)


class MenuDust(Entity):
    """Partículas de polvo estelar diminutas con movimiento y deriva constante"""

    def __init__(self, **kwargs):
        super().__init__(
            model='sphere',
            color=color.rgba(255, 255, 255, 90),
            scale=random.uniform(0.01, 0.03),
            **kwargs
        )
        self.speed = random.uniform(0.8, 2.5)

    def update(self):
        self.z -= self.speed * time.dt
        if self.z < 2:
            self.z = random.uniform(25, 35)
            self.x = random.uniform(-20, 20)
            self.y = random.uniform(-12, 12)


class MainMenu(Entity):
    """Menú Principal estructurado como Entidad para evitar fallos de ejecución"""

    def __init__(self, start_game_func, **kwargs):
        super().__init__(**kwargs)
        self.start_game_func = start_game_func

        # Contenedor del espacio de fondo
        self.bg_container = Entity(parent=self)

        self.sun = MenuSun(parent=self.bg_container)
        self.planet1 = MenuPlanet(parent=self.bg_container, color=color.rgb(25, 28, 35), scale=12.0,
                                  position=(-25, -10, 60))
        self.planet2 = MenuPlanet(parent=self.bg_container, color=color.rgb(40, 42, 45), scale=5.0,
                                  position=(18, -6, 40))

        self.meteors = []
        for _ in range(8):
            m = MenuMeteor(parent=self.bg_container)
            self.meteors.append(m)

        self.dust_particles = []
        for _ in range(140):
            d = MenuDust(parent=self.bg_container,
                         position=(random.uniform(-22, 22), random.uniform(-12, 12), random.uniform(4, 32)))
            self.dust_particles.append(d)

        # Interfaz de Usuario
        self.ui_container = Entity(parent=camera.ui)

        self.title_text = Text(parent=self.ui_container, text='ASTRA 3D', position=(-0.82, 0.38), scale=5.5,
                               color=color.white)
        self.subtitle_text = Text(parent=self.ui_container, text='SIMULADOR DE VIAJE ASTRONÁUTICO',
                                  position=(-0.81, 0.27), scale=1.1, color=color.light_gray)

        self.btn_start = Button(parent=self.ui_container, text='INICIAR VUELO', scale=(0.4, 0.08),
                                position=(-0.6, 0.05), color=color.dark_gray, highlight_color=color.gray,
                                on_click=self.press_start, z=-1)
        self.btn_score = Button(parent=self.ui_container, text='PUNTUACIÓN ATLAS', scale=(0.4, 0.08),
                                position=(-0.6, -0.05), color=color.dark_gray, highlight_color=color.gray,
                                on_click=self.press_score, z=-1)
        self.btn_exit = Button(parent=self.ui_container, text='SALIR DE LA EXPERIENCIA', scale=(0.4, 0.08),
                               position=(-0.6, -0.15), color=color.red, highlight_color=color.rgb(255, 80, 80),
                               on_click=application.quit, z=-1)

        self.fade_overlay = Entity(parent=camera.ui, model='quad', color=color.rgba(0, 0, 0, 0), scale=(99, 99), z=-10,
                                   enabled=False)
        self.pan_direction = 1

    def update(self):
        """Animación de paneo suave para el fondo del menú"""
        if self.bg_container.enabled:
            self.bg_container.rotation_y += 0.5 * self.pan_direction * time.dt
            if self.bg_container.rotation_y > 5 or self.bg_container.rotation_y < -5:
                self.pan_direction *= -1

    def press_start(self):
        self.btn_start.enabled = False
        self.btn_score.enabled = False
        self.btn_exit.enabled = False

        self.fade_overlay.enabled = True
        self.fade_overlay.animate_color(color.rgba(0, 0, 0, 255), duration=1.5)
        invoke(self.execute_start, delay=1.5)

    def execute_start(self):
        self.disable()
        self.start_game_func()
        self.fade_overlay.animate_color(color.rgba(0, 0, 0, 0), duration=1.0)
        invoke(self.reset_menu_state, delay=1.0)

    def reset_menu_state(self):
        self.fade_overlay.enabled = False
        self.btn_start.enabled = True
        self.btn_score.enabled = True
        self.btn_exit.enabled = True

    def press_score(self):
        print("[Terminal]: Accediendo a los registros de vuelo guardados...")

    def disable(self):
        self.bg_container.disable()
        self.ui_container.disable()

    def enable(self):
        self.bg_container.enable()
        self.ui_container.enable()