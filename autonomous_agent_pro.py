#!/usr/bin/env python3
"""
Autonomous Coding Agent -- Claude Pro Edition
==============================================

A lightweight multi-agent harness designed for Claude Pro subscribers.
Uses the Claude Agent SDK with claude login auth (no API key required).
Tracks tasks locally via TASKS.md instead of Linear.
Uses the gh CLI for GitHub operations instead of Arcade.

Usage:
    python3.12 autonomous_agent_pro.py --project-dir my-app
    python3.12 autonomous_agent_pro.py --project-dir my-app --max-iterations 5
    python3.12 autonomous_agent_pro.py --project-dir my-app --model sonnet
"""

import argparse
import asyncio
import os
import shutil
import sys
from pathlib import Path

from dotenv import load_dotenv

from agent import run_autonomous_agent

load_dotenv()

# Available models
AVAILABLE_MODELS: dict[str, str] = {
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-4-5-20250929",
    "opus": "claude-opus-4-5-20251101",
}

# Default orchestrator model -- haiku keeps token usage low on Pro
DEFAULT_MODEL: str = os.environ.get("ORCHESTRATOR_MODEL", "haiku").lower()
if DEFAULT_MODEL not in AVAILABLE_MODELS:
    DEFAULT_MODEL = "haiku"

# Default output location
DEFAULT_GENERATIONS_BASE: Path = Path(
    os.environ.get("GENERATIONS_BASE_PATH", "./generations")
)

# Default max iterations -- kept low for Pro token limits
DEFAULT_MAX_ITERATIONS: int = int(os.environ.get("MAX_ITERATIONS", "10"))


def check_prerequisites() -> bool:
    """Check that required tools are available."""
    # Check gh CLI
    if not shutil.which("gh"):
        print("Error: GitHub CLI (gh) is not installed.")
        print("Install it with: brew install gh")
        print("Then authenticate with: gh auth login")
        return False

    # Check gh is authenticated
    result = os.system("gh auth status > /dev/null 2>&1")
    if result != 0:
        print("Error: GitHub CLI is not authenticated.")
        print("Run: gh auth login")
        return False

    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Autonomous Coding Agent (Claude Pro Edition)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start a new project
  python3.12 autonomous_agent_pro.py --project-dir my-app

  # Limit iterations to stay within Pro token limits
  python3.12 autonomous_agent_pro.py --project-dir my-app --max-iterations 5

  # Use sonnet for better coding quality
  python3.12 autonomous_agent_pro.py --project-dir my-app --model sonnet

  # Custom output location
  python3.12 autonomous_agent_pro.py --generations-base ~/projects --project-dir my-app
        """,
    )

    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path("./pro_demo_project"),
        help="Project name or path. Relative paths go inside the generations base.",
    )

    parser.add_argument(
        "--generations-base",
        type=Path,
        default=None,
        help=f"Base directory for generated projects (default: {DEFAULT_GENERATIONS_BASE})",
    )

    parser.add_argument(
        "--max-iterations",
        type=int,
        default=DEFAULT_MAX_ITERATIONS,
        help=f"Max agent iterations before pausing (default: {DEFAULT_MAX_ITERATIONS}). "
             "Recommended to keep low on Pro plan to avoid hitting token limits.",
    )

    parser.add_argument(
        "--model",
        type=str,
        choices=list(AVAILABLE_MODELS.keys()),
        default=DEFAULT_MODEL,
        help=f"Orchestrator model (default: {DEFAULT_MODEL}). "
             "Sub-agents use: coding=sonnet, github=haiku.",
    )

    parser.add_argument(
        "--no-github",
        action="store_true",
        help="Disable GitHub integration (local git only).",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    # Check prerequisites
    if not args.no_github:
        if not check_prerequisites():
            return 1

    # Resolve paths
    generations_base: Path = args.generations_base or DEFAULT_GENERATIONS_BASE
    if not generations_base.is_absolute():
        generations_base = Path.cwd() / generations_base

    project_dir: Path = args.project_dir
    if not project_dir.is_absolute():
        project_name = str(project_dir).lstrip("./")
        project_dir = generations_base / project_name

    generations_base.mkdir(parents=True, exist_ok=True)

    model_id: str = AVAILABLE_MODELS[args.model]

    print("\n" + "=" * 60)
    print("  AUTONOMOUS CODING AGENT -- CLAUDE PRO EDITION")
    print("=" * 60)
    print(f"\nProject directory : {project_dir}")
    print(f"Orchestrator model: {args.model}")
    print(f"Max iterations    : {args.max_iterations}")
    print(f"GitHub integration: {'disabled' if args.no_github else 'enabled (gh CLI)'}")
    print()

    try:
        asyncio.run(
            run_autonomous_agent(
                project_dir=project_dir,
                model=model_id,
                max_iterations=args.max_iterations,
                github_enabled=not args.no_github,
            )
        )
        return 0
    except KeyboardInterrupt:
        print("\n\nInterrupted. Run the same command again to resume.")
        return 130
    except Exception as e:
        print(f"\nFatal error ({type(e).__name__}): {e}")
        print("\nCommon causes:")
        print("  1. Not logged in to Claude -- run: claude login")
        print("  2. gh CLI not authenticated -- run: gh auth login")
        print("  3. Hit Pro plan token limit -- wait and try again, or use --max-iterations to reduce usage")
        raise


if __name__ == "__main__":
    sys.exit(main())
