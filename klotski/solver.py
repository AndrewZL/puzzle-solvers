from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from heapq import heappop, heappush
from typing import List, Optional, Set, Tuple


class PieceColor(Enum):
    RED = "#FF6F61"
    GRAY = "#CFCFC4"


class Direction(Enum):
    RIGHT = 1
    LEFT = 2
    UP = 3
    DOWN = 4


@dataclass
class Piece:
    is_goal: bool
    is_single: bool
    coord_x: int
    coord_y: int
    size: Tuple[int, int]
    color: str

    def move(self, direction: Direction) -> None:
        if direction == Direction.RIGHT:
            self.coord_x += 1
        elif direction == Direction.LEFT:
            self.coord_x -= 1
        elif direction == Direction.UP:
            self.coord_y -= 1
        elif direction == Direction.DOWN:
            self.coord_y += 1
        else:
            raise ValueError(f"Invalid direction: {direction}")


@dataclass
class Board:
    pieces: List[Piece]
    width: int
    height: int
    grid: List[List[str]] = field(init=False)

    def __post_init__(self) -> None:
        self.construct_grid()

    def construct_grid(self) -> None:
        self.grid = [["." for _ in range(self.width)] for _ in range(self.height)]

        for piece in self.pieces:
            if piece.is_goal:
                self.grid[piece.coord_y][piece.coord_x] = "1"
                self.grid[piece.coord_y][piece.coord_x + 1] = "1"
                self.grid[piece.coord_y + 1][piece.coord_x] = "1"
                self.grid[piece.coord_y + 1][piece.coord_x + 1] = "1"
            elif piece.is_single:
                self.grid[piece.coord_y][piece.coord_x] = "2"
            else:
                if piece.size == (1, 2):
                    self.grid[piece.coord_y][piece.coord_x] = "<"
                    self.grid[piece.coord_y][piece.coord_x + 1] = ">"
                elif piece.size == (2, 1):
                    self.grid[piece.coord_y][piece.coord_x] = "^"
                    self.grid[piece.coord_y + 1][piece.coord_x] = "v"

    def display(self) -> None:
        """Print out the current board."""
        for line in self.grid:
            print("".join(line))

    def find_empty(self) -> List[Tuple[int, int]]:
        """Find all empty coordinates on the board."""
        empty_coords = []
        for i in range(len(self.grid)):
            for j in range(len(self.grid[0])):
                if self.grid[i][j] == ".":
                    empty_coords.append((i, j))
        return empty_coords


@dataclass(order=True)
class State:
    """
    State class wrapping a Board with some extra current state information.
    Note that State and Board are different. Board has the locations of the pieces.
    State has a Board and some extra information that is relevant to the search:
    heuristic function, f value, current depth and parent.
    """

    board: Board = field(compare=False)
    f: int
    depth: int
    parent: Optional["State"] = field(compare=False, default=None)

    def __post_init__(self) -> None:
        self.id = hash(str(self.board.grid))


def read_from_file(filename: str) -> Board:
    """Read the board configuration from a file."""
    with open(filename, "r") as puzzle_file:
        y = 0
        pieces = []
        g_found = False

        for line in puzzle_file:
            for x, ch in enumerate(line.strip()):
                if ch == "^":  # found vertical piece
                    pieces.append(Piece(False, False, x, y, (2, 1), PieceColor.GRAY.value))
                elif ch == "<":  # found horizontal piece
                    pieces.append(Piece(False, False, x, y, (1, 2), PieceColor.GRAY.value))
                elif ch == "2":
                    pieces.append(Piece(False, True, x, y, (1, 1), PieceColor.GRAY.value))
                elif ch == "1":
                    if not g_found:
                        pieces.append(Piece(True, False, x, y, (2, 2), PieceColor.RED.value))
                        g_found = True
            y += 1

    width = max(piece.coord_x + piece.size[1] for piece in pieces)
    height = max(piece.coord_y + piece.size[0] for piece in pieces)
    return Board(pieces, width, height)


def write_to_file(filename: str, solution: List[State]) -> None:
    """Write the solution to a given file."""
    with open(filename, "w") as f:
        for state in solution:
            for line in state.board.grid:
                f.write("".join(line) + "\n")
            f.write("\n")


def is_goal_state(b: Board) -> bool:
    """Check if the board is in a goal state."""
    for piece in b.pieces:
        if piece.is_goal and piece.coord_x == 1 and piece.coord_y == 3:
            return True
    return False


def adjacent_empties(empty_coords: List[Tuple[int, int]]) -> Optional[str]:
    """Determine if the empty coordinates are adjacent."""
    if empty_coords[0][0] == empty_coords[1][0] and abs(empty_coords[0][1] - empty_coords[1][1]) == 1:
        return "hor"
    elif empty_coords[0][1] == empty_coords[1][1] and abs(empty_coords[0][0] - empty_coords[1][0]) == 1:
        return "ver"
    return None


def gen_state(idx: int, state_orig: State, direction: Direction) -> State:
    """Generate a new state by moving a piece in the given direction."""
    piece_list = deepcopy(state_orig.board.pieces)
    piece_list[idx].move(direction)
    board = Board(piece_list, state_orig.board.width, state_orig.board.height)
    next_state = State(board, state_orig.depth + manhattan(board), state_orig.depth + 1, state_orig)
    return next_state


