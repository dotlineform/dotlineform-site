import { buildStudioRouteUrl } from "./studio-config.js";
import { catalogueOutputError } from "./catalogue-output-result.js";
import { applyCatalogueDelete, createCatalogueWork, previewCatalogueDelete, saveCatalogueBulkRecords, saveCatalogueWork } from "./catalogue-editor-service-client.js";

import { formatCatalogueDeletePreview } from "./catalogue-editor-modal-formatters.js";
import { confirmCatalogueActionModal } from "./catalogue-editor-action-modals.js";
import { extractCatalogueActionPreview, getCataloguePreviewBlocker } from "./catalogue-editor-action-workflow.js";
import {
  setLoadedBulkWorks,
  setLoadedWorkRecord
} from "./catalogue-work-route-state.js";
import {
  WORK_DOWNLOAD_FIELDS as DOWNLOAD_FIELDS,
  WORK_LINK_FIELDS as LINK_FIELDS
} from "./catalogue-editor-embedded-items.js";

import { WORK_EDITABLE_FIELDS as EDITABLE_FIELDS, buildCreateWorkPayload, buildWorkRecordFromDraft, normalizeText, normalizeWorkId } from "./catalogue-work-fields.js";
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


function buildPayload(state) {
  const record = buildWorkRecordFromDraft(state.draft, { downloadFields: DOWNLOAD_FIELDS, linkFields: LINK_FIELDS });
  if (state.mode !== "bulk") return {work_id: state.currentWorkId, expected_record_hash: state.currentRecordHash, record};
  const setFields = {};
  for (const field of EDITABLE_FIELDS) {
    if (state.bulkTouchedFields.has(field.key)) setFields[field.key] = record[field.key] ?? null;
  }
  return {kind: "works", ids: state.bulkWorkIds.slice(), expected_record_hashes: Object.fromEntries(state.bulkRecordHashes), set_fields: setFields};
}


export async function saveCurrentWork(state, context) {
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
    setTextWithState(context, state.statusNode, t(state, context, "save_status_validation_error", "Fix validation errors before saving."), "error");
    context.updateEditorState();
    return;
  }

  state.isSaving = true;
  state.saveButton.disabled = true;
  setTextWithState(
    context,
    state.statusNode,
    t(state, context, "save_status_saving", "Saving source record…")
  );
  setTextWithState(context, state.resultNode, "");

  try {
    if (state.mode === "bulk") {
      const response = await saveCatalogueBulkRecords(buildPayload(state));
      const changedRecords = Array.isArray(response && response.records) ? response.records : [];
      applyBulkWorkRecordMutations(state, changedRecords);
      setLoadedBulkWorks(state, state.bulkWorkIds, state.bulkRecords, state.bulkRecordHashes, context.workRouteStateOptions({keepResult: true}));
      const outputError = catalogueOutputError(response);
      setTextWithState(context, state.resultNode, outputError || "Saved " + (response.changed_count || 0) + " work records and refreshed output.", outputError ? "error" : "success");
      return;
    }

    const payload = buildPayload(state);
    const response = await saveCatalogueWork(payload);
    const record = response && response.record && typeof response.record === "object" ? response.record : null;
    if (!record) {
      throw new Error("save response missing record");
    }
    applyWorkRecordMutation(state, {
      workId: state.currentWorkId,
      record,
      recordHash: response.record_hash
    });
    const lookup = await context.loadWorkLookupRecord(state.currentWorkId);
    const stagedPreviewVersion = state.mediaPreviewVersion;
    setLoadedWorkRecord(state, state.currentWorkId, record, context.workRouteStateOptions({
      recordHash: response.record_hash || normalizeText(lookup && lookup.record_hash) || "",
      keepResult: true,
      lookup
    }));
    state.mediaPreviewVersion = stagedPreviewVersion;
    const outputError = catalogueOutputError(response);
    setTextWithState(context, state.resultNode, outputError || "Saved and output refreshed.", outputError ? "error" : "success");
  } catch (error) {
    const isConflict = Number(error && error.status) === 409;
    const message = isConflict
      ? t(state, context, "save_status_conflict", "Source record changed since this page loaded. Reload the work before saving again.")
      : `${t(state, context, "save_status_failed", "Source save failed.")} ${normalizeText(error && error.message)}`.trim();
    setTextWithState(context, state.statusNode, message, "error");
  } finally {
    state.isSaving = false;
    context.updateEditorState();
  }
}

