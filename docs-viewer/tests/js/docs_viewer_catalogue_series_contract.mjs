import assert from "node:assert/strict";
import fs from "node:fs";
import { FakeDocument } from "./support/media-dom.mjs";
import { catalogueSeriesMediaPresentation, catalogueWorkThumbnail } from "../../runtime/js/shared/docs-viewer-catalogue-media.js";
import { normalizeDocsViewerMediaPresentation } from "../../runtime/js/shared/docs-viewer-media-presentation.js";
import { createDocsViewerMediaDetailAdapter } from "../../runtime/js/shared/docs-viewer-media-detail.js";
import { createDocsViewerManagementSourceAdapter } from "../../runtime/js/management/docs-viewer-management-source-adapter.js";
import { createDocsViewerConfiguredScopeProvider } from "../../runtime/js/shared/docs-viewer-configured-scope-provider.js";
import { resolveDocsViewerRouteConfig } from "../../runtime/js/shared/docs-viewer-route-config.js";
import { docsViewerMediaGalleryPage, docsViewerMediaGalleryPosition } from "../../runtime/js/shared/docs-viewer-media-gallery.js";

const raw = { header: { schema: "series_record_v5", series_id: "143" },
  series: { series_id: "143", title: "simultaneous equations", year_display: "2026" },
  member_works: [{ work_id: "01942", title: "se2" }, { work_id: "01941", title: "se1" }] };
const thumbnails = { base_url: "/catalogue/works/thumbs/", size: 96, suffix: "thumb", format: "webp" };
const project = (data = raw) => catalogueSeriesMediaPresentation(data, "143", thumbnails);
const projected = project();
const normalized = normalizeDocsViewerMediaPresentation(projected);
assert.deepEqual(normalized.gallery.members.map(m => m.target.id), ["01942", "01941"]);
assert.equal(normalized.gallery.members[0].thumbnail.src, "/catalogue/works/thumbs/01942-thumb-96.webp");
assert(normalized.gallery.members.every(m => m.work === null), "gallery entry requires no complete Work records");
assert.equal(Object.isFrozen(normalized.gallery.members[0].target), true);
assert.deepEqual(normalized.gallery.metadata, [{ label: "Year", value: "2026" }]);
assert.equal(Object.isFrozen(normalized.gallery.metadata[0]), true);
assert.throws(() => normalizeDocsViewerMediaPresentation({ ...projected, gallery: { ...projected.gallery, metadata: null } }), /metadata/);
assert.equal(normalizeDocsViewerMediaPresentation(project({ ...raw, member_works: [] })).gallery.members.length, 0);
assert.throws(() => project({ ...raw, series: { ...raw.series, series_id: "144" } }), /does not match/);
assert.throws(() => project({ ...raw, member_works: [raw.member_works[0], raw.member_works[0]] }), /duplicate Work/);
assert.throws(() => project({ ...raw, member_works: [{ work_id: "1942", title: "Invalid" }] }), /exact/);
for (const base_url of ["//evil.test/", "http://evil.test/", "/thumbs/?x=/"]) {
  assert.throws(() => catalogueWorkThumbnail("01942", "se2", { ...thumbnails, base_url }), /unsafe/);
}
assert.throws(() => catalogueWorkThumbnail("01942", "se2", { ...thumbnails, suffix: undefined }), /configuration/);

// Source/provider request agreement and public configuration use the same unchanged record.
const registry = JSON.parse(fs.readFileSync(new URL("../../config/routes/docs-viewer-routes.json", import.meta.url)));
const publicRegistry = JSON.parse(fs.readFileSync(new URL("../../../site/docs-viewer/config/routes/docs-viewer-public-routes.json", import.meta.url)));
const localRoute = resolveDocsViewerRouteConfig({ routeConfig: registry.routes.find(r => r.route_id === "docs-manage") });
const publicRoute = resolveDocsViewerRouteConfig({ routeConfig: publicRegistry.routes[0] });
const requests = [];
const source = createDocsViewerManagementSourceAdapter({ sourceService: { baseUrl: "http://127.0.0.1:9999" },
  window: { fetch: async (url, options) => { requests.push({ url, cache: options.cache }); return { ok: true, json: async () => raw }; } } });
