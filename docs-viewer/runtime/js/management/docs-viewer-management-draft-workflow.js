import { readManagedDocMetadata, setManagedDocDraft } from "./docs-viewer-management-client.js";
import { managedDocumentTargetsEqual, normalizeManagedDocumentTarget } from "./docs-viewer-management-document-target.js";

/** Await the exact revision-bound write and its visible document/index refresh. */
export async function toggleManagedDocDraft(target, options) {
  const normalized = normalizeManagedDocumentTarget(target);
  if (normalized.scope !== "analysis" || normalized.stage !== "working") {
    throw new Error("Draft readiness is available only in Analysis Working.");
  }
  const metadata = await readManagedDocMetadata(normalized, options.clientOptions);
  const metadataTarget = { scope: metadata.scope, stage: metadata.stage, doc_id: metadata.doc_id,
    ...(Object.prototype.hasOwnProperty.call(metadata, "sub_scope") ? { sub_scope: metadata.sub_scope } : {}) };
  if (!managedDocumentTargetsEqual(metadataTarget, normalized)
    || !metadata.record || typeof metadata.record.draft !== "boolean"
    || !/^sha256:[0-9a-f]{64}$/.test(metadata.source_revision || "")) {
    throw new Error("Draft readiness did not match the requested document.");
  }
  const draft = !metadata.record.draft;
  const response = await setManagedDocDraft(normalized, {
    draft: draft, source_revision: metadata.source_revision
  }, options.clientOptions);
  if (!response || response.ok !== true || !managedDocumentTargetsEqual(response.target, normalized)
    || !response.record || response.record.draft !== draft) {
    throw new Error("Draft readiness response did not match the requested document.");
  }
  await options.reloadTarget(normalized, response);
  return response;
}
