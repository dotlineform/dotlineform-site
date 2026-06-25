## General Behaviour

- Ask for confirmation before edits unless the request is trivial or the user has explicitly asked for the edit.
- For code changes, summarize the intended change set and ask for confirmation before editing unless the request is trivial.
- Use `docs-viewer/source/studio/development-checklist.md` as the project implementation checklist. Keep durable repo guardrails there.
- Use `docs-viewer/source/studio/development-workflow.md` when lifecycle decisions, change requests, task trackers, or closeout state need more context.
- Compatibility aliases are prohibited unless justified before implementation with removal criteria.
- If you find compatibility layers during new feature development, report and fix them immediately when non-trivial.
- Tests and documents are not contracts for deciding how to implement code. They should follow current development objectives unless a constraint has been called out and agreed.
- Answer questions based on domain best practice, suggest ways to reduce maintenance risk and improve performance, and raise likely side effects or missing requirements.
- When discussing options, explain tradeoffs in a way that helps the user decide and iterate requirements.
- Prefer targeted file reads, scoped diffs, and concise command output over broad searches or full diffs.
- The public site has no deploy-time build or copy step: `site/` is the tracked GitHub Pages artifact. Local apps and `/docs/` may share site-owned config, CSS, and runtime files through explicit service route mapping, especially Docs Viewer public/shared assets.
- For long multi-batch work, or before a long thread reaches context limits, produce a handoff note with changed files, decisions made, remaining tasks, commands run, and known risks. If the implementation is documented, add the handoff note to that document.
- For material new changes, requirements, or refactors, state the main benefits and risks. For trivial or mechanical edits, a short summary is enough.

## Documentation And Generated Payloads

- Update source documents, but do not rebuild Docs Viewer payloads unless the task explicitly calls for that follow-through.
- Routine docs-source edits are regenerated manually, by `bin/local-studio`, or by the docs watcher. If the watcher regenerates published JSON after source docs change, let it and do not revert those generated changes.
- The `studio` scope is the reference scope for live development and maintenance documents.
- Docs Viewer payload and search builders are Python entrypoints:
  - docs payloads: `$HOME/miniconda3/bin/python3 docs-viewer/build/build_docs.py --scope studio --write`
  - docs search: `$HOME/miniconda3/bin/python3 docs-viewer/build/build_search.py --scope studio --write`
- `build_docs.py` prints a compact human summary by default. Automation that needs the machine-readable diagnostics line should pass `--diagnostics`.

## Runtime And Paths

- Run project commands from `dotlineform-site/` unless explicitly told otherwise.
- Use `$HOME/miniconda3/bin/python3` for Python commands.
- Do not invoke Python entrypoints through their shebangs in Codex runs. Use `$HOME/miniconda3/bin/python3 <script>` explicitly.
- Env vars are saved in `var/local/site.env`.
- In repo docs and command examples, prefer the shortest project-local script form unless a pinned interpreter or non-default path is required.

## Checks And Test Policy

- Use `docs-viewer/source/studio/testing.md`, `testing-pytest.md`, and `smoke-testing.md` as the maintained test policy.
- Choose the smallest check that proves the changed contract. Do not run broad profiles just to produce more evidence.
- Before adding or expanding a permanent test, apply the review gate:
  - Can this be tested as pure function or service behavior?
  - Can this be tested by direct HTTP/API request?
  - Is a browser required to verify a product contract, or only to mimic user clicks?
  - Will this fail because copy, layout, focus, hover state, or modal timing changed?
- Permanent tests should protect data flows, server responses, generated contracts, parser behavior, ownership boundaries, and route/module integration. They should not police ordinary UI choreography, modal lifecycle feel, focus timing, copy, hover styling, or layout.
- Browser smokes are only for durable browser boundaries: route boot, module wiring, public/private asset boundaries, local API reachability, request/response agreement, or shared ready/busy state. Use manual or temporary browser checks for tactile interaction, visual fit, copy tone, modal feel, and mobile ergonomics.
- Default focused checks:
  - Python/service changes: `$HOME/miniconda3/bin/python3 -m pytest <test-path>`
  - Script changes: syntax check with `$HOME/miniconda3/bin/python3 -m py_compile <files>`
  - Repo whitespace: `git diff --check`
  - Broader blast radius: `$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py --profile <profile>`
- Use the smallest relevant `run_checks.py` profile, such as `quick`, `catalogue`, `docs`, `admin-smoke`, `analytics-smoke`, `docs-viewer-smoke`, or `studio-smoke`.
- When `admin-app/commands/run_checks.py` is used, report the profile, pass/fail result, and `var/admin/test-runs/.../summary.md` path.
- For commands that bind loopback ports or launch browser smokes, run them with elevated localhost/browser permissions in the Codex sandbox. Keep pure syntax checks, `git diff --check`, JSON parsing, and non-network pytest runs sandboxed.
- If a local route is expected to be running but the sandbox cannot reach localhost, say that the sandbox cannot reach it and use an isolated temporary build/server only if automated verification needs it.
- For Codex-run browser checks, use Playwright from the Miniconda environment when needed:
  - Playwright CLI: `$HOME/miniconda3/bin/playwright`
  - Python entrypoint: `$HOME/miniconda3/bin/python -m playwright`

## Public Static Site Toolchain

- `site/` is the tracked static site root and the GitHub Pages upload root.
- `site-tools/config/site-tools.json` owns static-site validation config and site-level media settings used by local Python tooling.
- Use `bin/site-validate` to validate the deploy root.
- Use `bin/site-preview` for local public-site preview; it serves `site/` directly with Python's HTTP server.
- Local Studio is served by `bin/local-studio`, not by the public-site preview server.

## Security And Sanitization

- Use `docs-viewer/source/studio/development-checklist.md` for sanitization triggers and local write-service safety.
- When a focused scan is needed for changed files, use:
  - `rg -n "/Users/|/home/|C:\\\\|miniconda|rbenv|api[_-]?key|token|secret|password|PRIVATE KEY" <changed-files>`

## Codex Cloud / Codespaces Runtime Contract

- Treat local and cloud sessions as one workflow with the same command shapes and validation steps.
- In cloud sessions, keep repo docs and examples machine-agnostic.
- Required shared env vars for media/generation flows: `DOTLINEFORM_PROJECTS_BASE_DIR`
- Optional shared env var: `MAKE_SRCSET_JOBS`
- Keep remote media credentials out of tracked files; use platform secret stores.
- Before reporting environment issues in Codex Cloud or Codespaces, run a Python version/dependency check for app/runtime, site validation, and preview work.
- Use dry-run generator commands first in cloud sessions unless an explicit write run was requested.

## Git And Change Hygiene

- Do not commit unless explicitly requested.
- Do not amend commits unless explicitly requested.
- Never use destructive git commands (`reset --hard`, checkout/revert of unrelated changes) without explicit approval.
- Ignore unrelated dirty files and do not revert user changes.
