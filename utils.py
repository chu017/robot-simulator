"""
Grid environment utilities for the robot simulator.
Cell types: 0=empty, 1=obstacle, 2=robot, 3=task
"""
import numpy as np
import random
from typing import List, Tuple

# Cell type constants
EMPTY = 0
OBSTACLE = 1
ROBOT = 2
TASK = 3

# Movement directions: (dy, dx) for row, col
UP = (-1, 0)
DOWN = (1, 0)
LEFT = (0, -1)
RIGHT = (0, 1)
DIRECTIONS = [UP, DOWN, LEFT, RIGHT]
DIRECTION_NAMES = ["UP", "DOWN", "LEFT", "RIGHT"]


def direction_to_name(dy: int, dx: int) -> str:
    """Convert (dy, dx) to name."""
    for (ddy, ddx), name in zip(DIRECTIONS, DIRECTION_NAMES):
        if (dy, dx) == (ddy, ddx):
            return name
    return "UNKNOWN"


def name_to_direction(name: str) -> Tuple[int, int]:
    """Convert name to (dy, dx)."""
    name = name.strip().upper()
    for n, (dy, dx) in zip(DIRECTION_NAMES, DIRECTIONS):
        if n == name:
            return (dy, dx)
    return (0, 0)


def create_grid(rows: int, cols: int) -> np.ndarray:
    """Create an empty grid (all EMPTY)."""
    return np.zeros((rows, cols), dtype=np.int32)


def add_obstacles(grid: np.ndarray, count: int, exclude: List[Tuple[int, int]]) -> None:
    """Add random obstacles; exclude given (row, col) positions."""
    rows, cols = grid.shape
    cells = [(r, c) for r in range(rows) for c in range(cols) if (r, c) not in exclude]
    if count >= len(cells):
        count = max(0, len(cells) - 1)
    for (r, c) in random.sample(cells, count):
        grid[r, c] = OBSTACLE


def place_robot(grid: np.ndarray, row: int, col: int) -> None:
    """Set cell to robot (call after clearing previous robot cell if moving)."""
    grid[row, col] = ROBOT


def place_task(grid: np.ndarray, row: int, col: int) -> None:
    """Set cell to task."""
    grid[row, col] = TASK


def find_robot(grid: np.ndarray) -> Tuple[int, int] | None:
    """Return (row, col) of robot or None."""
    ys, xs = np.where(grid == ROBOT)
    if len(ys) == 0:
        return None
    return (int(ys[0]), int(xs[0]))


def find_tasks(grid: np.ndarray) -> List[Tuple[int, int]]:
    """Return list of (row, col) for all task cells."""
    ys, xs = np.where(grid == TASK)
    return list(zip(ys.tolist(), xs.tolist()))


def is_valid_cell(grid: np.ndarray, row: int, col: int) -> bool:
    """True if (row, col) is within bounds."""
    rows, cols = grid.shape
    return 0 <= row < rows and 0 <= col < cols


def is_walkable(grid: np.ndarray, row: int, col: int, ignore_robot: bool = False) -> bool:
    """True if cell can be moved into (empty, task, or robot if ignore_robot)."""
    if not is_valid_cell(grid, row, col):
        return False
    v = grid[row, col]
    if v == OBSTACLE:
        return False
    if v == ROBOT and not ignore_robot:
        return False
    return True


def get_neighbors(grid: np.ndarray, row: int, col: int, walkable_only: bool = True) -> List[Tuple[int, int]]:
    """Return neighboring (row, col) cells. If walkable_only, exclude obstacles."""
    out = []
    for dy, dx in DIRECTIONS:
        r, c = row + dy, col + dx
        if not is_valid_cell(grid, r, c):
            continue
        if walkable_only and grid[r, c] == OBSTACLE:
            continue
        out.append((r, c))
    return out


def manhattan(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    """Manhattan distance between (r1,c1) and (r2,c2)."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def init_simulation(
    rows: int = 12,
    cols: int = 16,
    num_tasks: int = 3,
    num_obstacles: int = 15,
    seed: int | None = None,
) -> Tuple[np.ndarray, Tuple[int, int], List[Tuple[int, int]]]:
    """
    Create grid with robot at start, tasks, and obstacles.
    Returns (grid, robot_pos, task_positions).
    """
    if seed is not None:
        random.seed(seed)
    grid = create_grid(rows, cols)
    robot_pos = (0, 0)
    place_robot(grid, *robot_pos)
    exclude = [robot_pos]
    task_positions = []
    for _ in range(num_tasks):
        cells = [(r, c) for r in range(rows) for c in range(cols) if (r, c) not in exclude and grid[r, c] == EMPTY]
        if not cells:
            break
        r, c = random.choice(cells)
        place_task(grid, r, c)
        task_positions.append((r, c))
        exclude.append((r, c))
    add_obstacles(grid, num_obstacles, exclude)
    return grid, robot_pos, task_positions
