#!/usr/bin/env python3
"""Smoke-check shared Studio operational route shell JavaScript helpers."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import Page, sync_playwright


class QuietStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A003
        return


def start_static_server(site_root: Path) -> tuple[ThreadingHTTPServer, str]:
    resolved_root = site_root.expanduser().resolve()
    if not resolved_root.exists():
        raise FileNotFoundError(f"site root does not exist: {resolved_root}")
    handler = partial(QuietStaticHandler, directory=str(resolved_root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def assert_operational_route_helpers(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            document.body.innerHTML = `
              <section id="root"></section>
              <button id="run"></button>
              <p id="status"></p>
            `;
            const module = await import('/studio/app/frontend/js/studio-operational-route.js');
            const root = document.getElementById('root');
            const run = document.getElementById('run');
            const status = document.getElementById('status');
            const state = {
                root,
                serviceAvailable: false,
                isRunning: false,
                entries: []
            };
            const required = module.collectOperationalRouteElements({
                root,
                run,
                missingNode: null
            });
            const unavailable = module.renderOperationalServiceStatus(status, state, {
                unavailableText: 'Service unavailable.',
                unavailableState: 'error'
            });
            const disabled = module.applyOperationalRunButtonState(run, state, {
                serviceAvailable: (routeState) => routeState.serviceAvailable,
                isBusy: (routeState) => routeState.isRunning
            });
            module.markOperationalRouteReady(state, true, {
                route: 'demo-route',
                mode: (routeState) => routeState.entries.length ? 'results' : 'idle',
                serviceAvailable: (routeState) => routeState.serviceAvailable,
                isBusy: (routeState) => routeState.isRunning,
                recordLoaded: (routeState) => routeState.entries.length > 0
            });
            state.serviceAvailable = true;
            state.isRunning = true;
            state.entries = [{ id: 1 }];
            const busyDetail = module.buildOperationalRouteStateDetail(state, {
                route: 'demo-route',
                mode: (routeState) => routeState.entries.length ? 'results' : 'idle',
                serviceAvailable: (routeState) => routeState.serviceAvailable,
                recordLoaded: (routeState) => routeState.entries.length > 0
            });
            module.syncOperationalRouteBusyState(state, {
                route: 'demo-route',
                mode: 'results',
                serviceAvailable: true,
                isBusy: (routeState) => routeState.isRunning,
                recordLoaded: true
            });
            await Promise.all([
                import('/studio/app/frontend/js/bulk-add-work.js'),
                import('/studio/app/frontend/js/project-state.js'),
                import('/studio/app/frontend/js/studio-audits.js'),
            ]);
            const registry = await import('/studio/app/frontend/js/studio-route-registry.js');
            const config = {
                app: {
                    routes: {
                        project_state: {
                            label: 'project state',
                            title: 'Project State',
                            path: '/studio/project-state/?mode=manage',
                            script: '/studio/app/frontend/js/project-state.js',
                            doc_id: 'project-state-page',
                            nav: false,
                            shell_type: 'javascript',
                            ready_state_route_id: 'project-state'
                        },
                        catalogue_work_editor: {
                            label: 'work editor',
                            title: 'Catalogue Work Editor',
                            path: '/studio/catalogue-work/?mode=manage',
                            script: '/studio/app/frontend/js/catalogue-work-editor.js',
                            doc_id: 'catalogue-work-editor',
                            nav: false,
                            shell_type: 'javascript',
                            ready_state_route_id: 'catalogue-work'
                        }
                    }
                }
            };
            const route = registry.resolveStudioRoute(config, { pathname: '/studio/project-state/' });
            const contract = registry.buildStudioShellContract(config, { pathname: '/studio/project-state/' });
            const missing = registry.buildStudioShellContract(config, { pathname: '/studio/not-registered/' });
            const workRoute = registry.findStudioRoute(config, 'catalogue-work-editor');
            return {
                required,
                unavailable,
                disabled,
                statusText: status.textContent,
                statusState: status.dataset.state,
                runDisabled: run.disabled,
                ready: root.dataset.studioReady,
                modeAfterReady: root.dataset.studioMode,
                serviceAfterReady: root.dataset.studioService,
                recordLoadedAfterReady: root.dataset.studioRecordLoaded,
                busy: root.dataset.studioBusy,
                modeAfterBusy: root.dataset.studioMode,
                serviceAfterBusy: root.dataset.studioService,
                recordLoadedAfterBusy: root.dataset.studioRecordLoaded,
                busyDetail,
                resolvedRouteId: route && route.id,
                resolvedRouteReadyId: route && route.readyStateRouteId,
                contractShouldRenderShell: contract.shouldRenderShell,
                contractReason: contract.reason,
                missingContractReason: missing.reason,
                workRoutePath: workRoute && workRoute.path,
                workRouteNeedsScript: registry.routeRequiresShellScript(workRoute)
            };
        }"""
    )
    assert result["required"]["ok"] is False
    assert result["required"]["missing"] == ["missingNode"]
    assert result["unavailable"] == {
        "rendered": True,
        "message": "Service unavailable.",
        "state": "error",
    }
    assert result["disabled"]["disabled"] is True
    assert result["statusText"] == "Service unavailable."
    assert result["statusState"] == "error"
    assert result["runDisabled"] is True
    assert result["ready"] == "true"
    assert result["busy"] == "true"
    assert result["modeAfterBusy"] == "results"
    assert result["serviceAfterBusy"] == "available"
    assert result["recordLoadedAfterBusy"] == "true"
    assert result["busyDetail"] == {
        "route": "demo-route",
        "mode": "results",
        "service": "available",
        "recordLoaded": True,
    }
    assert result["resolvedRouteId"] == "project_state"
    assert result["resolvedRouteReadyId"] == "project-state"
    assert result["contractShouldRenderShell"] is True
    assert result["contractReason"] == ""
    assert result["missingContractReason"] == "route_not_registered"
    assert result["workRoutePath"] == "/studio/catalogue-work/?mode=manage"
    assert result["workRouteNeedsScript"] is True


def run(site_root: Path) -> None:
    server, base_url = start_static_server(site_root)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{base_url}/", wait_until="domcontentloaded")
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            assert_operational_route_helpers(page)
            browser.close()
            if errors:
                raise AssertionError(f"page errors during operational route module smoke: {errors!r}")
    finally:
        server.shutdown()
        server.server_close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-root", default=".", help="Site root to serve for module imports.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(Path(args.site_root))


if __name__ == "__main__":
    main()
