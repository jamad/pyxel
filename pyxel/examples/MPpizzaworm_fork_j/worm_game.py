""" Types for player interaction """
import random
import math

import socket
import threading
import struct
from enum import IntEnum, unique, auto
import pyxel as P
from pyxel import btn,btnp,quit

class Human():# Player -it had Player arg  """ Human player with controls """
    def __init__(self, name, im, kc):
        print('debug Human',name)
        self.name = name
        self.IN = InputState()
        
        if kc != (-1, -1):
            im.add_mapping(self.IN, kc[0], Action.TURN_LEFT)
            im.add_mapping(self.IN, kc[1], Action.TURN_RIGHT)

    def act(self):#""" Process the inputs to the controlled snake.AI players can process the game state in this function. """
        if self.IN.button_state[Action.TURN_LEFT]:self.snake_input = -S_TURN
        elif self.IN.button_state[Action.TURN_RIGHT]:self.snake_input = S_TURN
        else:self.snake_input = 0

    def send_update(self, snake_id, added_parts,num_RMVED):
        del snake_id  # unused interface
        del added_parts  # unused interface
        del num_RMVED  # unused interface

class SimpleAI():# """ Simple AI to test interfaces """ - it had Player
    def __init__(self, name):
        self.num = 0
        self.name = name
    def act(self):self.snake_input = random.randrange(-5, 6)# """ Generate input """
    def send_update(self, snake_id, added_parts,num_RMVED):# """ Interface which remote and AI players can override to upkeep game state """
        del snake_id  # unused interface
        del added_parts  # unused interface
        del num_RMVED  # unused interface

##############################################  ALL NETWORKING for the following part  ##########################

DEFAULT_PORT = 45000

#@unique
#class NetMessage(IntEnum):#""" All game actions that buttons can be mapped to """
C_REGISTER_PLAYER = 1000
C_SNAKE_INPUT = 1001
S_PLAYER_REGISTERED = 2000
S_NEW_PLAYER = 2001
S_GAME_UPDATE = 3000
S_PLAYER_REFUSED = 8000

# Messages:

# Client to server:
#    REGISTER PLAYER
#    bytes       data
#    4           Message type
#    4           Message length
#    4           Client Specified Player ID
#    1           Player Name length
#    [1]*        Player Name characteer

#    SNAKE_INPUT:
#    4           Message type
#    4           Message length
#    4           Snake ID (Must match client's own snake ID)
#    4           Turn direction [-5, 5]

# Server to client:
#    PLAYER_REGISTERED (own information, answer to ADD_PLAYER)
#    4           Message type
#    4           Message length
#    4           Controlled Snake ID
#    4           Client Specified remote player ID

#    PLAYER_REFUSED (Game full etc.)
#    4           Message type
#    4           Message length
#    4           Client Specified remote player ID
#    [1]*        Error message

#    NEW_PLAYER (external players)
#    4           Message type
#    4           Message length
#    4           Snake ID
#    1           Player Name length
#    [1]*        Player Name

#    GAME_STATE_UPDATE:
#    4           Message Type
#    4           Message length
#    4           Pizzas Removed
#    4           Pizzas Added
#    [
#      4         Removed pizza ID
#    ] * removed pizzas
#    [
#      4         Pizza ID
#      4         X
#      4         Y
#      4         Radius
#    ] * added pizzas
#    4           Snakes count
#    [
#      4         Snake ID
#      4         Snake Direction in Degrees
#      4         Count of Removed Tail Parts
#      4         Added Part count
#      [
#        4       X
#        4       Y
#        4       PartID
#      ] * Parts
#    ] * Snakes

def int_to_bytes(x):return x.to_bytes(4, byteorder='big') #   """ Convert int to bytes """
def bytes_to_int(byte_array):return int.from_bytes(byte_array, byteorder='big')#    """ Bytes to int """
def pack_into(fmt, buffer, offset, *args):#    """ Pack data with struct.pack_into and given data format.        return the size of the output data with that format.        Use offset += pack_into() to update the offset for next call """
    struct.pack_into(fmt, buffer, offset, *args)
    return struct.calcsize(fmt)

HEADER_FORMAT = '>ii'
MSG_HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

