"""
AI-Powered Robot Simulator – main entry and pygame visualization.
"""
import sys
import pygame
import numpy as np

from utils import (
    EMPTY,
    OBSTACLE,
    ROBOT,
    TASK,
    init_simulation,
    find_robot,
    find_tasks,
    place_robot,
    is_walkable,
    DIRECTIONS,
    name_to_direction,
)
from pathfinding import astar
from ai_task import get_optimal_task_order

# Pygame
CELL_SIZE = 40
GRID_MARGIN = 2
HEADER_H = 56
COLORS = {
    "empty": (240, 240, 245),
    "obstacle": (30, 30, 35),
    "robot": (60, 120, 220),
    "task": (50, 180, 100),
    "task_done": (180, 180, 190),
    "bg": (250, 250, 252),
    "text": (40, 40, 50),
    "text_secondary": (100, 100, 110),
}


def cell_to_rect(row: int, col: int) -> pygame.Rect:
    x = col * (CELL_SIZE + GRID_MARGIN) + GRID_MARGIN
    y = HEADER_H + row * (CELL_SIZE + GRID_MARGIN) + GRID_MARGIN
    return pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)


def draw_grid(surface: pygame.Surface, grid: np.ndarray, completed_tasks: set) -> None:
    surface.fill(COLORS["bg"])
    rows, cols = grid.shape
    for r in range(rows):
        for c in range(cols):
            rect = cell_to_rect(r, c)
            val = grid[r, c]
            if val == OBSTACLE:
                color = COLORS["obstacle"]
            elif val == ROBOT:
                color = COLORS["robot"]
            elif (r, c) in completed_tasks:
                color = COLORS["task_done"]
            elif val == TASK:
                color = COLORS["task"]
            else:
                color = COLORS["empty"]
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, (200, 200, 210), rect, 1)


def draw_header(
    surface: pygame.Surface,
    steps: int,
    tasks_done: int,
    total_tasks: int,
    font: pygame.font.Font,
) -> None:
    header = pygame.Rect(0, 0, surface.get_width(), HEADER_H)
    pygame.draw.rect(surface, (255, 255, 255), header)
    pygame.draw.line(surface, (220, 220, 230), (0, HEADER_H - 1), (surface.get_width(), HEADER_H - 1), 2)
    y_center = HEADER_H // 2
    texts = [
        f"Steps: {steps}",
        f"Tasks: {tasks_done}/{total_tasks}",
        "Space=Auto  S=Step  R=Reset  Q=Quit",
    ]
    x = 20
    for i, t in enumerate(texts):
        color = COLORS["text"] if i < 2 else COLORS["text_secondary"]
        img = font.render(t, True, color)
        surface.blit(img, (x, y_center - img.get_height() // 2))
        x += 180 if i < 2 else 220


def run_simulation(
    grid_rows: int = 12,
    grid_cols: int = 16,
    num_tasks: int = 3,
    num_obstacles: int = 15,
    seed: int | None = None,
    ai_prefer: str = "auto",
) -> None:
    grid, robot_pos, task_positions = init_simulation(
        rows=grid_rows,
        cols=grid_cols,
        num_tasks=num_tasks,
        num_obstacles=num_obstacles,
        seed=seed,
    )
    completed_tasks = set()
    steps = 0
    # Plan task order once at start
    task_order = get_optimal_task_order(robot_pos, task_positions, prefer=ai_prefer)
    # Build full move queue: for each task, A* path then pop task when reached
    move_queue = []
    current_goal_index = 0

    def refill_moves() -> bool:
        nonlocal current_goal_index, move_queue
        while current_goal_index < len(task_order):
            goal = task_order[current_goal_index]
            if goal in completed_tasks:
                current_goal_index += 1
                continue
            rp = find_robot(grid)
            if rp is None:
                return False
            path = astar(grid, rp, goal)
            if not path:
                current_goal_index += 1
                continue
            move_queue = path
            return True
        return False

    refill_moves()

    pygame.init()
    font = pygame.font.Font(None, 28)
    width = grid_cols * (CELL_SIZE + GRID_MARGIN) + GRID_MARGIN * 2
    height = HEADER_H + grid_rows * (CELL_SIZE + GRID_MARGIN) + GRID_MARGIN * 2
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("AI Robot Simulator")
    clock = pygame.time.Clock()

    auto_advance = False
    step_once = False
    frame_delay = 8
    frame_count = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit(0)
                if event.key == pygame.K_r:
                    pygame.quit()
                    run_simulation(
                        grid_rows=grid_rows,
                        grid_cols=grid_cols,
                        num_tasks=num_tasks,
                        num_obstacles=num_obstacles,
                        seed=(seed + 1) if seed is not None else None,
                        ai_prefer=ai_prefer,
                    )
                    return
                if event.key == pygame.K_SPACE:
                    auto_advance = not auto_advance
                if event.key == pygame.K_s:
                    step_once = True

        do_one_step = step_once or (auto_advance and frame_count % frame_delay == 0 and move_queue)
        if step_once:
            step_once = False

        if do_one_step and move_queue:
            dy, dx = move_queue.pop(0)
            rp = find_robot(grid)
            if rp is not None:
                r, c = rp
                nr, nc = r + dy, c + dx
                if is_walkable(grid, nr, nc, ignore_robot=True):
                    grid[r, c] = EMPTY
                    if grid[nr, nc] == TASK:
                        completed_tasks.add((nr, nc))
                        grid[nr, nc] = EMPTY
                    place_robot(grid, nr, nc)
                    steps += 1
            if not move_queue:
                refill_moves()
        frame_count += 1

        draw_grid(screen, grid, completed_tasks)
        draw_header(screen, steps, len(completed_tasks), len(task_positions), font)
        pygame.display.flip()
        clock.tick(40)


if __name__ == "__main__":
    run_simulation(seed=42, ai_prefer="auto")
