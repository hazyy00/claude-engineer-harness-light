"""
Bash Security Hooks
===================

Validates bash commands before execution.
All segments of compound commands (&&, ||, ;, |) are checked individually.
"""

import re
from typing import Any

# Commands the agent is allowed to run
ALLOWED_COMMANDS = {
    # Package managers
    "npm", "npx", "node", "yarn", "pnpm",
    # Python
    "python", "python3", "python3.12", "pip", "pip3",
    # Git
    "git",
    # GitHub CLI -- replaces Arcade for GitHub operations
    "gh",
    # File operations
    "ls", "cat", "head", "tail", "mkdir", "cp", "mv", "touch",
    "find", "grep", "sed", "awk", "sort", "uniq", "wc",
    "chmod", "echo", "pwd", "which",
    # Network
    "curl", "wget",
    # Build tools
    "make", "cargo", "go",
    # Shell utilities
    "export", "source", "env",
    # Shell built-ins
    "cd", ".", "eval", "test", "[",
    # Process
    "kill", "pkill",
}

# Single-word commands that are blocked outright (checked with word boundaries)
BLOCKED_WORDS = {
    "sudo", "su", "shutdown", "reboot", "dd", "mkfs", "fdisk",
}

# Patterns for dangerous rm usage
DANGEROUS_RM_PATTERNS = [
    r"rm\s+(-\w*[rf]\w*\s+)*(-rf|-fr|-r\s+-f|-f\s+-r)\s+/(?!tmp|var/tmp)",
    r"rm\s+(-[^\s]*\s+)*\$HOME",
    r"rm\s+(-[^\s]*\s+)*~\s*(/|$)",
    r"rm\s+(-[^\s]*\s+)*\*\s*$",
]


def _split_segments(command: str) -> list[str]:
    """Split a compound shell command into individual segments."""
    # Split on ||, &&, ;, and | (in that order to avoid partial matches)
    parts = re.split(r"\|\||&&|;|\|", command)
    return [p.strip() for p in parts if p.strip()]


def _base_cmd(segment: str) -> str:
    """Return the first token (the executable) of a command segment."""
    tokens = segment.strip().split()
    return tokens[0] if tokens else ""


def _check_segment(segment: str) -> str | None:
    """
    Validate a single command segment.
    Returns an error message string if blocked, or None if allowed.
    """
    if not segment:
        return None

    base = _base_cmd(segment)

    # Check for blocked single-word commands using word-boundary matching
    for word in BLOCKED_WORDS:
        if re.search(r"(?<!\w)" + re.escape(word) + r"(?!\w)", segment):
            return f"Command blocked for safety: '{word}'"

    # Validate rm commands against dangerous patterns
    if base == "rm":
        for pattern in DANGEROUS_RM_PATTERNS:
            if re.search(pattern, segment):
                return f"Dangerous rm command blocked: {segment[:100]}"

    # Allow if base command is in the allowlist
    if base in ALLOWED_COMMANDS:
        return None

    return (
        f"Command not in allowlist: '{base}'. "
        f"If this is needed, add it to ALLOWED_COMMANDS in security.py."
    )


def bash_security_hook(tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any] | None:
    """
    Pre-execution hook that validates bash commands.

    Every segment of compound commands (&&, ||, ;, |) is checked individually.
    Returns None to allow, or a dict with "error" to block.
    """
    if tool_name != "Bash":
        return None

    command: str = tool_input.get("command", "")
    if not command:
        return None

    for segment in _split_segments(command):
        error = _check_segment(segment)
        if error:
            return {"error": error}

    return None
