from ursina import *
from weapons import DualLaser
import random
import math


class SpeedLine(Entity):
    def __init__(self, **kwargs):
        super().__init__(parent=camera.ui, model='quad', color=color.rgba(200, 240, 255, 70), z=-1.1, **kwargs)
        self.angle = random.uniform(0, math.tau)
        self.distance = random.uniform(0.15, 0.35)
        self.speed = random.uniform(4.0, 7.0)
        self.max_scale_y = random.uniform(0.06, 0.18)
        self.scale = (0.0015, 0.01)
        self.rotation_z = math.degrees(self.angle) - 90
        self.update_position()

    def update_position(self):
        self.x = math.cos(self.angle) * self.distance
        self.y = math.sin(self.angle) * self.distance

    def update(self):
        self.distance += self.speed * time.dt
        self.scale_y = min(self.max_scale_y, self.distance * 0.4)
        self.update_position()
        if self.distance > 0.6: self.alpha -= time.dt * 5
        if self.distance > 1.2 or self.alpha <= 0: destroy(self)


class MaterialPopup(Entity):
    def __init__(self, target_asteroid, **kwargs):
        super().__init__(parent=camera.ui, z=-15, ignore_paused=True, **kwargs)
        self.target = target_asteroid

        self.bg = Entity(parent=self, model='quad', color=color.rgba(10, 15, 25, 230), scale=(0.4, 0.16),
                         position=(0.2, -0.08))
        Entity(parent=self.bg, model='quad', color=color.cyan, scale=(0.02, 1), position=(-0.5, 0), z=-0.01)
        Entity(parent=self.bg, model='quad', color=color.cyan, scale=(0.2, 0.05), position=(0.4, 0.475), z=-0.01)

        Text(parent=self, text='[ ANÁLISIS MINERAL ]', position=(0.02, -0.02), scale=1.2, color=color.cyan, z=-1)
        Text(parent=self, text=self.target.material_name, position=(0.02, -0.06), scale=1.8, color=color.white, z=-1)
        Text(parent=self, text=f"Tipo: {self.target.material_desc}", position=(0.02, -0.11), scale=1.1,
             color=color.light_gray, z=-1)

        self.dist_text = Text(parent=self, text='0m', position=(0.32, -0.02), scale=1.2, color=color.orange, z=-1)

        self.scale = 0
        self.animate_scale(1, duration=0.2, curve=curve.out_back)
        self.is_fading = False

    def fade_and_destroy(self):
        if self.is_fading: return
        self.is_fading = True
        self.animate_scale(0, duration=0.15)
        destroy(self, delay=0.2)

    def update(self):
        if application.paused:
            self.visible = False
            return
        if not self.target or self.target not in scene.entities:
            self.fade_and_destroy()
            return

        dist = distance(self.target.position, camera.world_position)
        if dist > 500:
            self.fade_and_destroy()
            return

        self.dist_text.text = f"{int(dist)}m"
        if (self.target.position - camera.world_position).dot(camera.forward) < 0:
            self.visible = False
        else:
            self.visible = True

        pos_2d = self.target.screen_position
        self.position = pos_2d + Vec2(0.06, 0.04)


