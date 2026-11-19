---
draft: false
doc_id: d-20260422-174736-9bd0fc
title: Local Runners
added_date: "2026-04-22 17:47:36"
last_updated: "2026-11-19"
parent_id: d-20260413-000000-d314b7

---

# Local Runners

## Choose A Runner

| Command | Starts |
| --- | --- |
| `bin/local-studio` | Studio Catalogue authoring and its local APIs. |
| `docs-viewer/bin/docs-viewer` | Docs Viewer with generated reads and separately enabled Manage/Review. Service startup fills missing settings from `.env.local`. |
| `bin/site-preview` | The static `site/` preview after validation. |
| `bin/local-all` | The sibling services under one supervisor. |

Use the individual owner for a focused session and the supervisor for a cross-app session. [Environment and standalone Docs startup](Local_Setup.md#environment)

## Default Boundaries

| Surface | Default URL |
| --- | --- |
| Public preview | `http://127.0.0.1:4000/` |
| Studio | `http://127.0.0.1:8765/studio/catalogue-work/` |
| Docs Viewer | `http://127.0.0.1:8776/docs/` |
| Docs Review | `http://127.0.0.1:8776/docs-review/`, when enabled. |

Each service owns its pages and APIs. Studio links can point to the Docs reader or public preview through configured site bases. Changing one binding also requires keeping its consumer links aligned. [Configuration owners](Configuration_And_Extension_Points.md#find-the-owner)

## All-Services Runner

`bin/local-all` sources the local environment, checks enabled bindings for conflicts, then starts preview, Studio and Docs in that order. `SITE_ENABLED=0` skips preview and `STUDIO_APP_ENABLED=0` skips Studio. Docs Viewer starts in either case. A child exit stops the other children and returns failure, including an unexpected clean exit. Ctrl+C stops the supervised session. Review defaults on in the supervisor. [Supervisor source](../../bin/local-all)

## Configuration

Studio uses `STUDIO_APP_HOST`, `STUDIO_APP_PORT`, `STUDIO_APP_ENABLED` and `STUDIO_APP_ACCESS_LOG`. Preview uses `SITE_HOST`, `SITE_PORT`, `SITE_ROOT`, `SITE_PYTHON` and `SITE_VALIDATE`; `SITE_ENABLED` controls supervisor inclusion. Docs uses `DOCS_VIEWER_HOST`, `DOCS_VIEWER_PORT` and `DOCS_VIEWER_BASE_URL` plus the process flags described in Local Setup.

`SITE_PREVIEW_BASE` can override the preview cross-link base. Studio's runtime projection derives its Docs link from the Docs host/port or explicit base URL. Docs derives its Studio link from the Studio host/port. Runner/service source owns the exact defaults and argument parsing. Access logging is opt-in. Ordinary successful requests are quiet, while error logging retains service, method, path and status. [Studio runner](../../bin/local-studio) · [Preview runner](../../bin/site-preview) · [Docs service](../../docs-viewer/services/docs_viewer_service.py) · [Studio projection](../../studio/app/server/studio/studio_app_config.py)

## Early Browser Disconnects

Studio, Docs Viewer and preview use the shared `IgnoreEarlyDisconnectMixin`. It suppresses a `ConnectionResetError` only before the first request line has been read. Header/body/application failures retain their error paths. Preview separately handles abandoned file responses. Restart the affected Python server after changing this code. [Shared boundary](../../studio/shared/python/local_http_logging.py)

### Focused Disconnect Test Coverage

The approved 2026-10-24 test used the production mixin and Python's `BaseHTTPRequestHandler` parser and dispatch over in-memory socket substitutes. Its former path was `studio/tests/python/test_local_http_disconnects.py`. Recover that file from the revision in the retirement record if this boundary warrants new test work. [Site test retirement](../deliveries/Review_Test_Policy_And_Checks.md#recovery)

| Selector | Input and expected outcome |
| --- | --- |
| `test_early_reset_closes_without_dispatch` | The first request-line read raises `ConnectionResetError`; construction completes with the connection marked closed, no application dispatch and no response. |
| `test_header_reset_propagates` | A valid GET request line is followed by a reset while reading headers; the error propagates before application dispatch. |
| `test_body_reset_propagates` | A POST with a declared body resets during the application's body read; the error propagates after dispatch, with no response. |
| `test_application_errors_propagate` | A parsed GET handler raises either `ConnectionResetError` or `RuntimeError`; the exact application exception propagates. |
| `test_normal_request_still_returns_response` | A complete GET reaches the handler and returns an ordinary HTTP 200 response with the expected body. |

The historical selection used an in-memory reader/socket and a minimal GET/POST handler. It exercised the shared HTTP boundary without workspace or network effects. Browser reset timing and live logging remained unexercised. Source review traced the three server integrations. [Earlier run evidence](../deliveries/Runtime_Configuration_And_Recovery_Review.md#early-disconnect-delivery)