class PlayerRegisterMessage():# """ Register client player to the server """ - it had Message before
    player_id_format = '>i'
    def __init__(self, index, player):
        self.msg_type = C_REGISTER_PLAYER
        self.index = index
        self.player = player

    def message_length(self):return (struct.calcsize(self.player_id_format) +  len(self.player.name) + 1)# """ return message lenght """
    def total_message_size(self):return self.message_length() + struct.calcsize(HEADER_FORMAT)
    def reserve_msg_buffer(self):  return bytearray(self.total_message_size())#""" Reserve big enough buffer for the message """
    def pack_header(self, buffer):return pack_into(HEADER_FORMAT, buffer, 0, self.msg_type,self.message_length())#""" Write message header, return offset """

    def encode(self):#""" encode message into bytes """
        msg_bytes = self.reserve_msg_buffer()
        offset = self.pack_header(msg_bytes)
        offset += pack_into(self.player_id_format, msg_bytes, offset, self.index)
        offset += pack_into('{}p'.format(len(self.player.name) + 1), msg_bytes, offset, self.player.name.encode())
        return bytes(msg_bytes)

    @staticmethod
    def decode(payload) :# """ Return decoded [remote_id, player_name] tuple """
        remote_id, = struct.unpack_from(PlayerRegisterMessage.player_id_format, payload, 0)
        offset=4
        str_len, = struct.unpack_from('B', payload, offset)#""" Unpack variable lenght str from message payload    """
        name = struct.unpack_from( '{}p'.format(str_len + 1), payload, offset)
        print('debug name:',name)
        return (remote_id, name)

class PlayerRegisteredMessage():# """ Register client player to the server """ - it had Message before
    register_format = '>ii'
    def __init__(self, snake_id, remote_id):
        self.msg_type = S_PLAYER_REGISTERED
        self.snake_id = snake_id
        self.remote_id = remote_id

    def message_length(self): return struct.calcsize(self.register_format)
    def total_message_size(self):return self.message_length() + struct.calcsize(HEADER_FORMAT)
    def reserve_msg_buffer(self):  return bytearray(self.total_message_size())#""" Reserve big enough buffer for the message """
    def pack_header(self, buffer):return pack_into(HEADER_FORMAT, buffer, 0, self.msg_type,self.message_length())#""" Write message header, return offset """

    def encode(self):# """ encode message into bytes """
        msg_bytes= self.reserve_msg_buffer()
        offset = self.pack_header(msg_bytes)
        offset += pack_into(self.register_format, msg_bytes, offset,   self.snake_id, self.remote_id)
        return bytes(msg_bytes)

    def decode(self, payload): self.snake_id, self.remote_id = struct.unpack_from( self.register_format, payload, 0)# """ Decode snake_id and remote_id from server message """

class SnakeInputMessage():# """ Client to server snake control message """ - it had Message before
    input_format = '>ii'
    def __init__(self, snake_id, snake_input):
        self.msg_type = C_SNAKE_INPUT
        self.snake_id = snake_id
        self.snake_input = snake_input

    def message_length(self):return struct.calcsize(self.input_format)#  """ Calculate message length """
    def total_message_size(self):return self.message_length() + struct.calcsize(HEADER_FORMAT)
    def pack_header(self, buffer):return pack_into(HEADER_FORMAT, buffer, 0, self.msg_type,self.message_length())#""" Write message header, return offset """
    def reserve_msg_buffer(self):  return bytearray(self.total_message_size())#""" Reserve big enough buffer for the message """
    
    def encode(self):# """ Encode message to bytes to be send """
        msg_bytes= self.reserve_msg_buffer()
        offset = self.pack_header(msg_bytes)
        offset += pack_into(self.input_format, msg_bytes, offset,  self.snake_id, self.snake_input)
        return bytes(msg_bytes)

    def decode(self, payload): self.snake_id, self.snake_input = struct.unpack_from( self.input_format, payload, 0)#""" Decode snake_id and input from message payload """

