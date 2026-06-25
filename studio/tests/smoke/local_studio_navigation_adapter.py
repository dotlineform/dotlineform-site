#!/usr/bin/env python3
"""Smoke-check the local Studio config/navigation adapter."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from studio.app.server.studio.studio_app_server import StudioAppServer  # noqa: E402
from tests.smoke.route_ready_helpers import wait_for_route_ready  # noqa: E402


def start_server() -> tuple[StudioAppServer, str]:
    server = StudioAppServer(("127.0.0.1", 0), REPO_ROOT)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)

    server, base_url = start_server()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            console_errors: list[str] = []
            page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
            page.goto(f"{base_url}/studio/", wait_until="domcontentloaded")
            wait_for_route_ready(page, "#studioHomeRoot", "data-studio-ready", "data-studio-busy")
            result = page.evaluate(
                """async () => {
                    const mod = await import("/studio/app/frontend/js/studio-navigation.js");
                    const publicLinks = await import("/studio/app/frontend/js/catalogue-public-links.js");
                    const configMod = await import("/studio/app/frontend/js/studio-config.js");
                    const config = await (await fetch("/studio/runtime-config.json")).json();
                    const services = mod.getStudioServices(config);
                    const url = mod.buildStudioViewUrl(config, "catalogue_status", {
                        scope: "studio",
                        empty: "",
                        zero: 0
                    });
                    const workEditorUrl = configMod.buildStudioRouteUrl(config, "catalogue_work_editor", {
                        work: "00001",
                        empty: "",
                        zero: 0
                    });
                    const publicWorkUrl = mod.buildPublicSiteUrl(config, "/works/", {
                        work: "00123",
                        from: "studio",
                        empty: "",
                        zero: 0
                    });
                    const cataloguePublicWorkUrl = publicLinks.buildPublicWorkUrl(config, "00123", {
                        from: "studio"
                    });
                    let cataloguePublicMissingBaseError = "";
                    try {
                        publicLinks.buildPublicSeriesUrl({}, "009");
                    } catch (error) {
                        cataloguePublicMissingBaseError = String(error && error.message || error);
                    }
                    const liveWorkUrl = mod.buildPublicSiteUrl(config, "/works/", { work: "00123" }, { site: "production" });

                    const homeLinks = [...document.querySelectorAll(".studioLinkList__item")].map((link) => ({
                        label: link.textContent.trim(),
                        viewId: link.getAttribute("data-studio-navigate"),
                        href: link.getAttribute("href")
                    }));
                    const topNavLinks = [...document.querySelectorAll(".site-nav .nav-item")].map((link) => ({
                        label: link.textContent.trim(),
                        viewId: link.getAttribute("data-studio-navigate"),
                        href: link.getAttribute("href"),
                        active: link.classList.contains("is-active")
                    }));
                    const topNavTitle = document.querySelector(".site-title a")?.textContent.trim();
                    const topNavHomeHref = document.querySelector(".site-title a")?.getAttribute("href");
                    const homeReady = document.querySelector("#studioHomeRoot")?.getAttribute("data-studio-ready");

                    return {
                        hasDocsService: Object.prototype.hasOwnProperty.call(services, "docs"),
                        hasExternalLinks: Object.prototype.hasOwnProperty.call(config, "external_links"),
                        publicPreviewBase: mod.getStudioSiteBase(config, "public_preview"),
                        productionBase: mod.getStudioSiteBase(config, "production"),
                        dataPath: config.app.runtime.data_paths.ui_text.catalogue_status,
                        mediaThumbWorks: config.app.runtime.media.thumbs.works,
                        pipelineThumbSuffix: config.app.runtime.pipeline.variants.thumb.suffix,
                        url,
                        workEditorUrl,
                        publicWorkUrl,
                        cataloguePublicWorkUrl,
                        cataloguePublicMissingBaseError,
                        liveWorkUrl,
                        runtimePrimaryNav: config.app.runtime.navigation.primary,
                        homeLinks,
                        topNavLinks,
                        topNavTitle,
                        topNavHomeHref,
                        homeReady
                    };
                }"""
            )
            browser.close()

        expected_url = "/studio/catalogue-status/?scope=studio&zero=0"
        if result["hasDocsService"]:
            raise AssertionError("runtime services unexpectedly exposed a Docs Viewer service")
        if result["hasExternalLinks"]:
            raise AssertionError("runtime config unexpectedly exposed external link config")
        if result["publicPreviewBase"] != "http://127.0.0.1:4000":
            raise AssertionError(f"unexpected public preview base: {result['publicPreviewBase']!r}")
        if result["productionBase"] != "https://dotlineform.com":
            raise AssertionError(f"unexpected production base: {result['productionBase']!r}")
        expected_top_nav = []
        if result["runtimePrimaryNav"] != expected_top_nav:
            raise AssertionError(f"unexpected runtime primary nav: {result['runtimePrimaryNav']!r}")
        top_nav_ids = [link["viewId"] for link in result["topNavLinks"]]
        top_nav_labels = [link["label"] for link in result["topNavLinks"]]
        if top_nav_ids != expected_top_nav:
            raise AssertionError(f"unexpected top nav ids: {result['topNavLinks']!r}")
        if top_nav_labels:
            raise AssertionError(f"unexpected top nav labels: {result['topNavLinks']!r}")
        if result["topNavTitle"] != "dotlineform studio" or result["topNavHomeHref"] != "/studio/":
            raise AssertionError(f"unexpected top nav home link: {result['topNavTitle']!r} {result['topNavHomeHref']!r}")
        if result["dataPath"] != "/studio/app/frontend/config/ui-text/catalogue-status.json":
            raise AssertionError(f"unexpected UI text path: {result['dataPath']!r}")
        if result["mediaThumbWorks"] != "/assets/works/img":
            raise AssertionError(f"unexpected thumb works path: {result['mediaThumbWorks']!r}")
        if result["pipelineThumbSuffix"] != "thumb":
            raise AssertionError(f"unexpected pipeline thumb suffix: {result['pipelineThumbSuffix']!r}")
        if result["url"] != expected_url:
            raise AssertionError(f"unexpected view URL: {result['url']!r}")
        if result["workEditorUrl"] != "/studio/catalogue-work/?work=00001&zero=0":
            raise AssertionError(f"unexpected work editor URL: {result['workEditorUrl']!r}")
        if result["publicWorkUrl"] != "http://127.0.0.1:4000/works/?work=00123&from=studio&zero=0":
            raise AssertionError(f"unexpected public work URL: {result['publicWorkUrl']!r}")
        if result["cataloguePublicWorkUrl"] != "http://127.0.0.1:4000/works/?from=studio&work=00123":
            raise AssertionError(f"unexpected catalogue public work URL: {result['cataloguePublicWorkUrl']!r}")
        if "Missing Studio site base" not in result["cataloguePublicMissingBaseError"]:
            raise AssertionError(f"catalogue public links did not fail closed without a public base: {result['cataloguePublicMissingBaseError']!r}")
        if result["liveWorkUrl"] != "https://dotlineform.com/works/?work=00123":
            raise AssertionError(f"unexpected live work URL: {result['liveWorkUrl']!r}")
        home_link_hrefs = {link["href"] for link in result["homeLinks"]}
        home_link_labels = [link["label"] for link in result["homeLinks"]]
        expected_home_hrefs = {
            "/studio/catalogue-status/",
            "/studio/catalogue-series/",
            "/studio/catalogue-work/",
            "/studio/bulk-add-work/",
            "/studio/catalogue-field-registry/",
            "/studio/studio-works/?sort=cat&dir=asc",
            "/studio/project-state/",
        }
        if expected_home_hrefs - home_link_hrefs:
            raise AssertionError(f"Studio home missing expected links: {result['homeLinks']!r}")
        if home_link_labels[:5] != ["drafts", "series editor", "work editor", "bulk add", "field registry"]:
            raise AssertionError(f"Studio home has unexpected first links: {result['homeLinks']!r}")
        if result["homeReady"] != "true":
            raise AssertionError(f"Studio home did not expose ready state: {result['homeReady']!r}")
        if console_errors:
            raise AssertionError(f"console errors: {console_errors}")
        print(f"local Studio navigation adapter OK: {base_url}/studio/")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
