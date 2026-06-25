from ursina import *
from player import PlayerShip
from environment import AsteroidManager, SpaceGrid, SpaceDustManager


class PauseMenu(Entity):
    """Menú de pausa interactivo con cristal oscuro transparente garantizado"""

    def __init__(self, **kwargs):
        super().__init__(parent=camera.ui, ignore_paused=True, enabled=False, **kwargs)

        Entity(
            parent=self,
            model='quad',
            color=color.black66,
            scale=(99, 99),
            z=1
        )

        Text(parent=self, text='PAUSA', origin=(0, 0), scale=5, color=color.white, position=(0, 0.25), z=-1)

        self.btn_resume = Button(parent=self, text='Regresar al juego', scale=(0.4, 0.08), position=(0, 0.05),
                                 color=color.dark_gray, highlight_color=color.gray, on_click=self.resume, z=-1)

        self.btn_exit = Button(parent=self, text='Salir', scale=(0.4, 0.08), position=(0, -0.08),
                               color=color.red, highlight_color=color.rgb(255, 80, 80), on_click=application.quit, z=-1)

    def resume(self):
        application.paused = False
        self.enabled = False
        mouse.locked = True


class PauseController(Entity):
    """Controlador que escucha la tecla P en todo momento para alternar la pausa"""

    def __init__(self, pause_panel, **kwargs):
        super().__init__(ignore_paused=True, **kwargs)
        self.pause_panel = pause_panel

    def input(self, key):
        if key == 'p':
            if hasattr(self.pause_panel.parent, 'game_over_menu') and self.pause_panel.parent.game_over_menu.enabled:
                return  # No pausar si ya estás en Game Over
            application.paused = not application.paused
            self.pause_panel.enabled = application.paused
            mouse.locked = not application.paused


class GameOverMenu(Entity):
    """NUEVO: Menú de Game Over que aparece al colisionar con un asteroide"""

    def __init__(self, restart_func, **kwargs):
        super().__init__(parent=camera.ui, ignore_paused=True, enabled=False, **kwargs)

        # Fondo oscuro translúcido
        Entity(
            parent=self,
            model='quad',
            color=color.rgba(0, 0, 0, 220),
            scale=(99, 99),
            z=1
        )

        Text(parent=self, text='GAME OVER', origin=(0, 0), scale=5, color=color.red, position=(0, 0.25), z=-1)

        self.btn_restart = Button(parent=self, text='Volver a jugar', scale=(0.4, 0.08), position=(0, 0.05),
                                  color=color.dark_gray, highlight_color=color.gray, on_click=restart_func, z=-1)

        self.btn_exit = Button(parent=self, text='Salir', scale=(0.4, 0.08), position=(0, -0.08),
                               color=color.red, highlight_color=color.rgb(255, 80, 80), on_click=application.quit, z=-1)


class GameApp:
    def __init__(self):
        self.app = Ursina()

        window.size = (1600, 900)
        window.position = Vec2(100, 50)
        window.color = color.black
        window.title = "Simulador Espacial 3D"
        window.fps_counter.enabled = True

        window.exit_button.visible = False
        window.exit_button.enabled = False

        Sky(color=color.dark_gray)

        self.space_grid = SpaceGrid(size=1000)

        # 1. Inicializar primero el menú de Game Over
        self.game_over_menu = GameOverMenu(restart_func=self.restart_game)

        # 2. Pasamos el menú al jugador para que lo active al morir
        self.player = PlayerShip(game_over_menu=self.game_over_menu)

        self.environment = AsteroidManager(count=150, radius=350)
        self.space_dust = SpaceDustManager(player=self.player, count=300, radius=60)

        self.pause_menu = PauseMenu()
        self.pause_controller = PauseController(self.pause_menu)

    def restart_game(self):
        """Función encargada de resetear todo el estado del juego de forma limpia"""
        self.player.reset_ship()  # Resetea posición y HUD de la nave
        self.environment.clear_and_respawn()  # Regenera los asteroides en nuevas posiciones
        self.space_dust.reset_particles()  # Reubica el polvo cósmico alrededor del origen

        self.game_over_menu.enabled = False
        mouse.locked = True
        application.paused = False

    def run(self):
        self.app.run()


if __name__ == '__main__':
    game = GameApp()
    game.run()