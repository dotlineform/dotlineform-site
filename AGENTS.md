## General Behaviour

- Ask for confirmation before edits unless the request is trivial or the user has explicitly asked for the edit.
- For code changes, summarize the intended change set and ask for confirmation before editing unless the request is trivial.
- Use `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/scopes/studio/source/documents/d-20260523-190651-7157ec.md` as the project implementation checklist. Keep durable repo guardrails there.
- Use `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/scopes/studio/source/documents/d-20260523-000000-bf7161.md` when lifecycle decisions, roadmap deliveries, task trackers, or closeout state need more context.
- Compatibility aliases are prohibited unless justified before implementation with removal criteria.
- If you find compatibility layers during new feature development, report. Fix them immediately when non-trivial.
- Tests and documents are not contracts for deciding how to implement code. They should follow current development objectives unless a constraint has been called out and agreed.
- Answer questions based on domain best practice, suggest ways to reduce maintenance risk and improve performance, and raise likely side effects or missing requirements.
- When discussing options, explain tradeoffs in a way that helps the user decide and iterate requirements.
- Prefer targeted file reads, scoped diffs, and concise command output over broad searches or full diffs.

## Key development factors
- The public site has no deploy-time build step: `site/` is the tracked GitHub Pages artifact. Shared/public Docs Viewer JavaScript and stylesheets are canonical under `docs-viewer/` and have an explicit tracked projection under `site/docs-viewer/`; local apps serve the canonical files while public preview and GitHub Pages serve the projection.
- For long multi-batch work, or before a long thread reaches context limits, produce a handoff with changed files, decisions made, remaining tasks, commands run, and known risks. Keep the delivery document to current/next state, checkboxes, decisions, and completion gates.
- Non-trivial new features, requirements, or refactors are generally documentedd and parented to [Roadmap](/docs/?scope=studio&doc=d-20260428-000000-f5ff18), which contains delivery planning guidance.
- Local servers do not need to support multiple concurrent users. Modal workflows always complete before another one starts.

## Processing Project Boundary

- `processing/` is tracked in this Git repository but is currently a separate Java/Processing project, not a module of the website or the deployed `site/` artifact.
- Its documentation belongs to the `processing` Docs Viewer scope, and it is expected to acquire its own build, test, and development lifecycle. Until that lifecycle is defined, do not apply website runtime, build, test, or release assumptions to it implicitly; treat any integration with the website as an explicit cross-project change.

## Documentation And Generated Payloads

