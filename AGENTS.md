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

## Verification

- Define proportional targeted verification for implementation changes, including Codex-run checks and any manual checks that remain.
- Browser smoke tests are needed for non-trivial operational site or frontend changes, not for routine docs-only edits.
- For non-trivial UI changes, verify desktop behavior where practical. Only verify mobile behavior where public pages on the site (dotlineform.com) will be affected.
- After changing scripts, run a syntax check with the configured interpreter.
- For commands that clearly bind loopback ports or launch browser smokes, run them with elevated localhost permissions immediately in the Codex sandbox. Keep pure syntax checks, `git diff --check`, JSON parsing, and non-network pytest runs sandboxed.
- If a local route is expected to be running but the sandbox cannot reach localhost, say that the sandbox cannot reach it and use an isolated temporary build/server only if automated verification needs it.

## Public Jekyll Toolchain

- Ruby/Jekyll remains the public-site preview/build layer. App-facing Docs Viewer, search, catalogue search, and catalogue prose builders are Python-owned.
- The public Jekyll layer expects `.ruby-version` = `3.1.6` and Bundler = `2.6.9`.
- In Codex/sandbox runs, do not rely on system `ruby`/`bundle` (`/usr/bin/*`).
- Use rbenv shims explicitly for verification:
  - `$HOME/.rbenv/shims/ruby -v`
  - `$HOME/.rbenv/shims/bundle -v`
  - `$HOME/.rbenv/shims/bundle exec jekyll build --quiet`
- If `jekyll serve` is already running, do not verify against the default `_site/` destination concurrently. Use a separate destination such as `/tmp/dlf-jekyll-build`.
- If a build fails with “Could not find bundler 2.6.9” or shows `/usr/bin/ruby`, rerun using shim commands before reporting an issue.
- Local Studio is served by `bin/local-studio`, not by a Jekyll overlay.

## Tests

- Use `docs-viewer/source/studio/testing.md` and `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py` for broader verification when a change has enough blast radius.
- Do not run broad profiles by default; choose the smallest relevant profile such as `quick`, `catalogue`, `docs`, or `studio-smoke`.
- Python tests in `studio/commands/run_checks.py` must run through `$HOME/miniconda3/bin/python3`.
- For focused checks, use `$HOME/miniconda3/bin/python3 -m pytest <test-path>`.
- When `studio/commands/run_checks.py` is used, report the profiles, pass/fail result, and `var/test-runs/.../summary.md` path.
- For Codex-run browser smokes, prefer local Playwright Chromium via the Miniconda environment:
  - Playwright CLI: `$HOME/miniconda3/bin/playwright`
  - Python entrypoint: `$HOME/miniconda3/bin/python -m playwright`
- If Chromium launch fails in the Codex app sandbox, retry the same Playwright browser check with escalated permissions before treating it as a product/runtime issue.
- Avoid the raw Edge headless fallback unless Playwright is unavailable.
- For Studio Playwright smoke tests, follow `docs-viewer/source/studio/studio-smoke-testing.md`.

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
- Before reporting environment issues in Codex Cloud or Codespaces, run a Python version/dependency check for app/runtime work. For public Jekyll build or preview issues, also check Ruby, Bundler, and Jekyll.
- Use dry-run generator commands first in cloud sessions unless an explicit write run was requested.

## Git And Change Hygiene

- Do not commit unless explicitly requested.
- Do not amend commits unless explicitly requested.
- Never use destructive git commands (`reset --hard`, checkout/revert of unrelated changes) without explicit approval.
- Ignore unrelated dirty files and do not revert user changes.
