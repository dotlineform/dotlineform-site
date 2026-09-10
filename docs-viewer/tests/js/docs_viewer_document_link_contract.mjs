import assert from "node:assert/strict";
import { createDocsViewerManagementSourceAdapter } from "../../runtime/js/management/docs-viewer-management-source-adapter.js";
import { createDocsViewerConfiguredScopeProvider } from "../../runtime/js/shared/docs-viewer-configured-scope-provider.js";
import { createDocsViewerSourceEditorMode } from "../../runtime/js/management/source-editor/source-editor.js";
import { documentLinkControlDefinition } from "../../runtime/js/management/source-editor/document-link-contribution.js";
import { createDocsViewerManagementActionResolver } from "../../runtime/js/management/docs-viewer-management.js";
import { documentLinkMarkdown, filterDocumentLinkTargets, insertDocumentLink, normalizeDocumentLinkTargets } from "../../runtime/js/management/source-editor/document-link.js";

const id = "d-20260910-100000-aaaaaa";
const host = "d-20260910-100001-bbbbbb";
const context = { scope: "analysis", stage: "working", sub_scope: "works", doc_id: id };
const payload = { schema_version: "docs_document_link_targets_v1", scope: "analysis", stage: "working", sub_scopes: ["works", "concepts"], documents: [
  { target: { scope: "analysis", sub_scope: "works", doc_id: id }, title: "Same title", href: `/analysis/?doc=${host}&subdoc=${id}` },
  { target: { scope: "analysis", sub_scope: "", doc_id: id }, title: "Same title", href: `/analysis/?doc=${id}` }
] };
const records = normalizeDocumentLinkTargets(payload, context).documents;
assert.equal(filterDocumentLinkTargets(records, "").length, 2);
assert.equal(filterDocumentLinkTargets(records, "", "")[0].target.sub_scope, "");
assert.equal(filterDocumentLinkTargets(records, "same", "works")[0].target.sub_scope, "works");
assert.equal(filterDocumentLinkTargets(records, id, "concepts").length, 0);
assert.throws(() => normalizeDocumentLinkTargets(payload, { ...context, stage: "pre-publish" }), /scope and stage/);
for (const mutate of [
  p => { p.documents[0].target.doc_id = ""; },
  p => { p.documents[0].href = `/analysis/?doc=${host}&subdoc=${host}`; },
  p => { p.documents[0].href += "&stage=working"; },
  p => { p.documents[0].href = "//other.test/?doc=" + id; },
  p => { p.documents[0].target.sub_scope = "invented"; },
  p => { p.documents.push(p.documents[0]); }
]) {
  const bad = structuredClone(payload);
  mutate(bad);
  assert.throws(() => normalizeDocumentLinkTargets(bad, context));
}
const record = { ...records[0], title: "A [label] *literal* <b> & \\ end" };
const markdown = documentLinkMarkdown(record);
assert.equal(markdown, `[A \\[label\\] \\*literal\\* &lt;b&gt; &amp; \\\\ end](<${record.href}>)`);

const requests = [];
const source = createDocsViewerManagementSourceAdapter({
  sourceService: { baseUrl: "http://127.0.0.1:9999" }, viewerScope: "studio", viewerStage: "",
  window: { fetch: async (url, options) => {
    requests.push(url);
    assert.equal(options.cache, "no-store");
    return { ok: true, json: async () => payload };
  } }
});
const provider = createDocsViewerConfiguredScopeProvider({ source });
assert.equal(await provider.readDocumentLinkTargets({ scope: "analysis", stage: "working" }), payload);
assert.deepEqual(requests, ["http://127.0.0.1:9999/docs/document-link-targets?scope=analysis&stage=working"]);
assert.equal(createDocsViewerConfiguredScopeProvider({}).readDocumentLinkTargets, undefined);
assert.deepEqual(documentLinkControlDefinition().appKinds, ["manage"]);
for (const stage of ["", "working", "pre-publish"]) {
  const resolve = createDocsViewerManagementActionResolver({ selectedDocument: { selectedDocId: id }, viewerStage: () => stage });
  assert.equal(resolve(documentLinkControlDefinition().actionId).enabled, stage !== "pre-publish");
}

// Minimal platform objects exercise the real editor's range/revision and provider contract.
class Element extends EventTarget {
  children = [];
  classList = { toggle() {} };
  value = "";
  selectionStart = 0;
  selectionEnd = 0;
  setAttribute() {}
  focus() {}
  append(...children) { this.children.push(...children); }
  appendChild(child) { this.append(child); }
  replaceChildren(...children) { this.children = children; }
  setSelectionRange(start, end) { this.selectionStart = start; this.selectionEnd = end; }
  setRangeText(text, start, end) {
    this.value = this.value.slice(0, start) + text + this.value.slice(end);
    this.setSelectionRange(start + text.length, start + text.length);
  }
}
let textarea;
globalThis.document = { createElement(tag) { const element = new Element(); if (tag === "textarea") textarea = element; return element; } };
globalThis.window = new EventTarget();
let adapter;
const editor = createDocsViewerSourceEditorMode();
const mountContext = {
  sourceTarget: context, mount: new Element(), root: new Element(), documentView: { projectToolbar() {} },
  sourceEditorServices: { setActiveSourceEditorContextAdapter(value) { adapter = value; } },
  collectionProvider: {
    ...provider,
    readSource: async () => ({ ...context, source_body: "before selected after", source_revision: "revision" })
  }
};
await editor.mount(mountContext);
await adapter.readDocumentLinkTargets();
assert.equal(requests[1], requests[0], "the mounted child supplies scope/stage, not the outer route or sub-scope filter");
textarea.setSelectionRange(7, 15);
insertDocumentLink(adapter, adapter.captureSelection(), record, () => true);
assert.equal(textarea.value, "before " + markdown + " after", "selected words are replaced by the document-title link");
textarea.setSelectionRange(0, 0);
insertDocumentLink(adapter, adapter.captureSelection(), record, () => true);
assert.ok(textarea.value.startsWith(markdown + "before "), "empty selection inserts at the cursor");
const capture = adapter.captureSelection();
textarea.value += "edited";
textarea.dispatchEvent(new Event("input"));
assert.throws(() => insertDocumentLink(adapter, capture, record, () => true), /source changed/);
assert.throws(() => insertDocumentLink(adapter, adapter.captureSelection(), record, () => false), /no longer active/);
editor.unmount(mountContext);
console.log("Document link lookup, filtering, identity, Markdown and captured-source contracts passed");
