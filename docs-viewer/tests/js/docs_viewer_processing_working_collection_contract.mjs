import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";


const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");
const workingSubjects = await import(pathToFileURL(path.join(
  repoRoot,
  "docs-viewer/runtime/js/management/docs-viewer-management-subscope-dotlineform-projects.js"
)));
const configController = await import(pathToFileURL(path.join(
  repoRoot,
  "docs-viewer/runtime/js/shared/docs-viewer-config-controller.js"
)));
const subjects = await import(pathToFileURL(path.join(
  repoRoot,
  "docs-viewer/runtime/js/management/docs-viewer-management-document-subject.js"
)));

assert.deepEqual(subjects.parseDocsViewerDetailUid("00008-001"), { workId: "00008", detailId: "001" });
for (const invalid of ["8-1", "00008_001", "00008-001\n", "٠٠٠٠٨-001", null]) {
  assert.equal(subjects.parseDocsViewerDetailUid(invalid), null);
}
const detailDocument = {
  doc_id: "independent-analysis-doc",
  authoring_subject: { state: "valid", kind: "detail", key: "00008-001", fields: ["detail_uid"] }
};
assert.equal(workingSubjects.projectDocsViewerWorkingSubject(detailDocument, {
  available: true, titles: new Map()
}).state, "valid");
const analysisCollection = { scope: "analysis", sub_scope: "works" };
const analysisContribution = await workingSubjects.createDocsViewerManagementSubscopeAnalysisWorks({
  collection: analysisCollection,
  descriptor: configController.normalizeDocsViewerSubScopeCustomisation({
    id: "analysis_works", capabilities: { assignable_field_groups: ["authoring_subject"] }
  }),
  fetch: () => Promise.reject(new Error("No Catalogue required for a Detail subject"))
});
const detailInfo = analysisContribution.projectDetailInfo({
  collection: analysisCollection,
  target: { ...analysisCollection, doc_id: detailDocument.doc_id },
  document: detailDocument
});
assert.equal(detailInfo.actions.assignSubject, true);
assert.equal(detailInfo.fields[0].state, "detail");
assert.equal(detailInfo.fields[0].detail, "00008-001");
assert.throws(() => analysisContribution.projectDetailInfo({
  collection: analysisCollection,
  target: { ...analysisCollection, doc_id: "another-doc" },
  document: detailDocument
}), /target is invalid/);

const registrySource = fs.readFileSync(path.join(
  repoRoot,
  "docs-viewer/runtime/js/management/docs-viewer-management-subscope-customisation-registry.js"
), "utf8");
const stylesSource = fs.readFileSync(path.join(
  repoRoot,
  "docs-viewer/static/css/docs-viewer-manage.css"
), "utf8");

assert.match(registrySource, /dotlineform_processing: function/);
assert.match(registrySource, /createDocsViewerManagementSubscopeDotlineformProcessing/);
assert.doesNotMatch(stylesSource, /data-report-subscope="processing"/);
assert.match(stylesSource, /data-working-subject-columns="subject"/);
assert.match(stylesSource, /projectSubjectUnavailableLabel[^{]*\{[^}]*text-decoration:\s*line-through/s);

const deletedWorkDocument = {
  authoring_subject: {
    state: "valid",
    kind: "work",
    key: "01943",
    fields: ["work_id"]
  }
};
assert.deepEqual(
  workingSubjects.projectDocsViewerWorkingSubject(deletedWorkDocument, {
    available: true,
    titles: new Map()
  }),
  {
    kind: "work",
    key: "01943",
    label: "01943",
    state: "unavailable",
    targetTitle: ""
  }
);
assert.equal(
  workingSubjects.projectDocsViewerWorkingSubject(deletedWorkDocument, {
    available: false,
    titles: new Map()
  }).state,
  "valid"
);
assert.deepEqual(
  workingSubjects.projectDocsViewerWorkingSubject(deletedWorkDocument, {
    available: true,
    titles: new Map([["work:01943", "Impossibility And Incompleteness"]])
  }),
  {
    kind: "work",
    key: "01943",
    label: "Impossibility And Incompleteness",
    state: "valid",
    targetTitle: "Impossibility And Incompleteness"
  }
);

const projectsContribution = await workingSubjects.createDocsViewerManagementSubscopeDotlineformProjects({
  collection: { scope: "dotlineform", sub_scope: "projects" },
  descriptor: { id: "dotlineform_projects" },
  fetch: () => Promise.reject(new Error("Catalogue unavailable in focused test"))
});
const processingContribution = await workingSubjects.createDocsViewerManagementSubscopeDotlineformProcessing({
  collection: { scope: "dotlineform", sub_scope: "processing" },
  descriptor: { id: "dotlineform_processing" },
  fetch: () => Promise.reject(new Error("Catalogue unavailable in focused test"))
});
const projectsRoot = { dataset: {} };
const processingRoot = { dataset: {} };
projectsContribution.notify({ type: "mount", root: projectsRoot });
processingContribution.notify({ type: "mount", root: processingRoot });
assert.equal(projectsRoot.dataset.workingSubjectColumns, "publication");
assert.equal(processingRoot.dataset.workingSubjectColumns, "publication");
assert.equal(projectsContribution.renderListToolbar, undefined);
assert.equal(processingContribution.renderListToolbar, undefined);

const descriptor = configController.normalizeDocsViewerSubScopeCustomisation({
  id: "dotlineform_processing",
  capabilities: {
    assignable_field_groups: ["authoring_subject"],
    lineage_copy: {
      contract_id: "dotlineform_processing_to_analysis_works",
      target: { scope: "analysis", sub_scope: "works" },
      action_label: "Copy to Analysis",
      modal_title: "Copy to analysis/works"
    }
  }
});
assert.deepEqual(descriptor.capabilities.lineageCopy, {
  contractId: "dotlineform_processing_to_analysis_works",
  target: { scope: "analysis", sub_scope: "works" },
  actionLabel: "Copy to Analysis",
  modalTitle: "Copy to analysis/works"
});

console.log("docs_viewer_processing_working_collection_contract: passed");
