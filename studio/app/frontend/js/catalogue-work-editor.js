import {
  getStudioText
} from "./studio-config.js";
import {
  applyCatalogueEditorMediaAttrs
} from "./catalogue-editor-shell-media.js";
import {
  loadCatalogueMediaConfig
} from "./catalogue-media-preview.js";
import {
  loadStudioLookupRecordJson
} from "./studio-data.js";
import {
  configureCatalogueEditorRouteRuntime,
  loadCatalogueEditorLookupMaps,
  revealCatalogueEditorRoute,
  setCatalogueEditorTextWithState as setNodeTextWithState,
  showCatalogueEditorInitError
} from "./catalogue-editor-route-boot.js";
import {
  catalogueDeleteDisabled,
  catalogueDirtyWarningText,
  catalogueDraftHasChanges,
  catalogueSaveDisabled
} from "./catalogue-editor-dirty-state.js";
import {
  WORK_DOWNLOAD_FIELDS as DOWNLOAD_FIELDS,
  WORK_LINK_FIELDS as LINK_FIELDS,
  validateWorkEmbeddedItems
} from "./catalogue-editor-embedded-items.js";
import {
  confirmWorkEmbeddedDeleteModal,
  openWorkDetailSectionEditModal,
  openWorkEmbeddedEntryModal
} from "./catalogue-work-editor-modals.js";
import {
  openProjectMediaMultiFileModal
} from "./catalogue-project-media-picker.js";
import {
  applyCatalogueDelete,
  createCatalogueWorkDetailSection,
  previewCatalogueDelete,
  readProjectMediaFiles,
  readProjectMediaFolders,
  saveCatalogueWorkDetailSection
} from "./catalogue-editor-service-client.js";
import {
  formatCatalogueDeletePreview
} from "./catalogue-editor-modal-formatters.js";
import {
  confirmCatalogueActionModal
} from "./catalogue-editor-action-modals.js";
import {
  extractCatalogueActionPreview,
  getCataloguePreviewBlocker
} from "./catalogue-editor-action-workflow.js";
import {
  buildStudioActivityContext
} from "./studio-activity-context.js";
import {
  renderWorkCurrentPreview,
  renderWorkReadiness,
  updateWorkSummary
} from "./catalogue-work-sections.js";
import {
  updateWorkDetailBrowser
} from "./catalogue-work-detail-browser.js";
import {
  applyDraftToInputs,
  applyReadonly,
  applyWorkFormText,
  clearReadonlyFields,
  getFieldNodeValue,
  renderWorkEditorFields,
  setFieldNodeValue,
  setModeFieldAvailability,
  updateFieldMessages
} from "./catalogue-work-form.js";
import {
  initializeWorkRouteState,
  setEmptySearchMode,
  setLoadedBulkWorks,
  setLoadedWorkRecord,
  setNewWorkMode,
  syncWorkRouteBusyState
} from "./catalogue-work-route-state.js";
import {
  applyPublicationChange,
  bulkPublishedBuildTargets,
  bulkSelectionHasPublishedRecords,
  catalogueDeleteRemoteCleanupWarning,
  catalogueRemoteMediaWarning,
  currentWorkIsDraft,
  currentWorkIsPublished,
  deleteCurrentWork,
  parseBulkSeriesOperation,
  refreshBuildPreview,
  refreshWorkMedia
} from "./catalogue-work-actions.js";
import {
  saveWorkThenPublishMedia,
  workSaveActionRequired
} from "./catalogue-work-media-publish.js";
import {
  applyInitialWorkRouteSelection,
  bindWorkSelectionControls,
  openWorkById,
  setWorkSelectionPopupVisibility
} from "./catalogue-work-selection.js";
import {
  WORK_DATE_RE as DATE_RE,
  WORK_DIMENSION_FIELD_KEYS,
  WORK_EDITABLE_FIELDS as EDITABLE_FIELDS,
  WORK_SERIES_ID_RE as SERIES_ID_RE,
  WORK_STATUS_OPTIONS as STATUS_OPTIONS,
  canonicalizeWorkScalar as canonicalizeScalar,
  embeddedEntriesEqual,
  normalizeSeriesId,
  normalizeText,
  normalizeWorkId,
  parseSeriesIds,
  suggestNextWorkId
} from "./catalogue-work-fields.js";
import {
  bindWorkEditorEvents
} from "./catalogue-work-editor-events.js";
import {
  createCatalogueEditorMessageController,
  firstCatalogueValidationMessage
} from "./catalogue-editor-message-controller.js";
import {
  WORK_ROUTE_STATE,
  collectWorkEditorElements,
  createWorkEditorState,
  createWorkRouteStateOptions
} from "./catalogue-work-editor-state.js";

