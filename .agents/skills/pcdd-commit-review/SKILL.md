---
name: pcdd-commit-review
description: Review pending Git changes and organize them into coherent commits by intent and dependency. Use for organizing commits or explicit invocation; honor review-only requests without changing the index or history.
---

# PCDD Commit Review

Read the current checkout's project instructions, `.pcdd/core.md`, and the installed `pcdd-commit` skill unless already loaded. The commit skill defines identity, attribution, signing, gates, and authorization rules for each resulting commit. Resolve paths from this checkout, including worktrees; there is no dependency on another repository's commands or conventions.

This skill organizes commits. `pcdd-review` provides independent code review and verification for high-risk changes; organizing the diff does not replace that control.

An explicit invocation authorizes organizing and creating commits within its stated scope, unless the user restricts the request to review or a proposal. In that case, inspect and return the plan without changing files, the index, or history. An ordinary request to review code alone does not authorize commits. Preserve prior authorization; do not ask to approve the same plan again merely because it contains several commits. High-risk approval remains a separate required checkpoint.

1. Inspect status, full staged and unstaged diffs, and relevant new files. Identify the authorized work; existing staging does not establish ownership or inclusion. Ask only about ambiguity that affects scope, and continue independent authorized work where possible.
2. Group changes by intent and dependencies. Each unit should make sense independently and contain its relevant tests and docs. Isolate high-risk work from unrelated changes; do not split a necessary dependency into a broken intermediate state or impose a line-count quota. A coherent initial scaffold can be one commit.
3. Present a numbered plan with each proposed message, paths or hunks, dependencies, and exclusions. Use the project's commit convention or the English Conventional Commits default from `pcdd-commit`. If only review was requested, stop here without staging or committing.
4. Order prerequisites before their consumers. Validate the actual candidate for each commit according to the project gates. A passing final working tree alone does not prove that an intermediate commit works. Reuse evidence only when it covers that candidate and project rules allow it; do not repeat costly tests without a change or unresolved concern.
5. Execute each authorized unit through the `pcdd-commit` workflow, preserving unrelated staging and work. Keep the user's identity; never add `Co-Authored-By`, textual signatures, or AI attribution. Respect cryptographic signing and hooks. Complete `pcdd-review` and obtain the required risk approval before any high-risk commit; do not simulate an independent review yourself.
6. Verify the resulting sequence, messages, paths, and remaining status against the plan. Report hashes and exclusions. Push only with explicit authorization and to its specified destination. On divergence, inspect and report the situation; do not force-push, rebase, or overwrite remote work without the required authorization.

Do not impose a PR, new branch, model switch, or routine subagents. Respond in the user's language. Ask only about unresolved scope, unauthorized destructive actions, required high-risk approval, or concrete environment blockers.
