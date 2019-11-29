#""" Multiplayer Pizza Snake / Worm Game """
#from typing import List --- 何のため？ - maybe reference for it https://qiita.com/icoxfog417/items/c17eb042f4735b7924a3
#import pygame as P
import pyxel as P
from pyxel import btn,btnp,quit

#import settings # under 30 lines
from game_inputs import InputHandler, InputState # about 70 lines
from players import Player, Human, SimpleAI # about 80 lines

#from game_state import Snake, GameState # about 300 lines
import networking # about 620 lines

from collections import deque
import math
import random

# General global settings for configuring the game
PIZZA_RADIUS_RANGE = (2,10)#(10, 50)
SNAKE_INITIAL_LENGTH = 4 #20
SNAKE_SPEED = 0.8 # 4
SNAKE_RADIUS = 2 # 10
SNAKE_DIAMETER = 2 * SNAKE_RADIUS
SNAKE_DIAMETER_SQ = SNAKE_DIAMETER **2
SNAKE_TURN_RATE = 6
PIZZA_NUM = 10

PLAY_AREA = (240, 160) # 20% smaller than original

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

class Game:
    def __init__(self):
        P.init(240,160,scale=2)# pygame >> pyxel
        self.game_state = GameState()
        self.ongame=1
        self.frame_num= 0
        self.players = []
        self.inputs = InputHandler()
        self.server = networking.TCPServer(networking.DEFAULT_PORT)
        self.server.start_listening()
        self.add_player(Human('P1', self.inputs, (P.KEY_LEFT, P.KEY_RIGHT)))#(P.K_LEFT, P.K_RIGHT)
        for i in range(3):self.add_player(SimpleAI('Bot%d'%i))
        #run(self.update, self.draw)

    def add_player(self, player):#""" Add a player to the game. """
        snake_id = len(self.game_state.snakes)
        if snake_id < MAX_PLAYERS:
            snake = Snake(PLAYER_INIT_STATE[snake_id])
            player.bind_snake(snake_id)
            self.game_state.snakes.append(snake)
            self.players.append(player)

    def handle_events(self):#"""Main event pump"""
        if btnp(P.KEY_Q):quit()#  # If user clicked closeFlag that we are done so we exit this loop
#        else:self.inputs.handle_event(event)

    def update(self):#""" Game logic update """
        for snake, player in zip(self.game_state.snakes, self.players):
            snake.update(self.frame_num, player.get_snake_input())
            self.game_state.collisions.add_parts(snake.new_parts)
            self.game_state.collisions.remove_parts(snake.removed_parts)
            self.game_state.pizza_manager.eat(snake)
        self.game_state.collisions.handle_collisions(self.game_state.snakes)

        for snake_id, snake in enumerate(self.game_state.snakes):
            if len(snake.parts) > 0 and not snake.alive:
                self.game_state.collisions.remove_parts(snake.parts)
                snake.clear()
                # TODO remove? Game end logic and scoring?
                snake.reset(PLAYER_INIT_STATE[snake_id])

        self.game_state.pizza_manager.update_pizzas()
        self.update_state_to_players()
        self.frame_num += 1

    def update_state_to_players(self):#""" Send all tick changes to all players.This tells AI and remote players the game state"""
        # TODO move to networking code
        new_connections = self.server.get_new_connections()
        if len(new_connections) > 0:
            game_msg = networking.GameStateUpdateMessage(self.game_state.pizzas, [])
            for snake_id, snake in enumerate(self.game_state.snakes):game_msg.buffer_snake_update(snake_id, snake.dir, snake.parts,0)
            msg_data = game_msg.encode()
            for conn in new_connections: conn.send_bytes(msg_data)

        if len(self.server.connections) > 0:
            game_msg = networking.GameStateUpdateMessage(
                self.game_state.pizza_manager.new_pizzas,
                self.game_state.pizza_manager.removed_pizzas)
            for snake_id, snake in enumerate(self.game_state.snakes):game_msg.buffer_snake_update(snake_id, snake.dir, snake.new_parts, len(snake.removed_parts))
            self.server.broadcast(game_msg)

        self.server.connections += new_connections

        for conn in self.server.connections:
            players_to_register = conn.get_new_players()
            for player in players_to_register:self.add_player(player)
            conn.add_registered_players(players_to_register)

        # TODO clean closed connections

    def draw_game(self, game_state):
        P.cls(1)
        for pizza in game_state.pizzas:
            P.circ(pizza.x, pizza.y,pizza.radius,4)# color 5 is temporarily
            P.circ(pizza.x, pizza.y,max(1,pizza.radius - 1),10)# color 6 is temporarily
            P.circ(pizza.x, pizza.y,max(1,pizza.radius - 2),9)# color 7 is temporarily
        for player_idx, snake in enumerate(game_state.snakes):
            def player_color_index(pidx, value):
                size = PLAYER_COLOR_GRADIENT_SIZE
                return 1 + pidx * size + value % size
            POS=snake.new_parts[0]
            r=SNAKE_RADIUS
            c = 11 if player_idx<1 else 8
            for part in snake.new_parts:P.circ(part[0], part[1],r, c)# color 5 is temporarily
            snake.new_parts.clear()
            for part in snake.removed_parts:P.circ(part[0], part[1],r,c)# color 5 is temporarily
            snake.removed_parts.clear()
            if len(snake.parts) > 0:
                part = snake.parts[0]
                P.circ(part[0], part[1],r,c)
            P.text(POS[0],POS[1]-1,str(player_idx),0)# player id shadow
            P.text(POS[0]-1,POS[1]-2,str(player_idx),7 if player_idx<1 else 10)# player id draw

    def run(self):# """ Main Program Loop """
        while self.ongame:
            P.cls
            self.handle_events()

            for player in self.players:player.act()
            self.update()
            self.draw_game(self.game_state)
            #P.display.flip()
            P.flip()
            InputState.clear_tick_states()
            self.game_state.pizza_manager.clear_tick_changes()
