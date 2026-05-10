import { getStudioRoute } from "./studio-config.js";
import {
  applyCatalogueBuild,
  applyCatalogueDelete,
  applyCatalogueProseImport,
  applyCataloguePublication,
  createCatalogueSeries,
  previewCatalogueBuild,
  previewCatalogueDelete,
  previewCatalogueProseImport,
  previewCataloguePublication,
  saveCatalogueSeries
} from "./catalogue-editor-service-client.js";
import { computeRecordHash } from "./catalogue-editor-records.js";
import {
  formatCatalogueBuildPreview,
  formatCatalogueDeletePreview,
  formatCataloguePublicationPreview
} from "./catalogue-editor-modal-formatters.js";
import { buildStudioActivityContext } from "./studio-activity-context.js";
import { utcTimestamp } from "./tag-studio-save.js";
import {
  buildCreateSeriesPayload,
  buildSaveSeriesPayload,
  normalizeSeriesId,
  normalizeText,
  normalizeWorkId
} from "./catalogue-series-fields.js";
import {
  buildChangedSeriesWorkUpdates,
  buildSavedSeriesMembershipLookup,
  getCurrentSeriesMemberEntries
} from "./catalogue-series-membership.js";

function t(state, context, key, fallback, tokens = null) {
  return context.text(key, fallback, tokens);
}

function setTextWithState(context, node, text, state = "") {
  context.setTextWithState(node, text, state);
}

function buildSeriesActivityContext(actionId, controlId, controlSelector, seriesId) {
  return buildStudioActivityContext({
    pageId: "catalogue-series",
    actionId,
    route: "/studio/catalogue-series/",
    controlId,
    controlSelector,
    recordIdField: "series_id",
    recordId: seriesId
  });
}

function buildPayload(state, workUpdates) {
  return {
    ...buildSaveSeriesPayload(state, workUpdates),
    apply_build: currentSeriesIsPublished(state),
    activity_context: buildSeriesActivityContext("save-series", "catalogueSeriesSave", "#catalogueSeriesSave", state.currentSeriesId)
  };
}

export function currentSeriesIsPublished(state) {
  return normalizeText(state.draft && state.draft.status).toLowerCase() === "published";
}

export function currentSeriesIsDraft(state) {
  return normalizeText(state.draft && state.draft.status).toLowerCase() === "draft";
}

function applySaveBuildOutcome(state, response) {
  const build = response && response.build && typeof response.build === "object" ? response.build : null;
  if (!currentSeriesIsPublished(state)) {
    state.rebuildPending = false;
    return { kind: response && response.changed ? "saved_unpublished" : "unchanged", stamp: normalizeText(response && response.saved_at_utc) || utcTimestamp() };
  }
  if (!response || !response.build_requested || !build) {
    state.rebuildPending = Boolean(response && response.changed);
    return { kind: response && response.changed ? "saved" : "unchanged", stamp: normalizeText(response && response.saved_at_utc) || utcTimestamp() };
  }
  if (build.ok) {
    state.rebuildPending = false;
    state.pendingBuildExtraWorkIds = [];
    return { kind: "saved_and_updated", stamp: normalizeText(build.completed_at_utc || response.saved_at_utc) || utcTimestamp() };
  }
  state.rebuildPending = true;
  return {
    kind: "saved_update_failed",
    stamp: normalizeText(response.saved_at_utc) || utcTimestamp(),
    error: normalizeText(build.error)
  };
}

export async function refreshBuildPreview(state, context) {
  if (!state.currentSeriesId || !state.serverAvailable || !currentSeriesIsPublished(state)) {
    state.buildPreview = null;
    setTextWithState(context, state.buildImpactNode, "");
    context.renderReadiness();
    return;
  }
  try {
    const response = await previewCatalogueBuild({
      series_id: state.currentSeriesId,
      extra_work_ids: state.pendingBuildExtraWorkIds
    });
    state.buildPreview = response && response.build ? response.build : null;
    setTextWithState(context, state.buildImpactNode, formatCatalogueBuildPreview(state.buildPreview, {
      text: (key, fallback, tokens) => t(state, context, key, fallback, tokens),
      defaultTemplate: "Build preview: work {work_ids}; series {series_ids}; catalogue search {search_rebuild}."
    }));
    context.renderReadiness();
  } catch (error) {
    state.buildPreview = null;
    setTextWithState(
      context,
      state.buildImpactNode,
      `${t(state, context, "build_preview_failed", "Build preview unavailable.")} ${normalizeText(error && error.message)}`.trim(),
      "error"
    );
    context.renderReadiness();
  }
}

