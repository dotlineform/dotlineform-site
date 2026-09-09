import assert from "node:assert/strict";
import fs from "node:fs";
import { parseCatalogueToken, parseCatalogueTokens, serializeCatalogueToken } from "../../runtime/js/management/source-editor/catalogue-token-parser.js";
import { normalizeSemanticTokenRegistry } from "../../runtime/js/management/source-editor/semantic-token-registry.js";
import { catalogueMediaLinkLabel, readCatalogueMediaPresentation, loadCatalogueMediaSupport, catalogueMediaLinkControlDefinition } from "../../runtime/js/management/source-editor/catalogue-media-link.js";
import { createDocsViewerManagementSourceAdapter } from "../../runtime/js/management/docs-viewer-management-source-adapter.js";
import { createDocsViewerConfiguredScopeProvider } from "../../runtime/js/shared/docs-viewer-configured-scope-provider.js";
import { collectSemanticTokenTargetMatches } from "../../runtime/js/management/source-editor/semantic-token-targets.js";
import { catalogueMediaTarget, catalogueWorkDetails, catalogueWorkMediaPresentation } from "../../runtime/js/shared/docs-viewer-catalogue-media.js";
import { createDocsViewerMediaDetailAdapter } from "../../runtime/js/shared/docs-viewer-media-detail.js";
import { resolveDocsViewerRouteConfig } from "../../runtime/js/shared/docs-viewer-route-config.js";

const registryPayload = JSON.parse(fs.readFileSync(new URL("../../config/semantic-tokens/registry.json", import.meta.url)));
const registry = normalizeSemanticTokenRegistry(registryPayload);
const title = "A *label* | ] \\ end";
const token = serializeCatalogueToken({ presentation: "media", targetType: "work", targetId: "00523", title });
const parsed = parseCatalogueToken(token, { registry });
assert.equal(parsed.presentation, "media");
assert.equal(parsed.targetId, "00523");
assert.equal(parsed.title, title);
assert.equal(serializeCatalogueToken(parsed), token, "editing preserves the media form");
assert.equal(parseCatalogueToken("[[catalogue:work:00523|old]]", { registry }).presentation, "text");
for (const raw of ["[[catalogue:media:work:523|bad]]", "[[catalogue:media:series:143|bad]]"]) {
  assert.equal(parseCatalogueToken(raw, { registry }), null);
}
assert.equal(parseCatalogueTokens("`" + token + "`\n\n```text\n" + token + "\n```", { registry }).length, 0);
const first = { targetId: "00523", title: "First" };
const second = { targetId: "00524", title: "Second" };
assert.equal(catalogueMediaLinkLabel(first, "selected words", null), "selected words");
assert.equal(catalogueMediaLinkLabel(first, "", null), "First");
assert.equal(catalogueMediaLinkLabel(second, "First", first), "Second");
assert.equal(catalogueMediaLinkLabel(second, "edited label", first), "edited label");
assert.equal(catalogueMediaLinkLabel(second, "First", first, true), "First", "selected text remains authored even when it matches a Work title");

const requests = [];
const payload = { ok: true, schema_version: "docs_semantic_token_target_lookup_v2", targets: [
  { family: "catalogue", target_type: "work", target_id: "00523", title: "First", meta: ["2023"] }
] };
const workPayload = { work: { work_id: "00523", title: "First", width_px: 800, height_px: 600,
  height_cm: 45, width_cm: 80, media: { primary: [{ url: "https://media.example.test/image.webp", width: 800 }] } } };
const source = createDocsViewerManagementSourceAdapter({
  sourceService: { baseUrl: "http://127.0.0.1:9999" }, viewerScope: "analysis", viewerStage: "working",
  window: { fetch: async (url, options) => {
    requests.push(url);
    if (url.includes("catalogue-work?")) assert.equal(options.cache, "no-store");
    return { ok: true, json: async () => url.includes("catalogue-media-targets") ? payload : structuredClone(workPayload) };
  } }
});
const provider = createDocsViewerConfiguredScopeProvider({ source });
const support = await loadCatalogueMediaSupport(provider, { fetch: async () => ({ ok: true, json: async () => registryPayload }) });
assert.equal(collectSemanticTokenTargetMatches(support.targets, "00523", support.registry, 20)[0].title, "First");
assert.equal((await readCatalogueMediaPresentation(provider, "00523")).target.id, "00523");
assert.deepEqual(requests, ["http://127.0.0.1:9999/docs/catalogue-media-targets", "http://127.0.0.1:9999/docs/catalogue-work?work_id=00523"]);
assert.equal(createDocsViewerConfiguredScopeProvider({}).readCatalogueMediaTargets, undefined, "public provider has no local Catalogue reads");
await assert.rejects(readCatalogueMediaPresentation(provider, "00524"), /does not match/);
assert.deepEqual(catalogueMediaLinkControlDefinition().appKinds, ["manage"]);
console.log("Catalogue Media View source and provider contracts passed");

