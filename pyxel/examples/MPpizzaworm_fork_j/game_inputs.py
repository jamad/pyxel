# """ Input mapping from pygame events to game actions """
from enum import IntEnum, unique, auto
from typing import List, Tuple, Any
import pygame


@unique
class Action(IntEnum):
    """ All game actions that buttons can be mapped to """
    TURN_LEFT = 0
    TURN_RIGHT = auto()

class InputState:
    """ Game action state """
    @staticmethod
    def clear_tick_states():#    """ Clear the per tick 'pressed' and 'released'  states of all existing input states """
        for state in ALL_INPUT_STATES:
            state.clear_tick_actions()

    def __init__(self):
        self.button_state = [False] * len(Action)
        self.button_pressed = [False] * len(Action)
        self.button_released = [False] * len(Action)
        ALL_INPUT_STATES.append(self)

    def __del__(self):
        ALL_INPUT_STATES.remove(self)

    def handle_action(self, action, down):# """ Update input state based on action """
        self.button_state[action] = down
        if down: self.button_pressed[action] = True
        else: self.button_released[action] = True

    def clear_tick_actions(self) -> None:
        """ Clear states for pressed this tick and released this tick """
        self.button_pressed = [False] * len(Action)
        self.button_released = [False] * len(Action)


ALL_INPUT_STATES: List[InputState] = []


class InputHandler:
    """ Contains button states, handles input mappings to game actions """
    def add_mapping(self, input_state: InputState, key_code: int,
                    action: Action) -> None:
        """ Create a input mapping from key_code to game action """
        self.button_mappings[action].append((key_code, input_state))

    def __init__(self) -> None:
        self.button_mappings: List[List[Tuple[int, InputState]]] = [
            [] for action_index in Action
        ]

    def handle_event(self, event: Any) -> None:
        """ Process input mapping for event and update Action state """
        if event.type != pygame.KEYDOWN and event.type != pygame.KEYUP:
            return
        is_down = event.type == pygame.KEYDOWN
        for action_index, mapped_keys in enumerate(self.button_mappings):
            for mapping in mapped_keys:
                if event.key == mapping[0]:
                    mapping[1].handle_action(Action(action_index), is_down)
