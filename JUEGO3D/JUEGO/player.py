from ursina import *
from weapons import DualLaser
import random


class PlayerShip(Entity):
    """Clase de la nave con Screen Shake, Banking Horizontal, Banking Vertical, Dash y Game Over"""

    def __init__(self, game_over_menu=None, **kwargs):
        super().__init__(
            model='assets/nave1/SpaceShip.obj',
            color=color.white,
            scale=(0.2, 0.2, 0.2),
            position=(0, 0, 0),
            collider='box',
            **kwargs
        )

        self.game_over_menu = game_over_menu
        self.is_dead = False  # Control de estado de vida

        self.right_laser_offset = (2.4, -0.5, -0.6)
        self.left_laser_offset = (-2.4, -0.5, -0.6)

        self.target_speed = 0
        self.current_speed = 0
        self.normal_max_speed = 70
        self.boost_max_speed = 220
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
        self.dash_speed = 180
        self.dash_roll = 0.0

        self.shake_amount = 0.0
        self.shake_decay = 12.0

        self.max_boost = 100
        self.boost_fuel = 100
        self.boost_recharge_delay = 1.5
        self.boost_timer = 0
        self.trail_timer = 0

        self.camera_pivot = Entity(parent=self)
        camera.parent = self.camera_pivot
        self.camera_modes = [(0, 1.0, -9), (0, 1.5, -14), (0, 2.5, -20)]
        self.current_cam_index = 1
        camera.position = self.camera_modes[self.current_cam_index]
        camera.rotation = (0, 0, 0)
        self.base_fov = camera.fov
        mouse.locked = True

        self.crosshair = Entity(parent=camera.ui, model='quad', color=color.rgba(255, 255, 255, 200),
                                scale=(0.006, 0.006), position=(0, 0))
        self.warning_text = Text(text='¡PELIGRO: NAVE INVERTIDA!', position=(0, 0.25), origin=(0, 0), color=color.red,
                                 scale=1.5, enabled=False)

        tacho_center_x = -0.72
        tacho_center_y = -0.32

        self.tacho_bg = Entity(parent=camera.ui, model='circle', color=color.hex('#111111'), scale=0.25,
                               position=(tacho_center_x, tacho_center_y), z=1)
        self.tacho_needle = Entity(parent=self.tacho_bg, model='quad', color=color.hex('#ff3333'), scale=(0.02, 0.45),
                                   origin=(0, -0.5), position=(0, 0), rotation_z=-130, z=-0.1)
        Entity(parent=self.tacho_bg, model='circle', color=color.black, scale=0.15, z=-0.2)

        Text(parent=camera.ui, text='0', position=(tacho_center_x - 0.08, tacho_center_y - 0.08), origin=(0, 0),
             scale=0.9, color=color.light_gray, z=-1)
        Text(parent=camera.ui, text='45', position=(tacho_center_x - 0.09, tacho_center_y + 0.02), origin=(0, 0),
             scale=0.9, color=color.light_gray, z=-1)
        Text(parent=camera.ui, text='90', position=(tacho_center_x - 0.04, tacho_center_y + 0.08), origin=(0, 0),
             scale=0.9, color=color.light_gray, z=-1)
        Text(parent=camera.ui, text='135', position=(tacho_center_x + 0.04, tacho_center_y + 0.08), origin=(0, 0),
             scale=0.9, color=color.light_gray, z=-1)
        Text(parent=camera.ui, text='180', position=(tacho_center_x + 0.09, tacho_center_y + 0.02), origin=(0, 0),
             scale=0.9, color=color.light_gray, z=-1)
        Text(parent=camera.ui, text='220', position=(tacho_center_x + 0.08, tacho_center_y - 0.08), origin=(0, 0),
             scale=0.9, color=color.red, z=-1)

        self.speedometer = Text(parent=camera.ui, text='0', position=(tacho_center_x, tacho_center_y + 0.02),
                                origin=(0, 0), scale=3, color=color.white, z=-1)
        Text(parent=camera.ui, text='KM/H', position=(tacho_center_x, tacho_center_y - 0.04), origin=(0, 0), scale=1.0,
             color=color.gray, z=-1)

        self.boost_bar_bg = Entity(parent=camera.ui, model='quad', color=color.rgba(30, 35, 40, 250),
                                   scale=(0.02, 0.18), position=(tacho_center_x + 0.16, tacho_center_y), z=1)
        self.boost_bar = Entity(parent=self.boost_bar_bg, model='quad', color=color.cyan, scale=(1, 1),
                                position=(0, -0.5), origin=(0, -0.5), z=-1)
        Text(parent=camera.ui, text='TURBO', position=(tacho_center_x + 0.16, tacho_center_y - 0.11), origin=(0, 0),
             scale=0.8, color=color.white, z=-1)

        self.base_fire_rate = 0.45
        self.min_fire_rate = 0.08
        self.current_fire_rate = self.base_fire_rate
        self.fire_timer = 0
        self.heat = 0
        self.max_heat = 100
        self.overheated = False

        self.heat_bar_bg = Entity(parent=camera.ui, model='quad', color=color.dark_gray, scale=(0.3, 0.02),
                                  position=(0, -0.45), z=1)
        self.heat_bar = Entity(parent=self.heat_bar_bg, model='quad', color=color.orange, scale=(0, 1),
                               position=(-0.5, 0), origin=(-0.5, 0), z=-1)
        self.overheat_text = Text(parent=camera.ui, text='', origin=(0, 0), position=(0, -0.35), color=color.red,
                                  scale=1.5, z=-1)

    def generate_trail(self):
        self.trail_timer -= time.dt
        if self.trail_timer <= 0:
            for offset_x in [-1.5, 1.5]:
                trail_pos = self.position + (self.right * offset_x) + (self.up * -0.2) + (self.forward * -1.5)
                p = Entity(model='cube', color=color.cyan, scale=(0.3, 0.3, 0.3), position=trail_pos,
                           rotation=self.rotation)
                p.animate_scale(Vec3(0, 0, 0), duration=0.4, curve=curve.linear)
                destroy(p, delay=0.5)
            self.trail_timer = 0.015

    def start_dash(self, direction):
        self.is_dashing = True
        self.dash_time_left = self.dash_duration
        self.dash_timer = self.dash_cooldown
        self.dash_direction = direction

        self.dash_roll = 0
        self.animate('dash_roll', 360 * direction, duration=self.dash_duration, curve=curve.out_sine)

        self.boost_fuel -= 15
        self.boost_timer = self.boost_recharge_delay

    def reset_ship(self):
        """NUEVO: Restablece todos los valores de la nave al reiniciar el juego"""
        self.position = (0, 0, 0)
        self.rotation = (0, 0, 0)
        self.base_pitch = 0.0
        self.current_speed = 0
        self.target_speed = 0
        self.boost_fuel = 100
        self.heat = 0
        self.overheated = False
        self.is_dead = False
        self.visible = True
        self.collider = 'box'  # Reactivamos la colisión física
        self.dash_timer = 0
        self.is_dashing = False
        self.overheat_text.text = ''
        self.heat_bar.color = color.orange
        self.tacho_needle.color = color.hex('#ff3333')
        self.speedometer.color = color.white

    def update(self):
        # Si la nave chocó, detenemos las físicas y dejamos caer las agujas a cero
        if self.is_dead:
            self.current_speed = lerp(self.current_speed, 0, time.dt * self.friction)
            self.speedometer.text = str(int(abs(self.current_speed)))
            self.tacho_needle.rotation_z = -130 + (clamp(abs(self.current_speed) / self.boost_max_speed, 0, 1) * 260)
            self.warning_text.enabled = False
            return

        # Detección de colisión con un asteroide
        hit_info = self.intersects()
        if hit_info.hit and hasattr(hit_info.entity, 'is_asteroid'):
            self.is_dead = True
            if self.game_over_menu:
                self.game_over_menu.enabled = True
            mouse.locked = False
            self.visible = False  # Ocultamos el modelo visualmente
            self.collider = None  # Desactivamos las hitboxes para que no rebote muerta
            return

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
        elif held_keys['w']:
            self.target_speed = self.normal_max_speed
        elif held_keys['s']:
            self.target_speed = -self.normal_max_speed / 2
        else:
            self.target_speed = 0

        lerp_factor = self.acceleration if abs(self.target_speed) > abs(self.current_speed) else self.friction
        self.current_speed = lerp(self.current_speed, self.target_speed, time.dt * lerp_factor)
        self.position += self.forward * self.current_speed * time.dt
        camera.fov = lerp(camera.fov, self.base_fov + (abs(self.current_speed) * 0.35), time.dt * 5)

        if self.dash_timer > 0:
            self.dash_timer -= time.dt

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
        self.boost_bar.scale_y = self.boost_fuel / self.max_boost

        display_speed = int(abs(self.current_speed))
        self.speedometer.text = str(display_speed)

        speed_ratio = clamp(abs(self.current_speed) / self.boost_max_speed, 0, 1)
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
        else:
            self.camera_pivot.rotation_y = lerp(self.camera_pivot.rotation_y, 0, time.dt * 10)
            self.rotation_y += mouse.velocity[0] * self.mouse_sensitivity
            self.base_pitch -= mouse.velocity[1] * self.mouse_sensitivity

            pitch_overshoot = clamp(mouse.velocity[1] * 600, -self.max_pitch_banking, self.max_pitch_banking)

            accel_pitch = 0
            if is_boosting:
                accel_pitch = 8.0
            elif held_keys['w']:
                accel_pitch = 3.0
            elif held_keys['s']:
                accel_pitch = -3.0

            target_pitch = self.base_pitch - pitch_overshoot + accel_pitch
            self.rotation_x = lerp(self.rotation_x, target_pitch, time.dt * 12)

            visual_pitch_offset = self.rotation_x - self.base_pitch
            self.camera_pivot.rotation_x = lerp(self.camera_pivot.rotation_x, -visual_pitch_offset, time.dt * 10)

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

        if self.is_dashing:
            self.rotation_z = base_z_target + self.dash_roll

        self.camera_pivot.world_rotation_z = 0

        base_cam_pos = self.camera_modes[self.current_cam_index]
        if self.shake_amount > 0:
            self.shake_amount -= time.dt * self.shake_decay
            self.shake_amount = max(0.0, self.shake_amount)

            camera.x = base_cam_pos[0] + random.uniform(-self.shake_amount, self.shake_amount)
            camera.y = base_cam_pos[1] + random.uniform(-self.shake_amount, self.shake_amount)
        else:
            camera.x = base_cam_pos[0]
            camera.y = base_cam_pos[1]

        camera.z = base_cam_pos[2]

        self.fire_timer -= time.dt
        if not held_keys['left mouse']:
            self.heat -= 40 * time.dt
            self.current_fire_rate = lerp(self.current_fire_rate, self.base_fire_rate, time.dt * 3)
        self.heat = clamp(self.heat, 0, self.max_heat)

        if self.heat >= self.max_heat and not self.overheated:
            self.overheated = True
            self.overheat_text.text = '¡SOBRECALENTAMIENTO! ESPERE...'
            self.heat_bar.color = color.red

        if self.overheated and self.heat <= 20:
            self.overheated = False
            self.overheat_text.text = ''
            self.heat_bar.color = color.orange

        if held_keys['left mouse'] and not self.overheated and self.fire_timer <= 0:
            true_aim_rotation = Vec3(self.base_pitch, self.rotation_y, self.rotation_z)

            DualLaser(self.position, true_aim_rotation, self.forward, self.right, self.up,
                      offset_x=self.right_laser_offset[0], offset_y=self.right_laser_offset[1],
                      offset_z=self.right_laser_offset[2])
            DualLaser(self.position, true_aim_rotation, self.forward, self.right, self.up,
                      offset_x=self.left_laser_offset[0], offset_y=self.left_laser_offset[1],
                      offset_z=self.left_laser_offset[2])

            self.shake_amount = clamp(self.shake_amount + 0.2, 0, 0.6)
            self.heat += 6
            self.current_fire_rate = max(self.min_fire_rate, self.current_fire_rate - 0.05)
            self.fire_timer = self.current_fire_rate

        self.heat_bar.scale_x = self.heat / self.max_heat

    def input(self, key):
        if self.is_dead:
            return  # No permitir acciones si la nave está destruida

        if key == 'v':
            self.current_cam_index += 1
            if self.current_cam_index >= len(self.camera_modes):
                self.current_cam_index = 0
            camera.position = self.camera_modes[self.current_cam_index]

        if key == 'a' and self.dash_timer <= 0 and self.boost_fuel >= 15:
            self.start_dash(-1)
        if key == 'd' and self.dash_timer <= 0 and self.boost_fuel >= 15:
            self.start_dash(1)