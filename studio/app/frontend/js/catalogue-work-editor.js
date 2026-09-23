import { saveCurrentWork } from "./catalogue-work-actions.js";
import { createWorkSeriesBrowser } from "./catalogue-work-series-browser.js";
import { applyWorkRecordMutation } from "./catalogue-work-action-records.js";
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
  loadStudioServerReadJson
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
  openWorkEmbeddedEntryModal
} from "./catalogue-work-editor-modals.js";
import {
  readProjectMediaFiles,
  readProjectMediaFolders,
  readWorkMediaSources
} from "./catalogue-editor-service-client.js";
import {
  renderWorkCurrentPreview,
  renderWorkReadiness,
  updateWorkSummary
} from "./catalogue-work-sections.js";
import { applyDraftToInputs, applyWorkMediaSourceConfig, applyReadonly, applyWorkFormText, clearReadonlyFields, getFieldNodeValue, renderSeriesPicker, renderWorkEditorFields, resolvedWorkMediaSourceId, setModeFieldAvailability, updateFieldMessages } from "./catalogue-work-form.js";
import {
  initializeWorkRouteState,
  setEmptySearchMode,
  setLoadedBulkWorks,
  setLoadedWorkRecord,
  setNewWorkMode,
  syncWorkRouteBusyState
} from "./catalogue-work-route-state.js";
import { deleteCurrentWork } from "./catalogue-work-actions.js";

import {
  applyInitialWorkRouteSelection,
  bindWorkSelectionControls,
  openWorkById,
  setWorkSelectionPopupVisibility
} from "./catalogue-work-selection.js";
import { WORK_DIMENSION_FIELD_KEYS, WORK_EDITABLE_FIELDS as EDITABLE_FIELDS, WORK_SERIES_ID_RE as SERIES_ID_RE, canonicalizeWorkScalar as canonicalizeScalar, embeddedEntriesEqual, normalizeSeriesId, normalizeText, normalizeWorkId, suggestNextWorkId } from "./catalogue-work-fields.js";
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

const REQUIRED_WORK_FIELDS = ["title", "year", "year_display"];

function setOpenInputMode(state) {
  state.searchNode.placeholder = t(state, "search_placeholder", "find work id(s): 00001, 00003-00005");
  state.searchNode.setAttribute("aria-label", t(state, "search_label", "Find work by id"));
}

async function loadWorkLookupRecord(workId) {
  const lookup = await loadStudioServerReadJson("catalogue_work_record", workId, { cache: "no-store" });
  if (!Array.isArray(lookup.gallery_ids)) throw new Error("Work Gallery membership is unavailable.");
  return { ...lookup, work: { ...lookup.work, gallery_ids: lookup.gallery_ids } };
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
  const errors = new Map();
  const active = key => state.mode !== "bulk" || state.bulkTouchedFields.has(key);
  if (state.mode === "new") {
    const workId = normalizeWorkId(state.draft.work_id);
    if (!workId) errors.set("work_id", "Enter a work id.");
    else if (state.workSearchById.has(workId)) errors.set("work_id", "Work id already exists.");
    for (const key of REQUIRED_WORK_FIELDS) if (!normalizeText(state.draft[key])) errors.set(key, "Enter " + key.replaceAll("_", " ") + ".");
  }
  if (active("year") && normalizeText(state.draft.year) && !/^-?\d+$/.test(state.draft.year)) errors.set("year", "Use a whole year or leave blank.");
  for (const key of WORK_DIMENSION_FIELD_KEYS) if (active(key) && normalizeText(state.draft[key]) && !Number.isFinite(Number(state.draft[key]))) errors.set(key, "Use a number or leave blank.");
  const series = normalizeText(state.draft.series_id);
  if (active("series_id") && series) {
    if (!SERIES_ID_RE.test(series)) errors.set("series_id", "Use one numeric Series id or leave blank.");
    else if (!state.seriesById.has(normalizeSeriesId(series))) errors.set("series_id", "Unknown Series id: " + series + ".");
  }
  if (state.mode !== "bulk") {
    const ids = state.draft.gallery_ids;
    if (!Array.isArray(ids) || ids.some(id => !state.galleriesById.has(id)) || new Set(ids).size !== ids.length) {
      errors.set("gallery_ids", "Select distinct existing galleries.");
    }
    const sources = state.workMediaSourceConfig?.mediaSourceIds || [];
    if (!sources.includes(resolvedWorkMediaSourceId(state))) errors.set("media_source_id", "Select a configured media source.");
    validateWorkEmbeddedItems(state.draft, {text: (key, fallback, tokens) => t(state, key, fallback, tokens)}).forEach((message, key) => errors.set(key, message));
  }
  return errors;
}

function clearActionMessages(state) {
  state.messageController.clearActionMessages();
}

function firstBulkMixedMessage(state) {
  if (state.mode !== "bulk") return "";
  for (const field of EDITABLE_FIELDS) {
    if (field.key === "media_source_id" || field.key === "gallery_ids") continue;
    if (!state.bulkMixedFields.has(field.key) || state.bulkTouchedFields.has(field.key)) continue;
    return field.key === "series_id"
      ? t(state, "bulk_field_mixed_series", "Mixed values. Leave untouched to preserve, enter one Series id to reassign, or clear to remove membership.")
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
    dirtyMessage: state.mode === "new" ? "" : catalogueDirtyWarningText({
      dirty,
      mode: state.mode,
      message: t(state, "dirty_warning", "Unsaved source changes.")
    })
  });
}