- When writing or updating Markdown source documents, do not apply a fixed-column source wrap. Each paragraph is one source line, each list item is one source line. Code blocks, tables, headings, and front matter retain their required structure.
- Every configured Docs Viewer scope stores its lifecycle beneath `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/scopes/<scope-id>/`: canonical input in `source/`, replaceable Build output in `generated/`, and the accepted local snapshot in `published/`. The repository `docs-viewer/scopes/` tree is retired and must not be recreated or used as a fallback.
- Scope configuration is the authority for storage resolution. If a configured external root is unavailable, report the scope as unavailable; do not create a replacement root, infer a repository path, or manufacture a second copy.
- Keep the same media skeleton in every scope: `source/media/{img,svg,files,html,build-source/mermaid}`. Empty directories are intentional and may be retained.
- For an ordinary Markdown create or edit in any configured scope, write valid canonical Markdown to that scope's configured `source/documents/` location through the normal source/mutation boundary and let the docs watcher running under `bin/local-studio` rebuild the document projections. Do not run a manual Docs or Search rebuild merely to finish the source change.
- The watcher rebuilds document projections only; inspect those outputs and do not rerun the builder solely for idempotence evidence.
- The `studio` scope is the reference scope for live development and maintenance documents.
- If the watcher is unavailable, regenerate an ordinary doc-only source change with `$HOME/miniconda3/bin/python3 docs-viewer/build/build_docs.py --scope <scope-id> --write --only-doc-ids <comma-separated-doc-ids> --skip-media-builds`. The targeted build still recomputes the collection indexes while preserving unaffected by-ID payloads.
- Use a full-scope document build only when targeted prerequisites are missing, a global builder/config/renderer contract changed, generated state needs complete reconciliation, or registered media output is actually under review. Add `--skip-media-builds` for a docs-only full reconciliation; omit it only when the registered media producers and real external workspace are part of the evidence.
- Docs search has no targeted-postings mode and intentionally does not follow ordinary watcher or management writes automatically. A stale Search index after an ordinary document edit is not unfinished document work. Rebuild Search only when the user explicitly requests it or Search itself is the task, using the Manage Rebuild control or `$HOME/miniconda3/bin/python3 docs-viewer/build/build_search.py --scope <scope-id> --write`.
- `build_docs.py` prints a compact human summary by default. Automation that needs the machine-readable diagnostics line should pass `--diagnostics`.
- A complete Build replaces that scope's `generated/` files and records the completed generated snapshot. Review Generated before Publish. Publish deletes the previous managed files under `published/`, writes the accepted generated snapshot there, and records the completed published snapshot. Empty directories may remain.
- Publish changes only the scope's external `published/` snapshot and owns the sole `publishable` eligibility decision. Every downstream consumer uses that same accepted document set.
- Deploy Repo is an Analysis-only, revision-bound preview/apply operation over one complete Published snapshot. It may perform configured destination preparation and reconcile only its owned repository/R2, document-location, Catalogue, and publication-lineage projections; it must not read source or generated output, invoke Build or Publish, or apply another document filter.
- The local Publish modal may compose Publish and Deploy Repo, with both selected by default when available, while retaining Publish-only and Deploy-Repo-only operation and separate outcomes. Git commit and push remain explicit ordinary user actions. Deploy Public remains the separate manually triggered GitHub Pages workflow over the committed `site/` snapshot.
- Recovery uses ordinary sources and Git history: fix the source, builder, or destination and rerun the owning Build, Publish, or Deploy Repo operation. If lineage updates but the `dotlineform/projects` follow-through Build fails, repair the cause and run that ordinary Projects Build. The clean Git commit immediately before the Stage 2.3 repository-copy removal remains the recovery point for the retired tracked tree; do not add aliases, shadow copies, retry markers, transactional swaps, or automatic backup directories.

## Runtime And Paths

- Run project commands from `dotlineform-site/` unless explicitly told otherwise.
- Use `$HOME/miniconda3/bin/python3` for Python commands.
- Do not invoke Python entrypoints through their shebangs in Codex runs. Use `$HOME/miniconda3/bin/python3 <script>` explicitly.
- Env vars are saved in `.env.local`.
- In repo docs and command examples, prefer the shortest project-local script form unless a pinned interpreter or non-default path is required.

## Checks And Test Policy

- Use `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/scopes/studio/source/documents/d-20260501-174746-efd581.md`, `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/scopes/studio/source/documents/d-20260514-135716-c70591.md`, and `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/scopes/studio/source/documents/d-20260501-000000-49b626.md` as the maintained test policy.
- `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/scopes/studio/source/documents/d-20260627-212121-7cf7de.md` determines approach for subsequent testing and review of existing tests.
- Choose the smallest check that proves the changed contract. Do not run broad profiles just to produce more evidence.
- Leave UI design testing to the user unless specifically requested; browser probes are brittle.
- A UI change does not create an automatic requirement to add, update, or run a permanent browser test. Recorded manual confirmation is sufficient for ordinary interaction, presentation, copy, focus, modal, filtering, and navigation behavior when no durable browser integration boundary changed.
- Before adding or expanding a browser test, name the unique regression it could catch, why a pure/service/API/generator check cannot catch it, and why repeated manual confirmation would be materially costly or risky. If those answers are not concrete, do not change the browser suite.
- Do not use an executable smoke as a shared fixture library. Put genuinely shared route startup/readiness code in a small non-test support module; keep each retained smoke to one integration boundary.
- Treat a browser script over 500 lines or covering more than one route/workflow owner as a mandatory deletion/split review, not a file to extend. Existing profile membership is not evidence that the script remains worthwhile.
- Do not include smoke scripts in broad pytest collection. Smoke profiles are explicit boundary audits, not ordinary closeout gates.
- Before adding or expanding a permanent test, apply the review gate:
  - Can this be tested as pure function or service behavior?
  - Can this be tested by direct HTTP/API request?
  - Is a browser required to verify a product contract, or only to mimic user clicks?
  - Will this fail because copy, layout, focus, hover state, or modal timing changed?
