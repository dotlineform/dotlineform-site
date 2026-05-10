import {
  getStudioText,
  loadStudioConfigWithText
} from "./studio-config.js";
import {
  loadStudioLookupJson,
  loadStudioLookupRecordJson
} from "./studio-data.js";
import {
  probeCatalogueHealth
} from "./studio-transport.js";
import { computeRecordHash } from "./catalogue-editor-records.js";
import {
  catalogueDeleteDisabled,
  catalogueDirtyWarningText,
  catalogueDraftChangedFieldNames,
  catalogueDraftHasChanges,
  catalogueSaveDisabled
} from "./catalogue-editor-dirty-state.js";
import {
  formatCatalogueBuildPreviewModalHtml
} from "./catalogue-editor-modal-formatters.js";
import {
  WORK_DOWNLOAD_FIELDS as DOWNLOAD_FIELDS,
  WORK_LINK_FIELDS as LINK_FIELDS,
  buildWorkEmbeddedDeleteConfirmation,
  buildWorkEmbeddedEntry,
  buildWorkEmbeddedModalDescriptor,
  validateWorkEmbeddedEntryValues,
  validateWorkEmbeddedItems
} from "./catalogue-editor-embedded-items.js";
import {
  buildWorkRecordSummary as buildRecordSummary,
  renderWorkCurrentPreview,
  renderWorkReadiness,
  updateWorkDetailSections,
  updateWorkSummary
} from "./catalogue-work-sections.js";
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
  markWorkRouteReady,
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
  currentWorkIsDraft,
  currentWorkIsPublished,
  deleteCurrentWork,
  importWorkProse,
  parseBulkSeriesOperation,
  previewCurrentBuildImpact,
  refreshBuildPreview,
  refreshWorkMedia,
  saveCurrentWork
} from "./catalogue-work-actions.js";
import {
  buildSaveModeText
} from "./tag-studio-save.js";
import {
  loadCatalogueMediaConfig
} from "./catalogue-media-preview.js";
import {
  createStudioModalHost,
  openConfirmModal,
  renderStudioModalFrame
} from "./studio-modal.js";
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

const SEARCH_LIMIT = 20;
const REQUIRED_WORK_FIELDS = ["title", "year", "year_display", "series_ids"];

