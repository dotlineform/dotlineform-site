import { getStudioRoute } from "./studio-config.js";
import {
  applyCatalogueBuild,
  applyCatalogueDelete,
  applyCatalogueProseImport,
  applyCataloguePublication,
  createCatalogueWork,
  previewCatalogueBuild,
  previewCatalogueDelete,
  previewCatalogueProseImport,
  previewCataloguePublication,
  saveCatalogueBulkRecords,
  saveCatalogueWork
} from "./catalogue-editor-service-client.js";
import { computeRecordHash } from "./catalogue-editor-records.js";
import {
  formatCatalogueBuildPreview,
  formatCatalogueDeletePreview,
  formatCataloguePublicationPreview
} from "./catalogue-editor-modal-formatters.js";
import { confirmCatalogueActionModal } from "./catalogue-editor-action-modals.js";
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
} from "./tag-studio-save.js";
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

function t(state, context, key, fallback, tokens = null) {
  return context.text(key, fallback, tokens);
}

function setTextWithState(context, node, text, state = "") {
  context.setTextWithState(node, text, state);
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

function previewExtraSeriesIdsForDraft(state) {
  const previousSeriesIds = parseSeriesIds(state.baselineDraft && state.baselineDraft.series_ids);
  const nextSeriesIds = parseSeriesIds(state.draft && state.draft.series_ids);
  return dedupeSeriesIds([
    ...state.pendingBuildExtraSeriesIds,
    ...previousSeriesIds
  ]).filter((seriesId) => !nextSeriesIds.includes(seriesId));
}

function applySingleSaveBuildOutcome(state, response) {
  const build = response && response.build && typeof response.build === "object" ? response.build : null;
  if (!currentWorkIsPublished(state)) {
    state.rebuildPending = false;
    state.pendingBuildExtraSeriesIds = [];
    return { kind: response && response.changed ? "saved_unpublished" : "unchanged", stamp: normalizeText(response && response.saved_at_utc) || utcTimestamp() };
  }
  if (!response || !response.build_requested || !build) {
    state.rebuildPending = Boolean(response && response.changed);
    return { kind: response && response.changed ? "saved" : "unchanged", stamp: normalizeText(response && response.saved_at_utc) || utcTimestamp() };
  }
  if (build.ok) {
    state.rebuildPending = false;
    state.pendingBuildExtraSeriesIds = [];
    return { kind: "saved_and_updated", stamp: normalizeText(build.completed_at_utc || response.saved_at_utc) || utcTimestamp() };
  }
  state.rebuildPending = true;
  return {
    kind: "saved_update_failed",
    stamp: normalizeText(response.saved_at_utc) || utcTimestamp(),
    error: normalizeText(build.error)
  };
}

function applyBulkSaveBuildOutcome(state, response, fallbackBuildTargets) {
  const build = response && response.build && typeof response.build === "object" ? response.build : null;
  if (!response || !response.build_requested || !build) {
    state.rebuildPending = Boolean(response && response.changed);
    state.bulkBuildTargets = fallbackBuildTargets;
    return { kind: response && response.changed ? "saved" : "unchanged", stamp: normalizeText(response && response.saved_at_utc) || utcTimestamp() };
  }
  if (build.ok) {
    state.rebuildPending = false;
    state.bulkBuildTargets = [];
    return { kind: "saved_and_updated", stamp: normalizeText(build.completed_at_utc || response.saved_at_utc) || utcTimestamp() };
  }
  state.rebuildPending = true;
  state.bulkBuildTargets = Array.isArray(build.remaining_targets) ? build.remaining_targets : fallbackBuildTargets;
  return {
    kind: "saved_update_failed",
    stamp: normalizeText(response.saved_at_utc) || utcTimestamp(),
    error: normalizeText(build.error)
  };
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
      changedRecords.forEach((item) => {
        const workId = normalizeWorkId(item && item.work_id);
        const record = item && item.record && typeof item.record === "object" ? item.record : null;
        if (!workId || !record) return;
        state.sourceWorkRecordsById.set(workId, record);
        state.bulkRecords.set(workId, record);
        state.bulkRecordHashes.set(workId, normalizeText(item.record_hash) || "");
        state.workSearchById.set(workId, {
          work_id: workId,
          title: normalizeText(record.title),
          year_display: normalizeText(record.year_display),
          status: normalizeText(record.status),
          series_ids: Array.isArray(record.series_ids) ? record.series_ids.slice() : [],
          record_hash: normalizeText(item.record_hash)
        });
      });
      const fallbackBuildTargets = Array.isArray(response && response.build_targets) ? response.build_targets : [];
      const outcome = applyBulkSaveBuildOutcome(state, response, fallbackBuildTargets);
      setLoadedBulkWorks(state, state.bulkWorkIds, state.bulkRecords, state.bulkRecordHashes, context.workRouteStateOptions({
        keepResult: true,
        buildTargets: state.bulkBuildTargets
      }));
      if (outcome.kind === "saved_and_updated") {
        setTextWithState(
          context,
          state.resultNode,
          t(state, context, "bulk_save_result_success_applied", "Saved {count} work records and updated public catalogue output for published records at {saved_at}.", {
            count: String(response.changed_count || 0),
            saved_at: outcome.stamp
          }),
          "success"
        );
        setTextWithState(context, state.statusNode, t(state, context, "build_status_success", "Site update completed."), "success");
      } else if (outcome.kind === "saved_update_failed") {
        setTextWithState(
          context,
          state.resultNode,
          t(state, context, "bulk_save_result_success_partial", "Saved {count} work records at {saved_at}, but the public update failed.", {
            count: String(response.changed_count || 0),
            saved_at: outcome.stamp
          }),
          "warn"
        );
        setTextWithState(context, state.statusNode, `${t(state, context, "build_status_failed", "Site update failed.")} ${outcome.error}`.trim(), "error");
      } else {
        setTextWithState(
          context,
          state.resultNode,
          response.changed
            ? t(state, context, "bulk_save_result_success", "Saved {count} work records at {saved_at}.", {
              count: String(response.changed_count || 0),
              saved_at: outcome.stamp
            })
            : t(state, context, "save_result_unchanged", "Source already matches the current form values."),
          response.changed ? "success" : ""
        );
        setTextWithState(
          context,
          state.statusNode,
          t(state, context, "bulk_status_loaded", "Loaded {count} work records.", { count: String(state.bulkWorkIds.length) }),
          response.changed ? "success" : ""
        );
      }
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
    state.sourceWorkRecordsById.set(state.currentWorkId, record);
    state.workSearchById.set(state.currentWorkId, {
      work_id: state.currentWorkId,
      title: normalizeText(record.title),
      year_display: normalizeText(record.year_display),
      status: normalizeText(record.status),
      series_ids: Array.isArray(record.series_ids) ? record.series_ids.slice() : [],
      record_hash: normalizeText(response.record_hash)
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
    setLoadedWorkRecord(state, state.currentWorkId, record, context.workRouteStateOptions({
      recordHash: response.record_hash || normalizeText(lookup && lookup.record_hash) || "",
      keepResult: true,
      lookup
    }));
    await refreshBuildPreview(state, context);
    if (outcome.kind === "saved_and_updated") {
      setTextWithState(
        context,
        state.resultNode,
        t(state, context, "save_result_success_applied", "Saved source changes and updated the public catalogue at {saved_at}.", { saved_at: outcome.stamp }),
        "success"
      );
      setTextWithState(context, state.statusNode, t(state, context, "build_status_success", "Site update completed."), "success");
    } else if (outcome.kind === "saved_update_failed") {
      setTextWithState(
        context,
        state.resultNode,
        t(state, context, "save_result_success_partial", "Source changes were saved at {saved_at}, but the public update failed.", { saved_at: outcome.stamp }),
        "warn"
      );
      setTextWithState(context, state.statusNode, `${t(state, context, "build_status_failed", "Site update failed.")} ${outcome.error}`.trim(), "error");
    } else if (outcome.kind === "saved_unpublished") {
      setTextWithState(
        context,
        state.resultNode,
        t(state, context, "save_result_success_unpublished", "Source saved at {saved_at}. Public update is unavailable while the work is not published.", { saved_at: outcome.stamp }),
        "success"
      );
      setTextWithState(context, state.statusNode, t(state, context, "save_status_loaded", "Loaded work {work_id}.", { work_id: state.currentWorkId }), "success");
    } else {
      setTextWithState(
        context,
        state.resultNode,
        response.changed
          ? t(state, context, "save_result_success", "Source saved at {saved_at}.", { saved_at: outcome.stamp })
          : t(state, context, "save_result_unchanged", "Source already matches the current form values."),
        response.changed ? "success" : ""
      );
      setTextWithState(context, state.statusNode, t(state, context, "save_status_loaded", "Loaded work {work_id}.", { work_id: state.currentWorkId }), "success");
    }
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
      state.sourceWorkRecordsById.set(workId, record);
      state.workSearchById.set(workId, {
        work_id: workId,
        title: normalizeText(record.title),
        year_display: normalizeText(record.year_display),
        status: normalizeText(record.status),
        series_ids: Array.isArray(record.series_ids) ? record.series_ids.slice() : [],
        record_hash: normalizeText(response.record_hash)
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
    const response = await previewCatalogueBuild({
      work_id: state.currentWorkId,
      extra_series_ids: state.pendingBuildExtraSeriesIds
    });
    state.buildPreview = response && response.build ? response.build : null;
    setTextWithState(context, state.buildImpactNode, formatCatalogueBuildPreview(state.buildPreview, {
      text: (key, fallback, tokens) => t(state, context, key, fallback, tokens),
      defaultTemplate: "Public update preview: work {work_ids}; series {series_ids}; catalogue search {search_rebuild}."
    }));
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

export async function previewCurrentBuildImpact(state, context) {
  if (!state.currentRecord || !state.currentWorkId || state.mode !== "single") return;
  if (!state.serverAvailable) {
    setTextWithState(context, state.statusNode, t(state, context, "build_preview_server_unavailable", "Local catalogue server unavailable."), "error");
    return;
  }
  if (!currentWorkIsPublished(state)) {
    setTextWithState(context, state.statusNode, t(state, context, "build_preview_unpublished", "Public update unavailable while the work is not published."), "warn");
    return;
  }
  if (state.validationErrors.size > 0) {
    setTextWithState(context, state.statusNode, t(state, context, "save_status_validation_error", "Fix validation errors before saving."), "error");
    return;
  }
  const changedFields = context.changedWorkFieldNames();
  if (!changedFields.length) {
    setTextWithState(context, state.statusNode, t(state, context, "build_preview_no_changes", "No unsaved changes to preview."));
    return;
  }

  state.isPreviewingBuild = true;
  context.updateEditorState();
  setTextWithState(context, state.statusNode, t(state, context, "build_preview_status_running", "Preparing public update preview..."));
  let openedPreviewModal = false;
  try {
    const response = await previewCatalogueBuild({
      work_id: state.currentWorkId,
      record_family: "work",
      changed_fields: changedFields,
      extra_series_ids: previewExtraSeriesIdsForDraft(state)
    });
    setTextWithState(context, state.statusNode, t(state, context, "save_status_loaded", "Loaded work {work_id}.", { work_id: state.currentWorkId }));
    state.isPreviewingBuild = false;
    context.updateEditorState();
    context.openBuildPreviewModal(response, changedFields);
    openedPreviewModal = true;
  } catch (error) {
    setTextWithState(
      context,
      state.statusNode,
      `${t(state, context, "build_preview_failed", "Public update preview unavailable.")} ${normalizeText(error && error.message)}`.trim(),
      "error"
    );
  } finally {
    if (!openedPreviewModal) {
      state.isPreviewingBuild = false;
      context.updateEditorState();
    }
  }
}

export async function importWorkProse(state, context) {
  if (!state.currentRecord || !state.currentWorkId || !state.serverAvailable) return;
  if (context.draftHasChanges()) {
    setTextWithState(context, state.statusNode, t(state, context, "prose_import_save_first", "Save source changes before importing prose."), "error");
    return;
  }

  state.isBuilding = true;
  context.updateEditorState();
  setTextWithState(context, state.statusNode, t(state, context, "prose_import_preview_running", "Previewing staged prose…"));
  setTextWithState(context, state.resultNode, "");
  try {
    const preview = await previewCatalogueProseImport({
      target_kind: "work",
      work_id: state.currentWorkId
    });
    if (!preview.valid) {
      const errors = Array.isArray(preview.errors) ? preview.errors.join(" ") : "";
      throw new Error(errors || t(state, context, "prose_import_preview_invalid", "Staged prose is not ready to import."));
    }
    let confirmOverwrite = false;
    if (preview.overwrite_required) {
      const message = t(
        state,
        context,
        "prose_import_confirm_overwrite",
        "Overwrite existing prose source at {target_path} with staged file {staging_path}?",
        {
          target_path: normalizeText(preview.target_path),
          staging_path: normalizeText(preview.staging_path)
        }
      );
      state.isBuilding = false;
      context.updateEditorState();
      const proseRestoreFocus = state.readinessNode && state.readinessNode.querySelector('[data-prose-import="work"]');
      confirmOverwrite = await confirmCatalogueActionModal(state, {
        title: t(state, context, "prose_import_confirm_title", "Confirm prose overwrite"),
        message,
        primaryLabel: t(state, context, "prose_import_confirm_button", "Overwrite"),
        cancelLabel: t(state, context, "confirm_cancel_button", "Cancel"),
        restoreFocus: proseRestoreFocus
      });
      if (!confirmOverwrite) {
        setTextWithState(context, state.statusNode, t(state, context, "prose_import_overwrite_cancelled", "Prose import cancelled."), "warning");
        return;
      }
      state.isBuilding = true;
      context.updateEditorState();
    }
    setTextWithState(context, state.statusNode, t(state, context, "prose_import_running", "Importing staged prose…"));
    const importResponse = await applyCatalogueProseImport({
      target_kind: "work",
      work_id: state.currentWorkId,
      confirm_overwrite: confirmOverwrite
    });
    await refreshBuildPreview(state, context);
    const completedAt = normalizeText(importResponse.imported_at_utc || utcTimestamp());
    setTextWithState(
      context,
      state.resultNode,
      t(state, context, "prose_import_result_success", "Prose imported to {target_path} at {completed_at}. The next site update will publish it.", {
        completed_at: completedAt,
        target_path: normalizeText(importResponse.target_path)
      }),
      "success"
    );
    setTextWithState(context, state.statusNode, t(state, context, "prose_import_status_success", "Prose import completed."), "success");
  } catch (error) {
    setTextWithState(
      context,
      state.statusNode,
      `${t(state, context, "prose_import_status_failed", "Prose import failed.")} ${normalizeText(error && error.message)}`.trim(),
      "error"
    );
  } finally {
    state.isBuilding = false;
    context.updateEditorState();
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
      const buildTargets = state.rebuildPending && state.bulkBuildTargets.length
        ? state.bulkBuildTargets
        : bulkPublishedBuildTargets(state);
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
      setTextWithState(
        context,
        state.resultNode,
        t(state, context, "bulk_build_result_success", "Updated {count} work scopes at {completed_at}. Studio Activity updated.", {
          count: String(buildTargets.length),
          completed_at: completedAt
        }),
        "success"
      );
      setTextWithState(context, state.statusNode, t(state, context, "build_status_success", "Site update completed."), "success");
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
    setTextWithState(
      context,
      state.resultNode,
      t(state, context, "build_result_success", "Public catalogue updated at {completed_at}. Studio Activity updated.", { completed_at: completedAt }),
      "success"
    );
    setTextWithState(context, state.statusNode, t(state, context, "build_status_success", "Site update completed."), "success");
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
    const preview = previewResponse && previewResponse.preview ? previewResponse.preview : null;
    const blockers = Array.isArray(preview && preview.blockers) ? preview.blockers : [];
    if ((preview && preview.blocked) || blockers.length) {
      const message = blockers[0] || t(state, context, "publication_status_blocked", "Publication change is blocked.");
      setTextWithState(context, state.statusNode, message, "error");
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
    state.sourceWorkRecordsById.set(workId, record);
    state.workSearchById.set(workId, {
      work_id: workId,
      title: normalizeText(record.title),
      year_display: normalizeText(record.year_display),
      status: normalizeText(record.status),
      series_ids: Array.isArray(record.series_ids) ? record.series_ids.slice() : [],
      record_hash: recordHash
    });
    state.rebuildPending = response.status === "public_update_failed";
    state.pendingBuildExtraSeriesIds = [];
    const lookup = await context.loadWorkLookupRecord(workId).catch(() => null);
    setLoadedWorkRecord(state, workId, record, context.workRouteStateOptions({
      recordHash,
      keepResult: true,
      lookup
    }));
    await refreshBuildPreview(state, context);

    if (response.status === "public_update_failed") {
      const error = normalizeText(response.public_update && response.public_update.error);
      setTextWithState(context, state.statusNode, `${t(state, context, "publication_status_public_failed", "Publication state changed, but the public update failed.")} ${error}`.trim(), "error");
      setTextWithState(context, state.resultNode, t(state, context, "publication_result_public_failed", "Source status changed, but public artifacts did not finish updating."), "warn");
      return;
    }

    if (action === "publish") {
      setTextWithState(context, state.statusNode, t(state, context, "publication_status_published", "Work published."), "success");
      setTextWithState(context, state.resultNode, t(state, context, "publication_result_published", "Work is published and public catalogue output has been updated."), "success");
    } else {
      setTextWithState(context, state.statusNode, t(state, context, "publication_status_unpublished", "Work unpublished."), "success");
      setTextWithState(context, state.resultNode, t(state, context, "publication_result_unpublished", "Work is draft again and public catalogue output has been cleaned up."), "success");
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

export async function refreshWorkMedia(state, context) {
  if (!state.currentRecord || !state.currentWorkId || !state.serverAvailable || context.draftHasChanges()) return;
  state.isBuilding = true;
  context.updateEditorState();
  setTextWithState(context, state.statusNode, t(state, context, "media_refresh_status_running", "Refreshing media…"));
  setTextWithState(context, state.resultNode, "");
  try {
    const response = await applyCatalogueBuild({
      work_id: state.currentWorkId,
      media_only: true,
      force: true
    });
    const blockedCount = countMediaItems(response && response.media, "blocked");
    await refreshBuildPreview(state, context);
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
    const preview = previewResponse && previewResponse.preview ? previewResponse.preview : null;
    const blockers = Array.isArray(preview && preview.blockers) ? preview.blockers : [];
    const validationErrors = Array.isArray(preview && preview.validation_errors) ? preview.validation_errors : [];
    if ((preview && preview.blocked) || blockers.length || validationErrors.length) {
      const message = blockers[0] || validationErrors[0] || t(state, context, "delete_status_blocked", "Delete is blocked.");
      state.isDeleting = false;
      context.updateEditorState();
      setTextWithState(context, state.statusNode, message, "error");
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
      return;
    }
    state.isDeleting = true;
    context.updateEditorState();
    setTextWithState(context, state.statusNode, t(state, context, "delete_status_running", "Deleting source record…"));
    await applyCatalogueDelete(request);
    const route = getStudioRoute(state.config, "catalogue_status");
    window.location.assign(route);
  } catch (error) {
    const message = Number(error && error.status) === 409
      ? t(state, context, "delete_status_conflict", "Source record changed since this page loaded. Reload before deleting again.")
      : `${t(state, context, "delete_status_failed", "Source delete failed.")} ${normalizeText(error && error.message)}`.trim();
    state.isDeleting = false;
    context.updateEditorState();
    setTextWithState(context, state.statusNode, message, "error");
  }
}
