## General Behaviour

- Ask for confirmation before edits unless the request is trivial or the user has explicitly asked for the edit.
- For code changes, summarize the intended change set and ask for confirmation before editing unless the request is trivial.
- Use `documentation/studio/d-20260523-190651-7157ec.md` as the project implementation checklist. Keep durable repo guardrails there.
- Use `documentation/studio/d-20260523-000000-bf7161.md` when lifecycle decisions, roadmap deliveries, task trackers, or closeout state need more context.
- Compatibility aliases are prohibited unless justified before implementation with removal criteria.
- If you find compatibility layers during new feature development, report. Fix them immediately when non-trivial.
- Tests and documents are not contracts for deciding how to implement code. They should follow current development objectives unless a constraint has been called out and agreed.
- Answer questions based on domain best practice, suggest ways to reduce maintenance risk and improve performance, and raise likely side effects or missing requirements.
- When discussing options, explain tradeoffs in a way that helps the user decide and iterate requirements.
- Prefer targeted file reads, scoped diffs, and concise command output over broad searches or full diffs.

## Key development factors
- The public site has no deploy-time build step: `site/` is the tracked GitHub Pages artifact. Shared/public Docs Viewer JavaScript and stylesheets are canonical under `docs-viewer/` and have an explicit tracked projection under `site/docs-viewer/`; local apps serve the canonical files while public preview and GitHub Pages serve the projection.
- For long multi-batch work, or before a long thread reaches context limits, produce a handoff with changed files, decisions made, remaining tasks, commands run, and known risks. Keep the delivery document to current/next state, checkboxes, decisions, and completion gates.
- Non-trivial new features, requirements, or refactors are generally documented and parented to [Planned Features](documentation/studio/d-20260428-000000-f5ff18.md), which contains delivery planning guidance.
- Local servers do not need to support multiple concurrent users. Modal workflows always complete before another one starts.

## Processing Project Boundary

- `processing/` is tracked in this Git repository but is currently a separate Java/Processing project, not a module of the website or the deployed `site/` artifact.
- Durable Processing documentation belongs to its repository owner. The Docs Viewer Working `processing` collection is an explicitly configured document collection, not the Processing project's build or test lifecycle. Do not apply website runtime, build, test, or release assumptions to Processing implicitly; treat any integration with the website as an explicit cross-project change.
- Processing work media belongs under the explicitly configured `$DOTLINEFORM_PROJECTS_BASE_DIR/processing/<project-id>/` boundary. A GUI-launched sketch must use its project-local portable configuration, validate the exact project identity, and fail visibly without falling back to the sketch or repository.

## Native Application Boundary

- `app/` is the tracked Swift native-application project, separate from the website runtime, `site/` deployment artifact, and `processing/` project. Read `app/AGENTS.md` before changing it.
- The maintained project and scheme are `app/dotlineform.xcodeproj` and `dotlineform`. One Swift 6 app target supports native Mac and iPad destinations only, with minimum macOS and iPadOS 26.0; iPhone and Apple Vision are outside the target boundary.
- Run App commands from the repository root and place repeatable command-line build products under the ignored `var/app/DerivedData/` boundary. Retain the selected Personal Team identifier in `project.pbxproj`; Apple-account credentials, certificates and private keys, Xcode-managed provisioning artifacts, device state, and `xcuserdata` remain local.
- Native Mac and physical-iPad presentation remain manual review gates. Signing, device installation, paid cloud activation, deployment, commit, and push require their own explicit action.

## Documentation And Generated Payloads