export async function saveNewWork(state, context) {
  if (state.mode !== "new") return;
  const errors = context.validateDraft();
  context.updateFieldMessages(errors);
  if (errors.size > 0) {
    const workIdError = errors.get("work_id") || "";
    setTextWithState(
      context,
      state.statusNode,
      workIdError || t(state, context, "new_save_status_validation_error", "Fix validation errors before saving the work."),
      "error"
    );
    context.updateEditorState();
    return;
  }

  state.isSaving = true;
  context.updateEditorState();
  setTextWithState(context, state.statusNode, t(state, context, "new_save_status_saving", "Saving new work…"));
  setTextWithState(context, state.resultNode, "");

  try {
    const createPayload = buildCreateWorkPayload(state.draft);
    const response = await createCatalogueWork(createPayload);
    const workId = normalizeWorkId(response && response.work_id);
    const record = response && response.record && typeof response.record === "object" ? response.record : null;
    if (!workId) {
      throw new Error("create response missing work id");
    }
    if (record) {
      applyWorkRecordMutation(state, {
        workId,
        record,
        recordHash: response.record_hash
      });
    }
    await context.openWorkById(workId);
    setTextWithState(context, state.resultNode, t(state, context, "new_save_result_success", "Saved work {work_id}.", { work_id: workId }), "success");
    setTextWithState(context, state.statusNode, t(state, context, "new_save_status_success", "Saved work {work_id}.", { work_id: workId }), "success");
    const outputError = catalogueOutputError(response);
    if (outputError) {
      setTextWithState(context, state.resultNode, outputError, "error");
      setTextWithState(context, state.statusNode, "", "");
    }
  } catch (error) {
    setTextWithState(context, state.statusNode, `${t(state, context, "new_save_status_failed", "Work save failed.")} ${normalizeText(error && error.message)}`.trim(), "error");
  } finally {
    state.isSaving = false;
    context.updateEditorState();
  }
}


export async function deleteCurrentWork(state, context) {
  if (!state.currentRecord || state.mode === "bulk" || !state.serverAvailable) return;
  state.isDeleting = true;
  context.updateEditorState();
  setTextWithState(context, state.statusNode, t(state, context, "delete_status_running", "Preparing delete preview…"));
  setTextWithState(context, state.resultNode, "");
  try {
    const request = {
      kind: "work",
      work_id: state.currentWorkId,
      expected_record_hash: state.currentRecordHash
    };
    const previewResponse = await previewCatalogueDelete(request);
    const preview = extractCatalogueActionPreview(previewResponse);
    const blocker = getCataloguePreviewBlocker(preview, {
      includeValidationErrors: true,
      fallback: t(state, context, "delete_status_blocked", "Delete is blocked.")
    });
    if (blocker) {
      state.isDeleting = false;
      context.updateEditorState();
      setTextWithState(context, state.statusNode, blocker, "error");
      return;
    }
    const summary = formatCatalogueDeletePreview(preview, {
      text: (key, fallback, tokens) => t(state, context, key, fallback, tokens),
      defaultText: "Delete this source record?"
    });
    state.isDeleting = false;
    context.updateEditorState();
    const confirmed = await confirmCatalogueActionModal(state, {
      title: t(state, context, "delete_confirm_title", "Confirm delete"),
      message: summary,
      primaryLabel: t(state, context, "delete_confirm_button", "Delete"),
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
    setTextWithState(context, state.statusNode, t(state, context, "delete_status_running", "Deleting source record…"));
    const response = await applyCatalogueDelete(request);
    const outputError = catalogueOutputError(response);
    if (outputError) {
      state.currentRecord = null;
      state.isDeleting = false;
      context.updateEditorState();
      setTextWithState(context, state.resultNode, outputError, "error");
      return;
    }
    window.location.assign(buildStudioRouteUrl(state.config, "catalogue_work_editor"));
  } catch (error) {
    const message = Number(error && error.status) === 409
      ? t(state, context, "delete_status_conflict", "Source record changed since this page loaded. Reload before deleting again.")
      : `${t(state, context, "delete_status_failed", "Source delete failed.")} ${normalizeText(error && error.message)}`.trim();
    state.isDeleting = false;
    context.updateEditorState();
    setTextWithState(context, state.statusNode, message, "error");
  }
}
