import assert from "node:assert/strict";
import { createDocsViewerReportService } from "../../runtime/js/reports/docs-viewer-report-service.js";
import { readUnpublishableRows } from "../../runtime/js/reports/unpublishable-report.js";

const docId = "d-20260909-160000-000001";
const collection = { scope: "analysis", stage: "working" };
const row = {
  target: { ...collection, sub_scope: "", doc_id: docId }, title: "Document", collection_title: "Scope documents",
  href: `/docs/?scope=analysis&stage=working&doc=${docId}`
};
const child = {
  ...row, target: { ...row.target, sub_scope: "works" }, collection_title: "Works",
  href: `/docs/?scope=analysis&stage=working&doc=report-host&subdoc=${docId}`
};
const payload = { ok: true, schema_version: "docs_unpublishable_report_v1", ...collection, rows: [row, child] };
assert.deepEqual(readUnpublishableRows(payload), [row, child]);
assert.deepEqual(readUnpublishableRows({ ...payload, rows: [] }), []);
assert.throws(() => readUnpublishableRows({ ...payload, stage: "pre-publish" }), /data is invalid/);
assert.throws(() => readUnpublishableRows({ ...payload, rows: [row, row] }), /link is invalid/);
assert.throws(() => readUnpublishableRows({ ...payload, rows: [{ ...row, target: { ...row.target, stage: "pre-publish" } }] }), /identity is invalid/);
assert.throws(() => readUnpublishableRows({ ...payload, rows: [{ ...row, href: row.href.replace("working", "pre-publish") }] }), /link is invalid/);
assert.throws(() => readUnpublishableRows({ ...payload, rows: [{ ...row, href: "https://example.test/" }] }), /link is invalid/);

const requests = [];
const service = createDocsViewerReportService({
  baseUrl: "http://fixture.test",
  fetch: async (url, options) => {
    requests.push({ url, options });
    return { ok: true, json: async () => payload };
  }
});
assert.equal(await service.readUnpublishable(collection), payload);
assert.equal(requests[0].url, "http://fixture.test/docs/unpublishable-report?scope=analysis&stage=working");
assert.equal(requests[0].options.method, "GET");
assert.equal(requests[0].options.cache, "no-store");
console.log("Unpublishable contract passed: exact Working reads and parent/child links.");