- Durable Studio development and maintenance documentation is maintained in repository `documentation/studio/`. The full Studio source Markdown copy retains its existing filenames and immutable document IDs; use these repository files as the maintained authority.
- For `documentation/studio/` edits, read the current file and edit it directly with `apply_patch`. Repository documentation does not use the Docs source service, watcher, or Docs/Search rebuilds.
- When writing or updating Markdown source documents, do not apply a fixed-column source wrap. Each paragraph is one source line, each list item is one source line. Code blocks, tables, headings, and front matter retain their required structure.
- The single Docs Viewer workspace stores its lifecycle directly beneath `$DOTLINEFORM_DOCS_BASE_DIR`: canonical input in `working/source/`, replaceable Working output in `working/generated/`, prepared input/output in `pre-publish/source/` and `pre-publish/generated/`, and the accepted local snapshot in `published/`. Both external `scopes/analysis/` nesting and repository `docs-viewer/scopes/` storage are retired and must not be recreated or used as fallbacks.
- `docs-viewer/config/workspace/docs-workspace.json` is the authority for storage resolution. Source/generated operations require an explicit `working` or `pre-publish` stage; Published has its own reader and snapshot boundary. If the configured external root is unavailable, report the workspace as unavailable; do not create a replacement root, infer a repository path, or manufacture a second copy.
- Keep the same media skeleton beneath Working and Pre-publish: `<stage>/source/media/{img,svg,files,html,build-source/mermaid}`. Configured collections retain their collection-owned source/generated/media beneath each stage. Empty directories are intentional and may be retained.
- For an ordinary Markdown create or edit, resolve the canonical Working documents location from workspace and collection configuration. When that source is directly writable, edit the Markdown file in place with `apply_patch`; do not route the text edit through the source service. Let the docs watcher running under `bin/local-studio` rebuild the document projections. Do not run a manual Docs or Search rebuild merely to finish the source change.
- The watcher rebuilds document projections only; inspect those outputs and do not rerun the builder solely for idempotence evidence.
- If the watcher is unavailable, regenerate an ordinary doc-only source change with `$HOME/miniconda3/bin/python3 docs-viewer/build/build_docs.py --stage working --write --only-doc-ids <comma-separated-doc-ids> --skip-media-builds`. For a configured named collection, use `--collection <child-id>` instead of `--only-doc-ids`; named collection builds currently rebuild the full collection. An ordinary targeted build still recomputes its collection indexes while preserving unaffected by-ID payloads.
- Use a complete collection document build only when targeted prerequisites are missing, a global builder/config/renderer contract changed, generated state needs complete reconciliation, or registered media output is actually under review. Add `--skip-media-builds` for a docs-only full reconciliation; omit it only when the registered media producers and real external workspace are part of the evidence.
- Docs search has no targeted-postings mode and intentionally does not follow ordinary watcher or management writes automatically. A stale Search index after an ordinary document edit is not unfinished document work. Rebuild Search only when the user explicitly requests it or Search itself is the task, using the Manage Rebuild control or `$HOME/miniconda3/bin/python3 docs-viewer/build/build_search.py --stage working --write`.
- `build_docs.py` prints a compact human summary by default. Automation that needs the machine-readable diagnostics line should pass `--diagnostics`.
- A complete Build replaces the selected stage's `generated/` files and records the completed generated snapshot. Working owns authoring; Pre-publish explicitly prepares eligible Working source and builds its derivative. Review Pre-publish before Publish. Publish replaces the managed files under workspace-root `published/` with that prepared snapshot. Empty directories may remain.
- Working `draft` state and `working/source/documents/unpublishable.json` own preparation eligibility. Missing `draft` remains draft; no metadata backfill is implied. Publish accepts the complete prepared set and changes only the external `published/` snapshot. Every downstream consumer uses that same accepted document set. Subject specialisation belongs to the configured Works collection, not ordinary documents.
- Deploy Repo is a revision-bound preview/apply operation over one complete Published snapshot. It may perform configured destination preparation and reconcile only its owned repository/R2, document-location, Catalogue, and publication-lineage projections; it must not read source or generated output, invoke Build or Publish, or apply another document filter.
- The local Publish modal may compose Publish and Deploy Repo, with both selected by default when available, while retaining Publish-only and Deploy-Repo-only operation and separate outcomes. Git commit and push remain explicit ordinary user actions. Deploy Public remains the separate manually triggered GitHub Pages workflow over the committed `site/` snapshot.
- Recovery uses ordinary sources and Git history: fix the source, builder, or destination and rerun the owning Build, Publish, or Deploy Repo operation. Publication lineage requires exact configured Working collection owners; current configuration has no lineage workflow, and the two inactive historical tables were explicitly retired at cutover. The clean Git commit immediately before the Stage 2.3 repository-copy removal remains the recovery point for that retired tracked tree; do not add aliases, shadow copies, retry markers, transactional swaps, or automatic backup directories.