class TacticalScanner:
    def __init__(self, player):
        self.player = player
        self.active = False
        self.scan_radius = 500
        self.max_targets = 15
        self.markers = []
        self.active_timer = 0
        self.current_popup = None

        self.scan_line = Entity(parent=camera.ui, model='quad', scale=(2.5, 0.03), color=color.cyan, z=-3,
                                enabled=False)
        self.analyzing_text = Text(parent=camera.ui, text='ANALIZANDO...', position=(0, 0.35), origin=(0, 0), scale=2.5,
                                   color=color.white, enabled=False)

    def toggle(self, force_off=False):
        if force_off:
            self.active = False
        else:
            self.active = not self.active

        if self.active:
            self.active_timer = 6.0
            self.play_scan_animation()
            self.scan_environment()
        else:
            self.clear_markers()

    def play_scan_animation(self):
        self.scan_line.enabled = True
        self.scan_line.y = 0.5
        self.scan_line.animate_y(-0.5, duration=0.6, curve=curve.linear)
        invoke(self.scan_line.disable, delay=0.6)
        self.analyzing_text.enabled = True
        invoke(self.analyzing_text.disable, delay=2.0)

    def scan_environment(self):
        self.clear_markers()
        asteroids_in_range = []
        for entity in scene.entities:
            if hasattr(entity, 'is_asteroid') and entity.enabled:
                dist = distance(self.player.position, entity.position)
                if dist <= self.scan_radius:
                    asteroids_in_range.append((dist, entity))

        asteroids_in_range.sort(key=lambda x: x[0])
        top_targets = asteroids_in_range[:self.max_targets]

        for dist, entity in top_targets:
            marker = Entity(parent=entity, billboard=True)
            marker.scale = (0, 0, 0)
            marker.animate_scale((1, 1, 1), duration=0.4, curve=curve.out_back)

            c = color.rgba(0, 255, 255, 180)
            Entity(parent=marker, model='quad', scale=(2.0, 0.05), position=(0, 1.0, 0), color=c, unlit=True)
            Entity(parent=marker, model='quad', scale=(2.0, 0.05), position=(0, -1.0, 0), color=c, unlit=True)
            Entity(parent=marker, model='quad', scale=(0.05, 2.0), position=(1.0, 0, 0), color=c, unlit=True)
            Entity(parent=marker, model='quad', scale=(0.05, 2.0), position=(-1.0, 0, 0), color=c, unlit=True)

            marker.text_dist = Text(parent=marker, text=f'{int(dist)}m', position=(0, -1.8, 0), origin=(0, 0), scale=9,
                                    color=color.cyan)
            self.markers.append(marker)

    def update(self):
        if not self.active: return
        self.active_timer -= time.dt
        if self.active_timer <= 0:
            self.toggle(force_off=True)
            return

        hit_info = raycast(camera.world_position, camera.forward, distance=self.scan_radius, ignore=[self.player])
        if hit_info.hit and hasattr(hit_info.entity, 'is_asteroid'):
            target = hit_info.entity
            if getattr(self.current_popup, 'target', None) != target:
                if self.current_popup:
                    self.current_popup.fade_and_destroy()
                self.current_popup = MaterialPopup(target)
        else:
            if self.current_popup:
                self.current_popup.fade_and_destroy()
                self.current_popup = None

        for marker in self.markers[:]:
            if not marker.parent or marker.parent not in scene.entities or not marker.parent.enabled:
                destroy(marker)
                self.markers.remove(marker)
                continue

            dist = distance(self.player.position, marker.parent.position)
            if dist > self.scan_radius:
                destroy(marker)
                self.markers.remove(marker)
                continue

            marker.text_dist.text = f'{int(dist)}m'
            marker.text_dist.color = color.red if dist < 120 else color.cyan

    def clear_markers(self):
        for marker in self.markers:
            marker.animate_scale((0, 0, 0), duration=0.2)
            destroy(marker, delay=0.2)
        self.markers.clear()
        if getattr(self, 'current_popup', None):
            self.current_popup.fade_and_destroy()
            self.current_popup = None


