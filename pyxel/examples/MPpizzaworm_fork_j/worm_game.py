""" Types for player interaction """
from abc import ABC, abstractmethod ##### what is this for ????
import random
from collections import deque
import math

import socket
import threading
import struct
from enum import IntEnum, unique, auto

import pyxel as P
from pyxel import btn,btnp,quit

class Player(ABC):# """ Human player """
    def __init__(self, name):
        self.name = name
        self.snake_input = 0
        self.snake_id = -1

    @abstractmethod
    def act(self):pass# """ Process the inputs to the controlled snake.AI players can process the game state in this function. """
    def bind_snake(self, snake_id):self.snake_id = snake_id#""" Set the controlled snake_id """
    def get_snake_input(self):return self.snake_input#""" return the snake turning input """

    @abstractmethod
    def send_update(self, snake_id, added_parts,num_removed_parts):pass# """ Interface which remote and AI players can override to upkeep game state """

class Human(Player):
    """ Human player with controls """
    def __init__(self, name, input_mapper, keyboard_controls):
        super().__init__(name)
        self.input_state = InputState()
        if keyboard_controls != (-1, -1):
            input_mapper.add_mapping(self.input_state, keyboard_controls[0], Action.TURN_LEFT)
            input_mapper.add_mapping(self.input_state, keyboard_controls[1], Action.TURN_RIGHT)

    def act(self):#""" Process the inputs to the controlled snake.AI players can process the game state in this function. """
        if self.input_state.button_state[Action.TURN_LEFT]:self.snake_input = -settings.SNAKE_TURN_RATE
        elif self.input_state.button_state[Action.TURN_RIGHT]:self.snake_input = settings.SNAKE_TURN_RATE
        else:self.snake_input = 0

    def send_update(self, snake_id, added_parts,num_removed_parts):
        del snake_id  # unused interface
        del added_parts  # unused interface
        del num_removed_parts  # unused interface

class SimpleAI(Player):# """ Simple AI to test interfaces """
    def __init__(self, name):
        self.num = 0
        super().__init__(name)
    def act(self):self.snake_input = random.randrange(-5, 6)# """ Generate input """
    def send_update(self, snake_id, added_parts,num_removed_parts):# """ Interface which remote and AI players can override to upkeep game state """
        del snake_id  # unused interface
        del added_parts  # unused interface
        del num_removed_parts  # unused interface

##############################################  ALL NETWORKING for the following part  ##########################
AddrType = (str, int)
DEFAULT_PORT = 45000

@unique
class NetMessage(IntEnum):
    """ All game actions that buttons can be mapped to """
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
#    bytes       data
#    4           Message type
#    4           Message length
#    4           Snake ID (Must match client's own snake ID)
#    4           Turn direction [-5, 5]

# Server to client:
#    PLAYER_REGISTERED (own information, answer to ADD_PLAYER)
#    bytes       data
#    4           Message type
#    4           Message length
#    4           Controlled Snake ID
#    4           Client Specified remote player ID

#    PLAYER_REFUSED (Game full etc.)
#    bytes       data
#    4           Message type
#    4           Message length
#    4           Client Specified remote player ID
#    [1]*        Error message

#    NEW_PLAYER (external players)
#    bytes       data
#    4           Message type
#    4           Message length
#    4           Snake ID
#    1           Player Name length
#    [1]*        Player Name

#    GAME_STATE_UPDATE:
#    bytes       data
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


def int_to_bytes(x: int) -> bytes:
    """ Convert int to bytes """
    return x.to_bytes(4, byteorder='big')


def bytes_to_int(byte_array: bytes):
    """ Bytes to int """
    return int.from_bytes(byte_array, byteorder='big')


def pack_into(fmt, buffer: bytearray, offset: int, *args):
    """ Pack data with struct.pack_into and given data format.
        return the size of the output data with that format.
        Use offset += pack_into() to update the offset for next call """
    struct.pack_into(fmt, buffer, offset, *args)
    return struct.calcsize(fmt)


MSG_HEADER_FORMAT = '>ii'
MSG_HEADER_SIZE = struct.calcsize(MSG_HEADER_FORMAT)


