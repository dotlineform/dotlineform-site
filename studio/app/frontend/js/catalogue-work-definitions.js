import { openWorkGalleryModal } from "./catalogue-work-gallery-modal.js";
import { openWorkSeriesTitleModal } from "./catalogue-work-series-modal.js";
import { catalogueOutputError, catalogueSavedActionError } from "./catalogue-output-result.js";
import { syncWorkRouteBusyState } from "./catalogue-work-route-state.js";

function removeGalleryMembership(record, galleryId) {
  if (Array.isArray(record?.gallery_ids)) {
    record.gallery_ids = record.gallery_ids.filter(id => id !== galleryId);
  }
}

function applyGalleryResult(state, response) {
  const id = response.gallery_id;
  if (response.deleted) {
    state.galleriesById.delete(id);
    // Remove only this identity from saved baselines and unsaved drafts. Other
    // edits and stale-revision protection remain owned by ordinary Work Save.
    for (const record of [state.draft, state.baselineDraft, state.currentRecord, state.currentLookup,
      state.currentLookup?.work, ...state.workSearchById.values(),
      ...state.sourceWorkRecordsById.values(), ...state.bulkRecords.values()]) {
      removeGalleryMembership(record, id);
    }
  } else {
    state.galleriesById.set(id, response.record);
    if (response.created) {
      state.draft.gallery_ids = [...(state.draft.gallery_ids || []), id].sort();
      if (state.mode === "bulk") state.bulkTouchedFields.add("gallery_ids");
    }
  }
}

function applySeriesResult(state, response) {
  const id = response.deleted ? response.id : response.series_id;
  if (response.deleted) {
    state.seriesById.delete(id);
    if (state.draft.series_id === id) state.draft.series_id = "";
  } else {
    state.seriesById.set(id, { ...response.record, record_hash: response.record_hash });
    if (response.created && state.mode !== "bulk") state.draft.series_id = id;
  }
}

function validateResponse(kind, requestedId, response) {
  const key = kind === "Gallery" ? "gallery_id" : "series_id";
  const id = kind === "Series" && response?.deleted ? response.id : response?.[key];
  if (!response?.ok || typeof id !== "string" || !id || (requestedId && id !== requestedId)
    || (!requestedId && !response.created)
    || (response.deleted && kind === "Series" && response.kind !== "series")
    || (!response.deleted && (response.record?.[key] !== id
      || typeof response.record.title !== "string" || !response.record_hash))) {
    throw new Error(`${kind} response is missing its exact record or revision.`);
  }
}

/** Keep the Work draft while a shared definition saves; refresh saved labels and membership baselines. */
export async function editWorkDefinition(state, { kind, id = "", restoreFocus, refresh }) {
  if (state.isEditingDefinition || state.isSaving || state.isBuilding || state.isDeleting || !state.serverAvailable) return null;
  state.messageController.clearActionMessages();
  state.isEditingDefinition = true;
  const panels = [...state.root.children].filter(node => node !== state.modalHost);
  const previousInert = panels.map(node => node.inert);
  const lockPanels = () => panels.forEach(node => { node.inert = true; });
  lockPanels();
  let result;
  let response = null;
  let errorMessage = "";
  try {
    const onBusyChange = busy => {
      state.isSaving = busy;
      state.root.dataset.workSaving = String(busy);
      syncWorkRouteBusyState(state);
    };
    const modalOptions = { restoreFocus, onBusyChange };
    result = kind === "Gallery"
      ? await openWorkGalleryModal(state, { ...modalOptions, galleryId: id })
      : await openWorkSeriesTitleModal(state, { ...modalOptions, seriesId: id });
    if (result.confirmed) {
      response = result.response;
      validateResponse(kind, id, response);
      if (kind === "Gallery") applyGalleryResult(state, response);
      else applySeriesResult(state, response);
      errorMessage = catalogueOutputError(response);
    }
  } catch (error) {
    errorMessage = catalogueSavedActionError(response, error) || error.message;
    result = null;
  } finally {
    state.isEditingDefinition = false;
    state.isSaving = false;
    panels.forEach((node, index) => { node.inert = previousInert[index]; });
    try {
      refresh();
      state.seriesBrowser?.refresh();
    } catch (error) {
      errorMessage = catalogueSavedActionError(response, error) || error.message;
      result = null;
    }
    restoreFocus?.focus({ preventScroll: true });
  }
  if (errorMessage) state.messageController.setActionTextWithState(state.statusNode, errorMessage, "error");
  return result;
}
