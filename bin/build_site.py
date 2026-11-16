#!/usr/bin/env python3
"""Generate the static landing pages in site/ from one template.

Usage: python3 bin/build_site.py [--check]

The site is served as plain files (no build on the host). This script only keeps
the English and Spanish pages in sync; run it after editing copy or markup and
commit the output. --check exits 1 if the committed pages are out of date.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
REPO = "https://github.com/aledepaoligampel/pcdd"
INSTALL = "curl -fsSL https://pcdd.dev/install.sh | sh"
PACKAGE_VERSION = re.search(r"__version__ = '([^']+)'",
                            (ROOT / "src" / "pcdd_toolkit" / "__init__.py").read_text(encoding="utf-8")).group(1)
VERSION = "v" + ".".join(PACKAGE_VERSION.split(".")[:2])

LOGO = ('<svg aria-hidden="true" width="{s}" height="{s}" viewBox="0 0 48 48">'
        '<path d="M4 40 L44 40 L38.7 31 L9.3 31 Z" fill="#C8F560"/>'
        '<path d="M11.1 28 L36.9 28 L32.2 20 L15.8 20 Z" fill="#C8F560" opacity=".6"/>'
        '<path d="M17.5 17 L30.5 17 L24 6 Z" fill="#C8F560" opacity=".3"/></svg>')
CHECK = ('<svg class="ok" aria-hidden="true" width="14" height="14" viewBox="0 0 24 24" fill="none" '
         'stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">'
         '<path d="M4 12.5l5 5L20 6.5"/></svg>')
CROSS = ('<svg class="x" aria-hidden="true" width="14" height="14" viewBox="0 0 24 24" fill="none" '
         'stroke="currentColor" stroke-width="2.6" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>')
STAR = ('<svg aria-hidden="true" width="14" height="14" viewBox="0 0 24 24" fill="#C8F560">'
        '<path d="M12 2.5l2.9 6.1 6.6.8-4.9 4.6 1.3 6.6L12 17.3l-5.9 3.3 1.3-6.6-4.9-4.6 6.6-.8z"/></svg>')
GITHUB = ('<svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
          'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 19c-4.3 1.4-4.3-2.5-6-3m12 '
          '5v-3.5c0-1 .1-1.4-.5-2 2.8-.3 5.5-1.4 5.5-6a4.6 4.6 0 0 0-1.3-3.2 4.2 4.2 0 0 0-.1-3.2s-1.1-.3-3.5 '
          '1.3a12.3 12.3 0 0 0-6.2 0C6.5 2.8 5.4 3.1 5.4 3.1a4.2 4.2 0 0 0-.1 3.2A4.6 4.6 0 0 0 4 9.5c0 4.6 2.7 '
          '5.7 5.5 6-.6.6-.6 1.2-.5 2V21"/></svg>')
AGENTS = [
    ("Codex", "OpenAI", '<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M22.2819 9.8211a5.9847 5.9847 0 0 0-.5157-4.9108 6.0462 6.0462 0 0 0-6.5098-2.9A6.0651 6.0651 0 0 0 4.9807 4.1818a5.9847 5.9847 0 0 0-3.9977 2.9 6.0462 6.0462 0 0 0 .7427 7.0966 5.98 5.98 0 0 0 .511 4.9107 6.051 6.051 0 0 0 6.5146 2.9001A5.9847 5.9847 0 0 0 13.2599 24a6.0557 6.0557 0 0 0 5.7718-4.2058 5.9894 5.9894 0 0 0 3.9977-2.9001 6.0557 6.0557 0 0 0-.7475-7.0729zm-9.022 12.6081a4.4755 4.4755 0 0 1-2.8764-1.0408l.1419-.0804 4.7783-2.7582a.7948.7948 0 0 0 .3927-.6813v-6.7369l2.02 1.1686a.071.071 0 0 1 .038.052v5.5826a4.504 4.504 0 0 1-4.4945 4.4944zm-9.6607-4.1254a4.4708 4.4708 0 0 1-.5346-3.0137l.142.0852 4.783 2.7582a.7712.7712 0 0 0 .7806 0l5.8428-3.3685v2.3324a.0804.0804 0 0 1-.0332.0615L9.74 19.9502a4.4992 4.4992 0 0 1-6.1408-1.6464zM2.3408 7.8956a4.485 4.485 0 0 1 2.3655-1.9728V11.6a.7664.7664 0 0 0 .3879.6765l5.8144 3.3543-2.0201 1.1685a.0757.0757 0 0 1-.071 0l-4.8303-2.7865A4.504 4.504 0 0 1 2.3408 7.872zm16.5963 3.8558L13.1038 8.364 15.1192 7.2a.0757.0757 0 0 1 .071 0l4.8303 2.7913a4.4944 4.4944 0 0 1-.6765 8.1042v-5.6772a.79.79 0 0 0-.407-.667zm2.0107-3.0231l-.142-.0852-4.7735-2.7818a.7759.7759 0 0 0-.7854 0L9.409 9.2297V6.8974a.0662.0662 0 0 1 .0284-.0615l4.8303-2.7866a4.4992 4.4992 0 0 1 6.6802 4.66zM8.3065 12.863l-2.02-1.1638a.0804.0804 0 0 1-.038-.0567V6.0742a4.4992 4.4992 0 0 1 7.3757-3.4537l-.142.0805L8.704 5.459a.7948.7948 0 0 0-.3927.6813zm1.0976-2.3654l2.602-1.4998 2.6069 1.4998v2.9994l-2.5974 1.4997-2.6067-1.4997Z"/></svg>'),
    ("Claude Code", "Anthropic", '<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="m4.7144 15.9555 4.7174-2.6471.079-.2307-.079-.1275h-.2307l-.7893-.0486-2.6956-.0729-2.3375-.0971-2.2646-.1214-.5707-.1215-.5343-.7042.0546-.3522.4797-.3218.686.0608 1.5179.1032 2.2767.1578 1.6514.0972 2.4468.255h.3886l.0546-.1579-.1336-.0971-.1032-.0972L6.973 9.8356l-2.55-1.6879-1.3356-.9714-.7225-.4918-.3643-.4614-.1578-1.0078.6557-.7225.8803.0607.2246.0607.8925.686 1.9064 1.4754 2.4893 1.8336.3643.3035.1457-.1032.0182-.0728-.164-.2733-1.3539-2.4467-1.445-2.4893-.6435-1.032-.17-.6194c-.0607-.255-.1032-.4674-.1032-.7285L6.287.1335 6.6997 0l.9957.1336.419.3642.6192 1.4147 1.0018 2.2282 1.5543 3.0296.4553.8985.2429.8318.091.255h.1579v-.1457l.1275-1.706.2368-2.0947.2307-2.6957.0789-.7589.3764-.9107.7468-.4918.5828.2793.4797.686-.0668.4433-.2853 1.8517-.5586 2.9021-.3643 1.9429h.2125l.2429-.2429.9835-1.3053 1.6514-2.0643.7286-.8196.85-.9046.5464-.4311h1.0321l.759 1.1293-.34 1.1657-1.0625 1.3478-.8804 1.1414-1.2628 1.7-.7893 1.36.0729.1093.1882-.0183 2.8535-.607 1.5421-.2794 1.8396-.3157.8318.3886.091.3946-.3278.8075-1.967.4857-2.3072.4614-3.4364.8136-.0425.0304.0486.0607 1.5482.1457.6618.0364h1.621l3.0175.2247.7892.522.4736.6376-.079.4857-1.2142.6193-1.6393-.3886-3.825-.9107-1.3113-.3279h-.1822v.1093l1.0929 1.0686 2.0035 1.8092 2.5075 2.3314.1275.5768-.3218.4554-.34-.0486-2.2039-1.6575-.85-.7468-1.9246-1.621h-.1275v.17l.4432.6496 2.3436 3.5214.1214 1.0807-.17.3521-.6071.2125-.6679-.1214-1.3721-1.9246L14.38 17.959l-1.1414-1.9428-.1397.079-.674 7.2552-.3156.3703-.7286.2793-.6071-.4614-.3218-.7468.3218-1.4753.3886-1.9246.3157-1.53.2853-1.9004.17-.6314-.0121-.0425-.1397.0182-1.4328 1.9672-2.1796 2.9446-1.7243 1.8456-.4128.164-.7164-.3704.0667-.6618.4008-.5889 2.386-3.0357 1.4389-1.882.929-1.0868-.0062-.1579h-.0546l-6.3385 4.1164-1.1293.1457-.4857-.4554.0608-.7467.2307-.2429 1.9064-1.3114Z"/></svg>'),
    ("Antigravity", "Google", '<svg aria-hidden="true" width="24" height="24" viewBox="8 8 96 96" fill="currentColor"><path d="M89.6992 93.695C94.3659 97.195 101.366 94.8617 94.9492 88.445C75.6992 69.7783 79.7825 18.445 55.8659 18.445C31.9492 18.445 36.0325 69.7783 16.7825 88.445C9.78251 95.445 17.3658 97.195 22.0325 93.695C40.1159 81.445 38.9492 59.8617 55.8659 59.8617C72.7825 59.8617 71.6159 81.445 89.6992 93.695Z"/></svg>'),
]
FEATURE_ICONS = [
    '<path d="M14 3v4a1 1 0 0 0 1 1h4"/><path d="M17 21H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h7l5 5v11a2 2 0 0 1-2 2z"/><path d="m9 14 2 2 4-4"/>',
    '<path d="M9 3h6"/><path d="M10 3v6L4.5 18.5A1.6 1.6 0 0 0 6 21h12a1.6 1.6 0 0 0 1.5-2.5L14 9V3"/><path d="M7 15h10"/>',
    '<circle cx="12" cy="12" r="3"/><path d="M12 3v6"/><path d="M12 15v6"/>',
    '<path d="M3 7l9-4 9 4-9 4-9-4z"/><path d="M3 12l9 4 9-4"/><path d="M3 17l9 4 9-4"/>',
]
NODE_IDS = ["ctx", "specs", "tasks", "impl", "checks", "evidence", "review", "accept"]
LEVEL_NODES = [
    ["ctx", "impl", "checks", "accept"],
    ["ctx", "specs", "tasks", "impl", "checks", "evidence", "accept"],
    NODE_IDS,
]

EN = {
    "lang": "en", "path": "/", "other_path": "/es/", "other_lang": "es", "other_name": "Español",
    "title": "PCDD — Ship with AI agents without losing the plot",
    "description": "PCDD gives every change just enough process: a spec when it matters, a record that outlives the session, and a finish line you approve. Works with Codex, Claude Code and Antigravity.",
    "skip": "Skip to content", "home": "pcdd, home",
    "nav": ["Why", "How it works", "Get started", "Compare"],
    "star_label": "Star PCDD on GitHub", "star": "Star",
    "badge": "Open source · MIT · Codex, Claude Code, Antigravity", "acro_extra": "",
    "h1": ["Ship with AI agents.", "Without losing", "the plot."],
    "sub": 'PCDD gives every change <em>just enough process</em>: a spec when it matters, a record that outlives the session, and a finish line you approve.',
    "copy": "Copy", "copied": "Copied", "copy_label": "Copy install command",
    "alt_lead": "or",
    "alt": ["uv tool install pcdd", "pipx install pcdd", "npx @pcdd-dev/cli", "Python 3.9+, zero dependencies"],
    "term_label": "PCDD command-line session", "term_dir": "~/your-project",
    "term": [
        ("cmd", "pcdd init"), ("dim", "  ›_ pcdd · each change, just enough."), ("ok", "PCDD is ready."),
        ("dim", "  Create  .pcdd/core.md"), ("dim", "  Create  AGENTS.md"), ("dim", "  Create  CLAUDE.md"),
        ("out", "Your own content is preserved."), ("gap", ""),
        ("cmd", "pcdd new rate-limit"), ("ok", "Change created: pcdd/changes/rate-limit.md"),
        ("out", "Define specs before implementing."), ("gap", ""),
        ("cmd", "pcdd time status rate-limit"), ("ok", "2/3 tasks completed · 2880 s recorded"),
    ],
    "works": "Works with your agent",
    "works_note": 'Other agents that read <code>AGENTS.md</code> can follow the core — not tested yet.',
    "p_eyebrow": "The problem", "p_h2": "AI coding fails in two opposite ways.",
    "p_lead": "Most teams swing between them. One fix gets a ten-page spec; the next risky migration gets a prompt and a prayer.",
    "p_cards": [
        ("Too little process", "Fast today. Lost tomorrow.", False, [
            "A new session forgets what was decided and why.",
            "“Done” means it compiled, not that it works.",
            "Risky changes get the same treatment as typos."]),
        ("Too much process", "Safe on paper. Skipped in practice.", False, [
            "A full spec for a one-line fix.",
            "Ceremony burns context, tokens and patience.",
            "So people stop following it — even when it matters."]),
        ("PCDD", "Process proportional to risk.", True, [
            "Small, clear work goes straight through.",
            "Substantial work gets approved specs and a record.",
            "Risky work gets independent review before commit."]),
    ],
    "m_eyebrow": "Why it matters", "m_h2": "Thursday morning.<br>New session.",
    "m_lead": "You started a feature on Monday. Same request, same agent — the only difference is what it can read.",
    "m_without": "Without PCDD", "m_with": "With PCDD",
    "m_q1": "Let’s continue the rate limiting work.", "m_q2": "Is it finished?",
    "m_bad1": "Sure! Could you remind me which approach we agreed on and what’s already done?",
    "m_bad2": "Yes, it’s done! The feature is implemented.",
    "m_bad_v": "You re-explain. You find the bug later.",
    "m_good1": 'Resuming <span class="acc">rate-limit</span>: 2/3 tasks done, tests passing. Next step: you test the lockout after 5 attempts.',
    "m_good2": 'The gate passed (<code>make ready</code>). It’s done when you accept it — here’s how to check.',
    "m_good_v": "It reads the record. You decide when it’s done.",
    "h_eyebrow": "How it works", "h_h2": "Pick a change. Watch the process fit.",
    "h_lead": "The agent assesses risk on its own terms, not by line count. Size alone never decides.",
    "group": "Example change", "risk_h": "## Risk",
    "nodes": ["Read context", "Approved specs", "Tasks", "Implement", "Checks", "Evidence", "Independent review", "Your acceptance"],
    "levels": [
        ("small", "Fix a typo in the docs", "Straight through.",
         "Well-understood and bounded. The agent reads just enough context, makes the change and runs the checks. The diff is the record — no change document, no ceremony.",
         "Risk: none", "Record: the diff itself"),
        ("substantial", "Add rate limiting to login", "Define, then build.",
         "The agent proposes verifiable specs and waits for your approval. Tasks, test results and the next step are written to pcdd/changes/rate-limit.md, so any session can pick it up.",
         "Risk: item 2 (security)", "Record: pcdd/changes/rate-limit.md"),
        ("high risk", "Migrate auth to a new provider", "Review before commit.",
         "Irreversible effects and security on the line. After the gate passes, an independent review verifies the work, and you approve from a summary you can actually understand.",
         "Risk: items 1, 2, 3 (data, security, contracts)", "Record: change + independent review"),
    ],
    "c_eyebrow": "Continuity", "c_h2": "Close the laptop.<br>Keep the context.",
    "c_lead": "Every substantial change lives in one Markdown file in your repo: specs, tasks, evidence and the exact next step. A fresh session — or a different agent — reads that, not your entire history.",
    "c_small": "Small starting context. Skills load only when needed. No external memory service.",
    "c_s1": "Session 1 · Codex", "c_s2": "Session 2 · Claude Code", "c_doc_label": "Example change record",
    "c_tasks": "2/3 tasks",
    "c_doc": ["S1 — Limit login attempts per IP. <span class=\"acc\">Approved.</span>",
              "T1 (S1) Write the failing test", "T2 (S1) Implement the limiter", "T3 (S1) Verify and accept",
              "Next step: user tests lockout after 5 attempts."],
    "s_eyebrow": "Get started", "s_h2": "Three steps.<br>Nothing new to learn.",
    "s_lead": "No new app, no account, no config to write. You keep using your agent the way you already do.",
    "s_steps": [
        ("Install once", None, "One line. Installs uv if it’s missing. Python 3.9+, zero runtime dependencies."),
        ("Add it to your project", "pcdd init", 'Preview first with <code>--dry-run</code>. Your own content is preserved, and <code>pcdd rollback</code> undoes it.'),
        ("Just describe the change", "“Add rate limiting to the login endpoint.”", "Open Codex, Claude Code or Antigravity. The agent picks the right amount of process and asks only what it needs."),
    ],
    "y_eyebrow": "You stay in charge", "y_h2": "The agent proposes.<br>You decide.",
    "y_feats": [
        ("You approve the specs", "Verifiable criteria, with your words quoted, before any code is written."),
        ("Evidence, not vibes", "Test-first when the result is clear; otherwise the record says what remains unverified."),
        ("No surprise commits", "Commits, pushes and publishing need your explicit go-ahead. No AI attribution added."),
        ("Yours, locally", "Plain Markdown in your repo. Preview, update and roll back installs. No service, no lock-in."),
    ],
    "x_eyebrow": "Compare", "x_h2": "Not the lightest.<br>The one that fits.",
    "x_lead": "Same change, three approaches. See how much process each one asks for.",
    "x_names": [("SDD", "Spec-Driven"), ("ODD", "Organic Driven"), ("PCDD", "Progressive Change-Driven")],
    "x_step": ("step", "steps"), "x_key": ["Your acceptance", "Independent review"],
    "x_sets": [
        ("Spec-first workflows pay full ceremony for a one-line change. PCDD goes straight through — and you still check the result.",
         ["Spec", "Plan", "Implement", "Checks"], ["Implement", "Checks"], ["Implement", "Checks", "Your acceptance"]),
        ("Here PCDD looks like SDD — plus a change record any session or agent can resume, and your sign-off at the end.",
         ["Spec", "Plan", "Tasks", "Implement", "Checks"], ["Context notes", "Implement", "Checks"],
         ["Approved specs", "Tasks", "Implement", "Checks", "Change record", "Your acceptance"]),
        ("When security and irreversible effects are on the line, PCDD adds an independent review after the gate, before anything is committed.",
         ["Spec", "Plan", "Tasks", "Implement", "Checks"], ["Context notes", "Implement", "Checks"],
         ["Approved specs", "Tasks", "Implement", "Checks", "Change record", "Independent review", "Your acceptance"]),
    ],
    "x_disclaimer": "Shapes follow each approach’s organizing idea; real implementations vary. We haven’t measured time or tokens yet — when we do, we’ll publish the method with the numbers.",
    "f_h2": "Each change,<br>just enough process.", "f_lead": "Install in one line. Try it on your next change.",
    "f_star": "Star on GitHub",
    "footer": "PCDD v0.4 is an early toolkit. The CLI manages files and records; instructions guide the agent but can’t guarantee a model follows them. Checks and your acceptance stay essential. Codex, Claude Code and Antigravity are trademarks of their respective owners; PCDD is not affiliated with them.",
    "og_alt": "PCDD: ship with AI agents without losing the plot.",
    "license": "MIT License", "footer_label": "Footer", "skipped": "skipped", "copied_status": "Install command copied.",
}

ES = dict(EN)
ES.update({
    "lang": "es", "path": "/es/", "other_path": "/", "other_lang": "en", "other_name": "English",
    "title": "PCDD — Programá con agentes de IA sin perder el hilo",
    "description": "PCDD le da a cada cambio el proceso justo: una spec cuando importa, un registro que sobrevive a la sesión y una línea de llegada que aprobás vos. Funciona con Codex, Claude Code y Antigravity.",
    "skip": "Ir al contenido", "home": "pcdd, inicio",
    "nav": ["Por qué", "Cómo funciona", "Empezar", "Comparación"],
    "star_label": "Star a PCDD en GitHub",
    "badge": "Código abierto · MIT · Codex, Claude Code, Antigravity",
    "acro_extra": "<small> · desarrollo progresivo guiado por cambios</small>",
    "h1": ["Programá con IA.", "Sin perder", "el hilo."],
    "sub": 'PCDD le da a cada cambio <em>el proceso justo</em>: una spec cuando importa, un registro que sobrevive a la sesión y una línea de llegada que aprobás vos.',
    "copy": "Copiar", "copied": "Copiado", "copy_label": "Copiar el comando de instalación",
    "alt_lead": "o",
    "alt": ["uv tool install pcdd", "pipx install pcdd", "npx @pcdd-dev/cli", "Python 3.9+, sin dependencias"],
    "term_label": "Sesión de la CLI de PCDD", "term_dir": "~/tu-proyecto",
    "term": [
        ("cmd", "pcdd init"), ("dim", "  ›_ pcdd · cada cambio, el proceso justo."), ("ok", "PCDD está listo."),
        ("dim", "  Crear  .pcdd/core.md"), ("dim", "  Crear  AGENTS.md"), ("dim", "  Crear  CLAUDE.md"),
        ("out", "Tu contenido propio se conserva."), ("gap", ""),
        ("cmd", "pcdd new rate-limit"), ("ok", "Change creado: pcdd/changes/rate-limit.md"),
        ("out", "Definí las specs antes de implementar."), ("gap", ""),
        ("cmd", "pcdd time status rate-limit"), ("ok", "2/3 tareas completadas · 2880 s registrados"),
    ],
    "works": "Funciona con tu agente",
    "works_note": 'Otros agentes que leen <code>AGENTS.md</code> pueden seguir el núcleo; todavía sin probar.',
    "p_eyebrow": "El problema", "p_h2": "Programar con IA falla de dos formas opuestas.",
    "p_lead": "La mayoría oscila entre las dos. Un arreglo chico recibe una spec de diez páginas; la migración riesgosa siguiente, un prompt y una plegaria.",
    "p_cards": [
        ("Poco proceso", "Rápido hoy. Perdido mañana.", False, [
            "Una sesión nueva olvida qué se decidió y por qué.",
            "«Listo» significa que compila, no que funciona.",
            "Un cambio riesgoso recibe el mismo trato que un typo."]),
        ("Demasiado proceso", "Seguro en papel. Salteado en la práctica.", False, [
            "Una spec completa para un arreglo de una línea.",
            "La ceremonia consume contexto, tokens y paciencia.",
            "Entonces se deja de seguir, incluso cuando importa."]),
        ("PCDD", "Proceso proporcional al riesgo.", True, [
            "Lo chico y claro avanza directo.",
            "Lo sustancial lleva specs aprobadas y un registro.",
            "Lo riesgoso lleva revisión independiente antes del commit."]),
    ],
    "m_eyebrow": "Por qué importa", "m_h2": "Jueves a la mañana.<br>Sesión nueva.",
    "m_lead": "Empezaste una feature el lunes. Mismo pedido, mismo agente: lo único que cambia es lo que puede leer.",
    "m_without": "Sin PCDD", "m_with": "Con PCDD",
    "m_q1": "Sigamos con el rate limiting.", "m_q2": "¿Está terminado?",
    "m_bad1": "¡Claro! ¿Me recordás qué enfoque acordamos y qué está hecho?",
    "m_bad2": "¡Sí, listo! La feature está implementada.",
    "m_bad_v": "Volvés a explicar. El bug aparece después.",
    "m_good1": 'Retomo <span class="acc">rate-limit</span>: 2/3 tareas hechas, tests en verde. Próximo paso: probás el bloqueo después de 5 intentos.',
    "m_good2": 'Pasó el gate (<code>make ready</code>). Está terminado cuando vos lo aceptes; te explico cómo probarlo.',
    "m_good_v": "Lee el registro. Vos decidís cuándo está listo.",
    "h_eyebrow": "Cómo funciona", "h_h2": "Elegí un cambio. Mirá cómo se ajusta el proceso.",
    "h_lead": "El agente evalúa el riesgo por lo que el cambio toca, no por la cantidad de líneas. El tamaño solo nunca decide.",
    "group": "Cambio de ejemplo", "risk_h": "## Riesgo",
    "nodes": ["Leer contexto", "Specs aprobadas", "Tareas", "Implementar", "Checks", "Evidencia", "Revisión independiente", "Tu aceptación"],
    "levels": [
        ("chico", "Corregir un typo en la documentación", "Directo.",
         "Bien entendido y acotado. El agente lee el contexto justo, hace el cambio y corre los checks. El diff es el registro: sin documento de cambio, sin ceremonia.",
         "Risk: none", "Registro: el diff"),
        ("sustancial", "Agregar rate limiting al login", "Definí, después construí.",
         "El agente propone specs verificables y espera tu aprobación. Tareas, resultados de tests y el próximo paso se escriben en pcdd/changes/rate-limit.md, así cualquier sesión puede retomarlo.",
         "Risk: item 2 (seguridad)", "Registro: pcdd/changes/rate-limit.md"),
        ("alto riesgo", "Migrar la autenticación a otro proveedor", "Revisión antes del commit.",
         "Hay efectos irreversibles y seguridad en juego. Después de pasar los checks, una revisión independiente verifica el trabajo y vos aprobás a partir de un resumen que se entiende.",
         "Risk: items 1, 2, 3 (datos, seguridad, contratos)", "Registro: change + revisión independiente"),
    ],
    "c_eyebrow": "Continuidad", "c_h2": "Cerrá la notebook.<br>El contexto queda.",
    "c_lead": "Cada cambio sustancial vive en un archivo Markdown en tu repo: specs, tareas, evidencia y el próximo paso exacto. Una sesión nueva, o incluso otro agente, lee eso y no todo tu historial.",
    "c_small": "Contexto inicial chico. Las skills se cargan solo cuando hacen falta. Sin servicio de memoria externo.",
    "c_s1": "Sesión 1 · Codex", "c_s2": "Sesión 2 · Claude Code", "c_doc_label": "Ejemplo de registro de cambio",
    "c_tasks": "2/3 tareas",
    "c_doc": ["S1 — Limitar intentos de login por IP. <span class=\"acc\">Aprobada.</span>",
              "T1 (S1) Escribir el test que falla", "T2 (S1) Implementar el limitador", "T3 (S1) Verificar y aceptar",
              "Next step: el usuario prueba el bloqueo tras 5 intentos."],
    "s_eyebrow": "Empezar", "s_h2": "Tres pasos.<br>Nada nuevo que aprender.",
    "s_lead": "Sin app nueva, sin cuenta, sin configuración que escribir. Seguís usando tu agente como ya lo hacés.",
    "s_steps": [
        ("Instalá una vez", None, "Una línea. Instala uv si falta. Python 3.9+, sin dependencias de runtime."),
        ("Sumalo a tu proyecto", "pcdd init", 'Mirá antes la vista previa con <code>--dry-run</code>. Tu contenido se conserva y <code>pcdd rollback</code> lo deshace.'),
        ("Contale el cambio", "«Agregá rate limiting al endpoint de login.»", "Abrí Codex, Claude Code o Antigravity. El agente elige cuánto proceso hace falta y pregunta solo lo necesario."),
    ],
    "y_eyebrow": "Vos tenés el control", "y_h2": "El agente propone.<br>Vos decidís.",
    "y_feats": [
        ("Vos aprobás las specs", "Criterios verificables, con tus palabras citadas, antes de escribir código."),
        ("Evidencia, no intuición", "Test primero cuando el resultado es claro; si no, el registro dice qué queda sin verificar."),
        ("Sin commits sorpresa", "Commits, push y publicación requieren tu permiso explícito. Sin atribución de IA."),
        ("Tuyo, en local", "Markdown plano en tu repo. Instalaciones con vista previa, actualización y rollback. Sin servicio ni lock-in."),
    ],
    "x_eyebrow": "Comparación", "x_h2": "No es el más liviano.<br>Es el que encaja.",
    "x_lead": "El mismo cambio, tres enfoques. Mirá cuánto proceso pide cada uno.",
    "x_step": ("paso", "pasos"), "x_key": ["Tu aceptación", "Revisión independiente"],
    "x_sets": [
        ("Los flujos que exigen spec primero pagan la ceremonia completa por un cambio de una línea. PCDD avanza directo, y vos igual revisás el resultado.",
         ["Spec", "Plan", "Implementar", "Checks"], ["Implementar", "Checks"], ["Implementar", "Checks", "Tu aceptación"]),
        ("Acá PCDD se parece a SDD, más un registro de cambio que cualquier sesión o agente puede retomar y tu aprobación al final.",
         ["Spec", "Plan", "Tareas", "Implementar", "Checks"], ["Notas de contexto", "Implementar", "Checks"],
         ["Specs aprobadas", "Tareas", "Implementar", "Checks", "Registro de cambio", "Tu aceptación"]),
        ("Cuando hay seguridad y efectos irreversibles en juego, PCDD suma una revisión independiente después de los checks y antes de cualquier commit.",
         ["Spec", "Plan", "Tareas", "Implementar", "Checks"], ["Notas de contexto", "Implementar", "Checks"],
         ["Specs aprobadas", "Tareas", "Implementar", "Checks", "Registro de cambio", "Revisión independiente", "Tu aceptación"]),
    ],
    "x_disclaimer": "La forma de cada columna sigue la idea organizadora de cada enfoque; las implementaciones reales varían. Todavía no medimos tiempo ni tokens: cuando lo hagamos, publicaremos el método junto con los números.",
    "f_h2": "Cada cambio,<br>el proceso justo.", "f_lead": "Se instala en una línea. Probalo en tu próximo cambio.",
    "f_star": "Dale una estrella en GitHub",
    "footer": "PCDD v0.4 es un toolkit temprano. La CLI gestiona archivos y registros; las instrucciones guían al agente pero no garantizan que el modelo las siga. Los checks y tu aceptación siguen siendo esenciales. Codex, Claude Code y Antigravity son marcas de sus respectivos dueños; PCDD no está afiliado a ellos.",
    "og_alt": "PCDD: programá con agentes de IA sin perder el hilo.",
    "license": "Licencia MIT", "footer_label": "Pie de página", "skipped": "omitido", "copied_status": "Comando de instalación copiado.",
    "star": "Star",
})


def cmd_box(t, extra=""):
    return (f'<div class="cmd beam{extra}"><code><span class="p">$ </span>{INSTALL}</code>'
            f'<button type="button" hidden data-copy="{INSTALL}" data-done="{t["copied"]}" '
            f'aria-label="{t["copy_label"]}">{t["copy"]}</button></div>')


def head_block(eyebrow, h2, lead=None):
    lead_html = f'<p class="lead">{lead}</p>' if lead else ""
    return f'<div class="head reveal"><p class="eyebrow">{eyebrow}</p><h2>{h2}</h2>{lead_html}</div>'


def tabs(t, name, items, current):
    buttons = "".join(
        f'<button type="button" aria-pressed="{"true" if i == current else "false"}">'
        f'<small>{tag}</small><span>{label}</span></button>'
        for i, (tag, label) in enumerate(items))
    return f'<div class="tabs" role="group" aria-label="{t["group"]}" data-tabs="{name}">{buttons}</div>'


def levels(t):
    out = []
    for i, (tag, label, title, body, risk, record) in enumerate(t["levels"]):
        skipped = f'<span class="sr"> ({t["skipped"]})</span>'
        nodes = "".join(
            f'<li class="{"on" if nid in LEVEL_NODES[i] else "off"}{" key" if nid in ("review", "accept") else ""}">'
            f'{name}{"" if nid in LEVEL_NODES[i] else skipped}</li>'
            for nid, name in zip(NODE_IDS, t["nodes"]))
        out.append(
            f'<div class="level{" cur" if i == 1 else ""}" data-panel="levels"><div class="pipe">'
            f'<div class="nodes-w"><span aria-hidden="true" class="wire"></span><ol class="nodes">{nodes}</ol></div>'
            f'<div class="detail"><div><h3><span class="tabtag">{label}: </span>{title}</h3><p>{body}</p></div>'
            f'<div class="riskbox"><span>{t["risk_h"]}</span><b>{risk}</b><span>{record}</span></div></div>'
            f'</div></div>')
    return "".join(out)


def compare(t):
    out = []
    for i, (note, sdd, odd, pcdd) in enumerate(t["x_sets"]):
        cols = []
        for (name, sub), steps, mine in zip(t["x_names"], (sdd, odd, pcdd), (False, False, True)):
            word = t["x_step"][0] if len(steps) == 1 else t["x_step"][1]
            key = ' class="key"'
            items = "".join(f'<li{key if mine and s in t["x_key"] else ""}>{s}</li>' for s in steps)
            cols.append(
                f'<div class="col{" me2" if mine else ""}"><header><div><b>{name}</b><small>{sub}</small></div>'
                f'<span>{len(steps)} {word}</span></header>'
                f'<div class="meter"><i class="w{len(steps)}"></i></div>'
                f'<ul class="steps">{items}</ul></div>')
        label = t["levels"][i][1]
        out.append(
            f'<div class="cmpset{" cur" if i == 0 else ""}" data-panel="cmp">'
            f'<h3 class="tabtag cmph">{label}</h3><div class="cols">{"".join(cols)}</div>'
            f'<div class="cmpnote"><p>{note}</p><p>{t["x_disclaimer"]}</p></div></div>')
    return "".join(out)


def versioned(name):
    digest = hashlib.sha256((SITE / "assets" / name).read_bytes()).hexdigest()[:10]
    return f"/assets/{name}?v={digest}"


def structured_data(t):
    data = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": "PCDD",
        "alternateName": "Progressive Change-Driven Development",
        "description": t["description"],
        "url": "https://pcdd.dev" + t["path"],
        "inLanguage": t["lang"],
        "applicationCategory": "DeveloperApplication",
        "operatingSystem": "macOS, Linux, Windows",
        "softwareVersion": PACKAGE_VERSION,
        "license": "https://opensource.org/licenses/MIT",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "downloadUrl": "https://pypi.org/project/pcdd/",
        "sameAs": [REPO, "https://pypi.org/project/pcdd/"],
    }
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def page(t):
    css = versioned("site.css")
    js = versioned("site.js")
    nav_ids = ["why", "how", "start", "compare"]
    navlinks = "".join(f'<a href="#{i}">{n}</a>' for i, n in zip(nav_ids, t["nav"]))
    if t["lang"] == "en":
        lang_sw = '<span aria-current="page">EN</span><a href="/es/" lang="es" hreflang="es">ES</a>'
    else:
        lang_sw = '<a href="/" lang="en" hreflang="en">EN</a><span aria-current="page">ES</span>'
    term = "".join(
        f'<div class="l-{k}">{("$ " + s) if k == "cmd" else s}</div>' if k != "gap" else '<div class="l-gap"> </div>'
        for k, s in t["term"])
    transcript = "\n".join(("$ " + s) if k == "cmd" else s.strip() for k, s in t["term"])
    agents = "".join(f'<span class="agent">{svg}{name}<small>{org}</small></span>' for name, org, svg in AGENTS)
    pcards = "".join(
        f'<div class="card reveal{" hi" if hi else ""}"><span class="tag">{tag}</span><h3>{h}</h3>'
        f'<ul class="list">{"".join(f"<li>{CHECK if hi else CROSS}<span>{x}</span></li>" for x in items)}</ul></div>'
        for tag, h, hi, items in t["p_cards"])
    steps = []
    for n, (h, box, p) in enumerate(t["s_steps"], 1):
        if box is None:
            box_html = f'<code class="box"><span class="p">$ </span>{INSTALL}</code>'
        elif box.startswith("pcdd"):
            box_html = f'<code class="box"><span class="p">$ </span>{box}</code>'
        else:
            box_html = f'<div class="box quote">{box}</div>'
        steps.append(f'<li class="card step reveal"><span class="num">{n}</span><h3>{h}</h3>{box_html}<p>{p}</p></li>')
    feats = "".join(
        f'<div class="card feat reveal"><svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" '
        f'stroke="#C8F560" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{icon}</svg>'
        f'<h3>{h}</h3><p>{p}</p></div>'
        for icon, (h, p) in zip(FEATURE_ICONS, t["y_feats"]))
    doc = t["c_doc"]
    level_tabs = [(tag, label) for tag, label, *_ in t["levels"]]
    return f'''<!doctype html>
<html lang="{t["lang"]}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t["title"]}</title>
<meta name="description" content="{t["description"]}">
<link rel="canonical" href="https://pcdd.dev{t["path"]}">
<link rel="alternate" hreflang="en" href="https://pcdd.dev/">
<link rel="alternate" hreflang="es" href="https://pcdd.dev/es/">
<link rel="alternate" hreflang="x-default" href="https://pcdd.dev/">
<meta name="theme-color" content="#09090B">
<meta property="og:type" content="website">
<meta property="og:url" content="https://pcdd.dev{t["path"]}">
<meta property="og:title" content="{t["title"]}">
<meta property="og:description" content="{t["description"]}">
<meta property="og:locale" content="{"en_US" if t["lang"] == "en" else "es_AR"}">
<meta property="og:locale:alternate" content="{"es_AR" if t["lang"] == "en" else "en_US"}">
<meta property="og:site_name" content="PCDD">
<meta property="og:image" content="https://pcdd.dev/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{t["og_alt"]}">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">{structured_data(t)}</script>
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preload" href="/assets/fonts/geist.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/geist-mono.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{css}">
<script src="{js}" defer></script>
</head>
<body>
<a class="skip" href="#main">{t["skip"]}</a>
<header class="top"><nav class="topnav" aria-label="PCDD">
<a class="brand" href="#top" aria-label="{t["home"]}">{LOGO.format(s=30)}pcdd</a>
<div class="navr">{navlinks}
<a class="star" href="{REPO}" aria-label="{t["star_label"]}">{STAR}{t["star"]}<span class="count" data-stars hidden></span></a>
<div class="lang">{lang_sw}</div>
</div></nav></header>
<main id="main">
<section id="top" class="hero">
<div class="gridbg" aria-hidden="true"></div><div class="glow" aria-hidden="true"></div>
<div class="hero-in">
<div class="hero-l">
<a class="badge rise" href="{REPO}"><b>{VERSION}</b>{t["badge"]}</a>
<p class="acro rise"><b>P</b>rogressive <b>C</b>hange-<b>D</b>riven <b>D</b>evelopment{t["acro_extra"]}</p>
<h1 class="rise"><span>{t["h1"][0]}</span><span>{t["h1"][1]}</span><span class="acc">{t["h1"][2]}</span></h1>
<p class="sub rise">{t["sub"]}</p>
<div class="install rise">{cmd_box(t)}<p class="alt">{t["alt_lead"]} {" · ".join(f"<span>{item}</span>" for item in t["alt"])}</p></div>
</div>
<div class="term-w fade">
<figure class="term" aria-label="{t["term_label"]}">
<div class="bar"><i aria-hidden="true"></i><i aria-hidden="true"></i><i aria-hidden="true"></i><span>{t["term_dir"]}</span></div>
<div class="screen" data-term aria-hidden="true">{term}<span class="caret"></span></div>
<pre class="sr">{transcript}</pre>
</figure>
</div>
</div>
</section>
<section class="works bt" aria-label="{t["works"]}"><div class="row reveal">
<span class="lbl">{t["works"]}</span>{agents}<p>{t["works_note"]}</p>
</div></section>
<section id="why" class="bt"><div class="wrap">
{head_block(t["p_eyebrow"], t["p_h2"], t["p_lead"])}
<div class="grid g300">{pcards}</div>
</div></section>
<section class="bt"><div class="wrap">
{head_block(t["m_eyebrow"], t["m_h2"], t["m_lead"])}
<div class="grid g340">
<div class="chat reveal"><div>{t["m_without"]}</div><div class="msgs">
<div class="me">{t["m_q1"]}</div><div class="ai">{t["m_bad1"]}</div>
<div class="me">{t["m_q2"]}</div><div class="ai">{t["m_bad2"]}</div>
<p class="verdict">{t["m_bad_v"]}</p></div></div>
<div class="chat hi reveal"><div>{t["m_with"]}</div><div class="msgs">
<div class="me">{t["m_q1"]}</div><div class="ai">{t["m_good1"]}</div>
<div class="me">{t["m_q2"]}</div><div class="ai">{t["m_good2"]}</div>
<p class="verdict">{t["m_good_v"]}</p></div></div>
</div>
</div></section>
<section id="how" class="bt soft"><div class="wrap">
{head_block(t["h_eyebrow"], t["h_h2"], t["h_lead"])}
<div class="panel reveal">{tabs(t, "levels", level_tabs, 1)}{levels(t)}</div>
</div></section>
<section class="bt"><div class="wrap split">
<div class="head reveal"><p class="eyebrow">{t["c_eyebrow"]}</p><h2>{t["c_h2"]}</h2><p class="lead">{t["c_lead"]}</p><p class="small">{t["c_small"]}</p></div>
<div class="reveal">
<div class="sessions"><span>{t["c_s1"]}</span><i aria-hidden="true" class="wire"></i><span>{t["c_s2"]}</span></div>
<figure class="doc" aria-label="{t["c_doc_label"]}">
<div><span>pcdd/changes/rate-limit.md</span><span class="acc">{t["c_tasks"]}</span></div>
<pre><span class="h">## Specs</span>
{doc[0]}

<span class="h">## Tasks</span>
<span class="acc">- [x]</span> {doc[1]}
<span class="acc">- [x]</span> {doc[2]}
<span class="h">- [ ]</span> {doc[3]}

<span class="h">## Continuation</span>
<span class="next">{doc[4]}</span></pre>
</figure>
</div>
</div></section>
<section id="start" class="bt soft"><div class="wrap">
{head_block(t["s_eyebrow"], t["s_h2"], t["s_lead"])}
<ol class="grid g300 plain">{"".join(steps)}</ol>
</div></section>
<section class="bt"><div class="wrap">
{head_block(t["y_eyebrow"], t["y_h2"])}
<div class="grid g240">{feats}</div>
</div></section>
<section id="compare" class="bt"><div class="wrap">
{head_block(t["x_eyebrow"], t["x_h2"], t["x_lead"])}
<div class="panel reveal">{tabs(t, "cmp", level_tabs, 0)}{compare(t)}</div>
</div></section>
<section class="cta bt"><div class="glow" aria-hidden="true"></div>
<div class="cta-in reveal">
<h2>{t["f_h2"]}</h2><p class="lead">{t["f_lead"]}</p>
{cmd_box(t)}
<a class="gh" href="{REPO}">{GITHUB}{t["f_star"]}<span class="count" data-stars hidden></span></a>
</div></section>
</main>
<p class="sr" role="status" data-status data-msg="{t["copied_status"]}"></p>
<footer class="bt"><div class="row">
<p>{t["footer"]}</p>
<nav aria-label="{t["footer_label"]}"><a href="{REPO}">GitHub</a><a href="{REPO}/blob/main/LICENSE">{t["license"]}</a><a href="{t["other_path"]}" lang="{t["other_lang"]}" hreflang="{t["other_lang"]}">{t["other_name"]}</a></nav>
</div></footer>
</body>
</html>
'''


def not_found(_t=None):
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Page not found · PCDD</title>
<meta name="robots" content="noindex">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{versioned("site.css")}">
</head>
<body>
<main id="main" class="nf">
<a class="brand" href="/" aria-label="pcdd, home">{LOGO.format(s=30)}pcdd</a>
<h1>404</h1>
<p class="lead">This page doesn’t exist. <span lang="es">Esta página no existe.</span></p>
<p class="nf-links"><a href="/">Go to pcdd.dev</a><a href="/es/" lang="es" hreflang="es">Ir a la versión en español</a></p>
</main>
</body>
</html>
'''


OUTPUTS = {SITE / "index.html": EN, SITE / "es" / "index.html": ES, SITE / "404.html": None}


def main(argv):
    check = "--check" in argv
    stale = []
    for path, strings in OUTPUTS.items():
        html = page(strings) if strings else not_found()
        if check:
            if not path.exists() or path.read_text(encoding="utf-8") != html:
                stale.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(html, encoding="utf-8")
    if stale:
        print("Out of date, run python3 bin/build_site.py: " + ", ".join(stale))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