class Message(ABC):
    """ Network message interface for serialization """
    header_format = '>ii'

    def __init__(self, msg_type: NetMessage):
        self.msg_type = msg_type

    @abstractmethod
    def message_length(self):
        """ Calculate message payload length without header """
    def total_message_size(self):
        """ Message size with header """
        return self.message_length() + struct.calcsize(self.header_format)

    @abstractmethod
    def encode(self) -> bytes:
        """ return the bytes of the encoded message """
    def pack_header(self, buffer: bytearray):
        """ Write message header, return offset """
        return pack_into(self.header_format, buffer, 0, self.msg_type,
                         self.message_length())

    @staticmethod
    def pack_str(buffer: bytearray, offset: int, msg):
        """ Encode variable length str, return packed size """
        fmt = '{}p'.format(len(msg) + 1)
        return pack_into(fmt, buffer, offset, msg.encode())

    @staticmethod
    def unpack_str(payload: bytes, offset: int):
        """ Unpack variable lenght str from message payload
            return (str, new offset) """
        str_len, = struct.unpack_from('B', payload, offset)
        fmt = '{}p'.format(str_len + 1)
        name, = struct.unpack_from(fmt, payload, offset)
        return (name, offset + str_len + 1)

    def reserve_msg_buffer(self) -> bytearray:
        """ Reserve big enough buffer for the message """
        return bytearray(self.total_message_size())


class PlayerRegisterMessage(Message):
    """ Register client player to the server """
    player_id_format = '>i'

    def __init__(self, index, player):
        super().__init__(NetMessage.C_REGISTER_PLAYER)
        self.index = index
        self.player = player

    def message_length(self):
        """ return message lenght """
        return (struct.calcsize(self.player_id_format) +
                len(self.player.name) + 1)

    def encode(self) -> bytes:
        """ encode message into bytes """
        msg_bytes: bytearray = self.reserve_msg_buffer()
        offset = self.pack_header(msg_bytes)
        offset += pack_into(self.player_id_format, msg_bytes, offset,
                            self.index)
        offset += self.pack_str(msg_bytes, offset, self.player.name)
        return bytes(msg_bytes)

    @staticmethod
    def decode(payload: bytes) :
        """ Return decoded [remote_id, player_name] tuple """
        remote_id, = struct.unpack_from(PlayerRegisterMessage.player_id_format,
                                        payload, 0)
        name, _ = Message.unpack_str(payload, 4)
        return (remote_id, name)


class PlayerRegisteredMessage(Message):
    """ Register client player to the server """
    register_format = '>ii'

    def __init__(self, snake_id: int, remote_id: int):
        super().__init__(NetMessage.S_PLAYER_REGISTERED)
        self.snake_id = snake_id
        self.remote_id = remote_id

    def message_length(self):
        return struct.calcsize(self.register_format)

    def encode(self) -> bytes:
        """ encode message into bytes """
        msg_bytes: bytearray = self.reserve_msg_buffer()
        offset = self.pack_header(msg_bytes)
        offset += pack_into(self.register_format, msg_bytes, offset,
                            self.snake_id, self.remote_id)

        return bytes(msg_bytes)

    def decode(self, payload: bytes):
        """ Decode snake_id and remote_id from server message """
        self.snake_id, self.remote_id = struct.unpack_from(
            self.register_format, payload, 0)


class SnakeInputMessage(Message):
    """ Client to server snake control message """
    input_format = '>ii'

    def __init__(self, snake_id: int, snake_input: int):
        super().__init__(NetMessage.C_SNAKE_INPUT)
        self.snake_id = snake_id
        self.snake_input = snake_input

    def message_length(self):
        """ Calculate message length """
        return struct.calcsize(self.input_format)

    def encode(self) -> bytes:
        """ Encode message to bytes to be send """
        msg_bytes: bytearray = self.reserve_msg_buffer()
        offset = self.pack_header(msg_bytes)
        offset += pack_into(self.input_format, msg_bytes, offset,
                            self.snake_id, self.snake_input)
        return bytes(msg_bytes)

    def decode(self, payload: bytes):
        """ Decode snake_id and input from message payload """
        self.snake_id, self.snake_input = struct.unpack_from(
            self.input_format, payload, 0)


