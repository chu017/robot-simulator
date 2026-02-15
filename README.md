# AI-Powered Robot Simulator

A 2D grid robot simulator with A* pathfinding and AI-optimized task ordering. Built for a 3–4 hour hackathon.

## Features

- **2D Grid Environment**: Numpy-based grid with obstacles, robot, and tasks
- **A* Pathfinding**: Optimal path from robot to any goal
- **AI Task Planning**: Gemini / OpenAI or nearest-task-first heuristic for task order
- **Pygame Visualization**: Animated robot movement, colored cells, optional stats overlay

## How to run

**1. Open the project folder (e.g. in terminal):**
```bash
cd /path/to/robot-simulator   # or your worktree path, e.g. .../robot-simulator/ahb
```

**2. Create a virtual environment and install dependencies:**

Run these as **separate** commands (do not type `then` between them; the shell will not run the second command):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows use `.venv\Scripts\activate` instead of `source .venv/bin/activate`. Or as a single line (Mac/Linux): `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`

**3. Run the simulator:**
```bash
python main.py
```

**4. In the window:** Press **Space** to auto-run, **S** to step once, **R** to reset, **Q** to quit.

Set `OPENAI_API_KEY` or `GOOGLE_API_KEY` in the environment for AI task ordering; otherwise the simulator uses the nearest-task-first heuristic.

## Project Structure

- `main.py` – Entry point, pygame loop, animation, dashboard
- `pathfinding.py` – A* algorithm
- `ai_task.py` – AI/heuristic task order planning
- `utils.py` – Grid representation, cell types, helpers

## Controls

- **Space**: Toggle auto-run (robot keeps moving)
- **S**: Single step (one cell)
- **1 / 2 / 3**: Speed when auto-running (slow / medium / fast)
- **R**: Reset / new random scenario
- **Q**: Quit

The planned path to the current goal is shown in light blue. The robot is drawn with a facing direction; waypoints are numbered (1, 2, 3) and the status line shows "Navigating to waypoint X" or "Mission complete."

## How to progress this project

- **Try AI task ordering:** Set `OPENAI_API_KEY` or `GOOGLE_API_KEY`, then in `main.py` change `ai_prefer="heuristic"` to `ai_prefer="auto"` and run again.
- **Tweak the grid:** In `main.py`, adjust `run_simulation(num_tasks=3, num_obstacles=15, ...)` or the grid size.
- **Optional enhancements (from the SOP):**
  - Multi-robot simulation with collision avoidance
  - Real-time re-planning when obstacles move
  - Overlay showing AI decision-making (e.g. planned path or task order)
- **Demo:** Run several scenarios, take screenshots or record a GIF for a presentation.
- **Commit often:** Commit after each feature (e.g. “Add A* pathfinding”, “Add AI task order”) or use branches for experiments.

## Tech Stack

- Python 3, pygame, numpy, networkx (optional), OpenAI / Gemini API (optional)
