import { buildStudioRouteUrl } from "./studio-config.js";
import {
  applyCatalogueBuild,
  applyCatalogueDelete,
  applyCataloguePublication,
  createCatalogueWorkDetail,
  previewCatalogueBuild,
  previewCatalogueDelete,
  previewCataloguePublication,
  saveCatalogueBulkRecords,
  saveCatalogueWorkDetail
} from "./catalogue-editor-service-client.js";
import { computeRecordHash } from "./catalogue-editor-records.js";
import {
  formatCatalogueBuildPreview,
  formatCatalogueDeletePreview,
  formatCataloguePublicationPreview
} from "./catalogue-editor-modal-formatters.js";
import { confirmCatalogueActionModal } from "./catalogue-editor-action-modals.js";
import {
  CATALOGUE_ACTION_OUTCOME,
  extractCatalogueActionPreview,
  getCataloguePreviewBlocker,
  projectCatalogueActionPresentation,
  projectCatalogueSaveOutcomePresentation,
  resolveCataloguePendingBuildTargets,
  resolveCatalogueSaveBuildOutcome
} from "./catalogue-editor-action-workflow.js";
import { buildStudioActivityContext } from "./studio-activity-context.js";
import { utcTimestamp } from "./tag-studio-save.js";
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
      setFields[field.key] = field.key === "status"
        ? normalizeText(state.draft[field.key]).toLowerCase() || null
        : normalizeText(state.draft[field.key]) || null;
    });
    const expectedRecordHashes = {};
    state.bulkDetailUids.forEach((detailUid) => {
      expectedRecordHashes[detailUid] = state.bulkRecordHashes.get(detailUid) || "";
    });
    return {
      kind: "work_details",
      ids: state.bulkDetailUids.slice(),
      expected_record_hashes: expectedRecordHashes,
      apply_build: bulkSelectionHasPublishedRecords(state),
      set_fields: setFields
    };
  }

  const draft = state.draft;
  return {
    ...buildSaveWorkDetailPayload({ ...state, draft, applyBuild: currentDetailIsPublished(state) }),
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

export function currentDetailIsPublished(state) {
  return normalizeText(state.draft && state.draft.status).toLowerCase() === "published";
}

export function currentDetailIsDraft(state) {
  return normalizeText(state.draft && state.draft.status).toLowerCase() === "draft";
}

export function bulkSelectionHasPublishedRecords(state) {
  if (state.mode !== "bulk") return false;
  return state.bulkDetailUids.some((detailUid) => {
    const record = state.bulkRecords.get(detailUid);
    return normalizeText(record && record.status).toLowerCase() === "published";
  });
}

export function bulkPublishedBuildTargets(state) {
  return state.bulkDetailUids
    .filter((detailUid) => {
      const record = state.bulkRecords.get(detailUid);
      return normalizeText(record && record.status).toLowerCase() === "published";
    })
    .map((detailUid) => {
      const record = state.bulkRecords.get(detailUid);
      return { work_id: normalizeWorkId(record && record.work_id), extra_series_ids: [] };
    })
    .filter((target) => target.work_id);
}

export function updateWorkDetailPublishControls(state, context, { hasRecord, dirty, errors }) {
  const canPublish = state.mode === "single" && hasRecord && currentDetailIsDraft(state);
  const canUnpublish = state.mode === "single" && hasRecord && currentDetailIsPublished(state);
  const label = canUnpublish
    ? t(state, context, "unpublish_button", "Unpublish")
    : t(state, context, "publish_button", "Publish");
  state.publicationButton.textContent = label;
  state.publicationButton.hidden = !(canPublish || canUnpublish);
  state.publicationButton.disabled = !(canPublish || canUnpublish)
    || (canPublish && dirty)
    || (canPublish && errors.size > 0)
    || state.isSaving
    || state.isBuilding
    || state.isDeleting
    || !state.serverAvailable;
}

function applySingleSaveBuildOutcome(state, response) {
  const outcome = resolveCatalogueSaveBuildOutcome({
    response,
    isPublished: currentDetailIsPublished(state)
  });
  state.rebuildPending = outcome.rebuildPending;
  return outcome;
}

function applyBulkSaveBuildOutcome(state, response, fallbackBuildTargets) {
  const outcome = resolveCatalogueSaveBuildOutcome({
    response,
    isPublished: bulkSelectionHasPublishedRecords(state),
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
        text: t(state, context, "bulk_save_result_success_unpublished", "Saved {count} draft detail records at {saved_at}.", savedAt),
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

function projectDetailBuildPresentation(state, context, { bulk = false, count = "", completedAt = "" } = {}) {
  return projectCatalogueActionPresentation({
    resultKey: bulk ? "bulkSuccess" : "success",
    statusKey: "success",
    resultLabels: {
      bulkSuccess: {
        text: t(state, context, "bulk_build_result_success", "Updated {count} parent work scopes at {completed_at}. Studio Activity updated.", {
          count,
          completed_at: completedAt
        }),
        tone: "success"
      },
      success: {
        text: t(state, context, "build_result_success", "Parent work output updated at {completed_at}. Studio Activity updated.", { completed_at: completedAt }),
        tone: "success"
      }
    },
    statusLabels: {
      success: {
        text: t(state, context, "build_status_success", "Site update completed."),
        tone: "success"
      }
    }
  });
}

function projectDetailPublicationPresentation(state, context, action, response) {
  const publicUpdateFailed = response && response.status === "public_update_failed";
  const publicUpdateError = normalizeText(response && response.public_update && response.public_update.error);
  return projectCatalogueActionPresentation({
    resultKey: publicUpdateFailed ? "publicFailed" : action === "publish" ? "published" : "unpublished",
    statusKey: publicUpdateFailed ? "publicFailed" : action === "publish" ? "published" : "unpublished",
    resultLabels: {
      publicFailed: {
        text: t(state, context, "publication_result_public_failed", "Source status changed, but public artifacts did not finish updating."),
        tone: "warn"
      },
      published: {
        text: t(state, context, "publication_result_published", "Detail is published and parent work output has been updated."),
        tone: "success"
      },
      unpublished: {
        text: t(state, context, "publication_result_unpublished", "Detail is draft again and public output has been cleaned up."),
        tone: "success"
      }
    },
    statusLabels: {
      publicFailed: {
        text: `${t(state, context, "publication_status_public_failed", "Publication state changed, but the public update failed.")} ${publicUpdateError}`.trim(),
        tone: "error"
      },
      published: {
        text: t(state, context, "publication_status_published", "Detail published."),
        tone: "success"
      },
      unpublished: {
        text: t(state, context, "publication_status_unpublished", "Detail unpublished."),
        tone: "success"
      }
    }
  });
}

export async function refreshWorkDetailBuildPreview(state, context) {
  if (state.mode === "bulk") {
    const previewTargets = state.rebuildPending && state.bulkBuildTargets.length
      ? state.bulkBuildTargets
      : bulkPublishedBuildTargets(state);
    state.buildPreview = null;
    setTextWithState(
      context,
      state.buildImpactNode,
      previewTargets.length
        ? t(state, context, "bulk_build_preview", "Build preview: {count} parent work scopes will be rebuilt.", {
          count: String(previewTargets.length)
        })
        : ""
    );
    context.renderCurrentPreview();
    return;
  }
  if (!state.currentWorkId || !state.serverAvailable) {
    state.buildPreview = null;
    setTextWithState(context, state.buildImpactNode, "");
    context.renderCurrentPreview();
    context.renderReadiness();
    return;
  }
  if (!currentDetailIsPublished(state)) {
    state.buildPreview = null;
    setTextWithState(context, state.buildImpactNode, t(state, context, "build_preview_unpublished", "Public update unavailable while the detail is not published."));
    context.renderCurrentPreview();
    context.renderReadiness();
    return;
  }
  try {
    const response = await previewCatalogueBuild({
      work_id: state.currentWorkId,
      detail_uid: state.currentDetailUid
    });
    state.buildPreview = response && response.build ? response.build : null;
    setTextWithState(context, state.buildImpactNode, formatCatalogueBuildPreview(state.buildPreview, {
      text: (key, fallback, tokens) => t(state, context, key, fallback, tokens),
      defaultTemplate: "Build preview: work {work_ids}; series {series_ids}; catalogue search {search_rebuild}."
    }));
    context.renderCurrentPreview();
    context.renderReadiness();
  } catch (error) {
    state.buildPreview = null;
    setTextWithState(
      context,
      state.buildImpactNode,
      `${t(state, context, "build_preview_failed", "Build preview unavailable.")} ${normalizeText(error && error.message)}`.trim(),
      "error"
    );
    context.renderCurrentPreview();
    context.renderReadiness();
  }
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
    (state.mode === "bulk" ? bulkSelectionHasPublishedRecords(state) : currentDetailIsPublished(state))
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
    await refreshWorkDetailBuildPreview(state, context);
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
      workIdError || t(state, context, "create_status_validation_error", "Fix validation errors before creating the draft detail."),
      "error"
    );
    context.updateEditorState();
    return;
  }

  state.isSaving = true;
  context.updateEditorState();
  setTextWithState(context, state.statusNode, t(state, context, "create_status_saving", "Creating draft detail..."));
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
    setTextWithState(context, state.resultNode, t(state, context, "create_result_success", "Created draft detail {detail_uid}. Opening edit mode...", { detail_uid: detailUid }), "success");
    setTextWithState(context, state.statusNode, t(state, context, "create_status_success", "Created draft detail {detail_uid}.", { detail_uid: detailUid }), "success");
  } catch (error) {
    const message = `${t(state, context, "create_status_failed", "Draft detail create failed.")} ${normalizeText(error && error.message)}`.trim();
    setTextWithState(context, state.statusNode, message, "error");
    setTextWithState(context, state.resultNode, message, "error");
    state.isSaving = false;
    context.updateEditorState();
  }
}

export async function buildCurrentDetail(state, context) {
  if (state.mode === "bulk") {
    if (!state.bulkDetailUids.length || !state.serverAvailable) return;
  } else if (!state.currentRecord || !state.currentWorkId || !state.serverAvailable) {
    return;
  }
  state.isBuilding = true;
  context.updateEditorState();
  setTextWithState(context, state.statusNode, t(state, context, "build_status_running", "Updating site…"));
  setTextWithState(context, state.resultNode, "");
  try {
    if (state.mode === "bulk") {
      const buildTargets = resolveCataloguePendingBuildTargets({
        rebuildPending: state.rebuildPending,
        pendingTargets: state.bulkBuildTargets,
        fallbackTargets: Array.from(new Set(state.bulkDetailUids.map((detailUid) => {
          const record = state.bulkRecords.get(detailUid);
          return normalizeWorkId(record && record.work_id);
        }).filter(Boolean))).map((workId) => ({ work_id: workId, extra_series_ids: [] }))
      });
      for (const target of buildTargets) {
        await applyCatalogueBuild({
          work_id: target.work_id,
          extra_series_ids: Array.isArray(target.extra_series_ids) ? target.extra_series_ids : []
        });
      }
      state.rebuildPending = false;
      state.bulkBuildTargets = [];
      await refreshWorkDetailBuildPreview(state, context);
      const completedAt = utcTimestamp();
      applyActionPresentation(context, state, projectDetailBuildPresentation(state, context, {
        bulk: true,
        count: String(buildTargets.length),
        completedAt
      }));
      return;
    }

    const response = await applyCatalogueBuild({
      work_id: state.currentWorkId,
      detail_uid: state.currentDetailUid
    });
    state.rebuildPending = false;
    await refreshWorkDetailBuildPreview(state, context);
    const completedAt = normalizeText(response.completed_at_utc || utcTimestamp());
    applyActionPresentation(context, state, projectDetailBuildPresentation(state, context, { completedAt }));
  } catch (error) {
    setTextWithState(
      context,
      state.statusNode,
      `${t(state, context, "build_status_failed", "Site update failed.")} ${normalizeText(error && error.message)}`.trim(),
      "error"
    );
  } finally {
    state.isBuilding = false;
    context.updateEditorState();
  }
}

export async function applyWorkDetailPublicationChange(state, context) {
  if (state.mode !== "single" || !state.currentRecord || !state.currentDetailUid || !state.serverAvailable) return;
  const action = currentDetailIsPublished(state) ? "unpublish" : currentDetailIsDraft(state) ? "publish" : "";
  if (!action) {
    setTextWithState(context, state.statusNode, t(state, context, "publication_status_invalid", "Publication is available only for draft or published details."), "error");
    return;
  }
  if (action === "publish" && context.draftHasChanges()) {
    setTextWithState(context, state.statusNode, t(state, context, "publication_save_first", "Save source changes before publishing."), "error");
    return;
  }

  if (action === "publish") {
    const errors = context.validateDraft();
    context.updateFieldMessages(errors);
    if (errors.size > 0) {
      setTextWithState(context, state.statusNode, t(state, context, "publication_status_validation_error", "Fix validation errors before changing publication state."), "error");
      context.updateEditorState();
      return;
    }
  }

  state.isBuilding = true;
  context.updateEditorState();
  setTextWithState(
    context,
    state.statusNode,
    action === "publish"
      ? t(state, context, "publication_preview_publish_running", "Preparing publish preview…")
      : t(state, context, "publication_preview_unpublish_running", "Preparing unpublish preview…")
  );
  setTextWithState(context, state.resultNode, "");

  try {
    const request = {
      kind: "work_detail",
      action,
      detail_uid: state.currentDetailUid,
      expected_record_hash: state.currentRecordHash,
      activity_context: buildWorkDetailActivityContext(`${action}-work-detail`, "catalogueWorkDetailPublication", "#catalogueWorkDetailPublication", state.currentDetailUid)
    };
    const previewResponse = await previewCataloguePublication(request);
    const preview = extractCatalogueActionPreview(previewResponse);
    const blocker = getCataloguePreviewBlocker(preview, {
      fallback: t(state, context, "publication_status_blocked", "Publication change is blocked.")
    });
    if (blocker) {
      setTextWithState(context, state.statusNode, blocker, "error");
      return;
    }

    if (action === "unpublish") {
      const summary = formatCataloguePublicationPreview(preview, {
        text: (key, fallback, tokens) => t(state, context, key, fallback, tokens),
        defaultText: "Unpublish this detail?",
        includeDirtyNote: context.draftHasChanges()
      });
      state.isBuilding = false;
      context.updateEditorState();
      const confirmed = await confirmCatalogueActionModal(state, {
        title: t(state, context, "publication_unpublish_confirm_title", "Confirm unpublish"),
        message: summary,
        primaryLabel: t(state, context, "publication_unpublish_confirm_button", "Unpublish"),
        cancelLabel: t(state, context, "confirm_cancel_button", "Cancel"),
        restoreFocus: state.publicationButton
      });
      if (!confirmed) {
        setTextWithState(context, state.statusNode, t(state, context, "publication_status_cancelled", "Publication change cancelled."));
        return;
      }
      state.isBuilding = true;
      context.updateEditorState();
    }

    setTextWithState(
      context,
      state.statusNode,
      action === "publish"
        ? t(state, context, "publication_publish_running", "Publishing detail…")
        : t(state, context, "publication_unpublish_running", "Unpublishing detail…")
    );
    const response = await applyCataloguePublication(request);
    const record = response && response.record && typeof response.record === "object" ? response.record : null;
    if (!record) throw new Error("publication response missing record");

    const detailUid = state.currentDetailUid;
    const recordHash = normalizeText(response.record_hash) || await computeRecordHash(record);
    state.detailSearchByUid.set(detailUid, context.buildDetailSearchRecord(detailUid, record));
    state.rebuildPending = response.status === "public_update_failed";
    const lookup = await context.loadDetailLookupRecord(detailUid).catch(() => null);
    context.setLoadedRecord(detailUid, record, {
      recordHash,
      keepResult: true,
      lookup: lookup || {
        work_detail: record,
        record_hash: recordHash
      }
    });
    await refreshWorkDetailBuildPreview(state, context);

    const presentation = projectDetailPublicationPresentation(state, context, action, response);
    applyActionPresentation(context, state, presentation);
    if (response.status === "public_update_failed") {
      return;
    }
  } catch (error) {
    const message = Number(error && error.status) === 409
      ? t(state, context, "publication_status_conflict", "Source record changed since this page loaded. Reload before changing publication state.")
      : `${t(state, context, "publication_status_failed", "Publication change failed.")} ${normalizeText(error && error.message)}`.trim();
    setTextWithState(context, state.statusNode, message, "error");
  } finally {
    state.isBuilding = false;
    context.updateEditorState();
  }
}

function countMediaItems(media, group) {
  const values = media && media[group] && typeof media[group] === "object" ? media[group] : {};
  return Object.values(values).reduce((total, items) => total + (Array.isArray(items) ? items.length : 0), 0);
}

export async function refreshWorkDetailMedia(state, context) {
  if (!state.currentRecord || !state.currentWorkId || !state.currentDetailUid || !state.serverAvailable || context.draftHasChanges()) return;
  state.isBuilding = true;
  context.updateEditorState();
  setTextWithState(context, state.statusNode, t(state, context, "media_refresh_status_running", "Refreshing media…"));
  setTextWithState(context, state.resultNode, "");
  try {
    const response = await applyCatalogueBuild({
      work_id: state.currentWorkId,
      detail_uid: state.currentDetailUid,
      media_only: true,
      force: true
    });
    const blockedCount = countMediaItems(response && response.media, "blocked");
    await refreshWorkDetailBuildPreview(state, context);
    if (blockedCount > 0) {
      setTextWithState(context, state.statusNode, t(state, context, "media_refresh_status_blocked", "Media refresh blocked."), "error");
      setTextWithState(context, state.resultNode, normalizeText(response && response.media && response.media.summary), "error");
      return;
    }
    setTextWithState(context, state.statusNode, t(state, context, "media_refresh_status_success", "Media refresh completed."), "success");
    setTextWithState(context, state.resultNode, t(state, context, "media_refresh_result_success", "Thumbnails updated; primary variants staged for publishing."), "success");
  } catch (error) {
    setTextWithState(
      context,
      state.statusNode,
      `${t(state, context, "media_refresh_status_failed", "Media refresh failed.")} ${normalizeText(error && error.message)}`.trim(),
      "error"
    );
  } finally {
    state.isBuilding = false;
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
