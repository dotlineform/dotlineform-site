import { readManagedDocMetadata, setManagedDocDraft } from "./docs-viewer-management-client.js";
import { managedDocumentTargetsEqual, normalizeManagedDocumentTarget } from "./docs-viewer-management-document-target.js";
/** Save the intended readiness state and await its document generation. */
export async function toggleManagedDocDraft(target, draft, options) {
  const normalized = normalizeManagedDocumentTarget(target);
  if (typeof draft !== "boolean") {
    throw new Error("Draft readiness requires the intended boolean state.");
  }
  const metadata = await readManagedDocMetadata(normalized, {
    ...options.clientOptions, cache: "no-store"
  });
  const metadataTarget = {  doc_id: metadata.doc_id,
    ...(Object.prototype.hasOwnProperty.call(metadata, "collection") ? { collection: metadata.collection } : {}) };
  if (!managedDocumentTargetsEqual(metadataTarget, normalized)
    || !metadata.record || typeof metadata.record.draft !== "boolean"
    || !/^sha256:[0-9a-f]{64}$/.test(metadata.source_revision || "")) {
    throw new Error("Draft readiness did not match the requested document.");
  }
  let response;
  try {
    response = await setManagedDocDraft(normalized, {
      draft: draft, source_revision: metadata.source_revision
    }, options.clientOptions);
  } catch (error) {
    const partial = error.payload;
    if (partial && partial.source_saved === true && managedDocumentTargetsEqual(partial.target, normalized)
      && partial.record && partial.record.draft === draft) options.onSaved(normalized, partial);
    throw error;
  }
  if (!response || response.ok !== true || !managedDocumentTargetsEqual(response.target, normalized)
    || !response.record || response.record.draft !== draft) {
    throw new Error("Draft readiness response did not match the requested document.");
  }
  options.onSaved(normalized, response);
  return response;
}
