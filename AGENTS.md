## General behaviour

- use `docs-viewer/source/studio/development-workflow.md` as the primary guide and follow its links to task-specific docs.
- answer questions based on applying best practice in this technical or creative domain, provide suggestions to mitigate maintenance risk and improve site or application performance. ask for confirmation before any edits.
- code changes: summarise the intended change set and ask for confirmation before editing code unless the request is trivial.
- consider the prompt requirements and ask for clarification, raise potential issues or unintended side-effects.
- update source documents but do not rebuild doc payloads because this is done manually or by `bin/local-studio` / the docs-watcher. If docs-watcher re-generates published JSON when source documents change, let it. Do not revert published changes created by docs-watcher.
- when a command is clearly a localhost/browser smoke that binds a server or launches Playwright, run it elevated immediately with a concise justification instead of doing the doomed sandbox attempt first. For non-network checks like quick, syntax checks, git diff --check, and pure pytest that doesn’t bind ports, keep them sandboxed.
- When discussing options, explain tradeoffs in a way that helps the user decide and iterate requirements, not just implement the first possible solution.
- Prefer targeted file reads, scoped diffs, and concise command output over broad searches or full diffs that flood the transcript.
- For long-running multi-batch work, or before a long thread reaches context limit, produce a handoff note: changed files, decisions made, remaining tasks, commands run, and known risks. If the implementation is documented, add the handoff note to the document at the top of the document for the next Codex session to read.

## UI Guidance

- `docs-viewer/source/studio/ui.md` is the section containing UI guidance and maintenance rules.
- `docs-viewer/source/studio/ui-catalogue.md` defines the site-wide UI interaction default UI components.
- Keep UI shell concerns separate from application logic, validation, and mutation behavior.

## Implementation Style

- Prefer shared JS/CSS logic over duplicated inline logic.
- When modifying CSS, consider whether there is an opportunity to refactor or consolidate shared styles.
- Keep comments concise and implementation-focused.
- use the apppropriate config file to store UI copy such as labels and status message text. 
- For material new changes, new requirements, or refactors, state the main benefits and risks associated with:
  - new changes
  - new requirements
  - refactors
- For trivial or mechanical edits, a short summary is enough.

## Script Module Boundaries

- Do not add new responsibilities to large route/controller files by default.
- Before changing a Studio or Docs Viewer route controller, check whether the behavior belongs in an existing route-local module, shared module, render module, service/write module, domain module, modal module, or workflow module.
- Create a focused module when the change adds a complete responsibility such as rendering, modal lifecycle, service orchestration, result shaping, validation, import/export flow, or route-state projection.
- Keep route entry modules as orchestration shells: boot/config, route readiness, event wiring, and handoff between focused modules.
- When optimising code or refactoring, extract around stable ownership boundaries.
- For risk mitigation and scoring, consult as appropriate:
  - Javascript: `docs-viewer/source/studio/studio-javascript-payload-inventory.md`
  - Python, Ruby: `docs-viewer/source/studio/studio-python-ruby-script-inventory.md`

## Studio Documentation and Search

- Docs source is flat under `docs-viewer/source/<scope>/*.md`; section grouping comes from `doc_id`, `parent_id`, and top-level section docs rather than source folders.
- scope `studio` is the reference for live development and maintenance documents.
- The docs viewer reads generated JSON from `assets/data/docs/scopes/...`, not source Markdown directly.
- Do not rebuild doc payloads
- When a published doc references another published doc, use the docs-viewer link form `/docs/?scope=studio&mode=manage&doc=<doc_id>`.
- Use explicit scope for docs search rebuilds: `./scripts/build_search.rb --scope studio --write`

## Change Log