export async function importSeriesProse(state, context) {
  if (!state.currentRecord || !state.currentSeriesId || !state.serverAvailable) return;
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
      target_kind: "series",
      series_id: state.currentSeriesId
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
      confirmOverwrite = window.confirm(message);
      if (!confirmOverwrite) {
        setTextWithState(context, state.statusNode, t(state, context, "prose_import_overwrite_cancelled", "Prose import cancelled."), "warning");
        return;
      }
    }
    setTextWithState(context, state.statusNode, t(state, context, "prose_import_running", "Importing staged prose…"));
    const importResponse = await applyCatalogueProseImport({
      target_kind: "series",
      series_id: state.currentSeriesId,
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
  if (!context.draftHasChanges()) {
    setTextWithState(context, state.statusNode, t(state, context, "save_status_no_changes", "No changes to save."));
    setTextWithState(context, state.resultNode, t(state, context, "save_result_unchanged", "Source already matches the current form values."));
    context.updateEditorState();
    return;
  }

  state.isSaving = true;
  context.updateEditorState();
  setTextWithState(
    context,
    state.statusNode,
    currentSeriesIsPublished(state)
      ? t(state, context, "save_status_saving_and_updating", "Saving source record and updating site…")
      : t(state, context, "save_status_saving", "Saving source record…")
  );
  setTextWithState(context, state.resultNode, "");

  try {
    const previousMembers = new Set(Array.from(state.baselineMemberSeriesIdsByWorkId.keys()).filter((workId) => (state.baselineMemberSeriesIdsByWorkId.get(workId) || []).includes(state.currentSeriesId)));
    const currentMembers = new Set(getCurrentSeriesMemberEntries(state).map((entry) => entry.workId));
    const response = await saveCatalogueSeries(buildPayload(state, await buildChangedSeriesWorkUpdates(state)));
    const record = response && response.record && typeof response.record === "object" ? response.record : null;
    if (!record) throw new Error("save response missing record");
    state.seriesById.set(state.currentSeriesId, {
      series_id: state.currentSeriesId,
      title: normalizeText(record.title),
      status: normalizeText(record.status),
      primary_work_id: normalizeText(record.primary_work_id),
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
        status: normalizeText(workRecord.status),
        series_ids: Array.isArray(workRecord.series_ids) ? workRecord.series_ids.slice() : [],
        record_hash: entry.record_hash || state.workSearchById.get(workId)?.record_hash || ""
      });
    });
    const outcome = applySaveBuildOutcome(state, response);
    let pendingBuildExtraWorkIds = [];
    if (response.changed && currentSeriesIsPublished(state) && outcome.kind !== "saved_and_updated") {
      pendingBuildExtraWorkIds = Array.from(previousMembers).filter((workId) => !currentMembers.has(workId));
    }
    const recordHash = normalizeText(response.record_hash) || await computeRecordHash(record);
    context.setLoadedSeries(state.currentSeriesId, record, {
      recordHash,
      keepResult: true,
      lookup: buildSavedSeriesMembershipLookup(state, record, recordHash),
      pendingBuildExtraWorkIds
    });
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
        t(state, context, "save_result_success_unpublished", "Source saved at {saved_at}. Public update is unavailable while the series is not published.", { saved_at: outcome.stamp }),
        "success"
      );
      setTextWithState(context, state.statusNode, t(state, context, "save_status_loaded", "Loaded series {series_id}.", { series_id: state.currentSeriesId }), "success");
    } else {
      setTextWithState(
        context,
        state.resultNode,
        response.changed
          ? t(state, context, "save_result_success", "Source saved at {saved_at}. Public catalogue update still pending.", { saved_at: outcome.stamp })
          : t(state, context, "save_result_unchanged", "Source already matches the current form values."),
        response.changed ? "success" : ""
      );
      setTextWithState(context, state.statusNode, t(state, context, "save_status_loaded", "Loaded series {series_id}.", { series_id: state.currentSeriesId }), "success");
    }
  } catch (error) {
    const isConflict = Number(error && error.status) === 409;
    const message = isConflict
      ? t(state, context, "save_status_conflict", "Source record changed since this page loaded. Reload the series before saving again.")
      : `${t(state, context, "save_status_failed", "Source save failed.")} ${normalizeText(error && error.message)}`.trim();
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
      seriesIdError || t(state, context, "create_status_validation_error", "Fix validation errors before creating the draft series."),
      "error"
    );
    context.updateEditorState();
    return;
  }

  state.isSaving = true;
  context.updateEditorState();
  setTextWithState(context, state.statusNode, t(state, context, "create_status_saving", "Creating draft series..."));
  setTextWithState(context, state.resultNode, "");

  try {
    const response = await createCatalogueSeries({
      ...buildCreateSeriesPayload(state.draft),
      activity_context: buildSeriesActivityContext("create-series", "catalogueSeriesSave", "#catalogueSeriesSave", state.draft.series_id)
    });
    const seriesId = normalizeSeriesId(response && response.series_id);
    const record = response && response.record && typeof response.record === "object" ? response.record : null;
    if (!seriesId) {
      throw new Error("create response missing series id");
    }
    if (record) {
      state.seriesById.set(seriesId, {
        series_id: seriesId,
        title: normalizeText(record.title),
        status: normalizeText(record.status),
        primary_work_id: normalizeText(record.primary_work_id),
        record_hash: normalizeText(response.record_hash)
      });
    }
    state.isSaving = false;
    context.syncRouteBusyState();
    await context.openSeriesById(seriesId);
    setTextWithState(context, state.resultNode, t(state, context, "create_result_success", "Created draft series {series_id}. Opening edit mode...", { series_id: seriesId }), "success");
    setTextWithState(context, state.statusNode, t(state, context, "create_status_success", "Created draft series {series_id}.", { series_id: seriesId }), "success");
  } catch (error) {
    setTextWithState(context, state.statusNode, `${t(state, context, "create_status_failed", "Draft series create failed.")} ${normalizeText(error && error.message)}`.trim(), "error");
    state.isSaving = false;
    context.updateEditorState();
  }
}

