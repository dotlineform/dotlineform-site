import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";


const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");
const workingSubjects = await import(pathToFileURL(path.join(
  repoRoot,
  "docs-viewer/runtime/js/management/docs-viewer-management-subscope-dotlineform-projects.js"
)));

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
assert.equal(processingRoot.dataset.workingSubjectColumns, "subject");
assert.equal(projectsContribution.renderListToolbar, undefined);
assert.equal(processingContribution.renderListToolbar, undefined);

console.log("docs_viewer_processing_working_collection_contract: passed");
