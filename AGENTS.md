## General Behaviour

- Ask for confirmation before edits unless the request is trivial or the user has explicitly asked for the edit.
- For code changes, summarize the intended change set and ask for confirmation before editing unless the request is trivial.
- Use `documentation/development/Development_Checklist.md` as the project implementation checklist. Keep durable repo guardrails there.
- Use `documentation/development/Development_Workflow.md` when lifecycle decisions, roadmap deliveries, task trackers, or closeout state need more context.
- Implement the agreed operating model. Do not silently add requirements for concurrent users, external mutation, corrupted application data, backward compatibility, automatic repair or stronger recovery. Raise material extensions to that model before implementing them.
- Give validation one authoritative owner. Authoring/import owners establish domain validity; downstream operations trust completed application-produced data and handoffs. Retain necessary parsing, authority, confinement, sanitization and transfer checks at their actual boundaries.
- Carry known inputs and completed effects forward. Reuse loaded state, resolved configuration, parsed records and supplied selections. Additional calls, reads, scans, hashes, rebuilds and refreshes require a concrete operational purpose.
- Choose the authoritative owner before the implementation language or existing helper. Studio and Docs Viewer are predominantly frontend apps in a single-user local operating model. Selection, authoring feedback, membership choices and view state belong in the browser when it already has the required data; Python owns required filesystem persistence, media processing, generation and transfers. State the frontend responsibility and concrete server work before implementation. Existing Python code is not a reason to move a browser-owned decision to the server.
- Give routine operations narrow interfaces and explicit dependencies. Separate metadata discovery, selected preparation, rendering, persistence, transfer and explicit maintenance. One workflow owner should expose the consequential reads, transformations, writes and completion effects, carrying resolved inputs forward. Do not conceal expensive loading, validation or rendering behind general context-loading helpers, shared mutable state, constructors or default arguments.
- Refactor along demonstrated responsibility boundaries within the agreed delivery. A useful extraction removes an implicit dependency, duplicated decision or unnecessary operation; file-size reduction or more modules alone is not evidence of improvement. Review reused helpers beyond the changed lines, and keep each extraction's inputs, output and side effects clear.
- Review defensive behavior explicitly. Every material delivery's code review must challenge unnecessary validation, auditing, preflights, freshness checks, normalization, fallbacks and recovery machinery, including behavior hidden inside reused helpers. Record material safeguards and their justification in implementation notes. Use the mandatory Redundancy And Defensive Behavior Review in `documentation/development/Development_Checklist.md`.
- Compatibility aliases are prohibited unless justified before implementation with removal criteria.
- If you find compatibility layers during new feature development, report. Fix them immediately when non-trivial.
- Tests and documents are not contracts for deciding how to implement code. They should follow current development objectives unless a constraint has been called out and agreed.
- Answer questions based on domain best practice, suggest ways to reduce maintenance risk and improve performance, and raise likely side effects or missing requirements.
- When discussing options, explain tradeoffs in a way that helps the user decide and iterate requirements.
- Prefer targeted file reads, scoped diffs, and concise command output over broad searches or full diffs.

## Key development factors
- The public site has no deploy-time build step: `site/` is the tracked GitHub Pages artifact. Shared/public Docs Viewer JavaScript and stylesheets are canonical under `docs-viewer/` and have an explicit tracked projection under `site/docs-viewer/`; local apps serve the canonical files while public preview and GitHub Pages serve the projection.
- For long multi-batch work, or before a long thread reaches context limits, produce a handoff with changed files, decisions made, remaining tasks, commands run, and known risks. Keep the delivery document to current/next state, checkboxes, decisions, and completion gates.
- Review [Working](documentation/_working/README.md) for active/proposed work when choosing or resuming a task. Changes needing a plan use concise outcome, scope, steps, decisions and completion gates under `documentation/_working/`, following [Development Workflow](documentation/development/Development_Workflow.md). A central feature register or mandatory feature-parent hierarchy is not required.
- Local servers do not need to support multiple concurrent users. Modal workflows always complete before another one starts.

## Processing Project Boundary

- `processing/` is tracked in this Git repository but is currently a separate Java/Processing project, not a module of the website or the deployed `site/` artifact.
- Durable Processing documentation belongs to its project owner under `documentation/Processing/`. Any Docs Viewer document collection needs its own explicit configuration and does not define the Processing project's build or test lifecycle. Do not apply website runtime, build, test, or release assumptions to Processing implicitly; treat integration with the website as an explicit cross-project change.
- Processing work media belongs under the explicitly configured `$DOTLINEFORM_PROJECTS_BASE_DIR/processing/<project-id>/` boundary. A GUI-launched sketch must use its project-local portable configuration, validate the exact project identity, and fail visibly without falling back to the sketch or repository.

