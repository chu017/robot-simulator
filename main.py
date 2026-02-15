"""
AI-Powered Robot Simulator – main entry and pygame visualization.
"""
from __future__ import annotations
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
from controller import get_path_cells, is_path_blocked, replan_path
import time

# Pygame
CELL_SIZE = 40
GRID_MARGIN = 2
HEADER_H = 80
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


def pixel_to_cell(px: int, py: int, grid_rows: int, grid_cols: int) -> tuple[int, int] | None:
    """Convert screen (px, py) to grid (row, col) or None if outside grid."""
    if px < GRID_MARGIN or py < HEADER_H + GRID_MARGIN:
        return None
    c = (px - GRID_MARGIN) // (CELL_SIZE + GRID_MARGIN)
    r = (py - HEADER_H - GRID_MARGIN) // (CELL_SIZE + GRID_MARGIN)
    if 0 <= r < grid_rows and 0 <= c < grid_cols:
        return (r, c)
    return None


def _draw_robot(surface: pygame.Surface, rect: pygame.Rect, facing: tuple[int, int]) -> None:
    """Draw a simple robot shape with a front direction (body circle + direction wedge)."""
    cx = rect.centerx
    cy = rect.centery
    r = min(rect.w, rect.h) // 3
    pygame.draw.circle(surface, (50, 100, 200), (cx, cy), r)
    pygame.draw.circle(surface, (30, 70, 160), (cx, cy), r, 2)
    # Direction wedge (triangle "front")
    dy, dx = facing
    if (dy, dx) == (0, 0):
        dy, dx = 0, 1
    # Nudge the wedge outward from center
    tip_x = cx + dx * (r + 4)
    tip_y = cy + dy * (r + 4)
    # Perpendicular for base of triangle
    perp_x = -dy * 5
    perp_y = dx * 5
    base1 = (cx + dx * r * 0.3 + perp_x, cy + dy * r * 0.3 + perp_y)
    base2 = (cx + dx * r * 0.3 - perp_x, cy + dy * r * 0.3 - perp_y)
    pygame.draw.polygon(surface, (80, 140, 255), [base1, base2, (tip_x, tip_y)])
    pygame.draw.polygon(surface, (30, 70, 160), [base1, base2, (tip_x, tip_y)], 1)


def _waypoint_number(task_order: list, pos: tuple[int, int]) -> int | None:
    """Return 1-based waypoint index for this task position, or None."""
    if pos not in task_order:
        return None
    return task_order.index(pos) + 1


