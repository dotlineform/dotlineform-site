import { buildStudioRouteUrl } from "./studio-config.js";
import { catalogueOutputError, catalogueSavedActionError } from "./catalogue-output-result.js";
import { applyCatalogueDelete, createCatalogueSeries, previewCatalogueDelete, saveCatalogueSeries } from "./catalogue-editor-service-client.js";

import { formatCatalogueDeletePreview } from "./catalogue-editor-modal-formatters.js";
import { confirmCatalogueActionModal } from "./catalogue-editor-action-modals.js";
import { extractCatalogueActionPreview, getCataloguePreviewBlocker } from "./catalogue-editor-action-workflow.js";

import {
  buildCreateSeriesPayload,
  buildSaveSeriesPayload,
  normalizeSeriesId,
  normalizeText,
  normalizeWorkId
} from "./catalogue-series-fields.js";
import { buildChangedSeriesWorkUpdates, buildSavedSeriesMembershipLookup } from "./catalogue-series-membership.js";

function t(state, context, key, fallback, tokens = null) {
  return context.text(key, fallback, tokens);
}

function setTextWithState(context, node, text, state = "") {
  context.setTextWithState(node, text, state);
}


function buildPayload(state, workUpdates) { return buildSaveSeriesPayload(state, workUpdates); }


