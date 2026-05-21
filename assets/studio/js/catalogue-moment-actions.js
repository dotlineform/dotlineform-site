import { getStudioRoute } from "./studio-config.js";
import {
  applyCatalogueBuild,
  applyCatalogueDelete,
  applyCatalogueProseImport,
  applyCataloguePublication,
  previewCatalogueBuild,
  previewCatalogueDelete,
  previewCatalogueProseImport,
  previewCataloguePublication,
  saveCatalogueMoment
} from "./catalogue-editor-service-client.js";
import { computeRecordHash } from "./catalogue-editor-records.js";
import {
  formatCatalogueDeletePreview,
  formatCataloguePublicationPreview
} from "./catalogue-editor-modal-formatters.js";
import { confirmCatalogueActionModal } from "./catalogue-editor-action-modals.js";
import {
  extractCatalogueActionPreview,
  getCataloguePreviewBlocker,
  projectCatalogueActionPresentation,
  projectCatalogueSaveOutcomePresentation,
  resolveCatalogueSaveBuildOutcome
} from "./catalogue-editor-action-workflow.js";
import { buildStudioActivityContext } from "./studio-activity-context.js";
import { utcTimestamp } from "./tag-studio-save.js";
import {
  buildSaveMomentPayload,
  normalizeMomentRecord,
  normalizeText
} from "./catalogue-moment-fields.js";

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

function buildMomentActivityContext(actionId, controlId, controlSelector, momentId) {
  return buildStudioActivityContext({
    pageId: "catalogue-moment",
    actionId,
    route: "/studio/catalogue-moment/",
    controlId,
    controlSelector,
    recordIdField: "moment_id",
    recordId: momentId
  });
}

function readDraft(context) {
  return context.readDraft();
}

export function currentMomentIsPublished(state, context) {
  return normalizeText(readDraft(context).status).toLowerCase() === "published";
}

export function currentMomentIsDraft(state, context) {
  return normalizeText(readDraft(context).status).toLowerCase() === "draft";
}

function applySaveBuildOutcome(state, context, payload) {
  const outcome = resolveCatalogueSaveBuildOutcome({
    response: payload,
    isPublished: currentMomentIsPublished(state, context)
  });
  state.needsBuild = outcome.rebuildPending;
  return outcome;
}

function projectMomentSavePresentation(state, context, payload, outcome) {
  const savedAt = { saved_at: outcome.stamp };
  const savedStatus = t(state, context, "save_status_success", "Saved.");
  return projectCatalogueSaveOutcomePresentation({
    outcome,
    changed: Boolean(payload && payload.changed),
    resultLabels: {
      savedAndUpdated: {
        text: t(state, context, "save_result_success_applied", "Saved source changes and updated the public moment at {saved_at}.", savedAt),
        tone: "success"
      },
      savedUpdateFailed: {
        text: t(state, context, "save_result_success_partial", "Source changes were saved at {saved_at}, but the public update failed.", savedAt),
        tone: "warning"
      },
      savedUnpublished: {
        text: t(state, context, "save_result_success_unpublished", "Source saved at {saved_at}.", savedAt),
        tone: "success"
      },
      saved: {
        text: t(state, context, "save_result_success", "Source saved at {saved_at}.", savedAt),
        tone: "success"
      },
      unchanged: {
        text: t(state, context, "save_result_success", "Source saved at {saved_at}.", savedAt),
        tone: "success"
      }
    },
    statusLabels: {
      savedAndUpdated: {
        text: savedStatus,
        tone: "success"
      },
      savedUpdateFailed: {
        text: savedStatus,
        tone: "success"
      },
      loaded: {
        text: savedStatus,
        tone: "success"
      }
    }
  });
}

function projectMomentPublicationPresentation(state, context, action, payload) {
  const publicUpdateFailed = payload && payload.status === "public_update_failed";
  const publicUpdateError = normalizeText(payload && payload.public_update && payload.public_update.error);
  return projectCatalogueActionPresentation({
    resultKey: publicUpdateFailed ? "publicFailed" : action === "publish" ? "published" : "unpublished",
    statusKey: publicUpdateFailed ? "publicFailed" : action === "publish" ? "published" : "unpublished",
    resultLabels: {
      publicFailed: {
        text: t(state, context, "publication_result_public_failed", "Source status changed, but public artifacts did not finish updating."),
        tone: "warning"
      },
      published: {
        text: t(state, context, "publication_result_published", "Moment is published and public output has been updated."),
        tone: "success"
      },
      unpublished: {
        text: t(state, context, "publication_result_unpublished", "Moment is draft again and public output has been cleaned up."),
        tone: "success"
      }
    },
    statusLabels: {
      publicFailed: {
        text: `${t(state, context, "publication_status_public_failed", "Publication state changed, but the public update failed.")} ${publicUpdateError}`.trim(),
        tone: "error"
      },
      published: {
        text: t(state, context, "publication_status_published", "Moment published."),
        tone: "success"
      },
      unpublished: {
        text: t(state, context, "publication_status_unpublished", "Moment unpublished."),
        tone: "success"
      }
    }
  });
}

