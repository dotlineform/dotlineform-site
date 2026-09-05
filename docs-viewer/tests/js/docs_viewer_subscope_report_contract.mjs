import assert from "node:assert/strict";
import { mountDocsViewerReport } from "../../runtime/js/reports/docs-viewer-reports.js";
import { filterSeriesWorks, readSeriesWorksRows, readSeriesWorkPresentation } from "../../runtime/js/reports/series-works-report.js";

// Minimal document surface for the loader/child ownership boundary, not layout.
class Element {
  constructor(tag, ownerDocument) {
    this.tagName = tag.toUpperCase();
    this.ownerDocument = ownerDocument;
    this.children = [];
    this.dataset = {};
    this.attributes = new Map();
    this.listeners = new Map();
    this.className = "";
    this.value = "";
  }
  get childNodes() { return this.children; }
  get firstChild() { return this.children[0] || null; }
  get isConnected() { return Boolean(this.connected || this.parentNode?.isConnected); }
  set innerHTML(value) {
    this.replaceChildren();
    if (value.includes("data-docs-viewer-report-host")) {
      const host = this.ownerDocument.createElement("section");
      host.setAttribute("data-docs-viewer-report-host", "");
      this.appendChild(host);
    }
  }
  setAttribute(key, value) { this.attributes.set(key, String(value)); }
  getAttribute(key) { return this.attributes.get(key) ?? null; }
  removeAttribute(key) { this.attributes.delete(key); }
  appendChild(child) { child.remove(); this.children.push(child); child.parentNode = this; return child; }
  append(...children) { children.forEach(child => this.appendChild(child)); }
  removeChild(child) { this.children.splice(this.children.indexOf(child), 1); child.parentNode = null; }
  remove() { if (this.parentNode) this.parentNode.removeChild(this); }
  replaceChildren(...children) { [...this.children].forEach(child => child.remove()); this.append(...children); }
  contains(node) { return node === this || this.children.some(child => child.contains(node)); }
  addEventListener(type, callback) { this.listeners.set(type, callback); }
  querySelectorAll(selector) {
    const matches = node => selector.startsWith("[")
      ? node.attributes.has(selector.slice(1, -1))
      : selector.startsWith(".")
        ? node.className.split(" ").includes(selector.slice(1))
        : node.tagName.toLowerCase() === selector;
    return this.children.flatMap(child => [...(matches(child) ? [child] : []), ...child.querySelectorAll(selector)]);
  }
  querySelector(selector) { return this.querySelectorAll(selector)[0] || null; }
}

const parentId = "d-20260905-000000-000001";
const firstId = "d-20260905-000000-000002";
const secondId = "d-20260905-000000-000003";
globalThis.window = {
  location: new URL(`http://example.test/docs/?scope=analysis&doc=${parentId}&subdoc=${firstId}`),
  history: {
    state: {},
    pushState(state, _, url) { this.state = state; window.location = new URL(url, window.location); }
  }
};
const documentRef = {
  defaultView: window,
  querySelector() { return null; },
  createElement(tag) { return new Element(tag, this); }
};
globalThis.document = documentRef;
const content = documentRef.createElement("article");
content.connected = true;
content.innerHTML = '<section data-docs-viewer-report-host></section>';

const rows = [{ work_id: "01941", title: "se1", year_display: "2026" }];
assert.deepEqual(filterSeriesWorks(rows, "2026"), rows);
assert.deepEqual(filterSeriesWorks(rows, "SE1"), rows);
assert.deepEqual(filterSeriesWorks(rows, "01942"), []);
assert.throws(() => readSeriesWorksRows({
  schema: "docs_series_works_report_v1", target: { scope: "analysis", doc_id: firstId }, works: rows
}, { scope: "analysis", sub_scope: "works", doc_id: firstId }), /does not match/);