// Public records are revalidated independently of document payloads and local APIs.
const publicRegistry = JSON.parse(fs.readFileSync(new URL("../../../site/docs-viewer/config/routes/docs-viewer-public-routes.json", import.meta.url)));
const routeConfig = resolveDocsViewerRouteConfig({ routeConfig: publicRegistry.routes[0] });
assert.equal(routeConfig.catalogueWorkRecordsBaseUrl, "/assets/data/catalogue/works/index/");
const publicRequests = [];
let currentWork = structuredClone(workPayload);
let responseStatus = 200;
const publicProvider = createDocsViewerConfiguredScopeProvider({ routeContext: { routeConfig }, window: {
  fetch: async (url, options) => {
    publicRequests.push(url);
    assert.equal(options.cache, "no-cache");
    return { ok: responseStatus === 200, status: responseStatus, json: async () => structuredClone(currentWork) };
  }
} });
assert.equal(publicProvider.readCatalogueMediaTargets, undefined);
assert.equal((await readCatalogueMediaPresentation(publicProvider, "00523")).label, "First");
currentWork.work.title = "Current title";
currentWork.work.media.primary[0].url = "https://media.example.test/replaced.webp?v=3";
const fresh = await readCatalogueMediaPresentation(publicProvider, "00523");
assert.equal(fresh.label, "Current title");
assert.equal(fresh.image.src, currentWork.work.media.primary[0].url);
assert.deepEqual(publicRequests, Array(2).fill("/assets/data/catalogue/works/index/00523.json"));
responseStatus = 404;
await assert.rejects(publicProvider.readCatalogueWork("00523"), /HTTP 404/);
responseStatus = 200;
assert.equal((await publicProvider.readCatalogueWork("00523")).work.title, "Current title");
await assert.rejects(publicProvider.readCatalogueWork("523"), /exact/);
for (const url of ["//evil.test/x", "javascript:alert(1)", "https://user:pass@example.test/x", "http://example.test/x", "https://safe.test\\@evil.test/x"]) {
  const unsafe = structuredClone(workPayload);
  unsafe.work.media.primary[0].url = url;
  assert.throws(() => catalogueWorkMediaPresentation(unsafe, "00523"), /unsafe/);
}

// Late reads cannot reopen a replaced document or supersede a newer activation.
const adapter = createDocsViewerMediaDetailAdapter();
const control = {};
const root = { querySelectorAll: () => [], contains: (node) => node === control };
const pending = [];
const opened = [];
let childCurrent = true;
const mount = {
  content: root, viewerScope: "analysis", viewerStage: "working", doc: { doc_id: "parent" }, documentMountGeneration: 1,
  collectionProvider: { readCatalogueWork: () => new Promise((resolve, reject) => pending.push({ resolve, reject })) },
  requestContentDetail: (target) => { opened.push(target); return true; }
};
adapter.mountDocument(mount);
const request = { content: root, documentMountGeneration: 1, invocationControl: control,
  mediaTarget: { kind: "catalogue-work", id: "00523" },
  documentTarget: { scope: "analysis", stage: "working", subScope: "works", docId: "child" },
  isCurrentDocument: () => childCurrent };
const firstRead = adapter.openTarget(request);
const newerRead = adapter.openTarget(request);
await Promise.resolve();
assert.equal(pending.length, 1, "simultaneous entries share just the in-flight Work read");
pending[0].resolve(currentWork);
assert.equal(await newerRead, true);
assert.equal(await firstRead, false);
assert.equal(opened.length, 1);
assert.deepEqual(opened[0].documentTarget, request.documentTarget);
const childRead = adapter.openTarget(request);
await Promise.resolve();
childCurrent = false;
pending[1].resolve(workPayload);
assert.equal(await childRead, false);
childCurrent = true;
const navigationRead = adapter.openTarget(request);
await Promise.resolve();
adapter.releaseDocument({ content: root });
pending[2].reject(new Error("late failure"));
assert.equal(await navigationRead, false);
assert.equal(opened.length, 1);
console.log("Current Catalogue loading, public isolation and stale-response contracts passed");

const detail = { work_id: "00523", detail_id: "015", detail_uid: "00523-015", title: "The exact Detail",
  width_px: 600, height_px: 600, media: { primary: [{ width: 800, url: "https://media.example.test/detail-15.webp?v=4" }] } };
const detailPayload = { work: { ...workPayload.work, media: {} }, sections: [{ details: [detail] }] };
assert.equal(catalogueWorkDetails(detailPayload, "00523")[0], detail);
const detailPresentation = catalogueWorkMediaPresentation(detailPayload, "00523", "015");
assert.deepEqual(detailPresentation.target, { kind: "catalogue-work-detail", id: "00523-015", workId: "00523" });
assert.equal(detailPresentation.image.src, detail.media.primary[0].url);
assert.equal(detailPresentation.label, detail.title);
assert.equal(detailPresentation.metadata.some((item) => item.label === "Dimensions"), false, "parent physical dimensions are not Detail dimensions");
assert.throws(() => catalogueWorkMediaPresentation(detailPayload, "00523"), /unavailable/);
assert.throws(() => catalogueWorkMediaPresentation(detailPayload, "00523", "016"), /unavailable/);
assert.throws(() => catalogueMediaTarget("00523", "15"), /exact/);
const duplicate = structuredClone(detailPayload);
duplicate.sections[0].details.push(detail);
assert.throws(() => catalogueWorkDetails(duplicate, "00523"), /mismatched/);
const wrongParent = structuredClone(detailPayload);
wrongParent.sections[0].details[0].work_id = "00524";
assert.throws(() => catalogueWorkDetails(wrongParent, "00523"), /mismatched/);
currentWork = detailPayload;
assert.equal((await publicProvider.readCatalogueWork("00523")).sections[0].details[0].detail_uid, "00523-015", "public raw reads permit Details without a Work primary");
assert.equal((await readCatalogueMediaPresentation(publicProvider, "00523", "015")).target.workId, "00523");
console.log("Exact generated Detail selection and public reader contracts passed");