function projectMomentProseImportPresentation(state, context, payload) {
  return projectCatalogueActionPresentation({
    resultKey: "success",
    statusKey: "success",
    resultLabels: {
      success: {
        text: t(state, context, "prose_import_result_success", "Prose imported to {target_path} at {completed_at}. The next site update will publish it.", {
          target_path: payload && payload.target_path,
          completed_at: payload && payload.imported_at_utc || utcTimestamp()
        }),
        tone: "success"
      }
    },
    statusLabels: {
      success: {
        text: t(state, context, "prose_import_status_success", "Prose import completed."),
        tone: "success"
      }
    }
  });
}

export async function refreshBuildPreview(state, context) {
  if (!state.currentMomentId || !state.serverAvailable) return;
  if (!currentMomentIsPublished(state, context)) {
    state.buildPreview = null;
    context.renderBuildImpact();
    context.renderSummary();
    return;
  }
  try {
    const payload = await previewCatalogueBuild({ moment_id: state.currentMomentId });
    state.buildPreview = payload.build || null;
    context.renderBuildImpact();
    context.renderSummary();
  } catch (error) {
    console.warn("catalogue_moment_actions: build preview failed", error);
    setTextWithState(context, state.buildImpactNode, t(state, context, "build_preview_failed", "Build preview unavailable."));
  }
}

export async function saveCurrentMoment(state, context) {
  if (!state.currentRecord || state.isSaving) return;
  const validation = context.validateDraft();
  if (!validation.valid) {
    setTextWithState(context, state.statusNode, t(state, context, "save_status_validation_error", "Fix validation errors before saving."), "error");
    return;
  }
  if (!context.draftHasChanges()) {
    setTextWithState(context, state.statusNode, t(state, context, "save_status_no_changes", "No changes to save."), "warning");
    setTextWithState(context, state.resultNode, t(state, context, "save_result_unchanged", "Source already matches the current form values."));
    return;
  }

  state.isSaving = true;
  context.updateEditorState();
  const applyBuild = currentMomentIsPublished(state, context);
  setTextWithState(
    context,
    state.statusNode,
    applyBuild ? t(state, context, "save_status_saving_and_updating", "Saving source record and updating public moment...") : t(state, context, "save_status_saving", "Saving source record..."),
    "pending"
  );
  try {
    const payload = await saveCatalogueMoment({
      ...buildSaveMomentPayload(state, {
        draft: validation.draft,
        applyBuild,
        getFieldNodeValue: context.getFieldNodeValue
      }),
      activity_context: buildMomentActivityContext("save-moment", "catalogueMomentSave", "#catalogueMomentSave", state.currentMomentId)
    });
    state.currentRecord = payload.record || validation.draft;
    state.expectedRecordHash = payload.record_hash || await computeRecordHash(state.currentRecord);
    state.moments.set(state.currentMomentId, state.currentRecord);
    const outcome = applySaveBuildOutcome(state, context, payload);
    applyActionPresentation(context, state, projectMomentSavePresentation(state, context, payload, outcome));
    await context.previewMoment(state.currentMomentId);
    context.renderSummary();
  } catch (error) {
    if (error && error.status === 409) {
      setTextWithState(context, state.statusNode, t(state, context, "save_status_conflict", "Source record changed since this page loaded. Reload the moment before saving again."), "error");
    } else {
      setTextWithState(context, state.statusNode, `${t(state, context, "save_status_failed", "Source save failed.")} ${normalizeText(error && error.message)}`.trim(), "error");
    }
  } finally {
    state.isSaving = false;
    context.updateEditorState();
  }
}

