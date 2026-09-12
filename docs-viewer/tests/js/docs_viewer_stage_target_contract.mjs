import assert from "node:assert/strict";
import { buildViewerUrlForScope, routeFromAnchorHref } from "../../runtime/js/shared/docs-viewer-router.js";
import { createDocsViewerGeneratedDataRuntime } from "../../runtime/js/shared/docs-viewer-generated-data-runtime.js";
import { createDocsViewerConfiguredScopeProvider } from "../../runtime/js/shared/docs-viewer-configured-scope-provider.js";
import { normalizeManagedDocumentTarget, managedDocumentTargetsEqual } from "../../runtime/js/management/docs-viewer-management-document-target.js";
import { normalizeManagedSubscopeCollection, committedDocumentCreateTarget, committedDocumentMoveRecord, committedDocumentPlacement } from "../../runtime/js/management/docs-viewer-management-actions.js";
import { createManagedDoc, readManagedDocSource, rebuildManagedDocSource, applyManagedSubScopeDocDelete, assignManagedDocFieldGroup, moveManagedDoc } from "../../runtime/js/management/docs-viewer-management-client.js";
import { createDocsViewerManagementActionResolver } from "../../runtime/js/management/docs-viewer-management.js";
import { DOCS_VIEWER_ACTION_IDS } from "../../runtime/js/management/docs-viewer-action-definitions.js";
import { subjectMetadataFromResponse } from "../../runtime/js/management/docs-viewer-management-project-subject-modal.js";
import { loadDocsViewerSubscopeContribution } from "../../runtime/js/management/docs-viewer-management-document-reports.js";
import { createDocsViewerIndexSelectionOwner } from "../../runtime/js/management/docs-viewer-index-selection.js";
import { docsViewerSetPublishableActionControlState, docsViewerDocumentTransferActionControlState } from "../../runtime/js/management/docs-viewer-management-index-controller.js";
import { setManagedDocsPublishable } from "../../runtime/js/management/docs-viewer-management-client.js";
import { validateSetPublishableResponse } from "../../runtime/js/management/docs-viewer-management-publishable-workflow.js";
import { createDocsViewerManagementCapabilityController, scopePrePublishSupported, scopePublishSupported } from "../../runtime/js/management/docs-viewer-management-capabilities.js";
import { docsViewerPublishWorkflowAvailability } from "../../runtime/js/management/docs-viewer-management-publish-workflow.js";