function updateEditorState(state) {
  state.seriesBrowser?.sync();
  const hasRecord = state.mode === "new" ? true : state.mode === "bulk" ? state.bulkWorkIds.length > 0 : Boolean(state.currentRecord);
  const errors = hasRecord ? validateDraft(state) : new Map();
  state.validationErrors = errors;
  updateFieldMessages(state, errors, workFormOptions(state));
  setModeFieldAvailability(state);
  updateSummary(state);
  setNodeTextWithState(state.buildImpactNode, "");

  const dirty = hasRecord && draftHasChanges(state);
  if (state.mode === "bulk" && hasRecord) {
    state.messageController.setDefaultMessage(t(state, "bulk_status_loaded", "Loaded {count} work records.", { count: String(state.bulkWorkIds.length) }));
  } else if (state.mode === "single" && hasRecord) {
    state.messageController.setDefaultMessage(t(state, "save_status_loaded", "Loaded work {work_id}.", { work_id: state.currentWorkId }));
  }
  renderEditorMessage(state, { hasRecord, dirty, errors });

  state.saveButton.textContent = t(state, "save_button", "Save");
  state.saveButton.disabled = catalogueSaveDisabled({
    hasRecord,
    isSaving: state.isSaving || state.isBuilding || state.isDeleting,
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
  renderReadiness(state);
  syncWorkRouteBusyState(state);
}

function onFieldInput(state, fieldKey) {
  const node = state.fieldNodes.get(fieldKey);
  if (!node) return;
  clearActionMessages(state);
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
    getMediaSourceId: () => resolvedWorkMediaSourceId(state),
    loadProjectFolders: (sourceId, query) => readProjectMediaFolders(sourceId, query),
    loadProjectFiles: (request) => readProjectMediaFiles(request)
  };
}

function workRouteStateOptions(state, overrides = {}) {
  return createWorkRouteStateOptions(state, {
    text: (key, fallback, tokens) => t(state, key, fallback, tokens),
    setTextWithState: (node, text, tone) => state.messageController.setRouteTextWithState(node, text, tone),
    setOpenInputMode: () => setOpenInputMode(state),
    setPopupVisibility: (visible) => setWorkSelectionPopupVisibility(state, visible),
    applyDraftToInputs: () => applyDraftToInputs(state),
    applyReadonly: () => applyReadonly(state),
    clearReadonlyFields: () => clearReadonlyFields(state),
    updateEditorState: () => updateEditorState(state)
  }, overrides);
}

function workSelectionOptions(state) {
  return {
    text: (key, fallback, tokens) => t(state, key, fallback, tokens),
    loadWorkLookupRecord,
    setLoadedBulkWorks: (workIds, recordsById, recordHashes) => {
      setLoadedBulkWorks(state, workIds, recordsById, recordHashes, workRouteStateOptions(state));
    },
    setLoadedWorkRecord: (workId, record, options = {}) => {
      applyWorkRecordMutation(state, { workId, record, recordHash: options.recordHash });
      setLoadedWorkRecord(state, workId, record, workRouteStateOptions(state, options));
    },
    updateEditorState: () => updateEditorState(state),
    saveCurrentWork: () => saveCurrentWork(state, workActionOptions(state)),
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
    loadWorkLookupRecord,
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

function updateSummary(state) {
  updateWorkSummary(state, workSectionOptions(state));
}

function applyWorkEditorText(state, elements) {
  setOpenInputMode(state);
  applyWorkFormText(state, workFormOptions(state));
  elements.openButton.textContent = t(state, "open_button", "Open");
  elements.newButton.textContent = t(state, "new_button", "New");
  elements.saveButton.textContent = t(state, "save_button", "Save");
  elements.deleteButton.textContent = t(state, "delete_button", "Delete");
}

async function configureWorkEditorRuntime(state, elements) {
  return configureCatalogueEditorRouteRuntime(state, {
    namespace: "catalogue_work_editor",
    applyText: (config) => {
      applyCatalogueEditorMediaAttrs(elements.root, config, [
        "worksPrimaryBase",
        "thumbWorksBase",
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
  const [sourcePayload, galleryPayload] = await Promise.all([
    readWorkMediaSources(),
    loadStudioServerReadJson("catalogue_galleries", "", { cache: "no-store" }),
    loadCatalogueEditorLookupMaps(state, [
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
    ])
  ]);
  if (!galleryPayload.galleries || typeof galleryPayload.galleries !== "object" || Array.isArray(galleryPayload.galleries)) {
    throw new Error("Gallery lookup is unavailable.");
  }
  state.galleriesById = new Map(Object.entries(galleryPayload.galleries));
  applyWorkMediaSourceConfig(state, sourcePayload);
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
    state.seriesBrowser = createWorkSeriesBrowser(state, elements, {
      draftHasChanges: () => draftHasChanges(state),
      onSeriesChanged: () => {
        renderSeriesPicker(state);
        updateEditorState(state);
      },
      openWork: workId => openWorkById(state, workId, workSelectionOptions(state))
    });
    bindWorkEditorEvents(state, {
      bindSelectionControls: () => bindWorkSelectionControls(state, workSelectionOptions(state)),
      renderEditorMessage: () => renderEditorMessage(state),
      openEmbeddedEntryModal: (kind, index) => openEmbeddedEntryModal(state, kind, index),
      deleteEmbeddedEntry: (kind, index) => deleteEmbeddedEntry(state, kind, index),
      setNewWorkMode: () => setNewWorkMode(state, workRouteStateOptions(state)),
      saveCurrentWork: () => saveCurrentWork(state, workActionOptions(state)),
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
