# PCDD — Project conventions

- Maintain agent instructions and distributed templates in English. The public README is in English; other project documentation stays in Spanish. Code, identifiers, tests, and commit messages use English.
- Feature status lives in `docs/roadmap.md`; work records live in `pcdd/changes/<change>.md`. Load only relevant specs/tasks and continuation notes; consult Log when a decision needs clarification.
- Architecture and distribution decisions: `docs/design.md`. Usage: `USAGE.md`. Verification evidence: `docs/verification.md`.
- Use this checkout's CLI: `python3 pcdd.py` from the repository root (add `--json` for machine-readable output). Do not rely on a different PCDD installation from PATH.
- Runtime: Python 3.9+, no runtime dependencies. Public CLI tests use temporary projects; there is no database gate. Gate commands live in `.pcdd/config.json`.
- Commits require explicit authorization; implementation or spec approval alone does not authorize committing. Follow the high-risk checkpoint in the installed core when applicable.
- Develop distributed instructions in `assets/`. The installed `.pcdd/core.md` and adapter skills are managed snapshots, not editable sources. Keep them fixed while implementing instruction changes. After validation, preview and explicitly refresh this installation with `python3 pcdd.py update --dry-run` and `python3 pcdd.py update` within the authorized scope; use a new client session to load refreshed skills. Do not update them automatically during a change.
<!-- pcdd:begin -->
Read `.pcdd/core.md` for the workflow. Load only relevant skills.
<!-- pcdd:end -->
