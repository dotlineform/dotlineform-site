import { createCatalogueWorkBatch } from "./catalogue-editor-service-client.js";
import { firstCatalogueValidationMessage } from "./catalogue-editor-message-controller.js";
import { catalogueSaveCompletionError, catalogueSavedActionError } from "./catalogue-save-result.js";
import { applyWorkRecordMutation } from "./catalogue-work-action-records.js";
import { buildWorkRecordFromDraft, suggestNextWorkId } from "./catalogue-work-fields.js";
import { setEmptySearchMode, setLoadedWorkRecord } from "./catalogue-work-route-state.js";
import { WORK_DOWNLOAD_FIELDS, WORK_LINK_FIELDS } from "./catalogue-editor-embedded-items.js";

/**
 * @typedef {Object} PendingWorkBatch
 * @property {string} media_source_id Exact configured source identity.
 * @property {string} project_folder One source-relative project folder.
 * @property {string} project_subfolder One direct subfolder.
 * @property {string[]} filenames Complete confirmed picker list, retained through Save.
 */

function batchPayload(state) {
  const record = buildWorkRecordFromDraft(state.draft, {
    downloadFields: WORK_DOWNLOAD_FIELDS, linkFields: WORK_LINK_FIELDS
  });
  for (const key of ["title", "media_source_id", "project_folder", "project_subfolder", "project_filename"]) delete record[key];
  return {
    record, gallery_ids: state.draft.gallery_ids.slice(),
    folder_selection: { ...state.pendingWorkBatch, filenames: state.pendingWorkBatch.filenames.slice() }
  };
}

/**
 * Create one awaited batch and reconcile every saved Work into live search/list
 * state. Validation retains the draft; canonical success releases creation intent
 * even if local media or later editor adoption fails. Never replay automatically.
 */
export async function saveNewWorkBatch(state, context) {
  if (state.mode !== "new" || !state.pendingWorkBatch || state.isSaving) return;
  const errors = context.validateDraft();
  context.updateFieldMessages(errors);
  if (errors.size) {
    const message = firstCatalogueValidationMessage(errors);
    if (message) context.setTextWithState(state.statusNode, message, "error");
    context.updateEditorState();
    return;
  }
  state.isSaving = true;
  context.updateEditorState();
  context.setTextWithState(state.statusNode, "Saving new Works…");
  context.setTextWithState(state.resultNode, "");
  let savedResponse = null;
  try {
    const request = batchPayload(state);
    const response = await createCatalogueWorkBatch(request);
    savedResponse = response;
    // Release batch creation before any fallible editor completion.
    state.pendingWorkBatch = null;
    context.noteCatalogueSaved(response);
    const ids = response.created_ids;
    const records = response.records;
    if (!Array.isArray(ids) || !ids.length || ids.length !== request.folder_selection.filenames.length
      || ids.some(id => typeof id !== "string" || !/^\d{5}$/.test(id)) || new Set(ids).size !== ids.length
      || !Array.isArray(records) || records.length !== ids.length
      || records.some((item, index) => item.work_id !== ids[index] || !item.record || !item.record_hash || !Array.isArray(item.gallery_ids))
      || records.map(item => item.record.project_filename).sort().join("\n") !== request.folder_selection.filenames.slice().sort().join("\n")) {
      throw new Error("Batch create response does not match the confirmed images.");
    }
    for (const item of records) {
      applyWorkRecordMutation(state, {
        workId: item.work_id, record: { ...item.record, gallery_ids: item.gallery_ids }, recordHash: item.record_hash
      });
    }
    state.nextSuggestedWorkId = suggestNextWorkId([...state.workSearchById.values()]);
    const first = records[0];
    const completionError = catalogueSaveCompletionError(response);
    setLoadedWorkRecord(state, first.work_id, { ...first.record, gallery_ids: first.gallery_ids }, context.workRouteStateOptions({
      recordHash: first.record_hash, keepResult: true
    }));
    const message = completionError || `Saved ${ids.length} Works.`;
    context.setTextWithState(state.resultNode, message, completionError ? "error" : "success");
    context.setTextWithState(state.statusNode, "");
    state.currentLookup = await context.loadWorkLookupRecord(first.work_id);
  } catch (error) {
    if (savedResponse?.saved && state.mode === "new") {
      setEmptySearchMode(state, context.workRouteStateOptions({ keepResult: true }));
    }
    const failure = catalogueSavedActionError(savedResponse, error) || (error.status
      ? `Work save failed. ${error.message}`
      : `Save outcome could not be confirmed. Check the canonical Works before saving this batch again. ${error.message}`);
    context.setTextWithState(state.statusNode, failure, "error");
  } finally {
    state.isSaving = false;
    context.updateEditorState();
  }
}