const REQUIRED_WORK_FIELDS = ["title", "year", "year_display", "series_ids"];

function setOpenInputMode(state) {
  state.searchNode.placeholder = t(state, "search_placeholder", "find work id(s): 00001, 00003-00005");
  state.searchNode.setAttribute("aria-label", t(state, "search_label", "Find work by id"));
}

async function loadWorkLookupRecord(state, workId) {
  return loadStudioLookupRecordJson(state.config, "catalogue_work_record", workId, {
    cache: "no-store",
    catalogueServerAvailable: state.serverAvailable
  });
}

async function openEmbeddedEntryModal(state, kind, index = null) {
  const result = await openWorkEmbeddedEntryModal(state, kind, index, {
    text: (key, fallback, tokens) => t(state, key, fallback, tokens)
  });
  if (!result || !result.confirmed) return;
  clearActionMessages(state);
  state.draft[result.entriesKey] = result.entries;
  updateEditorState(state);
  if (!result.editing) {
    const addActionSelector = result.entriesKey === "downloads"
      ? '#catalogueWorkResourcesActions [data-record-list-action="new-download"]'
      : '#catalogueWorkResourcesActions [data-record-list-action="new-link"]';
    window.setTimeout(() => {
      const addButton = document.querySelector(addActionSelector);
      if (addButton && typeof addButton.focus === "function") addButton.focus();
    }, 0);
  }
}

async function deleteEmbeddedEntry(state, kind, index) {
  const result = await confirmWorkEmbeddedDeleteModal(state, kind, index, {
    text: (key, fallback, tokens) => t(state, key, fallback, tokens)
  });
  if (!result || !result.confirmed) return;
  clearActionMessages(state);
  state.draft[result.entriesKey] = result.entries;
  updateEditorState(state);
}

function usedDetailSubfolders(state) {
  const sections = state.currentLookup && Array.isArray(state.currentLookup.detail_sections)
    ? state.currentLookup.detail_sections
    : [];
  return sections
    .map((section) => normalizeText(section && section.details_subfolder))
    .filter(Boolean);
}

async function openDetailSectionPicker(state) {
  if (!state.currentRecord || state.mode === "bulk") return null;
  clearActionMessages(state);
  const result = await openProjectMediaMultiFileModal(state, {
    text: (key, fallback, tokens) => t(state, key, fallback, tokens),
    initialSelection: {
      project_folder: state.currentRecord.project_folder || state.draft.project_folder || ""
    },
    disabledSubfolders: usedDetailSubfolders(state),
    loadProjectFolders: (query) => readProjectMediaFolders(query),
    loadProjectFiles: (request) => readProjectMediaFiles(request)
  });
  if (!result || !result.confirmed) return result;
  const selection = result.selection || {};
  const filenames = Array.isArray(selection.filenames) ? selection.filenames : [];
  state.isSaving = true;
  syncWorkRouteBusyState(state);
  renderEditorMessage(state);
  try {
    state.messageController.setActionTextWithState(
      state.statusNode,
      t(state, "detail_section_create_status_running", "Creating detail section..."),
      "info"
    );
    const payload = await createCatalogueWorkDetailSection({
      work_id: state.currentWorkId,
      project_folder: selection.project_folder,
      project_subfolder: selection.project_subfolder,
      filenames
    });
    const remoteWarning = catalogueRemoteMediaWarning(payload && payload.r2_media);
    const sectionId = normalizeText(payload && payload.section_id);
    if (sectionId) state.detailBrowserSelectedSectionId = sectionId;
    state.currentLookup = await loadWorkLookupRecord(state, state.currentWorkId);
    if (sectionId) state.detailBrowserSelectedSectionId = sectionId;
    updateSummary(state);
    if (payload && payload.reason === "section_exists") {
      state.messageController.setActionTextWithState(
        state.resultNode,
        t(state, "detail_section_create_status_exists", "Detail section already exists."),
        "info"
      );
    } else if (remoteWarning) {
      const targetText = remoteWarning.targets.length
        ? remoteWarning.targets.join(", ")
        : (payload.created_detail_uids || []).join(", ");
      state.messageController.setActionTextWithState(
        state.statusNode,
        t(state, "detail_section_create_status_r2_warning", "Detail section created, but R2 media publishing needs attention."),
        "warn"
      );
      state.messageController.setActionTextWithState(
        state.resultNode,
        t(
          state,
          "detail_section_create_result_r2_warning",
          "Publish the remaining R2 primary media manually for: {targets}.",
          { targets: targetText }
        ),
        "warn"
      );
    } else {
      state.messageController.setActionTextWithState(
        state.resultNode,
        t(state, "detail_section_create_status_created", "Created detail section with {count} detail file(s).", {
          count: String(payload && payload.created_count != null ? payload.created_count : filenames.length)
        }),
        "success"
      );
    }
  } catch (error) {
    state.messageController.setActionTextWithState(
      state.resultNode,
      normalizeText(error && error.message) || t(state, "detail_section_create_status_failed", "Detail section create failed."),
      "error"
    );
  } finally {
    state.isSaving = false;
    syncWorkRouteBusyState(state);
    renderEditorMessage(state);
  }
  return result;
}

