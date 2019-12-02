""" Manages drawing of the game """
from typing import List, Tuple, Any
import colorsys
import random
import pygame
import settings
from game_state import GameState, Snake, Pizza

Color = Tuple[int, int, int]


class Colors:
    """ Basic colors """
    CLEAR_COLOR = (240, 240, 240)
    BLACK = (0, 0, 0)
    DARK_YELLOW = (200, 200, 0)
    HOT_PINK = (220, 0, 127)
    PINK = (255, 192, 203)
    FUCHSIA = (255, 130, 255)
    LIME = (0, 255, 0)
    P1_GREEN = (100, 255, 10)
    P1_YELLOW = (255, 255, 10)
    P2_RED = (255, 10, 10)
    P2_ORANGE = (255, 200, 10)
    P3_BLUE = (10, 10, 255)
    P3_CYAN = (10, 200, 200)
    P4_VIOLET = (150, 50, 255)
    P4_BLUE = (50, 50, 100)
    MINT = (170, 255, 195)
    GOLD = (249, 166, 2)
    ROYAL = (250, 218, 94)


PLAYER_COLORS = [(Colors.P1_GREEN, Colors.P1_YELLOW),
                 (Colors.P2_RED, Colors.P2_ORANGE),
                 (Colors.P3_BLUE, Colors.P3_CYAN),
                 (Colors.P4_VIOLET, Colors.P4_BLUE),
                 (Colors.HOT_PINK, Colors.PINK),
                 (Colors.BLACK, Colors.DARK_YELLOW),
                 (Colors.ROYAL, Colors.GOLD), (Colors.FUCHSIA, Colors.MINT)]


def generate_gradient(colors: Tuple[Color, Color], steps: int) -> List[Color]:
    """ Generate a color gradient with 2*steps for two input colors """
    def lerp(val1: int, val2: int, scale: float) -> int:
        """ interpolate between values val1 and val2 with scale [0, 1] """
        return int(val1 + (val2 - val1) * scale)

    palette = []
    c1_red, c1_green, c1_blue = colors[0]
    c2_red, c2_green, c2_blue = colors[1]

    for i in range(steps):
        scale = i / steps
        red = lerp(c1_red, c2_red, scale)
        green = lerp(c1_green, c2_green, scale)
        blue = lerp(c1_blue, c2_blue, scale)
        palette.append((red, green, blue))
    for i in range(steps):
        scale = i / steps
        red = lerp(c2_red, c1_red, scale)
        green = lerp(c2_green, c1_green, scale)
        blue = lerp(c2_blue, c1_blue, scale)
        palette.append((red, green, blue))
    return palette


class SnakeGraphics:
    """ Implements Snake drawing with 8-bit texture
        and palette color rotations """
    def __init__(self) -> None:
        def hsl_color_pair(seed: float,
                           player_index: int) -> Tuple[Color, Color]:
            """ Generate a hsl color with unique hue for each player """
            def hsl_color(hue: float, saturation: float,
                          lightness: float) -> Color:
                """ Convert hsl to rgb """
                hue = hue - 1 if hue > 1 else hue
                red, green, blue = (
                    int(256 * i)
                    for i in colorsys.hls_to_rgb(hue, lightness, saturation))
                return (red, green, blue)

            pidx = player_index / settings.MAX_PLAYERS
            return (hsl_color(seed + pidx, 0.99,
                              0.5), hsl_color(seed + pidx, 0.7, 0.3))

        self.image = pygame.Surface(settings.PLAY_AREA, 0, 8)
        self.image.fill((0, 0, 0))
        self.image.set_colorkey((0, 0, 0))
        self.gradients = [
            generate_gradient(
                PLAYER_COLORS[index] if index < len(PLAYER_COLORS) else
                hsl_color_pair(random.random(), index),
                settings.PLAYER_COLOR_GRADIENT_SIZE // 2)
            for index in range(settings.MAX_PLAYERS)
        ]

        assert len(self.gradients) == settings.MAX_PLAYERS
        self.palette = [(0, 0, 0)] * 256
        self.rotate: float = 0.0
        self.update_palette()

    def rotate_palette(self) -> None:
        """ Rotate the color gradients for each player to create animation """
        self.rotate += settings.SNAKE_COLOR_ROT
        rot = int(self.rotate)
        size = settings.PLAYER_COLOR_GRADIENT_SIZE
        for pidx in range(settings.MAX_PLAYERS):
            base = 1 + pidx * size
            for i in range(size):
                self.palette[base + i] = self.gradients[pidx][(i + rot) % size]

    def update_palette(self) -> None:
        """ Animate color palette and apply it to the snake texture """
        self.rotate_palette()
        self.image.set_palette(self.palette)

    def draw_snake(self, player_idx: int, snake: Snake) -> None:
        """ Apply updates to the snake texture """
        def player_color_index(pidx: int, value: int) -> int:
            """ return player color index in the shared palette """
            size = settings.PLAYER_COLOR_GRADIENT_SIZE
            return 1 + pidx * size + value % size

        for part in snake.new_parts:
            index = player_color_index(player_idx, part[2])
            pygame.draw.circle(self.image, index, [part[0], part[1]],
                               settings.SNAKE_RADIUS)
        snake.new_parts.clear()

        for part in snake.removed_parts:
            pygame.draw.circle(self.image, 0, [part[0], part[1]],
                               settings.SNAKE_RADIUS)
        snake.removed_parts.clear()

        # Replace last part as it was partially removed,
        # clearing could be implemented better with masking
        if len(snake.parts) > 0:
            part = snake.parts[0]
            corr_col_index = player_color_index(player_idx, part[2])
            pygame.draw.circle(self.image, corr_col_index, [part[0], part[1]],
                               settings.SNAKE_RADIUS)

    def draw_snakes(self, screen: Any, snakes: List[Snake]) -> None:
        """ Draw all provided snake objects and rotate palette """
        for snake_id, snake in enumerate(snakes):
            self.draw_snake(snake_id, snake)
        self.update_palette()
        screen.blit(self.image, (0, 0))


class GameRenderer:
    """ Handles game state rendering """
    def __init__(self) -> None:
        self.snake_graphics = SnakeGraphics()
        self.screen = pygame.display.set_mode(settings.PLAY_AREA)

    def draw_pizza(self, pizza: Pizza) -> None:
        """ Draw a pizza object to the screen """
        pygame.draw.circle(self.screen, (180, 160, 10), [pizza.x, pizza.y],
                           pizza.radius)
        pygame.draw.circle(self.screen, (255, 210, 10), [pizza.x, pizza.y],
                           pizza.radius - 3)
        pygame.draw.circle(self.screen, (255, 100, 10), [pizza.x, pizza.y],
                           pizza.radius - 6)

    def draw_pizzas(self, pizzas: List[Pizza]) -> None:
        """ Draw all pizzas in a list """
        for pizza in pizzas:
            self.draw_pizza(pizza)

    def draw_game(self, game_state: GameState) -> None:
        """ Draw game """
        self.screen.fill(Colors.CLEAR_COLOR)
        self.draw_pizzas(game_state.pizzas)
        self.snake_graphics.draw_snakes(self.screen, game_state.snakes)
