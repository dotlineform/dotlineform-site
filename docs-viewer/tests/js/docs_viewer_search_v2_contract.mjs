import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");
const fixture = JSON.parse(fs.readFileSync(
  path.join(repoRoot, "docs-viewer/tests/fixtures/docs_viewer_search_v2_contract.json"),
  "utf8"
));
const search = await import(pathToFileURL(
  path.join(repoRoot, "site/docs-viewer/runtime/js/shared/docs-viewer-search.js")
));

fixture.tokenizer_cases.forEach((testCase) => {
  assert.deepEqual(search.tokenizeSearchValue(testCase.value), testCase.terms);
});

const documentsById = new Map(fixture.documents.map((document) => [document.id, document]));
const index = {
  header: { schema: "docs_viewer_search_index_v2", scope: "studio" },
  fields: fixture.fields,
  docs: fixture.expected_document_ids.map((docId) => documentsById.get(docId)),
  terms: fixture.expected_postings
};
fixture.queries.forEach((testCase) => {
  assert.deepEqual(
    search.collectSearchMatches(index, testCase.value).map((match) => match.entry.id),
    testCase.document_ids,
    testCase.value
  );
});

console.log("Docs Viewer search v2 JavaScript contract OK");
