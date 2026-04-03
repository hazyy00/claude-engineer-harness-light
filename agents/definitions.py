"""
Agent Definitions -- Pro Edition
==================================

Two specialized agents: Coding and GitHub.
No Linear or Slack -- task tracking is local, notifications are terminal-only.
GitHub uses the gh CLI via Bash instead of Arcade.
"""

import os
from pathlib import Path
from typing import Final, Literal, TypeGuard

from claude_agent_sdk.types import AgentDefinition

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

ModelOption = Literal["haiku", "sonnet", "opus", "inherit"]
_VALID_MODELS: Final[tuple[str, ...]] = ("haiku", "sonnet", "opus", "inherit")

DEFAULT_MODELS: Final[dict[str, ModelOption]] = {
    "coding": "sonnet",   # Sonnet for best coding quality
    "github": "haiku",    # Haiku for simple git/gh operations
}

# Tools available to the coding agent
CODING_TOOLS: list[str] = [
    "Read", "Write", "Edit", "Glob", "Grep", "Bash",
    # Playwright tools added dynamically if USE_PLAYWRIGHT=true
]

# Tools available to the GitHub agent
# Uses gh CLI via Bash -- no Arcade required
GITHUB_TOOLS: list[str] = [
    "Read", "Write", "Edit", "Glob", "Grep", "Bash",
]


def _is_valid_model(value: str) -> TypeGuard[ModelOption]:
    return value in _VALID_MODELS


def _get_model(agent_name: str) -> ModelOption:
    env_var = f"{agent_name.upper()}_AGENT_MODEL"
    value = os.environ.get(env_var, "").lower().strip()
    if _is_valid_model(value):
        return value
    return DEFAULT_MODELS.get(agent_name, "haiku")


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text()


def _get_coding_tools() -> list[str]:
    """Get coding tools, adding Playwright if enabled."""
    tools = list(CODING_TOOLS)
    if os.environ.get("USE_PLAYWRIGHT", "false").lower() == "true":
        tools.extend([
            "mcp__playwright__browser_navigate",
            "mcp__playwright__browser_take_screenshot",
            "mcp__playwright__browser_click",
            "mcp__playwright__browser_type",
            "mcp__playwright__browser_select_option",
            "mcp__playwright__browser_hover",
            "mcp__playwright__browser_snapshot",
            "mcp__playwright__browser_wait_for",
        ])
    return tools


def get_agent_definitions(github_enabled: bool = True) -> dict[str, AgentDefinition]:
    """
    Build agent definitions based on configuration.

    Args:
        github_enabled: Whether to include the GitHub agent.
    """
    agents: dict[str, AgentDefinition] = {
        "coding": AgentDefinition(
            description=(
                "Implements features, writes and tests code, reads TASKS.md to "
                "understand what to build, and marks tasks complete when done. "
                "Use for all coding and implementation work."
            ),
            prompt=_load_prompt("coding_agent_prompt"),
            tools=_get_coding_tools(),
            model=_get_model("coding"),
        ),
    }

    if github_enabled:
        agents["github"] = AgentDefinition(
            description=(
                "Handles git commits, branch creation, and GitHub pull requests "
                "using the gh CLI. Use after features are implemented and tested."
            ),
            prompt=_load_prompt("github_agent_prompt"),
            tools=GITHUB_TOOLS,
            model=_get_model("github"),
        )

    return agents
