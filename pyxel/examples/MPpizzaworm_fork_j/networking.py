# All network related thingies """

import socket
from abc import ABC, abstractmethod
import threading
import struct
#from typing import List, Sequence, Optional, Tuple, Any, Dict
from enum import IntEnum, unique
from game_state import Pizza, SnakePart
from players import Player

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


def bytes_to_int(byte_array: bytes) -> int:
    """ Bytes to int """
    return int.from_bytes(byte_array, byteorder='big')


def pack_into(fmt: str, buffer: bytearray, offset: int, *args) -> int:
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
    def message_length(self) -> int:
        """ Calculate message payload length without header """
    def total_message_size(self) -> int:
        """ Message size with header """
        return self.message_length() + struct.calcsize(self.header_format)

    @abstractmethod
    def encode(self) -> bytes:
        """ return the bytes of the encoded message """
    def pack_header(self, buffer: bytearray) -> int:
        """ Write message header, return offset """
        return pack_into(self.header_format, buffer, 0, self.msg_type,
                         self.message_length())

    @staticmethod
    def pack_str(buffer: bytearray, offset: int, msg: str) -> int:
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

    def __init__(self, index: int, player: Player):
        super().__init__(NetMessage.C_REGISTER_PLAYER)
        self.index = index
        self.player = player

    def message_length(self) -> int:
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

    def message_length(self) -> int:
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

    def message_length(self) -> int:
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

    def message_length(self) -> int:
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

    def encode_pizzas(self, msg_buffer: bytearray, offset: int) -> int:
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

    def encode_snakes(self, msg_buffer: bytearray, offset: int) -> int:
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

    def decode_pizzas(self, payload: bytes, offset: int) -> int:
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

    def decode_snakes(self, payload: bytes, offset: int) -> int:
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
    def __init__(self, remote_id: int, name: str):
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
