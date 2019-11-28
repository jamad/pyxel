""" Manages drawing of the game """
import random
import settings
from game_state import GameState, Snake, Pizza
import pyxel as P

class SnakeGraphics:# """ Implements Snake drawing with 8-bit texture and palette color rotations """
    def __init__(self):
        self.palette = [(0, 0, 0)] * 256
        self.rotate = 0.0

    def draw_snakes(self, screen, snakes):
        for player_idx, snake in enumerate(snakes):
            def player_color_index(pidx, value):
                size = settings.PLAYER_COLOR_GRADIENT_SIZE
                return 1 + pidx * size + value % size
            POS=snake.new_parts[0]
            r=settings.SNAKE_RADIUS
            ci = player_color_index
            for part in snake.new_parts:P.circ(part[0], part[1],r, ci(player_idx, part[2])%16)# color 5 is temporarily
            snake.new_parts.clear()
            for part in snake.removed_parts:P.circ(part[0], part[1],r,ci(player_idx, part[2])%16)# color 5 is temporarily
            snake.removed_parts.clear()
            if len(snake.parts) > 0:
                part = snake.parts[0]
                #P.draw.circle(self.image, corr_col_index, [part[0], part[1]],r)
                P.circ(part[0], part[1],r, ci(player_idx, part[2])%16)# color 5 is temporarily

            P.text(POS[0],POS[1]-1,str(player_idx),0)# player id shadow
            P.text(POS[0]-1,POS[1]-2,str(player_idx),10 if player_idx<2 else 11)# player id draw

class GameRenderer:
    def __init__(self):self.snake_graphics = SnakeGraphics()

    def draw_game(self, game_state):
        P.cls(1)
        for pizza in game_state.pizzas:
            P.circ(pizza.x, pizza.y,pizza.radius,4)# color 5 is temporarily
            P.circ(pizza.x, pizza.y,max(1,pizza.radius - 1),10)# color 6 is temporarily
            P.circ(pizza.x, pizza.y,max(1,pizza.radius - 2),9)# color 7 is temporarily
        self.snake_graphics.draw_snakes(1, game_state.snakes)