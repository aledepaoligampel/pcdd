---
name: pcdd-work
description: Define, implement, or resume a substantial change in a PCDD project, preserving specs, tasks, and evidence across sessions. Also handles requests to save progress or continue where work stopped, in the user's language.
---

# PCDD Work

Consult `.pcdd/core.md` if you have not read it yet. Do not reread the entire project. Use `--json` to consume CLI results, for example `pcdd --json time status <name>`; human output is not a parsing contract.

Follow the language policy in the core: respond in the user's language, write project content in its agreed language, and preserve quotations verbatim. Recognize save/resume requests by meaning in the user's language; no exact phrase is required. Translate user-facing examples below as appropriate. Keep `## Tasks`, task IDs, state markers, and command syntax unchanged because the CLI parses them. Preserve existing document headings; the continuation section may be called `Continuation`, `Continuación`, or the project's equivalent.

- If no change exists yet, recover scope from relevant documentation discovered through the core. A brief is context, not automatic approval: distinguish confirmed decisions from proposals before drafting specs. Do not require a fixed filename or ask again for information already documented.
- Identify the change in the roadmap if one exists. The roadmap tracks feature status; the change document tracks tasks. Do not create a roadmap just to duplicate a document.
- Create the document with `pcdd new <name>` (or `python3 /path/to/pcdd.py new <name>` if the CLI is not on PATH). The path resolves from the target project. Adapt the new template's prose to the project's language; do not rewrite existing documents merely to match the English template.
- Specs S#: original quotation, verifiable behavior, and acceptance criterion. Identify agent proposals; do not attribute them to the user. Adopt inherited rules explicitly.
- Before coding, obtain approval for new specs and record the quotation in Log. Link tasks to S#, with evidence and a commit when one exists. Do not invent hashes.
- Task format: `- [ ] T1 (S1) description`. States: space for pending, `>` in progress, `!` blocked, `x` completed. IDs must be unique. Keep only tasks in `## Tasks`; put detailed evidence in the evidence section.
- Complete a task when it meets its criterion and has evidence. Explain scope when tasks are added; a changed denominator does not automatically mean regression.
- Track time with `pcdd time start <name>`. Use `pause` or `stop` to close the interval before waiting for a reply or ending the turn. Tests and builds count as work; human waiting does not. Each start is an interval, not necessarily a chat session.
- On resuming, consult `pcdd time status <name>`. If an interval from another session remains open and its end is unknown, use `abandon`, not `stop`: it remains incomplete and excluded from the total. Do not estimate missing time. Then start a new interval.
- Report progress when status changes, in its own paragraph at the end of the summary, separated from the preceding text by a blank line: `**PCDD** · 4/6 tasks completed · 18 min`. Show only the task count and measured duration, using minutes and seconds when useful. Omit timer status and recording details such as “recorded since the timer started” or “timer paused”. Do not append the paragraph to a sentence about files or continuation. Use the confirmed closed total; do not invent unmeasured time. Explain missing or incomplete timing separately only when it materially affects the result. Do not confuse task counts with effort or final acceptance.
- Before pausing, update the continuation section with the next step, blocker, and current evidence. Preserve original decisions in Log; consult it only to resolve uncertainty.
- At delivery, report behavior, validation, residual risks, recorded time and incomplete intervals, and human testing steps. Keep acceptance pending until the user tests and confirms.

If the CLI is missing or fails, report it; do not invent metrics or download tools automatically. Tasks can be maintained in Markdown while the limitation is resolved.

## Save progress

Keep the continuation section current when closing a unit of work; do not wait until context is exhausted. When the user asks to save progress, save a resumption point in the change document. If none exists and work must persist across sessions, create a minimal record using the project's format.

- Leave a short account of the current task and concrete next action; implemented versus verified work; blockers; relevant specs and references to recorded approvals. Preserve quotations in Log without duplicating or reinterpreting them.
- Record relevant modified files, branch/commit if available, checks run, and the state they covered. Distinguish uncommitted work from others' changes; do not invent ownership or hashes.
- Include discarded attempts only when they prevent repeating a mistake, and your own active processes if they affect continuation. Do not copy the conversation, secrets, or complete tool output.
- Close the known time interval before finishing; do not complete tasks or create commits merely to save progress. If saving or closing the timer fails, report what was not persisted.
- Verify that the document was saved. Identify the change and say, in the user's language: “Progress saved. You can open a new session and ask: ‘Continue where we left off.’” Include the change name in that phrase if several efforts are active.

## Continue where work stopped

- Identify the requested change. Use it if only one is active; ask which one if several are plausible. Do not choose solely by file date or read every Log.
- Read the continuation section, relevant tasks, and their specs. Consult referenced evidence or approvals only when needed.
- Compare the note with files, the diff, and Git status if available. Reconcile subsequent changes without overwriting them; ask only about contradictions that affect scope or authorization. Do not treat a test on different code as current evidence.
- Check the timer: abandon a previous interval with no known end as incomplete, never add estimated time. Start a new interval when work resumes.
- Preserve previous approvals and continue with the next action within their scope. Do not restart planning or ask to approve the same work again. Saving progress did not authorize new work.

The agent may suggest switching sessions at a stable point if the conversation has accumulated irrelevant context. Do not assume access to a context percentage or promise to open a new session automatically. These phrases are requests to the agent, not CLI subcommands.
