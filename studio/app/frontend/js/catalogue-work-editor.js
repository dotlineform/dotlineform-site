import { saveCurrentWork } from "./catalogue-work-actions.js";
import { createWorkSeriesBrowser } from "./catalogue-work-series-browser.js";
import { createWorkEditorLayout } from "./catalogue-work-layout.js";
import { editWorkDefinition, offerEmptyGalleryCleanup } from "./catalogue-work-definitions.js";
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
  readCatalogueRefreshStatus,
  readProjectMediaFiles,
  readProjectMediaFolders,
  readWorkMediaSources,
  openWorkProjectMedia,
  refreshCatalogue as requestCatalogueRefresh
} from "./catalogue-editor-service-client.js";
import { openNativeWorkAttachment, syncPendingAttachmentNames } from "./catalogue-work-attachments.js";
import {
  renderWorkCurrentPreview,
  renderWorkReadiness,
  updateWorkSummary
} from "./catalogue-work-sections.js";
import { applyDraftToInputs, applyWorkMediaSourceConfig, applyReadonly, applyWorkFormText, clearReadonlyFields, getFieldNodeValue, renderWorkEditorFields, resolvedWorkMediaSourceId, setModeFieldAvailability, updateFieldMessages } from "./catalogue-work-form.js";
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
  openWorkSelection,
  setWorkSelectionPopupVisibility
} from "./catalogue-work-selection.js";
import { NEW_WORK_EDITABLE_FIELDS, WORK_DIMENSION_FIELD_KEYS, WORK_EDITABLE_FIELDS as EDITABLE_FIELDS, WORK_FIELD_DEFINITIONS, WORK_SERIES_ID_RE as SERIES_ID_RE, canonicalizeWorkScalar as canonicalizeScalar, embeddedEntriesEqual, isWorkFieldRequired, normalizeSeriesId, normalizeText, normalizeWorkId, suggestNextWorkId } from "./catalogue-work-fields.js";
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
  if (kind === "download" && index === null) {
    try {
      openNativeWorkAttachment(state, {
        onChange: () => { clearActionMessages(state); updateEditorState(state); },
        onError: error => state.messageController.setActionTextWithState(state.statusNode, error.message, "error")
      });
    } catch (error) {
      state.messageController.setActionTextWithState(state.statusNode, error.message, "error");
    }
    return;
  }
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
  const filename = kind === "download" ? state.draft.downloads[index]?.filename : "";
  const result = await confirmWorkEmbeddedDeleteModal(state, kind, index, {
    text: (key, fallback, tokens) => t(state, key, fallback, tokens)
  });
  if (!result || !result.confirmed) return;
  clearActionMessages(state);
  state.draft[result.entriesKey] = result.entries;
  if (filename) state.pendingAttachments.delete(filename);
  updateEditorState(state);
}