class GameStateUpdateMessage(Message):
    """ Game state update message encoding and decoding  """
    pizza_count_format = '>ii'
    pizza_rem_id_format = '>i'
    pizza_added_format = '>4i'
    snake_count_format = '>i'
    snake_header_format = '>4i'
    snake_part_format = '>3i'

    def __init__(self, added_pizzas, removed_pizzas):
        super().__init__(NetMessage.S_GAME_UPDATE)
        self.added_pizzas = added_pizzas
        self.removed_pizzas = removed_pizzas
        self.snake_updates: List[
            Tuple[int, int, int, Sequence[SnakePart]]] = []

    def buffer_snake_update(self, snake_id, snake_dir,added_parts,removed_parts):
        """ Buffer a single snake information internally """
        self.snake_updates.append(
            (snake_id, snake_dir, removed_parts, added_parts))

    def message_length(self):
        """ Calculate the message payload byte size (without header) """
        removed = len(self.removed_pizzas)
        added = len(self.added_pizzas)
        msg_len = (struct.calcsize(self.pizza_count_format) +
                   removed * struct.calcsize(self.pizza_rem_id_format) +
                   added * struct.calcsize(self.pizza_added_format))
        msg_len += struct.calcsize(self.snake_count_format)
        for _, _, _, added_parts in self.snake_updates:
            msg_len += (
                struct.calcsize(self.snake_header_format) +
                struct.calcsize(self.snake_part_format) * len(added_parts))
        return msg_len

    def encode_pizzas(self, msg_buffer: bytearray, offset: int):
        """ Encode pizzas into the message """
        offset += pack_into(self.pizza_count_format, msg_buffer, offset,
                            len(self.removed_pizzas), len(self.added_pizzas))
        for pizza_id in self.removed_pizzas:
            offset += pack_into(self.pizza_rem_id_format, msg_buffer, offset,
                                pizza_id)
        for pizza in self.added_pizzas:
            offset += pack_into(self.pizza_added_format, msg_buffer, offset,
                                pizza.pizza_id, pizza.x, pizza.y, pizza.radius)
        return offset

    def encode_snakes(self, msg_buffer: bytearray, offset: int):
        """ Encode snakes into the message """
        offset += pack_into(self.snake_count_format, msg_buffer, offset,
                            len(self.snake_updates))
        for snake_id, snake_dir, rem_count, added, in self.snake_updates:
            offset += pack_into(self.snake_header_format, msg_buffer, offset,
                                snake_id, snake_dir, rem_count, len(added))
            for part in added:
                offset += pack_into(self.snake_part_format, msg_buffer, offset,
                                    part[0], part[1], part[2])
        return offset

    def encode(self) -> bytes:
        """ Encode a complete server to client message as bytes object """
        msg_bytes: bytearray = self.reserve_msg_buffer()
        offset = self.pack_header(msg_bytes)
        offset = self.encode_pizzas(msg_bytes, offset)
        offset = self.encode_snakes(msg_bytes, offset)
        return bytes(msg_bytes)

    def decode_pizzas(self, payload: bytes, offset: int):
        """ Decode pizza update from the server message payload """
        removed, added = struct.unpack_from(self.pizza_count_format, payload,
                                            offset)
        offset += struct.calcsize(self.pizza_count_format)

        removed_format_size = struct.calcsize(self.pizza_rem_id_format)
        for _ in range(removed):
            rem, = struct.unpack_from(self.pizza_rem_id_format, payload,
                                      offset)
            offset += removed_format_size
            self.removed_pizzas.append(rem)

        pizza_format_size = struct.calcsize(self.pizza_added_format)
        for _ in range(added):
            pizza_id, pos_x, pos_y, radius = struct.unpack_from(
                self.pizza_added_format, payload, offset)
            offset += pizza_format_size
            self.added_pizzas.append(Pizza(pos_x, pos_y, radius, pizza_id))

        return offset

    def decode_snakes(self, payload: bytes, offset: int):
        """ Decode snakes part of the server game state update """
        snake_count, = struct.unpack_from(self.snake_count_format, payload,
                                          offset)
        offset += struct.calcsize(self.snake_count_format)
        header_size = struct.calcsize(self.snake_header_format)
        part_size = struct.calcsize(self.snake_part_format)
        for _ in range(snake_count):
            snake_id, snake_dir, rem_count, added_count = struct.unpack_from(
                self.snake_header_format, payload, offset)
            offset += header_size
            added_parts: List[SnakePart] = []
            for _ in range(added_count):
                pos_x, pos_y, part_id = struct.unpack_from(
                    self.snake_part_format, payload, offset)
                offset += part_size
                added_parts.append((pos_x, pos_y, part_id))
            self.snake_updates.append(
                (snake_id, snake_dir, rem_count, added_parts))
        return offset

    def decode(self, payload: bytes):
        """ Decode the gamestate update message payload.
            Generate 'added_pizzas', 'removed_pizzas' and
            snake_updates lists. """
        offset = 0
        offset = self.decode_pizzas(payload, offset)
        offset = self.decode_snakes(payload, offset)


