import { buildStudioRouteUrl } from "./studio-config.js";
import {
  applyCatalogueDelete,
  createCatalogueWorkDetail,
  previewCatalogueDelete,
  saveCatalogueBulkRecords,
  saveCatalogueWorkDetail
} from "./catalogue-editor-service-client.js";
import { computeRecordHash } from "./catalogue-editor-records.js";
import { formatCatalogueDeletePreview } from "./catalogue-editor-modal-formatters.js";
import { confirmCatalogueActionModal } from "./catalogue-editor-action-modals.js";
import {
  CATALOGUE_ACTION_OUTCOME,
  extractCatalogueActionPreview,
  getCataloguePreviewBlocker,
  projectCatalogueSaveOutcomePresentation,
  resolveCatalogueSaveBuildOutcome
} from "./catalogue-editor-action-workflow.js";
import { buildStudioActivityContext } from "./studio-activity-context.js";
import {
  WORK_DETAIL_EDITABLE_FIELDS as EDITABLE_FIELDS,
  buildCreateWorkDetailPayload,
  buildSaveWorkDetailPayload,
  normalizeDetailId,
  normalizeDetailUid,
  normalizeText,
  normalizeWorkId
} from "./catalogue-work-detail-fields.js";

function t(state, context, key, fallback, tokens = null) {
  return context.text(key, fallback, tokens);
}

function setTextWithState(context, node, text, state = "") {
  context.setTextWithState(node, text, state);
}

function applyActionPresentation(context, state, presentation) {
  setTextWithState(context, state.resultNode, presentation.resultText, presentation.resultTone);
  setTextWithState(context, state.statusNode, presentation.statusText, presentation.statusTone);
}

function buildPayload(state) {
  if (state.mode === "bulk") {
    const setFields = {};
    EDITABLE_FIELDS.forEach((field) => {
      if (!state.bulkTouchedFields.has(field.key)) return;
      setFields[field.key] = normalizeText(state.draft[field.key]) || null;
    });
    const expectedRecordHashes = {};
    state.bulkDetailUids.forEach((detailUid) => {
      expectedRecordHashes[detailUid] = state.bulkRecordHashes.get(detailUid) || "";
    });
    return {
      kind: "work_details",
      ids: state.bulkDetailUids.slice(),
      expected_record_hashes: expectedRecordHashes,
      apply_build: bulkSelectionHasPublishedParentWorks(state),
      set_fields: setFields
    };
  }

  const draft = state.draft;
  return {
    ...buildSaveWorkDetailPayload({ ...state, draft, applyBuild: currentDetailParentWorkIsPublished(state) }),
    activity_context: buildWorkDetailActivityContext("save-work-detail", "catalogueWorkDetailSave", "#catalogueWorkDetailSave", state.currentDetailUid)
  };
}

function buildWorkDetailActivityContext(actionId, controlId, controlSelector, detailUid) {
  return buildStudioActivityContext({
    pageId: "catalogue-work-detail",
    actionId,
    route: "/studio/catalogue-work-detail/",
    controlId,
    controlSelector,
    recordIdField: "detail_uid",
    recordId: detailUid
  });
}

function parentWorkIsPublished(state, workId) {
  const parent = state.workSearchById instanceof Map ? state.workSearchById.get(normalizeWorkId(workId)) : null;
  return normalizeText(parent && parent.status).toLowerCase() === "published";
}

export function currentDetailParentWorkIsPublished(state) {
  return parentWorkIsPublished(state, state.currentWorkId);
}

export function bulkSelectionHasPublishedParentWorks(state) {
  if (state.mode !== "bulk") return false;
  return state.bulkDetailUids.some((detailUid) => {
    const record = state.bulkRecords.get(detailUid);
    return parentWorkIsPublished(state, record && record.work_id);
  });
}

function applySingleSaveBuildOutcome(state, response) {
  const outcome = resolveCatalogueSaveBuildOutcome({
    response,
    isPublished: currentDetailParentWorkIsPublished(state)
  });
  state.rebuildPending = outcome.rebuildPending;
  return outcome;
}

function applyBulkSaveBuildOutcome(state, response, fallbackBuildTargets) {
  const outcome = resolveCatalogueSaveBuildOutcome({
    response,
    isPublished: bulkSelectionHasPublishedParentWorks(state),
    buildTargets: Array.isArray(response && response.build_targets) ? response.build_targets : fallbackBuildTargets,
    fallbackBuildTargets,
    unpublishedKind: CATALOGUE_ACTION_OUTCOME.SAVED_UNPUBLISHED
  });
  state.rebuildPending = outcome.rebuildPending;
  state.bulkBuildTargets = outcome.buildTargets;
  return outcome;
}

