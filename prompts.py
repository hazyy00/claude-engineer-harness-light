"""
Prompt Loading Utilities
========================
"""

import shutil
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent / "prompts"
TASK_SPEC_FILE = "task_spec.txt"


def get_task_spec() -> str:
    """Read the task specification."""
    spec_path = PROMPTS_DIR / TASK_SPEC_FILE
    if not spec_path.exists():
        return "No task spec found. Please create prompts/task_spec.txt."
    return spec_path.read_text()


def copy_spec_to_project(project_dir: Path) -> None:
    """Copy task_spec.txt into the project directory for the agent to read."""
    src = PROMPTS_DIR / TASK_SPEC_FILE
    dst = project_dir / TASK_SPEC_FILE
    if src.exists():
        shutil.copy(src, dst)


def get_initializer_task(project_dir: Path) -> str:
    """Get the task prompt for the first session."""
    template = (PROMPTS_DIR / "initializer_task.md").read_text()
    return template.replace("{{PROJECT_DIR}}", str(project_dir.resolve()))


def get_continuation_task(project_dir: Path) -> str:
    """Get the task prompt for continuation sessions."""
    template = (PROMPTS_DIR / "continuation_task.md").read_text()
    return template.replace("{{PROJECT_DIR}}", str(project_dir.resolve()))
