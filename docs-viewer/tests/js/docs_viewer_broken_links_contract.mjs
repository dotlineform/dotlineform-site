import assert from "node:assert/strict";
import {
  brokenLinksReportSelection,
  mountDocsBrokenLinksReport
} from "../../runtime/js/reports/docs-broken-links-report.js";
import { createDocsViewerReportService } from "../../runtime/js/reports/docs-viewer-report-service.js";

const scopeConfigs = ["studio", "analysis", "notes", "app"].map((scopeId) => ({ scopeId }));
const studio = { viewerScope: "studio", scopeConfigs };
const analysis = { viewerScope: "analysis", viewerStage: "working", scopeConfigs };
assert.deepEqual(brokenLinksReportSelection(studio, "analysis").scopes.map((item) => item.scopeId), ["studio", "notes", "app"]);
assert.equal(brokenLinksReportSelection(studio, "analysis").selectedScope, "studio");
assert.equal(brokenLinksReportSelection(studio, "notes").selectedScope, "notes");
assert.equal(brokenLinksReportSelection(analysis, "studio").selectedScope, "analysis");
assert.throws(() => brokenLinksReportSelection({ ...analysis, viewerStage: "pre-publish" }), /Working/);

const calls = [];
const service = createDocsViewerReportService({ baseUrl: "http://fixture.test", fetch: async (url, options) => {
  calls.push({ url, body: JSON.parse(options.body) });
  return { ok: true, json: async () => ({ ok: true }) };
} });
for (const request of [
  { scope: "notes", report_context: { scope: "studio" } },
  { scope: "analysis", stage: "working", report_context: { scope: "analysis", stage: "working" } }
]) {
  await service.runBrokenLinksAudit(request);
  assert.deepEqual(calls.at(-1), { url: "http://fixture.test/docs/broken-links", body: request });
}

// Minimal document surface verifies request/response rendering without browser choreography.
class Node {
  children = [];
  dataset = {};
  appendChild(child) { this.children.push(child); child.parentNode = this; }
  removeChild(child) { this.children.splice(this.children.indexOf(child), 1); }
  get firstChild() { return this.children[0]; }
  setAttribute() {}
  addEventListener() {}
}
globalThis.document = { createElement: () => new Node() };
globalThis.window = {
  location: { href: "http://fixture.test/docs/?scope=analysis&stage=working&report_scope=studio", search: "?scope=analysis&stage=working&report_scope=studio" },
  history: { replaceState: (_state, _title, href) => { window.location.href = new URL(href, window.location.href).href; } }
};
const exactHref = "/docs/?scope=analysis&stage=working&doc=d-20260101-000000-000002&subdoc=d-20260101-000000-000003";
const reportRoot = new Node();
await mountDocsBrokenLinksReport({
  ...analysis, reportRoot,
  viewerUrlForScope: () => { throw new Error("Must retain the exact service-owned correction URL"); },
  reportService: { runBrokenLinksAudit: async (request) => {
    assert.deepEqual(request, { scope: "analysis", stage: "working", report_context: { scope: "analysis", stage: "working" } });
    return {
      ok: true, scope: "analysis", stage: "working",
      entries: [{ from_page_url: exactHref, from_page_text: "Source", link_text: "Missing", link_url: "/docs/?doc=missing" }],
      unavailable_sources: [{ from_page_url: exactHref, from_page_text: "Unbuilt" }]
    };
  } }
});
const rows = reportRoot.children[1].children[1].children;
assert.equal(rows[0].children[0].href, exactHref);
assert.equal(rows[1].children[0].href, exactHref);
assert.equal(new URL(window.location.href).searchParams.get("report_scope"), "analysis");
console.log("Broken Links request, source partition and correction URL contracts passed.");