## Runtime And Paths

- Run project commands from `dotlineform-site/` unless explicitly told otherwise.
- Use `$HOME/miniconda3/bin/python3` for Python commands.
- Do not invoke Python entrypoints through their shebangs in Codex runs. Use `$HOME/miniconda3/bin/python3 <script>` explicitly.
- Env vars are saved in `.env.local`.
- In repo docs and command examples, prefer the shortest project-local script form unless a pinned interpreter or non-default path is required.

## Checks And Test Policy

- Use `documentation/studio/d-20260501-174746-efd581.md`, `documentation/studio/d-20260514-135716-c70591.md`, and `documentation/studio/d-20260501-000000-49b626.md` as the maintained test policy.
- `documentation/studio/d-20260627-212121-7cf7de.md` determines approach for subsequent testing and review of existing tests.
- Test work is a delivery with its own agreed specification. Approval to implement a feature or fix does not authorize creating, updating, refactoring, deleting, or expanding tests, fixtures, harnesses, or profile membership. Specify the proposed test work and obtain approval before implementing it; an already approved test specification is sufficient authorization within its scope.
- This applies to every test layer, including temporary regression scripts. Do not bypass the rule by calling new test code a probe, smoke, or one-off check.
- Maintain each test or coherent collection's specification and current coverage description outside delivery documents, under Testing or its durable app/domain owner. Document exact test paths/selectors and collection membership, scenarios and inputs, asserted outcomes, fixtures and mocks, real systems exercised, write/network effects, exclusions, run commands/triggers, and costs. A profile name, test count, pass result, or source listing alone does not explain coverage. Deliveries link to this record and keep only selected run evidence and outcomes.
- Account for authoring, maintenance, runtime, compute, setup, token/context use, and diagnosis time. Before a non-trivial run, identify the risk it addresses, the exact existing selection, what it proves, its side effects, and a proportionate cost estimate or unknowns. Use the smallest justified existing check within the accepted verification budget; do not run suites automatically because a file changed or a delivery is closing. Do not benchmark merely to fill an estimate.
- Read-only inspection and ordinary existing lint, syntax, whitespace, or direct diagnostic commands may provide focused evidence without creating test code. A documentation-only or trivial change may need no executable test. An unapproved test proposal does not block an otherwise complete fix unless the user has made it an acceptance requirement; report the evidence limit.
- Existing tests without adequate coverage documentation are unreviewed, not automatically accepted. Inspect only the relevant selection before relying on it; record what it actually does and any unknowns. Suite-wide documentation, cleanup, or redesign is separately scoped work. A failure does not authorize changing either the test or production behavior merely to obtain a pass.
- Leave UI design testing to the user unless specifically requested; browser probes are brittle.
- A UI change does not create an automatic requirement to add, update, or run a permanent browser test. Recorded manual confirmation is sufficient for ordinary interaction, presentation, copy, focus, modal, filtering, and navigation behavior when no durable browser integration boundary changed.
- Before adding or expanding a browser test, name the unique regression it could catch, why a pure/service/API/generator check cannot catch it, and why repeated manual confirmation would be materially costly or risky. If those answers are not concrete, do not change the browser suite.
- Do not use an executable smoke as a shared fixture library. Put genuinely shared route startup/readiness code in a small non-test support module; keep each retained smoke to one integration boundary.
- Treat a browser script over 500 lines or covering more than one route/workflow owner as a mandatory deletion/split review, not a file to extend. Existing profile membership is not evidence that the script remains worthwhile.
- Do not include smoke scripts in broad pytest collection. Smoke profiles are explicit boundary audits, not ordinary closeout gates.
- When specifying test work for approval, apply the review gate:
  - Can this be tested as pure function or service behavior?
  - Can this be tested by direct HTTP/API request?
  - Is a browser required to verify a product contract, or only to mimic user clicks?
  - Will this fail because copy, layout, focus, hover state, or modal timing changed?