const docId = "d-20260906-170000-a1b2c3";
const working = { scope: "analysis", stage: "working", sub_scope: "projects", doc_id: docId };
const prePublish = { ...working, stage: "pre-publish" };
assert.deepEqual(normalizeManagedDocumentTarget(working), working);
assert.equal(managedDocumentTargetsEqual(working, prePublish), false);
assert.throws(() => normalizeManagedDocumentTarget({ ...working, stage: "" }), /stage/);
assert.deepEqual(normalizeManagedSubscopeCollection({ scope: "analysis", stage: "working", sub_scope: "projects" }), { scope: "analysis", stage: "working", sub_scope: "projects" });
assert.throws(() => committedDocumentCreateTarget({ ...working, stage: "pre-publish", target: working, record: { doc_id: docId } }), /stage/);
const hostTarget = { scope: "analysis", stage: "working", doc_id: docId };
const selection = createDocsViewerIndexSelectionOwner({ initialScopeId: "analysis" });
selection.enter();
selection.toggle(docId, true);
for (const stage of ["working", "pre-publish"]) {
  const resolveAction = createDocsViewerManagementActionResolver({ indexSelection: selection, viewerStage: () => stage });
  const resolution = resolveAction(DOCS_VIEWER_ACTION_IDS.SET_PUBLISHABLE);
  assert.equal(resolution.enabled, stage === "working");
  const state = docsViewerSetPublishableActionControlState({
    source: { scope: "analysis", stage }, resolution, managementChecked: true, managementAvailable: true,
    capabilities: { scopes: { analysis: { available: true, stage, publishable: stage === "working", publishing: { apply: false, confirm: false } } } }
  });
  assert.equal(state.disabled, stage !== "working");
  assert.equal(state.hidden, stage !== "working");
}
const publishableCollection = { scope: "analysis", stage: "working" };
const publishableResult = { ok: true, operation: "set_publishable", publishable: false, target: publishableCollection, requested_doc_ids: [docId] };
const publishableOptions = { source: publishableCollection, checkedDocIds: [docId], publishable: false };
assert.equal(validateSetPublishableResponse(publishableResult, publishableOptions), publishableResult);
for (const target of [{ scope: "analysis" }, { ...publishableCollection, stage: "pre-publish" }]) {
  assert.throws(() => validateSetPublishableResponse({ ...publishableResult, target }, publishableOptions), /exact checked selection/);
}
const moved = { ...hostTarget, target: hostTarget, record: { doc_id: docId, parent_id: "d-20260907-210000-a1b2c3" } };
assert.deepEqual(committedDocumentMoveRecord(moved, hostTarget), moved.record);
const destination = { ...hostTarget, sub_scope: "works" };
const placement = { changed: true, collection_changed: true, ignored: false, viewer_url: `/docs/?scope=analysis&stage=working&doc=host&subdoc=${docId}` };
assert.deepEqual(committedDocumentPlacement({ target: destination, placement }, hostTarget), { ...placement, target: destination });
assert.equal(committedDocumentPlacement({ target: hostTarget, placement: { changed: false, collection_changed: false, ignored: true } }, hostTarget).ignored, true);
for (const invalid of [
  { target: { ...destination, doc_id: "other" }, placement },
  { target: { ...destination, stage: "pre-publish" }, placement },
  { target: destination, placement: { ...placement, collection_changed: false } },
  { target: destination, placement: { ...placement, viewer_url: placement.viewer_url.replace(docId, "other") } },
  { target: destination, placement: { ...placement, viewer_url: "https://example.test" + placement.viewer_url } }
]) assert.throws(() => committedDocumentPlacement(invalid, hostTarget), /Placement service/);
for (const mode of ["copy", "move"]) {
  assert.equal(docsViewerDocumentTransferActionControlState({ mode, source: { scope: "analysis", stage: "working" } }).hidden, true);
  assert.equal(docsViewerDocumentTransferActionControlState({ mode, source: { scope: "studio" } }).hidden, false);
}
for (const wrongTarget of [
  { ...hostTarget, stage: "pre-publish" },
  { scope: hostTarget.scope, doc_id: docId },
  { scope: "studio", doc_id: docId }
]) {
  assert.throws(() => committedDocumentMoveRecord({ ...moved, target: wrongTarget }, hostTarget), /different document target/);
}
assert.throws(() => committedDocumentMoveRecord({ ...moved, record: { ...moved.record, doc_id: "another" } }, hostTarget), /invalid committed move record/);
const sourceActions = [
  DOCS_VIEWER_ACTION_IDS.SOURCE_ADD_CATALOGUE_IMAGE,
  DOCS_VIEWER_ACTION_IDS.SOURCE_ADD_MEDIA_VIEW_LINK,
  DOCS_VIEWER_ACTION_IDS.SOURCE_ADD_FILE,
  DOCS_VIEWER_ACTION_IDS.SOURCE_ADD_IMAGE,
  DOCS_VIEWER_ACTION_IDS.SOURCE_INSERT_DOC_LINK
];
for (const stage of ["working", "pre-publish", ""]) {
  const selectedDocument = { selectedDocId: docId };
  const resolveAction = createDocsViewerManagementActionResolver({ selectedDocument, viewerStage: () => stage });
  for (const action of sourceActions) {
    assert.equal(resolveAction(action).enabled, stage !== "pre-publish", `${stage}: ${action}`);
  }
  selectedDocument.selectedDocId = "";
  assert.ok(sourceActions.every(action => !resolveAction(action).enabled), "insertion requires an active document");
  const rebuild = resolveAction(DOCS_VIEWER_ACTION_IDS.REBUILD_DOCS);
  assert.equal(rebuild.enabled, stage !== "pre-publish", `${stage}: scope rebuild does not require an active document`);
  assert.equal(Boolean(rebuild.hidden), stage === "pre-publish", `${stage}: scope rebuild availability`);
  assert.equal(resolveAction(DOCS_VIEWER_ACTION_IDS.PUBLISH_DOCS).enabled, stage !== "working");
  assert.equal(resolveAction(DOCS_VIEWER_ACTION_IDS.PRE_PUBLISH_DOCS).enabled, stage !== "pre-publish");
}
const stagedCapabilities = {
  docs_management: true, publishing: { confirm: true, apply: true },
  scopes: { analysis: { available: true, stages: {
    working: { stage: "working", available: true, pre_publish: { preview: true, apply: true } },
    "pre-publish": { stage: "pre-publish", available: true, publishing: { confirm: true, apply: true } }
  } } }
};
// Exercise the service response through the real controller before checking the
// toolbar/workflow consumers. They receive the selected stage, not nested stages.
for (const stage of ["working", "pre-publish"]) {
  const management = { managementCapabilityCheckId: 0 };
  let capabilitiesReady;
  const ready = new Promise(resolve => { capabilitiesReady = resolve; });
  const controller = createDocsViewerManagementCapabilityController({
    management,
    routeSession: {},
    context: { isManagementContext: () => true, managementBaseUrl: "http://fixture.test" },
    callbacks: {
      viewerScope: () => "analysis",
      managementClientOptions: () => ({
        stage, baseUrl: "http://fixture.test",
        fetch: async () => ({ ok: true, json: async () => ({ capabilities: stagedCapabilities }) })
      }),
      renderManagementUi: () => { if (management.managementChecked) capabilitiesReady(); }
    }
  });
  controller.initialize();
  await ready;
  const active = management.managementCapabilities;
  assert.equal(management.managementAvailable, true);
  assert.equal(scopePrePublishSupported(active, "analysis", stage), stage === "working");
  assert.equal(scopePublishSupported(active, "analysis", stage), stage === "pre-publish");
  assert.equal(docsViewerPublishWorkflowAvailability(active, "analysis", stage).publish.available, stage === "pre-publish");
  const otherStage = stage === "working" ? "pre-publish" : "working";
  assert.equal(scopePrePublishSupported(active, "analysis", otherStage), false);
  assert.equal(scopePublishSupported(active, "analysis", otherStage), false);
}
assert.equal(scopePublishSupported(stagedCapabilities, "analysis"), false);
const subject = { state: "valid", kind: "work", key: "00293", fields: ["work_id"] };
const metadata = { ...working, record: { doc_id: docId, authoring_subject: subject } };
const sourceRevision = "sha256:" + "a".repeat(64);
const assignMetadata = { ...metadata, source_revision: sourceRevision };
assert.deepEqual(subjectMetadataFromResponse(assignMetadata, working), { subject, sourceRevision });
for (const wrongStage of ["pre-publish", undefined]) {
  const wrongMetadata = { ...assignMetadata, stage: wrongStage };
  if (wrongStage === undefined) delete wrongMetadata.stage;
  assert.throws(() => subjectMetadataFromResponse(wrongMetadata, working), /exact target/);
}