- The source model and authoring workflow for change logs are documented in `studio/workflows/change-requests/README.md`; entry files live under `studio/workflows/change-requests/logs/entries/`.
- Keep raw repo file paths for unpublished docs, literal output paths, and non-doc files such as scripts, JSON artifacts, `README.md`, or `AGENTS.md`.
- Script-specific references for command usage, flags, outputs, and operational notes need to be documented under the parent doc for the scope that own the change, these are top level folders in Docs Viewer. Where a script or functionality crosses scopes (e.g. Catalogue + Library) then it is described under Studio parent. When a script of funmctionality applies across the site, it is described under Site parent.
- Update the owning runtime, UI, or script doc when behavior, dependencies, or build/write responsibilities changed; do not spread partial schema notes across multiple sections.
- When features are implemented or changed, update the associated docs in the same change.

## Runtime and Paths

- Use `$HOME/miniconda3/bin/python3` for all Python commands.
- Do not invoke Python entrypoints through their shebangs in Codex runs. Use `$HOME/miniconda3/bin/python3 <script>` explicitly.
- Run project commands from `dotlineform-site/` unless explicitly told otherwise.
- Env vars are saved in `var/local/site.env`
- In repo docs and command examples, prefer the shortest project-local script form unless explicitly needed.

## Ruby / Jekyll Toolchain

- This repo expects:
  - `.ruby-version` = `3.1.6`
  - Bundler = `2.6.9`
- In Codex/sandbox runs, do not rely on system `ruby`/`bundle` (`/usr/bin/*`), which can cause false failures.
- Use rbenv shims explicitly for verification commands:
  - `$HOME/.rbenv/shims/ruby -v`
  - `$HOME/.rbenv/shims/bundle -v`
  - `$HOME/.rbenv/shims/bundle exec jekyll build --quiet`
- If `jekyll serve` is already running, do not verify against the default `_site/` destination concurrently.
- In that case, use a separate destination for one-off verification builds:
  - `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`
- Before relying on, starting, stopping, or interrupting local services for verification, tell the user whether they need to start or stop those services. Do not assume running local Studio services are available for tests; they may only be running so the user can read docs.
- A failed Codex `curl` to `localhost:4000` or `127.0.0.1:4000` may be a sandbox/network boundary, not proof that Jekyll is not running. If the user says the route is running, trust that and avoid contradicting it.
- When localhost reachability is uncertain, say the sandbox cannot reach the route and use an isolated temporary build/server for automated verification only if needed.
- Local Studio is served by `bin/local-studio`, not by a Jekyll overlay. For isolated public Jekyll smoke tests, copy the needed generated `assets/data/docs/scopes/<scope>/` and `assets/data/search/<scope>/` payloads into the temporary build destination when the build destination excludes or lacks those generated payloads.
- If a build fails with “Could not find bundler 2.6.9” or shows `/usr/bin/ruby`, rerun using the shim commands before reporting an issue.
- Local shell should load rbenv (for interactive use), but Codex checks should still prefer explicit shim paths.

## Verification

- For implementation changes, define proportional targeted verification for both:
  - Codex-run checks
  - manual checks
- Browser smoke tests are only needed when changes have been to the operational site or front end, not when documents have been edited.
- Codex performs most testing where practical. Manual testing in this repo is expected to be light-touch and pragmatic. There is no formal QA sign-off process.
- Include changed file paths in summaries.
- After changing scripts, run a syntax check with the configured interpreter.
- After UI changes, verify behavior on both desktop and mobile.

## Tests

- For a Codex-run browser smoke test on this machine, prefer local Playwright Chromium via the Miniconda Python environment:
  - Playwright CLI: `$HOME/miniconda3/bin/playwright`
  - Python entrypoint: `$HOME/miniconda3/bin/python -m playwright`
  - example one-off smoke test:
    - `$HOME/miniconda3/bin/python - <<'PY'`
    - `from pathlib import Path`
    - `from playwright.sync_api import sync_playwright`
    - `url = Path('/tmp/dlf-jekyll-build/docs/index.html').resolve().as_uri()`
    - `with sync_playwright() as p:`
    - `    browser = p.chromium.launch(headless=True)`
    - `    page = browser.new_page()`
    - `    page.goto(url, wait_until='domcontentloaded')`
    - `    print(page.title())`
    - `    browser.close()`
    - `PY`
  - installed browsers currently live under `~/Library/Caches/ms-playwright/`
