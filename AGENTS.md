## General behaviour

- when prompted to 'read Agents.md', note any actions needed before continuing.
- consider whether edits are implied by the current request. If the request is analysis-only, exploratory, uses words like 'check' or 'confirm', or includes a '?', do not make edits without asking first.
- when edits are implied, briefly state the intended change set before editing unless the request is trivial or already specific.
- consider the prompt requirements and ask for clarification, raise potential issues or unintended side-effects.

## Context and Batching

- Treat the visible context window as a hard working budget; do not rely on automatic compaction succeeding.
- Keep broad requests split into narrow, finishable slices that can be completed, verified, and summarized in one context window.
- Prefer targeted file reads, scoped diffs, and concise command output over broad searches or full diffs that flood the transcript.
- For long-running multi-batch work, leave a compact checkpoint before stopping or before context gets high:
  - completed slice and files changed
  - checks run and results
  - known risks or blockers
  - exact next slice to start
- If a slice is growing beyond the remaining context budget, stop at a clean checkpoint rather than pushing into an interruption-prone state.

## Runtime and Paths

- Use `/Users/dlf/miniconda3/bin/python3` for all Python commands.
- Run project commands from `dotlineform-site/` unless explicitly told otherwise.
- Media/generator scripts should rely on `DOTLINEFORM_PROJECTS_BASE_DIR` by default for source image lookups.
- Only pass `--projects-base-dir` when intentionally overriding `DOTLINEFORM_PROJECTS_BASE_DIR`.
- If work/detail/moment dimension lookups fail unexpectedly, verify `DOTLINEFORM_PROJECTS_BASE_DIR` in the current shell before supplying a manual `--projects-base-dir`.
- In repo docs and command examples, prefer the shortest project-local script form unless explicitly needed:
  - use `./scripts/...` rather than `python3 scripts/...`
  - only mention workbook paths for the configured Studio bulk-import workflow

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

## Ruby / Jekyll Toolchain

- This repo expects:
  - `.ruby-version` = `3.1.6`
  - Bundler = `2.6.9`
- In Codex/sandbox runs, do not rely on system `ruby`/`bundle` (`/usr/bin/*`), which can cause false failures.
- Use rbenv shims explicitly for verification commands:
  - `/Users/dlf/.rbenv/shims/ruby -v`
  - `/Users/dlf/.rbenv/shims/bundle -v`
  - `/Users/dlf/.rbenv/shims/bundle exec jekyll build --quiet`
- If `jekyll serve` or `bin/dev-studio` is already running, do not verify against the default `_site/` destination concurrently.
- In that case, use a separate destination for one-off verification builds:
  - `/Users/dlf/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`
- After changing `_docs/`, ensure Studio docs-viewer JSON payloads under `assets/data/docs/scopes/studio/...` are updated before treating the docs output as final. If `bin/dev-studio` or a docs-watch process is already running locally and is expected to regenerate docs payloads, do not run a manual docs rebuild unless deterministic verification is needed or the watcher appears inactive.
- After changing `_docs_library/`, ensure library docs-viewer JSON payloads under `assets/data/docs/scopes/library/...` are updated before treating the docs output as final. If `bin/dev-studio` or a docs-watch process is already running locally and is expected to regenerate docs payloads, do not run a manual docs rebuild unless deterministic verification is needed or the watcher appears inactive.
- When docs search output must be kept live with docs changes, rebuild the matching scope explicitly:
  - `./scripts/build_search.rb --scope studio --write`
  - `./scripts/build_search.rb --scope library --write`
- Do not assume all-scope rebuilds by default; treat `studio` and `library` as separate corpora and pass `--scope` explicitly unless the task intentionally requires both.
- Do not assume `jekyll build` alone updates docs-viewer content; use it only as a separate site verification step after the docs-data rebuild when needed.
- If a build fails with “Could not find bundler 2.6.9” or shows `/usr/bin/ruby`, rerun using the shim commands before reporting an issue.
- Local shell should load rbenv (for interactive use), but Codex checks should still prefer explicit shim paths.

## Safety Defaults

- Prefer dry-run behavior for generators unless explicitly asked to write.
- Do not delete generated or source files unless explicitly requested.

## Validation Checklist

- After changing Python scripts, run a syntax check with the configured interpreter.
- After generator or pipeline-entrypoint changes, verify `scripts/catalogue_json_build.py` still previews or runs successfully.
- After generator changes, run a dry-run and summarize what would be written.
- After layout/template changes, verify behavior on desktop and mobile.
- For a Codex-run browser smoke test on this machine, prefer local Playwright Chromium via the Miniconda Python environment:
  - Playwright CLI: `/Users/dlf/miniconda3/bin/playwright`
  - Python entrypoint: `/Users/dlf/miniconda3/bin/python -m playwright`
  - example one-off smoke test:
    - `/Users/dlf/miniconda3/bin/python - <<'PY'`
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
- For Studio Playwright smoke tests, follow `_docs/studio-smoke-testing.md`: wait for the route root to be visible and for route-specific loaded status before interacting; for controls below async-rendered lists, scroll into view and verify `document.elementFromPoint()` resolves to the target or a child before pointer clicking; use DOM activation only for setup-only actions, not for the behavior being tested.
- Use `_docs/testing.md` and `./scripts/run_checks.py` for optional broader verification when a change has enough blast radius that manual checks alone are likely to miss regressions. Do not run broad profiles by default for every change; choose the smallest relevant profile such as `quick`, `catalogue`, `docs`, or `studio-smoke`.
- When `./scripts/run_checks.py` is used, report the profiles, pass/fail result, and `var/test-runs/.../summary.md` path in the final response.
- For implementation changes, define proportional targeted verification for both:
  - Codex-run checks
  - manual checks