- Permanent tests should protect data flows, server responses, generated contracts, parser behavior, ownership boundaries, and route/module integration. They should not police ordinary UI choreography, modal lifecycle feel, focus timing, copy, hover styling, or layout.
- Browser smokes are only for durable browser boundaries: route boot, module wiring, public/private asset boundaries, local API reachability, request/response agreement, or shared ready/busy state.
- Human manual checks are used for tactile interaction, visual fit, copy tone, modal feel, and mobile ergonomics.
- The retained Docs Viewer browser profile is intentionally limited to Manage route/service boot, Docs Review authority, public read-only isolation, and external-local Mermaid loading. Additions require an explicit policy change, not routine feature follow-through.
- The retained Studio browser profile is intentionally limited to local Catalogue route/service boot and one representative public Catalogue route without local capability. When automation is approved, deterministic Catalogue behavior belongs in Python tests; UI behavior remains manual.
- Command recipes for justified checks, not an automatic checklist:
  - Selected existing Python/service tests: `$HOME/miniconda3/bin/python3 -m pytest <test-path> [-k <selection>]`
  - Python syntax when relevant: `$HOME/miniconda3/bin/python3 -m py_compile <files>`
  - Changed Python source: `bin/lint-python <path> [path ...]`
  - Changed JavaScript source: `bin/lint-js <path> [path ...]`
  - Complete adopted source boundary: `bin/lint --scope <scope-id>`
  - Repo whitespace: `git diff --check`
  - Accepted collection with a documented purpose and cost: `$HOME/miniconda3/bin/python3 tests/run_checks.py --profile <profile>`

## Important testing factors
- Before running Python tests that import Docs Viewer services, export `.env.local` in the same shell (`set -a; source .env.local; set +a`). The Docs workspace requires `DOTLINEFORM_DOCS_BASE_DIR`; Projects-owned media and packages independently require `DOTLINEFORM_PROJECTS_BASE_DIR`. Docs pytest fixtures isolate both settings before service imports.
- Retire Scopes did not migrate tests or profiles. Existing scope-bearing test APIs and build commands are unreviewed for the new workspace contract; inspect the exact selection and obtain the separate test-work approval before changing them. Explicit build isolation uses `--docs-base-dir <absolute-writable-path>` and, when Projects-owned media or packages are involved, `--projects-base-dir <absolute-writable-path>` independently.
- Select a `run_checks.py` profile only after inspecting its resolved commands and coverage; prefer an individual command when the collection includes unnecessary work. Profile names such as `quick` do not establish cost or relevance.
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

- Use `documentation/studio/d-20260523-190651-7157ec.md` for sanitization triggers and local write-service safety.
- When a focused scan is needed for changed files, use:
  - `rg -n "/Users/|/home/|C:\\\\|miniconda|rbenv|api[_-]?key|token|secret|password|PRIVATE KEY" <changed-files>`

## Codex Cloud / Codespaces Runtime Contract

- Treat local and cloud sessions as one workflow with the same command shapes and validation steps.
- In cloud sessions, keep repo docs and examples machine-agnostic.
- Required shared env vars: `DOTLINEFORM_DOCS_BASE_DIR` for Docs lifecycle storage; `DOTLINEFORM_PROJECTS_BASE_DIR` for other project/media workspaces. Both select explicit existing roots and neither is an alias or fallback for the other.
- Optional shared env var: `MAKE_SRCSET_JOBS`
- Keep remote media credentials out of tracked files; use platform secret stores.
- Before reporting environment issues in Codex Cloud or Codespaces, run a Python version/dependency check for app/runtime, site validation, and preview work.
- Use dry-run generator commands first in cloud sessions unless an explicit write run was requested.

## Git And Change Hygiene

- Do not commit unless explicitly requested.
- Do not amend commits unless explicitly requested.
- Never use destructive git commands (`reset --hard`, checkout/revert of unrelated changes) without explicit approval.
- Ignore unrelated dirty files and do not revert user changes.
