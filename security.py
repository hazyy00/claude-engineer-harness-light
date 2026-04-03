"""
Bash Security Hooks
===================

Validates bash commands before execution.
Prevents dangerous operations while allowing everything needed
for development work including the gh CLI.
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
    # Process
    "kill", "pkill",
}

# Commands that are blocked outright regardless of arguments
BLOCKED_COMMANDS = {
    "sudo", "su", "rm -rf /", "shutdown", "reboot",
    "dd", "mkfs", "fdisk",
}

# Patterns for dangerous rm usage
DANGEROUS_RM_PATTERNS = [
    r"rm\s+(-\w*f\w*|-\w*r\w*\s+-\w*f\w*|-rf|-fr)\s+/(?!tmp|var/tmp)",
    r"rm\s+.*\$HOME",
    r"rm\s+.*~\s*$",
]


def bash_security_hook(tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any] | None:
    """
    Pre-execution hook that validates bash commands.

    Returns None to allow the command, or a dict with an error to block it.
    """
    if tool_name != "Bash":
        return None

    command: str = tool_input.get("command", "")
    if not command:
        return None

    # Get the base command
    base_command = command.strip().split()[0] if command.strip() else ""

    # Block outright dangerous commands
    for blocked in BLOCKED_COMMANDS:
        if blocked in command:
            return {
                "error": f"Command blocked for safety: contains '{blocked}'"
            }

    # Validate rm commands
    for pattern in DANGEROUS_RM_PATTERNS:
        if re.search(pattern, command):
            return {
                "error": f"Dangerous rm command blocked: {command[:100]}"
            }

    # Allow if base command is in the allowlist
    if base_command in ALLOWED_COMMANDS:
        return None

    # Allow shell built-ins and common patterns
    if base_command in {"cd", "export", "source", ".", "eval", "test", "["}:
        return None

    # Allow pipes and compound commands by checking the first token
    if "|" in command or "&&" in command or ";" in command:
        first_cmd = re.split(r"[|;&]", command)[0].strip().split()[0]
        if first_cmd in ALLOWED_COMMANDS or first_cmd in {"cd", "export"}:
            return None

    # Block anything else
    return {
        "error": f"Command not in allowlist: '{base_command}'. "
                 f"If this is needed, add it to ALLOWED_COMMANDS in security.py."
    }