function projectSingleDetailSavePresentation(state, context, response, outcome) {
  const savedAt = { saved_at: outcome.stamp };
  const loadedDetail = { detail_uid: state.currentDetailUid };
  const statusFailed = `${t(state, context, "build_status_failed", "Site update failed.")} ${normalizeText(outcome.error)}`.trim();
  return projectCatalogueSaveOutcomePresentation({
    outcome,
    changed: Boolean(response && response.changed),
    resultLabels: {
      savedAndUpdated: {
        text: t(state, context, "save_result_success_applied", "Saved source changes and updated the parent work output at {saved_at}.", savedAt),
        tone: "success"
      },
      savedUpdateFailed: {
        text: t(state, context, "save_result_success_partial", "Source changes were saved at {saved_at}, but the public update failed.", savedAt),
        tone: "warn"
      },
      savedUnpublished: {
        text: t(state, context, "save_result_success_unpublished", "Source saved at {saved_at}.", savedAt),
        tone: "success"
      },
      saved: {
        text: t(state, context, "save_result_success", "Source saved at {saved_at}. Parent-work update still pending.", savedAt),
        tone: "success"
      },
      unchanged: {
        text: t(state, context, "save_result_unchanged", "Source already matches the current form values.")
      }
    },
    statusLabels: {
      savedAndUpdated: {
        text: t(state, context, "build_status_success", "Site update completed."),
        tone: "success"
      },
      savedUpdateFailed: {
        text: statusFailed,
        tone: "error"
      },
      loaded: {
        text: t(state, context, "save_status_loaded", "Loaded detail {detail_uid}.", loadedDetail),
        tone: "success"
      }
    }
  });
}

function projectBulkDetailSavePresentation(state, context, response, outcome) {
  const savedAt = {
    count: String(response && response.changed_count || 0),
    saved_at: outcome.stamp
  };
  const loadedCount = { count: String(state.bulkDetailUids.length) };
  const statusFailed = `${t(state, context, "build_status_failed", "Site update failed.")} ${normalizeText(outcome.error)}`.trim();
  return projectCatalogueSaveOutcomePresentation({
    outcome,
    changed: Boolean(response && response.changed),
    resultLabels: {
      savedAndUpdated: {
        text: t(state, context, "bulk_save_result_success_applied", "Saved {count} detail records and updated the parent work output at {saved_at}.", savedAt),
        tone: "success"
      },
      savedUpdateFailed: {
        text: t(state, context, "bulk_save_result_success_partial", "Saved {count} detail records at {saved_at}, but the public update failed.", savedAt),
        tone: "warn"
      },
      savedUnpublished: {
        text: t(state, context, "bulk_save_result_success_unpublished", "Saved {count} detail records at {saved_at}.", savedAt),
        tone: "success"
      },
      saved: {
        text: t(state, context, "bulk_save_result_success", "Saved {count} detail records at {saved_at}. Parent-work update still pending.", savedAt),
        tone: "success"
      },
      unchanged: {
        text: t(state, context, "save_result_unchanged", "Source already matches the current form values.")
      }
    },
    statusLabels: {
      savedAndUpdated: {
        text: t(state, context, "build_status_success", "Site update completed."),
        tone: "success"
      },
      savedUpdateFailed: {
        text: statusFailed,
        tone: "error"
      },
      loaded: {
        text: t(state, context, "bulk_status_loaded", "Loaded {count} detail records.", loadedCount),
        tone: response && response.changed ? "success" : ""
      }
    }
  });
}

