"""
Claude SDK Client Configuration
================================

Configures the Claude Agent SDK client for the Pro edition.
No Arcade gateway -- uses gh CLI for GitHub, local files for task tracking.
"""

import json
import os
from pathlib import Path
from typing import Literal, TypedDict

from dotenv import load_dotenv

load_dotenv()

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, McpServerConfig
from claude_agent_sdk.types import HookCallback, HookMatcher

from agents.definitions import get_agent_definitions
from security import bash_security_hook


PermissionMode = Literal["acceptEdits", "acceptAll", "reject", "ask"]


class SandboxConfig(TypedDict):
    enabled: bool
    autoAllowBashIfSandboxed: bool


class PermissionsConfig(TypedDict):
    defaultMode: PermissionMode
    allow: list[str]


class SecuritySettings(TypedDict):
    sandbox: SandboxConfig
    permissions: PermissionsConfig


# Playwright MCP tools (optional -- only included if USE_PLAYWRIGHT=true in .env)
PLAYWRIGHT_TOOLS: list[str] = [
    "mcp__playwright__browser_navigate",
    "mcp__playwright__browser_take_screenshot",
    "mcp__playwright__browser_click",
    "mcp__playwright__browser_type",
    "mcp__playwright__browser_select_option",
    "mcp__playwright__browser_hover",
    "mcp__playwright__browser_snapshot",
    "mcp__playwright__browser_wait_for",
]

BUILTIN_TOOLS: list[str] = [
    "Read", "Write", "Edit", "Glob", "Grep", "Bash",
]

PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_orchestrator_prompt() -> str:
    return (PROMPTS_DIR / "orchestrator_prompt.md").read_text()


def use_playwright() -> bool:
    return os.environ.get("USE_PLAYWRIGHT", "false").lower() == "true"


def create_security_settings(project_dir: Path) -> SecuritySettings:
    project_abs = str(project_dir.resolve())
    allowed: list[str] = [
        f"Read({project_abs}/**)",
        f"Write({project_abs}/**)",
        f"Edit({project_abs}/**)",
        f"Glob({project_abs}/**)",
        f"Grep({project_abs}/**)",
        # Bash is gated by bash_security_hook -- not a blanket allow
        "Bash(*)",
    ]
    if use_playwright():
        allowed.extend(PLAYWRIGHT_TOOLS)

    return SecuritySettings(
        sandbox=SandboxConfig(enabled=True, autoAllowBashIfSandboxed=True),
        permissions=PermissionsConfig(
            defaultMode="acceptEdits",
            allow=allowed,
        ),
    )


def write_security_settings(project_dir: Path, settings: SecuritySettings) -> Path:
    project_dir.mkdir(parents=True, exist_ok=True)
    settings_file = project_dir / ".claude_settings.json"
    with open(settings_file, "w") as f:
        json.dump(settings, f, indent=2)
    return settings_file


def create_client(
    project_dir: Path,
    model: str,
    github_enabled: bool = True,
) -> ClaudeSDKClient:
    """
    Create a Claude Agent SDK client.

    Security layers:
    1. Sandbox -- OS-level bash isolation
    2. Permissions -- file ops restricted to absolute project_dir path
    3. Security hooks -- every segment of compound bash commands validated
    """
    security_settings = create_security_settings(project_dir)
    settings_file = write_security_settings(project_dir, security_settings)

    print(f"Security settings written to {settings_file}")
    print(f"  - Filesystem restricted to: {project_dir.resolve()}")
    print(f"  - GitHub: {'gh CLI' if github_enabled else 'disabled'}")
    print(f"  - Playwright: {'enabled' if use_playwright() else 'disabled'}")
    print()

    orchestrator_prompt = load_orchestrator_prompt()

    allowed_tools = list(BUILTIN_TOOLS)
    if use_playwright():
        allowed_tools.extend(PLAYWRIGHT_TOOLS)

    mcp_servers: dict[str, McpServerConfig] = {}
    if use_playwright():
        mcp_servers["playwright"] = McpServerConfig(
            command="npx",
            args=["-y", "@playwright/mcp@latest"],
        )

    hook: HookCallback = bash_security_hook  # type: ignore[assignment]

    return ClaudeSDKClient(
        options=ClaudeAgentOptions(
            model=model,
            system_prompt=orchestrator_prompt,
            allowed_tools=allowed_tools,
            mcp_servers=mcp_servers,
            hooks={
                "PreToolUse": [
                    HookMatcher(
                        matcher="Bash",
                        hooks=[hook],
                    ),
                ],
            },
            agents=get_agent_definitions(github_enabled=github_enabled),
            max_turns=500,
            cwd=str(project_dir.resolve()),
            settings=str(settings_file.resolve()),
        )
    )
