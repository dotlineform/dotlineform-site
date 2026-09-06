import assert from "node:assert/strict";
import { normalizeProjectStateResponse } from "../../runtime/js/reports/project-state-report.js";

const target = {
  scope: "analysis", stage: "working", sub_scope: "works", doc_id: "d-20260101-000000-000001"
};
const href = "/docs/?scope=analysis&stage=working&doc=d-20260801-073826-8865a8&subdoc=" + target.doc_id;
const response = {
  ok: true,
  report: {
    schema_version: "docs_project_state_report_v3",
    generation: "sha256:" + "1".repeat(64),
    generated_at: "2026-09-06T20:00:00Z",
    inputs: { scope: "analysis", stage: "working", sub_scope: "works" },
    rows: [{
      folder: { key: "projects/alpha", label: "/alpha", href: "dlf-local:projects/alpha" },
      documents: [{
        target, title: "Alpha notes", href,
        declared_subject: { kind: "folder", key: "projects/alpha" }, applicable_series_ids: []
      }],
      series: [], series_issues: [], states: { reconciliation: "documents_only" },
      matched_document_count: 1, matched_work_count: 0
    }]
  }
};

const document = normalizeProjectStateResponse(response).rows[0].documents[0];
assert.deepEqual(document.target, target);
assert.equal(document.href, href);
for (const owner of ["inputs", "document"]) {
  for (const stage of [undefined, "pre-publish"]) {
    const invalid = structuredClone(response);
    const changed = owner === "inputs" ? invalid.report.inputs : invalid.report.rows[0].documents[0].target;
    changed.stage = stage;
    assert.throws(() => normalizeProjectStateResponse(invalid), /invalid/);
  }
}
const retired = structuredClone(response);
retired.report.rows[0].documents[0].target = { ...target, scope: "dotlineform", sub_scope: "projects" };
assert.throws(() => normalizeProjectStateResponse(retired), /document target is invalid/);
console.log("Project State contract passed: exact Working Works document targets and links.");