def draw_grid(
    surface: pygame.Surface,
    grid: np.ndarray,
    completed_tasks: set,
    path_cells: list | None = None,
    task_order: list | None = None,
    robot_pos: tuple[int, int] | None = None,
    robot_facing: tuple[int, int] = (0, 1),
    path_replan_flash: bool = False,
) -> None:
    surface.fill(COLORS["bg"])
    rows, cols = grid.shape
    path_set = set(path_cells) if path_cells else set()
    task_order = task_order or []
    path_color = (255, 220, 100) if path_replan_flash else (200, 220, 255)
    for r in range(rows):
        for c in range(cols):
            rect = cell_to_rect(r, c)
            val = grid[r, c]
            if val == OBSTACLE:
                color = COLORS["obstacle"]
                pygame.draw.rect(surface, color, rect)
            elif val == ROBOT:
                pygame.draw.rect(surface, COLORS["empty"], rect)
                _draw_robot(surface, rect, robot_facing)
            elif (r, c) in completed_tasks:
                color = COLORS["task_done"]
                pygame.draw.rect(surface, color, rect)
                num = _waypoint_number(task_order, (r, c))
                if num is not None:
                    font = pygame.font.Font(None, 24)
                    img = font.render(str(num), True, (100, 100, 110))
                    surface.blit(img, (rect.centerx - img.get_width() // 2, rect.centery - img.get_height() // 2))
            elif val == TASK:
                color = COLORS["task"]
                pygame.draw.rect(surface, color, rect)
                num = _waypoint_number(task_order, (r, c))
                if num is not None:
                    font = pygame.font.Font(None, 26)
                    img = font.render(str(num), True, (255, 255, 255))
                    surface.blit(img, (rect.centerx - img.get_width() // 2, rect.centery - img.get_height() // 2))
            elif (r, c) in path_set:
                pygame.draw.rect(surface, path_color, rect)
            else:
                color = COLORS["empty"]
                pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, (200, 200, 210), rect, 1)


def draw_header(
    surface: pygame.Surface,
    steps: int,
    tasks_done: int,
    total_tasks: int,
    current_goal: int,
    speed_label: str,
    status_msg: str,
    font: pygame.font.Font,
) -> None:
    header = pygame.Rect(0, 0, surface.get_width(), HEADER_H)
    pygame.draw.rect(surface, (255, 255, 255), header)
    pygame.draw.line(surface, (220, 220, 230), (0, HEADER_H - 1), (surface.get_width(), HEADER_H - 1), 2)
    y_center = 22
    texts = [
        f"Steps: {steps}",
        f"Waypoints: {tasks_done}/{total_tasks}",
        f"Goal: {current_goal}/{total_tasks}" if total_tasks else "",
        f"Speed: {speed_label}",
    ]
    x = 16
    for i, t in enumerate(texts):
        if not t:
            continue
        color = COLORS["text"] if i < 3 else COLORS["text_secondary"]
        img = font.render(t, True, color)
        surface.blit(img, (x, y_center - img.get_height() // 2))
        x += 120 if i < 4 else 200
    # Robot status line
    status_color = (40, 120, 60) if "complete" in status_msg.lower() else COLORS["text_secondary"]
    status_img = font.render(status_msg, True, status_color)
    surface.blit(status_img, (16, 38))
    # Controls hint
    ctrl_img = font.render("Space=Run  S=Step  1/2/3  R=Reset  Q=Quit  |  Click/Drag: edit obstacles", True, COLORS["text_secondary"])
    surface.blit(ctrl_img, (16, 56))


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
    frame_delay = 3  # steps per tick when auto; lower = faster
    speed_labels = {6: "1-Slow", 3: "2-Med", 1: "3-Fast"}
    frame_count = 0
    robot_facing = (0, 1)  # last move direction; (0,1) = right
    replan_flash_until = 0.0  # time until path stops showing yellow
    # Mouse: obstacle edit
    mouse_down_cell = None
    mouse_down_was_obstacle = False

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                cell = pixel_to_cell(event.pos[0], event.pos[1], grid_rows, grid_cols)
                if cell is not None:
                    mouse_down_cell = cell
                    mouse_down_was_obstacle = grid[cell[0], cell[1]] == OBSTACLE
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if mouse_down_cell is not None:
                    cell = pixel_to_cell(event.pos[0], event.pos[1], grid_rows, grid_cols)
                    if cell is not None:
                        if cell == mouse_down_cell:
                            # Toggle: empty <-> obstacle (do not put obstacle on robot/task)
                            if grid[cell[0], cell[1]] == OBSTACLE:
                                grid[cell[0], cell[1]] = EMPTY
                            elif grid[cell[0], cell[1]] == EMPTY:
                                grid[cell[0], cell[1]] = OBSTACLE
                        else:
                            # Drag: move obstacle from mouse_down_cell to cell
                            if mouse_down_was_obstacle and grid[cell[0], cell[1]] == EMPTY:
                                grid[mouse_down_cell[0], mouse_down_cell[1]] = EMPTY
                                grid[cell[0], cell[1]] = OBSTACLE
                    mouse_down_cell = None
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
                if event.key == pygame.K_1:
                    frame_delay = 6
                if event.key == pygame.K_2:
                    frame_delay = 3
                if event.key == pygame.K_3:
                    frame_delay = 1

        do_one_step = step_once or (auto_advance and frame_count % frame_delay == 0 and move_queue)
        if step_once:
            step_once = False

        # Path validity: before moving, check if current path is blocked; replan if so
        rp = find_robot(grid)
        path_cells = get_path_cells(rp, move_queue) if (rp is not None and move_queue) else []
        if do_one_step and move_queue and rp is not None:
            if is_path_blocked(path_cells, grid):
                goal = task_order[current_goal_index] if current_goal_index < len(task_order) else None
                if goal is not None and goal not in completed_tasks:
                    new_path = replan_path(rp, goal, grid)
                    move_queue = new_path
                    replan_flash_until = time.time() + 0.5
                    if not move_queue:
                        refill_moves()
                path_cells = get_path_cells(rp, move_queue) if move_queue else []

        if do_one_step and move_queue:
            dy, dx = move_queue.pop(0)
            robot_facing = (dy, dx)
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

        # Path preview cells for drawing (current state after move)
        rp = find_robot(grid)
        path_cells = get_path_cells(rp, move_queue) if (rp is not None and move_queue) else []

        current_goal = current_goal_index + 1 if current_goal_index < len(task_order) else len(task_positions)
        path_replan_flash = time.time() < replan_flash_until
        # Robot status message
        if path_replan_flash:
            status_msg = "Replanning path..."
        elif len(completed_tasks) >= len(task_positions) and len(task_positions) > 0:
            status_msg = "Mission complete."
        elif move_queue:
            status_msg = f"Navigating to waypoint {current_goal}..."
        else:
            status_msg = "Idle."
        rp = find_robot(grid)
        draw_grid(
            screen,
            grid,
            completed_tasks,
            path_cells=path_cells,
            task_order=task_order,
            robot_pos=rp,
            robot_facing=robot_facing,
            path_replan_flash=path_replan_flash,
        )
        draw_header(
            screen,
            steps,
            len(completed_tasks),
            len(task_positions),
            current_goal,
            speed_labels.get(frame_delay, "2-Med"),
            status_msg,
            font,
        )
        pygame.display.flip()
        clock.tick(40)


if __name__ == "__main__":
    # Use "heuristic" for instant start; "auto" tries Gemini/OpenAI (slower, needs API keys)
    run_simulation(seed=42, ai_prefer="heuristic")
