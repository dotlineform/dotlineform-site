import {
  getStudioRoute,
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
  catalogueDeleteDisabled,
  catalogueDirtyWarningText,
  catalogueDraftChangedFieldNames,
  catalogueDraftHasChanges,
  catalogueSaveDisabled
} from "./catalogue-editor-dirty-state.js";
import {
  formatCatalogueBuildPreview,
  formatCatalogueBuildPreviewModalHtml,
  formatCatalogueDeletePreview,
  formatCataloguePublicationPreview
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
  formatWorkSelectionList as formatSelectionList,
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
  initializeStudioRouteState,
  setStudioRouteBusy,
  setStudioRouteReady
} from "./studio-route-state.js";
import {
  buildSaveModeText,
  utcTimestamp
} from "./tag-studio-save.js";
import {
  loadCatalogueMediaConfig
} from "./catalogue-media-preview.js";
import {
  createStudioModalHost,
  openConfirmModal,
  renderStudioModalFrame
} from "./studio-modal.js";
import { buildStudioActivityContext } from "./studio-activity-context.js";
import {
  WORK_DATE_RE as DATE_RE,
  WORK_DIMENSION_FIELD_KEYS,
  WORK_EDITABLE_FIELDS as EDITABLE_FIELDS,
  WORK_SERIES_ID_RE as SERIES_ID_RE,
  WORK_STATUS_OPTIONS as STATUS_OPTIONS,
  buildCreateWorkPayload,
  buildWorkDraftFromRecord,
  buildWorkRecordFromDraft,
  canonicalizeWorkScalar as canonicalizeScalar,
  dedupeSeriesIds,
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

function previewExtraSeriesIdsForDraft(state) {
  const previousSeriesIds = parseSeriesIds(state.baselineDraft && state.baselineDraft.series_ids);
  const nextSeriesIds = parseSeriesIds(state.draft && state.draft.series_ids);
  return dedupeSeriesIds([
    ...state.pendingBuildExtraSeriesIds,
    ...previousSeriesIds
  ]).filter((seriesId) => !nextSeriesIds.includes(seriesId));
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

function buildBulkDraftFromRecords(records) {
  const drafts = records.map((record) => buildDraftFromRecord(record));
  const draft = {};
  const mixedFields = new Set();
  EDITABLE_FIELDS.forEach((field) => {
    const values = drafts.map((item) => canonicalizeScalar(field, item[field.key]));
    const first = values[0] || "";
    const allSame = values.every((value) => value === first);
    if (allSame) {
      draft[field.key] = drafts[0][field.key];
    } else {
      draft[field.key] = "";
      mixedFields.add(field.key);
    }
  });
  return { draft, mixedFields };
}

function parseBulkSeriesOperation(value) {
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

function setTextWithState(node, text, state = "") {
  if (!node) return;
  node.textContent = text || "";
  if (state) {
    node.dataset.state = state;
  } else {
    delete node.dataset.state;
  }
}

function routeModeForState(state) {
  if (state.mode === "new") return "new";
  if (state.mode === "bulk") return "bulk";
  if (state.currentRecord) return "single";
  return "empty";
}

function routeRecordLoadedForState(state) {
  if (state.mode === "bulk") return state.bulkWorkIds.length > 0;
  if (state.mode === "single") return Boolean(state.currentRecord);
  return false;
}

function routeStateDetail(state) {
  return {
    route: "catalogue-work",
    mode: routeModeForState(state),
    service: state.serverAvailable ? "available" : "unavailable",
    recordLoaded: routeRecordLoadedForState(state)
  };
}

function syncRouteBusyState(state) {
  setStudioRouteBusy(
    state.root,
    Boolean(state.isSaving || state.isBuilding || state.isPreviewingBuild || state.isDeleting),
    routeStateDetail(state)
  );
}

function markRouteReady(state, ready) {
  setStudioRouteReady(state.root, ready, routeStateDetail(state));
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

function buildDraftFromRecord(record) {
  return buildWorkDraftFromRecord(record, {
    fields: EDITABLE_FIELDS,
    downloadFields: DOWNLOAD_FIELDS,
    linkFields: LINK_FIELDS
  });
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

function syncUrl(workValue, mode = "") {
  const url = new URL(window.location.href);
  if (mode === "new") {
    url.searchParams.delete("work");
    url.searchParams.set("mode", "new");
  } else if (workValue) {
    url.searchParams.delete("mode");
    url.searchParams.set("work", workValue);
  } else {
    url.searchParams.delete("mode");
    url.searchParams.delete("work");
  }
  window.history.replaceState({}, "", url.toString());
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

function currentWorkIsPublished(state) {
  return normalizeText(state.draft && state.draft.status).toLowerCase() === "published";
}

function currentWorkIsDraft(state) {
  return normalizeText(state.draft && state.draft.status).toLowerCase() === "draft";
}

function bulkSelectionHasPublishedRecords(state) {
  if (state.mode !== "bulk") return false;
  return state.bulkWorkIds.some((workId) => {
    const record = state.bulkRecords.get(workId);
    return normalizeText(record && record.status).toLowerCase() === "published";
  });
}

function bulkPublishedBuildTargets(state) {
  return state.bulkWorkIds
    .filter((workId) => {
      const record = state.bulkRecords.get(workId);
      return normalizeText(record && record.status).toLowerCase() === "published";
    })
    .map((workId) => ({ work_id: workId, extra_series_ids: [] }));
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

function setLoadedRecord(state, workId, record, options = {}) {
  state.mode = "single";
  state.currentWorkId = workId;
  state.currentRecord = record;
  state.currentLookup = options.lookup || state.currentLookup;
  state.currentRecordHash = normalizeText(options.recordHash || state.currentRecordHash);
  state.bulkWorkIds = [];
  state.bulkRecords = new Map();
  state.bulkRecordHashes = new Map();
  state.bulkMixedFields = new Set();
  state.bulkTouchedFields = new Set();
  state.bulkBuildTargets = [];
  state.baselineDraft = buildDraftFromRecord(record);
  state.draft = { ...state.baselineDraft };
  setOpenInputMode(state);
  applyDraftToInputs(state, workFormOptions(state));
  applyReadonly(state);
  syncUrl(workId);
  setTextWithState(state.contextNode, t(state, "context_loaded", "Editing source metadata for work {work_id}.", { work_id: workId }));
  setTextWithState(state.statusNode, t(state, "save_status_loaded", "Loaded work {work_id}.", { work_id: workId }));
  setTextWithState(state.warningNode, "");
  if (!options.keepResult) {
    setTextWithState(state.resultNode, "");
  }
  updateEditorState(state);
}

function setLoadedBulkWorks(state, workIds, recordsById, recordHashes, options = {}) {
  state.mode = "bulk";
  state.currentWorkId = "";
  state.currentRecord = null;
  state.currentLookup = null;
  state.currentRecordHash = "";
  state.bulkWorkIds = workIds.slice();
  state.bulkRecords = new Map(recordsById);
  state.bulkRecordHashes = new Map(recordHashes);
  state.bulkBuildTargets = Array.isArray(options.buildTargets) ? options.buildTargets.slice() : [];
  const records = workIds.map((workId) => recordsById.get(workId)).filter(Boolean);
  const bulkDraft = buildBulkDraftFromRecords(records);
  state.baselineDraft = { ...bulkDraft.draft };
  state.draft = { ...bulkDraft.draft };
  state.bulkMixedFields = bulkDraft.mixedFields;
  state.bulkTouchedFields = new Set();
  setOpenInputMode(state);
  applyDraftToInputs(state, workFormOptions(state));
  clearReadonlyFields(state);
  syncUrl(workIds.join(","));
  setTextWithState(
    state.contextNode,
    t(state, "bulk_context_loaded", "Bulk editing {count} work records: {work_ids}.", {
      count: String(workIds.length),
      work_ids: formatSelectionList(workIds)
    })
  );
  setTextWithState(
    state.statusNode,
    t(state, "bulk_status_loaded", "Loaded {count} work records.", { count: String(workIds.length) })
  );
  setTextWithState(state.warningNode, "");
  if (!options.keepResult) {
    setTextWithState(state.resultNode, "");
  }
  updateEditorState(state);
}

function setNewWorkMode(state, options = {}) {
  state.mode = "new";
  state.currentWorkId = "";
  state.currentRecord = null;
  state.currentLookup = null;
  state.currentRecordHash = "";
  state.bulkWorkIds = [];
  state.bulkRecords = new Map();
  state.bulkRecordHashes = new Map();
  state.bulkMixedFields = new Set();
  state.bulkTouchedFields = new Set();
  state.bulkBuildTargets = [];
  state.baselineDraft = {};
  state.draft = {};
  EDITABLE_FIELDS.forEach((field) => {
    state.draft[field.key] = "";
  });
  state.draft.status = "draft";
  state.draft.published_date = "";
  state.draft.downloads = [];
  state.draft.links = [];
  state.draft.work_id = normalizeWorkId(options.workId) || state.nextSuggestedWorkId || suggestNextWorkId(Array.from(state.workSearchById.values()));
  state.searchNode.value = state.draft.work_id;
  state.searchNode.placeholder = t(state, "new_work_id_placeholder", "new work id");
  state.searchNode.setAttribute("aria-label", t(state, "new_work_id_label", "New work id"));
  state.detailSearchNode.value = "";
  state.pendingBuildExtraSeriesIds = [];
  state.rebuildPending = false;
  state.buildPreview = null;
  applyDraftToInputs(state, workFormOptions(state));
  clearReadonlyFields(state);
  setPopupVisibility(state, false);
  syncUrl("", "new");
  setTextWithState(state.contextNode, t(state, "new_context_loaded", "Creating a draft work source record."));
  setTextWithState(state.statusNode, "");
  setTextWithState(state.warningNode, "");
  if (!options.keepResult) {
    setTextWithState(state.resultNode, "");
  }
  updateEditorState(state);
}

function setEmptySearchMode(state, options = {}) {
  state.mode = "single";
  state.currentWorkId = "";
  state.currentRecord = null;
  state.currentLookup = null;
  state.currentRecordHash = "";
  state.bulkWorkIds = [];
  state.bulkRecords = new Map();
  state.bulkRecordHashes = new Map();
  state.bulkMixedFields = new Set();
  state.bulkTouchedFields = new Set();
  state.bulkBuildTargets = [];
  state.baselineDraft = null;
  state.draft = {};
  EDITABLE_FIELDS.forEach((field) => {
    state.draft[field.key] = "";
  });
  state.draft.downloads = [];
  state.draft.links = [];
  state.detailSearchNode.value = "";
  state.pendingBuildExtraSeriesIds = [];
  state.rebuildPending = false;
  state.buildPreview = null;
  setOpenInputMode(state);
  if (!options.keepSearchValue) {
    state.searchNode.value = "";
  }
  applyDraftToInputs(state, workFormOptions(state));
  clearReadonlyFields(state);
  setPopupVisibility(state, false);
  syncUrl("");
  setTextWithState(state.contextNode, t(state, "missing_work_param", "Search for a work by work id."));
  setTextWithState(state.warningNode, "");
  if (!options.keepResult) {
    setTextWithState(state.resultNode, "");
  }
  updateEditorState(state);
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
  syncRouteBusyState(state);
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

function workSectionOptions(state) {
  return {
    text: (key, fallback, tokens) => t(state, key, fallback, tokens),
    changedWorkFieldNames,
    draftHasChanges,
    isCurrentWorkPublished: currentWorkIsPublished,
    onPreviewBuildImpact: previewCurrentBuildImpact,
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

async function saveCurrentWork(state) {
  if (state.mode === "new") {
    await createCurrentWork(state);
    return;
  }
  if (state.mode === "bulk") {
    if (!state.bulkWorkIds.length) return;
  } else if (!state.currentRecord) {
    return;
  }
  const errors = validateDraft(state);
  updateFieldMessages(state, errors, workFormOptions(state));
  if (errors.size > 0) {
    setTextWithState(state.statusNode, t(state, "save_status_validation_error", "Fix validation errors before saving."), "error");
    updateEditorState(state);
    return;
  }

  if (!draftHasChanges(state)) {
    setTextWithState(state.statusNode, t(state, "save_status_no_changes", "No changes to save."));
    setTextWithState(state.resultNode, t(state, "save_result_unchanged", "Source already matches the current form values."));
    updateEditorState(state);
    return;
  }

  state.isSaving = true;
  state.saveButton.disabled = true;
  setTextWithState(
    state.statusNode,
    (state.mode === "bulk" ? bulkSelectionHasPublishedRecords(state) : currentWorkIsPublished(state))
      ? t(state, "save_status_saving_and_updating", "Saving source record and updating site…")
      : t(state, "save_status_saving", "Saving source record…")
  );
  setTextWithState(state.resultNode, "");

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
      setLoadedBulkWorks(state, state.bulkWorkIds, state.bulkRecords, state.bulkRecordHashes, {
        keepResult: true,
        buildTargets: state.bulkBuildTargets
      });
      if (outcome.kind === "saved_and_updated") {
        setTextWithState(
          state.resultNode,
          t(state, "bulk_save_result_success_applied", "Saved {count} work records and updated public catalogue output for published records at {saved_at}.", {
            count: String(response.changed_count || 0),
            saved_at: outcome.stamp
          }),
          "success"
        );
        setTextWithState(state.statusNode, t(state, "build_status_success", "Site update completed."), "success");
      } else if (outcome.kind === "saved_update_failed") {
        setTextWithState(
          state.resultNode,
          t(state, "bulk_save_result_success_partial", "Saved {count} work records at {saved_at}, but the public update failed.", {
            count: String(response.changed_count || 0),
            saved_at: outcome.stamp
          }),
          "warn"
        );
        setTextWithState(state.statusNode, `${t(state, "build_status_failed", "Site update failed.")} ${outcome.error}`.trim(), "error");
      } else {
        setTextWithState(
          state.resultNode,
          response.changed
            ? t(state, "bulk_save_result_success", "Saved {count} work records at {saved_at}.", {
              count: String(response.changed_count || 0),
              saved_at: outcome.stamp
            })
            : t(state, "save_result_unchanged", "Source already matches the current form values."),
          response.changed ? "success" : ""
        );
        setTextWithState(
          state.statusNode,
          t(state, "bulk_status_loaded", "Loaded {count} work records.", { count: String(state.bulkWorkIds.length) }),
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
    const lookup = await loadWorkLookupRecord(state, state.currentWorkId);
    setLoadedRecord(state, state.currentWorkId, record, {
      recordHash: response.record_hash || normalizeText(lookup && lookup.record_hash) || "",
      keepResult: true,
      lookup
    });
    await refreshBuildPreview(state);
    if (outcome.kind === "saved_and_updated") {
      setTextWithState(
        state.resultNode,
        t(state, "save_result_success_applied", "Saved source changes and updated the public catalogue at {saved_at}.", { saved_at: outcome.stamp }),
        "success"
      );
      setTextWithState(state.statusNode, t(state, "build_status_success", "Site update completed."), "success");
    } else if (outcome.kind === "saved_update_failed") {
      setTextWithState(
        state.resultNode,
        t(state, "save_result_success_partial", "Source changes were saved at {saved_at}, but the public update failed.", { saved_at: outcome.stamp }),
        "warn"
      );
      setTextWithState(state.statusNode, `${t(state, "build_status_failed", "Site update failed.")} ${outcome.error}`.trim(), "error");
    } else if (outcome.kind === "saved_unpublished") {
      setTextWithState(
        state.resultNode,
        t(state, "save_result_success_unpublished", "Source saved at {saved_at}. Public update is unavailable while the work is not published.", { saved_at: outcome.stamp }),
        "success"
      );
      setTextWithState(state.statusNode, t(state, "save_status_loaded", "Loaded work {work_id}.", { work_id: state.currentWorkId }), "success");
    } else {
      setTextWithState(
        state.resultNode,
        response.changed
          ? t(state, "save_result_success", "Source saved at {saved_at}.", { saved_at: outcome.stamp })
          : t(state, "save_result_unchanged", "Source already matches the current form values."),
        response.changed ? "success" : ""
      );
      setTextWithState(state.statusNode, t(state, "save_status_loaded", "Loaded work {work_id}.", { work_id: state.currentWorkId }), "success");
    }
  } catch (error) {
    const isConflict = Number(error && error.status) === 409;
    const message = isConflict
      ? t(state, "save_status_conflict", "Source record changed since this page loaded. Reload the work before saving again.")
      : `${t(state, "save_status_failed", "Source save failed.")} ${normalizeText(error && error.message)}`.trim();
    setTextWithState(state.statusNode, message, "error");
  } finally {
    state.isSaving = false;
    updateEditorState(state);
  }
}

async function createCurrentWork(state) {
  if (state.mode !== "new") return;
  const errors = validateDraft(state);
  updateFieldMessages(state, errors, workFormOptions(state));
  if (errors.size > 0) {
    const workIdError = errors.get("work_id") || "";
    setTextWithState(
      state.statusNode,
      workIdError || t(state, "create_status_validation_error", "Fix validation errors before creating the draft work."),
      "error"
    );
    updateEditorState(state);
    return;
  }

  state.isSaving = true;
  updateEditorState(state);
  setTextWithState(state.statusNode, t(state, "create_status_saving", "Creating draft work..."));
  setTextWithState(state.resultNode, "");

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
    await openWorkById(state, workId);
    setTextWithState(state.resultNode, t(state, "create_result_success", "Created draft work {work_id}. Opening edit mode...", { work_id: workId }), "success");
    setTextWithState(state.statusNode, t(state, "create_status_success", "Created draft work {work_id}.", { work_id: workId }), "success");
  } catch (error) {
    setTextWithState(state.statusNode, `${t(state, "create_status_failed", "Draft work create failed.")} ${normalizeText(error && error.message)}`.trim(), "error");
  } finally {
    state.isSaving = false;
    updateEditorState(state);
  }
}

async function refreshBuildPreview(state) {
  if (state.mode === "bulk") {
    const previewTargets = state.rebuildPending && state.bulkBuildTargets.length
      ? state.bulkBuildTargets
      : bulkPublishedBuildTargets(state);
    setTextWithState(
      state.buildImpactNode,
      previewTargets.length
        ? t(state, "bulk_build_preview", "Public update preview: {count} published work scope(s) will be updated.", {
          count: String(previewTargets.length)
        })
        : ""
    );
    state.buildPreview = null;
    renderCurrentPreview(state);
    renderReadiness(state);
    return;
  }
  if (!state.currentWorkId || !state.serverAvailable) {
    setTextWithState(state.buildImpactNode, "");
    state.buildPreview = null;
    renderCurrentPreview(state);
    renderReadiness(state);
    return;
  }
  if (!currentWorkIsPublished(state)) {
    setTextWithState(state.buildImpactNode, t(state, "build_preview_unpublished", "Site update unavailable while the work is not published."));
    state.buildPreview = null;
    renderCurrentPreview(state);
    renderReadiness(state);
    return;
  }
  try {
    const response = await previewCatalogueBuild({
      work_id: state.currentWorkId,
      extra_series_ids: state.pendingBuildExtraSeriesIds
    });
    state.buildPreview = response && response.build ? response.build : null;
    setTextWithState(state.buildImpactNode, formatCatalogueBuildPreview(state.buildPreview, {
      text: (key, fallback, tokens) => t(state, key, fallback, tokens),
      defaultTemplate: "Public update preview: work {work_ids}; series {series_ids}; catalogue search {search_rebuild}."
    }));
    renderCurrentPreview(state);
    renderReadiness(state);
  } catch (error) {
    state.buildPreview = null;
    setTextWithState(
      state.buildImpactNode,
      `${t(state, "build_preview_failed", "Public update preview unavailable.")} ${normalizeText(error && error.message)}`.trim(),
      "error"
    );
    renderCurrentPreview(state);
    renderReadiness(state);
  }
}

async function previewCurrentBuildImpact(state) {
  if (!state.currentRecord || !state.currentWorkId || state.mode !== "single") return;
  if (!state.serverAvailable) {
    setTextWithState(state.statusNode, t(state, "build_preview_server_unavailable", "Local catalogue server unavailable."), "error");
    return;
  }
  if (!currentWorkIsPublished(state)) {
    setTextWithState(state.statusNode, t(state, "build_preview_unpublished", "Public update unavailable while the work is not published."), "warn");
    return;
  }
  if (state.validationErrors.size > 0) {
    setTextWithState(state.statusNode, t(state, "save_status_validation_error", "Fix validation errors before saving."), "error");
    return;
  }
  const changedFields = changedWorkFieldNames(state);
  if (!changedFields.length) {
    setTextWithState(state.statusNode, t(state, "build_preview_no_changes", "No unsaved changes to preview."));
    return;
  }

  state.isPreviewingBuild = true;
  updateEditorState(state);
  setTextWithState(state.statusNode, t(state, "build_preview_status_running", "Preparing public update preview..."));
  try {
    const response = await previewCatalogueBuild({
      work_id: state.currentWorkId,
      record_family: "work",
      changed_fields: changedFields,
      extra_series_ids: previewExtraSeriesIdsForDraft(state)
    });
    openBuildPreviewModal(state, response, changedFields);
    setTextWithState(state.statusNode, t(state, "save_status_loaded", "Loaded work {work_id}.", { work_id: state.currentWorkId }));
  } catch (error) {
    setTextWithState(
      state.statusNode,
      `${t(state, "build_preview_failed", "Public update preview unavailable.")} ${normalizeText(error && error.message)}`.trim(),
      "error"
    );
  } finally {
    state.isPreviewingBuild = false;
    updateEditorState(state);
  }
}

async function importWorkProse(state) {
  if (!state.currentRecord || !state.currentWorkId || !state.serverAvailable) return;
  if (draftHasChanges(state)) {
    setTextWithState(state.statusNode, t(state, "prose_import_save_first", "Save source changes before importing prose."), "error");
    return;
  }

  state.isBuilding = true;
  updateEditorState(state);
  setTextWithState(state.statusNode, t(state, "prose_import_preview_running", "Previewing staged prose…"));
  setTextWithState(state.resultNode, "");
  try {
    const preview = await previewCatalogueProseImport({
      target_kind: "work",
      work_id: state.currentWorkId
    });
    if (!preview.valid) {
      const errors = Array.isArray(preview.errors) ? preview.errors.join(" ") : "";
      throw new Error(errors || t(state, "prose_import_preview_invalid", "Staged prose is not ready to import."));
    }
    let confirmOverwrite = false;
    if (preview.overwrite_required) {
      const message = t(
        state,
        "prose_import_confirm_overwrite",
        "Overwrite existing prose source at {target_path} with staged file {staging_path}?",
        {
          target_path: normalizeText(preview.target_path),
          staging_path: normalizeText(preview.staging_path)
        }
      );
      confirmOverwrite = window.confirm(message);
      if (!confirmOverwrite) {
        setTextWithState(state.statusNode, t(state, "prose_import_overwrite_cancelled", "Prose import cancelled."), "warning");
        return;
      }
    }
    setTextWithState(state.statusNode, t(state, "prose_import_running", "Importing staged prose…"));
    const importResponse = await applyCatalogueProseImport({
      target_kind: "work",
      work_id: state.currentWorkId,
      confirm_overwrite: confirmOverwrite
    });
    await refreshBuildPreview(state);
    const completedAt = normalizeText(importResponse.imported_at_utc || utcTimestamp());
    setTextWithState(
      state.resultNode,
      t(state, "prose_import_result_success", "Prose imported to {target_path} at {completed_at}. The next site update will publish it.", {
        completed_at: completedAt,
        target_path: normalizeText(importResponse.target_path)
      }),
      "success"
    );
    setTextWithState(state.statusNode, t(state, "prose_import_status_success", "Prose import completed."), "success");
  } catch (error) {
    setTextWithState(
      state.statusNode,
      `${t(state, "prose_import_status_failed", "Prose import failed.")} ${normalizeText(error && error.message)}`.trim(),
      "error"
    );
  } finally {
    state.isBuilding = false;
    updateEditorState(state);
  }
}

async function buildCurrentWork(state) {
  if (state.mode === "bulk") {
    if (!state.bulkWorkIds.length || !state.serverAvailable) return;
  } else if (!state.currentRecord || !state.serverAvailable || !currentWorkIsPublished(state)) {
    return;
  }
  state.isBuilding = true;
  updateEditorState(state);
  setTextWithState(state.statusNode, t(state, "build_status_running", "Updating site…"));
  setTextWithState(state.resultNode, "");
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
      await refreshBuildPreview(state);
      const completedAt = utcTimestamp();
      setTextWithState(
        state.resultNode,
        t(state, "bulk_build_result_success", "Updated {count} work scopes at {completed_at}. Studio Activity updated.", {
          count: String(buildTargets.length),
          completed_at: completedAt
        }),
        "success"
      );
      setTextWithState(state.statusNode, t(state, "build_status_success", "Site update completed."), "success");
      return;
    }

    const response = await applyCatalogueBuild({
      work_id: state.currentWorkId,
      extra_series_ids: state.pendingBuildExtraSeriesIds
    });
    state.rebuildPending = false;
    state.pendingBuildExtraSeriesIds = [];
    await refreshBuildPreview(state);
    const completedAt = normalizeText(response.completed_at_utc || utcTimestamp());
    setTextWithState(
      state.resultNode,
      t(state, "build_result_success", "Public catalogue updated at {completed_at}. Studio Activity updated.", { completed_at: completedAt }),
      "success"
    );
    setTextWithState(state.statusNode, t(state, "build_status_success", "Site update completed."), "success");
  } catch (error) {
    setTextWithState(
      state.statusNode,
      `${t(state, "build_status_failed", "Site update failed.")} ${normalizeText(error && error.message)}`.trim(),
      "error"
    );
  } finally {
    state.isBuilding = false;
    updateEditorState(state);
  }
}

async function applyPublicationChange(state) {
  if (state.mode !== "single" || !state.currentRecord || !state.currentWorkId || !state.serverAvailable) return;
  const action = currentWorkIsPublished(state) ? "unpublish" : currentWorkIsDraft(state) ? "publish" : "";
  if (!action) {
    setTextWithState(state.statusNode, t(state, "publication_status_invalid", "Publication is available only for draft or published works."), "error");
    return;
  }
  if (action === "publish" && draftHasChanges(state)) {
    setTextWithState(state.statusNode, t(state, "publication_save_first", "Save source changes before publishing."), "error");
    return;
  }

  if (action === "publish") {
    const errors = validateDraft(state);
    updateFieldMessages(state, errors, workFormOptions(state));
    if (errors.size > 0) {
      setTextWithState(state.statusNode, t(state, "publication_status_validation_error", "Fix validation errors before changing publication state."), "error");
      updateEditorState(state);
      return;
    }
  }

  state.isBuilding = true;
  updateEditorState(state);
  setTextWithState(
    state.statusNode,
    action === "publish"
      ? t(state, "publication_preview_publish_running", "Preparing publish preview…")
      : t(state, "publication_preview_unpublish_running", "Preparing unpublish preview…")
  );
  setTextWithState(state.resultNode, "");

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
      const message = blockers[0] || t(state, "publication_status_blocked", "Publication change is blocked.");
      setTextWithState(state.statusNode, message, "error");
      return;
    }

    if (action === "unpublish") {
      const summary = formatCataloguePublicationPreview(preview, {
        text: (key, fallback, tokens) => t(state, key, fallback, tokens),
        defaultText: "Unpublish this work?",
        includeDirtyNote: draftHasChanges(state)
      });
      if (!window.confirm(summary)) {
        setTextWithState(state.statusNode, t(state, "publication_status_cancelled", "Publication change cancelled."));
        return;
      }
    }

    setTextWithState(
      state.statusNode,
      action === "publish"
        ? t(state, "publication_publish_running", "Publishing work…")
        : t(state, "publication_unpublish_running", "Unpublishing work…")
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
    const lookup = await loadWorkLookupRecord(state, workId).catch(() => null);
    setLoadedRecord(state, workId, record, {
      recordHash,
      keepResult: true,
      lookup
    });
    await refreshBuildPreview(state);

    if (response.status === "public_update_failed") {
      const error = normalizeText(response.public_update && response.public_update.error);
      setTextWithState(state.statusNode, `${t(state, "publication_status_public_failed", "Publication state changed, but the public update failed.")} ${error}`.trim(), "error");
      setTextWithState(state.resultNode, t(state, "publication_result_public_failed", "Source status changed, but public artifacts did not finish updating."), "warn");
      return;
    }

    if (action === "publish") {
      setTextWithState(state.statusNode, t(state, "publication_status_published", "Work published."), "success");
      setTextWithState(state.resultNode, t(state, "publication_result_published", "Work is published and public catalogue output has been updated."), "success");
    } else {
      setTextWithState(state.statusNode, t(state, "publication_status_unpublished", "Work unpublished."), "success");
      setTextWithState(state.resultNode, t(state, "publication_result_unpublished", "Work is draft again and public catalogue output has been cleaned up."), "success");
    }
  } catch (error) {
    const message = Number(error && error.status) === 409
      ? t(state, "publication_status_conflict", "Source record changed since this page loaded. Reload before changing publication state.")
      : `${t(state, "publication_status_failed", "Publication change failed.")} ${normalizeText(error && error.message)}`.trim();
    setTextWithState(state.statusNode, message, "error");
  } finally {
    state.isBuilding = false;
    updateEditorState(state);
  }
}

function countMediaItems(media, group) {
  const values = media && media[group] && typeof media[group] === "object" ? media[group] : {};
  return Object.values(values).reduce((total, items) => total + (Array.isArray(items) ? items.length : 0), 0);
}

async function refreshWorkMedia(state) {
  if (!state.currentRecord || !state.currentWorkId || !state.serverAvailable || draftHasChanges(state)) return;
  state.isBuilding = true;
  updateEditorState(state);
  setTextWithState(state.statusNode, t(state, "media_refresh_status_running", "Refreshing media…"));
  setTextWithState(state.resultNode, "");
  try {
    const response = await applyCatalogueBuild({
      work_id: state.currentWorkId,
      media_only: true,
      force: true
    });
    const blockedCount = countMediaItems(response && response.media, "blocked");
    await refreshBuildPreview(state);
    if (blockedCount > 0) {
      setTextWithState(state.statusNode, t(state, "media_refresh_status_blocked", "Media refresh blocked."), "error");
      setTextWithState(state.resultNode, normalizeText(response && response.media && response.media.summary), "error");
      return;
    }
    setTextWithState(state.statusNode, t(state, "media_refresh_status_success", "Media refresh completed."), "success");
    setTextWithState(state.resultNode, t(state, "media_refresh_result_success", "Thumbnails updated; primary variants staged for publishing."), "success");
  } catch (error) {
    setTextWithState(
      state.statusNode,
      `${t(state, "media_refresh_status_failed", "Media refresh failed.")} ${normalizeText(error && error.message)}`.trim(),
      "error"
    );
  } finally {
    state.isBuilding = false;
    updateEditorState(state);
  }
}

async function deleteCurrentWork(state) {
  if (!state.currentRecord || state.mode === "bulk" || !state.serverAvailable) return;
  state.isDeleting = true;
  updateEditorState(state);
  setTextWithState(state.statusNode, t(state, "delete_status_running", "Preparing delete preview…"));
  setTextWithState(state.resultNode, "");
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
      const message = blockers[0] || validationErrors[0] || t(state, "delete_status_blocked", "Delete is blocked.");
      state.isDeleting = false;
      updateEditorState(state);
      setTextWithState(state.statusNode, message, "error");
      return;
    }
    const summary = formatCatalogueDeletePreview(preview, {
      text: (key, fallback, tokens) => t(state, key, fallback, tokens),
      defaultText: "Delete this source record?"
    });
    if (!window.confirm(summary)) {
      state.isDeleting = false;
      updateEditorState(state);
      setTextWithState(state.statusNode, t(state, "delete_status_cancelled", "Delete cancelled."));
      return;
    }
    setTextWithState(state.statusNode, t(state, "delete_status_running", "Deleting source record…"));
    await applyCatalogueDelete(request);
    const route = getStudioRoute(state.config, "catalogue_status");
    window.location.assign(route);
  } catch (error) {
    const message = Number(error && error.status) === 409
      ? t(state, "delete_status_conflict", "Source record changed since this page loaded. Reload before deleting again.")
      : `${t(state, "delete_status_failed", "Source delete failed.")} ${normalizeText(error && error.message)}`.trim();
    state.isDeleting = false;
    updateEditorState(state);
    setTextWithState(state.statusNode, message, "error");
  }
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
  setLoadedBulkWorks(state, workIds, recordsById, recordHashes);
  await refreshBuildPreview(state);
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
  setLoadedRecord(state, workId, record, {
    recordHash: await computeRecordHash(record),
    lookup
  });
  await refreshBuildPreview(state);
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
      saveCurrentWork(state).catch((error) => {
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
      setEmptySearchMode(state, { keepSearchValue: true });
    }
    openWorkSelection(state, state.searchNode.value).catch((error) => {
      console.warn("catalogue_work_editor: failed to open requested work selection", error);
    });
  });
  state.newButton.addEventListener("click", () => {
    setNewWorkMode(state);
  });
  state.readinessNode.addEventListener("click", (event) => {
    const mediaButton = event.target && event.target.closest ? event.target.closest("[data-media-refresh]") : null;
    if (mediaButton) {
      refreshWorkMedia(state).catch((error) => {
        console.warn("catalogue_work_editor: unexpected media refresh failure", error);
      });
      return;
    }
    const proseButton = event.target && event.target.closest ? event.target.closest("[data-prose-import]") : null;
    if (!proseButton) return;
    importWorkProse(state).catch((error) => {
      console.warn("catalogue_work_editor: unexpected prose import failure", error);
    });
  });
  state.saveButton.addEventListener("click", () => saveCurrentWork(state).catch((error) => {
    console.warn("catalogue_work_editor: unexpected save failure", error);
  }));
  state.publicationButton.addEventListener("click", () => applyPublicationChange(state).catch((error) => {
    console.warn("catalogue_work_editor: unexpected publication failure", error);
  }));
  state.deleteButton.addEventListener("click", () => deleteCurrentWork(state).catch((error) => {
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
      setEmptySearchMode(state, { keepSearchValue: true });
      setTextWithState(
        state.statusNode,
        `${t(state, "load_requested_work_failed", "Failed to load the requested work.")} ${normalizeText(error && error.message)}`.trim(),
        "error"
      );
    }
  } else if (requestedMode === "new") {
    setNewWorkMode(state);
  } else {
    setEmptySearchMode(state);
  }
}

function markWorkEditorLoaded(state, elements) {
  state.root.hidden = false;
  elements.loadingNode.hidden = true;
  markRouteReady(state, true);
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

  initializeStudioRouteState(elements.root, { route: "catalogue-work" });
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
