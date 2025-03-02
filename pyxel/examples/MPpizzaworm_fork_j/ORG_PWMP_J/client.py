""" Client implementation """

from typing import List
import sys
import pygame
from game_inputs import InputHandler, InputState
from networking import TCPClient, DEFAULT_PORT
from graphics import GameRenderer
from game_state import GameState, Snake
from players import Player, Human


class ClientApp:
    """ Client window that connects to the server """
    def __init__(self, host_addr: str, port: int = DEFAULT_PORT) -> None:
        pygame.init()
        self.game_state = GameState()
        self.server_connection = TCPClient((host_addr, port))
        self.done: bool = False
        self.players: List[Player] = []
        self.inputs = InputHandler()
        self.renderer = GameRenderer()
        # might not be needed when syncing to server
        self.clock = pygame.time.Clock()

    def add_player(self, player: Player) -> None:
        """ Add a player to the game. """
        self.players.append(player)

    def init_client_players(self) -> None:
        """ Register client players to the server """
        for local_id, player in enumerate(self.players):
            self.server_connection.register_player(local_id, player)

    def handle_events(self) -> None:
        """ Main event pump """
        for event in pygame.event.get():  # User did something
            if event.type == pygame.QUIT:  # If user clicked close
                self.done = True  # Flag that we are done so we exit this loop
            else:
                self.inputs.handle_event(event)

    def update_game_state(self) -> None:
        """ Apply server state updates to local state """
        for game_update in self.server_connection.received_game_updates:
            self.game_state.remove_pizzas(game_update.removed_pizzas)
            self.game_state.pizzas += game_update.added_pizzas
            for sid, sdir, rem_count, parts in game_update.snake_updates:
                while sid >= len(self.game_state.snakes):
                    self.game_state.snakes.append(Snake((0, 0, 0)))
                snake = self.game_state.snakes[sid]
                snake.dir = sdir
                snake.add_parts(parts)
                snake.remove_n_parts(rem_count)
        self.server_connection.received_game_updates.clear()

    def update_collision_structures(self) -> None:
        """ Update collision structure for the use of AI player """
        for snake in self.game_state.snakes:
            self.game_state.collisions.add_parts(snake.new_parts)
            self.game_state.collisions.remove_parts(snake.removed_parts)

    def process_player_input(self) -> None:
        """ Resolve player input and push it to server """
        for local_id, player in enumerate(self.players):
            player.act()
            self.server_connection.send_snake_input(local_id,
                                                    player.get_snake_input())

    def run(self) -> None:
        """ Main Program Loop """

        self.init_client_players()

        while not self.done:
            self.handle_events()

            if not self.server_connection.receive_game_uptate():
                self.done = True
                break

            self.update_game_state()
            self.update_collision_structures()

            self.process_player_input()

            self.renderer.draw_game(self.game_state)

            pygame.display.flip()
            InputState.clear_tick_states()

            # Client rendering timed by server update messages
            # self.clock.tick(60)
        self.server_connection.shutdown()
        pygame.display.quit()


HOST_ADDR = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
GAME = ClientApp(HOST_ADDR)
GAME.add_player(Human('R1', GAME.inputs, (pygame.K_LEFT, pygame.K_RIGHT)))
GAME.add_player(Human('R2', GAME.inputs, (pygame.K_a, pygame.K_d)))
GAME.run()