async function editDetailSection(state, row, rows = []) {
  if (!state.currentRecord || state.mode === "bulk" || !state.serverAvailable) return;
  const sectionId = normalizeText(row && row.id);
  if (!sectionId) return;
  clearActionMessages(state);
  const result = await openWorkDetailSectionEditModal(state, row, rows, {
    text: (key, fallback, tokens) => t(state, key, fallback, tokens)
  });
  if (!result || !result.confirmed) return;
  if (!result.changed) {
    state.messageController.setActionTextWithState(
      state.resultNode,
      t(state, "detail_section_edit_status_unchanged", "Detail section already matches the current values."),
      "info"
    );
    return;
  }
  state.isSaving = true;
  syncWorkRouteBusyState(state);
  renderEditorMessage(state);
  state.messageController.setActionTextWithState(
    state.statusNode,
    t(state, "detail_section_edit_status_saving", "Saving detail section..."),
    "info"
  );
  state.messageController.setActionTextWithState(state.resultNode, "");
  try {
    await saveCatalogueWorkDetailSection({
      work_id: state.currentWorkId,
      ...(result.payload || {})
    });
    state.currentLookup = await loadWorkLookupRecord(state, state.currentWorkId);
    state.detailBrowserSelectedSectionId = sectionId;
    updateSummary(state);
    state.messageController.setActionTextWithState(
      state.resultNode,
      t(state, "detail_section_edit_status_saved", "Saved detail section {section_id}.", {
        section_id: sectionId
      }),
      "success"
    );
    state.messageController.setActionTextWithState(state.statusNode, "");
  } catch (error) {
    state.messageController.setActionTextWithState(
      state.statusNode,
      `${t(state, "detail_section_edit_status_failed", "Detail section save failed.")} ${normalizeText(error && error.message)}`.trim(),
      "error"
    );
  } finally {
    state.isSaving = false;
    syncWorkRouteBusyState(state);
    renderEditorMessage(state);
  }
}

function buildDetailSectionActivityContext(sectionId) {
  return buildStudioActivityContext({
    pageId: "catalogue-work",
    actionId: "delete-work-detail-section",
    route: "/studio/catalogue-work/",
    controlId: "catalogueWorkDetailBrowserSectionActions",
    controlSelector: "#catalogueWorkDetailBrowserSectionActions",
    recordIdField: "section_id",
    recordId: sectionId
  });
}