class GameStateUpdateMessage(): # """ Game state update message encoding and decoding  """ it had Message before
    pizza_count_format = '>ii'
    pizza_rem_id_format = '>i'
    pizza_added_format = '>4i'
    snake_count_format = '>i'
    snake_header_format = '>4i'
    snake_part_format = '>3i'

    def __init__(self, added_pizzas, removed_pizzas):
        self.msg_type = S_GAME_UPDATE
        self.added_pizzas = added_pizzas
        self.RMedPZ = removed_pizzas
        self.SN_UPD= []

    def message_length(self):#""" Calculate the message payload byte size (without header) """
        removed = len(self.RMedPZ)
        added = len(self.added_pizzas)
        msg_len = (struct.calcsize(self.pizza_count_format) + removed * struct.calcsize(self.pizza_rem_id_format) + added * struct.calcsize(self.pizza_added_format))
        msg_len += struct.calcsize(self.snake_count_format)
        for _, _, _, added_parts in self.SN_UPD: msg_len += ( struct.calcsize(self.snake_header_format) +  struct.calcsize(self.snake_part_format) * len(added_parts))
        return msg_len

    def encode_pizzas(self, msg_buffer, offset):# """ Encode pizzas into the message """
        offset += pack_into(self.pizza_count_format, msg_buffer, offset,    len(self.RMedPZ), len(self.added_pizzas))
        for id in self.RMedPZ:offset += pack_into(self.pizza_rem_id_format, msg_buffer, offset,id)
        for pizza in self.added_pizzas:offset += pack_into(self.pizza_added_format, msg_buffer, offset,pizza.id, pizza.x, pizza.y, pizza.r)
        return offset

    def encode_snakes(self, msg_buffer, offset):#""" Encode snakes into the message """
        offset += pack_into(self.snake_count_format, msg_buffer, offset,len(self.SN_UPD))
        for snake_id, snake_dir, rem_count, added, in self.SN_UPD:
            offset += pack_into(self.snake_header_format, msg_buffer, offset,snake_id, snake_dir, rem_count, len(added))
            for part in added:offset += pack_into(self.snake_part_format, msg_buffer, offset,part[0], part[1], part[2])
        return offset
    
    def total_message_size(self):return self.message_length() + struct.calcsize(HEADER_FORMAT)
    def reserve_msg_buffer(self):  return bytearray(self.total_message_size())#""" Reserve big enough buffer for the message """
    def pack_header(self, buffer):return pack_into(HEADER_FORMAT, buffer, 0, self.msg_type,self.message_length())#""" Write message header, return offset """

    def encode(self):# """ Encode a complete server to client message as bytes object """
        msg_bytes= self.reserve_msg_buffer()
        offset = self.pack_header(msg_bytes)
        offset = self.encode_pizzas(msg_bytes, offset)
        offset = self.encode_snakes(msg_bytes, offset)
        return bytes(msg_bytes)

    def decode_pizzas(self, payload: bytes, offset):# """ Decode pizza update from the server message payload """
        removed, added = struct.unpack_from(self.pizza_count_format, payload,offset)
        offset += struct.calcsize(self.pizza_count_format)
        removed_format_size = struct.calcsize(self.pizza_rem_id_format)
        for _ in range(removed):
            rem, = struct.unpack_from(self.pizza_rem_id_format, payload,offset)
            offset += removed_format_size
            self.RMedPZ.append(rem)

        pizza_format_size = struct.calcsize(self.pizza_added_format)
        for _ in range(added):
            id, pos_x, pos_y, r = struct.unpack_from(self.pizza_added_format, payload, offset)
            offset += pizza_format_size
            self.added_pizzas.append(Pizza(pos_x, pos_y, r, id))
        return offset

    def decode_snakes(self, payload: bytes, offset):#""" Decode snakes part of the server game state update """
        snake_count, = struct.unpack_from(self.snake_count_format, payload,offset)
        offset += struct.calcsize(self.snake_count_format)
        header_size = struct.calcsize(self.snake_header_format)
        part_size = struct.calcsize(self.snake_part_format)
        for _ in range(snake_count):
            snake_id, snake_dir, rem_count, added_count = struct.unpack_from(self.snake_header_format, payload, offset)
            offset += header_size
            added_parts = []
            for _ in range(added_count):
                pos_x, pos_y, part_id = struct.unpack_from(self.snake_part_format, payload, offset)
                offset += part_size
                added_parts.append((pos_x, pos_y, part_id))
            self.SN_UPD+=[(snake_id, snake_dir, rem_count, added_parts)]
        return offset

    def decode(self, payload):#""" Decode the gamestate update message payload.Generate 'added_pizzas', 'removed_pizzas' andsnake_updates lists. """
        offset = 0
        offset = self.decode_pizzas(payload, offset)
        offset = self.decode_snakes(payload, offset)

