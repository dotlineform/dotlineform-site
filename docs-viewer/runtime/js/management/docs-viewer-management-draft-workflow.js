import { readManagedDocMetadata, setManagedDocDraft } from "./docs-viewer-management-client.js";
import { managedDocumentTargetsEqual, normalizeManagedDocumentTarget } from "./docs-viewer-management-document-target.js";

/** Save the exact source field; watcher completion drives the later index reload. */
export async function toggleManagedDocDraft(target, options) {
  const normalized = normalizeManagedDocumentTarget(target);
  if (normalized.stage !== "working") {
    throw new Error("Draft readiness is available only in Working.");
  }
  const metadata = await readManagedDocMetadata(normalized, options.clientOptions);
  const metadataTarget = { stage: metadata.stage, doc_id: metadata.doc_id,
    ...(Object.prototype.hasOwnProperty.call(metadata, "collection") ? { collection: metadata.collection } : {}) };
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
  options.onSaved(normalized, response);
  return response;
}
