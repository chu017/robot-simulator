"""
A* pathfinding for the robot simulator.
Input: start (row,col), goal (row,col), grid.
Output: list of moves [UP, RIGHT, ...] or [] if no path.
"""
import heapq
from typing import List, Tuple
import numpy as np

from utils import (
    DIRECTIONS,
    direction_to_name,
    is_valid_cell,
    manhattan,
    OBSTACLE,
    ROBOT,
    TASK,
    EMPTY,
)


def _walkable(grid: np.ndarray, row: int, col: int, start: Tuple[int, int]) -> bool:
    """Cell is walkable if empty, task, or is the start (robot) cell."""
    if not is_valid_cell(grid, row, col):
        return False
    v = grid[row, col]
    if v == OBSTACLE:
        return False
    if (row, col) == start:
        return True
    return v in (EMPTY, TASK, ROBOT)


def astar(
    grid: np.ndarray,
    start: Tuple[int, int],
    goal: Tuple[int, int],
) -> List[Tuple[int, int]]:
    """
    A* from start to goal on grid.
    Returns list of (dy, dx) moves, e.g. [(-1,0), (0,1)] for UP then RIGHT.
    """
    if start == goal:
        return []
    if not _walkable(grid, goal[0], goal[1], start):
        return []

    # priority, counter, (row, col), path_so_far
    counter = 0
    open_set = [(manhattan(start, goal), counter, start, [])]
    heapq.heapify(open_set)
    seen = {start}

    while open_set:
        _, _, (r, c), path = heapq.heappop(open_set)
        if (r, c) == goal:
            return path
        for dy, dx in DIRECTIONS:
            nr, nc = r + dy, c + dx
            if (nr, nc) in seen:
                continue
            if not _walkable(grid, nr, nc, start):
                continue
            seen.add((nr, nc))
            new_path = path + [(dy, dx)]
            g = len(new_path)
            h = manhattan((nr, nc), goal)
            heapq.heappush(open_set, (g + h, counter, (nr, nc), new_path))
            counter += 1
    return []


def astar_moves_as_names(grid: np.ndarray, start: Tuple[int, int], goal: Tuple[int, int]) -> List[str]:
    """Same as astar but returns move names: [\"UP\", \"RIGHT\", ...]."""
    path = astar(grid, start, goal)
    return [direction_to_name(dy, dx) for dy, dx in path]
