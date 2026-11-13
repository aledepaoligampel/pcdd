---
name: pcdd-commit
description: Create a coherent Git commit within the user's authorized scope, preserving unrelated work and staging. Use for commit requests or explicit invocation; a review-only request does not authorize Git writes.
---

# PCDD Commit

Read the current checkout's project instructions and `.pcdd/core.md`, unless already loaded. Discover applicable commit conventions and gate commands from that project; do not assume a package manager, directory layout, or separate command file. Resolve the root with `git rev-parse --show-toplevel` and work in that checkout, including worktrees.

## Scope and authorization

An explicit invocation or request to commit authorizes commits within the stated scope. Present the message and paths as an informative update and proceed without asking for equivalent approval again. An explicit push request may include preparing necessary commits for the named work, subject to project rules; preserve its specified destination. A commit request alone never authorizes push, PR, merge, or publication.

PCDD's high-risk control still applies: the candidate must pass its gate, receive code review and independent verification through `pcdd-review`, and receive human approval of the risk summary before committing. General commit authorization or spec approval does not replace that checkpoint. Preserve an approval already granted for the same candidate and scope.

If the request is only to review or propose, return findings without changing the index or history. If scope is ambiguous, inspect first and ask only about the unresolved part. Do not infer ownership or include another effort merely because it is dirty or staged.

## Prepare and commit

1. Inspect status, complete staged and unstaged diffs, and relevant untracked files. Check Git author and committer identity without replacing it with an agent identity. If identity is missing or inconsistent with the requested author, resolve that before committing; do not invent it.
2. Confirm that the changes express one coherent intent. If they need multiple commits, use `pcdd-commit-review`; the existing authorization remains valid for the same scope. Include related tests and documentation with each unit. Do not force a split by line count.
3. Run the project's applicable gates for the candidate, including its database gate when required. Existing evidence is reusable only if it covers this candidate and project rules allow it. Do not bypass failures, label missing checks as passed, or substitute an unrelated benchmark. Apply the high-risk checkpoint when relevant.
4. Exclude secrets, real environment files, private keys/certificates, generated dependencies, builds, and scratch files unless the project intentionally tracks an appropriate non-secret artifact. Review example environment files for real credentials. Preserve unrelated files and staged changes.
5. Follow the project's commit convention. If none exists, use English Conventional Commits: `type(scope): imperative description`, with a subject no longer than 72 characters and an optional body explaining why. Use an existing meaningful scope; do not invent a fixed module catalog. Reference the actual change document and task/spec IDs when relevant, without inventing them.
6. Show the message and included paths. Stage explicit paths or selected hunks, never indiscriminately run `git add .` or `git add -A`. A path can contain both authorized and unrelated edits: preserve those hunks and any pre-existing staging. Isolate the candidate safely; ask about the affected scope if that cannot be done without losing or including unrelated staging.
7. Review the entire candidate index and staged diff before committing. Keep the user's Git identity. Never add `Co-Authored-By` trailers, textual signatures, or AI attribution to commit messages or PR descriptions. Do not rewrite unrelated messages or history to enforce this on earlier commits.
8. Write the message literally to a temporary file and use `git commit -F <message-file>`, with no shell expansion of its contents. Respect configured cryptographic signing and hooks: do not disable signing, change persistent Git configuration, or bypass hooks to make a commit succeed. A signing or hook failure is a concrete blocker to resolve, not permission to bypass it.
9. Inspect the resulting commit's message, author/committer, and changed paths, then check remaining status and staging. Report its hash, summary, checks, and remaining work. If a hook changed the result unexpectedly, explain it and resolve within authorization; do not silently amend or reset history. Push only when explicitly authorized, to the specified destination; no force-push or history rewriting without specific authorization.

If no changes remain in scope, report that without creating an empty commit. Do not impose a PR, new branch, model switch, or routine delegation. Distinguish missing user authorization from an actual sandbox restriction. Respond in the user's language; follow the project's language convention for the commit message.
