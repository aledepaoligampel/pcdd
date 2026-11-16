# PCDD

**Progressive Change-Driven Development**

Each change, just enough process.

PCDD is a local toolkit for working with AI coding agents. It helps a person and an agent agree on a change, keep enough context to resume it, and verify the result before calling it done.

The idea is to add structure as the work needs it. A small, well-understood fix can proceed directly. A substantial change gets approved specifications, tasks, and evidence. A risky change gets independent review and verification before commit approval. Size alone does not determine risk.

## How it works

1. **Understand the request.** The agent reads relevant project context and resolves decisions that affect the work.
2. **Define the change.** For substantial work, record verifiable specifications and get approval before implementation.
3. **Implement and verify.** Use test-first development when there is a deterministic test and a clear expected result; otherwise record the alternative evidence. Run the project's checks.
4. **Keep continuity.** Record tasks, evidence, and the next step in a change document so a new session can pick up the work.
5. **Accept the result.** The user tests the outcome before the change is considered complete. Commits and publication follow the project's authorization rules.

The starting context stays small: a short core points the agent to relevant instructions and project files. Detailed skills are loaded when needed.

## PCDD, SDD, and ODD

These approaches overlap. The comparison below describes their organizing ideas; individual implementations can differ.

| Approach | Organizing idea | Practical emphasis |
| --- | --- | --- |
| **SDD — Spec-Driven Development** | Use a specification to guide implementation and verification. | Make intended behavior explicit and carry it through planning, code, and checks. |
| **ODD — Organic Driven Development** | Adapt the workflow to the request and available context. | Handle understood work directly and preserve context for substantial work. |
| **PCDD — Progressive Change-Driven Development** | Organize work around a change, adding definition and checks as needed. | Use approved specifications for substantial work, independent review for high risk, and local records for continuation and acceptance. |

PCDD uses specifications and adapts process to the work. Its concrete choices are a local CLI, Markdown change records, project-owned gates, and agent skills. It does not require an external memory service or a particular application stack. No comparative token, speed, or quality advantage has been established.

## What's included

- **Codex, Claude Code, and Antigravity adapters**, installed in the target project.
- **Four skills:** `pcdd-work`, `pcdd-review`, `pcdd-commit`, and `pcdd-commit-review`.
- **Installation and maintenance:** preview changes, check an installation, update managed files, and recover or roll back transactions.
- **Change records:** specifications, task states, verification evidence, and continuation notes.
- **Progress and time:** task counts and explicitly recorded work intervals, available as human-readable output or JSON.
- **English and Spanish CLI output.** Agent responses follow the user's language; project documents follow the project's conventions.

## Try it

Requires **Python 3.9+**, with no runtime dependencies. Install it in one line (it installs [uv](https://docs.astral.sh/uv/) if it's missing):

```sh
curl -fsSL https://pcdd.dev/install.sh | sh
```

Or install the [`pcdd` package from PyPI](https://pypi.org/project/pcdd/) with uv (recommended) or [pipx](https://pipx.pypa.io/). Both put the `pcdd` command on your `PATH` in an isolated environment:

```sh
uv tool install pcdd
# or
pipx install pcdd
```

If you don't have uv, install it with `brew install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh` (see the [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/) for Windows and other options). For pipx, use `brew install pipx && pipx ensurepath`. Open a new terminal afterwards so `pcdd` is on your `PATH`.

You can also install the latest `main` with `uv tool install pcdd --from git+https://github.com/aledepaoligampel/pcdd`, or from a local checkout with `uv tool install /path/to/pcdd` or `pipx install /path/to/pcdd`. To upgrade, run `uv tool upgrade pcdd` or `pipx upgrade pcdd`.

Then work from the project where you want to use PCDD:

```sh
cd /path/to/your-project
pcdd init --dry-run
pcdd init
pcdd doctor
```

`init` installs Codex and Claude Code by default. Select Antigravity with `pcdd init --adapters antigravity`, or combine adapters with commas, such as `--adapters codex,claude,antigravity`. Codex and Antigravity share `AGENTS.md` and the four skills in `.agents/skills/`; Claude Code also uses `CLAUDE.md` and `.claude/skills/`. Review the preview before applying it. Existing installations keep their adapter selection when updated.

Without installing, you can run a checkout directly with `python3 /path/to/pcdd/pcdd.py` or add `/path/to/pcdd/bin` to your `PATH`; use `--project /path/to/your-project` before the subcommand to target a project without changing directories.

Open a new agent session in the target project and describe the change you want. The installed instructions guide the agent through the appropriate workflow. Configure real project checks before committing; a fresh installation has no gate commands yet.

To check the toolkit itself:

```sh
make ready
make package-check  # builds and installs a wheel in a temporary venv; needs network
```

See [usage and recovery](USAGE.md), [design](docs/design.md), and the [roadmap](docs/roadmap.md) for details. These project documents are currently in Spanish.

PCDD is released under the [MIT License](LICENSE).

## Current scope

PCDD v0.4 is an early toolkit. Antigravity installation is covered by CLI tests, with a discovery and continuation pilot in Antigravity CLI. Behavior in the graphical IDE has not been verified; check discovery in the client you use. The CLI manages files and records; the instructions guide agent behavior. It does not technically enforce every workflow rule or guarantee that a model follows it.

Task counts measure completed tasks, not effort. Recorded time covers explicitly opened and closed intervals, not necessarily the full development duration. Project checks and human acceptance remain necessary.
