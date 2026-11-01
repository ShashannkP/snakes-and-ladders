"""Run with python -m snakes_ladders.main."""

import logging

import pygame
from time import perf_counter

from snakes_ladders.controller.game_controller import GameController
from snakes_ladders.ui.game_screen import GameScreen
from snakes_ladders.ui.result_screen import ResultScreen
from snakes_ladders.ui.setup_screen import SetupScreen
from snakes_ladders.ui.viewport import LOGICAL_SIZE, logical_event, present, viewport_rect
from snakes_ladders.ui.animation import TARGET_FPS


def main():
    pygame.init()
    try:
        surface = pygame.display.set_mode(LOGICAL_SIZE, pygame.RESIZABLE)
        canvas = pygame.Surface(LOGICAL_SIZE)
        pygame.display.set_caption("Snakes and Ladders")
        pygame.key.start_text_input()
        controller = GameController()

        def make_setup():
            return SetupScreen(
                on_start=controller.start_new_game,
                on_resume=controller.on_resume_requested,
                can_resume=controller.can_resume,
                controller=controller,
            )

        screens = {
            "setup": make_setup(),
            "game": GameScreen(controller),
            "result": ResultScreen(controller),
        }
        clock = pygame.time.Clock()
        force_redraw = True
        while controller.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    controller.running = False
                elif event.type == pygame.VIDEORESIZE:
                    size = (max(LOGICAL_SIZE[0], event.w), max(LOGICAL_SIZE[1], event.h))
                    surface = pygame.display.set_mode(size, pygame.RESIZABLE)
                    force_redraw = True
                elif event.type == pygame.WINDOWEXPOSED:
                    force_redraw = True
                else:
                    event = logical_event(event, viewport_rect(surface.get_size()))
                    if event is None:
                        continue
                    previous_screen = controller.screen
                    screens[controller.screen].handle_event(event)
                    if previous_screen != "setup" and controller.screen == "setup":
                        screens["setup"] = make_setup()
            if controller.screen == "game":
                screens["game"].update(clock.get_time() / 1000)
            dirty = screens[controller.screen].draw(canvas)
            present(canvas, surface, None if force_redraw else dirty)
            force_redraw = False
            pygame.display.flip()
            if controller.screen == "game":
                screens["game"].record_frame(perf_counter())
            clock.tick(TARGET_FPS)
    finally:
        pygame.quit()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