async function deleteDetailSection(state, row) {
  if (!state.currentRecord || state.mode === "bulk" || !state.serverAvailable) return;
  const sectionId = normalizeText(row && row.id);
  if (!sectionId) return;
  const restoreFocus = document.activeElement instanceof HTMLElement
    ? document.activeElement
    : state.detailBrowserSectionActionsNode;
  state.isDeleting = true;
  syncWorkRouteBusyState(state);
  renderEditorMessage(state);
  state.messageController.setActionTextWithState(
    state.statusNode,
    t(state, "detail_section_delete_status_running", "Preparing detail section delete preview..."),
    "info"
  );
  state.messageController.setActionTextWithState(state.resultNode, "");
  const request = {
    kind: "work_detail_section",
    section_id: sectionId,
    activity_context: buildDetailSectionActivityContext(sectionId)
  };
  try {
    const previewResponse = await previewCatalogueDelete(request);
    const preview = extractCatalogueActionPreview(previewResponse);
    const blocker = getCataloguePreviewBlocker(preview, {
      includeValidationErrors: true,
      fallback: t(state, "detail_section_delete_status_blocked", "Detail section delete is blocked.")
    });
    if (blocker) {
      state.messageController.setActionTextWithState(state.statusNode, blocker, "error");
      return;
    }
    const summary = formatCatalogueDeletePreview(preview, {
      text: (key, fallback, tokens) => t(state, key, fallback, tokens),
      defaultText: "Delete this detail section?"
    });
    state.isDeleting = false;
    syncWorkRouteBusyState(state);
    renderEditorMessage(state);
    const confirmed = await confirmCatalogueActionModal(state, {
      title: t(state, "detail_section_delete_confirm_title", "Confirm detail section delete"),
      message: summary,
      primaryLabel: t(state, "detail_section_delete_confirm_button", "Delete"),
      cancelLabel: t(state, "confirm_cancel_button", "Cancel"),
      defaultAction: "cancel",
      restoreFocus
    });
    if (!confirmed) {
      state.messageController.setActionTextWithState(
        state.statusNode,
        t(state, "detail_section_delete_status_cancelled", "Detail section delete cancelled.")
      );
      return;
    }
    state.isDeleting = true;
    syncWorkRouteBusyState(state);
    renderEditorMessage(state);
    state.messageController.setActionTextWithState(
      state.statusNode,
      t(state, "detail_section_delete_status_deleting", "Deleting detail section..."),
      "info"
    );
    const response = await applyCatalogueDelete(request);
    const remoteWarning = catalogueDeleteRemoteCleanupWarning(response);
    state.currentLookup = await loadWorkLookupRecord(state, state.currentWorkId);
    state.detailBrowserSelectedSectionId = "";
    state.detailBrowserSelectedDetailUid = "";
    updateSummary(state);
    if (remoteWarning) {
      const targetText = remoteWarning.targets.length
        ? remoteWarning.targets.join(", ")
        : sectionId;
      state.messageController.setActionTextWithState(
        state.statusNode,
        t(state, "detail_section_delete_status_r2_warning", "Detail section deleted, but R2 media cleanup needs attention."),
        "warn"
      );
      state.messageController.setActionTextWithState(
        state.resultNode,
        t(
          state,
          "detail_section_delete_result_r2_warning",
          "Remove the remaining R2 primary media manually for: {targets}.",
          { targets: targetText }
        ),
        "warn"
      );
    } else {
      state.messageController.setActionTextWithState(
        state.resultNode,
        t(state, "detail_section_delete_status_deleted", "Deleted detail section {section_id}.", {
          section_id: sectionId
        }),
        "success"
      );
      state.messageController.setActionTextWithState(state.statusNode, "");
    }
  } catch (error) {
    state.messageController.setActionTextWithState(
      state.statusNode,
      `${t(state, "detail_section_delete_status_failed", "Detail section delete failed.")} ${normalizeText(error && error.message)}`.trim(),
      "error"
    );
  } finally {
    state.isDeleting = false;
    syncWorkRouteBusyState(state);
    renderEditorMessage(state);
  }
}

function draftHasChanges(state) {
  return catalogueDraftHasChanges({
    mode: state.mode,
    fields: EDITABLE_FIELDS,
    draft: state.draft,
    baselineDraft: state.baselineDraft,
    touchedFields: state.bulkTouchedFields,
    canonicalizeScalar,
    newModeChanged: () => Boolean(
      normalizeWorkId(state.draft.work_id) ||
      EDITABLE_FIELDS.some((field) => normalizeText(state.draft[field.key]))
    ),
    extraComparisons: [
      {
        key: "downloads",
        changed: ({ draft, baselineDraft }) => !embeddedEntriesEqual(draft.downloads, baselineDraft.downloads, DOWNLOAD_FIELDS)
      },
      {
        key: "links",
        changed: ({ draft, baselineDraft }) => !embeddedEntriesEqual(draft.links, baselineDraft.links, LINK_FIELDS)
      }
    ]
  });
}