class RemotePlayer():#    """ Player whose inputs come over network """ - it had Player before
    def __init__(self, remote_id, name):
        super().__init__(name)
        self.remote_id = remote_id
        self.__last_snake_input = 0
        self.player_lock = threading.Lock()

    def set_remote_input(self, remote_input):#""" Safely store snake control input for this player """
        with self.player_lock:self.__last_snake_input = remote_input

    def act(self):
        with self.player_lock:self.snake_input = self.__last_snake_input #""" Copy remote input to interface """

    def send_update(self, snake_id, added_parts,num_RMVED):
        del snake_id  # unused interface
        del added_parts  # unused interface
        del num_RMVED  # unused interface

class ClientConnection:#    """ Socket encapsulation for sending message to clients """
    def __init__(self, client_socket: socket.socket, addr):
        print("Got connection from ", addr)
        self.alive = 1
        self.client_socket = client_socket
        self.send_lock = threading.Lock()

        self.message_callbacks = {C_REGISTER_PLAYER: self.parse_register_player,C_SNAKE_INPUT: self.parse_snake_input}
        self.__players= {}
        self.__new_players = []
        self.player_lock = threading.Lock()
        listerner_thread = threading.Thread(target=self.listen_messages,args=())
        listerner_thread.start()

    def register_new_player(self, player: RemotePlayer):#""" Add player to temporary list of new players to be joining the game """
        with self.player_lock:self.__new_players.append(player)

    def get_new_players(self):#""" Get a list of players that have not been mapped to game yet """
        with self.player_lock:
            players = list(self.__new_players)
            self.__new_players.clear()
            return players

    def add_registered_players(self, new_players):#""" Add a new list of remote players that have been      mapped to a snake """
        with self.player_lock:
            for player in new_players:
                if player.snake_id != -1:self.__players[player.snake_id] = player

        for player in new_players:
            if player.snake_id != -1:self.send_message(PlayerRegisteredMessage(player.snake_id, player.remote_id))
            else:pass# TO_DO   # self.send_message(PlayerRefusedMessage(player.remote_id,"Game Full"))
                
    def send_message(self, msg):self.send_bytes(msg.encode()) #        """ Send a network message to this client connection """

    def send_bytes(self, msg):#        """ Send encoded network message to this client connection """
        if self.alive:
            try:
                with self.send_lock:self.client_socket.sendall(msg)
            except socket.error:self.shutdown()

    def listen_messages(self):#""" Message listening loop for one client connection """
        try:
            while 1:self.receive_messages()
        except socket.error:self.shutdown()

    def parse_register_player(self, payload):#""" Reguest for a new player from client """
        remote_id, name = PlayerRegisterMessage.decode(payload)
        self.register_new_player(RemotePlayer(remote_id, name))

    def __set_input(self, snake_id, snake_input):#  """ Safely set the input for a player """
        with self.player_lock:
            if snake_id in self.__players:self.__players[snake_id].set_remote_input(snake_input)

    def parse_snake_input(self, payload):#   """ Received a snake input message from client """
        msg = SnakeInputMessage(0, 0)
        msg.decode(payload)
        self.__set_input(msg.snake_id, msg.snake_input)

    def send_game_update(self, game_msg: GameStateUpdateMessage):self.send_message(game_msg)#""" Send a snake update to a client """

    def receive_messages(self):#  """ Read one message from socket """
        header = self.client_socket.recv(struct.calcsize(HEADER_FORMAT))
        msg_type, msg_len = struct.unpack_from(HEADER_FORMAT, header, 0)
        payload = self.client_socket.recv(msg_len)
        self.message_callbacks[msg_type](payload)

    def shutdown(self):#   """ Shutdown client connection """
        self.alive = False
        self.client_socket.close()

