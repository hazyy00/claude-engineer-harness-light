# Agent Harness Pro Edition -- Setup Guide

This version requires no API billing and no Arcade account. You need a Claude Pro subscription and a GitHub account.

---

## Prerequisites

- **Python 3.12** -- install with `brew install python@3.12`
- **Node.js v18+** -- install with `brew install node`
- **Git** -- usually pre-installed on Mac
- **A Claude Pro subscription** -- for `claude login`
- **A GitHub account** -- for `gh` CLI integration

---

## Step 1: Install Python 3.12

```bash
brew install python@3.12
python3.12 --version
```

---

## Step 2: Install the Claude Code CLI

Run from anywhere -- this is a global install:

```bash
npm install -g @anthropic-ai/claude-code
claude --version
```

---

## Step 3: Log In to Claude

```bash
claude login
```

Follow the prompts to authenticate with your Anthropic account. This is how the agent uses your Pro subscription -- no API key needed.

---

## Step 4: Install the GitHub CLI and Authenticate

```bash
brew install gh
gh auth login
```

Follow the prompts to authenticate with your GitHub account. The agent uses `gh` for commits, branches, and pull requests -- no Arcade required.

---

## Step 5: Clone the Repository

```bash
cd ~/Desktop/FOLDER_NAME
git clone https://github.com/hazyy00/claude-engineer-harness-light.git
cd YOUR_REPO
```

**All remaining steps must be run from inside this folder.**

---

## Step 6: Create a Virtual Environment and Install Dependencies

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

You will see `(venv)` at the start of your prompt when the environment is active.

---

## Step 7: Configure Environment Variables (Optional)

The agent works out of the box with no `.env` file. Optionally copy and edit it to customize behavior:

```bash
cp .env.example .env
open -e .env
```

The main things you might want to change:

```env
MAX_ITERATIONS=10          # Lower this if hitting Pro token limits
CODING_AGENT_MODEL=sonnet  # Change to haiku to save tokens
USE_PLAYWRIGHT=false       # Set to true to enable browser UI testing
```

---

## Step 8: Write Your Task Spec

Edit `prompts/task_spec.txt` to describe what you want the agent to build:

```bash
open -e prompts/task_spec.txt
```

Replace the example content with your own project description. See `prompts/example_task_specs/` for examples.

---

## Step 9: Run the Agent

```bash
python3.12 autonomous_agent_pro.py --project-dir my-app
```

The agent will:
1. Read your task spec
2. Create `TASKS.md` in the project folder with a breakdown of the work
3. Start implementing tasks one by one
4. Commit work to git after each task (if GitHub is enabled)

**The first session sets up the project and implements the first task.** Subsequent runs pick up where it left off.

---

## Every Time You Return

```bash
cd ~/Desktop/harness/YOUR_REPO
source venv/bin/activate
python3.12 autonomous_agent_pro.py --project-dir my-app
```

Check progress anytime by opening the project's `TASKS.md`:

```bash
cat generations/my-app/TASKS.md
```

---

## Useful Flags

```bash
# Limit iterations to stay within Pro token limits
python3.12 autonomous_agent_pro.py --project-dir my-app --max-iterations 5

# Use a better model for the orchestrator
python3.12 autonomous_agent_pro.py --project-dir my-app --model sonnet

# Disable GitHub if you just want local code
python3.12 autonomous_agent_pro.py --project-dir my-app --no-github

# Put generated projects somewhere else
python3.12 autonomous_agent_pro.py --generations-base ~/projects --project-dir my-app
```

---

## Troubleshooting

**`python: command not found`** -- use `python3` or `python3.12` instead.

**`claude-agent-sdk has no matching versions`** -- your Python is too old. Run `brew install python@3.12`.

**`externally-managed-environment`** -- use a virtual environment. See Step 6.

**`claude login` fails** -- make sure you have an active Claude Pro subscription at [claude.ai](https://claude.ai).

**`gh: command not found`** -- install with `brew install gh`, then run `gh auth login`.

**`gh auth status` fails** -- run `gh auth login` and follow the prompts.

**Hit Pro token limit mid-session** -- the agent will stop cleanly. Wait a few minutes and run the same command to resume from where it left off.

**Want to reduce token usage** -- lower `--max-iterations`, switch `CODING_AGENT_MODEL=haiku` in `.env`, or break your task spec into smaller chunks.

**`main.py: No such file or directory`** -- the entry point is `autonomous_agent_pro.py`, not `main.py`.
