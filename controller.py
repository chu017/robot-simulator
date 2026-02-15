"""
Controller layer: path validity check and replanning.
Tracks current path, detects invalid path (blocked by obstacle), triggers replan.
"""
from __future__ import annotations
from typing import List, Tuple
import numpy as np

from pathfinding import astar
from utils import OBSTACLE


def get_path_cells(
    robot_pos: Tuple[int, int],
    move_queue: List[Tuple[int, int]],
) -> List[Tuple[int, int]]:
    """Return list of (row, col) cells the path visits (robot pos + each step)."""
    cells = []
    r, c = robot_pos
    cells.append((r, c))
    for dy, dx in move_queue:
        r, c = r + dy, c + dx
        cells.append((r, c))
    return cells


def is_path_blocked(path_cells: List[Tuple[int, int]], grid: np.ndarray) -> bool:
    """
    Return True if any node on the path is now an obstacle (path invalid).
    """
    for (row, col) in path_cells:
        if 0 <= row < grid.shape[0] and 0 <= col < grid.shape[1]:
            if grid[row, col] == OBSTACLE:
                return True
    return False


def replan_path(
    robot_pos: Tuple[int, int],
    goal: Tuple[int, int],
    grid: np.ndarray,
) -> List[Tuple[int, int]]:
    """
    Replan from robot to goal using A*. Returns new list of (dy, dx) moves.
    """
    return astar(grid, robot_pos, goal)