class RemotePlayer(Player):
    """ Player whose inputs come over network """
    def __init__(self, remote_id: int, name):
        super().__init__(name)
        self.remote_id = remote_id
        self.__last_snake_input = 0
        self.player_lock = threading.Lock()

    def set_remote_input(self, remote_input: int):
        """ Safely store snake control input for this player """
        with self.player_lock:
            self.__last_snake_input = remote_input

    def act(self):
        """ Copy remote input to interface """
        with self.player_lock:
            self.snake_input = self.__last_snake_input

    def send_update(self, snake_id, added_parts,num_removed_parts):
        del snake_id  # unused interface
        del added_parts  # unused interface
        del num_removed_parts  # unused interface


class ClientConnection:
    """ Socket encapsulation for sending message to clients """
    def __init__(self, client_socket: socket.socket, addr: AddrType):
        print("Got connection from ", addr)
        self.alive = True
        self.client_socket = client_socket
        self.send_lock = threading.Lock()

        self.message_callbacks = {
            NetMessage.C_REGISTER_PLAYER: self.parse_register_player,
            NetMessage.C_SNAKE_INPUT: self.parse_snake_input
        }
        self.__players: Dict[int, RemotePlayer] = {}
        self.__new_players: List[RemotePlayer] = []
        self.player_lock = threading.Lock()
        listerner_thread = threading.Thread(target=self.listen_messages,
                                            args=())
        listerner_thread.start()

    def register_new_player(self, player: RemotePlayer):
        """ Add player to temporary list of new players to be
            joining the game """
        with self.player_lock:
            self.__new_players.append(player)

    def get_new_players(self):
        """ Get a list of players that have not been mapped to game yet """
        with self.player_lock:
            players = list(self.__new_players)
            self.__new_players.clear()
            return players

    def add_registered_players(self, new_players):
        """ Add a new list of remote players that have been
            mapped to a snake """
        with self.player_lock:
            for player in new_players:
                if player.snake_id != -1:
                    self.__players[player.snake_id] = player

        for player in new_players:
            if player.snake_id != -1:
                self.send_message(
                    PlayerRegisteredMessage(player.snake_id, player.remote_id))
            else:
                pass
                # TODO
                # self.send_message(PlayerRefusedMessage(player.remote_id,
                #                                        "Game Full"))
                #

    def send_message(self, msg: Message):
        """ Send a network message to this client connection """
        self.send_bytes(msg.encode())

    def send_bytes(self, msg: bytes):
        """ Send encoded network message to this client connection """
        if self.alive:
            try:
                with self.send_lock:
                    self.client_socket.sendall(msg)
            except socket.error:
                self.shutdown()

    def listen_messages(self):
        """ Message listening loop for one client connection """
        try:
            while True:
                self.receive_messages()
        except socket.error:
            self.shutdown()

    def parse_register_player(self, payload: bytes):
        """ Reguest for a new player from client """
        remote_id, name = PlayerRegisterMessage.decode(payload)
        self.register_new_player(RemotePlayer(remote_id, name))

    def __set_input(self, snake_id: int, snake_input: int):
        """ Safely set the input for a player """
        with self.player_lock:
            if snake_id in self.__players:
                self.__players[snake_id].set_remote_input(snake_input)

    def parse_snake_input(self, payload: bytes):
        """ Received a snake input message from client """
        msg = SnakeInputMessage(0, 0)
        msg.decode(payload)
        self.__set_input(msg.snake_id, msg.snake_input)

    def send_game_update(self, game_msg: GameStateUpdateMessage):
        """ Send a snake update to a client """
        self.send_message(game_msg)

    def receive_messages(self):
        """ Read one message from socket """
        header = self.client_socket.recv(struct.calcsize(MSG_HEADER_FORMAT))
        msg_type, msg_len = struct.unpack_from(MSG_HEADER_FORMAT, header, 0)
        payload = self.client_socket.recv(msg_len)
        self.message_callbacks[NetMessage(msg_type)](payload)

    def shutdown(self):
        """ Shutdown client connection """
        self.alive = False
        self.client_socket.close()

