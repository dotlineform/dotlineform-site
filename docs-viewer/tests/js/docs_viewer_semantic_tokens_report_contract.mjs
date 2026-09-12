import assert from "node:assert/strict";
import {
  loadSemanticTokenRows, mountSemanticTokensReport, readSemanticTokenRows
} from "../../runtime/js/reports/semantic-tokens-report.js";
import { createDocsViewerReportService } from "../../runtime/js/reports/docs-viewer-report-service.js";

const docId = "d-20260912-120000-000001";
const hostId = "d-20260912-120000-000002";
const raw = "[[catalogue:image:work:00008|alt=Detail&detail_id=003]]";
const occurrence = collection => ({
  family: "catalogue", target_type: "work", target_id: "00008", title: "Detail", raw,
  source_scope: "analysis", source_sub_scope: collection, source_doc_id: docId
});
const source = (collection, title) => ({
  target: { scope: "analysis", sub_scope: collection, doc_id: docId }, title,
  href: `/docs/?scope=analysis&stage=working&doc=${collection ? hostId : docId}${collection ? "&subdoc=" + docId : ""}`
});
const payload = {
  scope: "analysis", stage: "working",
  occurrences: [occurrence(""), occurrence("works"), occurrence("works")],
  source_documents: [source("", "Main title"), source("works", "Work title")]
};
const before = structuredClone(payload);
const rows = readSemanticTokenRows(payload);
assert.deepEqual(rows.map(row => row.sourceTitle), ["Main title", "Work title", "Work title"]);
assert.equal(rows[1].sourceHref, payload.source_documents[1].href);
assert.equal(rows[0].sourceHref, payload.source_documents[0].href);
assert.equal(rows[1].sourceSubScope, "works");
assert.equal(rows[1].targetId, "00008");
assert.equal(rows[1].raw, raw);
assert.deepEqual(payload, before);
assert.throws(() => readSemanticTokenRows({ ...payload, source_documents: [payload.source_documents[0]] }), /unavailable/);
assert.throws(() => readSemanticTokenRows({ ...payload, stage: "pre-publish" }), /scope\/stage/);
assert.throws(() => readSemanticTokenRows({ ...payload, scope: "studio" }), /scope\/stage/);

const calls = [];
const reportService = createDocsViewerReportService({
  baseUrl: "http://127.0.0.1:8776",
  fetch: async (url, options) => {
    calls.push({ url, options });
    return { ok: true, json: async () => payload };
  }
});
const context = { viewerScope: "analysis", viewerStage: "working", reportService };
assert.deepEqual(await loadSemanticTokenRows(context), rows);
assert.equal(calls[0].url, "http://127.0.0.1:8776/docs/semantic-tokens?scope=analysis&stage=working");
assert.equal(calls[0].options.method, "GET");
assert.equal(calls[0].options.cache, "no-store");
for (const invalid of [
  { ...context, viewerScope: "studio" },
  { ...context, viewerStage: "pre-publish" },
  { ...context, viewerStage: "" }
]) {
  assert.throws(() => mountSemanticTokensReport(invalid), /only in Analysis Working/);
  await assert.rejects(() => loadSemanticTokenRows(invalid), /only in Analysis Working/);
}
assert.equal(calls.length, 1);
console.log("Semantic Tokens source identity, occurrence, stage and report/service contracts passed.");