- If Chromium launch fails in the Codex app sandbox, retry the same Playwright browser check with escalated permissions before treating it as a product or runtime issue.
- Avoid the raw Edge headless fallback unless Playwright is unavailable; Edge can trigger crash-report noise on this machine.
- For Studio Playwright smoke tests, follow `docs-viewer/source/studio/studio-smoke-testing.md`: wait for the route root to be visible and for route-specific loaded status before interacting; for controls below async-rendered lists, scroll into view and verify `document.elementFromPoint()` resolves to the target or a child before pointer clicking; use DOM activation only for setup-only actions, not for the behavior being tested.
- Use `docs-viewer/source/studio/testing.md` and `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py` for optional broader verification when a change has enough blast radius that manual checks alone are likely to miss regressions.
- Do not run broad profiles by default for every change; choose the smallest relevant profile such as `quick`, `catalogue`, `docs`, or `studio-smoke`.
- Python tests in `studio/commands/run_checks.py` must run through the configured Miniconda interpreter. Use `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile <profile>` rather than any root-level wrapper or shebang invocation.
- For focused checks, use `$HOME/miniconda3/bin/python3 -m pytest <test-path>` over relying on whichever `python` happens to be active.
- When `studio/commands/run_checks.py` is used, report the profiles, pass/fail result, and `var/test-runs/.../summary.md` path in the final response.

## Security and Sanitization

- Only run a sanitization scan when a change touches credential handling, logging, local-service writes, docs/examples with system paths or commands, generated docs payloads that may include local output, or any script/doc change with realistic risk of leaking local paths or sensitive values.
- For small low-risk edits, a reasoned no-scan decision is acceptable.
- When scanning changed files for local path leaks and sensitive terms, use:
  - `rg -n "/Users/|/home/|C:\\\\|miniconda|rbenv|api[_-]?key|token|secret|password|PRIVATE KEY" <changed-files>`
- Remove user-specific absolute paths from comments/docs/examples unless explicitly required by the user.
- Keep script examples generic and project-local (`./scripts/...`) unless a pinned interpreter or non-default workbook path is explicitly needed.
- Do not publish machine-specific usernames, absolute filesystem paths, or local mount details in repo docs.
- Never hardcode credentials, tokens, or private keys in source/docs; use env vars and redact examples.
- Keep logs for local write services minimal (ids/counts/status), not full payload/file-content dumps.
- For local write services, keep explicit write allowlists and do not widen write scope implicitly.
- Keep local write services bound to loopback and limit CORS to localhost origins only.
- If a runtime smoke test is blocked by sandbox restrictions, ask for elevated permissions.

## Codex Cloud / Codespaces Runtime Contract

- Treat local and cloud sessions as one workflow with the same command shapes and validation steps.
- In cloud sessions, keep repo docs and examples machine-agnostic (no user-specific absolute paths).
- Required shared env vars for media/generation flows:
  - `DOTLINEFORM_PROJECTS_BASE_DIR`
- Optional shared env var:
  - `MAKE_SRCSET_JOBS`
- Keep remote media credentials out of tracked files; use platform secret stores for values such as:
  - `R2_ACCOUNT_ID`
  - `R2_ACCESS_KEY_ID`
  - `R2_SECRET_ACCESS_KEY`
  - `R2_BUCKET`
  - `R2_ENDPOINT`
- Before reporting environment issues in Codex Cloud or Codespaces, run a version check pass for Python, Ruby, Bundler, and Jekyll.
- Use dry-run generator commands first in cloud sessions unless an explicit write run was requested.

## Git and Change Hygiene

- Do not commit unless explicitly requested.
- Do not amend commits unless explicitly requested.
- Never use destructive git commands (`reset --hard`, checkout/revert of unrelated changes) without explicit approval.
- Ignore unrelated dirty files and do not revert user changes.
