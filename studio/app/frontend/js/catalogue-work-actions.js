import { saveNewWorkBatch } from "./catalogue-work-batch.js";
import { firstCatalogueValidationMessage } from "./catalogue-editor-message-controller.js";
import { catalogueSaveCompletionError, catalogueSavedActionError } from "./catalogue-save-result.js";
import { applyCatalogueDelete, createCatalogueWork, saveCatalogueBulkRecords, saveCatalogueWork } from "./catalogue-editor-service-client.js";

import { confirmCatalogueActionModal } from "./catalogue-editor-action-modals.js";
import {
  setEmptySearchMode,
  setLoadedBulkWorks,
  setLoadedWorkRecord
} from "./catalogue-work-route-state.js";
import {
  WORK_DOWNLOAD_FIELDS as DOWNLOAD_FIELDS,
  WORK_LINK_FIELDS as LINK_FIELDS
} from "./catalogue-editor-embedded-items.js";

import { BULK_WORK_METADATA_FIELDS, buildCreateWorkPayload, buildWorkRecordFromDraft, normalizeText, normalizeWorkId, suggestNextWorkId } from "./catalogue-work-fields.js";
import {
  applyBulkWorkRecordMutations,
  applyWorkRecordMutation
} from "./catalogue-work-action-records.js";


function setTextWithState(context, node, text, state = "") {
  context.setTextWithState(node, text, state);
}

function workMediaRequest(state) {
  return {
    regenerateImage: state.regenerateImage,
    pendingAttachments: state.pendingAttachments,
    attachmentLimits: state.attachmentLimits
  };
}

/** Bulk patches carry only explicit edits; control serialization remains UI-owned. */
function buildPayload(state) {
  if (state.mode !== "bulk") return {
    work_id: state.currentWorkId,
    record: buildWorkRecordFromDraft(state.draft, { downloadFields: DOWNLOAD_FIELDS, linkFields: LINK_FIELDS }),
    gallery_ids: state.draft.gallery_ids.slice()
  };
  const payload = {
    kind: "works", ids: state.bulkWorkIds.slice()
  };
  const setFields = {};
  for (const field of BULK_WORK_METADATA_FIELDS) {
    if (!state.bulkTouchedFields.has(field.key)) continue;
    const value = normalizeText(state.draft[field.key]);
    setFields[field.key] = value ? (field.type === "number" ? Number(value) : value) : null;
  }
  if (Object.keys(setFields).length) payload.set_fields = setFields;
  if (state.bulkTouchedFields.has("gallery_ids")) {
    payload.gallery_ids = state.draft.gallery_ids.slice();
  }
  return payload;
}

/** Capture removed memberships from saved records before adopting the Save response. */
function galleryIdsRemovedBySave(state, payload) {
  const removed = new Set();
  if (payload.gallery_ids === undefined) return removed;
  const retained = new Set(payload.gallery_ids);
  for (const workId of payload.ids || [payload.work_id]) {
    for (const galleryId of state.workSearchById.get(workId).gallery_ids) {
      if (!retained.has(galleryId)) removed.add(galleryId);
    }
  }
  return removed;
}

/** Find newly empty Galleries in the complete saved Work map after successful Save. */
function newlyEmptyGalleryIds(state, removed) {
  if (!removed.size) return [];
  for (const work of state.workSearchById.values()) {
    for (const galleryId of work.gallery_ids) removed.delete(galleryId);
    if (!removed.size) return [];
  }
  return Array.from(removed).sort();
}


