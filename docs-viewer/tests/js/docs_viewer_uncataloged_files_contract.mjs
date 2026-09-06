import assert from "node:assert/strict";
import { normalizeUncatalogedFilesResponse } from "../../runtime/js/reports/uncataloged-files-report.js";

const response = (rows) => ({
  ok: true,
  report: { schema_version: "docs_uncataloged_files_report_v1", rows }
});
const projectRow = {
  folder: "projects/alpha",
  file_name: "notes.pdf",
  local_target: "projects/alpha/notes.pdf"
};
const processingRow = {
  folder: "processing/ink-engine/output",
  file_name: "étude #1.png",
  local_target: "processing/ink-engine/output/%C3%A9tude%20%231.png"
};

assert.deepEqual(normalizeUncatalogedFilesResponse(response([projectRow, processingRow])), [
  { folder: "projects/alpha", fileName: "notes.pdf", localTarget: "projects/alpha/notes.pdf" },
  {
    folder: "processing/ink-engine/output",
    fileName: "étude #1.png",
    localTarget: "processing/ink-engine/output/%C3%A9tude%20%231.png"
  }
]);
assert.deepEqual(normalizeUncatalogedFilesResponse(response([])), []);
for (const invalid of [
  { ...projectRow, folder: "/projects/alpha" },
  { ...projectRow, local_target: "/projects/alpha/notes.pdf" },
  { ...projectRow, local_target: "" },
  { ...projectRow, file_name: "nested/notes.pdf" }
]) {
  assert.throws(() => normalizeUncatalogedFilesResponse(response([invalid])), /row is invalid/);
}
console.log("Uncataloged Files contract passed: configured source roots and encoded targets.");
