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

import { buildCreateWorkPayload, buildWorkRecordFromDraft, normalizeText, normalizeWorkId, suggestNextWorkId } from "./catalogue-work-fields.js";
import {
  applyBulkWorkRecordMutations,
  applyWorkRecordMutation
} from "./catalogue-work-action-records.js";


function t(state, context, key, fallback, tokens = null) {
  return context.text(key, fallback, tokens);
}

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

function buildPayload(state) {
  const record = buildWorkRecordFromDraft(state.draft, { downloadFields: DOWNLOAD_FIELDS, linkFields: LINK_FIELDS });
  if (state.mode !== "bulk") return {
    work_id: state.currentWorkId,
    expected_record_hash: state.currentRecordHash,
    record,
    gallery_ids: state.draft.gallery_ids.slice(),
    expected_gallery_ids: state.baselineDraft.gallery_ids.slice()
  };
  const payload = {
    kind: "works", ids: state.bulkWorkIds.slice(),
    expected_record_hashes: Object.fromEntries(state.bulkRecordHashes)
  };
  if (state.bulkTouchedFields.has("gallery_ids")) {
    payload.gallery_ids = state.draft.gallery_ids.slice();
    payload.expected_gallery_ids_by_work = Object.fromEntries(state.bulkWorkIds.map(id => [id, state.bulkRecords.get(id).gallery_ids.slice()]));
  }
  return payload;
}

function newlyEmptyGalleryIds(response) {
  const ids = response.newly_empty_gallery_ids;
  if (!Array.isArray(ids) || ids.some(id => typeof id !== "string" || !id) || new Set(ids).size !== ids.length) {
    throw new Error("Saved Work response is missing distinct newly empty Gallery IDs.");
  }
  return ids;
}


export async function saveCurrentWork(state, context) {
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
    t(state, context, "save_status_saving", "Saving source record…")
  );
  setTextWithState(context, state.resultNode, "");

  let savedResponse = null;
  let cleanupGalleryIds = [];
  try {
    if (state.mode === "bulk") {
      const response = await saveCatalogueBulkRecords(buildPayload(state));
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
      if (!completionError) cleanupGalleryIds = newlyEmptyGalleryIds(response);
    } else {
      const payload = buildPayload(state);
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
      state.currentLookup = await context.loadWorkLookupRecord(state.currentWorkId);
      if (!completionError) cleanupGalleryIds = newlyEmptyGalleryIds(response);
    }
  } catch (error) {
    const isConflict = Number(error && error.status) === 409;
    const message = catalogueSavedActionError(savedResponse, error) || (isConflict
      ? t(state, context, "save_status_conflict", "Source record changed since this page loaded. Reload the work before saving again.")
      : `${t(state, context, "save_status_failed", "Source save failed.")} ${normalizeText(error && error.message)}`.trim());
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
  setTextWithState(context, state.statusNode, t(state, context, "new_save_status_saving", "Saving new work…"));
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
    const completionError = catalogueSaveCompletionError(response);
    setLoadedWorkRecord(state, workId, record, context.workRouteStateOptions({
      recordHash: response.record_hash,
      keepResult: true,
      preserveMediaIntent: response.media?.status !== "completed"
    }));
    setTextWithState(context, state.resultNode, t(state, context, "new_save_result_success", "Saved work {work_id}.", { work_id: workId }), "success");
    setTextWithState(context, state.statusNode, t(state, context, "new_save_status_success", "Saved work {work_id}.", { work_id: workId }), "success");
    if (completionError) {
      setTextWithState(context, state.resultNode, completionError, "error");
      setTextWithState(context, state.statusNode, "", "");
    }
    state.currentLookup = await context.loadWorkLookupRecord(workId);
  } catch (error) {
    setTextWithState(context, state.statusNode, catalogueSavedActionError(savedResponse, error) || `${t(state, context, "new_save_status_failed", "Work save failed.")} ${normalizeText(error && error.message)}`.trim(), "error");
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
    const tokens = { count: String(workIds.length), work_ids: workIds.join(", "), work_id: workIds[0] };
    const summary = workIds.length === 1
      ? t(state, context, "delete_work_confirm", "Delete Work {work_id} and its Gallery memberships?", tokens)
      : t(state, context, "delete_works_confirm", "Delete these {count} Works and their Gallery memberships?\n{work_ids}", tokens);
    const confirmed = await confirmCatalogueActionModal(state, {
      title: t(state, context, "delete_confirm_title", "Confirm delete"),
      message: `${summary}\n${t(state, context, "delete_media_retained", "Shared images and files will be kept.")}`,
      primaryLabel: workIds.length === 1 ? t(state, context, "delete_confirm_button", "Delete")
        : t(state, context, "delete_works_confirm_button", "Delete {count} Works", tokens),
      cancelLabel: t(state, context, "confirm_cancel_button", "Cancel"),
      defaultAction: "cancel",
      restoreFocus: state.deleteButton
    });
    if (!confirmed) {
      setTextWithState(context, state.statusNode, t(state, context, "delete_status_cancelled", "Delete cancelled."));
      return;
    }
    state.isDeleting = true;
    context.updateEditorState();
    setTextWithState(context, state.resultNode, "");
    setTextWithState(context, state.statusNode, t(state, context, "delete_works_status_running", "Deleting selected Works…"));
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
      ? t(state, context, "delete_result_success", "Deleted work {work_id}.", tokens)
      : t(state, context, "delete_works_result_success", "Deleted {count} Works.", tokens);
    setTextWithState(context, state.resultNode, completionError || success, completionError ? "error" : "success");
  } catch (error) {
    const message = catalogueSavedActionError(savedResponse, error)
      || `${t(state, context, "delete_status_failed", "Source delete failed.")} ${normalizeText(error && error.message)}`.trim();
    setTextWithState(context, state.statusNode, message, "error");
  } finally {
    state.isDeleting = false;
    context.updateEditorState();
  }
}