export async function saveCurrentWork(state, context) {
  if (state.imagePreview?.status === "pending") return;
  if (!context.draftHasChanges()) return;
  if (state.mode === "new") {
    await saveNewWork(state, context);
    return;
  }
  if (state.mode === "bulk") {
    if (!state.bulkWorkIds.length) return;
  } else if (!state.currentRecord) {
    return;
  }
  const errors = context.validateDraft();
  context.updateFieldMessages(errors);
  if (errors.size > 0) {
    const message = firstCatalogueValidationMessage(errors);
    if (message) setTextWithState(context, state.statusNode, message, "error");
    context.updateEditorState();
    return;
  }

  state.isSaving = true;
  context.updateEditorState();
  setTextWithState(
    context,
    state.statusNode,
    "Saving source record…"
  );
  setTextWithState(context, state.resultNode, "");

  let savedResponse = null;
  let cleanupGalleryIds = [];
  try {
    const payload = buildPayload(state);
    const removedGalleryIds = galleryIdsRemovedBySave(state, payload);
    if (state.mode === "bulk") {
      const response = await saveCatalogueBulkRecords(payload);
      savedResponse = response;
      context.noteCatalogueSaved(response);
      const changedRecords = Array.isArray(response && response.records) ? response.records : [];
      if (changedRecords.map(item => item.work_id).sort().join(",") !== state.bulkWorkIds.slice().sort().join(",")) {
        throw new Error("Saved Work response does not match the selected Works.");
      }
      applyBulkWorkRecordMutations(state, changedRecords);
      setLoadedBulkWorks(state, state.bulkWorkIds, state.bulkRecords, state.bulkRecordHashes, context.workRouteStateOptions({keepResult: true}));
      const completionError = catalogueSaveCompletionError(response);
      setTextWithState(context, state.resultNode, completionError || "Saved " + (response.changed_count || 0) + " work records.", completionError ? "error" : "success");
      if (!completionError) cleanupGalleryIds = newlyEmptyGalleryIds(state, removedGalleryIds);
    } else {
      const response = await saveCatalogueWork(payload, workMediaRequest(state));
      savedResponse = response;
      context.noteCatalogueSaved(response);
      const record = response && response.record && typeof response.record === "object" && Array.isArray(response.gallery_ids)
        ? { ...response.record, gallery_ids: response.gallery_ids }
        : null;
      if (!record) {
        throw new Error("save response missing record");
      }
      applyWorkRecordMutation(state, {
        workId: state.currentWorkId,
        record,
        recordHash: response.record_hash
      });
      const completionError = catalogueSaveCompletionError(response);
      setLoadedWorkRecord(state, state.currentWorkId, record, context.workRouteStateOptions({
        recordHash: response.record_hash,
        keepResult: true,
        preserveMediaIntent: response.media?.status !== "completed"
      }));
      setTextWithState(context, state.resultNode, completionError || "Saved.", completionError ? "error" : "success");
      if (!completionError) cleanupGalleryIds = newlyEmptyGalleryIds(state, removedGalleryIds);
    }
  } catch (error) {
    const message = catalogueSavedActionError(savedResponse, error)
      || `Source save failed. ${normalizeText(error && error.message)}`.trim();
    setTextWithState(context, state.statusNode, message, "error");
  } finally {
    state.isSaving = false;
    context.updateEditorState();
  }
  if (cleanupGalleryIds.length) await context.offerEmptyGalleryCleanup(cleanupGalleryIds);
}

