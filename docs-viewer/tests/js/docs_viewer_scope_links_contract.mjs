import assert from "node:assert/strict";
import fs from "node:fs";
import { readScopeLinksRows, sortScopeLinksRows, mountScopeLinksReport } from "../../runtime/js/reports/scope-links-report.js";
import { createDocsViewerReportService } from "../../runtime/js/reports/docs-viewer-report-service.js";

const id = n => `d-20260910-120000-${String(n).padStart(6, "0")}`;
function summary(n, title, collection = "") {
  return { target: { scope: "analysis", sub_scope: collection, doc_id: id(n) }, title,
    href: `/docs/?scope=analysis&doc=${id(collection ? 99 : n)}${collection ? "&subdoc=" + id(n) : ""}`,
    subject: { state: "valid", kind: "work", key: "00523" } };
}
const a = summary(1, "Beta");
const b = summary(2, "Alpha", "concepts");
const c = summary(3, "Alpha", "works");
const edge = document => ({ document, occurrences: [{ label: "first" }, { label: "second" }] });
const record = (self, outgoing, incoming) => ({ schema_version: 1, self, outgoing: outgoing.map(edge), incoming: incoming.map(edge) });
const payload = { schema_version: 1, scope: "analysis", stage: "working", documents: [
  record(a, [b, c], [b]), record(b, [a], [a]), record(c, [], [a])
] };
const original = structuredClone(payload);
const rows = readScopeLinksRows(payload);
assert.equal(rows.length, 3); // Two occurrences stay one pair; incoming mirrors add no rows.
assert.deepEqual(rows.map(row => [row.from.target.doc_id, row.to.target.doc_id]), [[id(1), id(2)], [id(1), id(3)], [id(2), id(1)]]);
assert.deepEqual(rows[0].to.subject, b.subject); // Retain metadata for the later icon policy.
const childHref = new URL(rows[0].to.href, "https://docs.invalid");
assert.equal(childHref.searchParams.get("stage"), "working");
assert.equal(childHref.searchParams.get("doc"), id(99));
assert.equal(childHref.searchParams.get("subdoc"), id(2));
const pairs = list => list.map(row => [row.from.target.doc_id, row.to.target.doc_id]);
assert.deepEqual(pairs(sortScopeLinksRows(rows)), [[id(2), id(1)], [id(1), id(2)], [id(1), id(3)]]);
assert.deepEqual(pairs(sortScopeLinksRows(rows, "from", "desc")), [[id(1), id(2)], [id(1), id(3)], [id(2), id(1)]]);
assert.deepEqual(pairs(sortScopeLinksRows(rows, "to", "asc")), [[id(1), id(2)], [id(1), id(3)], [id(2), id(1)]]);
assert.deepEqual(pairs(sortScopeLinksRows(rows, "to", "desc")), [[id(2), id(1)], [id(1), id(2)], [id(1), id(3)]]);
assert.deepEqual(payload, original);
assert.deepEqual(readScopeLinksRows({ ...payload, documents: [] }), []);
for (const change of [
  p => { p.stage = "pre-publish"; },
  p => { p.documents[0].outgoing[0].document.href = "javascript:alert(1)"; },
  p => { p.documents[0].outgoing[0].document.href = `/docs/?scope=analysis&doc=${id(99)}&subdoc=${id(5)}`; },
  p => { p.documents.push(p.documents[0]); },
  p => { p.documents[0].outgoing.push(p.documents[0].outgoing[0]); }
]) {
  const invalid = structuredClone(payload);
  change(invalid);
  assert.throws(() => readScopeLinksRows(invalid));
}
assert.throws(() => mountScopeLinksReport({ viewerScope: "analysis", viewerStage: "pre-publish" }), /only in Analysis Working/);

const calls = [];
let status = 200;
const service = createDocsViewerReportService({ baseUrl: "http://127.0.0.1:8776", fetch: async (url, options) => {
  calls.push({ url, options });
  return { ok: status === 200, status, json: async () => status === 200 ? payload : { error: "Snapshot unavailable" } };
} });
assert.equal(await service.readScopeLinks({ scope: "analysis", stage: "working" }), payload);
assert.equal(calls[0].url, "http://127.0.0.1:8776/docs/scope-links?scope=analysis&stage=working");
assert.equal(calls[0].options.cache, "no-store");
assert.equal(calls[0].options.method, "GET");
status = 404;
await assert.rejects(() => service.readScopeLinks({ scope: "analysis", stage: "working" }), /Snapshot unavailable/);

const local = JSON.parse(fs.readFileSync(new URL("../../config/reports/reports.json", import.meta.url)));
assert.equal(local.reports.find(row => row.report_id === "scope_links").default_access, "local");
const publicRegistry = JSON.parse(fs.readFileSync(new URL("../../../site/assets/data/docs/public-reports.json", import.meta.url)));
assert.equal(publicRegistry.reports.some(row => row.report_id === "scope_links"), false);
assert.equal(fs.readFileSync(new URL("../../runtime/js/reports/docs-viewer-public-reports.js", import.meta.url), "utf8").includes("scope-links-report.js"), false);
console.log("Scope Links row, sort, navigation, service and local-boundary contracts passed.");