// Exercise the mounted report's actual module loader without DOM or Catalogue access.
const savedWindow = globalThis.window;
globalThis.window = { fetch: async () => { throw new Error("Catalogue unavailable in this fixture"); } };
try {
  for (const [subScope, customisationId] of [["works", "working_works"], ["processing", "working_processing"]]) {
    for (const stage of ["working", "pre-publish"]) {
      const collection = { scope: "analysis", stage, sub_scope: subScope };
      const contribution = await loadDocsViewerSubscopeContribution({
        managementContext: true,
        managementService: { baseUrl: "http://fixture.test" },
        routeContext: { viewerStage: stage },
        scopeConfigState: { scopeConfigs: [{ scopeId: "analysis", subScopes: [{
          subScope,
          subScopeCustomisation: { id: customisationId, capabilities: { assignableFieldGroups: ["authoring_subject"] } }
        }] }] }
      }, { scope: "analysis", stage, doc_id: docId }, subScope);
      const context = { collection, target: { ...collection, doc_id: docId }, document: metadata.record };
      const info = contribution.projectDetailInfo(context);
      if (stage === "working") {
        assert.equal(info.actions.assignSubject, true, `${subScope}: Working loads Subject capability`);
        assert.equal(info.fields[0].id, "authoring_subject");
        assert.throws(() => contribution.projectDetailInfo({
          ...context, target: { ...context.target, stage: "pre-publish" }
        }), /target is invalid/);
      } else {
        assert.equal(info, null, `${subScope}: Pre-publish retains its default contribution`);
      }
    }
  }
  for (const subScope of ["concepts", "moments"]) {
    const contribution = await loadDocsViewerSubscopeContribution({
      scopeConfigState: { scopeConfigs: [{ scopeId: "analysis", subScopes: [{ subScope }] }] }
    }, { scope: "analysis", stage: "working", doc_id: docId }, subScope);
    assert.equal(contribution.projectDetailInfo({}), null, "plain collections load the default contribution");
  }
} finally {
  if (savedWindow === undefined) delete globalThis.window;
  else globalThis.window = savedWindow;
}
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
await rebuildManagedDocSource(working, { source_body: "[[media:docs/analysis/img/one.jpg]]", source_revision: "revision" }, options);
await applyManagedSubScopeDocDelete(working, "sha256:" + "a".repeat(64), options);
assert.equal(requests[0].body.stage, "working");
assert.match(requests[1].url, /stage=working/);
assert.deepEqual(requests[2].body, { ...working, source_body: "[[media:docs/analysis/img/one.jpg]]", source_revision: "revision" });
assert.equal(requests[3].body.stage, "working");
const assignment = {
  source_revision: sourceRevision, field_group: "authoring_subject", confirm: true,
  fields: { folder_path: "", work_id: "00293", series_id: "", detail_uid: "" }
};
await assignManagedDocFieldGroup(working, assignment, options);
assert.deepEqual(requests.at(-1).body, { ...working, ...assignment });
await moveManagedDoc(docId, moved.record.parent_id, options);
assert.deepEqual(requests.at(-1).body, { ...hostTarget, parent_id: moved.record.parent_id });
await setManagedDocsPublishable(publishableCollection, [docId], false, options);
assert.deepEqual(requests.at(-1).body, { ...publishableCollection, doc_ids: [docId], publishable: false, confirm: true });

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