function validateDraft(state) {
  if (state.mode === "new") {
    const errors = new Map();
    const workId = normalizeWorkId(state.draft.work_id);
    if (!workId) {
      errors.set("work_id", t(state, "field_required_work_id", "Enter a work id."));
    } else if (state.workSearchById.has(workId) || state.sourceWorkRecordsById.has(workId)) {
      errors.set("work_id", t(state, "field_duplicate_work_id", "Work id already exists."));
    }

    REQUIRED_WORK_FIELDS.forEach((fieldKey) => {
      if (fieldKey === "series_ids") {
        if (!parseSeriesIds(state.draft.series_ids).length) {
          errors.set("series_ids", t(state, "field_required_series_ids", "Enter at least one series id."));
        }
        return;
      }
      if (!normalizeText(state.draft[fieldKey])) {
        const label = fieldKey.replace(/_/g, " ");
        errors.set(fieldKey, t(state, `field_required_${fieldKey}`, "Enter {field}.", { field: label }));
      }
    });

    const year = normalizeText(state.draft.year);
    if (year && !/^-?\d+$/.test(year)) {
      errors.set("year", t(state, "field_invalid_year", "Use a whole year or leave blank."));
    }

    WORK_DIMENSION_FIELD_KEYS.forEach((fieldKey) => {
      const value = normalizeText(state.draft[fieldKey]);
      if (value && !Number.isFinite(Number(value))) {
        errors.set(fieldKey, t(state, "field_invalid_number", "Use a number or leave blank."));
      }
    });

    const seriesText = normalizeText(state.draft.series_ids);
    if (seriesText) {
      const parts = seriesText.split(",").map((item) => normalizeText(item)).filter(Boolean);
      for (const part of parts) {
        if (!SERIES_ID_RE.test(part)) {
          errors.set("series_ids", t(state, "field_invalid_series_id", "Use comma-separated numeric series ids."));
          break;
        }
        const normalizedId = normalizeSeriesId(part);
        if (!state.seriesById.has(normalizedId)) {
          errors.set("series_ids", t(state, "field_unknown_series_id", "Unknown series id: {series_id}.", { series_id: normalizedId }));
          break;
        }
      }
    }
    return errors;
  }

  if (state.mode === "bulk") {
    const errors = new Map();
    if (state.bulkTouchedFields.has("status")) {
      const status = normalizeText(state.draft.status).toLowerCase();
      if (!STATUS_OPTIONS.has(status)) {
        errors.set("status", t(state, "field_invalid_status", "Use blank, draft, or published."));
      }
    }

    if (state.bulkTouchedFields.has("published_date")) {
      const publishedDate = normalizeText(state.draft.published_date);
      if (publishedDate && !DATE_RE.test(publishedDate)) {
        errors.set("published_date", t(state, "field_invalid_date", "Use YYYY-MM-DD or leave blank."));
      }
    }

    if (state.bulkTouchedFields.has("year")) {
      const year = normalizeText(state.draft.year);
      if (year && !/^-?\d+$/.test(year)) {
        errors.set("year", t(state, "field_invalid_year", "Use a whole year or leave blank."));
      }
    }

    WORK_DIMENSION_FIELD_KEYS.forEach((fieldKey) => {
      if (!state.bulkTouchedFields.has(fieldKey)) return;
      const value = normalizeText(state.draft[fieldKey]);
      if (value && !Number.isFinite(Number(value))) {
        errors.set(fieldKey, t(state, "field_invalid_number", "Use a number or leave blank."));
      }
    });

    if (state.bulkTouchedFields.has("series_ids")) {
      try {
        const operation = parseBulkSeriesOperation(state.draft.series_ids);
        const seriesIds = operation.mode === "replace"
          ? operation.series_ids
          : [...operation.add_series_ids, ...operation.remove_series_ids];
        for (const seriesId of seriesIds) {
          if (!state.seriesById.has(seriesId)) {
            errors.set("series_ids", t(state, "field_unknown_series_id", "Unknown series id: {series_id}.", { series_id: seriesId }));
            break;
          }
        }
      } catch (error) {
        errors.set(
          "series_ids",
          normalizeText(error && error.message) || t(state, "field_invalid_series_id", "Use comma-separated numeric series ids.")
        );
      }
    }

    return errors;
  }

  const errors = new Map();
  const status = normalizeText(state.draft.status).toLowerCase();
  if (!STATUS_OPTIONS.has(status)) {
    errors.set("status", t(state, "field_invalid_status", "Use blank, draft, or published."));
  }

  const publishedDate = normalizeText(state.draft.published_date);
  if (publishedDate && !DATE_RE.test(publishedDate)) {
    errors.set("published_date", t(state, "field_invalid_date", "Use YYYY-MM-DD or leave blank."));
  }

  const year = normalizeText(state.draft.year);
  if (year && !/^-?\d+$/.test(year)) {
    errors.set("year", t(state, "field_invalid_year", "Use a whole year or leave blank."));
  }

  WORK_DIMENSION_FIELD_KEYS.forEach((fieldKey) => {
    const value = normalizeText(state.draft[fieldKey]);
    if (value && !Number.isFinite(Number(value))) {
      errors.set(fieldKey, t(state, "field_invalid_number", "Use a number or leave blank."));
    }
  });

  const seriesText = normalizeText(state.draft.series_ids);
  if (seriesText) {
    const parts = seriesText.split(",").map((item) => normalizeText(item)).filter(Boolean);
    for (const part of parts) {
      if (!SERIES_ID_RE.test(part)) {
        errors.set("series_ids", t(state, "field_invalid_series_id", "Use comma-separated numeric series ids."));
        break;
      }
      const normalizedId = normalizeSeriesId(part);
      if (!state.seriesById.has(normalizedId)) {
        errors.set("series_ids", t(state, "field_unknown_series_id", "Unknown series id: {series_id}.", { series_id: normalizedId }));
        break;
      }
    }
  }

  validateWorkEmbeddedItems(state.draft, {
    text: (key, fallback, tokens) => t(state, key, fallback, tokens)
  }).forEach((message, key) => {
    errors.set(key, message);
  });

  return errors;
}