class PlayerShip(Entity):
    def __init__(self, game_over_menu=None, **kwargs):
        super().__init__(model='assets/nave1/SpaceShip.obj', color=color.white, scale=(0.2, 0.2, 0.2),
                         position=(0, 0, 0), collider='box', **kwargs)

        self.game_over_menu = game_over_menu
        self.is_dead = False
        self.is_cinematic = False

        self.max_shield = 100
        self.shield = 100
        self.error_spawn_timer = 0.0
        self.speed_line_timer = 0.0

        self.right_laser_offset = (3.5, -0.5, -5.5)
        self.left_laser_offset = (-3.5, -0.5, -5.5)

        self.target_speed = 0
        self.current_speed = 0
        self.normal_max_speed = 70
        self.boost_max_speed = 255
        self.acceleration = 1.5
        self.friction = 0.8
        self.mouse_sensitivity = 60
        self.roll_speed = 220

        self.auto_level_timer = 0
        self.auto_level_delay = 0.8
        self.level_damping = 1.2
        self.max_banking_angle = 30.0

        self.base_pitch = 0.0
        self.max_pitch_banking = 15.0

        self.dash_cooldown = 1.2
        self.dash_timer = 0
        self.is_dashing = False
        self.dash_duration = 0.4
        self.dash_time_left = 0
        self.dash_direction = 0
        self.dash_speed = 200
        self.dash_roll = 0.0
        self.camera_dash_drag = 0.3

        self.shake_amount = 0.0
        self.shake_decay = 12.0

        self.max_boost = 100
        self.boost_fuel = 100
        self.boost_recharge_delay = 1.5
        self.boost_timer = 0
        self.trail_timer = 0

        self.sector_radius = 2500
        self.oob_timer = 10.0

        self.thrusters = []
        self.scanner = TacticalScanner(self)

        for offset_x in [-0.6, 0.6]:
            t = Entity(parent=self, model='sphere', color=color.cyan, scale=(0.2, 0.2, 0.6),
                       position=(offset_x, -0.15, 1.1))
            self.thrusters.append(t)

        self.camera_pivot = Entity(parent=self)
        camera.parent = self.camera_pivot
        self.camera_modes = [(0, 1.0, -9), (0, 1.5, -14), (0, 2.5, -20)]
        self.current_cam_index = 1
        camera.position = self.camera_modes[self.current_cam_index]
        camera.rotation = (0, 0, 0)
        self.base_fov = camera.fov
        mouse.locked = True

        self.hud_container = Entity(parent=camera.ui)

        self.cine_text = Text(parent=self.hud_container, text='', origin=(0, 0), position=(0, 0.15), scale=2,
                              color=color.rgba(255, 255, 255, 0), enabled=False, z=-2)
        self.oob_warning = Text(parent=self.hud_container, text='', position=(0, 0.22), origin=(0, 0), scale=1.6,
                                enabled=False, z=-2)

        self.damage_flash_overlay = Entity(parent=self.hud_container, model='quad', color=color.rgba(255, 0, 0, 0),
                                           scale=(99, 99), z=-1.5)

        self.hud_borders = []
        self.hud_borders.append(
            Entity(parent=self.hud_container, model='quad', color=color.rgba(255, 0, 0, 0), scale=(0.04, 2.0),
                   position=(-0.86, 0), z=-1.4))
        self.hud_borders.append(
            Entity(parent=self.hud_container, model='quad', color=color.rgba(255, 0, 0, 0), scale=(0.04, 2.0),
                   position=(0.86, 0), z=-1.4))
        self.hud_borders.append(
            Entity(parent=self.hud_container, model='quad', color=color.rgba(255, 0, 0, 0), scale=(2.0, 0.04),
                   position=(0, 0.48), z=-1.4))
        self.hud_borders.append(
            Entity(parent=self.hud_container, model='quad', color=color.rgba(255, 0, 0, 0), scale=(2.0, 0.04),
                   position=(0, -0.48), z=-1.4))

        self.screen_cracks = []
        for _ in range(8):
            crack = Entity(parent=self.hud_container, model='quad', color=color.rgba(200, 230, 255, 140),
                           scale=(random.uniform(0.15, 0.45), 0.003),
                           position=(random.uniform(-0.6, 0.6), random.uniform(-0.4, 0.4)),
                           rotation_z=random.uniform(0, 360), enabled=False, z=-2)
            self.screen_cracks.append(crack)

        self.crosshair = Entity(parent=self.hud_container, model='quad', color=color.rgba(255, 255, 255, 200),
                                scale=(0.006, 0.006), position=(0, 0))
        self.warning_text = Text(parent=self.hud_container, text='¡PELIGRO: NAVE INVERTIDA!', position=(0, 0.35),
                                 origin=(0, 0), color=color.red, scale=1.5, enabled=False)

        # ==========================================================
        # BRÚJULA TÁCTICA MINIMALISTA FLOTANTE Y AMPLIADA
        # ==========================================================
        # Nodo invisible de anclaje de posición
        self.compass_bg = Entity(parent=self.hud_container, position=(0, 0.43), z=-1)

        # Indicador central (muesca) en cian
        self.compass_marker = Entity(parent=self.hud_container, model='quad', color=color.cyan, scale=(0.003, 0.016),
                                     position=(0, 0.45), z=-1.1)

        # Marcadores cardinales y numéricos cada 30 grados
        self.compass_points = [
            ('N', 0), ('30', 30), ('NE', 45), ('60', 60),
            ('E', 90), ('120', 120), ('SE', 135), ('150', 150),
            ('S', 180), ('210', 210), ('SW', 225), ('240', 240),
            ('W', 270), ('300', 300), ('NW', 315), ('330', 330)
        ]
        self.compass_labels = []
        for label, angle in self.compass_points:
            t = Text(parent=self.hud_container, text=label, scale=0.8, color=color.white, origin=(0, 0), z=-1.2)
            self.compass_labels.append((t, angle))

        # TACÓMETRO E INSTRUMENTAL
        tacho_center_x = -0.72
        tacho_center_y = -0.32
        self.tacho_bg = Entity(parent=self.hud_container, model='circle', color=color.hex('#111111'), scale=0.25,
                               position=(tacho_center_x, tacho_center_y), z=1)
        self.tacho_needle = Entity(parent=self.tacho_bg, model='quad', color=color.hex('#ff3333'), scale=(0.02, 0.45),
                                   origin=(0, -0.5), position=(0, 0), rotation_z=-130, z=-0.1)
        Entity(parent=self.tacho_bg, model='circle', color=color.black, scale=0.15, z=-0.2)

        Text(parent=self.hud_container, text='0', position=(tacho_center_x - 0.08, tacho_center_y - 0.08),
             origin=(0, 0), scale=0.9, color=color.light_gray, z=-1)
        Text(parent=self.hud_container, text='1200', position=(tacho_center_x - 0.09, tacho_center_y + 0.02),
             origin=(0, 0), scale=0.9, color=color.light_gray, z=-1)
        Text(parent=self.hud_container, text='2200', position=(tacho_center_x - 0.04, tacho_center_y + 0.08),
             origin=(0, 0), scale=0.9, color=color.light_gray, z=-1)
        Text(parent=self.hud_container, text='3200', position=(tacho_center_x + 0.04, tacho_center_y + 0.08),
             origin=(0, 0), scale=0.9, color=color.light_gray, z=-1)
        Text(parent=self.hud_container, text='4200', position=(tacho_center_x + 0.09, tacho_center_y + 0.02),
             origin=(0, 0), scale=0.9, color=color.light_gray, z=-1)
        Text(parent=self.hud_container, text='5000', position=(tacho_center_x + 0.08, tacho_center_y - 0.08),
             origin=(0, 0), scale=0.9, color=color.red, z=-1)

        self.speedometer = Text(parent=self.hud_container, text='0', position=(tacho_center_x, tacho_center_y + 0.02),
                                origin=(0, 0), scale=3, color=color.white, z=-1)
        Text(parent=self.hud_container, text='KM/H', position=(tacho_center_x, tacho_center_y - 0.04), origin=(0, 0),
             scale=1.0, color=color.gray, z=-1)

        self.bottom_hud = Entity(parent=self.hud_container, position=(0, -0.42))
        Text(parent=self.bottom_hud, text='ESCUDO', position=(-0.25, 0.02), scale=0.8, color=color.cyan,
             origin=(0.5, 0))
        self.shield_bar_bg = Entity(parent=self.bottom_hud, model='quad', color=color.rgba(10, 15, 20, 200),
                                    scale=(0.22, 0.01), position=(-0.14, 0))
        self.shield_bar = Entity(parent=self.shield_bar_bg, model='quad', color=color.cyan, scale=(1, 1),
                                 origin=(0.5, 0), position=(0.5, 0))

        Text(parent=self.bottom_hud, text='TURBO', position=(0.25, 0.02), scale=0.8, color=color.orange,
             origin=(-0.5, 0))
        self.boost_bar_bg = Entity(parent=self.bottom_hud, model='quad', color=color.rgba(10, 15, 20, 200),
                                   scale=(0.22, 0.01), position=(0.14, 0))
        self.boost_bar = Entity(parent=self.boost_bar_bg, model='quad', color=color.orange, scale=(1, 1),
                                origin=(-0.5, 0), position=(-0.5, 0))

        self.base_fire_rate = 0.45
        self.min_fire_rate = 0.08
        self.current_fire_rate = self.base_fire_rate
        self.fire_timer = 0
        self.heat = 0
        self.max_heat = 100
        self.overheated = False

        self.heat_widget = Entity(parent=self.hud_container, position=(0.02, -0.02), enabled=False)
        self.heat_bar_bg = Entity(parent=self.heat_widget, model='quad', color=color.rgba(0, 0, 0, 150),
                                  scale=(0.06, 0.008), rotation_z=-20)
        self.heat_bar = Entity(parent=self.heat_bar_bg, model='quad', color=color.orange, scale=(0, 1),
                               origin=(-0.5, 0), position=(-0.5, 0))
        self.overheat_text = Text(parent=self.heat_widget, text='! ALERTA TERMICA !', color=color.red, scale=0.8,
                                  position=(0.04, -0.02), enabled=False)

    def cracks_on_damage(self):
        disabled_cracks = [c for c in self.screen_cracks if not c.enabled]
        if disabled_cracks:
            random.choice(disabled_cracks).enabled = True

    def generate_trail(self):
        self.trail_timer -= time.dt
        if self.trail_timer <= 0:
            for offset_x in [-0.6, 0.6]:
                for _ in range(2):
                    direccion_expulsion = 1 if offset_x > 0 else -1
                    trail_pos = self.position + (self.right * offset_x) + (self.up * -0.15) + (self.forward * 1.1)
                    p = Entity(model='sphere', color=color.rgba(0, 255, 255, 50), scale=random.uniform(0.06, 0.14),
                               position=trail_pos)
                    duracion_vida = random.uniform(0.12, 0.22)
                    p.animate_scale(Vec3(0, 0, 0), duration=duracion_vida, curve=curve.linear)
                    p.animate_color(color.rgba(0, 255, 255, 0), duration=duracion_vida, curve=curve.linear)
                    pos_final = p.position + (self.right * direccion_expulsion * random.uniform(1.2, 2.5)) + (
                            self.forward * -1.5)
                    p.animate_position(pos_final, duration=duracion_vida, curve=curve.out_sine)
                    destroy(p, delay=duracion_vida + 0.05)
            self.trail_timer = 0.025

    def start_dash(self, direction):
        self.is_dashing = True
        self.dash_time_left = self.dash_duration
        self.dash_timer = self.dash_cooldown
        self.dash_direction = direction
        self.dash_roll = 0
        self.animate('dash_roll', 360 * direction, duration=self.dash_duration, curve=curve.out_sine)
        self.boost_fuel -= 15
        self.boost_timer = self.boost_recharge_delay

    def take_damage(self, amount):
        if self.is_dead or self.is_cinematic: return
        self.shield -= amount
        self.shield = max(0, self.shield)
        self.shake_amount = clamp(self.shake_amount + 0.4, 0, 0.9)
        self.damage_flash_overlay.alpha = 0.5
        self.cracks_on_damage()
        if self.shield <= 0: self.die()

    def repair_shield(self, amount):
        if self.is_dead: return
        self.shield += amount
        self.shield = min(self.max_shield, self.shield)
        if self.shield > 15:
            for crack in self.screen_cracks: crack.enabled = False
            for b in self.hud_borders: b.alpha = 0

    def die(self):
        self.is_dead = True
        self.clear_persistent_ui()
        self.hud_container.disable()
        camera.ui.x = 0
        camera.ui.y = 0
        self.camera_pivot.position = Vec3(0, 0, 0)
        self.scanner.clear_markers()
        self.scanner.active = False
        if self.game_over_menu: self.game_over_menu.enabled = True
        mouse.locked = False
        self.visible = False
        self.collider = None

    def reset_ship(self):
        self.is_cinematic = False
        self.position = (0, 0, 0)
        self.rotation = (0, 0, 0)
        self.base_pitch = 0.0
        self.current_speed = 0
        self.target_speed = 0
        self.boost_fuel = 100
        self.shield = 100
        self.heat = 0
        self.overheated = False
        self.is_dead = False
        self.visible = True
        self.collider = 'box'
        self.dash_timer = 0
        self.is_dashing = False
        self.heat_widget.enabled = False
        self.overheat_text.enabled = False
        self.heat_bar.color = color.orange
        self.tacho_needle.color = color.hex('#ff3333')
        self.speedometer.color = color.white
        self.scanner.clear_markers()
        self.scanner.active = False
        self.oob_timer = 10.0

        self.hud_container.enable()
        self.damage_flash_overlay.alpha = 0
        camera.ui.x = 0
        camera.ui.y = 0
        self.camera_pivot.position = Vec3(0, 0, 0)
        for b in self.hud_borders: b.alpha = 0
        for crack in self.screen_cracks: crack.enabled = False
        for t in self.thrusters: t.visible = True
        self.clear_persistent_ui()

    def clear_persistent_ui(self):
        if hasattr(self, 'scanner') and self.scanner:
            self.scanner.clear_markers()
            if hasattr(self.scanner, 'analyzing_text') and self.scanner.analyzing_text:
                self.scanner.analyzing_text.enabled = False
            if hasattr(self.scanner, 'scan_line') and self.scanner.scan_line:
                self.scanner.scan_line.enabled = False
        if hasattr(self, 'oob_warning') and self.oob_warning:
            self.oob_warning.enabled = False

    def update(self):
        if hasattr(self, 'scanner'): self.scanner.update()

        hide_ui = self.is_dead or self.is_cinematic
        self.compass_bg.enabled = not hide_ui
        self.compass_marker.enabled = not hide_ui

        # ==========================================================
        # ACTUALIZACIÓN DE BRÚJULA TÁCTICA EXPANDIDA PANORÁMICA
        # ==========================================================
        current_heading = self.rotation_y % 360
        for lbl_text, angle in self.compass_labels:
            if hide_ui:
                lbl_text.enabled = False
                continue

            diff = (angle - current_heading) % 360
            if diff > 180:
                diff -= 360

            # Rango visual ampliado a 60 grados para poblar la línea más larga
            if abs(diff) < 60:
                lbl_text.enabled = True
                # Multiplicador aumentado a 0.35 para estirar horizontalmente por la pantalla
                lbl_text.x = (diff / 60) * 0.35
                lbl_text.y = 0.44

                # Desvanecimiento dinámico adaptado al nuevo ancho de 60 grados
                alpha_factor = 1.0 - (abs(diff) / 60.0)
                txt = lbl_text.text

                if txt in ['N', 'S', 'E', 'W']:
                    lbl_text.color = color.rgba(0, 255, 255, int(255 * alpha_factor))
                elif txt in ['NE', 'SE', 'SW', 'NW']:
                    lbl_text.color = color.rgba(255, 255, 255, int(255 * alpha_factor))
                else:
                    lbl_text.color = color.rgba(220, 220, 225, int(190 * alpha_factor))
            else:
                lbl_text.enabled = False

        if self.is_dead:
            self.current_speed = lerp(self.current_speed, 0, time.dt * self.friction)
            self.speedometer.text = str(int(abs(self.current_speed)))
            self.tacho_needle.rotation_z = -130 + (clamp(abs(self.current_speed) / self.boost_max_speed, 0, 1) * 260)
            self.warning_text.enabled = False
            self.camera_pivot.position = lerp(self.camera_pivot.position, Vec3(0, 0, 0), time.dt * 15)
            for t in self.thrusters:
                t.scale_z = lerp(t.scale_z, 0, time.dt * 15)
                t.visible = False
            return

        if self.is_cinematic:
            for t in self.thrusters:
                t.scale_z = lerp(t.scale_z, random.uniform(0.3, 0.5), time.dt * 12)
                t.color = color.rgba(0, 180, 255, 120)
            return

        # LÍMITES DEL SECTOR
        distancia_centro = self.position.length()
        if distancia_centro > self.sector_radius:
            self.oob_warning.enabled = True
            self.damage_flash_overlay.alpha = random.uniform(0.2, 0.4)
            self.shake_amount = max(self.shake_amount, 0.25)

            self.oob_timer -= time.dt
            self.oob_warning.text = f'<red>¡ADVERTENCIA CRÍTICA!\n<white>ABANDONANDO SECTOR DE EXTRACCIÓN ALFA\n<red>DESPRESURIZACIÓN EN: {max(0, int(self.oob_timer))}s'

            if self.oob_timer <= 0:
                self.shield = 0
                self.die()
                return
        else:
            self.oob_warning.enabled = False
            self.oob_timer = 10.0

            if self.shield <= 15:
                pulso_alerta = 0.3 + math.sin(time.time() * 12) * 0.15
                for b in self.hud_borders: b.alpha = pulso_alerta
                for crack in self.screen_cracks: crack.enabled = True
                camera.fov += random.uniform(-0.8, 0.8)
                camera.ui.x = random.uniform(-0.006, 0.006)
                camera.ui.y = random.uniform(-0.006, 0.006)

                self.error_spawn_timer -= time.dt
                if self.error_spawn_timer <= 0:
                    mensajes_error = ["SISTEMA DEFECTUOSO", "NÚCLEO CRÍTICO", "ERROR: 0x00F8C3", "FUGA DE VOLTAJE",
                                      "FALLO ESTRUCTURAL", "PRESIÓN BAJA"]
                    err_txt = Text(text=random.choice(mensajes_error),
                                   position=(random.uniform(-0.4, 0.4), random.uniform(-0.2, 0.2)), color=color.red,
                                   scale=random.uniform(1.1, 1.5), parent=self.hud_container)
                    destroy(err_txt, delay=random.uniform(0.15, 0.3))
                    self.error_spawn_timer = random.uniform(0.25, 0.55)
            else:
                for b in self.hud_borders: b.alpha = 0
                camera.ui.x = 0
                camera.ui.y = 0

        # PLANETA O ASTEROIDES COLISIÓN
        hit_info = self.intersects()
        if hit_info.hit:
            ent = hit_info.entity
            if hasattr(ent, 'is_planet'):
                self.shield = 0
                self.take_damage(9999)
                return
            if hasattr(ent, 'is_asteroid'):
                from weapons import ExplosionParticle
                for _ in range(25):
                    ExplosionParticle(pos=ent.position)

                rebound_dir = (self.position - ent.position).normalized()
                self.position += rebound_dir * 1.5
                self.current_speed = -self.current_speed * 0.15
                ent.split()
                self.take_damage(30)
                return

        if self.damage_flash_overlay.alpha > 0 and distancia_centro <= self.sector_radius:
            self.damage_flash_overlay.alpha = lerp(self.damage_flash_overlay.alpha, 0, time.dt * 6)

        self.shield_bar.scale_x = self.shield / self.max_shield
        self.shield_bar.color = color.red if self.shield <= 15 else color.cyan

        if self.up.y < -0.1:
            self.warning_text.enabled = True
        else:
            self.warning_text.enabled = False

        is_boosting = held_keys['space'] and self.boost_fuel > 0

        if is_boosting:
            self.target_speed = self.boost_max_speed
            self.boost_fuel -= 18 * time.dt
            self.boost_timer = self.boost_recharge_delay
            self.generate_trail()
            self.shake_amount = max(self.shake_amount, 0.15)
            self.speed_line_timer -= time.dt
            if self.speed_line_timer <= 0:
                for _ in range(3): SpeedLine()
                self.speed_line_timer = 0.015
        elif held_keys['w']:
            self.target_speed = self.normal_max_speed
        elif held_keys['s']:
            self.target_speed = -self.normal_max_speed / 2
        else:
            self.target_speed = 0

        lerp_factor = self.acceleration if abs(self.target_speed) > abs(self.current_speed) else self.friction
        self.current_speed = lerp(self.current_speed, self.target_speed, time.dt * lerp_factor)

        speed_ratio = clamp(abs(self.current_speed) / self.boost_max_speed, 0, 1)
        target_fov = self.base_fov + (speed_ratio * 35.0)
        camera.fov = lerp(camera.fov, target_fov, time.dt * 5)

        self.position += self.forward * self.current_speed * time.dt

        if is_boosting:
            target_scale_z = random.uniform(3.5, 4.8)
            thruster_color = color.rgb(0, 255, 255)
        elif held_keys['w']:
            target_scale_z = random.uniform(1.3, 1.6)
            thruster_color = color.cyan
        elif held_keys['s']:
            target_scale_z = 0.15
            thruster_color = color.blue
        else:
            target_scale_z = random.uniform(0.3, 0.5)
            thruster_color = color.rgba(0, 180, 255, 120)

        for t in self.thrusters:
            t.scale_z = lerp(t.scale_z, target_scale_z, time.dt * 12)
            t.color = thruster_color
            if is_boosting or held_keys['w']:
                t.scale_x = lerp(t.scale_x, random.uniform(0.18, 0.24), time.dt * 20)
                t.scale_y = t.scale_x
            else:
                t.scale_x = lerp(t.scale_x, 0.2, time.dt * 10)
                t.scale_y = 0.2

        if self.dash_timer > 0: self.dash_timer -= time.dt

        if self.is_dashing:
            self.dash_time_left -= time.dt
            self.position += self.right * self.dash_direction * self.dash_speed * time.dt
            self.generate_trail()
            self.generate_trail()
            if self.dash_time_left <= 0:
                self.is_dashing = False
                self.dash_roll = 0

        if not is_boosting:
            if self.boost_timer > 0:
                self.boost_timer -= time.dt
            else:
                self.boost_fuel += 30 * time.dt
        self.boost_fuel = clamp(self.boost_fuel, 0, self.max_boost)
        self.boost_bar.scale_x = self.boost_fuel / self.max_boost

        display_speed = int(abs(self.current_speed) * 20)
        self.speedometer.text = str(display_speed)
        self.tacho_needle.rotation_z = -130 + (speed_ratio * 260)

        if speed_ratio > 0.8:
            self.tacho_needle.color = color.red
            self.speedometer.color = color.orange
        else:
            self.tacho_needle.color = color.hex('#ff3333')
            self.speedometer.color = color.white

        if held_keys['right mouse']:
            self.camera_pivot.rotation_y += mouse.velocity[0] * self.mouse_sensitivity
            self.camera_pivot.rotation_x -= mouse.velocity[1] * self.mouse_sensitivity
            self.camera_pivot.rotation_y = clamp(self.camera_pivot.rotation_y, -90, 90)
            self.camera_pivot.rotation_x = clamp(self.camera_pivot.rotation_x, -45, 45)
            target_cam_offset_x = 0
            target_cam_offset_y = 0
        else:
            self.camera_pivot.rotation_y = lerp(self.camera_pivot.rotation_y, 0, time.dt * 10)
            self.rotation_y += mouse.velocity[0] * self.mouse_sensitivity
            self.base_pitch -= mouse.velocity[1] * self.mouse_sensitivity

            accel_pitch = 0
            if is_boosting:
                accel_pitch = 8.0
            elif held_keys['w']:
                accel_pitch = 3.0
            elif held_keys['s']:
                accel_pitch = -3.0

            target_pitch = self.base_pitch + accel_pitch
            self.rotation_x = lerp(self.rotation_x, target_pitch, time.dt * 12)
            visual_pitch_offset = self.rotation_x - self.base_pitch
            self.camera_pivot.rotation_x = lerp(self.camera_pivot.rotation_x, -visual_pitch_offset, time.dt * 12)

            target_cam_offset_x = 0
            target_cam_offset_y = 0

        if self.is_dashing: target_cam_offset_x -= self.dash_direction * self.camera_dash_drag
        target_cam_offset_x = clamp(target_cam_offset_x, -1.2, 1.2)
        target_cam_offset_y = clamp(target_cam_offset_y, -0.7, 0.7)
        self.camera_pivot.position = lerp(self.camera_pivot.position, Vec3(target_cam_offset_x, target_cam_offset_y, 0),
                                          time.dt * 18)

        base_z_target = self.rotation_z
        if held_keys['q']:
            self.rotation_z -= self.roll_speed * time.dt
            self.auto_level_timer = self.auto_level_delay
            base_z_target = self.rotation_z
        elif held_keys['e']:
            self.rotation_z += self.roll_speed * time.dt
            self.auto_level_timer = self.auto_level_delay
            base_z_target = self.rotation_z
        else:
            target_z = round(self.rotation_z / 360) * 360
            if not held_keys['right mouse']:
                target_banking = clamp(mouse.velocity[0] * 350, -self.max_banking_angle, self.max_banking_angle)
                target_z += target_banking

            if self.auto_level_timer > 0:
                self.auto_level_timer -= time.dt
                if not held_keys['right mouse'] and abs(mouse.velocity[0]) > 0.005:
                    self.rotation_z = lerp(self.rotation_z, target_z, time.dt * 6)
            else:
                self.rotation_z = lerp(self.rotation_z, target_z, time.dt * self.level_damping)
            base_z_target = target_z

        if self.is_dashing: self.rotation_z = base_z_target + self.dash_roll
        self.camera_pivot.world_rotation_z = 0

        base_cam_pos = self.camera_modes[self.current_cam_index]
        dynamic_z_back = speed_ratio * 4.0

        if self.shake_amount > 0:
            self.shake_amount -= time.dt * self.shake_decay
            self.shake_amount = max(0.0, self.shake_amount)
            camera.x = base_cam_pos[0] + random.uniform(-self.shake_amount, self.shake_amount)
            camera.y = base_cam_pos[1] + random.uniform(-self.shake_amount, self.shake_amount)
        else:
            camera.x = base_cam_pos[0]
            camera.y = base_cam_pos[1]

        camera.z = base_cam_pos[2] - dynamic_z_back

        self.fire_timer -= time.dt
        self.heat -= 40 * time.dt
        if not held_keys['left mouse']: self.current_fire_rate = lerp(self.current_fire_rate, self.base_fire_rate,
                                                                      time.dt * 3)
        self.heat = clamp(self.heat, 0, self.max_heat)

        if self.heat > 1:
            self.heat_widget.enabled = True
            alpha_val = clamp(self.heat / 20, 0, 1)
            self.heat_bar.color = color.rgba(255, 165, 0, int(255 * alpha_val)) if not self.overheated else color.rgba(
                255, 50, 50, int(255 * alpha_val))
            self.heat_bar_bg.color = color.rgba(0, 0, 0, int(150 * alpha_val))
        else:
            self.heat_widget.enabled = False

        self.heat_bar.scale_x = self.heat / self.max_heat

        if self.heat >= self.max_heat and not self.overheated:
            self.overheated = True
            self.overheat_text.enabled = True

        if self.overheated and self.heat <= 20:
            self.overheated = False
            self.overheat_text.enabled = False

        if held_keys['left mouse'] and not self.overheated and self.fire_timer <= 0:
            true_aim_rotation = Vec3(self.base_pitch, self.rotation_y, self.rotation_z)
            from weapons import DualLaser
            DualLaser(self.position, true_aim_rotation, self.forward, self.right, self.up,
                      offset_x=self.right_laser_offset[0], offset_y=self.right_laser_offset[1],
                      offset_z=self.right_laser_offset[2])
            DualLaser(self.position, true_aim_rotation, self.forward, self.right, self.up,
                      offset_x=self.left_laser_offset[0], offset_y=self.left_laser_offset[1],
                      offset_z=self.left_laser_offset[2])

            self.shake_amount = clamp(self.shake_amount + 0.2, 0, 0.6)
            self.heat += 7
            self.current_fire_rate = max(self.min_fire_rate, self.current_fire_rate - 0.05)
            self.fire_timer = self.current_fire_rate

        self.heat_bar.scale_x = self.heat / self.max_heat

    def input(self, key):
        if self.is_dead or self.is_cinematic: return
        if key == 'v':
            self.current_cam_index += 1
            if self.current_cam_index >= len(self.camera_modes):
                self.current_cam_index = 0
            camera.position = self.camera_modes[self.current_cam_index]
        if key == 'a' and self.dash_timer <= 0 and self.boost_fuel >= 15:
            self.start_dash(-1)
        if key == 'd' and self.dash_timer <= 0 and self.boost_fuel >= 15:
            self.start_dash(1)
        if key == 'x':
            self.scanner.toggle()