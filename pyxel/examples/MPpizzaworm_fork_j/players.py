""" Types for player interaction """

from abc import ABC, abstractmethod
import random
import settings
from game_inputs import Action, InputHandler, InputState

class Player(ABC):
    """ Human player """
    def __init__(self, name: str):
        self.name = name
        self.snake_input = 0
        self.snake_id = -1

    @abstractmethod
    def act(self):
        """ Process the inputs to the controlled snake.
            AI players can process the game state in this function. """
    def bind_snake(self, snake_id):
        """ Set the controlled snake_id """
        self.snake_id = snake_id

    def get_snake_input(self) -> int:
        """ return the snake turning input """
        return self.snake_input

    @abstractmethod
    def send_update(self, snake_id, added_parts,num_removed_parts):
        """ Interface which remote and AI players can override to
            upkeep game state """

class Human(Player):
    """ Human player with controls """
    def __init__(self, name: str, input_mapper: InputHandler, keyboard_controls):
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