export async function applyPublicationChange(state, context) {
  if (!state.currentRecord || !state.currentMomentId || !state.serverAvailable || state.isBuilding) return;
  const action = currentMomentIsPublished(state, context) ? "unpublish" : currentMomentIsDraft(state, context) ? "publish" : "";
  if (!action) {
    setTextWithState(context, state.statusNode, t(state, context, "publication_status_invalid", "Publication is available only for draft or published moments."), "error");
    return;
  }
  if (action === "publish" && context.draftHasChanges()) {
    setTextWithState(context, state.statusNode, t(state, context, "publication_save_first", "Save source changes before publishing."), "error");
    return;
  }
  if (action === "publish") {
    const validation = context.validateDraft();
    if (!validation.valid) {
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
      ? t(state, context, "publication_preview_publish_running", "Preparing publish preview...")
      : t(state, context, "publication_preview_unpublish_running", "Preparing unpublish preview..."),
    "pending"
  );
  setTextWithState(context, state.resultNode, "");
  try {
    const request = {
      kind: "moment",
      action,
      moment_id: state.currentMomentId,
      expected_record_hash: state.expectedRecordHash,
      activity_context: buildMomentActivityContext(`${action}-moment`, "catalogueMomentPublication", "#catalogueMomentPublication", state.currentMomentId)
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
      state.isBuilding = false;
      context.updateEditorState();
      const summary = formatCataloguePublicationPreview(preview, {
        text: (key, fallback, tokens) => t(state, context, key, fallback, tokens),
        defaultText: "Unpublish this moment?",
        includeDirtyNote: context.draftHasChanges()
      });
      const confirmed = await confirmCatalogueActionModal(state, {
        title: t(state, context, "publication_unpublish_confirm_title", "Confirm unpublish"),
        message: summary,
        primaryLabel: t(state, context, "publication_unpublish_confirm_button", "Unpublish"),
        cancelLabel: t(state, context, "confirm_cancel_button", "Cancel"),
        restoreFocus: state.publicationButton
      });
      if (!confirmed) {
        setTextWithState(context, state.statusNode, t(state, context, "publication_status_cancelled", "Publication change cancelled."), "warning");
        return;
      }
      state.isBuilding = true;
      context.updateEditorState();
    }

    setTextWithState(
      context,
      state.statusNode,
      action === "publish"
        ? t(state, context, "publication_publish_running", "Publishing moment...")
        : t(state, context, "publication_unpublish_running", "Unpublishing moment..."),
      "pending"
    );
    const payload = await applyCataloguePublication(request);
    const record = payload && payload.record && typeof payload.record === "object" ? payload.record : null;
    if (!record) throw new Error("publication response missing record");
    state.currentRecord = normalizeMomentRecord(state.currentMomentId, record);
    state.expectedRecordHash = payload.record_hash || await computeRecordHash(state.currentRecord);
    state.moments.set(state.currentMomentId, state.currentRecord);
    const row = state.momentRows.find((item) => item.moment_id === state.currentMomentId);
    if (row) {
      Object.assign(row, state.currentRecord, {
        search: `${state.currentMomentId} ${normalizeText(state.currentRecord.title).toLowerCase()}`
      });
    }
    context.fillForm(state.currentRecord);
    state.needsBuild = payload.status === "public_update_failed";
    await context.previewMoment(state.currentMomentId);
    context.renderSummary();
    const presentation = projectMomentPublicationPresentation(state, context, action, payload);
    applyActionPresentation(context, state, presentation);
    if (payload.status === "public_update_failed") {
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

export async function refreshMomentMedia(state, context) {
  if (!state.currentMomentId || !state.serverAvailable || state.isBuilding || context.draftHasChanges()) return;
  state.isBuilding = true;
  context.updateEditorState();
  setTextWithState(context, state.statusNode, t(state, context, "media_refresh_status_running", "Refreshing media..."), "pending");
  setTextWithState(context, state.resultNode, "");
  try {
    const payload = await applyCatalogueBuild({
      moment_id: state.currentMomentId,
      media_only: true,
      force: true
    });
    const blockedCount = countMediaItems(payload && payload.media, "blocked");
    await context.previewMoment(state.currentMomentId);
    context.renderSummary();
    if (blockedCount > 0) {
      setTextWithState(context, state.statusNode, t(state, context, "media_refresh_status_blocked", "Media refresh blocked."), "error");
      setTextWithState(context, state.resultNode, normalizeText(payload && payload.media && payload.media.summary), "error");
      return;
    }
    setTextWithState(context, state.statusNode, t(state, context, "media_refresh_status_success", "Media refresh completed."), "success");
    setTextWithState(context, state.resultNode, t(state, context, "media_refresh_result_success", "Thumbnails updated; primary variants staged for publishing."), "success");
  } catch (error) {
    setTextWithState(context, state.statusNode, `${t(state, context, "media_refresh_status_failed", "Media refresh failed.")} ${normalizeText(error && error.message)}`.trim(), "error");
  } finally {
    state.isBuilding = false;
    context.updateEditorState();
  }
}

export async function importMomentProse(state, context) {
  if (!state.currentMomentId || context.draftHasChanges()) {
    setTextWithState(context, state.statusNode, t(state, context, "dirty_warning", "Unsaved source changes."), "error");
    return;
  }
  let restoreProseImportFocus = false;
  state.isBuilding = true;
  context.updateEditorState();
  setTextWithState(context, state.statusNode, t(state, context, "prose_import_preview_running", "Previewing staged prose..."), "pending");
  try {
    const preview = await previewCatalogueProseImport({
      target_kind: "moment",
      moment_id: state.currentMomentId
    });
    if (!preview.valid) {
      const errors = Array.isArray(preview.errors) ? preview.errors.join("; ") : "";
      throw new Error(errors || t(state, context, "prose_import_preview_invalid", "Staged prose is not ready to import."));
    }
    if (preview.overwrite_required) {
      state.isBuilding = false;
      context.updateEditorState();
      const confirmed = await confirmCatalogueActionModal(state, {
        title: t(state, context, "prose_import_confirm_title", "Confirm prose overwrite"),
        message: t(
          state,
          context,
          "prose_import_confirm_overwrite",
          "Overwrite existing prose source at {target_path} with staged file {staging_path}?",
          { target_path: preview.target_path, staging_path: preview.staging_path }
        ),
        primaryLabel: t(state, context, "prose_import_confirm_button", "Overwrite"),
        cancelLabel: t(state, context, "confirm_cancel_button", "Cancel"),
        restoreFocus: state.readinessNode && state.readinessNode.querySelector("[data-prose-import]")
      });
      if (!confirmed) {
        setTextWithState(context, state.statusNode, t(state, context, "prose_import_overwrite_cancelled", "Prose import cancelled."), "warning");
        restoreProseImportFocus = true;
        return;
      }
      state.isBuilding = true;
      context.updateEditorState();
    }
    setTextWithState(context, state.statusNode, t(state, context, "prose_import_running", "Importing staged prose..."), "pending");
    const payload = await applyCatalogueProseImport({
      target_kind: "moment",
      moment_id: state.currentMomentId,
      confirm_overwrite: Boolean(preview.overwrite_required)
    });
    state.needsBuild = Boolean(payload.changed);
    applyActionPresentation(context, state, projectMomentProseImportPresentation(state, context, payload));
    await context.previewMoment(state.currentMomentId);
    context.renderSummary();
  } catch (error) {
    setTextWithState(context, state.statusNode, `${t(state, context, "prose_import_status_failed", "Prose import failed.")} ${normalizeText(error && error.message)}`.trim(), "error");
  } finally {
    state.isBuilding = false;
    context.updateEditorState();
    if (restoreProseImportFocus && state.readinessNode) {
      const proseImportButton = state.readinessNode.querySelector("[data-prose-import]");
      if (proseImportButton && typeof proseImportButton.focus === "function") {
        proseImportButton.focus({ preventScroll: true });
      }
    }
  }
}

export async function deleteCurrentMoment(state, context) {
  if (!state.currentRecord || !state.serverAvailable || state.isDeleting) return;
  state.isDeleting = true;
  context.updateEditorState();
  setTextWithState(context, state.statusNode, t(state, context, "delete_status_running", "Preparing delete preview..."), "pending");
  setTextWithState(context, state.resultNode, "");
  try {
    const request = {
      kind: "moment",
      moment_id: state.currentMomentId,
      expected_record_hash: state.expectedRecordHash,
      activity_context: buildMomentActivityContext("delete-moment", "catalogueMomentDelete", "#catalogueMomentDelete", state.currentMomentId)
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
      setTextWithState(context, state.statusNode, t(state, context, "delete_status_cancelled", "Delete cancelled."), "warning");
      state.isDeleting = false;
      context.updateEditorState();
      return;
    }
    state.isDeleting = true;
    context.updateEditorState();
    setTextWithState(context, state.statusNode, t(state, context, "delete_status_deleting", "Deleting source record..."), "pending");
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