export async function buildCurrentSeries(state, context) {
  if (!state.currentRecord || !state.currentSeriesId || !state.serverAvailable) return;
  if (!currentSeriesIsPublished(state)) {
    state.rebuildPending = false;
    context.updateEditorState();
    return;
  }
  state.isBuilding = true;
  context.updateEditorState();
  setTextWithState(context, state.statusNode, t(state, context, "build_status_running", "Updating site…"));
  setTextWithState(context, state.resultNode, "");
  try {
    const response = await applyCatalogueBuild({
      series_id: state.currentSeriesId,
      extra_work_ids: state.pendingBuildExtraWorkIds
    });
    state.rebuildPending = false;
    state.pendingBuildExtraWorkIds = [];
    await refreshBuildPreview(state, context);
    const completedAt = normalizeText(response.completed_at_utc || utcTimestamp());
    setTextWithState(context, state.resultNode, t(state, context, "build_result_success", "Public catalogue updated at {completed_at}. Studio Activity updated.", { completed_at: completedAt }), "success");
    setTextWithState(context, state.statusNode, t(state, context, "build_status_success", "Site update completed."), "success");
  } catch (error) {
    setTextWithState(context, state.statusNode, `${t(state, context, "build_status_failed", "Site update failed.")} ${normalizeText(error && error.message)}`.trim(), "error");
  } finally {
    state.isBuilding = false;
    context.updateEditorState();
  }
}

