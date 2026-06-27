from ursina import *
from player import PlayerShip
from environment import AsteroidManager, CosmicBackground, SpaceDustManager
from menu import MainMenu
from cinematics import IntroCinematic


class PauseMenu(Entity):
    def __init__(self, game_instance, **kwargs):
        super().__init__(parent=camera.ui, ignore_paused=True, enabled=False, **kwargs)
        self.game = game_instance
        Entity(parent=self, model='quad', color=color.black66, scale=(99, 99), z=1)
        Text(parent=self, text='PAUSA', origin=(0, 0), scale=5, color=color.white, position=(0, 0.25), z=-1)

        self.btn_resume = Button(parent=self, text='Regresar al juego', scale=(0.4, 0.08), position=(0, 0.05),
                                 color=color.dark_gray, highlight_color=color.gray, on_click=self.resume, z=-1)
        self.btn_exit = Button(parent=self, text='Salir al Menú Principal', scale=(0.4, 0.08), position=(0, -0.08),
                               color=color.red, highlight_color=color.rgb(255, 80, 80), on_click=self.go_to_menu, z=-1)

    def resume(self):
        application.paused = False
        self.enabled = False
        mouse.locked = True
        self.game.player.hud_container.enable()

    def go_to_menu(self):
        application.paused = False
        self.enabled = False
        self.game.return_to_main_menu()


class PauseController(Entity):
    def __init__(self, game_instance, **kwargs):
        super().__init__(ignore_paused=True, **kwargs)
        self.game = game_instance

    def input(self, key):
        if key == 'p':
            if self.game.game_over_menu.enabled or self.game.main_menu.ui_container.enabled:
                return
            application.paused = not application.paused
            self.game.pause_menu.enabled = application.paused
            mouse.locked = not application.paused
            if application.paused:
                self.game.player.hud_container.disable()
            else:
                self.game.player.hud_container.enable()


class GameOverMenu(Entity):
    def __init__(self, restart_func, **kwargs):
        super().__init__(parent=camera.ui, ignore_paused=True, enabled=False, **kwargs)
        Entity(parent=self, model='quad', color=color.rgba(0, 0, 0, 220), scale=(99, 99), z=1)
        Text(parent=self, text='GAME OVER', origin=(0, 0), scale=5, color=color.red, position=(0, 0.25), z=-1)

        self.btn_restart = Button(parent=self, text='Volver a jugar', scale=(0.4, 0.08), position=(0, 0.05),
                                  color=color.dark_gray, highlight_color=color.gray, on_click=restart_func, z=-1)
        self.btn_exit = Button(parent=self, text='Salir', scale=(0.4, 0.08), position=(0, -0.08),
                               color=color.red, highlight_color=color.rgb(255, 80, 80), on_click=application.quit, z=-1)


class GameApp:
    def __init__(self):
        self.app = Ursina()
        window.size = (1600, 900)
        window.center_on_screen()
        window.color = color.black
        window.title = "Astra 3D"
        window.fps_counter.enabled = True
        window.exit_button.visible = False

        # Plano de renderizado seguro para evitar el quiebre de profundidad
        camera.clip_plane_far = 10000
        self.sky = Sky(color=color.black)

        self.game_over_menu = GameOverMenu(restart_func=self.restart_game)
        self.pause_menu = PauseMenu(game_instance=self)
        self.pause_controller = PauseController(game_instance=self)
        self.main_menu = MainMenu(start_game_func=self.start_actual_game)

        self.cosmic_bg = CosmicBackground()
        self.cosmic_bg.enabled = False

        self.player = PlayerShip(game_over_menu=self.game_over_menu)
        self.environment = AsteroidManager(player=self.player, count=60, radius=300)
        self.space_dust = SpaceDustManager(player=self.player, count=200, radius=60)
        self.intro_cinematic = IntroCinematic(self.player)

        self.player.enabled = False
        self.space_dust.enabled = False
        mouse.locked = False

        self.player.hud_container.disable()

    def start_actual_game(self):
        window.color = color.black
        self.cosmic_bg.enabled = True
        self.space_dust.enabled = True
        self.player.reset_ship()
        self.intro_cinematic.play()
        mouse.locked = True

    def return_to_main_menu(self):
        self.intro_cinematic.stop_and_clear()
        self.player.enabled = False
        self.player.clear_persistent_ui()
        self.player.hud_container.disable()
        self.cosmic_bg.enabled = False
        self.space_dust.enabled = False
        self.environment.clear_and_respawn()

        camera.parent = scene
        camera.position = (0, 0, 0)
        camera.rotation = (0, 0, 0)
        self.main_menu.enable()
        self.main_menu.reset_menu_state()
        mouse.locked = False

    def restart_game(self):
        self.intro_cinematic.stop_and_clear()
        self.player.reset_ship()
        self.environment.clear_and_respawn()
        self.space_dust.reset_particles()
        self.game_over_menu.enabled = False

        camera.parent = self.player.camera_pivot
        camera.position = self.player.camera_modes[self.player.current_cam_index]
        camera.rotation = (0, 0, 0)
        mouse.locked = True
        application.paused = False

    def run(self):
        self.app.run()


if __name__ == '__main__':
    game = GameApp()
    game.run()