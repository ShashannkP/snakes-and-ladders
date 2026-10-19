"""Run with python -m snakes_ladders.main."""

import pygame

from snakes_ladders.ui.setup_screen import SetupScreen


def main():
    pygame.init()
    try:
        surface = pygame.display.set_mode((1280, 720))
        pygame.display.set_caption("Snakes and Ladders")
        pygame.key.start_text_input()
        screen = SetupScreen()
        clock = pygame.time.Clock()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    screen.handle_event(event)
            screen.draw(surface)
            pygame.display.flip()
            clock.tick(60)
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