class TCPServer:#   """ Contains socket connections to clients, handles new connections """
    def __init__(self, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = ('', port)
        self.sock.bind(server_address)
        print("Listening at {}:{}".format(socket.gethostbyname(socket.gethostname()), port))
        self.__new_connections = []
        self.connections = []
        self.connection_lock = threading.Lock()
        self.listening_thread = None

    def __add_connection(self, conn: ClientConnection):#""" Append new connection safely to list of new connections """
        with self.connection_lock:self.__new_connections.append(conn)

    def get_new_connections(self):#""" Safely return a list of new connections """
        conns= []
        with self.connection_lock:
            conns += self.__new_connections
            self.__new_connections.clear()
        return conns

    def accept_connections(self):#""" Server listener socket loop, accept connections """
        try:
            self.sock.listen(5)
            while 1:
                self.__add_connection(ClientConnection(*self.sock.accept()))
        except socket.error: pass
        print("Closing server, thanks for playing!")
        self.sock.close()

    def start_listening(self):# """ Start listening thread """
        self.listening_thread = threading.Thread(target=self.accept_connections, args=())
        self.listening_thread.start()

    def broadcast(self, msg):# """ Send a message to all connected clients"""
        msg_data = msg.encode()
        for conn in self.connections:  conn.send_bytes(msg_data)

    def shutdown(self):#  """ Close sockets and terminate """
        self.sock.close()
        connections = self.get_new_connections()
        for conn in connections:     conn.shutdown()
        for conn in self.connections:     conn.shutdown()

class TCPClient:#  """ Class that encapsulate the TCP connection to the server """
    def __init__(self, server_addr):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("Connecting to ", server_addr)
        self.sock.connect(server_addr)
        self.message_callbacks = { S_GAME_UPDATE: self.parse_game_update, S_PLAYER_REGISTERED: self.parse_player_registered }
        self.received_game_updates = []
        self.player_to_snake = {}
        print("Connected to {}:{}, self {}".format(server_addr[0],server_addr[1],self.sock.getsockname()))

    def register_player(self, index, player): self.sock.sendall(PlayerRegisterMessage(index, player).encode())#  """ Send register player message to server """

    def send_snake_input(self, local_id, snake_input):#  """ Send snake input for a player to the server """
        if local_id in self.player_to_snake:
            snake_id = self.player_to_snake[local_id]
            self.sock.sendall(SnakeInputMessage(snake_id, snake_input).encode())

    def parse_player_registered(self, payload):#    """ Receive information from server about which snake            is yours to control """
        snake_id, player_id = struct.unpack_from('>ii', payload, 0)
        self.player_to_snake[player_id] = snake_id

    def parse_game_update(self, payload):#  """ Parse pizza update message, generate            a new item into received_pizza_updates list """
        msg = GameStateUpdateMessage([], [])
        msg.decode(payload)
        self.received_game_updates.append(msg)

    def receive_game_uptate(self) -> bool:# """ Listen to messages until a game update        Message has been read, return False if            Connection was closed """
        message_type = 0
        try:
            while message_type != S_GAME_UPDATE: message_type = self.receive_message()
        except socket.error:
            print("Connection closed!")
            return False
        return 1

    def receive_message(self):#""" Read one server message from socket """
        header = self.sock.recv(struct.calcsize(HEADER_FORMAT))
        msg_type, msg_len = struct.unpack_from(HEADER_FORMAT, header, 0)
        payload = self.sock.recv(msg_len)
        typed_message = msg_type

        self.message_callbacks[typed_message](payload)
        return typed_message

    def shutdown(self):self.sock.close()#""" Shutdown the client connection """

########################################## MAIN 

# 20% smaller than original - PLAY_AREA PA=(W,H)
W=H=240# larger screen - height changed from 160

S_INI_LEN = 4 #20 - SNAKE_INITIAL_LENGTH
S_SPD = 0.8 # 4 - SNAKE_SPEED
S_R = 2 # 10 - SNAKE_RADIUS
SD = 2 * S_R #- SNAKE_DIAMETER
S_TURN = 6 # SNAKE_TURN_RATE
PZ_R_RANGE = (3,10)#(10, 50) - pizza radius range
PZ_NUM = 10 # PIZZA_NUM

#self.dim =(1+W//SD,1+H//SD)

GRID_W=1+W//SD
GRID_H=1+H//SD

MAX_PLAYERS = 8
PLAYER_INIT_STATE =[ # posX,posY and orientation
    (SD,H//2,0),# left
    (W//2,SD,90),#  top
    (W-SD,H//2,180),# right
    (W//2,H-SD,270),#  bottom
    (SD,SD,45), #top left
    (W-SD, SD,135),# top right
    (W-SD,H-SD,225),# bottom right
    (SD,H-SD,315),# bottom left
    ]

class Game:
    def __init__(self):
        P.init(W,H,scale=2)# pygame >> pyxel
        self.GS = GameState()
        self.ongame=1
        self.frame_num= 0
        self.players = []
        self.inputs = InputHandler()
        self.server = TCPServer(DEFAULT_PORT) ### NETWORK HANDLING !!!!
        self.server.start_listening()

        self.add_player(Human('P1', self.inputs, (P.KEY_LEFT, P.KEY_RIGHT)))#(P.K_LEFT, P.K_RIGHT)

        for i in range(3):self.add_player(SimpleAI('Bot%d'%i))
        #run(self.update, self.draw)

    def add_player(self, player):#""" Add a player to the game. """
        snake_id = len(self.GS.SN)
        print('add_player() - snake_id',snake_id)
        if snake_id < MAX_PLAYERS:
            snake = Snake(PLAYER_INIT_STATE[snake_id])
            player.snake_id = snake_id
            
            self.GS.SN+=[snake]
            self.players.append(player)

    def handle_events(self):#"""Main event pump"""
        if btnp(P.KEY_Q):quit()#  # If user clicked closeFlag that we are done so we exit this loop
#        else:self.inputs.handle_event(event)

    def gameupdate(self):#""" Game logic update """
        for snake, player in zip(self.GS.SN, self.players):
            snake.snake_update(self.frame_num, player.snake_input)
            self.GS.COLs.add_parts(snake.ADDED)
            self.GS.COLs.remove_parts(snake.RMVED)
            self.GS.PZ_MGR.eat(snake)
        self.GS.COLs.handle_collisions(self.GS.SN)

        for snake_id, snake in enumerate(self.GS.SN):
            if len(snake.BODY) > 0 and not snake.alive:
                self.GS.COLs.remove_parts(snake.BODY)
                snake.clear()
                # TODO remove? Game end logic and scoring?
                snake.reset(*PLAYER_INIT_STATE[snake_id])

        self.GS.PZ_MGR.update_pizzas()
        #def update_state_to_players(self):#""" Send all tick changes to all players.This tells AI and remote players the game state"""
        # TODO move to networking code
        new_connections = self.server.get_new_connections()
        if len(new_connections) > 0:
            game_msg = GameStateUpdateMessage(self.GS.PZ, [])
            for snake_id, snake in enumerate(self.GS.SN): game_msg.SN_UPD+=[(snake_id, snake.dir, 0,snake.BODY)]
            msg_data = game_msg.encode()
            for conn in new_connections: conn.send_bytes(msg_data)

        if len(self.server.connections) > 0:
            game_msg = GameStateUpdateMessage(
                self.GS.PZ_MGR.NewPZ,
                self.GS.PZ_MGR.RMedPZ)
            for snake_id, snake in enumerate(self.GS.SN): game_msg.SN_UPD+=[(snake_id, snake.dir, len(snake.RMVED),snake.ADDED)]
            self.server.broadcast(game_msg)

        self.server.connections += new_connections

        for conn in self.server.connections:
            players_to_register = conn.get_new_players()
            for player in players_to_register:self.add_player(player)
            conn.add_registered_players(players_to_register)

        # TODO clean closed connections

        self.frame_num += 1

    def draw_game(self, GS):
        P.cls(1)
        for pz in GS.PZ:# draw all pizza
            for d,c in zip((0,1,2),(4,10,9)):P.circ(pz.x,pz.y,pz.r-d,c)# color 5 is temporarily

        for i, snake in enumerate(GS.SN): # execute it for all snakes
            POS=snake.ADDED[0]
            c = 11 if i<1 else 8
            for part in snake.ADDED:P.circ(part[0], part[1],S_R, c)# color 5 is temporarily
            snake.ADDED.clear()

            for part in snake.RMVED:P.circ(part[0], part[1],S_R,c)# color 5 is temporarily
            snake.RMVED.clear()

            if len(snake.BODY) > 0:
                part = snake.BODY[0]
                P.circ(part[0], part[1],S_R,c)

            P.text(POS[0],POS[1]-1,str(i),0)# player id shadow
            P.text(POS[0]-1,POS[1]-2,str(i),7 if i<1 else 10)# player id draw

    def run(self):# """ Main Program Loop """
        while self.ongame:
            P.cls
            self.handle_events()

            for player in self.players:player.act()
            self.gameupdate()
            self.draw_game(self.GS)
            #P.display.flip()
            P.flip()
            InputState.clear_tick_states()
            self.GS.PZ_MGR.clear_tick_changes()
#            self.clock.tick(60)# --- Limit to 60 frames per second
        #P.display.quit()
        self.server.shutdown()

STATES = []

@unique
class Action(IntEnum):#    """ All game actions that buttons can be mapped to """
    TURN_LEFT = 0
    TURN_RIGHT = auto() # what is it ???? >> looks coming from enum

class InputState:# """ Game action state """
    @staticmethod
    def clear_tick_states():#    """ Clear the per tick 'pressed' and 'released'  states of all existing input states """
        for x in STATES:
            #x.clear_tick_actions()        
            x.button_pressed = [0] * len(Action)
            x.button_released = [0] * len(Action)

    def __init__(self):
        self.button_state = [0] * len(Action)
        self.button_pressed = [0] * len(Action)
        self.button_released = [0] * len(Action)
        STATES.append(self)
        print('len(Action)',len(Action),Action)


    def handle_action(self, action, down):# """ Update input state based on action """
        self.button_state[action] = down
        if down: self.button_pressed[action] = 1
        else: self.button_released[action] = 1

#    def clear_tick_actions(self):# """ Clear states for pressed this tick and released this tick """
#        self.button_pressed = [0] * len(Action)
#        self.button_released = [0] * len(Action)


class InputHandler:#""" Contains button states, handles input mappings to game actions """
    def add_mapping(self, IN, key_code, action):
        self.button_mappings[action].append((key_code, IN))#""" Create a input mapping from key_code to game action """
    def __init__(self):
        self.button_mappings=[[]for _ in Action]
    def handle_event(self, event):#""" Process input mapping for event and update Action state """        
        if event.type != P.KEY_DOWN and event.type != P.KEY_UP:return
        is_down = event.type == P.KEY_DOWN
        for action_index, mapped_keys in enumerate(self.button_mappings):
            for m in mapped_keys:
                if event.key == m[0]:
                    m[1].handle_action(Action(action_index), is_down)

class Snake:#    """ Contains the state of a single snake object """
    def __init__(self, init_state):
        self.reset(*init_state)
        self.BODY = []
        self.ADDED = []
        self.RMVED = []

    def reset(self, x,y,d):#""" Reset snake to initial position and length, mark it alive """
        self.length = S_INI_LEN
        self.pos = (x,y)
        self.dir = d
        self.alive = 1

    def head(self):return self.BODY[-1]#"""  the front of the snake """
    def kill(self):self.alive = 0#""" Mark snake dead """

    def clear(self):#""" Mark all snake parts as removed, clear all parts """
        self.RMVED += self.BODY
        self.BODY = []
        self.length = 0

    def crate_new_head(self, frame_num):
        self.add_part((int(self.pos[0]), int(self.pos[1]), frame_num))#""" Create a new head part at snake position """

    def add_part(self, x):# """ Add a single part to the snake head """
        self.BODY+=[x]
        self.ADDED+=[x]
#        print(len(self.BODY),len(self.ADDED))

    def add_parts(self, G):# """ Add multi bodies to the snake head """
        for x in G:self.add_part(x)
        
    def remove_part(self):self.RMVED+=[self.BODY.pop(0)]# """ Remove a part from the TAIL """

    def snake_update(self, frame_num, turn_input):# """ Apply inputs and update snake head and tail. Changed parts can be queried in ADDED and RMVED """
        self.dir += turn_input
        rad = math.radians(self.dir)
        vel = (S_SPD * math.cos(rad), S_SPD * math.sin(rad)) #""" Calculate movement vector from direction and velocity """
        self.pos = (self.pos[0] + vel[0], self.pos[1] + vel[1])
        self.crate_new_head(frame_num)
        if self.length<len(self.BODY):self.remove_part() # what does it? 

    def is_own_head(self, colliding_part):#  """ Check if colliding part is part of snake's own head to            avoid self collisions """
        for i, part in enumerate(self.BODY[::-1]):
            if part == colliding_part:return 1
            if i * S_SPD > SD:return 0
        return 0

class Pizza:#  the state of one pizza object 
    def __init__(self, x, y, r, id):
        self.x = x
        self.y = y
        self.r = r
        self.id = id
        self.eaten = 0

class CollisionManager:#  """  use snake body size grid for Snake to snake colisions check only the current and boundary grid cells to find all possible collisions. """
    def __init__(self):self.COL_GRID= [ [] for _ in range(GRID_W*GRID_H)]

    def get_colliders(self, x):# """ Return all possible snake to snake collision parts   from current and boundary collision grid cells """
        ix = x[0] // SD
        iy = x[1] // SD
        COLs = []
        for i in range(max(ix - 1, 0), min(ix + 2, GRID_W)):
            for j in range(max(0, iy - 1), min(iy + 2, GRID_H)):
                COLs += [ p for p in self.COL_GRID[i+GRID_W*j] if (p[0] - x[0])**2 + (p[1] - x[1])**2 < SD**2    ]
#        print('COLs',COLs)
        return COLs

    def add_parts(self, ADDED):# """ Update the collision grid with several Snake parts """
        for x in ADDED:
            ix = x[0] // SD
            iy = x[1] // SD
            index = ix+GRID_W*iy
            if 0 <= index < len(self.COL_GRID):  self.COL_GRID[index].append(x)

    def remove_parts(self, RMVED):#""" Remove multiple parts from the collision grid """
        for snake_tail in RMVED:
            ix = snake_tail[0] // SD
            iy = snake_tail[1] // SD
            index = ix+GRID_W*iy
            if 0 <= index < len(self.COL_GRID): self.COL_GRID[index].remove(snake_tail)

    def handle_collisions(self, snakes):#   """ Check all border and snake to snake collisions.   Mark snakes as 'killed' if collisions happen. """
        def check_border_collisions(snake):# """ Check snake border collision """
            head = snake.head()
            return not S_R<= head[0]<W-S_R or not S_R<=head[1]< H-S_R

        def check_snake_collisions(snake):return any(not snake.is_own_head(col) for col in self.get_colliders(snake.head()))# """ Check snake to snake collisions """

        for x in snakes:
            if check_border_collisions(x) or check_snake_collisions(x):x.kill()

class PizzaManager:# """ Pizza generator and eating logic """
    def __init__(self, pizzas):
        self.PZ = pizzas
        self.NewPZ = []
        self.RMedPZ = []

    def generate_pizza(self):# """ Generate a new pizza at random location """
        r = random.randrange(PZ_R_RANGE[0], PZ_R_RANGE[1] + 1)
        x = r + random.randrange(W - 2 * r)
        y = r + random.randrange(H - 2 * r)
        pizza = Pizza(x, y, r, len(self.PZ))
        self.NewPZ+=[pizza]
        self.PZ+=[pizza]

    def update_pizzas(self):# """ Remove eaten pizzas, bake new ones to replace them """
        for pizza in self.PZ:
            if pizza.eaten:
                self.RMedPZ+=[pizza.id]
                self.PZ.remove(pizza)
        while len(self.PZ) < PZ_NUM: self.generate_pizza()

    def eat(self, snake):# """ Check if a snake touch to eat some pizzas. Multiple snakes can eat the same pizza before the eaten pizzas are removed at call to 'update'."""
        pos = snake.head()
        for pizza in self.PZ:
            if ( pos[0]- pizza.x)**2+ (pos[1]- pizza.y)**2 < (S_R + pizza.r)**2:
                pizza.eaten = 1
                snake.length+=pizza.r

    def clear_tick_changes(self):# """ Clear what pizzas were created or remove this frame """
        self.NewPZ.clear()
        self.RMedPZ.clear()

class GameState:#   """ A complete collections of the game state. Contains the state of Pizzas and Snakes """
    def __init__(self):
        self.COLs = CollisionManager()
        self.SN = []#self.snakes
        self.PZ = []#self.pizzas

        # TODO move to server game logic
        self.PZ_MGR = PizzaManager(self.PZ)

    def remove_pizzas(self, removed_pizzas):#""" Remove all provided pizza_ids from active pizzas """
        for id in removed_pizzas:
            for pizza in self.PZ:
                if pizza.id == id:
                    self.PZ.remove(pizza)
                    break

if __name__ == '__main__':
    GAME = Game()
    GAME.run()