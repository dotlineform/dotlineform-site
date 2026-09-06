import assert from "node:assert/strict";
import { buildViewerUrlForScope, routeFromAnchorHref } from "../../runtime/js/shared/docs-viewer-router.js";
import { createDocsViewerGeneratedDataRuntime } from "../../runtime/js/shared/docs-viewer-generated-data-runtime.js";
import { createDocsViewerConfiguredScopeProvider } from "../../runtime/js/shared/docs-viewer-configured-scope-provider.js";
import { normalizeManagedDocumentTarget, managedDocumentTargetsEqual } from "../../runtime/js/management/docs-viewer-management-document-target.js";
import { normalizeManagedSubscopeCollection, committedDocumentCreateTarget } from "../../runtime/js/management/docs-viewer-management-actions.js";
import { createManagedDoc, readManagedDocSource, rebuildManagedDocSource, applyManagedSubScopeDocDelete } from "../../runtime/js/management/docs-viewer-management-client.js";

const docId = "d-20260906-170000-a1b2c3";
const working = { scope: "analysis", stage: "working", sub_scope: "projects", doc_id: docId };
const prePublish = { ...working, stage: "pre-publish" };
assert.deepEqual(normalizeManagedDocumentTarget(working), working);
assert.equal(managedDocumentTargetsEqual(working, prePublish), false);
assert.throws(() => normalizeManagedDocumentTarget({ ...working, stage: "" }), /stage/);
assert.deepEqual(normalizeManagedSubscopeCollection({ scope: "analysis", stage: "working", sub_scope: "projects" }), { scope: "analysis", stage: "working", sub_scope: "projects" });
assert.throws(() => committedDocumentCreateTarget({ ...working, stage: "pre-publish", target: working, record: { doc_id: docId } }), /stage/);
const requests = [];
const fetch = async (url, options) => {
  requests.push({ url, body: options.body ? JSON.parse(options.body) : null });
  return { ok: true, json: async () => url.endsWith("/capabilities") ? { capabilities: {
    generated_data_reads: true, scopes: {
      analysis: { stages: { working: { available: true, generated_data_reads: true }, "pre-publish": { available: true, generated_data_reads: true } } },
      studio: { available: true, generated_data_reads: true }
    }
  } } : { ok: true, schema: "docs_index_tree_v1", docs: [], doc_id: docId } };
};
const options = { scope: "analysis", stage: "working", baseUrl: "http://fixture.test", fetch };
await createManagedDoc({ title: "Created", sub_scope: "projects" }, options);
await readManagedDocSource(working, options);
await rebuildManagedDocSource(working, { source_body: "[[media:docs/dotlineform/img/one.jpg]]", source_revision: "revision" }, options);
await applyManagedSubScopeDocDelete(working, "sha256:" + "a".repeat(64), options);
assert.equal(requests[0].body.stage, "working");
assert.match(requests[1].url, /stage=working/);
assert.deepEqual(requests[2].body, { ...working, source_body: "[[media:docs/dotlineform/img/one.jpg]]", source_revision: "revision" });
assert.equal(requests[3].body.stage, "working");

const configs = new Map([
  ["analysis", { scopeId: "analysis", stage: "pre-publish", viewerBaseUrl: "/docs/", includeScopeParam: true, indexTreeUrl: "/docs/index-tree?scope=analysis&stage=pre-publish" }],
  ["studio", { scopeId: "studio", indexTreeUrl: "/docs/index-tree?scope=studio" }]
]);
const data = createDocsViewerGeneratedDataRuntime({
  window: { fetch }, generatedBaseUrl: "http://fixture.test", generatedData: {}, management: {}, selectedDocument: {},
  viewerScope: () => "analysis", viewerStage: () => "pre-publish"
});
const provider = createDocsViewerConfiguredScopeProvider({ generatedData: data, viewerScope: () => "analysis", scopeConfig: { scopeConfigsById: configs } });
await provider.readIndex();
assert.match(requests.at(-1).url, /stage=pre-publish/);
await provider.readIndex({ scope: "studio" });
assert.doesNotMatch(requests.at(-1).url, /stage=/, "another scope must not inherit the current Analysis stage");
const href = buildViewerUrlForScope({ scope: "analysis", docId, origin: "http://fixture.test", scopeConfigsById: configs });
assert.match(href, /stage=pre-publish/);
assert.deepEqual(routeFromAnchorHref(href, {
  origin: "http://fixture.test", currentHref: `http://fixture.test/docs/?scope=analysis&stage=working&doc=${docId}`,
  viewerPathname: "/docs/", viewerScope: "analysis", includeScopeParam: true, allowScopeQuery: true
}), { navigateUrl: href });
console.log("Stage target contract passed: exact read/write requests, cross-scope reads and cross-stage navigation.");
