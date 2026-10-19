"""Run with python -m snakes_ladders.main."""

import pygame

from snakes_ladders.controller.game_controller import GameController
from snakes_ladders.ui.game_screen import GameScreen
from snakes_ladders.ui.setup_screen import SetupScreen


def main():
    pygame.init()
    try:
        surface = pygame.display.set_mode((1280, 720))
        pygame.display.set_caption("Snakes and Ladders")
        pygame.key.start_text_input()
        controller = GameController()
        screens = {"setup": SetupScreen(controller.start_new_game), "game": GameScreen(controller)}
        clock = pygame.time.Clock()
        while controller.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    controller.running = False
                else:
                    screens[controller.screen].handle_event(event)
            screens[controller.screen].draw(surface)
            pygame.display.flip()
            clock.tick(60)
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
