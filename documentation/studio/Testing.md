---
draft: false
doc_id: d-20260501-174746-efd581
title: Testing
added_date: 2026-05-01 17:47:46
last_updated: "2026-10-11 00:00:00"
parent_id: ""
---
# Testing

## Policy

Tests are deliveries with specifications and costs. Approval of a product change or confirmed bug does not authorize automatically creating, updating, refactoring, deleting, or expanding tests, fixtures, harnesses, or collections. Agree that test work before implementing it, including temporary regression scripts.

[Test Contract Discipline](Test_Contract_Discipline.md) owns the specification and approval rules, durable coverage record, execution budget, and treatment of existing tests. Keep each test or coherent collection's exact scenarios, assertions, membership, setup, side effects, limitations, commands, and costs in a maintained document under Testing or its app/domain owner, outside delivery documents. Deliveries link to that record and report only selected run evidence and outcomes.

Choose the smallest justified existing evidence. Consider authoring, maintenance, runtime, compute, setup, token/context use, and diagnosis time. Running a test is a deliberate choice based on understood coverage and a concrete risk, not an automatic consequence of changing a file. An otherwise complete fix need not wait for a new test proposal unless the user has made that test an acceptance requirement.

When test work is approved, suitable automation boundaries include:

- pure domain/planner/parser behavior;
- service/API inputs, outputs, validation, and write boundaries;
- config and generated-data contracts;
- public/private ownership boundaries;
- route boot, module wiring, and shared ready/busy integration when only a browser can prove them.

Do not make permanent tests police normal UI choreography: wording, placement, focus timing, hover/cursor state, modal feel, or ordinary click sequences. Use manual or temporary browser inspection for those.

A UI change does not automatically require a permanent browser test or a browser profile run. Recorded manual confirmation is sufficient for normal interaction, presentation, filtering, navigation, and modal behavior when no durable browser integration boundary changed.

Assert the surviving value, owner, or behavior. Do not encode retirement history as negative existence checks for former files, routes, selectors, or actions; those checks age into stale failures without proving the current contract.

Local app routes are laptop/desktop-only. Do not add or retain phone-sized viewport passes, touch-specific interaction checks, or responsive-CSS assertions for Studio, Docs Viewer Manage, Docs Review, Import, or other local routes. Mobile and responsive acceptance belongs to the owning public `site/` feature and must exercise the checked public artifact.

## Review Gate

When specifying test work for approval:

1. Can a pure function prove it?
2. Can a service call or direct HTTP request prove it?
3. Does a generator/output assertion prove it?
4. Is the browser required for route/module/asset/request integration, or only imitating a user?
5. Will ordinary copy/layout/timing changes cause false failures?
6. What unique regression would this test catch, and why would repeated manual confirmation be materially costly or risky?

Use the first adequate layer. If the last question has no concrete answer, do not propose the browser test. Passing this design review does not itself authorize test implementation. A broad end-to-end path is not stronger evidence when a lower-level contract is the real risk.

## Evidence Map

These are options for selecting existing evidence within the agreed budget, not instructions to create tests or run every listed check.

| Change | Candidate evidence |
| --- | --- |
| docs | read-through, link/build checks when publication is in scope, `git diff --check` |
| Python model/service/parser | source inspection and an existing focused pytest selection when justified |
| local HTTP boundary | existing focused API test or bounded direct request |
| JavaScript helper/component | source inspection or an existing module/DOM check |
| generator/config projection | dry run plus output/schema assertion |
| public/local route boot or asset boundary | existing focused browser smoke when its documented boundary is at risk; use a normal desktop viewport for local routes |
| visual/tactile UI | manual/temporary browser check |
| broad ownership change | an explicitly selected `run_checks.py` profile after inspecting its members, side effects, and cost |

## App Ownership

Tests live with the app/domain they prove:

- `studio/tests/`
- `docs-viewer/tests/`

Public-site behavior may be exercised by the app that owns its runtime. Do not place a test in Studio merely because it uses a browser or reads `site/`. Public mobile checks remain with the public route owner rather than being approximated through a resized local app.

## Runner