function clearActionMessages(state) {
  state.messageController.clearActionMessages();
}

function firstBulkMixedMessage(state) {
  if (state.mode !== "bulk") return "";
  for (const field of EDITABLE_FIELDS) {
    if (!state.bulkMixedFields.has(field.key) || state.bulkTouchedFields.has(field.key)) continue;
    return field.key === "series_ids"
      ? t(state, "bulk_field_mixed_series", "Mixed values across selection. Leave untouched to preserve, use plain ids to replace, or +id/-id to add or remove.")
      : t(state, "bulk_field_mixed", "Mixed values across selection. Leave untouched to preserve per-record values.");
  }
  return "";
}

function renderEditorMessage(state, snapshot = {}) {
  const hasRecord = Object.prototype.hasOwnProperty.call(snapshot, "hasRecord")
    ? snapshot.hasRecord
    : state.mode === "new"
      ? true
      : state.mode === "bulk"
        ? state.bulkWorkIds.length > 0
        : Boolean(state.currentRecord);
  const errors = snapshot.errors || state.validationErrors || new Map();
  const dirty = Object.prototype.hasOwnProperty.call(snapshot, "dirty") ? snapshot.dirty : hasRecord && draftHasChanges(state);
  state.messageController.render({
    busy: state.isSaving || state.isBuilding || state.isDeleting,
    validationMessage: firstCatalogueValidationMessage(errors),
    mixedMessage: firstBulkMixedMessage(state),
    dirtyMessage: catalogueDirtyWarningText({
      dirty,
      mode: state.mode,
      message: t(state, "dirty_warning", "Unsaved source changes.")
    })
  });
}