## Native Application Boundary

- `app/` is the tracked Swift native-application project, separate from the website runtime, `site/` deployment artifact, and `processing/` project. Read `app/AGENTS.md` before changing it.
- The maintained project and scheme are `app/dotlineform.xcodeproj` and `dotlineform`. One Swift 6 app target supports native Mac and iPad destinations only, with minimum macOS and iPadOS 26.0; iPhone and Apple Vision are outside the target boundary.
- Run App commands from the repository root and place repeatable command-line build products under the ignored `var/app/DerivedData/` boundary. Retain the selected Personal Team identifier in `project.pbxproj`; Apple-account credentials, certificates and private keys, Xcode-managed provisioning artifacts, device state, and `xcuserdata` remain local.
- Native Mac and physical-iPad presentation remain manual review gates. Signing, device installation, paid cloud activation, deployment, commit, and push require their own explicit action.

## Documentation And Generated Payloads

- Put current behaviour and ownership under `documentation/reference/`, design rationale and concepts under `documentation/design/`, and useful completed work records under `documentation/deliveries/`. Active or proposed deliveries and writing in progress live under `documentation/_working/`. Live development guidance lives under `documentation/development/`; Processing uses `documentation/Processing/`. The Studio documentation migration is complete. Link to useful delivery evidence when it answers a concrete question, while keeping current behaviour independently described in Reference. Use concise Markdown filenames with underscores, retain each existing `doc_id` and `title` in front matter, and update links when moving files.
- For repository documentation edits, read the current file and edit it directly with `apply_patch`. Repository documentation does not use the Docs source service or Docs/Search rebuilds.
- When writing or updating Markdown source documents, do not apply a fixed-column source wrap. Each paragraph is one source line, each list item is one source line. Code blocks, tables, headings, and front matter retain their required structure.
- The single Docs workspace stores canonical input in `$DOTLINEFORM_DOCS_BASE_DIR/working/source/`, replaceable output in `working/generated/` and selected prepared publication artifacts in `preview/`. Pre-publish, local Published, scope nesting and repository storage fallbacks remain retired.
- `docs-viewer/config/workspace/docs-workspace.json` owns storage resolution. Working owns source/generation, registration and finished public artifacts. Preview derives configured artifact/media owners without a browser stage, source/generated tree or preparation endpoint. Missing external storage is unavailable; never infer a fallback root or manufacture another workspace.
- Working owns configured document/media inputs, ready bytes and prepared public output. Generation records complete document-media references upstream. Preview receives selected finished artifacts and media; it has no persistent source/generated inputs, complete-snapshot receipt or browser route. Source Save and confirmed document Delete own their selected media removals; external-edit residue and orphan cleanup remain manual.
- For an ordinary Markdown create or edit, resolve the canonical Working documents location from workspace and collection configuration. When that source is directly writable, edit the Markdown file in place with `apply_patch`; do not route the text edit through the source service. The filesystem watcher is retired. Deliberate external source edits require explicit document generation; application Source Save awaits its own exact build and fresh display.
- Regenerate an external doc-only source change with `$HOME/miniconda3/bin/python3 docs-viewer/build/build_docs.py --stage working --write --only-doc-ids <comma-separated-doc-ids> --skip-media-builds`. For a configured named collection, add `--collection <child-id>` while retaining `--only-doc-ids`. Named-collection targeted builds read selected source files and merge their metadata into saved manifests, preserving unselected by-ID payloads. Ordinary targeted builds read selected sources and merge saved navigation metadata. Omit `--only-doc-ids` only for an intentional complete collection build. Inspect required output without rerunning solely for idempotence evidence.
- Use a complete collection document build only when targeted prerequisites are missing, a global builder/config/renderer contract changed, generated state needs complete reconciliation, or registered media output is actually under review. Add `--skip-media-builds` for a docs-only full reconciliation; omit it only when the registered media producers and real external workspace are part of the evidence.
- Docs search has no targeted-postings mode and intentionally does not follow ordinary management writes automatically. A stale Search index after an ordinary document edit is not unfinished document work. Rebuild Search only when the user explicitly requests it or Search itself is the task, using the Manage Rebuild control or `$HOME/miniconda3/bin/python3 docs-viewer/build/build_search.py --stage working --write`. Infrequent persistent media-source edits use the agreed explicit Rebuild docs and Search action; normal Save and exact-document Rebuild perform no media production or detection work.
- Search remains stage-independent `docs_viewer_search_index_v4` with identity/postings and no stage/result URLs. Explicit Working Search builds queue exact saved bytes; Full Working Build generates and queues Recent. Ordinary document operations preserve both. Publish copies only queued discovery output without freshness/membership checks or JSON rewriting.
- `build_docs.py` prints a compact human summary by default. Automation that needs the machine-readable diagnostics line should pass `--diagnostics`.
- A complete Working Build prepares local/public output, queues its completed effects and records operation completion. Publish is one awaited empty-body `/docs/publish` operation consuming only Docs/Catalogue selections. It applies selected files/removals to Preview and configured destinations, verifies selected transfers and removes successful units. Empty queues produce no publication work. Review repository output with `bin/site-preview`.
- Working draft state and the saved exclusion policy own upstream eligibility. Ordinary/non-Catalogue sources require explicit boolean draft; Catalogue has fixed intrinsic eligibility. Draft/unpublishable exclusions include descendants, and excluded collection hosts exclude their document collection. Publish trusts completed effects and performs no eligibility calculation, content/schema audit, generation, source read, directory/remote listing or corpus reconciliation. Catalogue host changes remain design-time-owned and do not delete canonical Work data/media.
- Carry resolved configuration, parsed queues, exact selected artifacts and verified Preview bytes through publication. Complete each document and its supplied media, or Catalogue Work unit, before successful entry removal; required shared output follows item work. Keep required path/symlink confinement, missing-input failures and selected output/transfer verification. Do not add progress/resume flags, freshness checks, corpus inventories or another publication ledger.
- Docs Viewer Manage exposes one Publish action. Working/Preview remain internal storage/build/publication roles; the stage selector, Preview browsing and split preparation/distribution endpoints are retired without aliases. Git commit and push remain explicit ordinary user actions. Deploy Public remains the separate manually triggered GitHub Pages workflow over the committed `site/` snapshot.
- Recovery uses ordinary sources and Git history: fix the source, builder or destination and rerun the owning Build or Publish operation. Publication lineage requires exact configured Working collection owners; current configuration has no lineage workflow, and the two inactive historical tables were explicitly retired at cutover. The clean Git commit immediately before the Stage 2.3 repository-copy removal remains the recovery point for that retired tracked tree; do not add aliases, shadow copies, retry markers, transactional swaps or automatic backup directories.

