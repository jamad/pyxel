#""" Multiplayer Pizza Snake / Worm Game """
#from typing import List --- 何のため？ - maybe reference for it https://qiita.com/icoxfog417/items/c17eb042f4735b7924a3
import pygame as P

import settings # under 30 lines
from game_inputs import InputHandler, InputState # about 70 lines
from players import Player, Human, SimpleAI # about 80 lines
from graphics import GameRenderer # about 170 lines

from game_state import Snake, GameState # about 300 lines
import networking # about 620 lines

class Game:
    def __init__(self):
        P.init()
        # P.display.set_mode((300, 200)) # set screen size - but renderer overrode it...
        self.game_state = GameState()
        self.ongame=1
        self.frame_num= 0
        self.clock = P.time.Clock()
        self.players = []
        self.inputs = InputHandler()
        self.renderer = GameRenderer()
        self.server = networking.TCPServer(networking.DEFAULT_PORT)
        self.server.start_listening()

    def add_player(self, player: Player):#""" Add a player to the game. """
        snake_id = len(self.game_state.snakes)
        if snake_id < settings.MAX_PLAYERS:
            snake = Snake(settings.PLAYER_INIT_STATE[snake_id])
            player.bind_snake(snake_id)
            self.game_state.snakes.append(snake)
            self.players.append(player)

    def handle_events(self):#"""Main event pump"""
        for event in P.event.get():  # User did something
            if event.type == P.QUIT:self.ongame = 0  #  # If user clicked closeFlag that we are done so we exit this loop
            else:self.inputs.handle_event(event)

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
        # for player in self.players:
        #    for snake_id, snake in enumerate(self.game_state.snakes):
        #        player.send_update(snake_id, snake.new_parts,
        #                           len(snake.removed_parts))

    def run(self):# """ Main Program Loop """
        while self.ongame:
            self.handle_events()

            for player in self.players:player.act()
            self.update()
            self.renderer.draw_game(self.game_state)
            P.display.flip()
            InputState.clear_tick_states()
            self.game_state.pizza_manager.clear_tick_changes()
            self.clock.tick(60)# --- Limit to 60 frames per second
        P.display.quit()
        self.server.shutdown()

GAME = Game()
GAME.add_player(Human('P1', GAME.inputs, (P.K_LEFT, P.K_RIGHT)))
GAME.add_player(Human('P2', GAME.inputs, (P.K_a, P.K_d)))

GAME.add_player(Human('P3', GAME.inputs, (P.K_v, P.K_n)))
GAME.add_player(Human('P4', GAME.inputs, (P.K_KP4, P.K_KP6)))
GAME.add_player(Human('P5', GAME.inputs, (P.K_i, P.K_p)))

for i in range(3):GAME.add_player(SimpleAI('Bot%d'%i))

GAME.run()