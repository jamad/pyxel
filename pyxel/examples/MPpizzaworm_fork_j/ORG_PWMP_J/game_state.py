""" Game objects and managers handling them """

from collections import deque
import math
import random
from typing import List, Tuple, Deque, Sequence
import settings

SnakePart = Tuple[int, int, int]
InitStateType = Tuple[int, int, int]  # (x, y, dir)


class Snake:
    """ Contains the state of a single snake object """
    def __init__(self, init_state: InitStateType) -> None:
        self.length: int = settings.SNAKE_INITIAL_LENGTH
        self.parts: Deque[SnakePart] = deque()
        self.pos: Tuple[float, float] = (init_state[0], init_state[1])
        self.dir: int = init_state[2]  # in Degrees
        self.new_parts: List[SnakePart] = []
        self.removed_parts: List[SnakePart] = []
        self.alive: bool = True
        self.calc_movement_vector()

    def head(self) -> SnakePart:
        """ return the front of the snake """
        return self.parts[-1]

    def kill(self) -> None:
        """ Mark snake dead """
        self.alive = False

    def clear(self) -> None:
        """ Mark all snake parts as removed, clear all parts """
        self.removed_parts += self.parts
        self.parts = deque()
        self.length = 0

    def reset(self, init_state: InitStateType) -> None:
        """ Reset snake to initial position and length, mark it alive """
        self.length = settings.SNAKE_INITIAL_LENGTH
        self.pos = (init_state[0], init_state[1])
        self.dir = init_state[2]
        self.alive = True

    def grow(self, food: int) -> None:
        """ Grow the snake with 'food' amount """
        self.length += food

    def calc_movement_vector(self) -> Tuple[float, float]:
        """ Calculate movement vector from direction and velocity """
        rad = math.radians(self.dir)
        speed = settings.SNAKE_SPEED
        return (speed * math.cos(rad), speed * math.sin(rad))

    def crate_new_head(self, frame_num: int) -> None:
        """ Create a new head part at snake position """
        self.add_part((int(self.pos[0]), int(self.pos[1]), frame_num))

    def add_part(self, part: Tuple[int, int, int]) -> None:
        """ Add a single part to the snake head """
        self.parts.append(part)
        self.new_parts.append(part)

    def add_parts(self, parts: Sequence[Tuple[int, int, int]]) -> None:
        """ Add multiple parts to the snake head """
        for part in parts:
            self.add_part(part)

    def remove_part(self) -> None:
        """ Remove one part from the tail of the snake """
        rem = self.parts.popleft()
        self.removed_parts.append(rem)

    def remove_n_parts(self, num: int) -> None:
        """ Remove multiple parts from the snake tail """
        for _ in range(num):
            self.remove_part()

    def update(self, frame_num: int, turn_input: int) -> None:
        """ Apply inputs and update snake head and tail. Changed parts
            can be queried in new_parts and removed_parts """
        self.dir += turn_input
        vel: Tuple[float, float] = self.calc_movement_vector()
        self.pos = (self.pos[0] + vel[0], self.pos[1] + vel[1])

        self.crate_new_head(frame_num)
        if len(self.parts) > self.length:
            self.remove_part()

    def is_own_head(self, colliding_part: SnakePart) -> bool:
        """ Check if colliding part is part of snake's own head to
            avoid self collisions """
        for i, part in enumerate(reversed(self.parts)):
            if part == colliding_part:
                return True
            if i * settings.SNAKE_SPEED > settings.SNAKE_DIAMETER:
                return False
        return False


class Pizza:
    """ Contain the state of one pizza object """
    def __init__(self, x: int, y: int, radius: int, pizza_id: int) -> None:
        self.x = x
        self.y = y
        self.radius = radius
        self.pizza_id = pizza_id
        self.still_good = True

    def is_close(self, pos: SnakePart, check_radius: int) -> bool:
        """ Hit check for the pizza and a collider at position 'pos' with
            radius 'check_radius' """
        dx = pos[0] - self.x
        dy = pos[1] - self.y
        dist = check_radius + self.radius
        if dx * dx + dy * dy < dist * dist:
            return True
        return False

    def mark_eaten(self) -> None:
        """ Marks pizza as eaten.
            Pizza will be removed at next manager update. """
        self.still_good = False


