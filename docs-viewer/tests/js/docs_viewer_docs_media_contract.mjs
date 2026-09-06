import assert from "node:assert/strict";
import { normalizeDocsMediaResponse } from "../../runtime/js/reports/docs-media-report.js";
import { createDocsViewerReportService } from "../../runtime/js/reports/docs-viewer-report-service.js";

const requests = [];
const fetch = async (_url, options) => {
  requests.push(JSON.parse(options.body));
  return { ok: true, json: async () => ({ ok: true }) };
};
const service = createDocsViewerReportService({ baseUrl: "http://fixture.test", fetch });
for (const collection of [
  { scope: "analysis", stage: "working" },
  { scope: "analysis", stage: "pre-publish" },
  { scope: "studio" }
]) {
  await service.runDocsMedia(collection);
  assert.deepEqual(requests.at(-1), collection);
  const stagePath = collection.stage ? collection.stage + "/" : "";
  const target = { ...collection, sub_scope: "", doc_id: "d-20260101-000000-000001" };
  const payload = {
    ok: true, dry_run: false, summary_text: "Docs Media refreshed.",
    report: {
      schema_version: "docs_media_report_v2", ...collection,
      rows: [{
        scope: collection.scope, media_type: "img", identity: "a file.png",
        local_target: `docs-viewer/scopes/${collection.scope}/${stagePath}source/media/img/a%20file.png`,
        documents: [{ target, title: "Media document", href: "/docs/?" + new URLSearchParams(collection) + "&doc=" + target.doc_id }]
      }]
    }
  };
  const report = normalizeDocsMediaResponse(payload, collection);
  assert.equal(report.stage, collection.stage);
  assert.equal(report.rows[0].documents[0].target.stage, collection.stage);
  assert.equal(report.rows[0].localTarget, payload.report.rows[0].local_target);
  if (collection.stage) {
    const other = collection.stage === "working" ? "pre-publish" : "working";
    assert.throws(() => normalizeDocsMediaResponse(payload, { ...collection, stage: other }), /report is invalid/);
    for (const wrongStage of [undefined, other]) {
      const invalid = structuredClone(payload);
      invalid.report.rows[0].documents[0].target.stage = wrongStage;
      assert.throws(() => normalizeDocsMediaResponse(invalid, collection), /document target is invalid/);
    }
  }
}
console.log("Docs Media contract passed: staged and unstaged requests, responses and document targets.");