const local = createDocsViewerConfiguredScopeProvider({ source, routeContext: { routeConfig: localRoute } });
const localSeries = await local.readCatalogueSeriesPresentation("143");
assert.deepEqual(requests, [{ url: "http://127.0.0.1:9999/docs/catalogue-series?series_id=143", cache: "no-store" }]);
assert.equal(localSeries.gallery.members[0].thumbnail.src, "/docs/catalogue-thumbnails/01942-thumb-96.webp");
requests.length = 0;
let response = raw;
let ok = true;
const publicProvider = createDocsViewerConfiguredScopeProvider({ routeContext: { routeConfig: publicRoute }, window: {
  fetch: async (url, options) => { requests.push({ url, cache: options.cache }); return { ok, status: ok ? 200 : 404, json: async () => response }; }
} });
const publicSeries = await publicProvider.readCatalogueSeriesPresentation("143");
assert.deepEqual(requests, [{ url: "/assets/data/catalogue/series/index/143.json", cache: "no-cache" }]);
assert.equal(publicSeries.gallery.members[0].thumbnail.src, "/assets/data/catalogue/works/thumbs/01942-thumb-96.webp");
ok = false;
await assert.rejects(publicProvider.readCatalogueSeriesPresentation("143"), /HTTP 404/);
ok = true;
response = { ...raw, series: { ...raw.series, series_id: "144" } };
await assert.rejects(publicProvider.readCatalogueSeriesPresentation("143"), /does not match/);
const beforeInvalid = requests.length;
await assert.rejects(publicProvider.readCatalogueSeriesPresentation("../143"), /exact/);
assert.equal(requests.length, beforeInvalid, "invalid identities do not cause a request");

// Real adapter contract: lazy Work reads, selected identity, retry, stale responses and release.
const doc = new FakeDocument();
const root = doc.createElement("article");
const marker = doc.createElement("span");
marker.setAttribute("data-docs-content-detail", "media");
marker.setAttribute("data-docs-media-kind", "catalogue-series");
marker.setAttribute("data-docs-media-id", "143");
const opener = doc.createElement("button");
opener.type = "button";
opener.setAttribute("type", "button");
opener.setAttribute("data-docs-media-open", "");
marker.appendChild(opener);
root.appendChild(marker);
const pending = [];
let seriesReads = 0;
let selected;
const adapter = createDocsViewerMediaDetailAdapter();
const mount = { content: root, viewerScope: "analysis", viewerStage: "working", doc: { doc_id: "document" }, documentMountGeneration: 1,
  collectionProvider: { readCatalogueSeriesPresentation: async () => { seriesReads += 1; return project(); },
    readCatalogueWork: id => new Promise((resolve, reject) => pending.push({ id, resolve, reject })) },
  requestContentDetail: target => { selected = target; return true; } };
assert.equal(adapter.mountDocument(mount).decorated, 1);
await opener.listeners.get("click")({ preventDefault() {} });
assert.equal(seriesReads, 1);
assert.equal(pending.length, 0);
const view = adapter.mountPresentation({ content: root, targetContext: selected });
assert.equal(view.root.querySelector(".docsViewer__mediaDetailPrevious").disabled, true, "one page has no previous page");
assert.equal(view.root.querySelector(".docsViewer__mediaDetailNext").disabled, true, "one page has no next page");
const work = id => ({ work: { work_id: id, title: id, width_px: 800, height_px: 600,
  media: { primary: [{ url: "https://media.example.test/" + id + ".webp", width: 800 }] } } });
