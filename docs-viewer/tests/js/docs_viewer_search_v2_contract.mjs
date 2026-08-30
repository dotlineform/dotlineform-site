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
  path.join(repoRoot, "docs-viewer/runtime/js/shared/docs-viewer-search.js")
));
const searchController = await import(pathToFileURL(
  path.join(repoRoot, "docs-viewer/runtime/js/shared/docs-viewer-search-controller.js")
));
const routeWorkflow = await import(pathToFileURL(
  path.join(repoRoot, "docs-viewer/runtime/js/shared/docs-viewer-route-workflow.js")
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

const fullTextIndex = {
  header: { schema: "docs_viewer_search_index_v2", scope: "studio" },
  fields: ["title", "heading", "body", "code"],
  docs: [
    { id: "doc-a", title: "Search Mechanics", href: "/docs/?doc=doc-a" },
    { id: "doc-b", title: "Runtime Notes", href: "/docs/?doc=doc-b" },
    { id: "doc-c", title: "Other", href: "/docs/?doc=doc-c" }
  ],
  terms: {
    search: { title: [0], heading: [1], body: [2] },
    compatibility: { body: [0, 1] },
    key: { body: [0] },
    known: { heading: [0] },
    weak: { heading: [0] },
    spots: { heading: [0] },
    docs_viewer_base_url: { code: [0] },
    docs: { code: [0] },
    viewer: { code: [0] },
    base: { code: [0] },
    url: { code: [0] },
    docs_subscope: { code: [0] },
    subscope: { code: [0] }
  }
};
function matchIds(query) {
  return search.collectSearchMatches(fullTextIndex, query).map((match) => match.entry.id);
}
assert.deepEqual(matchIds("search"), ["doc-a", "doc-b", "doc-c"]);
assert.deepEqual(matchIds("search compatibility"), ["doc-a", "doc-b"]);
assert.deepEqual(matchIds("known weak spots"), ["doc-a"]);
assert.deepEqual(matchIds("compatibility key"), ["doc-a"]);
assert.deepEqual(matchIds("DOCS_VIEWER_BASE_URL"), ["doc-a"]);
assert.deepEqual(matchIds("docs_subscope"), ["doc-a"]);
assert.deepEqual(matchIds("d-20260813-000001-aaaaaa"), []);
assert.deepEqual(matchIds("2026"), []);

const sharedDocId = "d-20260814-120000-abcdef";
const mixedTargetIndex = {
  header: { schema: "docs_viewer_search_index_v2", scope: "analysis" },
  fields: ["title", "identity"],
  docs: [
    { id: sharedDocId, title: "Parent target", href: `/analysis/?doc=${sharedDocId}` },
    {
      id: sharedDocId,
      title: "Child target",
      href: `/analysis/?doc=report&subdoc=${sharedDocId}`,
      sub_scope: "tags",
      report_doc_id: "report",
      collection_title: "Concepts",
      display_meta: "2026-08-14 • Concepts"
    }
  ],
  terms: {
    [sharedDocId]: { identity: [0, 1] },
    parent: { title: [0] },
    child: { title: [1] },
    target: { title: [0, 1] }
  }
};
assert.deepEqual(
  search.collectSearchMatches(mixedTargetIndex, sharedDocId).map((match) => (
    [match.entry.id, match.entry.sub_scope || ""]
  )),
  [[sharedDocId, "tags"], [sharedDocId, ""]]
);
assert.equal(
  search.collectSearchMatches(mixedTargetIndex, "child")[0].entry.report_doc_id,
  "report"
);

function viewerRouteCommands(viewerBaseUrl, includeScopeParam) {
  return routeWorkflow.initDocsViewerRouteWorkflow({
    content: {},
    documentIndex: {},
    includeScopeParam,
    preserveQueryParams: [],
    root: {},
    routeSession: {},
    scopeConfig: {},
    searchRecent: {},
    selectedDocument: {},
    viewerBaseUrl,
    viewerScope: "analysis",
    window: {
      location: {
        hash: "",
        href: "http://localhost/docs/",
        origin: "http://localhost",
        search: ""
      }
    }
  }).commands;
}

const manageRouteCommands = searchController.createDocsViewerSearchRouteCommands({
  routeCommands: viewerRouteCommands("/docs/", true),
  viewerTargetDocId: (docId) => docId
});
const publicRouteCommands = searchController.createDocsViewerSearchRouteCommands({
  routeCommands: viewerRouteCommands("/analysis/", false),
  viewerTargetDocId: (docId) => docId
});
assert.equal(
  manageRouteCommands.viewerUrl("report", "", "", { subdoc: sharedDocId }),
  `/docs/?scope=analysis&doc=report&subdoc=${sharedDocId}`
);
assert.equal(
  publicRouteCommands.viewerUrl("report", "", "", { subdoc: sharedDocId }),
  `/analysis/?doc=report&subdoc=${sharedDocId}`
);
assert.equal(
  manageRouteCommands.viewerUrl(sharedDocId, "", ""),
  `/docs/?scope=analysis&doc=${sharedDocId}`
);

const renderedRouteCalls = [];
const results = { innerHTML: "" };
const more = { hidden: true, innerHTML: "" };
const resultsStatus = {
  classList: { toggle() {} },
  hidden: true,
  textContent: ""
};
const priorDocument = globalThis.document;
globalThis.document = { title: "" };
try {
  const controller = searchController.initDocsViewerSearchController({
    documentIndex: { docsById: new Map() },
    hasActiveQuery: () => true,
    more,
    paneCommands: { showSearchPane() {} },
    recentEnabled: false,
    results,
    resultsStatus,
    routeCommands: {
      viewerTargetDocId: (docId) => docId === "report" ? "inferred-report" : docId,
      viewerUrl(docId, hash, query, reportParams) {
        renderedRouteCalls.push({ docId, hash, query, reportParams });
        return publicRouteCommands.viewerUrl(docId, hash, query, reportParams);
      }
    },
    searchBatchSize: 20,
    searchEnabled: true,
    searchRecent: {
      searchIndex: mixedTargetIndex,
      searchLoaded: true,
      searchQuery: "target",
      searchVisibleCount: 20
    },
    selectedDocument: {},
    setRecentModeActive() {}
  });
  controller.renderSearchMode();
} finally {
  globalThis.document = priorDocument;
}
assert.deepEqual(renderedRouteCalls, [
  { docId: "report", hash: "", query: "", reportParams: { subdoc: sharedDocId } },
  { docId: sharedDocId, hash: "", query: "", reportParams: undefined }
]);
assert.match(results.innerHTML, new RegExp(`/analysis/\\?doc=report&amp;subdoc=${sharedDocId}`));
assert.match(results.innerHTML, /2026-08-14 • Concepts/);

console.log("Docs Viewer search v2 JavaScript contract OK");
