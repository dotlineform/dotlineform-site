## General behaviour

- when prompted to 'read Agents.md', note any actions needed before continuing. Specifically: always ask for confirmation before edits.
- do not make code changes without first confirming what will be changed.
- instructions like 'check' and 'confirm' DO NOT imply you carry out code changes. always ask for confirmation to proceed.
- consider the prompt requirements and ask for clarification, raise potential issues or unintended side-effects.
- a ? in the prompt always indicates that some analysis is needed on reasons for observed behaviour of code, or clarification of the best course of action.

## Runtime and Paths

- Use `/Users/dlf/miniconda3/bin/python3` for all Python commands.
- Run project commands from `dotlineform-site/` unless explicitly told otherwise.
- Media/generator scripts should rely on `DOTLINEFORM_PROJECTS_BASE_DIR` by default for source image lookups.
- Only pass `--projects-base-dir` when intentionally overriding `DOTLINEFORM_PROJECTS_BASE_DIR`.
- If work/detail/moment dimension lookups fail unexpectedly, verify `DOTLINEFORM_PROJECTS_BASE_DIR` in the current shell before supplying a manual `--projects-base-dir`.
- In repo docs and command examples, prefer the shortest project-local script form unless explicitly needed:
  - use `./scripts/...` rather than `python3 scripts/...`
  - omit the positional `data/works.xlsx` argument when using the default workbook

## Codex Cloud / Codespaces Runtime Contract

- Treat local and cloud sessions as one workflow with the same command shapes and validation steps.
- In cloud sessions, keep repo docs and examples machine-agnostic (no user-specific absolute paths).
- Required shared env vars for media/generation flows:
  - `DOTLINEFORM_PROJECTS_BASE_DIR`
  - `DOTLINEFORM_MEDIA_BASE_DIR`
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
- If a build fails with “Could not find bundler 2.6.9” or shows `/usr/bin/ruby`, rerun using the shim commands before reporting an issue.
- Local shell should load rbenv (for interactive use), but Codex checks should still prefer explicit shim paths.

## Safety Defaults

- Prefer dry-run behavior for generators unless explicitly asked to write.
- Do not overwrite canonical work/series prose in the external `projects/*/<prose_subdir>/*.md` tree, or canonical moment prose in `moments/*.md`, unless explicitly requested.
- Do not delete generated or source files unless explicitly requested.

## Pipeline Conventions

- Treat `assets/studio/data/catalogue/*.json` as canonical source for catalogue metadata.
- Treat `data/works.xlsx` as a bulk-import source for new works and new work details only.
- Do not treat workbook-led scripts as part of the live workflow. `build_catalogue.py`, `copy_draft_media_files.py`, and `export_catalogue_source.py` are retained as deprecated reference entrypoints and should exit cleanly.
- Treat `scripts/catalogue_json_build.py` as the live CLI rebuild path for generated catalogue/runtime artifacts.
- Treat `scripts/generate_work_pages.py` as an internal generator entrypoint, not a user-facing command.
- Keep generated output deterministic (stable ordering, stable checksums, stable formatting).
- Canonical series prose is resolved via `Series.primary_work_id -> Works.project_folder -> <prose_subdir> -> Series.series_prose_file`.
- Keep `_series/*.md` minimal; richer series metadata and prose belong in generated JSON artifacts under `assets/series/index/`.

## Moments-Specific Rules

- Generate `_moments/*.md` from worksheet `Moments`.
- Canonical moment prose content lives in `moments/<slug>.md`.
- Keep `_moments/*.md` minimal; richer moment metadata belongs in generated JSON artifacts.
- `/moments/` should read aggregate moment metadata from `assets/data/moments_index.json`.
- `generate_work_pages.py` should always rebuild aggregate index JSON artifacts for series, works, and moments on every run, even when `--only` scopes page/file artifacts.
- Moment layout should use srcset variants `800`, `1200`, `1600` only.
- Do not add a `2400` variant for moments unless explicitly requested.

## Validation Checklist

- After changing Python scripts, run a syntax check with the configured interpreter.
- After generator or pipeline-entrypoint changes, verify both:
  - deprecated user-facing commands exit cleanly with guidance
  - `scripts/catalogue_json_build.py` still previews or runs successfully
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
- Always define targeted verification for both:
  - Codex-run checks
  - manual checks
- Manual testing in this repo is expected to be light-touch and pragmatic. There is no formal QA sign-off process.
- Include changed file paths (and line references when useful) in summaries.

## Security and Sanitization

- Treat sanitization as a required pre-finish check for script/doc changes.
- Scan changed files for local path leaks and sensitive terms before final response:
  - `rg -n "/Users/|/home/|C:\\\\|miniconda|rbenv|api[_-]?key|token|secret|password|PRIVATE KEY" <changed-files>`