const settle = async () => { for (let i = 0; i < 8; i += 1) await Promise.resolve(); };
const buttons = () => view.root.querySelectorAll(".docsViewer__mediaDetailThumbnail");
buttons()[0].dispatchClick();
await settle();
assert.deepEqual(pending.map(p => p.id), ["01942"]);
buttons()[1].dispatchClick();
await settle();
pending[1].resolve(work("01941"));
await settle();
assert.equal(view.root.getAttribute("data-docs-media-id"), "01941");
pending[0].resolve(work("01942"));
await settle();
assert.equal(view.root.getAttribute("data-docs-media-id"), "01941", "earlier selection cannot replace the selected Work");
view.root.querySelector(".docsViewer__mediaDetailSeriesLink").dispatchClick();
assert.equal(view.root.getAttribute("data-docs-media-id"), "143");
buttons()[0].dispatchClick();
await settle();
pending[2].reject(new Error("missing Work"));
await settle();
assert.equal(view.root.getAttribute("data-docs-media-id"), "143", "failed read retains the gallery");
const feedback = view.root.children[1];
assert.equal(feedback.hidden, false);
feedback.children[0].dispatchClick();
await settle();
assert.equal(pending[3].id, "01942");
pending[3].resolve(work("01942"));
await settle();
assert.equal(view.root.getAttribute("data-docs-media-id"), "01942");
view.root.querySelector(".docsViewer__mediaDetailSeriesLink").dispatchClick();
buttons()[0].dispatchClick();
await settle();
adapter.releaseDocument({ content: root });
pending[4].resolve(work("01942"));
await settle();
assert.equal(view.root.children[0].children.length, 0, "released views ignore completed reads");

// Empty Series opens its own gallery and makes no Work request.
adapter.mountDocument({ ...mount, documentMountGeneration: 2,
  collectionProvider: { readCatalogueSeriesPresentation: async () => project({ ...raw, member_works: [] }) } });
await opener.listeners.get("click")({ preventDefault() {} });
const empty = adapter.mountPresentation({ content: root, targetContext: selected });
assert.equal(empty.root.getAttribute("data-docs-media-id"), "143");
assert.equal(empty.root.querySelectorAll(".docsViewer__mediaDetailThumbnail").length, 0);
adapter.releaseDocument({ content: root });

// Page membership and neighbour targets preserve the complete supplied order, including a partial last page.
const largeRaw = { ...raw, member_works: Array.from({ length: 165 }, (_, index) => ({
  work_id: String(165 - index).padStart(5, "0"), title: "Work " + index
})) };
const largeGallery = normalizeDocsViewerMediaPresentation(project(largeRaw)).gallery;
const pages = [0, 1, 2, 3].map(index => docsViewerMediaGalleryPage(largeGallery, index));
assert.deepEqual(pages.map(page => page.members.length), [48, 48, 48, 21]);
assert.deepEqual(pages.flatMap(page => page.members.map(member => member.target.id)), largeRaw.member_works.map(work => work.work_id));
assert.equal(docsViewerMediaGalleryPage(largeGallery, -1).pageIndex, 3);
assert.equal(docsViewerMediaGalleryPage(largeGallery, 4).pageIndex, 0);
assert.equal(docsViewerMediaGalleryPage(largeGallery, 99).end, 165);
assert.equal(docsViewerMediaGalleryPage({ members: [] }).pageCount, 0);
assert.equal(docsViewerMediaGalleryPage({ members: [] }, -1).pageIndex, 0);
const singleGallery = { members: [largeGallery.members[0]] };
assert.equal(docsViewerMediaGalleryPage(singleGallery, -1).pageIndex, 0);
assert.equal(docsViewerMediaGalleryPage(singleGallery, 1).members.length, 1);
assert.throws(() => docsViewerMediaGalleryPage(largeGallery, 1.5), /integer/);
const at = index => largeGallery.members[index].target;
assert.equal(docsViewerMediaGalleryPosition(largeGallery, at(0)).previous, at(164));
assert.equal(docsViewerMediaGalleryPosition(largeGallery, at(164)).next, at(0));
assert.equal(docsViewerMediaGalleryPosition(singleGallery, at(0)).previous, null);
assert.equal(docsViewerMediaGalleryPosition(singleGallery, at(0)).next, null);
assert.equal(docsViewerMediaGalleryPosition(largeGallery, at(47)).next, at(48));
assert.equal(docsViewerMediaGalleryPosition(largeGallery, at(48)).pageIndex, 1);
assert.equal(docsViewerMediaGalleryPosition(largeGallery, at(48)).previous, at(47));
assert.equal(docsViewerMediaGalleryPosition(largeGallery, { kind: "catalogue-work", id: "99999" }), null);

