# """ Input mapping from pygame events to game actions """
from enum import IntEnum, unique, auto
import pyxel as P

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