export async function saveCurrentDetail(state, context) {
  if (state.mode === "new") {
    await createCurrentDetail(state, context);
    return;
  }
  if (state.mode === "bulk") {
    if (!state.bulkDetailUids.length) return;
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

  if (!context.draftHasChanges()) {
    setTextWithState(context, state.statusNode, t(state, context, "save_status_no_changes", "No changes to save."));
    setTextWithState(context, state.resultNode, t(state, context, "save_result_unchanged", "Source already matches the current form values."));
    context.updateEditorState();
    return;
  }

  state.isSaving = true;
  state.saveButton.disabled = true;
  context.syncRouteBusyState();
  setTextWithState(
    context,
    state.statusNode,
    (state.mode === "bulk" ? bulkSelectionHasPublishedParentWorks(state) : currentDetailParentWorkIsPublished(state))
      ? t(state, context, "save_status_saving_and_updating", "Saving source record and updating parent work output…")
      : t(state, context, "save_status_saving", "Saving source record…")
  );
  setTextWithState(context, state.resultNode, "");

  try {
    if (state.mode === "bulk") {
      const response = await saveCatalogueBulkRecords(buildPayload(state));
      const changedRecords = Array.isArray(response && response.records) ? response.records : [];
      changedRecords.forEach((item) => {
        const detailUid = normalizeDetailUid(item && item.detail_uid);
        const record = item && item.record && typeof item.record === "object" ? item.record : null;
        if (!detailUid || !record) return;
        state.bulkRecords.set(detailUid, record);
        state.bulkRecordHashes.set(detailUid, normalizeText(item.record_hash) || "");
        state.detailSearchByUid.set(detailUid, context.buildDetailSearchRecord(detailUid, record));
      });
      const fallbackBuildTargets = Array.isArray(response && response.build_targets) ? response.build_targets : [];
      const outcome = applyBulkSaveBuildOutcome(state, response, fallbackBuildTargets);
      context.setLoadedBulkDetails(state.bulkDetailUids, state.bulkRecords, state.bulkRecordHashes, {
        keepResult: true,
        buildTargets: state.bulkBuildTargets
      });
      applyActionPresentation(context, state, projectBulkDetailSavePresentation(state, context, response, outcome));
      return;
    }

    const response = await saveCatalogueWorkDetail(buildPayload(state));
    const record = response && response.record && typeof response.record === "object" ? response.record : null;
    if (!record) throw new Error("save response missing record");
    state.detailSearchByUid.set(state.currentDetailUid, context.buildDetailSearchRecord(state.currentDetailUid, record));
    const outcome = applySingleSaveBuildOutcome(state, response);
    const recordHash = normalizeText(response.record_hash) || await computeRecordHash(record);
    context.setLoadedRecord(state.currentDetailUid, record, {
      recordHash,
      keepResult: true,
      lookup: {
        work_detail: record,
        record_hash: recordHash
      }
    });
    applyActionPresentation(context, state, projectSingleDetailSavePresentation(state, context, response, outcome));
  } catch (error) {
    const isConflict = Number(error && error.status) === 409;
    const message = isConflict
      ? t(state, context, "save_status_conflict", "Source record changed since this page loaded. Reload the detail before saving again.")
      : `${t(state, context, "save_status_failed", "Source save failed.")} ${normalizeText(error && error.message)}`.trim();
    setTextWithState(context, state.statusNode, message, "error");
  } finally {
    state.isSaving = false;
    context.updateEditorState();
  }
}

async function createCurrentDetail(state, context) {
  if (state.mode !== "new") return;
  const errors = context.validateDraft();
  context.updateFieldMessages(errors);
  if (errors.size > 0) {
    const workIdError = errors.get("work_id") || "";
    setTextWithState(
      context,
      state.statusNode,
      workIdError || t(state, context, "create_status_validation_error", "Fix validation errors before creating the detail."),
      "error"
    );
    context.updateEditorState();
    return;
  }

  state.isSaving = true;
  context.updateEditorState();
  setTextWithState(context, state.statusNode, t(state, context, "create_status_saving", "Creating detail..."));
  setTextWithState(context, state.resultNode, "");

  try {
    const requestedDetailUid = normalizeDetailUid(`${normalizeWorkId(state.draft.work_id)}-${normalizeDetailId(state.draft.detail_id)}`);
    const response = await createCatalogueWorkDetail({
      ...buildCreateWorkDetailPayload(state.draft),
      activity_context: buildWorkDetailActivityContext("create-work-detail", "catalogueWorkDetailSave", "#catalogueWorkDetailSave", requestedDetailUid)
    });
    const detailUid = normalizeDetailUid(response && response.detail_uid);
    const record = response && response.record && typeof response.record === "object" ? response.record : null;
    if (!detailUid) {
      throw new Error("create response missing detail id");
    }
    if (record) {
      state.detailSearchByUid.set(detailUid, context.buildDetailSearchRecord(detailUid, record));
    }
    state.isSaving = false;
    context.syncRouteBusyState();
    await context.openDetailByUid(detailUid);
    setTextWithState(context, state.resultNode, t(state, context, "create_result_success", "Created detail {detail_uid}. Opening edit mode...", { detail_uid: detailUid }), "success");
    setTextWithState(context, state.statusNode, t(state, context, "create_status_success", "Created detail {detail_uid}.", { detail_uid: detailUid }), "success");
  } catch (error) {
    const message = `${t(state, context, "create_status_failed", "Detail create failed.")} ${normalizeText(error && error.message)}`.trim();
    setTextWithState(context, state.statusNode, message, "error");
    setTextWithState(context, state.resultNode, message, "error");
    state.isSaving = false;
    context.updateEditorState();
  }
}

export async function deleteCurrentDetail(state, context) {
  if (!state.currentRecord || state.mode === "bulk" || !state.serverAvailable) return;
  state.isDeleting = true;
  context.updateEditorState();
  setTextWithState(context, state.statusNode, t(state, context, "delete_status_running", "Preparing delete preview…"));
  setTextWithState(context, state.resultNode, "");
  try {
    const request = {
      kind: "work_detail",
      detail_uid: state.currentDetailUid,
      expected_record_hash: state.currentRecordHash,
      activity_context: buildWorkDetailActivityContext("delete-work-detail", "catalogueWorkDetailDelete", "#catalogueWorkDetailDelete", state.currentDetailUid)
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
      context.updateEditorState();
      return;
    }
    state.isDeleting = true;
    context.updateEditorState();
    setTextWithState(context, state.statusNode, t(state, context, "delete_status_running", "Deleting source record…"));
    await applyCatalogueDelete(request);
    window.location.assign(buildStudioRouteUrl(state.config, "catalogue_work_editor", {
      work: state.currentWorkId
    }));
  } catch (error) {
    const message = Number(error && error.status) === 409
      ? t(state, context, "delete_status_conflict", "Source record changed since this page loaded. Reload before deleting again.")
      : `${t(state, context, "delete_status_failed", "Source delete failed.")} ${normalizeText(error && error.message)}`.trim();
    setTextWithState(context, state.statusNode, message, "error");
    state.isDeleting = false;
    context.updateEditorState();
  }
}
