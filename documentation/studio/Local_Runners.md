---
draft: false
doc_id: d-20260422-174736-9bd0fc
title: Local Runners
added_date: "2026-04-22 17:47:36"
last_updated: "2026-10-24"
parent_id: d-20260413-000000-d314b7

---
# Local Runners

## Choose A Runner

| Command | Starts |
| --- | --- |
| `bin/local-studio` | Local Studio catalogue/tag routes |
| `docs-viewer/bin/docs-viewer` | Docs Viewer management, document-package routes, and Docs Review when enabled |
| `bin/site-preview` | checked-in public `site/` preview |
| `bin/local-all` | all enabled services above under one supervisor |

Run only the owner you are changing. Use `bin/local-all` when a workflow crosses app boundaries or Studio links need both the public preview and Docs Viewer.

## Default Boundaries

| Surface | Default URL | Owner |
| --- | --- | --- |
| Public preview | `http://127.0.0.1:4000/` | `bin/site-preview` |
| Studio | `http://127.0.0.1:8765/studio/` | `studio_app_server.py` |
| Docs Viewer | `http://127.0.0.1:8776/docs/` | Docs Viewer service |

Each app owns its own pages and APIs. `bin/local-all` supervises siblings; it does not merge their routes into Studio or add compatibility aliases.

## Studio Runner

`bin/local-studio`:

1. changes to the repo root and loads `.env.local` when present;
2. chooses `$HOME/miniconda3/bin/python3` when available;
3. verifies the configured Studio port before starting;
4. starts `studio/app/server/studio/studio_app_server.py` when enabled;
5. stops its child on interrupt, termination, or runner exit.

The filesystem watcher is retired. Docs application writes complete their own required generation through the Docs Viewer service. External Markdown edits require exact-document Rebuild; rare persistent media edits use the explicit Rebuild docs and Search action. [Source Organisation](Source_Organisation.md#explicit-external-edit-and-media-rebuilds) owns those workflows. Studio Catalogue Save and explicit Refresh retain their own boundaries; the runner performs no startup Catalogue or document rebuild.

## All-Services Runner

`bin/local-all` loads the same local environment, then preflights enabled host/port bindings for conflicts and availability before starting any child.

It starts the public preview, Studio runner, and Docs Viewer in that
order. If any child exits, the supervisor identifies it, stops the remaining
children, and returns a failing status for an unexpected clean exit or the
child's error status.

This fail-together behavior is useful for an integrated local session; it is not a production orchestration contract.

## Configuration

Local overrides belong in `.env.local`. The main variable families are:

- `STUDIO_APP_*` for enablement, host, port, and access logging;
- `SITE_*` for public preview enablement and binding;
- `DOCS_VIEWER_*` for the Docs Viewer binding/base URL and optional review surface.

The runner scripts are the authority for exact names and defaults. Avoid copying the full variable inventory into app documentation; it changes whenever local services are split or renamed.

Successful requests are quiet by default, while shared local HTTP logging retains useful 4xx/5xx service, method, path, and status context. Enable an app's access-log flag only when request-level detail is needed.

## Early Browser Disconnects

Studio, Docs Viewer and Site Preview use `IgnoreEarlyDisconnectMixin` from `studio/shared/python/local_http_logging.py`. It suppresses only `ConnectionResetError` raised before Python has read the first HTTP request line. At that point no application request has been parsed or dispatched. The connection closes normally through the existing server cleanup; there is no response, retry or recovery work.

Once Python has assigned `raw_requestline`, resets and other exceptions from header parsing, body reads, application handlers and response writing retain their existing error paths. Other exception types before the request line also remain visible. Existing 4xx/5xx logging and Site Preview's separate abandoned-file-response handling retain their owners. Restart the affected server or `bin/local-all` to load this Python change.

### Focused Disconnect Test Coverage

The user approved this test specification on 2026-10-24. The exact selection is `studio/tests/python/test_local_http_disconnects.py`; no profile definition or existing test is changed. The existing `studio` profile discovers this file through its complete `studio/tests/python` directory selection; it has no separate entry in the smaller explicit profiles. The tests protect the phase boundary that separates harmless early resets from real request failures, using the production mixin and Python's real `BaseHTTPRequestHandler` parser/dispatch over in-memory socket substitutes.

| Selector | Input and expected outcome |
| --- | --- |
| `test_early_reset_closes_without_dispatch` | The first request-line read raises `ConnectionResetError`; construction completes with the connection marked closed, no application dispatch and no response. |
| `test_header_reset_propagates` | A valid GET request line is followed by a reset while reading headers; the error propagates before application dispatch. |
| `test_body_reset_propagates` | A POST with a declared body resets during the application's body read; the error propagates after dispatch, with no response. |
| `test_application_errors_propagate` | A parsed GET handler raises either `ConnectionResetError` or `RuntimeError`; the exact application exception propagates. |
| `test_normal_request_still_returns_response` | A complete GET reaches the handler and returns an ordinary HTTP 200 response with the expected body. |

The file owns its in-memory reader/socket and minimal GET/POST handler; there are no fixtures, application-service imports, real sockets, servers, ports, credentials, external workspace reads or writes. Only ordinary pytest/bytecode caches may be created. This selection proves the shared HTTP boundary, not real browser reset timing, application-route behavior, live stderr formatting or the three server classes' wiring; those integrations receive source review. Run `python3 -m pytest studio/tests/python/test_local_http_disconnects.py -q` when changing this boundary. Expected runtime is seconds with low setup/compute cost; maintenance is limited to this small stdlib adapter. Run once, then repeat only after a relevant change or failure. Code review and the selected run record complete this scope.

Implemented and verified on 2026-10-24: the exact file selection passed all six cases in 0.04 seconds. Focused Python lint passed for the shared helper, all three server owners and the test file; whitespace checks passed. `python3 site-tools/site_preview.py --help` confirmed the preview's new shared import without starting a server. The distinct code and Redundancy And Defensive Behavior Review checked stdlib request-line assignment, exception propagation, existing finish/shutdown cleanup, all three explicit mixin integrations, preview import setup and the tests against their approved cases. The suppression uses the existing request-line phase marker and catches only the reported exception type; it adds no broader exception filter, validation, retry, recovery state, request parsing copy or extra I/O. Existing error logging and file-transfer disconnect handling remain intact. No actionable findings remained. No broad profile, live HTTP/browser check, application mutation, server restart, public projection, commit or push ran. Live log confirmation follows the ordinary server restart.

## Public Preview And Validation

`bin/site-preview` serves the checked-in `site/` tree. `bin/site-validate` checks that deploy-root contract without copying or generating files. Neither starts Studio services.

Studio public links use the configured preview base, so the preview must be running when testing those cross-host links.

## Extension And Weak Spots

- Add a new long-running app as its own runner first, then make `local-all` supervise it.
- Keep port preflight and shutdown behavior symmetrical when adding a child.
- Keep app routes with their owner; a runner should not provide old-path aliases.
- Environment settings are spread across sibling runners rather than described by one checked schema; inspect the scripts before changing cross-runner defaults.