def generate_successors(state: State) -> List[State]:
    """Generate all possible successor states from the current state."""
    successors = []
    empty_coords = state.board.find_empty()
    empty_config = adjacent_empties(empty_coords)
    for idx, piece in enumerate(state.board.pieces):
        if piece.is_goal:
            if not empty_config:
                continue
            if empty_config == "hor":
                if piece.coord_y - 1 == empty_coords[0][0] and piece.coord_x == empty_coords[0][1]:
                    successors.append(gen_state(idx, state, Direction.UP))
                elif piece.coord_y + 2 == empty_coords[0][0] and piece.coord_x == empty_coords[0][1]:
                    successors.append(gen_state(idx, state, Direction.DOWN))
            else:  # empty_config == 'ver'
                if piece.coord_x - 1 == empty_coords[0][1] and piece.coord_y == empty_coords[0][0]:
                    successors.append(gen_state(idx, state, Direction.LEFT))
                elif piece.coord_x + 2 == empty_coords[0][1] and piece.coord_y == empty_coords[0][0]:
                    successors.append(gen_state(idx, state, Direction.RIGHT))
        elif piece.is_single:
            if (
                piece.coord_x - 1 == empty_coords[0][1]
                and piece.coord_y == empty_coords[0][0]
                or piece.coord_x - 1 == empty_coords[1][1]
                and piece.coord_y == empty_coords[1][0]
            ):
                successors.append(gen_state(idx, state, Direction.LEFT))
            if (
                piece.coord_x + 1 == empty_coords[0][1]
                and piece.coord_y == empty_coords[0][0]
                or piece.coord_x + 1 == empty_coords[1][1]
                and piece.coord_y == empty_coords[1][0]
            ):
                successors.append(gen_state(idx, state, Direction.RIGHT))
            if (
                piece.coord_y - 1 == empty_coords[0][0]
                and piece.coord_x == empty_coords[0][1]
                or piece.coord_y - 1 == empty_coords[1][0]
                and piece.coord_x == empty_coords[1][1]
            ):
                successors.append(gen_state(idx, state, Direction.UP))
            if (
                piece.coord_y + 1 == empty_coords[0][0]
                and piece.coord_x == empty_coords[0][1]
                or piece.coord_y + 1 == empty_coords[1][0]
                and piece.coord_x == empty_coords[1][1]
            ):
                successors.append(gen_state(idx, state, Direction.DOWN))
        elif piece.size == (2, 1):
            if (
                piece.coord_y - 1 == empty_coords[0][0]
                and piece.coord_x == empty_coords[0][1]
                or piece.coord_y - 1 == empty_coords[1][0]
                and piece.coord_x == empty_coords[1][1]
            ):
                successors.append(gen_state(idx, state, Direction.UP))
            if (
                piece.coord_y + 2 == empty_coords[0][0]
                and piece.coord_x == empty_coords[0][1]
                or piece.coord_y + 2 == empty_coords[1][0]
                and piece.coord_x == empty_coords[1][1]
            ):
                successors.append(gen_state(idx, state, Direction.DOWN))
            if empty_config == "ver":
                if piece.coord_x - 1 == empty_coords[0][1] and piece.coord_y == empty_coords[0][0]:
                    successors.append(gen_state(idx, state, Direction.LEFT))
                if piece.coord_x + 1 == empty_coords[0][1] and piece.coord_y == empty_coords[0][0]:
                    successors.append(gen_state(idx, state, Direction.RIGHT))
        else:  # piece.size == (1, 2)
            if (
                piece.coord_x - 1 == empty_coords[0][1]
                and piece.coord_y == empty_coords[0][0]
                or piece.coord_x - 1 == empty_coords[1][1]
                and piece.coord_y == empty_coords[1][0]
            ):
                successors.append(gen_state(idx, state, Direction.LEFT))
            if (
                piece.coord_x + 2 == empty_coords[0][1]
                and piece.coord_y == empty_coords[0][0]
                or piece.coord_x + 2 == empty_coords[1][1]
                and piece.coord_y == empty_coords[1][0]
            ):
                successors.append(gen_state(idx, state, Direction.RIGHT))
            if empty_config == "hor":
                if piece.coord_y - 1 == empty_coords[0][0] and piece.coord_x == empty_coords[0][1]:
                    successors.append(gen_state(idx, state, Direction.UP))
                if piece.coord_y + 1 == empty_coords[0][0] and piece.coord_x == empty_coords[0][1]:
                    successors.append(gen_state(idx, state, Direction.DOWN))
    return successors


def get_solution(goal_state: State) -> List[State]:
    """Retrieve the solution path from the goal state."""
    sol = []
    while goal_state.parent is not None:
        sol.append(goal_state)
        goal_state = goal_state.parent
    sol.append(goal_state)
    return sol[::-1]


def hash_board(board: Board) -> str:
    """Generate a hash for the board."""
    return str(board.grid)


def dfs(init_state: State) -> Optional[List[State]]:
    """Depth-First Search algorithm."""
    stack = [init_state]
    explored = set()

    while stack:
        state = stack.pop()
        if is_goal_state(state.board):
            return get_solution(state)
        board_hash = hash_board(state.board)
        if board_hash not in explored:
            explored.add(board_hash)
            successors = generate_successors(state)
            stack.extend(successors)
    return None


def a_star(initial_state: State) -> Optional[List[State]]:
    """A* search algorithm for solving the puzzle."""
    explored: Set[str] = set()
    frontier: List[Tuple[int, int, State]] = []
    heappush(frontier, (initial_state.f, id(initial_state), initial_state))

    while frontier:
        _, _, current_state = heappop(frontier)

        if is_goal_state(current_state.board):
            return get_solution(current_state)

        board_hash = hash_board(current_state.board)
        if board_hash not in explored:
            explored.add(board_hash)
            for successor in generate_successors(current_state):
                heappush(frontier, (successor.f, id(successor), successor))

    return None


def manhattan(board: Board) -> int:
    """Calculate the Manhattan distance heuristic for the board."""
    for piece in board.pieces:
        if piece.is_goal:
            return abs(piece.coord_x - 1) + abs(piece.coord_y - 3)
    raise Exception("No goal piece found!")