export async function saveNewWork(state, context) {
  if (state.mode !== "new") return;
  if (state.pendingWorkBatch) {
    await saveNewWorkBatch(state, context);
    return;
  }
  const errors = context.validateDraft();
  context.updateFieldMessages(errors);
  if (errors.size > 0) {
    const message = firstCatalogueValidationMessage(errors);
    if (message) setTextWithState(context, state.statusNode, message, "error");
    context.updateEditorState();
    return;
  }

  state.isSaving = true;
  context.updateEditorState();
  setTextWithState(context, state.statusNode, "Saving new work…");
  setTextWithState(context, state.resultNode, "");

  let savedResponse = null;
  try {
    const createPayload = buildCreateWorkPayload(state.draft);
    const response = await createCatalogueWork(createPayload, workMediaRequest(state));
    savedResponse = response;
    context.noteCatalogueSaved(response);
    const workId = normalizeWorkId(response && response.work_id);
    const record = response && response.record && typeof response.record === "object" && Array.isArray(response.gallery_ids)
      ? { ...response.record, gallery_ids: response.gallery_ids } : null;
    if (workId !== createPayload.work_id || !record) {
      throw new Error("create response does not match the new Work");
    }
    applyWorkRecordMutation(state, { workId, record, recordHash: response.record_hash });
    state.nextSuggestedWorkId = suggestNextWorkId([...state.workSearchById.values()]);
    const completionError = catalogueSaveCompletionError(response);
    setLoadedWorkRecord(state, workId, record, context.workRouteStateOptions({
      recordHash: response.record_hash,
      keepResult: true,
      preserveMediaIntent: response.media?.status !== "completed"
    }));
    setTextWithState(context, state.resultNode, `Saved work ${workId}.`, "success");
    setTextWithState(context, state.statusNode, `Saved work ${workId}.`, "success");
    if (completionError) {
      setTextWithState(context, state.resultNode, completionError, "error");
      setTextWithState(context, state.statusNode, "", "");
    }
  } catch (error) {
    setTextWithState(context, state.statusNode, catalogueSavedActionError(savedResponse, error) || `Work save failed. ${normalizeText(error && error.message)}`.trim(), "error");
  } finally {
    state.isSaving = false;
    context.updateEditorState();
  }
}


/** Confirm the selected identities once, then delete current canonical Works and memberships. */
export async function deleteCurrentWork(state, context) {
  const workIds = state.mode === "bulk" ? state.bulkWorkIds.slice()
    : state.currentRecord ? [state.currentWorkId] : [];
  if (!workIds.length || !state.serverAvailable || state.isSaving || state.isBuilding
    || state.isDeleting || state.isEditingDefinition) return;
  let savedResponse = null;
  try {
    const summary = workIds.length === 1
      ? `Delete Work ${workIds[0]} and its Gallery memberships?`
      : `Delete these ${workIds.length} Works and their Gallery memberships?\n${workIds.join(", ")}`;
    const confirmed = await confirmCatalogueActionModal(state, {
      title: "Confirm delete",
      message: `${summary}\nTheir Catalogue images and files will be removed. Project originals and Series/Gallery definitions will be kept.`,
      primaryLabel: workIds.length === 1 ? "Delete"
        : `Delete ${workIds.length} Works`,
      cancelLabel: "Cancel",
      defaultAction: "cancel",
      restoreFocus: state.deleteButton
    });
    if (!confirmed) {
      setTextWithState(context, state.statusNode, "Delete cancelled.");
      return;
    }
    state.isDeleting = true;
    context.updateEditorState();
    setTextWithState(context, state.resultNode, "");
    setTextWithState(context, state.statusNode, "Deleting selected Works…");
    const response = await applyCatalogueDelete({ kind: "works", ids: workIds });
    savedResponse = response;
    context.noteCatalogueSaved(response);
    if (response.kind !== "works" || response.deleted !== true || !Array.isArray(response.ids)
      || response.ids.some(id => typeof id !== "string")
      || response.ids.length !== workIds.length
      || response.ids.slice().sort().join(",") !== workIds.slice().sort().join(",")) {
      throw new Error("Delete response does not match the selected Works.");
    }
    for (const workId of workIds) {
      state.sourceWorkRecordsById.delete(workId);
      state.workSearchById.delete(workId);
    }
    state.nextSuggestedWorkId = suggestNextWorkId([...state.workSearchById.values()]);
    setEmptySearchMode(state, context.workRouteStateOptions());
    const completionError = catalogueSaveCompletionError(response);
    const success = workIds.length === 1
      ? `Deleted work ${workIds[0]}.`
      : `Deleted ${workIds.length} Works.`;
    setTextWithState(context, state.resultNode, completionError || success, completionError ? "error" : "success");
  } catch (error) {
    const message = catalogueSavedActionError(savedResponse, error)
      || `Source delete failed. ${normalizeText(error && error.message)}`.trim();
    setTextWithState(context, state.statusNode, message, "error");
  } finally {
    state.isDeleting = false;
    context.updateEditorState();
  }
}
