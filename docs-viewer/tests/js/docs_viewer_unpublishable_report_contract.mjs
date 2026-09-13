import assert from "node:assert/strict";
import { createDocsViewerReportService } from "../../runtime/js/reports/docs-viewer-report-service.js";
import { readUnpublishableDocuments } from "../../runtime/js/reports/unpublishable-report.js";

const docId = "d-20260909-160000-000001";
const collection = { scope: "analysis", stage: "working" };
const record = { doc_id: docId, title: "Source title" };
const payload = { ok: true, schema_version: "docs_unpublishable_report_v3", ...collection, documents: [record] };
assert.deepEqual(readUnpublishableDocuments(payload), [record]);
assert.deepEqual(readUnpublishableDocuments({ ...payload, documents: [] }), []);
assert.deepEqual(readUnpublishableDocuments({ ...payload, documents: [{ ...record, title: null }] }), [{ ...record, title: null }]);
assert.throws(() => readUnpublishableDocuments({ ...payload, stage: "pre-publish" }));
assert.throws(() => readUnpublishableDocuments({ ...payload, documents: [record, record] }));
assert.throws(() => readUnpublishableDocuments({ ...payload, documents: [{ ...record, title: 1 }] }));

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
await service.openPublicationIgnore();
assert.equal(requests[1].url, "http://fixture.test/docs/open-publication-ignore");
assert.equal(requests[1].options.method, "POST");
assert.deepEqual(JSON.parse(requests[1].options.body), collection);
console.log("Unpublishable contract passed: fresh file reads and a confined editor target.");