function deferred() {
  let resolve;
  const promise = new Promise(complete => { resolve = complete; });
  return { promise, resolve };
}
const firstRead = deferred();
const secondRead = deferred();
const pendingFirst = deferred();
const requests = [];
const mediaRequests = [];
const mediaReads = [];
const mediaOpened = [];
const reportService = {
  readSeriesWorkMedia(request) {
    mediaRequests.push(request);
    const read = deferred();
    mediaReads.push(read);
    return read.promise;
  },
  readSeriesWorks({ target }) {
    requests.push(target);
    if (target.doc_id === firstId) {
      firstRead.resolve();
      return pendingFirst.promise;
    }
    secondRead.resolve();
    return Promise.resolve(response(target));
  }
};
function response(target) {
  return { schema: "docs_series_works_report_v1", target, series_id: "143", title: "Series", works: rows };
}
globalThis.fetch = async function (url) {
  const pathname = new URL(url, window.location).pathname;
  let payload;
  if (pathname === "/reports.json") {
    payload = { reports: [
      { report_id: "docs_subscope", default_access: "public", presets: [] },
      { report_id: "series_works", default_access: "local", presets: [] }
    ] };
  } else if (pathname === "/manifest.json") {
    payload = { docs: [{ doc_id: firstId, title: "First" }, { doc_id: secondId, title: "Second" }] };
  } else {
    const docId = pathname.slice("/children/".length, -".json".length);
    assert.ok([firstId, secondId].includes(docId), pathname);
    payload = { doc_id: docId, title: docId, report: { id: "series_works", access: "local" },
      content_html: '<section data-docs-viewer-report-host></section>' };
  }
  return { ok: true, json: async () => payload };
};

const mounted = mountDocsViewerReport({
  appContext: { kind: "manage" }, managementContext: true, managementService: {},
  content, doc: { doc_id: parentId }, viewerScope: "analysis",
  payload: { report: { id: "docs_subscope", access: "public", sub_scope: "works" } },
  reportRegistryUrl: "/reports.json", reportService,
  openMediaPresentation(request) { mediaOpened.push(request); return true; },
  subscopeReportContributionPromise: null,
  scopeConfigs: [{ scopeId: "analysis", subScopes: [{ subScope: "works", title: "Works",
    manifestUrl: "/manifest.json", byIdUrlBase: "/children" }] }]
});
await Promise.race([
  firstRead.promise,
  mounted.then(() => {
    const notes = content.querySelectorAll("p").map(node => node.textContent).join("; ");
    throw new Error("Parent mount ended before the child data request: " + notes);
  })
]);
assert.deepEqual(requests[0], { scope: "analysis", sub_scope: "works", doc_id: firstId });
const firstBody = content.querySelector("tbody");
assert.ok(firstBody);
content.querySelector(".docsReportDetail__back").listeners.get("click")();
const secondButton = content.querySelectorAll(".docsViewerReport__subscopeButton")[1];
assert.ok(secondButton);
secondButton.listeners.get("click")();
await secondRead.promise;
assert.deepEqual(requests[1], { scope: "analysis", sub_scope: "works", doc_id: secondId });
pendingFirst.resolve(response(requests[0]));
await mounted;
assert.equal(firstBody.children.length, 0, "late response must not fill the replaced child");
const currentBody = content.querySelector("tbody");
assert.notEqual(currentBody, firstBody);
assert.equal(currentBody.children.length, 1);
assert.deepEqual(currentBody.children[0].children.map(cell => cell.textContent || cell.firstChild?.textContent), ["01941", "se1", "2026"]);
assert.equal(mediaRequests.length, 0, "rendering rows must not fetch any Work media");
const titleLink = currentBody.querySelector(".docsViewerReport__workTitleLink");
const firstMedia = titleLink.listeners.get("click")();
assert.deepEqual(mediaRequests[0], { target: requests[1], workId: "01941" });
const mediaPayload = { target: requests[1], presentation: { target: { kind: "catalogue-work", id: "01941" } } };
assert.throws(() => readSeriesWorkPresentation(mediaPayload, requests[1], "01942"), /does not match/);
mediaReads[0].resolve(mediaPayload);
await firstMedia;
assert.equal(mediaOpened.length, 1);
assert.deepEqual(mediaOpened[0].documentTarget, { scope: "analysis", subScope: "works", docId: secondId });
assert.equal(mediaOpened[0].invocationControl, titleLink);
const lateMedia = titleLink.listeners.get("click")();
const filter = currentBody.parentNode.parentNode.parentNode.querySelector("input");
filter.value = "2026";
filter.listeners.get("input")();
mediaReads[1].resolve(mediaPayload);
await lateMedia;
assert.equal(mediaOpened.length, 1, "a replaced row must not open late media");
const currentTitle = content.querySelector(".docsViewerReport__workTitleLink");
const afterNavigation = currentTitle.listeners.get("click")();
content.querySelector(".docsReportDetail__back").listeners.get("click")();
mediaReads[2].resolve(mediaPayload);
await afterNavigation;
assert.equal(mediaOpened.length, 1, "a departed child must not open late media");
console.log("Sub-scope report contract passed: exact child targets, on-demand Work media, late-response isolation.");
