""" General global settings for configuring the game """

PIZZA_NUM = 10
PIZZA_RADIUS_RANGE = (10, 50)
SNAKE_INITIAL_LENGTH = 20
SNAKE_SPEED = 4
SNAKE_TURN_RATE = 6
SNAKE_RADIUS = 10
SNAKE_DIAMETER = 2 * SNAKE_RADIUS
SNAKE_DIAMETER_SQ = SNAKE_DIAMETER * SNAKE_DIAMETER
PLAY_AREA = (600, 400)
MAX_PLAYERS = 8
SNAKE_COLOR_ROT = 0.4
PLAYER_COLOR_GRADIENT_SIZE = 16
PLAYER_INIT_STATE = [(PLAY_AREA[0] // 2, PLAY_AREA[1] - SNAKE_DIAMETER, 270),
                     (PLAY_AREA[0] // 2, SNAKE_DIAMETER, 90),
                     (SNAKE_DIAMETER, PLAY_AREA[1] // 2, 0),
                     (PLAY_AREA[0] - SNAKE_DIAMETER, PLAY_AREA[1] // 2, 180),
                     (SNAKE_DIAMETER, SNAKE_DIAMETER, 45),
                     (SNAKE_DIAMETER, PLAY_AREA[1] - SNAKE_DIAMETER, 315),
                     (PLAY_AREA[0] - SNAKE_DIAMETER, SNAKE_DIAMETER, 135),
                     (PLAY_AREA[0] - SNAKE_DIAMETER,
                      PLAY_AREA[1] - SNAKE_DIAMETER, 225)]
