# Agent Harness -- Claude Pro Edition

An autonomous AI coding agent designed for **Claude Pro subscribers**. No API billing, no Arcade account, no Linear subscription required. Just a Claude Pro plan and a GitHub account.

> **Note:** Does not work on Windows due to Claude Agent SDK limitations. Use WSL or a Linux VM on Windows.

---

## Quick Start

See [SETUP.md](./SETUP.md) for the full step-by-step guide.

**After setup, run the agent with:**

```bash
source venv/bin/activate
python3.12 autonomous_agent_pro.py --project-dir my-app
```

Generated projects are created in the `generations/` folder.

**Every time you return:**

```bash
cd path/to/pro_agent
source venv/bin/activate
python3.12 autonomous_agent_pro.py --project-dir my-app
```

Check progress anytime with:

```bash
cat generations/my-app/TASKS.md
```

---

## How It Differs from the Full Version

| Feature | Full Version | Pro Edition |
|---|---|---|
| Authentication | API key (console billing) | `claude login` (Pro subscription) |
| Task tracking | Linear | Local `TASKS.md` file |
| GitHub | Arcade MCP gateway | `gh` CLI directly |
| Notifications | Slack | Terminal output |
| Setup steps | ~10 steps, multiple accounts | ~5 steps |
| Token usage | Unlimited (pay per token) | Managed via `--max-iterations` |

---

## Key Features

- **No API billing** -- uses your Pro subscription via `claude login`
- **No Arcade account** -- GitHub via `gh` CLI built into bash
- **No Linear** -- tasks tracked in a plain `TASKS.md` file in your project
- **Session continuity** -- interrupt and resume any time, agent picks up from TASKS.md
- **Token-aware** -- `--max-iterations` defaults to 10 to avoid hitting Pro limits mid-session
- **Optional Playwright** -- browser UI testing disabled by default, enable with `USE_PLAYWRIGHT=true`
- **Per-agent model config** -- Sonnet for coding, Haiku for everything else

---

## How It Works

### Multi-Agent Architecture

```
┌────────────────────────────────────────────────────────────┐
│                  MULTI-AGENT ARCHITECTURE                  │
│                    (Claude Pro Edition)                    │
├────────────────────────────────────────────────────────────┤
│                                                            │
│                  ┌─────────────────┐                       │
│                  │  ORCHESTRATOR   │  (Haiku by default)   │
│                  │  Reads TASKS.md │                       │
│                  └────────┬────────┘                       │
│                           │                                │
│              ┌────────────┴────────────┐                   │
│              │                         │                   │
│       ┌──────▼──────┐          ┌───────▼──────┐            │
│       │   CODING    │          │    GITHUB    │            │
│       │  (Sonnet)   │          │   (Haiku)    │            │
│       │ Writes code │          │  gh CLI + git│            │
│       │ Updates     │          │  Commits, PRs│            │
│       │ TASKS.md    │          └──────────────┘            │
│       └─────────────┘                                      │
│              │                                             │
│   ┌──────────▼──────────────────────────────────┐          │
│   │       PROJECT OUTPUT (Isolated Git)         │          │
│   │    GENERATIONS_BASE_PATH/project-name/      │          │
│   └─────────────────────────────────────────────┘          │
└────────────────────────────────────────────────────────────┘
```

### Agent Responsibilities

1. **Orchestrator** -- reads `TASKS.md`, decides what to work on next, delegates to coding or github agent, coordinates session handoff.

2. **Coding Agent** -- reads the task spec and `TASKS.md`, implements features, runs tests, marks tasks complete.

3. **GitHub Agent** *(optional)* -- uses `git` and `gh` CLI to commit code, create branches, and open pull requests. Requires `gh auth login`.

### Task Tracking

Instead of Linear, the agent maintains a `TASKS.md` file inside the project directory:

```markdown
# Project Tasks

## Tasks
- [x] Set up project structure
- [x] Create homepage
- [ ] Add authentication
- [ ] Add dark mode
```

The agent updates this file as it works. You can edit it manually between sessions to add, remove, or reprioritize tasks.

---

## Command Line Options

| Option | Description | Default |
|---|---|---|
| `--project-dir` | Project name or path | `./pro_demo_project` |
| `--generations-base` | Base directory for projects | `./generations` |
| `--max-iterations` | Max iterations before pausing | `10` |
| `--model` | Orchestrator model: haiku, sonnet, opus | `haiku` |
| `--no-github` | Disable GitHub integration | Off |

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `GENERATIONS_BASE_PATH` | Where generated projects are created | `./generations` |
| `MAX_ITERATIONS` | Default max iterations per run | `10` |
| `ORCHESTRATOR_MODEL` | Orchestrator model | `haiku` |
| `CODING_AGENT_MODEL` | Coding agent model | `sonnet` |
| `GITHUB_AGENT_MODEL` | GitHub agent model | `haiku` |
| `USE_PLAYWRIGHT` | Enable browser UI testing | `false` |

---

## Customization

**Change what gets built** -- edit `prompts/task_spec.txt` with your project description before the first run. Example specs are in `prompts/example_task_specs/`.

**Adjust the task breakdown** -- edit `prompts/initializer_task.md` to change how the agent structures the task list on first run.

**Edit tasks mid-project** -- open `TASKS.md` in the project output folder and add, remove, or reprioritize tasks. The agent will pick up the changes on the next run.

**Add allowed bash commands** -- edit `security.py` and add commands to `ALLOWED_COMMANDS`.

**Enable Playwright** -- add `USE_PLAYWRIGHT=true` to your `.env` file.

---

## Generated Project Structure

```
generations/my-app/
├── TASKS.md                  # Task list and progress tracker
├── task_spec.txt             # Copied project specification
├── .claude_settings.json     # Security settings (auto-generated)
├── .git/                     # Isolated git repository
└── [application files]       # Generated application code
```

---

## Security Model

Defense-in-depth (see `security.py` and `client.py`):

1. **OS-level Sandbox** -- bash commands run in an isolated environment
2. **Filesystem Restrictions** -- file operations restricted to project directory only
3. **Bash Allowlist** -- only specific commands permitted (npm, node, git, gh, curl, etc.)
4. **Dangerous Command Validation** -- `rm` and similar commands are validated before execution

---

## Pro Plan Token Tips

- Default `--max-iterations 10` keeps sessions from draining your quota
- Use `--model haiku` for the orchestrator (default) -- it just delegates, doesn't need to be smart
- Sonnet is used for coding by default -- downgrade to haiku if you are running low
- If you hit the limit mid-session, wait and run the same command -- the agent resumes from TASKS.md
- Smaller, focused task specs burn fewer tokens than large open-ended apps

---

## Project Structure

```
pro_agent/
├── autonomous_agent_pro.py    # Entry point -- run this
├── agent.py                   # Core agent loop and session logic
├── client.py                  # Claude SDK client configuration
├── tasks.py                   # Local task tracking (TASKS.md utilities)
├── prompts.py                 # Prompt loading utilities
├── security.py                # Bash command security hooks
├── agents/
│   └── definitions.py         # Coding and GitHub agent definitions
├── prompts/
│   ├── orchestrator_prompt.md
│   ├── coding_agent_prompt.md
│   ├── github_agent_prompt.md
│   ├── initializer_task.md
│   ├── continuation_task.md
│   ├── task_spec.txt          # Edit this with your project description
│   └── example_task_specs/    # Example specs to get started
├── .env.example
├── requirements.txt
└── SETUP.md
```

---

## License

MIT License -- see [LICENSE](./LICENSE) for details.
