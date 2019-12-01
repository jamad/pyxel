""" Client implementation """

from typing import List
import sys
#import pygame
import pyxel as P

from worm_game import InputHandler, InputState,TCPClient, DEFAULT_PORT,GameState, Snake,Human,Game # Player removed

class ClientApp:#  """ Client window that connects to the server """
    def __init__(self, host_addr, port = DEFAULT_PORT):
#        pygame.init()
        P.init(240,160,scale=2)# pygame >> pyxel
        self.GS = GameState()
        self.server_connection = TCPClient((host_addr, port))
        self.done = 0
        self.players = []
        self.inputs = InputHandler()

        self.draw_game = Game().draw_game
        # might not be needed when syncing to server
#        self.clock = pygame.time.Clock()

    def add_player(self, player):
        self.players.append(player)#""" Add a player to the game. """

#    def init_client_players(self):for local_id, player in enumerate(self.players):self.server_connection.register_player(local_id, player)#""" Register client players to the server """

    def handle_events(self):#""" Main event pump """
        ''' tmp disable
        for event in pygame.event.get():  # User did something
            if event.type == pygame.QUIT:  # If user clicked close
                self.done = 1  # Flag that we are done so we exit this loop
            else:self.inputs.handle_event(event)
        '''
    def update_game_state(self):#""" Apply server state updates to local state """
        for game_update in self.server_connection.received_game_updates:
            self.GS.remove_pizzas(game_update.removed_pizzas)
            self.GS.PZ += game_update.added_pizzas
            for sid, sdir, rem_count, parts in game_update.snake_updates:
                while sid >= len(self.GS.SN):self.GS.SN.append(Snake((0, 0, 0)))
                snake = self.GS.SN[sid]
                snake.dir = sdir
                snake.add_parts(parts)
                snake.remove_n_parts(rem_count)
        self.server_connection.received_game_updates.clear()

    def update_collision_structures(self):#""" Update collision structure for the use of AI player """
        for snake in self.GS.SN:
            self.GS.COLMGR.add_parts(snake.new_parts)
            self.GS.COLMGR.remove_parts(snake.removed_parts)

    def process_player_input(self):#""" Resolve player input and push it to server """
        for local_id, player in enumerate(self.players):
            player.act()
            self.server_connection.send_snake_input(local_id,player.get_snake_input())

    def run(self):#""" Main Program Loop """
#        self.init_client_players()
        for local_id, player in enumerate(self.players):
            self.server_connection.register_player(local_id, player)#""" Register client players to the server """

        while not self.done:
            self.handle_events()

            if not self.server_connection.receive_game_uptate():
                self.done = 1
                break

            self.update_game_state()
            self.update_collision_structures()
            self.process_player_input()
            self.draw_game(self.GS)
            #P.display.flip()
            P.flip()
            InputState.clear_tick_states()
            # Client rendering timed by server update messages
            # self.clock.tick(60)
        self.server_connection.shutdown()
#        pygame.display.quit()

HOST_ADDR = 1<len(sys.argv)and sys.argv[1] or  "127.0.0.1" #or'localhost'
print('HOST_ADDR:',HOST_ADDR)
GAME = ClientApp(HOST_ADDR)

# temp disable
#GAME.add_player(Human('R1', GAME.inputs, (pygame.K_LEFT, pygame.K_RIGHT)))
#GAME.add_player(Human('R2', GAME.inputs, (pygame.K_a, pygame.K_d)))
GAME.add_player(Human('P2', GAME.inputs, (P.KEY_A, P.KEY_D)))#(P.K_LEFT, P.K_RIGHT)

GAME.run()
