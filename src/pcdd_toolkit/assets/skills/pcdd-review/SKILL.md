---
name: pcdd-review
description: Independently review and verify a high-risk PCDD change after its gate passes and before requesting commit approval. Also supports explicit review requests without authorizing external writes.
---

# PCDD Review

The implementer first confirms that the candidate passes its gate. Do not launch reviews before that. The environment must provide code review and an independent verifier agent; if a capability is missing, report it and stop the high-risk commit. Do not simulate independence through self-review.

Follow the language policy in `.pcdd/core.md`: use the user's language for summaries, the project's agreed language for documents, and preserve original quotations verbatim. Keep the `PASS` and `CHANGES` verdicts unchanged.

The implementer prepares two bounded assignments: code review and public-interface verification. Use the native review command when available, otherwise a separate reviewer. Do not assume `/code-review` exists in every client.

Both receive only relevant specs, risk items, the diff including new files, conventions, and required commands. The verifier starts with fresh context, without Log, the implementer's narrative, or previous conclusions. There is no need to reread the entire history.

## Verifier assignment

- Try to demonstrate that a criterion is not met. Run targeted public-interface checks: HTTP, exit codes, output, or observable effects; reading code alone does not demonstrate behavior.
- Do not rerun the entire suite that already passed. Select edge cases relevant to the risk and regression tests for affected contracts.
- Do not modify existing files, configuration, or user data; use an isolated environment. You may deliver new tests in separate files for the implementer to evaluate.
- No cloud access, deployments, publications, stopping others' processes, or Git write operations.
- Return `PASS` or `CHANGES`, evidence per S#, reproducible findings, new tests, and limitations. A criterion without evidence remains unverified, not approved.

## Review closure

The implementer fixes findings and revalidates the final candidate. Adding tests or changing code requires rerunning the gate; material changes return to the relevant reviewer. An earlier review does not cover new changes.

Present a summary that does not require the user to read code: what changes, what could fail, what both reviews found, what was fixed, and what remains unverified. Wait for approval and record its quotation before committing. That approval does not authorize push or publication.