export async function saveCurrentSeries(state, context) {
  if (state.mode === "new") {
    await createCurrentSeries(state, context);
    return;
  }
  if (!state.currentRecord) return;
  const errors = context.validateDraft();
  context.updateFieldMessages(errors);
  if (errors.size > 0) {
    setTextWithState(context, state.statusNode, t(state, context, "save_status_validation_error", "Fix validation errors before saving."), "error");
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
  try {
    const response = await saveCatalogueSeries(buildPayload(state, await buildChangedSeriesWorkUpdates(state)));
    savedResponse = response;
    const record = response && response.record && typeof response.record === "object" ? response.record : null;
    if (!record) throw new Error("save response missing record");
    state.seriesById.set(state.currentSeriesId, {
      series_id: state.currentSeriesId,
      title: normalizeText(record.title),
      record_hash: normalizeText(response.record_hash)
    });
    const workRecords = Array.isArray(response.work_records) ? response.work_records : [];
    workRecords.forEach((entry) => {
      if (!entry || typeof entry !== "object") return;
      const workId = normalizeWorkId(entry.work_id);
      const workRecord = entry.record;
      if (!workId || !workRecord || typeof workRecord !== "object") return;
      state.workSearchById.set(workId, {
        work_id: workId,
        title: normalizeText(workRecord.title),
        year_display: normalizeText(workRecord.year_display),
        series_id: normalizeText(workRecord.series_id),
        record_hash: entry.record_hash || state.workSearchById.get(workId)?.record_hash || ""
      });
    });
    const recordHash = normalizeText(response.record_hash);
    context.setLoadedSeries(state.currentSeriesId, record, {
      recordHash,
      keepResult: true,
      lookup: buildSavedSeriesMembershipLookup(state, record, recordHash)
    });
    const outputError = catalogueOutputError(response);
    setTextWithState(context, state.resultNode, outputError || "Saved and output refreshed.", outputError ? "error" : "success");
  } catch (error) {
    const isConflict = Number(error && error.status) === 409;
    const message = catalogueSavedActionError(savedResponse, error) || (isConflict
      ? t(state, context, "save_status_conflict", "Source record changed since this page loaded. Reload the series before saving again.")
      : `${t(state, context, "save_status_failed", "Source save failed.")} ${normalizeText(error && error.message)}`.trim());
    setTextWithState(context, state.statusNode, message, "error");
  } finally {
    state.isSaving = false;
    context.updateEditorState();
  }
}

export async function createCurrentSeries(state, context) {
  if (state.mode !== "new") return;
  state.draft.series_id = normalizeSeriesId(state.searchNode.value);
  const errors = context.validateDraft();
  context.updateFieldMessages(errors);
  if (errors.size > 0) {
    const seriesIdError = errors.get("series_id") || "";
    setTextWithState(
      context,
      state.statusNode,
      seriesIdError || t(state, context, "create_status_validation_error", "Fix validation errors before creating the series."),
      "error"
    );
    context.updateEditorState();
    return;
  }

  state.isSaving = true;
  context.updateEditorState();
  setTextWithState(context, state.statusNode, t(state, context, "create_status_saving", "Creating series..."));
  setTextWithState(context, state.resultNode, "");

  let savedResponse = null;
  try {
    const response = await createCatalogueSeries(buildCreateSeriesPayload(state.draft));
    savedResponse = response;
    const seriesId = normalizeSeriesId(response && response.series_id);
    const record = response && response.record && typeof response.record === "object" ? response.record : null;
    if (!seriesId) {
      throw new Error("create response missing series id");
    }
    if (record) {
      state.seriesById.set(seriesId, {
        series_id: seriesId,
        title: normalizeText(record.title),
        record_hash: normalizeText(response.record_hash)
      });
    }
    state.isSaving = false;
    context.syncRouteBusyState();
    await context.openSeriesById(seriesId);
    setTextWithState(context, state.resultNode, t(state, context, "create_result_success", "Created series {series_id}. Opening edit mode...", { series_id: seriesId }), "success");
    setTextWithState(context, state.statusNode, t(state, context, "create_status_success", "Created series {series_id}.", { series_id: seriesId }), "success");
    const outputError = catalogueOutputError(response);
    if (outputError) {
      setTextWithState(context, state.resultNode, outputError, "error");
      setTextWithState(context, state.statusNode, "", "");
    }
  } catch (error) {
    setTextWithState(context, state.statusNode, catalogueSavedActionError(savedResponse, error) || `${t(state, context, "create_status_failed", "Series create failed.")} ${normalizeText(error && error.message)}`.trim(), "error");
    state.isSaving = false;
    context.updateEditorState();
  }
}


export async function deleteCurrentSeries(state, context) {
  if (!state.currentRecord || !state.currentSeriesId || !state.serverAvailable) return;
  state.isDeleting = true;
  context.updateEditorState();
  setTextWithState(context, state.statusNode, t(state, context, "delete_status_running", "Preparing delete preview…"));
  setTextWithState(context, state.resultNode, "");
  let savedResponse = null;
  try {
    const request = {
      kind: "series",
      series_id: state.currentSeriesId,
      expected_record_hash: state.currentRecordHash
    };
    const previewResponse = await previewCatalogueDelete(request);
    const preview = extractCatalogueActionPreview(previewResponse);
    const blocker = getCataloguePreviewBlocker(preview, {
      includeValidationErrors: true,
      fallback: t(state, context, "delete_status_blocked", "Delete is blocked.")
    });
    if (blocker) {
      setTextWithState(context, state.statusNode, blocker, "error");
      state.isDeleting = false;
      context.updateEditorState();
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
      state.isDeleting = false;
      context.updateEditorState();
      return;
    }
    state.isDeleting = true;
    context.updateEditorState();
    setTextWithState(context, state.statusNode, t(state, context, "delete_status_running", "Deleting source record…"));
    const response = await applyCatalogueDelete(request);
    savedResponse = response;
    const outputError = catalogueOutputError(response);
    if (outputError) {
      state.currentRecord = null;
      state.isDeleting = false;
      context.updateEditorState();
      setTextWithState(context, state.resultNode, outputError, "error");
      return;
    }
    window.location.assign(buildStudioRouteUrl(state.config, "catalogue_series_editor"));
  } catch (error) {
    const message = catalogueSavedActionError(savedResponse, error) || (Number(error && error.status) === 409
      ? t(state, context, "delete_status_conflict", "Source record changed since this page loaded. Reload before deleting again.")
      : `${t(state, context, "delete_status_failed", "Source delete failed.")} ${normalizeText(error && error.message)}`.trim());
    setTextWithState(context, state.statusNode, message, "error");
    state.isDeleting = false;
    context.updateEditorState();
  }
}
