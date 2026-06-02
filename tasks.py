"""
Local Task Tracking
===================

Replaces Linear with a simple TASKS.md file in the project directory.
The agent reads and updates this file to track what has been done
and what to work on next across sessions.
"""

import re
from pathlib import Path
from datetime import datetime


TASKS_FILE = "TASKS.md"
_TASK_PATTERN = re.compile(r"^- \[[ x]\]", re.MULTILINE)
_DONE_PATTERN = re.compile(r"^- \[x\]", re.MULTILINE)


def get_tasks_path(project_dir: Path) -> Path:
    return project_dir / TASKS_FILE


def is_initialized(project_dir: Path) -> bool:
    """Return True if TASKS.md exists AND contains at least one task entry.

    A TASKS.md that exists but has no checkboxes means the first run crashed
    before the agent populated the task list -- treat it as uninitialized.
    """
    path = get_tasks_path(project_dir)
    if not path.exists():
        return False
    content = path.read_text()
    return bool(_TASK_PATTERN.search(content))


def read_tasks(project_dir: Path) -> str:
    path = get_tasks_path(project_dir)
    if not path.exists():
        return ""
    return path.read_text()


def write_tasks(project_dir: Path, content: str) -> None:
    get_tasks_path(project_dir).write_text(content)


def count_tasks(project_dir: Path) -> dict[str, int]:
    content = read_tasks(project_dir)
    total = len(_TASK_PATTERN.findall(content))
    done = len(_DONE_PATTERN.findall(content))
    return {"total": total, "done": done, "remaining": total - done}


def print_progress(project_dir: Path) -> None:
    if not is_initialized(project_dir):
        print("  No tasks file found yet.")
        return

    counts = count_tasks(project_dir)
    total = counts["total"]
    done = counts["done"]
    remaining = counts["remaining"]

    if total == 0:
        print("  No tasks defined yet.")
        return

    pct = int((done / total) * 100)
    bar_len = 30
    filled = int(bar_len * done / total)
    bar = "█" * filled + "░" * (bar_len - filled)

    print(f"\n  Progress: [{bar}] {pct}%")
    print(f"  Tasks: {done}/{total} complete, {remaining} remaining")
    print(f"  File: {get_tasks_path(project_dir)}")


def create_initial_tasks(project_dir: Path, spec_content: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    content = f"""# Project Tasks

Generated: {timestamp}

## Spec

{spec_content}

## Tasks

<!-- The agent will populate this section on first run -->

"""
    write_tasks(project_dir, content)