- Permanent tests should protect data flows, server responses, generated contracts, parser behavior, ownership boundaries, and route/module integration. They should not police ordinary UI choreography, modal lifecycle feel, focus timing, copy, hover styling, or layout.
- Browser smokes are only for durable browser boundaries: route boot, module wiring, public/private asset boundaries, local API reachability, request/response agreement, or shared ready/busy state.
- Human manual checks are used for tactile interaction, visual fit, copy tone, modal feel, and mobile ergonomics.
- The retained Docs Viewer browser profile is intentionally limited to Manage route/service boot, Docs Review authority, public read-only isolation, and external-local Mermaid loading. Additions require an explicit policy change, not routine feature follow-through.
- The retained Studio browser profile is intentionally limited to local Catalogue route/service boot, local Tag route/service boot, and one representative public Catalogue route without local capability. Deterministic Catalogue/Tag behavior belongs in Python tests; UI behavior remains manual.
- Default focused checks:
  - Python/service changes: `$HOME/miniconda3/bin/python3 -m pytest <test-path>`
  - Script changes: syntax check with `$HOME/miniconda3/bin/python3 -m py_compile <files>`
  - Changed Python source: `bin/lint-python <path> [path ...]`
  - Changed JavaScript source: `bin/lint-js <path> [path ...]`
  - Complete adopted source boundary: `bin/lint --scope <scope-id>`
  - Repo whitespace: `git diff --check`
  - Broader blast radius: `$HOME/miniconda3/bin/python3 tests/run_checks.py --profile <profile>`

## Important testing factors
- Before running Python tests that import Docs Viewer services, export `.env.local` in the same shell (`set -a; source .env.local; set +a`). Scope configuration is loaded during test collection, and configured external-local scopes require `DOTLINEFORM_PROJECTS_BASE_DIR`; a test run without it can fail during collection before any tests execute.
- `tests/run_checks.py --profile docs` is self-contained: its broad Python step receives a run-owned writable Projects base, its Studio document build explicitly skips registered media producers, and its Studio search build does not resolve media storage. Checks that exercise managed media or registered media producers still need the real external workspace or an explicit suitable `--projects-base-dir <absolute-writable-path>`.
- Use the smallest relevant `run_checks.py` profile, such as `source-lint`, `quick`, `studio`, `catalogue`, `docs`, `docs-viewer-smoke`, or `studio-smoke`.
- When `tests/run_checks.py` is used, report the profile, pass/fail result, and `var/test-runs/.../summary.md` path.
- For commands that bind loopback ports or launch browser smokes, run them with elevated localhost/browser permissions in the Codex sandbox. Keep pure syntax checks, `git diff --check`, JSON parsing, and non-network pytest runs sandboxed.
- If a local route is expected to be running but the sandbox cannot reach localhost, use an isolated temporary build/server if automated verification needs it.
- When explicitly agreed as needed, Codex-run browser checks should use Playwright from the Miniconda environment:
  - Playwright CLI: `$HOME/miniconda3/bin/playwright`
  - Python entrypoint: `$HOME/miniconda3/bin/python -m playwright`

## Public Static Site Toolchain

- `site/` is the tracked static site root and the GitHub Pages upload root.
- `site-tools/config/site-tools.json` owns static-site validation config and site-level media settings used by local Python tooling.
- `site-tools/config/site-code-update.json` is the sole canonical-to-site inventory for shared/public Docs Viewer runtime code. When a change touches a canonical file represented there, run `bin/site-code-update`, inspect the exact tracked `site/` delta, then run `bin/site-code-update --check` and `bin/site-validate` before presenting the work for commit. Adding, removing, or changing the public status of a runtime file requires an explicit manifest update; local-only files in mixed source directories remain excluded.
- Use `bin/site-validate` to validate the deploy root.
- Use `bin/site-preview` for local public-site preview; it serves `site/` directly with Python's HTTP server.
- Local Studio is served by `bin/local-studio`, not by the public-site preview server.

## Security And Sanitization

- Use `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/scopes/studio/source/documents/d-20260523-190651-7157ec.md` for sanitization triggers and local write-service safety.
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