// Adapter integration renders only the active page and reads only explicitly selected Works.
const workRequests = [];
adapter.mountDocument({ ...mount, documentMountGeneration: 3,
  collectionProvider: { readCatalogueSeriesPresentation: async () => project(largeRaw),
    readCatalogueWork: id => new Promise((resolve, reject) => workRequests.push({ id, resolve, reject })) } });
await opener.listeners.get("click")({ preventDefault() {} });
const largeView = adapter.mountPresentation({ content: root, targetContext: selected });
const thumbnailsInView = () => largeView.root.querySelectorAll(".docsViewer__mediaDetailThumbnail");
const imageSources = () => largeView.root.querySelectorAll(".docsViewer__mediaDetailThumbnailImage").map(image => image.src);
const expectedSources = page => docsViewerMediaGalleryPage(largeGallery, page).members.map(member => member.thumbnail.src);
const next = () => largeView.root.querySelector(".docsViewer__mediaDetailNext").dispatchClick();
const previous = () => largeView.root.querySelector(".docsViewer__mediaDetailPrevious").dispatchClick();
const returnToSeries = () => largeView.root.querySelector(".docsViewer__mediaDetailSeriesLink").dispatchClick();
const resolveWork = async index => { workRequests[index].resolve(work(workRequests[index].id)); await settle(); };
assert.deepEqual(imageSources(), expectedSources(0));
assert.equal(largeView.root.querySelectorAll("img").length, 48);
assert.equal(workRequests.length, 0);
previous();
assert.deepEqual(imageSources(), expectedSources(3));
assert.equal(largeView.root.querySelectorAll("img").length, 21);
next();
assert.deepEqual(imageSources(), expectedSources(0), "page next wraps from last to first");
previous();
assert.equal(workRequests.length, 0, "page changes request no Work records");
previous(); previous();
thumbnailsInView()[47].dispatchClick();
await settle();
assert.equal(workRequests[0].id, at(95).id);
await resolveWork(0);
assert.equal(largeView.root.getAttribute("data-docs-media-id"), at(95).id);
assert.equal(largeView.root.querySelectorAll("img").length, 1);
next();
await settle();
assert.equal(workRequests[1].id, at(96).id, "Work next crosses the gallery page boundary");
workRequests[1].reject(new Error("Unavailable next Work"));
await settle();
assert.equal(largeView.root.getAttribute("data-docs-media-id"), at(95).id);
returnToSeries();
assert.deepEqual(imageSources(), expectedSources(1), "failure preserves the current Work's return page");
thumbnailsInView()[47].dispatchClick();
await settle();
await resolveWork(2);
next();
await settle();
await resolveWork(3);
assert.equal(largeView.root.getAttribute("data-docs-media-id"), at(96).id);
returnToSeries();
assert.deepEqual(imageSources(), expectedSources(2), "return shows the page containing the successfully selected Work");
thumbnailsInView()[0].dispatchClick();
await settle();
previous();
await resolveWork(4);
assert.equal(largeView.root.getAttribute("data-docs-media-kind"), "catalogue-series");
assert.deepEqual(imageSources(), expectedSources(1), "page navigation supersedes a pending Work read");
assert.equal(workRequests.length, 5, "only explicit selection and Work navigation read Work records");
previous();
thumbnailsInView()[0].dispatchClick();
await settle();
await resolveWork(5);
previous();
await settle();
assert.equal(workRequests[6].id, at(164).id, "Work previous wraps from first to last");
await resolveWork(6);
assert.equal(largeView.root.getAttribute("data-docs-media-id"), at(164).id);
returnToSeries();
assert.deepEqual(imageSources(), expectedSources(3), "wrapped last Work returns to the last gallery page");
thumbnailsInView()[20].dispatchClick();
await settle();
await resolveWork(7);
next();
await settle();
assert.equal(workRequests[8].id, at(0).id, "Work next wraps from last to first");
await resolveWork(8);
assert.equal(largeView.root.getAttribute("data-docs-media-id"), at(0).id);
returnToSeries();
assert.deepEqual(imageSources(), expectedSources(0), "wrapped first Work returns to the first gallery page");
assert.equal(workRequests.length, 9, "wrapping reads only the explicitly selected Work");
adapter.releaseDocument({ content: root });
console.log("Catalogue Series projection, page/sequence, bounded reads and selection lifetime contracts passed");