## Runtime And Paths

- Run project commands from `dotlineform-site/` unless explicitly told otherwise.
- Use `$HOME/miniconda3/bin/python3` for Python commands.
- Do not invoke Python entrypoints through their shebangs in Codex runs. Use `$HOME/miniconda3/bin/python3 <script>` explicitly.
- Env vars are saved in `.env.local`.
- In repo docs and command examples, prefer the shortest project-local script form unless a pinned interpreter or non-default path is required.

## Checks And Test Policy

- Use [Verification](documentation/development/Verification.md) for focused static diagnostics, required public projection/validation, bounded code review and manual acceptance. Leave visual and tactile UI review to the user unless specifically requested.
- Agree each test delivery separately before editing tests, fixtures or harnesses, including temporary regression scripts. Use [Test Contract Discipline](documentation/development/Test_Contract_Discipline.md) for the specification, coverage record, run selection and workspace isolation. An approved specification authorizes implementation within its scope.
- Run the smallest selection that answers the named risk. Use the app or tool that owns the behavior and reserve browser automation for failures that depend on a durable browser integration boundary. Report the evidence and its limits.

## Public Static Site Toolchain

- `site/` is the tracked static site root and the GitHub Pages upload root.
- `site-tools/config/site-tools.json` owns static-site validation config and site-level media settings used by local Python tooling.
- `site-tools/config/site-code-update.json` is the sole canonical-to-site inventory for shared/public Docs Viewer runtime code. When a change touches a canonical file represented there, run `bin/site-code-update`, inspect the exact tracked `site/` delta, then run `bin/site-code-update --check` and `bin/site-validate` before presenting the work for commit. Adding, removing, or changing the public status of a runtime file requires an explicit manifest update; local-only files in mixed source directories remain excluded.
- Use `bin/site-validate` to validate the deploy root.
- Use `bin/site-preview` for local public-site preview; it serves `site/` directly with Python's HTTP server.
- Local Studio is served by `bin/local-studio`, not by the public-site preview server.

## Security And Sanitization

- Use `documentation/development/Development_Checklist.md` for sanitization triggers and local write-service safety.
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