function draftHasChanges(state) {
  if (state.pendingWorkBatch) return true;
  if (state.mode !== "bulk" && (state.regenerateImage || state.pendingAttachments.size)) return true;
  return catalogueDraftHasChanges({
    mode: state.mode,
    fields: state.mode === "new" ? NEW_WORK_EDITABLE_FIELDS : EDITABLE_FIELDS,
    draft: state.draft,
    baselineDraft: state.baselineDraft,
    touchedFields: state.bulkTouchedFields,
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

function validateDraft(state) {
  const errors = new Map();
  const active = key => state.mode !== "bulk" || state.bulkTouchedFields.has(key);
  for (const field of Object.values(WORK_FIELD_DEFINITIONS)) {
    if (state.pendingWorkBatch && ["work_id", "title"].includes(field.key)) continue;
    if (isWorkFieldRequired(field, state.mode) && !normalizeText(state.draft[field.key])) {
      // Missing required values block Save; bold labels convey the requirement.
      errors.set(field.key, "");
    }
  }
  if (state.mode === "new" && !state.pendingWorkBatch) {
    const workId = normalizeWorkId(state.draft.work_id);
    if (!workId) errors.set("work_id", "");
    else if (state.workSearchById.has(workId)) errors.set("work_id", "Work id already exists.");
  }
  if (active("year") && normalizeText(state.draft.year) && !/^-?\d+$/.test(state.draft.year)) errors.set("year", "Use a whole year.");
  for (const key of WORK_DIMENSION_FIELD_KEYS) if (active(key) && normalizeText(state.draft[key]) && !Number.isFinite(Number(state.draft[key]))) errors.set(key, "Use a number or leave blank.");
  const series = normalizeText(state.draft.series_id);
  if (active("series_id") && series) {
    if (!SERIES_ID_RE.test(series)) errors.set("series_id", "Use one numeric Series id.");
    else if (!state.seriesById.has(normalizeSeriesId(series))) errors.set("series_id", "Unknown Series id: " + series + ".");
  }
  if (active("gallery_ids")) {
    const ids = state.draft.gallery_ids;
    if (!Array.isArray(ids) || ids.some(id => !state.galleriesById.has(id)) || new Set(ids).size !== ids.length) {
      errors.set("gallery_ids", "Select distinct existing galleries.");
    }
  }
  if (state.mode !== "bulk") {
    const sources = state.workMediaSourceConfig?.mediaSourceIds || [];
    if (!sources.includes(resolvedWorkMediaSourceId(state))) errors.set("media_source_id", "Select a configured media source.");
    validateWorkEmbeddedItems(state.draft, {text: (key, fallback, tokens) => t(state, key, fallback, tokens)}).forEach((message, key) => errors.set(key, message));
  }
  return errors;
}

function clearActionMessages(state) {
  state.messageController.clearActionMessages();
}

const REFRESH_TIME_FORMATTER = new Intl.DateTimeFormat("en-GB", {
  timeZone: "Europe/London", year: "numeric", month: "2-digit", day: "2-digit",
  hour: "2-digit", minute: "2-digit", hourCycle: "h23"
});

function formatCatalogueRefreshTime(value) {
  const date = new Date(value);
  if (!Number.isFinite(date.getTime())) return "";
  const parts = Object.fromEntries(REFRESH_TIME_FORMATTER.formatToParts(date).map(part => [part.type, part.value]));
  return `${parts.year}-${parts.month}-${parts.day} ${parts.hour}:${parts.minute}`;
}

function renderCatalogueRefreshStatus(state) {
  const refreshedAt = formatCatalogueRefreshTime(state.refreshStatus?.refreshed_at_utc);
  let text;
  let tone = "";
  if (!state.serverAvailable) text = "Catalogue Refresh is unavailable.";
  else if (state.isBuilding) text = "Refreshing Catalogue readers…";
  else if (!state.refreshStatus) text = "Checking Catalogue reader freshness…";
  else if (state.refreshStatus.status_error) {
    text = state.refreshStatus.status_error;
    tone = "error";
  } else if (state.refreshStatus.error) {
    text = state.refreshStatus.error;
    tone = "error";
  } else if (state.refreshStatus.needed) {
    text = "Catalogue readers need Refresh before Docs Publish.";
    tone = "warn";
  } else {
    text = refreshedAt ? `Working Catalogue readers refreshed at ${refreshedAt}.` : "Working Catalogue readers refreshed.";
  }
  setNodeTextWithState(state.refreshStatusNode, text, tone);
}

function noteCatalogueSaved(state, response) {
  if (response?.refresh_needed) {
    state.refreshStatus = { ok: true, needed: true };
    renderCatalogueRefreshStatus(state);
  }
}

async function runCatalogueRefresh(state) {
  if (!state.serverAvailable || state.isSaving || state.isBuilding || state.isDeleting || state.isEditingDefinition || draftHasChanges(state)) return;
  state.isBuilding = true;
  updateEditorState(state);
  try {
    const response = await requestCatalogueRefresh();
    if (!response.refresh_status || response.refresh_status.needed) throw new Error("Refresh completion was not verified.");
    state.refreshStatus = response.refresh_status;
  } catch (error) {
    state.refreshStatus = { ok: true, needed: true, error: error.message || String(error) };
  } finally {
    state.isBuilding = false;
    updateEditorState(state);
  }
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
    dirtyMessage: state.mode === "new" ? "" : catalogueDirtyWarningText({
      dirty,
      mode: state.mode,
      message: t(state, "dirty_warning", "Unsaved source changes.")
    })
  });
}


function updateEditorState(state) {
  syncPendingAttachmentNames(state);
  const busy = state.isSaving || state.isBuilding || state.isDeleting;
  state.root.dataset.workSaving = String(state.isSaving);
  state.searchNode.disabled = busy;
  if (state.workSearchClearButton) {
    const label = state.mode === "new"
      ? t(state, "cancel_new_work_button", "Cancel new Work")
      : t(state, "clear_search_button", "Clear search");
    state.workSearchClearButton.title = label;
    state.workSearchClearButton.setAttribute("aria-label", label);
    state.workSearchClearButton.disabled = busy;
  }
  state.newButton.disabled = busy;
  if (busy) state.workSearchController?.close();
  state.seriesBrowser?.sync();
  const hasRecord = state.mode === "new" ? true : state.mode === "bulk" ? state.bulkWorkIds.length > 0 : Boolean(state.currentRecord);
  const errors = hasRecord ? validateDraft(state) : new Map();
  state.validationErrors = errors;
  updateFieldMessages(state, errors, workFormOptions(state));
  setModeFieldAvailability(state);
  updateSummary(state);
  setNodeTextWithState(state.buildImpactNode, "");

  const dirty = hasRecord && draftHasChanges(state);
  state.refreshButton.disabled = busy || state.isEditingDefinition || dirty || !state.serverAvailable;
  renderCatalogueRefreshStatus(state);
  if (state.mode === "bulk" && hasRecord) {
    state.messageController.setDefaultMessage(t(state, "bulk_status_loaded", "Loaded {count} work records.", { count: String(state.bulkWorkIds.length) }));
  } else if (state.mode === "single" && hasRecord) {
    state.messageController.setDefaultMessage(t(state, "save_status_loaded", "Loaded work {work_id}.", { work_id: state.currentWorkId }));
  }
  renderEditorMessage(state, { hasRecord, dirty, errors });

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
  if (state.mode === "bulk") return;
  const node = state.fieldNodes.get(fieldKey);
  if (!node) return;
  clearActionMessages(state);
  state.draft[fieldKey] = getFieldNodeValue(node);
  updateEditorState(state);
}

function t(state, key, fallback, tokens = null) {
  return getStudioText(state.config, `catalogue_work_editor.${key}`, fallback, tokens);
}

function workDefinitionOptions(state) {
  return {
    noteCatalogueSaved: (response) => noteCatalogueSaved(state, response),
    refresh: () => {
      applyDraftToInputs(state);
      updateEditorState(state);
    }
  };
}

function workFormOptions(state) {
  return {
    text: (key, fallback, tokens) => t(state, key, fallback, tokens),
    onFieldInput: (fieldKey) => onFieldInput(state, fieldKey),
    onEditDefinition: (kind, id, restoreFocus) => editWorkDefinition(state, {
      ...workDefinitionOptions(state), kind, id, restoreFocus
    }),
    onStateChange: () => {
      clearActionMessages(state);
      updateEditorState(state);
    },
    draftHasChanges: () => draftHasChanges(state),
    getMediaSourceId: () => resolvedWorkMediaSourceId(state),
    loadProjectFolders: (sourceId, query) => readProjectMediaFolders(sourceId, query),
    loadProjectFiles: (request) => readProjectMediaFiles(request),
    onOpenSourceTarget: target => openDraftSourceTarget(state, target)
  };
}

async function openDraftSourceTarget(state, target) {
  if (state.mode === "bulk" || state.isSaving || state.isBuilding || state.isDeleting || state.isOpeningSource || !state.serverAvailable) return;
  state.isOpeningSource = true;
  setModeFieldAvailability(state);
  try {
    await openWorkProjectMedia({
      target,
      media_source_id: resolvedWorkMediaSourceId(state),
      project_folder: state.draft.project_folder,
      project_subfolder: state.draft.project_subfolder,
      project_filename: state.draft.project_filename
    });
  } catch (error) {
    state.messageController.setActionTextWithState(state.statusNode, error.message, "error");
  } finally {
    state.isOpeningSource = false;
    setModeFieldAvailability(state);
  }
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
      for (const workId of workIds) {
        applyWorkRecordMutation(state, { workId, record: recordsById.get(workId), recordHash: recordHashes.get(workId) });
      }
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
    noteCatalogueSaved: (response) => noteCatalogueSaved(state, response),
    offerEmptyGalleryCleanup: (galleryIds) => offerEmptyGalleryCleanup(state, {
      ...workDefinitionOptions(state), galleryIds, restoreFocus: state.saveButton
    })
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
  for (const [button, key, fallback] of [
    [elements.newButton, "new_button", "New"],
    [elements.saveButton, "save_button", "Save"],
    [elements.deleteButton, "delete_button", "Delete"],
    [elements.refreshButton, "refresh_button", "Refresh Catalogue"]
  ]) {
    const label = t(state, key, fallback);
    button.title = label;
    button.setAttribute("aria-label", label);
  }
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
  const [sourcePayload, galleryPayload, , refreshStatus] = await Promise.all([
    readWorkMediaSources(),
    loadStudioServerReadJson("catalogue_galleries", "", { cache: "no-store" }),
    loadCatalogueEditorLookupMaps(state, [
    {
      readKey: "catalogue_lookup_work_search",
      target: state.workSearchById,
      normalizeKey: (record) => normalizeWorkId(record.work_id),
      afterItems: (items) => {
        state.nextSuggestedWorkId = suggestNextWorkId(items);
      }
    },
    {
      readKey: "catalogue_lookup_series_search",
      target: state.seriesById,
      normalizeKey: (record) => normalizeSeriesId(record.series_id)
    }
    ]),
    readCatalogueRefreshStatus().catch(error => ({ ok: false, needed: true, status_error: error.message || String(error) }))
  ]);
  if (!galleryPayload.galleries || typeof galleryPayload.galleries !== "object" || Array.isArray(galleryPayload.galleries)) {
    throw new Error("Gallery lookup is unavailable.");
  }
  state.galleriesById = new Map(Object.entries(galleryPayload.galleries));
  state.refreshStatus = refreshStatus;
  const limits = sourcePayload.attachment_limits;
  if (!limits || !Number.isSafeInteger(limits.total_bytes) || limits.total_bytes < 1
    || !Number.isSafeInteger(limits.metadata_bytes) || limits.metadata_bytes < 1) {
    throw new Error("Work attachment limits are unavailable.");
  }
  state.attachmentLimits = limits;
  applyWorkMediaSourceConfig(state, sourcePayload);
}

function markWorkEditorLoaded(state, elements) {
  revealCatalogueEditorRoute(state, {
    loadingNode: elements.loadingNode,
    routeState: WORK_ROUTE_STATE
  });
}

async function init() {
  const refreshControls = document.getElementById("catalogueWorkRefreshControls");
  const headerRow = refreshControls?.closest(".studio")?.querySelector(":scope > .studio__headerRow");
  if (!headerRow || !refreshControls) return;
  headerRow.appendChild(refreshControls);
  const elements = collectWorkEditorElements();
  if (!elements) return;

  initializeWorkRouteState(elements.root);
  const state = createWorkEditorState(elements);
  state.layout = createWorkEditorLayout(elements, change => {
    if (state.seriesBrowser) state.seriesBrowser.preserveScrollAnchor(change);
    else change();
  });
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
      onEditDefinition: workFormOptions(state).onEditDefinition,
      openWorks: workIds => openWorkSelection(state, workIds.join(","), workSelectionOptions(state)),
      clearWork: () => setEmptySearchMode(state, workRouteStateOptions(state))
    });
    bindWorkEditorEvents(state, {
      bindSelectionControls: () => bindWorkSelectionControls(state, workSelectionOptions(state)),
      renderEditorMessage: () => renderEditorMessage(state),
      openEmbeddedEntryModal: (kind, index) => openEmbeddedEntryModal(state, kind, index),
      deleteEmbeddedEntry: (kind, index) => deleteEmbeddedEntry(state, kind, index),
      setNewWorkMode: () => setNewWorkMode(state, workRouteStateOptions(state)),
      saveCurrentWork: () => saveCurrentWork(state, workActionOptions(state)),
      refreshCatalogue: () => runCatalogueRefresh(state),
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