class CollisionManager:
    """ Handles all snake collisions.
        Contains a collision grid where grid size is the snake body diameter.
        Snake to snake colisions need to then check only the current and
        boundary grid cells to find all possible collisions. """
    def __init__(self) -> None:
        self.dim = (1 + settings.PLAY_AREA[0] // settings.SNAKE_DIAMETER,
                    1 + settings.PLAY_AREA[1] // settings.SNAKE_DIAMETER)
        self.collision_grid: List[List[SnakePart]] = [
            [] for i in range(self.dim[0] * self.dim[1])
        ]

    def __grid_index(self, grid_x: int, grid_y: int) -> int:
        """ return grid index """
        return grid_x + self.dim[0] * grid_y

    def __collide_cell(self, grid_idx: int,
                       snake_head: SnakePart) -> List[SnakePart]:
        """ Check snake collision inside a single collision grid cell. """
        def part_collide(part1: SnakePart, part2: SnakePart) -> bool:
            """ Check snake part to snake part collision.
                return True on collision. """
            dx = part1[0] - part2[0]
            dy = part1[1] - part2[1]
            return dx * dx + dy * dy < settings.SNAKE_DIAMETER_SQ

        return [
            part for part in self.collision_grid[grid_idx]
            if part_collide(part, snake_head)
        ]

    def get_colliders(self, snake_head: SnakePart) -> List[SnakePart]:
        """ Return all possible snake to snake collision parts
            from current and boundary collision grid cells """
        ix = snake_head[0] // settings.SNAKE_DIAMETER
        iy = snake_head[1] // settings.SNAKE_DIAMETER
        collisions: List[SnakePart] = []
        y_min_range = max(iy - 1, 0)
        y_max_range = min(iy + 2, self.dim[1])
        for i in range(max(ix - 1, 0), min(ix + 2, self.dim[0])):
            for j in range(y_min_range, y_max_range):
                collisions += self.__collide_cell(self.__grid_index(i, j),
                                                  snake_head)
        return collisions

    def add_part(self, snake_head: SnakePart) -> None:
        """ Update the collision grid with a new 'snake_head' """
        ix = snake_head[0] // settings.SNAKE_DIAMETER
        iy = snake_head[1] // settings.SNAKE_DIAMETER
        index = self.__grid_index(ix, iy)
        if 0 <= index < len(self.collision_grid):
            self.collision_grid[index].append(snake_head)

    def add_parts(self, new_parts: Sequence[SnakePart]) -> None:
        """ Update the collision grid with several Snake parts """
        for part in new_parts:
            self.add_part(part)

    def remove_part(self, snake_tail: SnakePart) -> None:
        """ Remove a single snake part from the collision grid """
        ix = snake_tail[0] // settings.SNAKE_DIAMETER
        iy = snake_tail[1] // settings.SNAKE_DIAMETER
        index = self.__grid_index(ix, iy)
        if 0 <= index < len(self.collision_grid):
            self.collision_grid[index].remove(snake_tail)

    def remove_parts(self, removed_parts: Sequence[SnakePart]) -> None:
        """ Remove multiple parts from the collision grid """
        for part in removed_parts:
            self.remove_part(part)

    def handle_collisions(self, snakes: List[Snake]) -> None:
        """ Check all border and snake to snake collisions.
            Mark snakes as 'killed' if collisions happen. """
        def check_border_collisions(snake: Snake) -> bool:
            """ Check snake border collision """
            head = snake.head()
            radius = settings.SNAKE_RADIUS
            if not radius <= head[0] < settings.PLAY_AREA[0] - radius:
                return True
            if not radius <= head[1] < settings.PLAY_AREA[1] - radius:
                return True
            return False

        def check_snake_collisions(snake: Snake) -> bool:
            """ Check snake to snake collisions """
            for col in self.get_colliders(snake.head()):
                if not snake.is_own_head(col):
                    return True
            return False

        for snake in snakes:
            if check_border_collisions(snake):
                snake.kill()
            elif check_snake_collisions(snake):
                snake.kill()


class PizzaManager:
    """ Pizza generator and eating logic """
    def __init__(self, pizzas: List[Pizza]) -> None:
        self.next_pizza_id = 0
        self.pizzas = pizzas
        self.new_pizzas: List[Pizza] = []
        self.removed_pizzas: List[int] = []

    def generate_pizza(self) -> None:
        """ Generate a new pizza at random location """
        radius = random.randrange(settings.PIZZA_RADIUS_RANGE[0],
                                  settings.PIZZA_RADIUS_RANGE[1] + 1)
        x = radius + random.randrange(settings.PLAY_AREA[0] - 2 * radius)
        y = radius + random.randrange(settings.PLAY_AREA[1] - 2 * radius)
        self.next_pizza_id += 1
        pizza = Pizza(x, y, radius, self.next_pizza_id)
        self.new_pizzas.append(pizza)
        self.pizzas.append(pizza)

    def update_pizzas(self) -> None:
        """ Remove eaten pizzas, bake new ones to replace them """
        for pizza in list(self.pizzas):
            if not pizza.still_good:
                self.removed_pizzas.append(pizza.pizza_id)
                self.pizzas.remove(pizza)

        while len(self.pizzas) < settings.PIZZA_NUM:
            self.generate_pizza()

    def eat(self, snake: Snake) -> None:
        """ Check if a snake is close enough to eat some pizzas.
            Fill the belly of the snake with eaten pizzas and make
            it grow. Multiple snakes can eat the same pizza before
            the eaten pizzas are removed at call to 'update'."""
        position = snake.head()
        for pizza in self.pizzas:
            if pizza.is_close(position, settings.SNAKE_RADIUS):
                snake.grow(pizza.radius)
                pizza.mark_eaten()

    def clear_tick_changes(self) -> None:
        """ Clear what pizzas were created or remove this frame """
        self.new_pizzas.clear()
        self.removed_pizzas.clear()


class GameState:
    """ A complete collections of the game state.
        Contains the state of Pizzas and Snakes """
    def __init__(self) -> None:
        self.collisions = CollisionManager()
        self.snakes: List[Snake] = []
        self.pizzas: List[Pizza] = []

        # TODO move to server game logic
        self.pizza_manager = PizzaManager(self.pizzas)

    def remove_pizza(self, pizza: Pizza) -> None:
        """ remove a pizza by reference """
        self.pizzas.remove(pizza)

    def remove_pizza_by_id(self, pizza_id: int) -> None:
        """ remove a pizza by id """
        for pizza in self.pizzas:
            if pizza.pizza_id == pizza_id:
                self.pizzas.remove(pizza)
                break

    def remove_pizzas(self, removed_pizzas: List[int]) -> None:
        """ Remove all provided pizza_ids from active pizzas """
        for pizza_id in removed_pizzas:
            self.remove_pizza_by_id(pizza_id)
