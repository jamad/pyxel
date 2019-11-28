#""" Multiplayer Pizza Snake / Worm Game """
#from typing import List --- 何のため？ - maybe reference for it https://qiita.com/icoxfog417/items/c17eb042f4735b7924a3
import pygame as P
import pyxel as P
from pyxel import btn,btnp,quit

import settings # under 30 lines
from game_inputs import InputHandler, InputState # about 70 lines
from players import Player, Human, SimpleAI # about 80 lines
#from graphics import GameRenderer # about 170 lines

from game_state import Snake, GameState # about 300 lines
import networking # about 620 lines

class Game:
    def __init__(self):
        P.init(240,160,scale=2)# pygame >> pyxel
        # P.display.set_mode((300, 200)) # set screen size - but renderer overrode it...
        self.game_state = GameState()
        self.ongame=1
        self.frame_num= 0
#        self.clock = P.time.Clock()
        self.players = []
        self.inputs = InputHandler()
#        self.renderer = GameRenderer()
        self.server = networking.TCPServer(networking.DEFAULT_PORT)
        self.server.start_listening()

        self.add_player(Human('P1', self.inputs, (P.KEY_LEFT, P.KEY_RIGHT)))#(P.K_LEFT, P.K_RIGHT)
        #self.add_player(Human('P2', self.inputs, (P.KEY_A, P.KEY_D)))
        #self.add_player(Human('P3', self.inputs, (P.KEY_V, P.KEY_N)))
        #self.add_player(Human('P4', self.inputs, (P.KEY_KP_4, P.KEY_KP_6)))
        #self.add_player(Human('P5', self.inputs, (P.KEY_I, P.KEY_P)))

        for i in range(3):self.add_player(SimpleAI('Bot%d'%i))

        #run(self.update, self.draw)

    def add_player(self, player):#""" Add a player to the game. """
        snake_id = len(self.game_state.snakes)
        if snake_id < settings.MAX_PLAYERS:
            snake = Snake(settings.PLAYER_INIT_STATE[snake_id])
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
                snake.reset(settings.PLAYER_INIT_STATE[snake_id])

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
                size = settings.PLAYER_COLOR_GRADIENT_SIZE
                return 1 + pidx * size + value % size
            POS=snake.new_parts[0]
            r=settings.SNAKE_RADIUS
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

GAME = Game()
GAME.run()