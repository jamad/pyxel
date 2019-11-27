#""" Multiplayer Pizza Snake / Worm Game """
#from typing import List
import pygame

from game_inputs import InputHandler, InputState
from graphics import GameRenderer
#import settings
from game_state import Snake, GameState
import networking
from players import Player, Human, SimpleAI


class Game:
    def __init__(self):
        (w, h) = (300, 200) # window size
        pygame.init()
        pygame.display.set_mode((w, h)) # set screen
        
        # Create the window, saving it to a variable.
#        surface = pygame.display.set_mode((350, 250), pygame.RESIZABLE)
#        pygame.display.set_caption("Example resizable window")

        self.game_state = GameState()
        self.done=0
        self.frame_num= 0
        self.clock = pygame.time.Clock()
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
        for event in pygame.event.get():  # User did something
            if event.type == pygame.QUIT:  # If user clicked close
                self.done = True  # Flag that we are done so we exit this loop
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
            game_msg = networking.GameStateUpdateMessage(
                self.game_state.pizzas, [])
            for snake_id, snake in enumerate(self.game_state.snakes):
                game_msg.buffer_snake_update(snake_id, snake.dir, snake.parts,
                                             0)
            msg_data = game_msg.encode()
            for conn in new_connections:
                conn.send_bytes(msg_data)

        if len(self.server.connections) > 0:
            game_msg = networking.GameStateUpdateMessage(
                self.game_state.pizza_manager.new_pizzas,
                self.game_state.pizza_manager.removed_pizzas)
            for snake_id, snake in enumerate(self.game_state.snakes):
                game_msg.buffer_snake_update(snake_id, snake.dir,
                                             snake.new_parts,
                                             len(snake.removed_parts))
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
        while not self.done:
            self.handle_events()

            for player in self.players:player.act()
            self.update()
            self.renderer.draw_game(self.game_state)
            pygame.display.flip()
            InputState.clear_tick_states()
            self.game_state.pizza_manager.clear_tick_changes()
            self.clock.tick(60)# --- Limit to 60 frames per second
        pygame.display.quit()
        self.server.shutdown()

GAME = Game()
GAME.add_player(Human('P1', GAME.inputs, (pygame.K_LEFT, pygame.K_RIGHT)))
GAME.add_player(Human('P2', GAME.inputs, (pygame.K_a, pygame.K_d)))
# GAME.add_player(Human('P3', GAME.inputs, (pygame.K_v, pygame.K_n)))
# GAME.add_player(Human('P4', GAME.inputs, (pygame.K_KP4, pygame.K_KP6)))
# GAME.add_player(Human('P5', GAME.inputs, (pygame.K_i, pygame.K_p)))
GAME.add_player(SimpleAI('Bot1'))
# GAME.add_player(SimpleAI('Bot2'))
# GAME.add_player(SimpleAI('Bot3'))

GAME.run()