#            self.clock.tick(60)# --- Limit to 60 frames per second
        P.display.quit()
        self.server.shutdown()


class Snake:
    """ Contains the state of a single snake object """
    def __init__(self, init_state):
        self.length = SNAKE_INITIAL_LENGTH
        self.parts = deque()
        self.pos= (init_state[0], init_state[1])
        self.dir= init_state[2]  # in Degrees
        self.new_parts = []
        self.removed_parts = []
        self.alive: bool = 1
        self.calc_movement_vector()

    def head(self):return self.parts[-1]#""" return the front of the snake """
    def kill(self):self.alive = 0#""" Mark snake dead """
    def clear(self):#""" Mark all snake parts as removed, clear all parts """
        self.removed_parts += self.parts
        self.parts = deque()
        self.length = 0
    def reset(self, init_state):#""" Reset snake to initial position and length, mark it alive """
        self.length = SNAKE_INITIAL_LENGTH
        self.pos = (init_state[0], init_state[1])
        self.dir = init_state[2]
        self.alive = 1
    def grow(self, food):self.length += food#""" Grow the snake with 'food' amount """
    def calc_movement_vector(self):# """ Calculate movement vector from direction and velocity """
        rad = math.radians(self.dir)
        speed = SNAKE_SPEED
        return (speed * math.cos(rad), speed * math.sin(rad))
    def crate_new_head(self, frame_num):self.add_part((int(self.pos[0]), int(self.pos[1]), frame_num))#""" Create a new head part at snake position """
    def add_part(self, part):# """ Add a single part to the snake head """
        self.parts.append(part)
        self.new_parts.append(part)
    def add_parts(self, parts):# """ Add multiple parts to the snake head """
        for part in parts:self.add_part(part)
    def remove_part(self):# """ Remove one part from the tail of the snake """
        rem = self.parts.popleft()
        self.removed_parts.append(rem)
    def remove_n_parts(self, num):# """ Remove multiple parts from the snake tail """
        for _ in range(num):self.remove_part()
    def update(self, frame_num, turn_input):
        """ Apply inputs and update snake head and tail. Changed parts
            can be queried in new_parts and removed_parts """
        self.dir += turn_input
        vel = self.calc_movement_vector()
        self.pos = (self.pos[0] + vel[0], self.pos[1] + vel[1])

        self.crate_new_head(frame_num)
        if len(self.parts) > self.length:
            self.remove_part()

    def is_own_head(self, colliding_part):
        """ Check if colliding part is part of snake's own head to
            avoid self collisions """
        for i, part in enumerate(reversed(self.parts)):
            if part == colliding_part:
                return 1
            if i * SNAKE_SPEED > SNAKE_DIAMETER:
                return 0
        return 0


class Pizza:
    """ Contain the state of one pizza object """
    def __init__(self, x, y, radius, pizza_id):
        self.x = x
        self.y = y
        self.radius = radius
        self.pizza_id = pizza_id
        self.still_good = 1

    def is_close(self, pos, check_radius):
        """ Hit check for the pizza and a collider at position 'pos' with
            radius 'check_radius' """
        dx = pos[0] - self.x
        dy = pos[1] - self.y
        dist = check_radius + self.radius
        if dx * dx + dy * dy < dist * dist:
            return 1
        return 0

    def mark_eaten(self):
        """ Marks pizza as eaten.
            Pizza will be removed at next manager update. """
        self.still_good = 0


