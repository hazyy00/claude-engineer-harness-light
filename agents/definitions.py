"""
Agent Definitions -- Pro Edition
==================================

Two specialized agents: Coding and GitHub.
No Linear or Slack -- task tracking is local, notifications are terminal-only.
GitHub uses the gh CLI via Bash instead of Arcade.
"""

import os
from pathlib import Path
from typing import Final

from claude_agent_sdk.types import AgentDefinition

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

# =============================================================================
# SUB-AGENT MODEL IDs -- UPDATE HERE WHEN ANTHROPIC RELEASES NEW MODELS
#
# These models are used by the coding and github sub-agents.
# The orchestrator model is set in autonomous_agent_pro.py.
#
# Override via environment variables:
#   CODING_AGENT_MODEL=sonnet   (accepts: haiku | sonnet | opus | inherit)
#   GITHUB_AGENT_MODEL=haiku
# =============================================================================
AGENT_MODEL_IDS: Final[dict[str, str]] = {
    "haiku":   "claude-haiku-4-5-20251001",
    "sonnet":  "claude-sonnet-4-6",
    "opus":    "claude-opus-4-7",
    "inherit": "inherit",
}

DEFAULT_AGENT_MODELS: Final[dict[str, str]] = {
    "coding": "sonnet",  # Sonnet for best coding quality
    "github": "haiku",   # Haiku for simple git/gh operations
}

# Tools available to the coding agent
CODING_TOOLS: list[str] = [
    "Read", "Write", "Edit", "Glob", "Grep", "Bash",
]

# Tools available to the GitHub agent (gh CLI via Bash)
GITHUB_TOOLS: list[str] = [
    "Read", "Glob", "Bash",
]


def _get_model_id(agent_name: str) -> str:
    env_var = f"{agent_name.upper()}_AGENT_MODEL"
    alias = os.environ.get(env_var, "").lower().strip()
    if alias not in AGENT_MODEL_IDS:
        alias = DEFAULT_AGENT_MODELS.get(agent_name, "haiku")
    return AGENT_MODEL_IDS[alias]


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text()


def _get_coding_tools() -> list[str]:
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
    agents: dict[str, AgentDefinition] = {
        "coding": AgentDefinition(
            description=(
                "Implements features, writes and tests code, reads TASKS.md to "
                "understand what to build, and marks tasks complete when done. "
                "Use for all coding and implementation work."
            ),
            prompt=_load_prompt("coding_agent_prompt"),
            tools=_get_coding_tools(),
            model=_get_model_id("coding"),
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
            model=_get_model_id("github"),
        )

    return agents
