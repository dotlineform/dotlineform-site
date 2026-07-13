import { buildStudioRouteUrl } from "./studio-config.js";
import {
  applyCatalogueBuild,
  applyCatalogueDelete,
  applyCataloguePublication,
  createCatalogueWork,
  previewCatalogueBuild,
  previewCatalogueDelete,
  previewCataloguePublication,
  saveCatalogueBulkRecords,
  saveCatalogueWork
} from "./catalogue-editor-service-client.js";
import { computeRecordHash } from "./catalogue-editor-records.js";
import {
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
import {
  setLoadedBulkWorks,
  setLoadedWorkRecord
} from "./catalogue-work-route-state.js";
import {
  WORK_DOWNLOAD_FIELDS as DOWNLOAD_FIELDS,
  WORK_LINK_FIELDS as LINK_FIELDS
} from "./catalogue-editor-embedded-items.js";
import { buildStudioActivityContext } from "./studio-activity-context.js";
import {
  utcTimestamp
} from "./studio-save-utils.js";
import {
  WORK_DIMENSION_FIELD_KEYS,
  WORK_EDITABLE_FIELDS as EDITABLE_FIELDS,
  buildCreateWorkPayload,
  buildWorkRecordFromDraft,
  dedupeSeriesIds,
  normalizeSeriesId,
  normalizeText,
  normalizeWorkId,
  parseSeriesIds
} from "./catalogue-work-fields.js";
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

function applyActionPresentation(context, state, presentation) {
  setTextWithState(context, state.resultNode, presentation.resultText, presentation.resultTone);
  setTextWithState(context, state.statusNode, presentation.statusText, presentation.statusTone);
}

function buildWorkSaveActivityContext(state) {
  return buildWorkActivityContext("save-work", "catalogueWorkSave", "#catalogueWorkSave", state.currentWorkId);
}

function buildWorkActivityContext(actionId, controlId, controlSelector, workId) {
  return buildStudioActivityContext({
    pageId: "catalogue-work",
    actionId,
    route: "/studio/catalogue-work/",
    controlId,
    controlSelector,
    recordIdField: "work_id",
    recordId: workId
  });
}

export function parseBulkSeriesOperation(value) {
  const text = normalizeText(value);
  if (!text) {
    return { mode: "replace", series_ids: [] };
  }
  const tokens = text.split(",").map((item) => normalizeText(item)).filter(Boolean);
  const signed = tokens.filter((token) => token.startsWith("+") || token.startsWith("-"));
  if (signed.length && signed.length !== tokens.length) {
    throw new Error("Use either plain series ids or only +id/-id entries.");
  }
  if (!signed.length) {
    return { mode: "replace", series_ids: parseSeriesIds(tokens) };
  }
  const addSeriesIds = [];
  const removeSeriesIds = [];
  tokens.forEach((token) => {
    const sign = token[0];
    const seriesId = normalizeSeriesId(token.slice(1));
    if (!seriesId) {
      throw new Error(`Invalid series id entry: ${token}`);
    }
    if (sign === "+") addSeriesIds.push(seriesId);
    if (sign === "-") removeSeriesIds.push(seriesId);
  });
  return {
    mode: "add_remove",
    add_series_ids: dedupeSeriesIds(addSeriesIds),
    remove_series_ids: dedupeSeriesIds(removeSeriesIds)
  };
}

function buildPayload(state) {
  if (state.mode === "bulk") {
    const setFields = {};
    EDITABLE_FIELDS.forEach((field) => {
      if (!state.bulkTouchedFields.has(field.key) || field.key === "series_ids") return;
      const value = state.draft[field.key];
      if (field.key === "status") {
        setFields.status = normalizeText(value).toLowerCase() || null;
        return;
      }
      if (field.key === "year") {
        setFields.year = normalizeText(value) ? Number(value) : null;
        return;
      }
      if (WORK_DIMENSION_FIELD_KEYS.includes(field.key)) {
        setFields[field.key] = normalizeText(value) ? Number(value) : null;
        return;
      }
      setFields[field.key] = normalizeText(value) || null;
    });

    const expectedRecordHashes = {};
    state.bulkWorkIds.forEach((workId) => {
      expectedRecordHashes[workId] = state.bulkRecordHashes.get(workId) || "";
    });

    const payload = {
      kind: "works",
      ids: state.bulkWorkIds.slice(),
      expected_record_hashes: expectedRecordHashes,
      apply_build: bulkSelectionHasPublishedRecords(state),
      set_fields: setFields
    };
    if (state.bulkTouchedFields.has("series_ids")) {
      payload.series_operation = parseBulkSeriesOperation(state.draft.series_ids);
    }
    return payload;
  }

  const draft = state.draft;
  return {
    work_id: state.currentWorkId,
    expected_record_hash: state.currentRecordHash,
    apply_build: currentWorkIsPublished(state),
    extra_series_ids: state.pendingBuildExtraSeriesIds.slice(),
    activity_context: buildWorkSaveActivityContext(state),
    record: buildWorkRecordFromDraft(draft, {
      downloadFields: DOWNLOAD_FIELDS,
      linkFields: LINK_FIELDS
    })
  };
}

export function currentWorkIsPublished(state) {
  return normalizeText(state.draft && state.draft.status).toLowerCase() === "published";
}

export function currentWorkIsDraft(state) {
  return normalizeText(state.draft && state.draft.status).toLowerCase() === "draft";
}

export function bulkSelectionHasPublishedRecords(state) {
  if (state.mode !== "bulk") return false;
  return state.bulkWorkIds.some((workId) => {
    const record = state.bulkRecords.get(workId);
    return normalizeText(record && record.status).toLowerCase() === "published";
  });
}

export function bulkPublishedBuildTargets(state) {
  return state.bulkWorkIds
    .filter((workId) => {
      const record = state.bulkRecords.get(workId);
      return normalizeText(record && record.status).toLowerCase() === "published";
    })
    .map((workId) => ({ work_id: workId, extra_series_ids: [] }));
}

function applySingleSaveBuildOutcome(state, response) {
  const isPublished = currentWorkIsPublished(state);
  const outcome = resolveCatalogueSaveBuildOutcome({
    response,
    isPublished
  });
  if (!isPublished || outcome.kind === CATALOGUE_ACTION_OUTCOME.SAVED_AND_UPDATED) {
    state.rebuildPending = false;
    state.pendingBuildExtraSeriesIds = [];
  } else {
    state.rebuildPending = outcome.rebuildPending;
  }
  return outcome;
}

function applyBulkSaveBuildOutcome(state, response, fallbackBuildTargets) {
  const outcome = resolveCatalogueSaveBuildOutcome({
    response,
    isPublished: true,
    buildTargets: fallbackBuildTargets,
    fallbackBuildTargets,
    unpublishedKind: CATALOGUE_ACTION_OUTCOME.SAVED
  });
  state.rebuildPending = outcome.rebuildPending;
  state.bulkBuildTargets = outcome.buildTargets;
  return outcome;
}

function projectSingleWorkSavePresentation(state, context, response, outcome) {
  const savedAt = { saved_at: outcome.stamp };
  const loadedWork = { work_id: state.currentWorkId };
  const statusFailed = `${t(state, context, "build_status_failed", "Site update failed.")} ${normalizeText(outcome.error)}`.trim();
  return projectCatalogueSaveOutcomePresentation({
    outcome,
    changed: Boolean(response && response.changed),
    resultLabels: {
      savedAndUpdated: {
        text: t(state, context, "save_result_success_applied", "Saved source changes and updated the public catalogue at {saved_at}.", savedAt),
        tone: "success"
      },
      savedUpdateFailed: {
        text: t(state, context, "save_result_success_partial", "Source changes were saved at {saved_at}, but the public update failed.", savedAt),
        tone: "warn"
      },
      savedUnpublished: {
        text: t(state, context, "save_result_success_unpublished", "Source saved at {saved_at}. Public update is unavailable while the work is not published.", savedAt),
        tone: "success"
      },
      saved: {
        text: t(state, context, "save_result_success", "Source saved at {saved_at}.", savedAt),
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
        text: t(state, context, "save_status_loaded", "Loaded work {work_id}.", loadedWork),
        tone: "success"
      }
    }
  });
}

function projectBulkWorkSavePresentation(state, context, response, outcome) {
  const savedAt = {
    count: String(response && response.changed_count || 0),
    saved_at: outcome.stamp
  };
  const loadedCount = { count: String(state.bulkWorkIds.length) };
  const statusFailed = `${t(state, context, "build_status_failed", "Site update failed.")} ${normalizeText(outcome.error)}`.trim();
  return projectCatalogueSaveOutcomePresentation({
    outcome,
    changed: Boolean(response && response.changed),
    resultLabels: {
      savedAndUpdated: {
        text: t(state, context, "bulk_save_result_success_applied", "Saved {count} work records and updated public catalogue output for published records at {saved_at}.", savedAt),
        tone: "success"
      },
      savedUpdateFailed: {
        text: t(state, context, "bulk_save_result_success_partial", "Saved {count} work records at {saved_at}, but the public update failed.", savedAt),
        tone: "warn"
      },
      saved: {
        text: t(state, context, "bulk_save_result_success", "Saved {count} work records at {saved_at}.", savedAt),
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
        text: t(state, context, "bulk_status_loaded", "Loaded {count} work records.", loadedCount),
        tone: response && response.changed ? "success" : ""
      }
    }
  });
}

function projectWorkBuildPresentation(state, context, { bulk = false, count = "", completedAt = "" } = {}) {
  return projectCatalogueActionPresentation({
    resultKey: bulk ? "bulkSuccess" : "success",
    statusKey: "success",
    resultLabels: {
      bulkSuccess: {
        text: t(state, context, "bulk_build_result_success", "Updated {count} work scopes at {completed_at}. Studio Activity updated.", {
          count,
          completed_at: completedAt
        }),
        tone: "success"
      },
      success: {
        text: t(state, context, "build_result_success", "Public catalogue updated at {completed_at}. Studio Activity updated.", { completed_at: completedAt }),
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

function projectWorkPublicationPresentation(state, context, action, response) {
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
        text: t(state, context, "publication_result_published", "Work is published and public catalogue output has been updated."),
        tone: "success"
      },
      unpublished: {
        text: t(state, context, "publication_result_unpublished", "Work is draft again and public catalogue output has been cleaned up."),
        tone: "success"
      }
    },
    statusLabels: {
      publicFailed: {
        text: `${t(state, context, "publication_status_public_failed", "Publication state changed, but the public update failed.")} ${publicUpdateError}`.trim(),
        tone: "error"
      },
      published: {
        text: t(state, context, "publication_status_published", "Work published."),
        tone: "success"
      },
      unpublished: {
        text: t(state, context, "publication_status_unpublished", "Work unpublished."),
        tone: "success"
      }
    }
  });
}

export async function saveCurrentWork(state, context) {
  if (state.mode === "new") {
    await createCurrentWork(state, context);
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

  if (!context.draftHasChanges()) {
    setTextWithState(context, state.statusNode, t(state, context, "save_status_no_changes", "No changes to save."));
    setTextWithState(context, state.resultNode, t(state, context, "save_result_unchanged", "Source already matches the current form values."));
    context.updateEditorState();
    return;
  }

  state.isSaving = true;
  state.saveButton.disabled = true;
  setTextWithState(
    context,
    state.statusNode,
    (state.mode === "bulk" ? bulkSelectionHasPublishedRecords(state) : currentWorkIsPublished(state))
      ? t(state, context, "save_status_saving_and_updating", "Saving source record and updating site…")
      : t(state, context, "save_status_saving", "Saving source record…")
  );
  setTextWithState(context, state.resultNode, "");

  try {
    if (state.mode === "bulk") {
      const response = await saveCatalogueBulkRecords(buildPayload(state));
      const changedRecords = Array.isArray(response && response.records) ? response.records : [];
      applyBulkWorkRecordMutations(state, changedRecords);
      const fallbackBuildTargets = Array.isArray(response && response.build_targets) ? response.build_targets : [];
      const outcome = applyBulkSaveBuildOutcome(state, response, fallbackBuildTargets);
      setLoadedBulkWorks(state, state.bulkWorkIds, state.bulkRecords, state.bulkRecordHashes, context.workRouteStateOptions({
        keepResult: true,
        buildTargets: state.bulkBuildTargets
      }));
      applyActionPresentation(context, state, projectBulkWorkSavePresentation(state, context, response, outcome));
      return;
    }

    const previousSeriesIds = parseSeriesIds(state.baselineDraft && state.baselineDraft.series_ids);
    const nextSeriesIds = parseSeriesIds(state.draft.series_ids);
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
    const outcome = applySingleSaveBuildOutcome(state, response);
    if (response.changed && outcome.kind !== "saved_and_updated" && outcome.kind !== "saved_unpublished") {
      state.pendingBuildExtraSeriesIds = dedupeSeriesIds([
        ...state.pendingBuildExtraSeriesIds,
        ...previousSeriesIds,
        ...nextSeriesIds
      ]).filter((seriesId) => !nextSeriesIds.includes(seriesId));
    }
    const lookup = await context.loadWorkLookupRecord(state.currentWorkId);
    const stagedPreviewVersion = state.mediaPreviewVersion;
    setLoadedWorkRecord(state, state.currentWorkId, record, context.workRouteStateOptions({
      recordHash: response.record_hash || normalizeText(lookup && lookup.record_hash) || "",
      keepResult: true,
      lookup
    }));
    state.mediaPreviewVersion = stagedPreviewVersion;
    await refreshBuildPreview(state, context);
    applyActionPresentation(context, state, projectSingleWorkSavePresentation(state, context, response, outcome));
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

export async function createCurrentWork(state, context) {
  if (state.mode !== "new") return;
  const errors = context.validateDraft();
  context.updateFieldMessages(errors);
  if (errors.size > 0) {
    const workIdError = errors.get("work_id") || "";
    setTextWithState(
      context,
      state.statusNode,
      workIdError || t(state, context, "create_status_validation_error", "Fix validation errors before creating the draft work."),
      "error"
    );
    context.updateEditorState();
    return;
  }

  state.isSaving = true;
  context.updateEditorState();
  setTextWithState(context, state.statusNode, t(state, context, "create_status_saving", "Creating draft work..."));
  setTextWithState(context, state.resultNode, "");

  try {
    const createPayload = {
      ...buildCreateWorkPayload(state.draft),
      activity_context: buildWorkActivityContext("create-work", "catalogueWorkSave", "#catalogueWorkSave", normalizeWorkId(state.draft.work_id))
    };
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
    setTextWithState(context, state.resultNode, t(state, context, "create_result_success", "Created draft work {work_id}. Opening edit mode...", { work_id: workId }), "success");
    setTextWithState(context, state.statusNode, t(state, context, "create_status_success", "Created draft work {work_id}.", { work_id: workId }), "success");
  } catch (error) {
    setTextWithState(context, state.statusNode, `${t(state, context, "create_status_failed", "Draft work create failed.")} ${normalizeText(error && error.message)}`.trim(), "error");
  } finally {
    state.isSaving = false;
    context.updateEditorState();
  }
}

export async function refreshBuildPreview(state, context) {
  if (state.mode === "bulk") {
    const previewTargets = state.rebuildPending && state.bulkBuildTargets.length
      ? state.bulkBuildTargets
      : bulkPublishedBuildTargets(state);
    setTextWithState(
      context,
      state.buildImpactNode,
      previewTargets.length
        ? t(state, context, "bulk_build_preview", "Public update preview: {count} published work scope(s) will be updated.", {
          count: String(previewTargets.length)
        })
        : ""
    );
    state.buildPreview = null;
    context.renderCurrentPreview();
    context.renderReadiness();
    return;
  }
  if (!state.currentWorkId || !state.serverAvailable) {
    setTextWithState(context, state.buildImpactNode, "");
    state.buildPreview = null;
    context.renderCurrentPreview();
    context.renderReadiness();
    return;
  }
  if (!currentWorkIsPublished(state)) {
    setTextWithState(context, state.buildImpactNode, t(state, context, "build_preview_unpublished", "Site update unavailable while the work is not published."));
    state.buildPreview = null;
    context.renderCurrentPreview();
    context.renderReadiness();
    return;
  }
  try {
    const request = {
      work_id: state.currentWorkId,
      extra_series_ids: state.pendingBuildExtraSeriesIds
    };
    if (context && typeof context.mediaSource === "function") {
      request.media_source = context.mediaSource();
      request.media_only = true;
    }
    const response = await previewCatalogueBuild(request);
    state.buildPreview = response && response.build ? response.build : null;
    setTextWithState(context, state.buildImpactNode, "");
    context.renderCurrentPreview();
    context.renderReadiness();
  } catch (error) {
    state.buildPreview = null;
    setTextWithState(
      context,
      state.buildImpactNode,
      `${t(state, context, "build_preview_failed", "Public update preview unavailable.")} ${normalizeText(error && error.message)}`.trim(),
      "error"
    );
    context.renderCurrentPreview();
    context.renderReadiness();
  }
}

export async function buildCurrentWork(state, context) {
  if (state.mode === "bulk") {
    if (!state.bulkWorkIds.length || !state.serverAvailable) return;
  } else if (!state.currentRecord || !state.serverAvailable || !currentWorkIsPublished(state)) {
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
        fallbackTargets: bulkPublishedBuildTargets(state)
      });
      for (const target of buildTargets) {
        await applyCatalogueBuild({
          work_id: target.work_id,
          extra_series_ids: Array.isArray(target.extra_series_ids) ? target.extra_series_ids : []
        });
      }
      state.rebuildPending = false;
      state.bulkBuildTargets = [];
      await refreshBuildPreview(state, context);
      const completedAt = utcTimestamp();
      applyActionPresentation(context, state, projectWorkBuildPresentation(state, context, {
        bulk: true,
        count: String(buildTargets.length),
        completedAt
      }));
      return;
    }

    const response = await applyCatalogueBuild({
      work_id: state.currentWorkId,
      extra_series_ids: state.pendingBuildExtraSeriesIds
    });
    state.rebuildPending = false;
    state.pendingBuildExtraSeriesIds = [];
    await refreshBuildPreview(state, context);
    const completedAt = normalizeText(response.completed_at_utc || utcTimestamp());
    applyActionPresentation(context, state, projectWorkBuildPresentation(state, context, { completedAt }));
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

export async function applyPublicationChange(state, context) {
  if (state.mode !== "single" || !state.currentRecord || !state.currentWorkId || !state.serverAvailable) return;
  const action = currentWorkIsPublished(state) ? "unpublish" : currentWorkIsDraft(state) ? "publish" : "";
  if (!action) {
    setTextWithState(context, state.statusNode, t(state, context, "publication_status_invalid", "Publication is available only for draft or published works."), "error");
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
      kind: "work",
      action,
      work_id: state.currentWorkId,
      expected_record_hash: state.currentRecordHash,
      activity_context: buildWorkActivityContext(`${action}-work`, "catalogueWorkPublication", "#catalogueWorkPublication", state.currentWorkId)
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
        defaultText: "Unpublish this work?",
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
        ? t(state, context, "publication_publish_running", "Publishing work…")
        : t(state, context, "publication_unpublish_running", "Unpublishing work…")
    );
    const response = await applyCataloguePublication(request);
    const record = response && response.record && typeof response.record === "object" ? response.record : null;
    if (!record) throw new Error("publication response missing record");

    const workId = state.currentWorkId;
    const recordHash = normalizeText(response.record_hash) || await computeRecordHash(record);
    applyWorkRecordMutation(state, { workId, record, recordHash });
    state.rebuildPending = response.status === "public_update_failed";
    state.pendingBuildExtraSeriesIds = [];
    const lookup = await context.loadWorkLookupRecord(workId).catch(() => null);
    setLoadedWorkRecord(state, workId, record, context.workRouteStateOptions({
      recordHash,
      keepResult: true,
      lookup
    }));
    await refreshBuildPreview(state, context);

    const presentation = projectWorkPublicationPresentation(state, context, action, response);
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

function workMediaSourceFromDraft(state) {
  return {
    project_folder: normalizeText(state.draft && state.draft.project_folder),
    project_subfolder: normalizeText(state.draft && state.draft.project_subfolder),
    project_filename: normalizeText(state.draft && state.draft.project_filename)
  };
}

export async function refreshWorkMedia(state, context) {
  if (!state.currentRecord || !state.currentWorkId || !state.serverAvailable) return;
  state.isBuilding = true;
  context.updateEditorState();
  setTextWithState(context, state.statusNode, t(state, context, "media_refresh_status_running", "Refreshing media…"));
  setTextWithState(context, state.resultNode, "");
  const mediaSource = workMediaSourceFromDraft(state);
  try {
    const response = await applyCatalogueBuild({
      work_id: state.currentWorkId,
      media_only: true,
      force: true,
      media_source: mediaSource
    });
    const blockedCount = countMediaItems(response && response.media, "blocked");
    state.mediaPreviewVersion = String(Date.now());
    await refreshBuildPreview(state, {
      ...context,
      mediaSource: () => mediaSource
    });
    if (blockedCount > 0) {
      setTextWithState(context, state.statusNode, t(state, context, "media_refresh_status_blocked", "Media refresh blocked."), "error");
      setTextWithState(context, state.resultNode, normalizeText(response && response.media && response.media.summary), "error");
      return;
    }
    setTextWithState(context, state.statusNode, t(state, context, "media_refresh_status_success", "Media refresh completed."), "success");
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

export function catalogueRemoteMediaWarning(remoteMedia) {
  if (!remoteMedia || normalizeText(remoteMedia.status) !== "warning") return null;
  const targets = (Array.isArray(remoteMedia.failed_targets) ? remoteMedia.failed_targets : [])
    .map((target) => {
      const kind = normalizeText(target && target.kind);
      const id = normalizeText(target && target.id);
      if (!id) return "";
      return `${kind === "work_details" ? "work detail" : "work"} ${id}`;
    })
    .filter(Boolean);
  return {
    failed: Math.max(0, Math.floor(Number(remoteMedia.failed) || 0)),
    targets
  };
}

export function catalogueDeleteRemoteCleanupWarning(response) {
  return catalogueRemoteMediaWarning(response && response.cleanup && response.cleanup.r2_media);
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
      expected_record_hash: state.currentRecordHash,
      activity_context: buildWorkActivityContext("delete-work", "catalogueWorkDelete", "#catalogueWorkDelete", state.currentWorkId)
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
    const remoteWarning = catalogueDeleteRemoteCleanupWarning(response);
    if (remoteWarning) {
      state.isDeleting = false;
      state.currentRecord = null;
      state.currentRecordHash = "";
      state.baselineDraft = null;
      state.buildPreview = null;
      state.mediaPublishPending = false;
      context.updateEditorState();
      const targetText = remoteWarning.targets.length
        ? remoteWarning.targets.join(", ")
        : state.currentWorkId;
      setTextWithState(
        context,
        state.statusNode,
        t(state, context, "delete_status_r2_cleanup_warning", "Work deleted, but R2 media cleanup needs attention."),
        "warn"
      );
      setTextWithState(
        context,
        state.resultNode,
        t(
          state,
          context,
          "delete_result_r2_cleanup_warning",
          "Remove the remaining R2 primary media manually for: {targets}.",
          { targets: targetText }
        ),
        "warn"
      );
      return;
    }
    window.location.assign(buildStudioRouteUrl(state.config, "catalogue_status"));
  } catch (error) {
    const message = Number(error && error.status) === 409
      ? t(state, context, "delete_status_conflict", "Source record changed since this page loaded. Reload before deleting again.")
      : `${t(state, context, "delete_status_failed", "Source delete failed.")} ${normalizeText(error && error.message)}`.trim();
    state.isDeleting = false;
    context.updateEditorState();
    setTextWithState(context, state.statusNode, message, "error");
  }
}