function updatePublishControls(state, { hasRecord, dirty, errors }) {
  const canPublish = state.mode === "single" && hasRecord && currentWorkIsDraft(state);
  const canUnpublish = state.mode === "single" && hasRecord && currentWorkIsPublished(state);
  const label = canUnpublish
    ? t(state, "unpublish_button", "Unpublish")
    : t(state, "publish_button", "Publish");
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

function updateEditorState(state) {
  const hasRecord = state.mode === "new" ? true : state.mode === "bulk" ? state.bulkWorkIds.length > 0 : Boolean(state.currentRecord);
  const errors = hasRecord ? validateDraft(state) : new Map();
  state.validationErrors = errors;
  updateFieldMessages(state, errors, workFormOptions(state));
  setModeFieldAvailability(state);
  updateSummary(state);
  if (!hasRecord) {
    setNodeTextWithState(state.buildImpactNode, "");
  } else if (state.mode === "bulk") {
    const previewTargets = state.rebuildPending && state.bulkBuildTargets.length
      ? state.bulkBuildTargets
      : bulkPublishedBuildTargets(state);
    setNodeTextWithState(
      state.buildImpactNode,
      t(state, "bulk_build_preview", "Public update preview: {count} published work scope(s) will be updated.", {
        count: String(previewTargets.length)
      })
    );
  }

  const dirty = hasRecord && draftHasChanges(state);
  if (state.mode === "bulk" && hasRecord) {
    state.messageController.setDefaultMessage(t(state, "bulk_status_loaded", "Loaded {count} work records.", { count: String(state.bulkWorkIds.length) }));
  } else if (state.mode === "single" && hasRecord) {
    state.messageController.setDefaultMessage(t(state, "save_status_loaded", "Loaded work {work_id}.", { work_id: state.currentWorkId }));
  }
  renderEditorMessage(state, { hasRecord, dirty, errors });

  state.saveButton.textContent = state.mode === "new"
    ? t(state, "create_button", "Create")
    : t(state, "save_button", "Save");
  state.saveButton.disabled = catalogueSaveDisabled({
    hasRecord,
    isSaving: state.isSaving || state.isBuilding || state.isDeleting,
    hasErrors: errors.size > 0,
    dirty: workSaveActionRequired(state, dirty),
    serverAvailable: state.serverAvailable
  });
  state.deleteButton.disabled = catalogueDeleteDisabled({
    hasRecord: Boolean(state.currentRecord),
    mode: state.mode,
    isSaving: state.isSaving,
    isBuilding: state.isBuilding,
    isDeleting: state.isDeleting,
    serverAvailable: state.serverAvailable
  });
  updatePublishControls(state, { hasRecord, dirty, errors });
  renderReadiness(state);
  syncWorkRouteBusyState(state);
}

function onFieldInput(state, fieldKey) {
  const node = state.fieldNodes.get(fieldKey);
  if (!node) return;
  clearActionMessages(state);
  if (state.mode === "new" && fieldKey === "status") {
    state.draft.status = "draft";
    setFieldNodeValue(node, "draft");
    updateEditorState(state);
    return;
  }
  if (state.mode === "new" && fieldKey === "published_date") {
    state.draft.published_date = "";
    setFieldNodeValue(node, "");
    updateEditorState(state);
    return;
  }
  state.draft[fieldKey] = getFieldNodeValue(node);
  if (state.mode === "bulk") {
    state.bulkTouchedFields.add(fieldKey);
  }
  updateEditorState(state);
}

function t(state, key, fallback, tokens = null) {
  return getStudioText(state.config, `catalogue_work_editor.${key}`, fallback, tokens);
}

function workFormOptions(state) {
  return {
    text: (key, fallback, tokens) => t(state, key, fallback, tokens),
    onFieldInput: (fieldKey) => onFieldInput(state, fieldKey),
    onStateChange: () => {
      clearActionMessages(state);
      updateEditorState(state);
    },
    draftHasChanges: () => draftHasChanges(state),
    loadProjectFolders: (query) => readProjectMediaFolders(query),
    loadProjectFiles: (request) => readProjectMediaFiles(request)
  };
}

function workRouteStateOptions(state, overrides = {}) {
  return createWorkRouteStateOptions(state, {
    text: (key, fallback, tokens) => t(state, key, fallback, tokens),
    setTextWithState: (node, text, tone) => state.messageController.setRouteTextWithState(node, text, tone),
    setOpenInputMode: () => setOpenInputMode(state),
    setPopupVisibility: (visible) => setWorkSelectionPopupVisibility(state, visible),
    applyDraftToInputs: () => applyDraftToInputs(state, workFormOptions(state)),
    applyReadonly: () => applyReadonly(state),
    clearReadonlyFields: () => clearReadonlyFields(state),
    updateEditorState: () => updateEditorState(state)
  }, overrides);
}

function workSelectionOptions(state) {
  return {
    text: (key, fallback, tokens) => t(state, key, fallback, tokens),
    loadWorkLookupRecord: (workId) => loadWorkLookupRecord(state, workId),
    setLoadedBulkWorks: (workIds, recordsById, recordHashes) => {
      setLoadedBulkWorks(state, workIds, recordsById, recordHashes, workRouteStateOptions(state));
    },
    setLoadedWorkRecord: (workId, record, options = {}) => {
      setLoadedWorkRecord(state, workId, record, workRouteStateOptions(state, options));
    },
    refreshBuildPreview: () => refreshBuildPreview(state, workActionOptions(state)),
    updateEditorState: () => updateEditorState(state),
    saveCurrentWork: () => saveWorkThenPublishMedia(state, workActionOptions(state)),
    setTextWithState: (node, text, tone) => state.messageController.setActionTextWithState(node, text, tone),
    setEmptySearchMode: (overrides = {}) => setEmptySearchMode(state, workRouteStateOptions(state, overrides)),
    setNewWorkMode: (overrides = {}) => setNewWorkMode(state, workRouteStateOptions(state, overrides))
  };
}

function workActionOptions(state) {
  return {
    text: (key, fallback, tokens) => t(state, key, fallback, tokens),
    setTextWithState: (node, text, tone) => state.messageController.setActionTextWithState(node, text, tone),
    validateDraft: () => validateDraft(state),
    updateFieldMessages: (errors) => updateFieldMessages(state, errors, workFormOptions(state)),
    draftHasChanges: () => draftHasChanges(state),
    updateEditorState: () => updateEditorState(state),
    loadWorkLookupRecord: (workId) => loadWorkLookupRecord(state, workId),
    workRouteStateOptions: (overrides = {}) => workRouteStateOptions(state, overrides),
    renderCurrentPreview: () => renderCurrentPreview(state),
    renderReadiness: () => renderReadiness(state),
    openWorkById: (workId) => openWorkById(state, workId, workSelectionOptions(state))
  };
}

function workSectionOptions(state) {
  return {
    text: (key, fallback, tokens) => t(state, key, fallback, tokens),
    draftHasChanges,
    isCurrentWorkPublished: currentWorkIsPublished,
    openDetailSectionPicker: () => openDetailSectionPicker(state),
    editDetailSection: (row, rows) => editDetailSection(state, row, rows),
    deleteDetailSection: (row) => deleteDetailSection(state, row),
    openEmbeddedEntryModal: (kind, index) => openEmbeddedEntryModal(state, kind, index),
    deleteEmbeddedEntry: (kind, index) => deleteEmbeddedEntry(state, kind, index),
    setTextWithState: (node, text, tone) => state.messageController.setActionTextWithState(node, text, tone)
  };
}

function renderCurrentPreview(state) {
  renderWorkCurrentPreview(state, workSectionOptions(state));
}

function renderReadiness(state) {
  renderWorkReadiness(state, workSectionOptions(state));
}

function updateDetailBrowser(state) {
  updateWorkDetailBrowser(state, workSectionOptions(state));
}

function updateSummary(state) {
  updateDetailBrowser(state);
  updateWorkSummary(state, workSectionOptions(state));
}

function applyWorkEditorText(state, elements) {
  setOpenInputMode(state);
  applyWorkFormText(state, workFormOptions(state));
  elements.detailBrowserSearchNode.placeholder = t(state, "detail_browser_search_placeholder", "find detail id");
  elements.openButton.textContent = t(state, "open_button", "Open");
  elements.newButton.textContent = t(state, "new_button", "New");
  elements.saveButton.textContent = t(state, "save_button", "Save");
  elements.publicationButton.textContent = t(state, "publish_button", "Publish");
  elements.deleteButton.textContent = t(state, "delete_button", "Delete");
}

async function configureWorkEditorRuntime(state, elements) {
  return configureCatalogueEditorRouteRuntime(state, {
    namespace: "catalogue_work_editor",
    applyText: (config) => {
      applyCatalogueEditorMediaAttrs(elements.root, config, [
        "worksPrimaryBase",
        "stagedWorksPrimaryBase",
        "thumbWorksBase",
        "thumbWorkDetailsBase",
        "primaryDisplayWidth",
        "primaryFullWidth",
        "primarySuffix",
        "thumbSizes",
        "thumbSuffix",
        "assetFormat"
      ]);
      state.mediaConfig = loadCatalogueMediaConfig(elements.root);
      applyWorkEditorText(state, elements);
    }
  });
}

async function loadInitialWorkEditorData(state) {
  await loadCatalogueEditorLookupMaps(state, [
    {
      configKey: "catalogue_lookup_work_search",
      target: state.workSearchById,
      normalizeKey: (record) => normalizeWorkId(record.work_id),
      afterItems: (items) => {
        state.nextSuggestedWorkId = suggestNextWorkId(items);
      }
    },
    {
      configKey: "catalogue_lookup_series_search",
      target: state.seriesById,
      normalizeKey: (record) => normalizeSeriesId(record.series_id)
    }
  ]);
}

function markWorkEditorLoaded(state, elements) {
  revealCatalogueEditorRoute(state, {
    loadingNode: elements.loadingNode,
    routeState: WORK_ROUTE_STATE
  });
}

async function init() {
  const elements = collectWorkEditorElements();
  if (!elements) return;

  initializeWorkRouteState(elements.root);
  const state = createWorkEditorState(elements);
  state.messageController = createCatalogueEditorMessageController({
    statusNode: state.statusNode,
    setTextWithState: setNodeTextWithState
  });
  renderWorkEditorFields(state, elements, workFormOptions(state));

  try {
    const serverAvailable = await configureWorkEditorRuntime(state, elements);
    if (!serverAvailable) {
      updateEditorState(state);
      markWorkEditorLoaded(state, elements);
      return;
    }

    await loadInitialWorkEditorData(state);
    bindWorkEditorEvents(state, {
      bindSelectionControls: () => bindWorkSelectionControls(state, workSelectionOptions(state)),
      renderEditorMessage: () => renderEditorMessage(state),
      updateWorkDetailBrowser: () => updateDetailBrowser(state),
      openEmbeddedEntryModal: (kind, index) => openEmbeddedEntryModal(state, kind, index),
      deleteEmbeddedEntry: (kind, index) => deleteEmbeddedEntry(state, kind, index),
      setNewWorkMode: () => setNewWorkMode(state, workRouteStateOptions(state)),
      refreshWorkMedia: () => refreshWorkMedia(state, workActionOptions(state)),
      saveCurrentWork: () => saveWorkThenPublishMedia(state, workActionOptions(state)),
      applyPublicationChange: () => applyPublicationChange(state, workActionOptions(state)),
      deleteCurrentWork: () => deleteCurrentWork(state, workActionOptions(state))
    });
    await applyInitialWorkRouteSelection(state, workSelectionOptions(state));
    markWorkEditorLoaded(state, elements);
  } catch (error) {
    console.warn("catalogue_work_editor: init failed", error);
    await showCatalogueEditorInitError(
      elements.loadingNode,
      "catalogue_work_editor",
      "Failed to load catalogue source data for the work editor."
    );
  }
}

init();