[Run Checks](Run_Checks.md) describes the optional profile runner. Use its source or `--list` to resolve the current command inventory, and the maintained coverage records to understand what those commands actually prove. A command inventory alone is not a test specification. Profiles are convenience groupings, not mandatory gates. Broad pytest profiles must not collect smoke scripts; browser boundaries belong only to their explicit smoke profiles.

Typical focused command:

```bash
$HOME/miniconda3/bin/python3 -m pytest <owning-test-path> -q
```

Loopback servers and browser smokes need local port/browser permissions. Pure tests, JSON parsing, syntax checks, and diff checks remain sandboxed.

## Browser Boundary

[Browser Smoke Testing](Browser_Smoke_Testing.md) owns harness mechanics. Retain a permanent smoke only when it proves route boot, module loading, public/private assets, ready-state wiring, API reachability, or browser request/response agreement.

Executable smokes must not double as shared fixture libraries. Put the smallest genuinely shared server/readiness helpers in a separate support module. Existing UI-heavy or multi-workflow smokes are deletion candidates, not patterns to extend.

## Closeout

Report the selected command/profile, result, and the summary path when the profile runner was used, or state that no executable tests were warranted. Link the durable coverage record and state what the evidence proves and any remaining manual check. Keep run results in the delivery record; keep the test's maintained purpose and coverage outside it.

Do not repair unrelated brittle test behavior inside a focused feature slice without explicitly widening scope.

## Limits

### UI Text Retirement

The user approved retirement of the Studio text registry and inclusion of Docs Viewer in the same cleanup on 2026-10-11. The approved scope is implemented. Test maintenance is limited to removing the retired Studio text-module path from `artifact_families[id=studio_config_and_route_ui].repo_paths` and `.public_output.paths` in `tests/contracts/projection_contract.json`. The retained Studio config path and its forbidden public-output policy remain in that family. No test case, assertion, fixture, harness or profile membership changes are included, and no wording assertions are added.