- Remove user-specific absolute paths from comments/docs/examples unless explicitly required by the user.
- Keep script examples generic and project-local (`./scripts/...`) unless a pinned interpreter or non-default workbook path is explicitly needed.
- Do not publish machine-specific usernames, absolute filesystem paths, or local mount details in repo docs.
- Never hardcode credentials, tokens, or private keys in source/docs; use env vars and redact examples.
- Keep logs for local write services minimal (ids/counts/status), not full payload/file-content dumps.
- For local write services, keep explicit write allowlists and do not widen write scope implicitly.
- Keep local write services bound to loopback and limit CORS to localhost origins only.
- For overwrite/import flows, create backups before write and document backup location/pattern.
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
- The primary purpose of refactoring is to improve readability, consistency, and reliability.
- Keep comments concise and implementation-focused.
- use studio_config.json (ui_text section) to store UI copy such as labels. 
- Always state the main benefits and risks associated with:
  - new changes
  - new requirements
  - refactors

## Studio UI Guidance

- `_docs_src/design/ui-framework.md` defines the site-wide UI interaction defaults plus the docs-viewer and public-search UI standards.
- `_docs_src/design/studio-ui-framework.md` defines the Studio shared UI contracts.
- When fixing Studio UI issues, always update `_docs_src/design/studio-ui-rules.md` with triage and outcome, and promote repeated/shared issues into permanent rules.
- When asked to add a UI element to a Studio page, or to develop a new Studio UI pattern, use `_docs_src/design/studio-ui-framework.md` as the basis.
- When asked to add a site UI interaction pattern such as navigation, paging, swipe behavior, docs-viewer UI, or public-search UI, use `_docs_src/design/ui-framework.md` as the basis.
- If site-wide UI defaults change, update `_docs_src/design/ui-framework.md` in the same change.
- If Studio UI definitions, scope, or shared naming boundaries change, update `_docs_src/design/studio-ui-framework.md` in the same change.
- Prefer extending shared `tagStudio*` primitives over borrowing another page's namespace or creating one-off patterns.
- Keep UI shell concerns separate from application logic, validation, and mutation behavior.

## Project Priorities and Tradeoffs

- This is a personal project. The user is effectively fulfilling developer, tester, and product roles together.
- Optimize for decisions that help the user understand:
  - clean and elegant UI design
  - organized, conceptually simple code
  - evolving or uncertain requirements
  - best practice and where compromise is justified
  - how Codex should best be used to implement requirements
- Performance at large scale is less important than clarity, maintainability, and good product judgment for the current scope.
- When discussing options, explain tradeoffs in a way that helps the user decide and iterate requirements, not just implement the first possible solution.

## Studio Documentation

- `_docs_src/studio/*.md` are the central product/behavior docs for Studio features.
- `_docs_src/search/*.md` are the central product/behavior docs for search.
- `_docs_src/data-models/*.md` are the central schema and payload-contract docs for generated/runtime data artifacts and source-data records.
- `_docs_src/new-pipeline/refine-catalogue.md` is the planning doc for post-Phase-15 workflow refinement and testing preparation.
- `_docs_src/site/*.md` plus `_docs_src/site-change-log.md` are the central architecture/history docs for the broader non-search site.
- When a published doc references another published doc, use the docs-viewer link form `/docs/?scope=studio&doc=<doc_id>` rather than a raw `.md` filename or legacy `/docs/.../` path.
- Keep raw repo file paths for unpublished docs, literal output paths, and non-doc files such as scripts, JSON artifacts, `README.md`, or `AGENTS.md`.
- Keep `_docs_src/scripts/scripts.md` as the high-level entry point for repo scripts.
- Keep `_docs_src/scripts/scripts-*.md` as the canonical script-specific references for command usage, flags, outputs, and operational notes.
- When a schema or payload contract changes, update the relevant `_docs_src/data-models/*.md` scope doc in the same change.
- Also update the owning runtime, UI, or script doc when behavior, dependencies, or build/write responsibilities changed; do not spread partial schema notes across multiple sections.
- Only split a lower-level data-model child doc out of a scope doc when one artifact family has become too dense to stay readable and maintainable in the parent scope doc.
- When Studio features are implemented or changed, update Studio docs and relevant scripts docs in the same change.
- When search behaviour, schema, ranking, normalization, UI, build flow, validation, or architecture changes materially, update the relevant `_docs_src/search/*.md` docs in the same change.
- For meaningful search changes, update `_docs_src/search/search-change-log.md` in the same change set as part of normal close-out.
- When non-search site, Studio, or shared pipeline behaviour changes materially, update the relevant `_docs_src/site/*.md` docs and `_docs_src/site-change-log.md` in the same change set as part of normal close-out.
