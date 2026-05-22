#!/usr/bin/env python3
"""Smoke-check the local Studio config/navigation adapter."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.studio.studio_app_server import StudioAppServer  # noqa: E402


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
            result = page.evaluate(
                """async () => {
                    const mod = await import("/assets/studio/js/studio-navigation.js");
                    const configMod = await import("/assets/studio/js/studio-config.js");
                    const config = await (await fetch("/studio/runtime-config.json")).json();
                    const url = mod.buildStudioViewUrl(config, "tag-groups", {
                        scope: "studio",
                        empty: "",
                        zero: 0
                    });
                    const workEditorUrl = configMod.buildStudioRouteUrl(config, "catalogue_work_editor", {
                        work: "00001",
                        empty: "",
                        zero: 0
                    });
                    const newDetailUrl = configMod.buildStudioRouteUrl(config, "catalogue_work_detail_editor", {
                        work: "00001",
                        mode: "new"
                    });
                    const publicWorkUrl = mod.buildPublicSiteUrl(config, "/works/00123/", {
                        from: "studio",
                        empty: "",
                        zero: 0
                    });
                    const liveWorkUrl = mod.buildPublicSiteUrl(config, "/works/00123/", {}, { site: "production" });
                    const initial = mod.readStudioInitialState(
                        "/docs/?scope=studio&doc=docs-viewer&modal=delete&modal.doc_id=docs-viewer&return_view=docs&return.scope=studio"
                    );
                    const store = new Map();
                    const storage = {
                        getItem: (key) => store.has(key) ? store.get(key) : null,
                        setItem: (key, value) => store.set(key, value),
                        removeItem: (key) => store.delete(key)
                    };
                    const returnContext = mod.createReturnContext("docs", { scope: "studio" }, { label: "Docs" });
                    mod.storeReturnContext(returnContext, { storage });
                    const storedContext = mod.readReturnContext({ storage });
                    const consumedContext = mod.consumeReturnContext({ storage });
                    const consumedAgain = mod.readReturnContext({ storage });

                    let openModalDetail = null;
                    document.addEventListener(mod.STUDIO_MODAL_EVENT, (event) => {
                        openModalDetail = event.detail;
                    }, { once: true });
                    const modalEvent = mod.openModal("Confirm Delete", { doc_id: "docs-viewer" });
                    const homeLinks = [...document.querySelectorAll(".studioLinkList__item")].map((link) => ({
                        viewId: link.getAttribute("data-studio-navigate"),
                        href: link.getAttribute("href")
                    }));
                    const homeReady = document.querySelector("#studioHomeRoot")?.getAttribute("data-studio-ready");

                    let delegatedModalDetail = null;
                    document.addEventListener(mod.STUDIO_MODAL_EVENT, (event) => {
                        delegatedModalDetail = event.detail;
                    }, { once: true });
                    const button = document.createElement("button");
                    button.type = "button";
                    button.setAttribute("data-studio-modal", "rename");
                    button.setAttribute("data-studio-params", JSON.stringify({ doc_id: "docs-viewer" }));
                    document.body.append(button);
                    button.click();

                    return {
                        serviceBase: mod.getStudioServices(config).docs.base,
                        publicPreviewBase: mod.getStudioSiteBase(config, "public_preview"),
                        productionBase: mod.getStudioSiteBase(config, "production"),
                        docsView: mod.getStudioView(config, "docs").path,
                        dataPath: config.app.runtime.data_paths.ui_text.tag_groups,
                        mediaThumbWorks: config.app.runtime.media.thumbs.works,
                        pipelineThumbSuffix: config.app.runtime.pipeline.variants.thumb.suffix,
                        stateStorageKey: config.app.runtime.state.return_context_storage_key,
                        modalEventName: config.app.runtime.modals.event,
                        url,
                        workEditorUrl,
                        newDetailUrl,
                        publicWorkUrl,
                        liveWorkUrl,
                        initial,
                        storedContext,
                        consumedContext,
                        consumedAgain,
                        openModalDetail,
                        modalDefaultPrevented: modalEvent.defaultPrevented,
                        homeLinks,
                        homeReady,
                        delegatedModalDetail
                    };
                }"""
            )
            browser.close()

        expected_url = "/studio/analytics/tag-groups/?scope=studio&zero=0"
        if result["serviceBase"] != "/studio/api/docs":
            raise AssertionError(f"unexpected Docs service base: {result['serviceBase']!r}")
        if result["publicPreviewBase"] != "http://127.0.0.1:4000":
            raise AssertionError(f"unexpected public preview base: {result['publicPreviewBase']!r}")
        if result["productionBase"] != "https://dotlineform.com":
            raise AssertionError(f"unexpected production base: {result['productionBase']!r}")
        if result["docsView"] != "/docs/?mode=manage":
            raise AssertionError(f"unexpected Docs view path: {result['docsView']!r}")
        if result["dataPath"] != "/assets/studio/data/ui_text/tag-groups.json":
            raise AssertionError(f"unexpected UI text path: {result['dataPath']!r}")
        if result["mediaThumbWorks"] != "/assets/works/img":
            raise AssertionError(f"unexpected thumb works path: {result['mediaThumbWorks']!r}")
        if result["pipelineThumbSuffix"] != "thumb":
            raise AssertionError(f"unexpected pipeline thumb suffix: {result['pipelineThumbSuffix']!r}")
        if result["stateStorageKey"] != "dlf.studio.returnContext":
            raise AssertionError(f"unexpected return context key: {result['stateStorageKey']!r}")
        if result["modalEventName"] != "studio:open-modal":
            raise AssertionError(f"unexpected modal event name: {result['modalEventName']!r}")
        if result["url"] != expected_url:
            raise AssertionError(f"unexpected view URL: {result['url']!r}")
        if result["workEditorUrl"] != "/studio/catalogue-work/?mode=manage&work=00001&zero=0":
            raise AssertionError(f"unexpected work editor URL: {result['workEditorUrl']!r}")
        if result["newDetailUrl"] != "/studio/catalogue-work-detail/?mode=new&work=00001":
            raise AssertionError(f"unexpected new detail URL: {result['newDetailUrl']!r}")
        if result["publicWorkUrl"] != "http://127.0.0.1:4000/works/00123/?from=studio&zero=0":
            raise AssertionError(f"unexpected public work URL: {result['publicWorkUrl']!r}")
        if result["liveWorkUrl"] != "https://dotlineform.com/works/00123/":
            raise AssertionError(f"unexpected live work URL: {result['liveWorkUrl']!r}")
        if result["initial"]["viewId"] != "docs":
            raise AssertionError(f"unexpected initial view: {result['initial']!r}")
        if result["initial"]["modal"]["params"]["doc_id"] != "docs-viewer":
            raise AssertionError(f"unexpected modal params: {result['initial']!r}")
        if result["initial"]["returnContext"]["params"]["scope"] != "studio":
            raise AssertionError(f"unexpected return context params: {result['initial']!r}")
        if result["storedContext"]["viewId"] != "docs" or result["storedContext"]["params"]["scope"] != "studio":
            raise AssertionError(f"unexpected stored return context: {result['storedContext']!r}")
        if result["consumedContext"]["viewId"] != "docs" or result["consumedAgain"] is not None:
            raise AssertionError("return context was not consumed correctly")
        if result["openModalDetail"]["name"] != "confirm-delete":
            raise AssertionError(f"unexpected openModal detail: {result['openModalDetail']!r}")
        if result["modalDefaultPrevented"]:
            raise AssertionError("openModal event was unexpectedly prevented")
        home_link_ids = {link["viewId"] for link in result["homeLinks"]}
        if "series_tag_editor" in home_link_ids:
            raise AssertionError(f"Studio home exposed hidden editor link: {result['homeLinks']!r}")
        if {"docs", "tag_groups", "activity"} - home_link_ids:
            raise AssertionError(f"Studio home missing expected links: {result['homeLinks']!r}")
        if result["homeReady"] != "true":
            raise AssertionError(f"Studio home did not expose ready state: {result['homeReady']!r}")
        if result["delegatedModalDetail"]["name"] != "rename":
            raise AssertionError(f"unexpected delegated modal detail: {result['delegatedModalDetail']!r}")
        if result["delegatedModalDetail"]["params"]["doc_id"] != "docs-viewer":
            raise AssertionError(f"unexpected delegated modal params: {result['delegatedModalDetail']!r}")
        if console_errors:
            raise AssertionError(f"console errors: {console_errors}")
        print(f"local Studio navigation adapter OK: {base_url}/studio/")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