Verification uses changed-source JavaScript/Python lint, Python syntax, read-only import/export and retired-reference inspection, JSON parsing of the edited contract, `bin/site-code-update --check`, `bin/site-validate` and whitespace review. These checks address broken module wiring, malformed configuration and stale public runtime copies; they do not establish browser interaction or exact visible wording. The public update command writes only inventory-owned tracked runtime copies before validation. Expected local cost is seconds, with no service/browser startup, network work, canonical document generation or publication; Python syntax may update ignored bytecode. No pytest, browser or profile run is included. [Studio Runtime](Studio_Runtime.md#ui-text-retirement) records the implementation and evidence.

### Studio Frontend Retirement

The user approved removal of the inspected unused Studio frontend modules/helpers, obsolete build-preview/readiness code and styles, unreferenced text entries, related references and the stale route-ready audit exception on 2026-10-11. The approved scope is implemented. Test maintenance is limited to `tests/audits/route_ready_state.py`: remove the deleted `studio-home.html` initial-ready exception, its otherwise unused `AppConfig.allow_initial_ready_true` option and the corresponding allowlist branch. Every configured template must start ready and busy as `false`. No test case, fixture, browser harness or profile membership is added, removed or expanded; other test files remain unchanged and unreviewed by this cleanup.

The retained focused selection is `python3 tests/audits/route_ready_state.py --strict --app studio`. It reads the real current `studio/app/frontend/routes/*.html` files and uses the existing HTML parser to check exactly one Studio ready-state root, boolean readiness, initially false readiness and matching initially false busy state. It uses no fixtures or mocks, starts no service/browser, performs no generation or media conversion, and writes no repository/workspace data or network traffic. Broader Docs Viewer template membership remains unchanged and is not part of this run. A pass proves the static template baseline, not browser boot, modal interaction, API responses or Save/Refresh/Publish behavior.

Verification is limited to the existing focused audit, changed-path JavaScript/Python lint, Python syntax, read-only module/import and retired-reference inspection, and whitespace checks. Expected local cost is seconds; authoring/maintenance removes one obsolete exception and its support code, without adding repeated test work. Syntax checks may update ignored Python bytecode. No pytest/profile/browser run, live write or publication is included. [Studio Runtime](Studio_Runtime.md#frontend-retirement) records the retired browser ownership.

### Studio Server Config Cleanup

The user approved removal of unused Studio server config projections/helpers, related obsolete assertions/references and orphaned bytecode on 2026-10-11. The approved scope is implemented. Test maintenance is limited to `studio/tests/python/test_studio_app_runtime_config.py::test_runtime_config_exposes_adapter_contract` and `::test_studio_route_registry_validation_rejects_invalid_routes`. No new cases, assertions, fixtures, harnesses or profile membership are included. The remaining tests in that file and broader Studio selections remain unchanged and unreviewed.

| Retained selector | Scenarios, inputs and asserted outcomes |
| --- | --- |
| `test_runtime_config_exposes_adapter_contract` | Read the real checked Studio route/workspace/pipeline configuration with temporary process-environment overrides for local site and Docs Viewer addresses. Retain the existing positive host, asset-version, runtime-config address, site bases, Work editor path/shell/ready identity, runtime-view identity and pipeline suffix/format assertions. Remove obsolete expectations for retired routes and removed service/data-path/navigation/modal metadata. Update the existing thumbnail-address assertion to the current `/docs/assets/works/thumbs` family. |
| `test_studio_route_registry_validation_rejects_invalid_routes` | Mutate in-memory copies of the real current runtime config. Retain duplicate-path, missing script/template, missing template file, unsupported shell type, external route containment and duplicated route-metadata rejection, plus valid additional-shell-route acceptance. The duplicate-path fixture clones the current Work editor record; the duplicate-metadata fixture uses that same real route identity under an explicitly constructed `paths.routes` object. No production route or config is changed. |

Studio test setup establishes import paths and imports the real server/config modules. These two cases use no mocks or shared temporary-workspace fixture, and read the existing configured Docs/Projects roots while resolving media addresses; they do not mutate canonical/workspace data, start HTTP servers, build output, convert media or use the network. Environment overrides are restored by the existing `finally` block. Pytest and syntax checks may update ignored local caches. Run only the two full node IDs with `python3 -m pytest <node-id> <node-id> -q` after exporting `.env.local` when config projection or route validation changes. Expected local cost is seconds; authoring/review is limited to deletion of obsolete expectations and repair of those two fixture fragments, with no added repeated runtime. A pass establishes these config/parser contracts, not HTTP dispatch, API writes, browser behavior or publication. Focused lint, syntax, configured read-only imports, source-reference review and whitespace checks provide the remaining removal/wiring evidence.

### Shared Helper Retirement

The user approved removal of unused `studio/shared/python/` helpers, obsolete prose configuration, one Markdown test case and two orphaned bytecode files on 2026-10-11. The approved scope is implemented. The bounded test work removes `studio/tests/python/test_markdown_renderer.py::test_separator_only_normalizer_preserves_unicode_blank_lines`, its import and its direct-script `main()` registration. That case passed `Before\n\u00a0\nAfter\u2028Next` to the otherwise unused separator-only helper and asserted preservation of the Unicode-only blank line plus a Markdown hard break. It used the real pure normalizer without fixtures, mocks, file writes, services or network access. No replacement case, fixture, harness or profile change is included; other test cases and registrations remain unchanged.

The retained verification selection is `studio/tests/python/test_markdown_renderer.py::test_normalizes_unicode_space_only_lines_outside_literal_blocks`, `::test_normalizes_unicode_line_and_paragraph_separators` and `::test_normalizes_unicode_separators_without_markdown_spaces_in_literal_blocks`. These exercise the real pure normalizer with inline strings and assert Unicode blank-line conversion outside fenced/preformatted content, hard-break/paragraph conversion and literal-block line-ending preservation. They address the removal of the internal normalization switch and do not prove service, import, Search-build or browser behavior. Run them by passing those three full selectors to `python3 -m pytest`; focused source lint, syntax, configured read-only imports, JSON parsing and whitespace checks provide removal/wiring evidence. Studio test setup only establishes import paths; pytest and syntax checks may update ignored local caches. The local execution budget is seconds with no service startup, generation, media conversion or network transfer; setup and maintenance are limited to the existing test file and this record.

### Catalogue Service Retirement

The user approved removal of the inspected unused Studio services/helpers, stale caches and their related obsolete tests/references on 2026-10-11. The approved scope is implemented. This retires obsolete coverage, with no replacement tests, new cases, harnesses or profile expansion.

| Retired test file | Former scenarios and reason for removal |
| --- | --- |
| `studio/tests/python/test_catalogue_routes.py` | Uniqueness and preflight membership of a disconnected route-constant table. The mounted Studio API no longer consumes that table, so these assertions provide no current routing evidence. |
| `studio/tests/python/test_catalogue_output.py` | Full/selected generation, stale-output cleanup, old external output-root confinement, thumbnail population, immediate Save/delete output completion, Detail sections, Save-time remote transfers, media versions and controlled upload/delete failures. The file imports the removed population API and the unused generator, constructs retired Detail records, and assumes pre-Refresh output/remote-transfer ownership. Its fake repository/Projects output root, local image-conversion substitutions and in-memory transport do not establish current Docs workspace or queue coverage. |
| `studio/tests/python/test_catalogue_delete_plans.py` | A non-mutating Series deletion preview that automatically clears Work membership, through the removed preview API. Current deletion requires an empty Series and has no such preview contract. |
| `studio/tests/python/test_catalogue_delete_service.py` | Revision rejection and canonical deletion of a Series, Work, Detail section or Detail while preserving independent rows and a frozen archive file. The request shapes, Detail families, populated-Series deletion and paused output contract are retired. The former temporary repository fixture does not model current queue/workspace completion. |

`studio/tests/fixtures/catalogue_factory.py` retains its two-Work/two-Series source fixture for the unchanged `studio/tests/python/test_studio_catalogue_write_routes.py`. It writes those maps with the current schema-only serializer and its existing local JSON helper; the retired Detail rows, production source-writer dependency and unused JSON reader are removed. No assertions are added or rewritten in the surviving route file. Its legacy response/workspace assumptions remain unreviewed, and it is not executed or adopted as current workflow evidence by this cleanup. The existing `write_json` helper and its other consumers remain available.

The `quick` profile's `python-syntax` command drops the two deleted service paths and the three explicitly listed deleted test paths; `quick-python-pytest` drops the deleted route and delete-preview files. The `studio` profile still selects the surviving Python test directory. Other profile members and test fixtures are unchanged and unreviewed. This scope does not repair or certify the broader profiles.

Verification is bounded source/import-reference review, changed-path Python lint, syntax compilation, configured read-only imports and whitespace checks. It uses no pytest/profile/browser run, production mutation, generation, media conversion, service startup or network transfer. Syntax checks may create local bytecode; stale source-less bytecode is cleared afterward. Expected execution cost is seconds locally; maintenance removes obsolete cases and adds only this coverage record, with no new repeated test runtime. Completion requires no surviving executable import or check registration for the retired code. This cleanup provides no new behavioral coverage for Save/Refresh/Regenerate/Publish or their failure paths.

### Source Save And Watcher Retirement

The current awaited Source Save and Draft generation paths have source/diff review and lint/syntax evidence. On 2026-10-08 the user confirmed normal and collection document authoring, changing Draft and starred state, and a much quicker experience. This is manual acceptance without measured timing; detailed route/history/reading-position cases were not separately itemised. No automated test selection has been adopted or executed for this change. Failure branches, other application-write workflows, explicit external-edit Rebuild and real persistent-media regeneration were not separately exercised as acceptance evidence.

`docs-viewer/tests/python/test_docs_live_rebuild_watcher.py` imports a retired production file and is unreviewed retirement residue. `test_docs_write_rebuild.py` and `test_docs_management_source_service.py` in the same directory still contain suppression hooks and obsolete request/build contracts; they cannot establish current Save coverage without separately approved review and test work. `test_docs_viewer_service_config.py`, `docs-viewer/tests/smoke/docs_viewer_route_smoke_support.py` and `tests/run_checks.py` still refer to the removed watcher configuration or selection. Other mutation/import tests also retain suppression-only arguments. These files, fixtures and profile memberships were left unchanged; their contents are neither implementation contracts nor claimed evidence. Any removal or replacement needs its own bounded specification and approval.

- Some Python tests retain direct-script compatibility and process-global assumptions.
- Profile membership is manually curated and can lag current ownership.
- A passing broad profile is not evidence for omitted app-smoke profiles or unexercised external workspaces.