class TCPServer:
    """ Contains socket connections to clients, handles new connections """
    def __init__(self, port: int):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = ('', port)
        self.sock.bind(server_address)
        print("Listening at {}:{}".format(
            socket.gethostbyname(socket.gethostname()), port))
        self.__new_connections: List[ClientConnection] = []
        self.connections: List[ClientConnection] = []
        self.connection_lock = threading.Lock()
        self.listening_thread: Optional[threading.Thread] = None

    def __add_connection(self, conn: ClientConnection):
        """ Append new connection safely to list of new connections """
        with self.connection_lock:
            self.__new_connections.append(conn)

    def get_new_connections(self):
        """ Safely return a list of new connections """
        conns: List[ClientConnection] = []
        with self.connection_lock:
            conns += self.__new_connections
            self.__new_connections.clear()
        return conns

    def accept_connections(self):
        """ Server listener socket loop, accept connections """
        try:
            self.sock.listen(5)
            while True:
                connection, addr = self.sock.accept()
                self.__add_connection(ClientConnection(connection, addr))
        except socket.error:
            pass
        print("Closing server, thanks for playing!")
        self.sock.close()

    def start_listening(self):
        """ Start listening thread """
        self.listening_thread = threading.Thread(
            target=self.accept_connections, args=())
        self.listening_thread.start()

    def broadcast(self, msg: Message):
        """ Send a message to all connected clients"""
        msg_data = msg.encode()
        for conn in self.connections:
            conn.send_bytes(msg_data)

    def shutdown(self):
        """ Close sockets and terminate """
        self.sock.close()
        connections = self.get_new_connections()
        for conn in connections:
            conn.shutdown()

        for conn in self.connections:
            conn.shutdown()


class TCPClient:
    """ Class that encapsulate the TCP connection to the server """
    def __init__(self, server_addr: AddrType):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("Connecting to ", server_addr)
        self.sock.connect(server_addr)
        self.message_callbacks = {
            NetMessage.S_GAME_UPDATE: self.parse_game_update,
            NetMessage.S_PLAYER_REGISTERED: self.parse_player_registered
        }
        self.received_game_updates: List[GameStateUpdateMessage] = []

        self.player_to_snake: Dict[int, int] = {}
        print("Connected to {}:{}, self {}".format(server_addr[0],server_addr[1],self.sock.getsockname()))

    def register_player(self, index: int, player: Player):
        """ Send register player message to server """
        self.sock.sendall(PlayerRegisterMessage(index, player).encode())

    def send_snake_input(self, local_id: int, snake_input: int):
        """ Send snake input for a player to the server """
        if local_id in self.player_to_snake:
            snake_id = self.player_to_snake[local_id]
            self.sock.sendall(
                SnakeInputMessage(snake_id, snake_input).encode())

    def parse_player_registered(self, payload: bytes):
        """ Receive information from server about which snake
            is yours to control """
        snake_id, player_id = struct.unpack_from('>ii', payload, 0)
        self.player_to_snake[player_id] = snake_id

    def parse_game_update(self, payload: bytes):
        """ Parse pizza update message, generate
            a new item into received_pizza_updates list """
        msg = GameStateUpdateMessage([], [])
        msg.decode(payload)
        self.received_game_updates.append(msg)

    def receive_game_uptate(self) -> bool:
        """ Listen to messages until a game update
            Message has been read, return False if
            Connection was closed """
        message_type = 0
        try:
            while message_type != NetMessage.S_GAME_UPDATE:
                message_type = self.receive_message()
        except socket.error:
            print("Connection closed!")
            return False
        return True

    def receive_message(self) -> NetMessage:#""" Read one server message from socket """
        header = self.sock.recv(struct.calcsize(MSG_HEADER_FORMAT))
        msg_type, msg_len = struct.unpack_from(MSG_HEADER_FORMAT, header, 0)
        payload = self.sock.recv(msg_len)
        typed_message = NetMessage(msg_type)
        self.message_callbacks[typed_message](payload)
        return typed_message

    def shutdown(self):self.sock.close()#""" Shutdown the client connection """


########################################## MAIN 

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
        self.server = TCPServer(DEFAULT_PORT)
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

@unique
class Action(IntEnum):#    """ All game actions that buttons can be mapped to """
    TURN_LEFT = 0
    TURN_RIGHT = auto()