class CollisionManager:
    """ Handles all snake collisions.
        Contains a collision grid where grid size is the snake body diameter.
        Snake to snake colisions need to then check only the current and
        boundary grid cells to find all possible collisions. """
    def __init__(self):
        self.dim = (1 + PLAY_AREA[0] // SNAKE_DIAMETER,
                    1 + PLAY_AREA[1] // SNAKE_DIAMETER)
        self.collision_grid: List[List[SnakePart]] = [
            [] for i in range(self.dim[0] * self.dim[1])
        ]

    def __grid_index(self, grid_x, grid_y) -> int:
        """ return grid index """
        return grid_x + self.dim[0] * grid_y

    def __collide_cell(self, grid_idx,snake_head):
        """ Check snake collision inside a single collision grid cell. """
        def part_collide(part1, part2):
            """ Check snake part to snake part collision.
                return 1 on collision. """
            dx = part1[0] - part2[0]
            dy = part1[1] - part2[1]
            return dx * dx + dy * dy < SNAKE_DIAMETER_SQ

        return [
            part for part in self.collision_grid[grid_idx]
            if part_collide(part, snake_head)
        ]

    def get_colliders(self, snake_head):
        """ Return all possible snake to snake collision parts
            from current and boundary collision grid cells """
        ix = snake_head[0] // SNAKE_DIAMETER
        iy = snake_head[1] // SNAKE_DIAMETER
        collisions = []
        y_min_range = max(iy - 1, 0)
        y_max_range = min(iy + 2, self.dim[1])
        for i in range(max(ix - 1, 0), min(ix + 2, self.dim[0])):
            for j in range(y_min_range, y_max_range): collisions += self.__collide_cell(self.__grid_index(i, j), snake_head)
        return collisions

    def add_parts(self, new_parts):# """ Update the collision grid with several Snake parts """
        for snake_head in new_parts:
            ix = snake_head[0] // SNAKE_DIAMETER
            iy = snake_head[1] // SNAKE_DIAMETER
            index = self.__grid_index(ix, iy)
            if 0 <= index < len(self.collision_grid):  self.collision_grid[index].append(snake_head)

    def remove_parts(self, removed_parts):#""" Remove multiple parts from the collision grid """
        for snake_tail in removed_parts:
            ix = snake_tail[0] // SNAKE_DIAMETER
            iy = snake_tail[1] // SNAKE_DIAMETER
            index = self.__grid_index(ix, iy)
            if 0 <= index < len(self.collision_grid):
                self.collision_grid[index].remove(snake_tail)

    def handle_collisions(self, snakes):
        """ Check all border and snake to snake collisions.
            Mark snakes as 'killed' if collisions happen. """
        def check_border_collisions(snake: Snake):
            """ Check snake border collision """
            head = snake.head()
            radius = SNAKE_RADIUS
            if not radius <= head[0] < PLAY_AREA[0] - radius:return 1
            if not radius <= head[1] < PLAY_AREA[1] - radius:return 1
            return 0

        def check_snake_collisions(snake: Snake):
            """ Check snake to snake collisions """
            for col in self.get_colliders(snake.head()):
                if not snake.is_own_head(col): return 1
            return 0

        for snake in snakes:
            if check_border_collisions(snake):snake.kill()
            elif check_snake_collisions(snake):snake.kill()

class PizzaManager:# """ Pizza generator and eating logic """
    def __init__(self, pizzas):
        self.next_pizza_id = 0
        self.pizzas = pizzas
        self.new_pizzas = []
        self.removed_pizzas = []

    def generate_pizza(self):# """ Generate a new pizza at random location """
        radius = random.randrange(PIZZA_RADIUS_RANGE[0], PIZZA_RADIUS_RANGE[1] + 1)
        x = radius + random.randrange(PLAY_AREA[0] - 2 * radius)
        y = radius + random.randrange(PLAY_AREA[1] - 2 * radius)
        self.next_pizza_id += 1
        pizza = Pizza(x, y, radius, self.next_pizza_id)
        self.new_pizzas.append(pizza)
        self.pizzas.append(pizza)

    def update_pizzas(self):# """ Remove eaten pizzas, bake new ones to replace them """
        for pizza in list(self.pizzas):
            if not pizza.still_good:
                self.removed_pizzas.append(pizza.pizza_id)
                self.pizzas.remove(pizza)

        while len(self.pizzas) < PIZZA_NUM: self.generate_pizza()

    def eat(self, snake: Snake):
        """ Check if a snake is close enough to eat some pizzas.
            Fill the belly of the snake with eaten pizzas and make
            it grow. Multiple snakes can eat the same pizza before
            the eaten pizzas are removed at call to 'update'."""
        position = snake.head()
        for pizza in self.pizzas:
            if pizza.is_close(position, SNAKE_RADIUS):
                snake.grow(pizza.radius)
                pizza.mark_eaten()

    def clear_tick_changes(self):# """ Clear what pizzas were created or remove this frame """
        self.new_pizzas.clear()
        self.removed_pizzas.clear()

class GameState:#   """ A complete collections of the game state. Contains the state of Pizzas and Snakes """
    def __init__(self):
        self.collisions = CollisionManager()
        self.snakes = []
        self.pizzas = []

        # TODO move to server game logic
        self.pizza_manager = PizzaManager(self.pizzas)

    def remove_pizza(self, pizza: Pizza):
        self.pizzas.remove(pizza)

    def remove_pizzas(self, removed_pizzas):#""" Remove all provided pizza_ids from active pizzas """
        for pizza_id in removed_pizzas:
            for pizza in self.pizzas:
                if pizza.pizza_id == pizza_id:
                    self.pizzas.remove(pizza)
                    break


GAME = Game()
GAME.run()