import { confirmCatalogueActionModal } from "./catalogue-editor-action-modals.js";
import { extractCatalogueActionPreview, getCataloguePreviewBlocker } from "./catalogue-editor-action-workflow.js";
import { applyCatalogueDelete, previewCatalogueDelete } from "./catalogue-editor-service-client.js";

/** Confirm an empty Series deletion; the service rechecks membership and revision on apply. */
export async function deleteEmptyWorkSeries(state, { seriesId, restoreFocus }) {
  const record = state.seriesById.get(seriesId);
  if (!record?.record_hash) throw new Error("Reload the Series before deleting it.");
  const request = { kind: "series", series_id: seriesId, expected_record_hash: record.record_hash };
  const preview = extractCatalogueActionPreview(await previewCatalogueDelete(request));
  if (preview?.kind !== "series" || preview.id !== seriesId) {
    throw new Error("Delete preview does not match the selected Series.");
  }
  const blocker = getCataloguePreviewBlocker(preview, {
    includeValidationErrors: true, fallback: "Series deletion is blocked."
  });
  if (blocker) throw new Error(blocker);
  if (!Array.isArray(preview.affected?.works) || preview.affected.works.length) {
    throw new Error("Only Series with no member Works can be deleted.");
  }
  const confirmed = await confirmCatalogueActionModal(state, {
    title: "Delete Series?",
    message: `Delete “${preview.record.title}” (${seriesId})? This Series has no member Works.`,
    primaryLabel: "Delete", cancelLabel: "Cancel", defaultAction: "cancel", restoreFocus
  });
  if (!confirmed) return null;
  return applyCatalogueDelete(request);
}