class InputState:# """ Game action state """
    @staticmethod
    def clear_tick_states():#    """ Clear the per tick 'pressed' and 'released'  states of all existing input states """
        for state in ALL_INPUT_STATES:state.clear_tick_actions()

    def __init__(self):
        self.button_state = [0] * len(Action)
        self.button_pressed = [0] * len(Action)
        self.button_released = [0] * len(Action)
        ALL_INPUT_STATES.append(self)

    def __del__(self):ALL_INPUT_STATES.remove(self)

    def handle_action(self, action, down):# """ Update input state based on action """
        self.button_state[action] = down
        if down: self.button_pressed[action] = 1
        else: self.button_released[action] = 1

    def clear_tick_actions(self):# """ Clear states for pressed this tick and released this tick """
        self.button_pressed = [0] * len(Action)
        self.button_released = [0] * len(Action)

ALL_INPUT_STATES = []

class InputHandler:#""" Contains button states, handles input mappings to game actions """
    def add_mapping(self, input_state, key_code, action):self.button_mappings[action].append((key_code, input_state))#""" Create a input mapping from key_code to game action """
    def __init__(self):self.button_mappings=[[]for _ in Action]
    def handle_event(self, event):#""" Process input mapping for event and update Action state """        
        if event.type != P.KEYDOWN and event.type != P.KEYUP: return
        is_down = event.type == P.KEYDOWN
        for action_index, mapped_keys in enumerate(self.button_mappings):
            for mapping in mapped_keys:
                if event.key == mapping[0]:mapping[1].handle_action(Action(action_index), is_down)


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

class Pizza:#  """ Contain the state of one pizza object """
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
        return dx**2+ dy**2 < dist**2

    def mark_eaten(self):self.still_good = 0 #""" Marks pizza as eaten. Pizza will be removed at next manager update. """

class CollisionManager:
    """ Handles all snake collisions.
        Contains a collision grid where grid size is the snake body diameter.
        Snake to snake colisions need to then check only the current and
        boundary grid cells to find all possible collisions. """
    def __init__(self):
        self.dim = (1 + PLAY_AREA[0] // SNAKE_DIAMETER,   1 + PLAY_AREA[1] // SNAKE_DIAMETER)
        self.collision_grid: List[List[SnakePart]] = [  [] for i in range(self.dim[0] * self.dim[1])  ]

    def __grid_index(self, grid_x, grid_y):return grid_x + self.dim[0] * grid_y #""" return grid index """

    def __collide_cell(self, grid_idx,snake_head):# """ Check snake collision inside a single collision grid cell. """
        def part_collide(part1, part2):# """ Check snake part to snake part collision.  return 1 on collision. """
            dx = part1[0] - part2[0]
            dy = part1[1] - part2[1]
            return dx**2 + dy**2 < SNAKE_DIAMETER_SQ 
        return [ part for part in self.collision_grid[grid_idx] if part_collide(part, snake_head)     ]

    def get_colliders(self, snake_head):
        """ Return all possible snake to snake collision parts
            from current and boundary collision grid cells """
        ix = snake_head[0] // SNAKE_DIAMETER
        iy = snake_head[1] // SNAKE_DIAMETER
        collisions = []
        y_min_range = max(iy - 1, 0)
        y_max_range = min(iy + 2, self.dim[1])
        for i in range(max(ix - 1, 0), min(ix + 2, self.dim[0])):
            for j in range(y_min_range, y_max_range):
                collisions += self.__collide_cell(self.__grid_index(i, j), snake_head)
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
        def check_border_collisions(snake):
            """ Check snake border collision """
            head = snake.head()
            radius = SNAKE_RADIUS
            if not radius <= head[0] < PLAY_AREA[0] - radius:return 1
            if not radius <= head[1] < PLAY_AREA[1] - radius:return 1
            return 0

        def check_snake_collisions(snake):return any(not snake.is_own_head(col) for col in self.get_colliders(snake.head()))# """ Check snake to snake collisions """

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

    def eat(self, snake):
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

    def remove_pizza(self, pizza: Pizza): self.pizzas.remove(pizza)

    def remove_pizzas(self, removed_pizzas):#""" Remove all provided pizza_ids from active pizzas """
        for pizza_id in removed_pizzas:
            for pizza in self.pizzas:
                if pizza.pizza_id == pizza_id:
                    self.pizzas.remove(pizza)
                    break
GAME = Game()
GAME.run()