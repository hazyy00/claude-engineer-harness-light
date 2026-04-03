"""
Agent Session Logic
===================

Core loop for running autonomous coding sessions.
"""

import asyncio
import traceback
from pathlib import Path
from typing import Literal, NamedTuple

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeSDKClient,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)

from client import create_client
from tasks import is_initialized, print_progress, copy_spec_to_project
from prompts import get_initializer_task, get_continuation_task, copy_spec_to_project as copy_spec


AUTO_CONTINUE_DELAY: int = 3
COMPLETION_SIGNAL = "PROJECT_COMPLETE:"

SessionStatus = Literal["continue", "error", "complete"]
SESSION_CONTINUE: SessionStatus = "continue"
SESSION_ERROR: SessionStatus = "error"
SESSION_COMPLETE: SessionStatus = "complete"


class SessionResult(NamedTuple):
    status: SessionStatus
    response: str


async def run_agent_session(
    client: ClaudeSDKClient,
    message: str,
    project_dir: Path,
) -> SessionResult:
    """Run a single agent session and return the result."""
    print("Sending prompt to Claude...\n")

    try:
        await client.query(message)

        response_text = ""
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        response_text += block.text
                        print(block.text, end="", flush=True)
                    elif isinstance(block, ToolUseBlock):
                        print(f"\n[Tool: {block.name}]", flush=True)
                        input_str = str(block.input)
                        preview = input_str[:200] + "..." if len(input_str) > 200 else input_str
                        print(f"   {preview}", flush=True)

            elif isinstance(msg, UserMessage):
                for block in msg.content:
                    if isinstance(block, ToolResultBlock):
                        is_error = bool(block.is_error) if block.is_error else False
                        content = block.content
                        if "blocked" in str(content).lower():
                            print(f"   [BLOCKED] {content}", flush=True)
                        elif is_error:
                            print(f"   [Error] {str(content)[:300]}", flush=True)
                        else:
                            print("   [Done]", flush=True)

        print("\n" + "-" * 60 + "\n")

        if COMPLETION_SIGNAL in response_text:
            return SessionResult(status=SESSION_COMPLETE, response=response_text)

        return SessionResult(status=SESSION_CONTINUE, response=response_text)

    except ConnectionError as e:
        print(f"\nNetwork error: {e}")
        return SessionResult(status=SESSION_ERROR, response=str(e))

    except TimeoutError as e:
        print(f"\nTimeout: {e}. Will retry.")
        return SessionResult(status=SESSION_ERROR, response=str(e))

    except Exception as e:
        error_type = type(e).__name__
        print(f"\nError ({error_type}): {e}")
        traceback.print_exc()

        msg = str(e).lower()
        if "rate" in msg or "limit" in msg:
            print("\nHit rate limit -- you may have reached your Pro plan token quota.")
            print("Wait a few minutes and try again, or reduce --max-iterations.")
        elif "auth" in msg or "token" in msg:
            print("\nAuthentication error. Run: claude login")

        return SessionResult(status=SESSION_ERROR, response=str(e))


async def run_autonomous_agent(
    project_dir: Path,
    model: str,
    max_iterations: int,
    github_enabled: bool = True,
) -> None:
    """Run the main autonomous agent loop."""
    project_dir.mkdir(parents=True, exist_ok=True)

    is_first_run = not is_initialized(project_dir)

    if is_first_run:
        print("Fresh project -- initializing...")
        copy_spec(project_dir)
        print()
        print("=" * 60)
        print("  NOTE: First session sets up the task list.")
        print("  This may take several minutes. Watch for [Tool: ...] output.")
        print("=" * 60)
        print()
    else:
        print("Resuming existing project.")
        print_progress(project_dir)

    iteration = 0

    while True:
        iteration += 1

        if iteration > max_iterations:
            print(f"\nReached max iterations ({max_iterations}).")
            print("Run the same command again to continue.")
            print_progress(project_dir)
            break

        print(f"\n{'=' * 60}")
        print(f"  SESSION {iteration} of {max_iterations}")
        print(f"{'=' * 60}\n")

        # Fresh client each iteration to prevent context window exhaustion
        client = create_client(project_dir, model, github_enabled)

        if is_first_run:
            prompt = get_initializer_task(project_dir)
            is_first_run = False
        else:
            prompt = get_continuation_task(project_dir)

        result = SessionResult(status=SESSION_ERROR, response="uninitialized")

        try:
            async with client:
                result = await run_agent_session(client, prompt, project_dir)
        except Exception as e:
            print(f"\nSession error ({type(e).__name__}): {e}")
            traceback.print_exc()
            result = SessionResult(status=SESSION_ERROR, response=str(e))

        if result.status == SESSION_COMPLETE:
            print("\n" + "=" * 60)
            print("  PROJECT COMPLETE")
            print("=" * 60)
            print_progress(project_dir)
            break
        elif result.status == SESSION_CONTINUE:
            print(f"\nContinuing in {AUTO_CONTINUE_DELAY}s...")
            print_progress(project_dir)
        elif result.status == SESSION_ERROR:
            print("\nSession error -- will retry with a fresh session.")

        await asyncio.sleep(AUTO_CONTINUE_DELAY)

    print("\n" + "=" * 60)
    print("  SESSION COMPLETE")
    print(f"  Project: {project_dir.resolve()}")
    print("=" * 60)
    print_progress(project_dir)
    print(f"\n  To run the generated app:\n  cd {project_dir.resolve()}")
    print("  npm install && npm run dev  (or check init.sh if present)")
    print()