function escapeHtml(value) {
  return normalizeText(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function changedWorkFieldNames(state) {
  if (state.mode !== "single" || !state.baselineDraft) return [];
  return catalogueDraftChangedFieldNames({
    fields: EDITABLE_FIELDS,
    draft: state.draft,
    baselineDraft: state.baselineDraft,
    canonicalizeScalar,
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

function buildSearchToken(value) {
  const text = normalizeText(value);
  if (!text) return "";
  const digits = text.replace(/\D/g, "");
  return digits || text.toLowerCase();
}

function parseWorkSelection(rawValue) {
  const text = normalizeText(rawValue);
  if (!text) return [];
  const tokens = text.split(",").map((item) => normalizeText(item)).filter(Boolean);
  const workIds = [];
  const seen = new Set();
  tokens.forEach((token) => {
    const rangeMatch = token.match(/^(\d{1,5})\s*-\s*(\d{1,5})$/);
    if (rangeMatch) {
      const start = Number(normalizeWorkId(rangeMatch[1]));
      const end = Number(normalizeWorkId(rangeMatch[2]));
      if (!Number.isFinite(start) || !Number.isFinite(end) || start > end) {
        throw new Error(`Invalid work id range: ${token}`);
      }
      for (let value = start; value <= end; value += 1) {
        const workId = String(value).padStart(5, "0");
        if (seen.has(workId)) continue;
        seen.add(workId);
        workIds.push(workId);
      }
      return;
    }
    const workId = normalizeWorkId(token);
    if (!workId) {
      throw new Error(`Invalid work id: ${token}`);
    }
    if (seen.has(workId)) return;
    seen.add(workId);
    workIds.push(workId);
  });
  return workIds;
}

function isWorkBulkQuery(rawValue) {
  try {
    return parseWorkSelection(rawValue).length > 1;
  } catch (_error) {
    return false;
  }
}

function setTextWithState(node, text, state = "") {
  if (!node) return;
  node.textContent = text || "";
  if (state) {
    node.dataset.state = state;
  } else {
    delete node.dataset.state;
  }
}

function setPopupVisibility(state, visible) {
  state.popupNode.hidden = !visible;
}

function setOpenInputMode(state) {
  state.searchNode.placeholder = t(state, "search_placeholder", "find work id(s): 00001, 00003-00005");
  state.searchNode.setAttribute("aria-label", t(state, "search_label", "Find work by id"));
}

function getSearchMatches(state, rawQuery) {
  const query = buildSearchToken(rawQuery);
  if (!query) return [];
  const matches = [];
  for (const [workId, record] of state.workSearchById.entries()) {
    if (workId.includes(query)) {
      matches.push({ workId, record });
      continue;
    }
    if (normalizeWorkId(query) && workId === normalizeWorkId(query)) {
      matches.push({ workId, record });
    }
  }
  matches.sort((a, b) => a.workId.localeCompare(b.workId, undefined, { numeric: true, sensitivity: "base" }));
  return matches.slice(0, SEARCH_LIMIT);
}

function renderSearchMatches(state, matches, message = "") {
  if (!matches.length && !message) {
    state.popupListNode.innerHTML = "";
    setPopupVisibility(state, false);
    return;
  }

  if (!matches.length) {
    state.popupListNode.innerHTML = `<p class="tagStudioForm__meta">${escapeHtml(message)}</p>`;
    setPopupVisibility(state, true);
    return;
  }

  const rows = matches.map(({ workId, record }) => `
    <button type="button" class="tagStudioSuggest__workButton" data-work-id="${escapeHtml(workId)}">
      <span class="tagStudioSuggest__workId">${escapeHtml(workId)}</span>
      <span class="tagStudioSuggest__workTitle">${escapeHtml(buildRecordSummary(record))}</span>
    </button>
  `);
  state.popupListNode.innerHTML = `<div class="tagStudioSuggest__workRows">${rows.join("")}</div>`;
  setPopupVisibility(state, true);
}

async function loadWorkLookupRecord(state, workId) {
  return loadStudioLookupRecordJson(state.config, "catalogue_lookup_work_base", workId, {
    cache: "no-store",
    catalogueServerAvailable: state.serverAvailable
  });
}

function getSourceWorkRecord(state, workId, fallbackRecord = null) {
  const sourceRecord = state.sourceWorkRecordsById.get(workId);
  if (sourceRecord && typeof sourceRecord === "object") return sourceRecord;
  if (fallbackRecord && typeof fallbackRecord === "object") return fallbackRecord;
  return null;
}

function closeEntryModal(state) {
  if (state.modalHost) state.modalHost.innerHTML = "";
  document.removeEventListener("keydown", state.activeModalKeydown);
  state.activeModalKeydown = null;
}

function modalFieldHtml({ fieldId, label, value, type = "text" }) {
  return `
    <label class="tagStudioForm__field" for="${escapeHtml(fieldId)}">
      <span class="tagStudioForm__label">${escapeHtml(label)}</span>
      <input class="tagStudio__input" id="${escapeHtml(fieldId)}" type="${escapeHtml(type)}" value="${escapeHtml(value)}">
    </label>
  `;
}

function openEmbeddedEntryModal(state, kind, index = null) {
  if (!state.currentRecord || state.mode === "bulk") return;
  const descriptor = buildWorkEmbeddedModalDescriptor(kind, index, {
    draft: state.draft,
    text: (key, fallback, tokens) => t(state, key, fallback, tokens)
  });
  if (!descriptor) return;
  const firstField = descriptor.fields[0];
  const secondField = descriptor.fields[1];

  closeEntryModal(state);
  state.modalHost.innerHTML = renderStudioModalFrame({
    hidden: false,
    title: descriptor.title,
    titleId: descriptor.titleId,
    modalRole: descriptor.modalRole,
    backdropRole: "entry-modal-cancel",
    bodyHtml: `
      <div class="tagStudioForm__fields">
        ${modalFieldHtml(firstField)}
        ${modalFieldHtml(secondField)}
      </div>
      <p class="tagStudioForm__status" id="${escapeHtml(descriptor.statusId)}"></p>
    `,
    actions: [
      { role: "entry-modal-save", label: t(state, "entry_modal_save_button", "Save") },
      { role: "entry-modal-cancel", label: t(state, "entry_modal_cancel_button", "Cancel") }
    ]
  });

  const firstNode = state.modalHost.querySelector(`#${firstField.fieldId}`);
  const secondNode = state.modalHost.querySelector(`#${secondField.fieldId}`);
  const statusNode = state.modalHost.querySelector(`#${descriptor.statusId}`);
  const saveNode = state.modalHost.querySelector('[data-role="entry-modal-save"]');
  const cancelNodes = state.modalHost.querySelectorAll('[data-role="entry-modal-cancel"]');

  const setModalStatus = (message) => {
    if (!statusNode) return;
    statusNode.textContent = message || "";
    if (message) {
      statusNode.dataset.state = "error";
    } else {
      delete statusNode.dataset.state;
    }
  };

  const submit = () => {
    const firstValue = normalizeText(firstNode && firstNode.value);
    const secondValue = normalizeText(secondNode && secondNode.value);
    const validationMessage = validateWorkEmbeddedEntryValues(kind, firstValue, secondValue, {
      text: (key, fallback, tokens) => t(state, key, fallback, tokens)
    });
    if (validationMessage) {
      setModalStatus(validationMessage);
      return;
    }
    const nextEntry = buildWorkEmbeddedEntry(kind, firstValue, secondValue);
    if (descriptor.editing) {
      descriptor.entries[index] = nextEntry;
    } else {
      descriptor.entries.push(nextEntry);
    }
    state.draft[descriptor.entriesKey] = descriptor.entries;
    closeEntryModal(state);
    updateEditorState(state);
  };

  state.activeModalKeydown = (event) => {
    if (event.key === "Escape") {
      event.preventDefault();
      closeEntryModal(state);
    }
    if (event.key === "Enter" && event.target && event.target.tagName === "INPUT") {
      event.preventDefault();
      submit();
    }
  };
  document.addEventListener("keydown", state.activeModalKeydown);
  cancelNodes.forEach((button) => button.addEventListener("click", () => closeEntryModal(state)));
  if (saveNode) saveNode.addEventListener("click", submit);
  if (firstNode) firstNode.focus();
}

async function deleteEmbeddedEntry(state, kind, index) {
  if (!state.currentRecord || state.mode === "bulk") return;
  const confirmation = buildWorkEmbeddedDeleteConfirmation(kind, state.draft, index, {
    text: (key, fallback, tokens) => t(state, key, fallback, tokens)
  });
  if (!confirmation) return;
  const result = await openConfirmModal({
    root: state.root,
    title: confirmation.title,
    body: confirmation.body,
    primaryLabel: t(state, "entry_modal_delete_button", "Delete"),
    cancelLabel: t(state, "entry_modal_cancel_button", "Cancel")
  });
  if (!result || !result.confirmed) return;
  confirmation.entries.splice(index, 1);
  state.draft[confirmation.entriesKey] = confirmation.entries;
  updateEditorState(state);
}

function closeBuildPreviewModal(state) {
  closeEntryModal(state);
}

function openBuildPreviewModal(state, response, changedFields) {
  closeEntryModal(state);
  state.modalHost.innerHTML = renderStudioModalFrame({
    hidden: false,
    title: t(state, "build_preview_modal_title", "Public update preview"),
    titleId: "catalogueWorkBuildPreviewModalTitle",
    modalRole: "build-preview-modal",
    backdropRole: "build-preview-modal-close",
    bodyHtml: formatCatalogueBuildPreviewModalHtml(response, changedFields, {
      text: (key, fallback, tokens) => t(state, key, fallback, tokens),
      defaultTemplate: "Public update preview: work {work_ids}; series {series_ids}; catalogue search {search_rebuild}.",
      reasonsClass: "catalogueWorkBuildPreview__reasons"
    }),
    actions: [
      { role: "build-preview-modal-close", label: t(state, "build_preview_modal_close", "Close") }
    ]
  });

  const closeNodes = state.modalHost.querySelectorAll('[data-role="build-preview-modal-close"]');
  state.activeModalKeydown = (event) => {
    if (event.key === "Escape") {
      event.preventDefault();
      closeBuildPreviewModal(state);
    }
  };
  document.addEventListener("keydown", state.activeModalKeydown);
  closeNodes.forEach((button) => button.addEventListener("click", () => closeBuildPreviewModal(state)));
  const closeButton = state.modalHost.querySelector('[data-role="build-preview-modal-close"]');
  if (closeButton) closeButton.focus();
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
    setTextWithState(state.buildImpactNode, "");
  } else if (state.mode === "bulk") {
    const previewTargets = state.rebuildPending && state.bulkBuildTargets.length
      ? state.bulkBuildTargets
      : bulkPublishedBuildTargets(state);
    setTextWithState(
      state.buildImpactNode,
      t(state, "bulk_build_preview", "Public update preview: {count} published work scope(s) will be updated.", {
        count: String(previewTargets.length)
      })
    );
  }

  const dirty = hasRecord && draftHasChanges(state);
  setTextWithState(state.warningNode, catalogueDirtyWarningText({
    dirty,
    mode: state.mode,
    message: t(state, "dirty_warning", "Unsaved source changes.")
  }));
  if (state.mode === "new" && !state.resultNode.textContent) {
    setTextWithState(
      state.statusNode,
      state.serverAvailable ? "" : t(state, "save_mode_unavailable_hint", "Local catalogue server unavailable. Save is disabled."),
      state.serverAvailable ? "" : "warn"
    );
  } else if (!dirty && !errors.size && !state.resultNode.textContent && hasRecord) {
    setTextWithState(
      state.statusNode,
      state.mode === "bulk"
        ? t(state, "bulk_status_loaded", "Loaded {count} work records.", { count: String(state.bulkWorkIds.length) })
        : t(state, "save_status_loaded", "Loaded work {work_id}.", { work_id: state.currentWorkId })
    );
  }

  state.saveButton.textContent = state.mode === "new"
    ? t(state, "create_button", "Create")
    : t(state, "save_button", "Save");
  state.saveButton.disabled = catalogueSaveDisabled({
    hasRecord,
    isSaving: state.isSaving,
    hasErrors: errors.size > 0,
    dirty,
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
    onStateChange: () => updateEditorState(state)
  };
}

function workRouteStateOptions(state, overrides = {}) {
  return {
    text: (key, fallback, tokens) => t(state, key, fallback, tokens),
    setTextWithState,
    setOpenInputMode: () => setOpenInputMode(state),
    setPopupVisibility: (visible) => setPopupVisibility(state, visible),
    applyDraftToInputs: () => applyDraftToInputs(state, workFormOptions(state)),
    applyReadonly: () => applyReadonly(state),
    clearReadonlyFields: () => clearReadonlyFields(state),
    updateEditorState: () => updateEditorState(state),
    ...overrides
  };
}

function workActionOptions(state) {
  return {
    text: (key, fallback, tokens) => t(state, key, fallback, tokens),
    setTextWithState,
    validateDraft: () => validateDraft(state),
    updateFieldMessages: (errors) => updateFieldMessages(state, errors, workFormOptions(state)),
    draftHasChanges: () => draftHasChanges(state),
    changedWorkFieldNames: () => changedWorkFieldNames(state),
    updateEditorState: () => updateEditorState(state),
    loadWorkLookupRecord: (workId) => loadWorkLookupRecord(state, workId),
    workRouteStateOptions: (overrides = {}) => workRouteStateOptions(state, overrides),
    renderCurrentPreview: () => renderCurrentPreview(state),
    renderReadiness: () => renderReadiness(state),
    openBuildPreviewModal: (response, changedFields) => openBuildPreviewModal(state, response, changedFields),
    openWorkById: (workId) => openWorkById(state, workId)
  };
}

function workSectionOptions(state) {
  return {
    text: (key, fallback, tokens) => t(state, key, fallback, tokens),
    changedWorkFieldNames,
    draftHasChanges,
    isCurrentWorkPublished: currentWorkIsPublished,
    onPreviewBuildImpact: () => previewCurrentBuildImpact(state, workActionOptions(state)),
    setTextWithState
  };
}

function renderCurrentPreview(state) {
  renderWorkCurrentPreview(state, workSectionOptions(state));
}

function renderReadiness(state) {
  renderWorkReadiness(state, workSectionOptions(state));
}

function updateDetailSections(state) {
  updateWorkDetailSections(state, workSectionOptions(state));
}

function updateSummary(state) {
  updateWorkSummary(state, workSectionOptions(state));
}

async function openWorkSelection(state, requestedValue) {
  let workIds;
  try {
    workIds = parseWorkSelection(requestedValue);
  } catch (error) {
    renderSearchMatches(state, [], normalizeText(error && error.message) || t(state, "search_empty", "Enter a work id."));
    return;
  }

  if (!workIds.length) {
    renderSearchMatches(state, [], t(state, "search_empty", "Enter a work id."));
    return;
  }
  if (workIds.length === 1) {
    await openWorkById(state, workIds[0]);
    return;
  }

  const unknown = workIds.find((workId) => !state.workSearchById.has(workId));
  if (unknown) {
    renderSearchMatches(state, [], t(state, "unknown_work_error", "Unknown work id: {work_id}.", { work_id: unknown }));
    return;
  }

  state.searchNode.value = workIds.join(", ");
  state.detailSearchNode.value = "";
  setPopupVisibility(state, false);
  state.pendingBuildExtraSeriesIds = [];
  state.rebuildPending = false;
  const lookups = await Promise.all(workIds.map((workId) => loadWorkLookupRecord(state, workId)));
  const recordsById = new Map();
  const recordHashes = new Map();
  for (let index = 0; index < workIds.length; index += 1) {
    const workId = workIds[index];
    const lookup = lookups[index];
    const fallbackRecord = lookup && lookup.work && typeof lookup.work === "object" ? lookup.work : null;
    const record = getSourceWorkRecord(state, workId, fallbackRecord);
    if (!record) {
      throw new Error(`work source missing record for ${workId}`);
    }
    recordsById.set(workId, record);
    recordHashes.set(workId, await computeRecordHash(record));
  }
  setLoadedBulkWorks(state, workIds, recordsById, recordHashes, workRouteStateOptions(state));
  await refreshBuildPreview(state, workActionOptions(state));
}

async function openWorkById(state, requestedWorkId) {
  const workId = normalizeWorkId(requestedWorkId);
  if (!workId) {
    renderSearchMatches(state, [], t(state, "search_empty", "Enter a work id."));
    return;
  }

  const searchRecord = state.workSearchById.get(workId);
  if (!searchRecord) {
    const matches = getSearchMatches(state, requestedWorkId);
    if (matches.length) {
      renderSearchMatches(state, matches);
    } else {
      renderSearchMatches(state, [], t(state, "unknown_work_error", "Unknown work id: {work_id}.", { work_id }));
    }
    return;
  }

  state.searchNode.value = workId;
  state.detailSearchNode.value = "";
  setPopupVisibility(state, false);
  state.pendingBuildExtraSeriesIds = [];
  state.rebuildPending = false;
  const lookup = await loadWorkLookupRecord(state, workId);
  const fallbackRecord = lookup && lookup.work && typeof lookup.work === "object" ? lookup.work : null;
  const record = getSourceWorkRecord(state, workId, fallbackRecord);
  if (!record) {
    throw new Error(`work source missing record for ${workId}`);
  }
  setLoadedWorkRecord(state, workId, record, workRouteStateOptions(state, {
    recordHash: await computeRecordHash(record),
    lookup
  }));
  await refreshBuildPreview(state, workActionOptions(state));
}

function collectWorkEditorElements() {
  const elements = {
    root: document.getElementById("catalogueWorkRoot"),
    loadingNode: document.getElementById("catalogueWorkLoading"),
    emptyNode: document.getElementById("catalogueWorkEmpty"),
    fieldsNode: document.getElementById("catalogueWorkFields"),
    readonlyNode: document.getElementById("catalogueWorkReadonly"),
    previewNode: document.getElementById("catalogueWorkPreview"),
    summaryNode: document.getElementById("catalogueWorkSummary"),
    readinessNode: document.getElementById("catalogueWorkReadiness"),
    runtimeStateNode: document.getElementById("catalogueWorkRuntimeState"),
    buildImpactNode: document.getElementById("catalogueWorkBuildImpact"),
    detailsHeadingNode: document.getElementById("catalogueWorkDetailsHeading"),
    newDetailLinkNode: document.getElementById("catalogueWorkNewDetailLink"),
    detailSearchRowNode: document.getElementById("catalogueWorkDetailsSearchRow"),
    detailSearchNode: document.getElementById("catalogueWorkDetailSearch"),
    detailsMetaNode: document.getElementById("catalogueWorkDetailsMeta"),
    detailsResultsNode: document.getElementById("catalogueWorkDetailsResults"),
    filesHeadingNode: document.getElementById("catalogueWorkFilesHeading"),
    newFileLinkNode: document.getElementById("catalogueWorkNewFileLink"),
    filesMetaNode: document.getElementById("catalogueWorkFilesMeta"),
    filesResultsNode: document.getElementById("catalogueWorkFilesResults"),
    linksHeadingNode: document.getElementById("catalogueWorkLinksHeading"),
    newLinkLinkNode: document.getElementById("catalogueWorkNewLinkLink"),
    linksMetaNode: document.getElementById("catalogueWorkLinksMeta"),
    linksResultsNode: document.getElementById("catalogueWorkLinksResults"),
    searchNode: document.getElementById("catalogueWorkSearch"),
    popupNode: document.getElementById("catalogueWorkPopup"),
    popupListNode: document.getElementById("catalogueWorkPopupList"),
    openButton: document.getElementById("catalogueWorkOpen"),
    newButton: document.getElementById("catalogueWorkNew"),
    saveButton: document.getElementById("catalogueWorkSave"),
    publicationButton: document.getElementById("catalogueWorkPublication"),
    deleteButton: document.getElementById("catalogueWorkDelete"),
    saveModeNode: document.getElementById("catalogueWorkSaveMode"),
    contextNode: document.getElementById("catalogueWorkContext"),
    statusNode: document.getElementById("catalogueWorkStatus"),
    warningNode: document.getElementById("catalogueWorkWarning"),
    resultNode: document.getElementById("catalogueWorkResult"),
    metaNode: document.getElementById("catalogueWorkMeta")
  };
  return Object.values(elements).every(Boolean) ? elements : null;
}

function createWorkEditorState(elements) {
  const {
    root,
    searchNode,
    popupNode,
    popupListNode,
    openButton,
    newButton,
    saveButton,
    publicationButton,
    deleteButton,
    saveModeNode,
    contextNode,
    statusNode,
    warningNode,
    resultNode,
    previewNode,
    summaryNode,
    readinessNode,
    runtimeStateNode,
    buildImpactNode,
    detailSearchRowNode,
    detailSearchNode,
    detailsMetaNode,
    detailsResultsNode,
    newDetailLinkNode,
    filesMetaNode,
    filesResultsNode,
    newFileLinkNode,
    linksMetaNode,
    linksResultsNode,
    newLinkLinkNode,
    metaNode
  } = elements;

  return {
    root,
    config: null,
    mode: "single",
    workSearchById: new Map(),
    seriesById: new Map(),
    sourceWorkRecordsById: new Map(),
    currentLookup: null,
    currentWorkId: "",
    currentRecord: null,
    currentRecordHash: "",
    nextSuggestedWorkId: "",
    bulkWorkIds: [],
    bulkRecords: new Map(),
    bulkRecordHashes: new Map(),
    bulkMixedFields: new Set(),
    bulkTouchedFields: new Set(),
    bulkBuildTargets: [],
    baselineDraft: null,
    draft: {},
    validationErrors: new Map(),
    mediaConfig: loadCatalogueMediaConfig(root),
    rebuildPending: false,
    pendingBuildExtraSeriesIds: [],
    buildPreview: null,
    isSaving: false,
    isBuilding: false,
    isPreviewingBuild: false,
    isDeleting: false,
    serverAvailable: false,
    modalHost: createStudioModalHost({ root }),
    activeModalKeydown: null,
    fieldNodes: new Map(),
    fieldStatusNodes: new Map(),
    readonlyNodes: new Map(),
    searchNode,
    popupNode,
    popupListNode,
    openButton,
    newButton,
    saveButton,
    publicationButton,
    deleteButton,
    saveModeNode,
    contextNode,
    statusNode,
    warningNode,
    resultNode,
    previewNode,
    summaryNode,
    readinessNode,
    runtimeStateNode,
    buildImpactNode,
    detailSearchRowNode,
    detailSearchNode,
    detailsMetaNode,
    detailsResultsNode,
    detailsPanelNode: detailsResultsNode.closest("section"),
    newDetailLinkNode,
    filesMetaNode,
    filesResultsNode,
    filesPanelNode: filesResultsNode.closest("section"),
    newFileLinkNode,
    linksMetaNode,
    linksResultsNode,
    linksPanelNode: linksResultsNode.closest("section"),
    newLinkLinkNode,
    metaNode
  };
}

function applyWorkEditorText(state, elements) {
  setOpenInputMode(state);
  applyWorkFormText(state, workFormOptions(state));
  elements.detailsHeadingNode.textContent = t(state, "details_heading", "work details");
  elements.newDetailLinkNode.textContent = t(state, "details_new_link", "new work detail →");
  elements.detailSearchNode.placeholder = t(state, "details_search_placeholder", "find detail by id");
  elements.filesHeadingNode.textContent = t(state, "files_heading", "downloads");
  elements.newFileLinkNode.textContent = t(state, "files_add_button", "Add file");
  elements.linksHeadingNode.textContent = t(state, "links_heading", "links");
  elements.newLinkLinkNode.textContent = t(state, "links_add_button", "Add link");
  elements.openButton.textContent = t(state, "open_button", "Open");
  elements.newButton.textContent = t(state, "new_button", "New");
  elements.saveButton.textContent = t(state, "save_button", "Save");
  elements.publicationButton.textContent = t(state, "publish_button", "Publish");
  elements.deleteButton.textContent = t(state, "delete_button", "Delete");
}

async function configureWorkEditorRuntime(state, elements) {
  const config = await loadStudioConfigWithText("catalogue_work_editor");
  state.config = config;
  applyWorkEditorText(state, elements);
  const serverAvailable = await probeCatalogueHealth();
  state.serverAvailable = Boolean(serverAvailable);
  state.saveModeNode.textContent = buildSaveModeText(config, state.serverAvailable ? "post" : "offline", (cfg, key, fallback, tokens) => getStudioText(cfg, `catalogue_work_editor.${key}`, fallback, tokens));
  return state.serverAvailable;
}

async function loadInitialWorkEditorData(state) {
  const serverReadOptions = { cache: "no-store", catalogueServerAvailable: state.serverAvailable };
  const [worksPayload, seriesPayload] = await Promise.all([
    loadStudioLookupJson(state.config, "catalogue_lookup_work_search", serverReadOptions),
    loadStudioLookupJson(state.config, "catalogue_lookup_series_search", serverReadOptions)
  ]);

  const workItems = Array.isArray(worksPayload && worksPayload.items) ? worksPayload.items : [];
  state.nextSuggestedWorkId = suggestNextWorkId(workItems);
  workItems.forEach((record) => {
    if (!record || typeof record !== "object") return;
    const workId = normalizeWorkId(record.work_id);
    if (!workId) return;
    state.workSearchById.set(workId, record);
  });
  const seriesItems = Array.isArray(seriesPayload && seriesPayload.items) ? seriesPayload.items : [];
  seriesItems.forEach((record) => {
    if (!record || typeof record !== "object") return;
    const seriesId = normalizeSeriesId(record.series_id);
    if (!seriesId) return;
    state.seriesById.set(seriesId, record);
  });
}

function bindWorkEditorEvents(state) {
  state.searchNode.addEventListener("input", () => {
    const query = state.searchNode.value;
    if (state.mode === "new") {
      state.draft.work_id = normalizeWorkId(query);
      setPopupVisibility(state, false);
      updateEditorState(state);
      return;
    }
    if (!normalizeText(query)) {
      renderSearchMatches(state, [], "");
      return;
    }
    if (isWorkBulkQuery(query)) {
      renderSearchMatches(state, [], "");
      return;
    }
    const matches = getSearchMatches(state, query);
    if (!matches.length) {
      renderSearchMatches(state, [], t(state, "search_no_match", "No matching work ids."));
      return;
    }
    renderSearchMatches(state, matches);
  });

  state.searchNode.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") return;
    event.preventDefault();
    if (state.mode === "new") {
      saveCurrentWork(state, workActionOptions(state)).catch((error) => {
        console.warn("catalogue_work_editor: unexpected create failure", error);
      });
      return;
    }
    openWorkSelection(state, state.searchNode.value).catch((error) => {
      console.warn("catalogue_work_editor: failed to open requested work selection", error);
    });
  });

  state.detailSearchNode.addEventListener("input", () => {
    updateDetailSections(state);
  });

  state.newFileLinkNode.addEventListener("click", () => openEmbeddedEntryModal(state, "download"));
  state.newLinkLinkNode.addEventListener("click", () => openEmbeddedEntryModal(state, "link"));

  state.filesResultsNode.addEventListener("click", (event) => {
    const editButton = event.target && event.target.closest ? event.target.closest("[data-download-edit]") : null;
    if (editButton) {
      openEmbeddedEntryModal(state, "download", Number(editButton.getAttribute("data-download-edit")));
      return;
    }
    const deleteButtonNode = event.target && event.target.closest ? event.target.closest("[data-download-delete]") : null;
    if (deleteButtonNode) {
      deleteEmbeddedEntry(state, "download", Number(deleteButtonNode.getAttribute("data-download-delete"))).catch((error) => {
        console.warn("catalogue_work_editor: failed to delete download", error);
      });
    }
  });

  state.linksResultsNode.addEventListener("click", (event) => {
    const editButton = event.target && event.target.closest ? event.target.closest("[data-link-edit]") : null;
    if (editButton) {
      openEmbeddedEntryModal(state, "link", Number(editButton.getAttribute("data-link-edit")));
      return;
    }
    const deleteButtonNode = event.target && event.target.closest ? event.target.closest("[data-link-delete]") : null;
    if (deleteButtonNode) {
      deleteEmbeddedEntry(state, "link", Number(deleteButtonNode.getAttribute("data-link-delete"))).catch((error) => {
        console.warn("catalogue_work_editor: failed to delete link", error);
      });
    }
  });

  state.popupListNode.addEventListener("click", (event) => {
    const button = event.target && event.target.closest ? event.target.closest("[data-work-id]") : null;
    if (!button) return;
    openWorkById(state, button.getAttribute("data-work-id")).catch((error) => {
      console.warn("catalogue_work_editor: failed to open selected work", error);
    });
  });

  state.openButton.addEventListener("click", () => {
    if (state.mode === "new") {
      setEmptySearchMode(state, workRouteStateOptions(state, { keepSearchValue: true }));
    }
    openWorkSelection(state, state.searchNode.value).catch((error) => {
      console.warn("catalogue_work_editor: failed to open requested work selection", error);
    });
  });
  state.newButton.addEventListener("click", () => {
    setNewWorkMode(state, workRouteStateOptions(state));
  });
  state.readinessNode.addEventListener("click", (event) => {
    const mediaButton = event.target && event.target.closest ? event.target.closest("[data-media-refresh]") : null;
    if (mediaButton) {
      refreshWorkMedia(state, workActionOptions(state)).catch((error) => {
        console.warn("catalogue_work_editor: unexpected media refresh failure", error);
      });
      return;
    }
    const proseButton = event.target && event.target.closest ? event.target.closest("[data-prose-import]") : null;
    if (!proseButton) return;
    importWorkProse(state, workActionOptions(state)).catch((error) => {
      console.warn("catalogue_work_editor: unexpected prose import failure", error);
    });
  });
  state.saveButton.addEventListener("click", () => saveCurrentWork(state, workActionOptions(state)).catch((error) => {
    console.warn("catalogue_work_editor: unexpected save failure", error);
  }));
  state.publicationButton.addEventListener("click", () => applyPublicationChange(state, workActionOptions(state)).catch((error) => {
    console.warn("catalogue_work_editor: unexpected publication failure", error);
  }));
  state.deleteButton.addEventListener("click", () => deleteCurrentWork(state, workActionOptions(state)).catch((error) => {
    console.warn("catalogue_work_editor: unexpected delete failure", error);
  }));

  document.addEventListener("click", (event) => {
    if (event.target === state.searchNode || state.popupNode.contains(event.target)) return;
    setPopupVisibility(state, false);
  });
}

async function applyInitialRouteSelection(state) {
  const params = new URLSearchParams(window.location.search);
  const requestedMode = normalizeText(params.get("mode")).toLowerCase();
  const requestedWorkValue = normalizeText(params.get("work"));
  if (requestedWorkValue) {
    try {
      await openWorkSelection(state, requestedWorkValue);
    } catch (error) {
      console.warn("catalogue_work_editor: failed to open requested work selection", error);
      setEmptySearchMode(state, workRouteStateOptions(state, { keepSearchValue: true }));
      setTextWithState(
        state.statusNode,
        `${t(state, "load_requested_work_failed", "Failed to load the requested work.")} ${normalizeText(error && error.message)}`.trim(),
        "error"
      );
    }
  } else if (requestedMode === "new") {
    setNewWorkMode(state, workRouteStateOptions(state));
  } else {
    setEmptySearchMode(state, workRouteStateOptions(state));
  }
}

function markWorkEditorLoaded(state, elements) {
  state.root.hidden = false;
  elements.loadingNode.hidden = true;
  markWorkRouteReady(state, true);
}

async function showWorkEditorInitError(loadingNode) {
  try {
    const config = await loadStudioConfigWithText("catalogue_work_editor");
    loadingNode.textContent = getStudioText(config, "catalogue_work_editor.load_failed_error", "Failed to load catalogue source data for the work editor.");
  } catch (_configError) {
    loadingNode.textContent = "Failed to load catalogue source data for the work editor.";
  }
}

async function init() {
  const elements = collectWorkEditorElements();
  if (!elements) return;

  initializeWorkRouteState(elements.root);
  const state = createWorkEditorState(elements);
  renderWorkEditorFields(state, elements, workFormOptions(state));

  try {
    const serverAvailable = await configureWorkEditorRuntime(state, elements);
    if (!serverAvailable) {
      setTextWithState(state.statusNode, t(state, "save_mode_unavailable_hint", "Local catalogue server unavailable. Save is disabled."), "warn");
      updateEditorState(state);
      markWorkEditorLoaded(state, elements);
      return;
    }

    await loadInitialWorkEditorData(state);
    bindWorkEditorEvents(state);
    await applyInitialRouteSelection(state);
    markWorkEditorLoaded(state, elements);
  } catch (error) {
    console.warn("catalogue_work_editor: init failed", error);
    await showWorkEditorInitError(elements.loadingNode);
  }
}

init();
