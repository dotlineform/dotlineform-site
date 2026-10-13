import { setManagedDocDraft } from "./docs-viewer-management-client.js";
import { managedDocumentTargetsEqual, normalizeManagedDocumentTarget } from "./docs-viewer-management-document-target.js";
/** Save the intended readiness state and await its document generation. */
export async function toggleManagedDocDraft(target, draft, options) {
  const normalized = normalizeManagedDocumentTarget(target);
  if (typeof draft !== "boolean") {
    throw new Error("Draft readiness requires the intended boolean state.");
  }
  let response;
  try {
    response = await setManagedDocDraft(normalized, {
      draft: draft
    }, options.clientOptions);
  } catch (error) {
    const partial = error.payload;
    if (partial && partial.source_saved === true && managedDocumentTargetsEqual(partial.target, normalized)
      && partial.record && partial.record.draft === draft) {
      try { await options.onSaved(normalized, partial); }
      catch (projectionError) { error.message += " " + projectionError.message; }
    }
    throw error;
  }
  if (!response || response.ok !== true || !managedDocumentTargetsEqual(response.target, normalized)
    || response.source_saved !== true || response.generation_complete !== true
    || !response.record || response.record.draft !== draft) {
    throw new Error("Draft readiness response did not match the requested document.");
  }
  await options.onSaved(normalized, response);
  return response;
}