- For docs-only or analysis-only changes, keep manual verification lightweight and state when no separate manual check is useful.
- Manual testing in this repo is expected to be light-touch and pragmatic. There is no formal QA sign-off process.
- Include changed file paths (and line references when useful) in summaries.

## Security and Sanitization

- Treat sanitization not as a mechanical step for every change. Only run a sanitization scan when a change touches credential handling, logging, local-service writes, docs/examples with system paths or commands, generated docs payloads that may include local output, or any script/doc change with realistic risk of leaking local paths or sensitive values.
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
- If a runtime smoke test is blocked by sandbox restrictions, state that clearly in the final summary.

## Git and Change Hygiene

- Do not commit unless explicitly requested.
- Do not amend commits unless explicitly requested.
- Never use destructive git commands (`reset --hard`, checkout/revert of unrelated changes) without explicit approval.
- Ignore unrelated dirty files and do not revert user changes.

## Implementation Style

- Preserve existing Jekyll/Liquid conventions in this repo.
- Prefer shared JS/CSS logic over duplicated inline logic.
- When modifying CSS, consider whether there is an opportunity to refactor or consolidate shared styles.
- The primary purpose of refactoring is to improve consistency and reliability of *.css
- Keep comments concise and implementation-focused.
- use studio_config.json (ui_text section) to store UI copy such as labels. 
- For material new changes, new requirements, or refactors, state the main benefits and risks associated with:
  - new changes
  - new requirements
  - refactors
- For trivial or mechanical edits, a short summary is enough.

## Studio UI Guidance

- `_docs/studio-ui-start.md` is the first-stop Studio UI implementation checklist. Use it first for Studio UI work, then follow its links into the longer reference docs as needed.
- `_docs/ui-framework.md` defines the site-wide UI interaction defaults plus the docs-viewer and public-search UI
- Prefer extending shared `tagStudio*` primitives over borrowing another page's namespace or creating one-off patterns.
- Keep UI shell concerns separate from application logic, validation, and mutation behavior.

## Project Priorities and Tradeoffs

- This is a personal project. The user is effectively fulfilling developer, tester, and product roles together.
- Optimize for decisions that help the user understand:
- clean and elegant UI design
- organized, maintainable code
- evolving or uncertain requirements
- best practice and where compromise is justified
- how Codex should best be used to implement requirements
- When discussing options, explain tradeoffs in a way that helps the user decide and iterate requirements, not just implement the first possible solution.

## Studio Documentation

- Docs source is now flat under `_docs/*.md`; section grouping comes from `doc_id`, `parent_id`, and top-level section docs rather than folders in _docs/.
- The docs viewer reads generated JSON from `assets/data/docs/scopes/...`, not `_docs/` directly.
- If `bin/dev-studio` or docs-watch is already running and expected to regenerate the payloads, do not rebuild doc payloads.
- Prefer explicit scope for docs search rebuilds:
  - `./scripts/build_search.rb --scope studio --write`
  - `./scripts/build_search.rb --scope library --write`
- Do not treat all-scope rebuilds as the default path; use them only when the task intentionally spans both corpora.
- `_docs/site-change-log.md` is the central change log. Only record changes when UI, build flow, validation, or architecture changes are significant and meaningful. Simple UI changes or minor code changes do not need change log entries. If in doubt, ask if a change log entry is required.
- For meaningful search changes, update `_docs/search-change-log.md` in the same change set as part of normal close-out.
- When a published doc references another published doc, use the docs-viewer link form `/docs/?scope=studio&doc=<doc_id>` rather than a raw `.md` filename or legacy `/docs/.../` path.
- Keep raw repo file paths for unpublished docs, literal output paths, and non-doc files such as scripts, JSON artifacts, `README.md`, or `AGENTS.md`.
- Script-specific references for command usage, flags, outputs, and operational notes need to be documented under the parent doc for the scope that own the change, these are top level folders in Docs Viewer. Where a script or functionality crosses scopes (e.g. Catalogue + Library) then it is described under Studio parent. When a script of funmctionality applies across the site, it is described under Site parent.
- Update the owning runtime, UI, or script doc when behavior, dependencies, or build/write responsibilities changed; do not spread partial schema notes across multiple sections.
- When features are implemented or changed, update docs in the same change.
- When search behaviour, schema, ranking, normalization, UI, build flow, validation, or architecture changes materially, update the relevant child docs under `_docs/search.md` in the same change.
