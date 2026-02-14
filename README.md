# AI-Powered Robot Simulator

A 2D grid robot simulator with A* pathfinding and AI-optimized task ordering. Built for a 3–4 hour hackathon.

## Features

- **2D Grid Environment**: Numpy-based grid with obstacles, robot, and tasks
- **A* Pathfinding**: Optimal path from robot to any goal
- **AI Task Planning**: Gemini / OpenAI or nearest-task-first heuristic for task order
- **Pygame Visualization**: Animated robot movement, colored cells, optional stats overlay

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

Set `OPENAI_API_KEY` or `GOOGLE_API_KEY` in the environment for AI task ordering; otherwise the simulator uses the nearest-task-first heuristic.

## Project Structure

- `main.py` – Entry point, pygame loop, animation, dashboard
- `pathfinding.py` – A* algorithm
- `ai_task.py` – AI/heuristic task order planning
- `utils.py` – Grid representation, cell types, helpers

## Controls

- **Space**: Step simulation (or run auto)
- **R**: Reset / new scenario
- **Q**: Quit

## Tech Stack

- Python 3, pygame, numpy, networkx (optional), OpenAI / Gemini API (optional)
