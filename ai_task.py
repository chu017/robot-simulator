"""
AI task planning: order tasks for the robot (Gemini/OpenAI or nearest-task-first heuristic).
"""
import os
import re
from typing import List, Tuple

from utils import manhattan


def _nearest_task_first(robot: Tuple[int, int], tasks: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """Order tasks by increasing Manhattan distance from robot (greedy nearest first)."""
    if not tasks:
        return []
    remaining = list(tasks)
    current = robot
    order = []
    while remaining:
        nearest = min(remaining, key=lambda t: manhattan(current, t))
        order.append(nearest)
        remaining.remove(nearest)
        current = nearest
    return order


def _parse_ordered_positions(text: str, task_set: set) -> List[Tuple[int, int]] | None:
    """
    Parse AI output for ordered (row,col) or (x,y) positions.
    Looks for patterns like (1,2), (3, 4), [1,2], 1,2 etc.
    """
    # Normalize: allow (r,c) or (x,y) style
    pattern = r"\(?\s*(\d+)\s*[,]\s*(\d+)\s*\)?"
    matches = re.findall(pattern, text)
    if not matches:
        return None
    parsed = [((int(r), int(c)) if (int(r), int(c)) in task_set else None) for r, c in matches]
    parsed = [p for p in parsed if p is not None]
    # Include any tasks we might have missed (different order in text)
    for t in task_set:
        if t not in parsed:
            parsed.append(t)
    return parsed if len(parsed) == len(task_set) else None


def order_tasks_openai(robot: Tuple[int, int], tasks: List[Tuple[int, int]]) -> List[Tuple[int, int]] | None:
    """Use OpenAI to suggest task order. Returns None on failure or missing key."""
    if not tasks:
        return []
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        if not client.api_key:
            return None
        task_str = ", ".join(f"({r},{c})" for r, c in tasks)
        prompt = (
            f"Robot at ({robot[0]},{robot[1]}). Tasks at [{task_str}]. "
            "Output optimal order to complete all tasks minimizing total steps. "
            "Reply with only the list of coordinates in order, e.g. (1,2), (0,3), (2,1)."
        )
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
        )
        text = (r.choices[0].message.content or "").strip()
        task_set = set(tasks)
        ordered = _parse_ordered_positions(text, task_set)
        return ordered
    except Exception:
        return None


def order_tasks_gemini(robot: Tuple[int, int], tasks: List[Tuple[int, int]]) -> List[Tuple[int, int]] | None:
    """Use Gemini to suggest task order. Returns None on failure or missing key."""
    if not tasks:
        return []
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
        if not os.environ.get("GOOGLE_API_KEY"):
            return None
        task_str = ", ".join(f"({r},{c})" for r, c in tasks)
        prompt = (
            f"Robot at ({robot[0]},{robot[1]}). Tasks at [{task_str}]. "
            "Output optimal order to complete all tasks minimizing total steps. "
            "Reply with only the list of coordinates in order, e.g. (1,2), (0,3), (2,1)."
        )
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        text = (response.text or "").strip()
        task_set = set(tasks)
        ordered = _parse_ordered_positions(text, task_set)
        return ordered
    except Exception:
        return None


def get_optimal_task_order(
    robot: Tuple[int, int],
    tasks: List[Tuple[int, int]],
    prefer: str = "auto",
) -> List[Tuple[int, int]]:
    """
    Return ordered list of tasks. prefer in ("gemini", "openai", "heuristic", "auto").
    auto: try Gemini then OpenAI then heuristic.
    """
    if not tasks:
        return []
    if len(tasks) == 1:
        return list(tasks)

    if prefer == "heuristic":
        return _nearest_task_first(robot, tasks)

    if prefer == "openai":
        ordered = order_tasks_openai(robot, tasks)
        return ordered if ordered is not None else _nearest_task_first(robot, tasks)

    if prefer == "gemini":
        ordered = order_tasks_gemini(robot, tasks)
        return ordered if ordered is not None else _nearest_task_first(robot, tasks)

    # auto
    ordered = order_tasks_gemini(robot, tasks)
    if ordered is not None:
        return ordered
    ordered = order_tasks_openai(robot, tasks)
    if ordered is not None:
        return ordered
    return _nearest_task_first(robot, tasks)