export async function applyPublicationChange(state, context) {
  if (!state.currentRecord || !state.currentSeriesId || !state.serverAvailable) return;
  const action = currentSeriesIsPublished(state) ? "unpublish" : currentSeriesIsDraft(state) ? "publish" : "";
  if (!action) {
    setTextWithState(context, state.statusNode, t(state, context, "publication_status_invalid", "Publication is available only for draft or published series."), "error");
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
      kind: "series",
      action,
      series_id: state.currentSeriesId,
      expected_record_hash: state.currentRecordHash,
      activity_context: buildSeriesActivityContext(`${action}-series`, "catalogueSeriesPublication", "#catalogueSeriesPublication", state.currentSeriesId)
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
        defaultText: "Unpublish this series?",
        includeDirtyNote: context.draftHasChanges()
      });
      if (!window.confirm(summary)) {
        setTextWithState(context, state.statusNode, t(state, context, "publication_status_cancelled", "Publication change cancelled."));
        return;
      }
    }

    setTextWithState(
      context,
      state.statusNode,
      action === "publish"
        ? t(state, context, "publication_publish_running", "Publishing series…")
        : t(state, context, "publication_unpublish_running", "Unpublishing series…")
    );
    const response = await applyCataloguePublication(request);
    const record = response && response.record && typeof response.record === "object" ? response.record : null;
    if (!record) throw new Error("publication response missing record");

    const recordHash = normalizeText(response.record_hash) || await computeRecordHash(record);
    state.seriesById.set(state.currentSeriesId, {
      series_id: state.currentSeriesId,
      title: normalizeText(record.title),
      status: normalizeText(record.status),
      primary_work_id: normalizeText(record.primary_work_id),
      record_hash: recordHash
    });
    state.rebuildPending = response.status === "public_update_failed";
    state.pendingBuildExtraWorkIds = [];
    context.setLoadedSeries(state.currentSeriesId, record, {
      recordHash,
      keepResult: true,
      lookup: buildSavedSeriesMembershipLookup(state, record, recordHash)
    });
    await refreshBuildPreview(state, context);

    if (response.status === "public_update_failed") {
      const error = normalizeText(response.public_update && response.public_update.error);
      setTextWithState(context, state.statusNode, `${t(state, context, "publication_status_public_failed", "Publication state changed, but the public update failed.")} ${error}`.trim(), "error");
      setTextWithState(context, state.resultNode, t(state, context, "publication_result_public_failed", "Source status changed, but public artifacts did not finish updating."), "warn");
      return;
    }

    if (action === "publish") {
      setTextWithState(context, state.statusNode, t(state, context, "publication_status_published", "Series published."), "success");
      setTextWithState(context, state.resultNode, t(state, context, "publication_result_published", "Series and attached draft works are published, and public catalogue output has been updated."), "success");
    } else {
      setTextWithState(context, state.statusNode, t(state, context, "publication_status_unpublished", "Series unpublished."), "success");
      setTextWithState(context, state.resultNode, t(state, context, "publication_result_unpublished", "Series is draft again and public catalogue output has been cleaned up."), "success");
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

export async function deleteCurrentSeries(state, context) {
  if (!state.currentRecord || !state.currentSeriesId || !state.serverAvailable) return;
  state.isDeleting = true;
  context.updateEditorState();
  setTextWithState(context, state.statusNode, t(state, context, "delete_status_running", "Preparing delete preview…"));
  setTextWithState(context, state.resultNode, "");
  try {
    const request = {
      kind: "series",
      series_id: state.currentSeriesId,
      expected_record_hash: state.currentRecordHash,
      activity_context: buildSeriesActivityContext("delete-series", "catalogueSeriesDelete", "#catalogueSeriesDelete", state.currentSeriesId)
    };
    const previewResponse = await previewCatalogueDelete(request);
    const preview = previewResponse && previewResponse.preview ? previewResponse.preview : null;
    const blockers = Array.isArray(preview && preview.blockers) ? preview.blockers : [];
    const validationErrors = Array.isArray(preview && preview.validation_errors) ? preview.validation_errors : [];
    if ((preview && preview.blocked) || blockers.length || validationErrors.length) {
      const message = blockers[0] || validationErrors[0] || t(state, context, "delete_status_blocked", "Delete is blocked.");
      setTextWithState(context, state.statusNode, message, "error");
      state.isDeleting = false;
      context.updateEditorState();
      return;
    }
    const summary = formatCatalogueDeletePreview(preview, {
      text: (key, fallback, tokens) => t(state, context, key, fallback, tokens),
      defaultText: "Delete this source record?"
    });
    if (!window.confirm(summary)) {
      setTextWithState(context, state.statusNode, t(state, context, "delete_status_cancelled", "Delete cancelled."));
      state.isDeleting = false;
      context.updateEditorState();
      return;
    }
    setTextWithState(context, state.statusNode, t(state, context, "delete_status_running", "Deleting source record…"));
    await applyCatalogueDelete(request);
    const route = getStudioRoute(state.config, "catalogue_status");
    window.location.assign(route);
  } catch (error) {
    const message = Number(error && error.status) === 409
      ? t(state, context, "delete_status_conflict", "Source record changed since this page loaded. Reload before deleting again.")
      : `${t(state, context, "delete_status_failed", "Source delete failed.")} ${normalizeText(error && error.message)}`.trim();
    setTextWithState(context, state.statusNode, message, "error");
    state.isDeleting = false;
    context.updateEditorState();
  }
}
