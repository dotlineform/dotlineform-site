import {
  getStudioText
} from "./studio-config.js";
import {
  configureCatalogueEditorRouteRuntime,
  initializeCatalogueEditorRoute,
  loadCatalogueEditorLookupMaps,
  markCatalogueEditorRouteReady,
  revealCatalogueEditorRoute,
  setCatalogueEditorTextWithState as setTextWithState,
  syncCatalogueEditorRouteBusyState
} from "./catalogue-editor-route-boot.js";
import {
  previewCatalogueMoment
} from "./catalogue-editor-service-client.js";
import {
  computeRecordHash,
  recordsEqual
} from "./catalogue-editor-records.js";
import {
  catalogueDeleteDisabled,
  catalogueDirtyWarningText
} from "./catalogue-editor-dirty-state.js";
import {
  normalizeMomentId,
  normalizeMomentRecord,
  normalizeText,
  readMomentDraft,
  validateMomentDraft
} from "./catalogue-moment-fields.js";
import {
  applyInitialMomentRouteSelection,
  bindMomentSelectionControls,
  setMomentSelectionPopupVisibility
} from "./catalogue-moment-selection.js";
import {
  applyMomentImport,
  clearImportPreview,
  currentImportMomentFile,
  previewMomentImport,
  readRequestedImportFile,
  updateImportState,
  writeRequestedImportFile
} from "./catalogue-moment-import.js";
import {
  buildSaveModeText
} from "./tag-studio-save.js";
import {
  applyMomentRecordToInputs,
  clearMomentFieldMessages,
  clearMomentReadonly,
  getMomentFieldNodeValue,
  renderMomentEditorFields,
  renderMomentReadonlyFields,
  updateMomentFieldMessages
} from "./catalogue-moment-form.js";
import {
  renderMomentBuildImpact,
  renderMomentReadiness,
  renderMomentSummary
} from "./catalogue-moment-sections.js";
import {
  applyPublicationChange,
  currentMomentIsDraft,
  currentMomentIsPublished,
  deleteCurrentMoment,
  importMomentProse,
  refreshBuildPreview as refreshMomentActionBuildPreview,
  refreshMomentMedia,
  saveCurrentMoment
} from "./catalogue-moment-actions.js";
import {
  bindMomentEditorEvents
} from "./catalogue-moment-editor-events.js";
import {
  MOMENT_ROUTE_STATE,
  collectMomentEditorElements,
  createMomentEditorState
} from "./catalogue-moment-editor-state.js";

function getFieldNodeValue(node) {
  return getMomentFieldNodeValue(node);
}

function syncRouteBusyState(state) {
  syncCatalogueEditorRouteBusyState(state, MOMENT_ROUTE_STATE);
}

function markRouteReady(state, ready) {
  markCatalogueEditorRouteReady(state, ready, MOMENT_ROUTE_STATE);
}

function t(state, key, fallback, tokens = null) {
  return getStudioText(state.config, `catalogue_moment_editor.${key}`, fallback, tokens);
}

function buildImportContext(state) {
  return {
    text: (key, fallback, tokens) => t(state, key, fallback, tokens),
    setTextWithState,
    syncRouteBusyState: () => syncRouteBusyState(state),
    completeImport: ({ momentId, record }) => completeMomentImport(state, momentId, record)
  };
}

function buildSelectionContext(state) {
  return {
    text: (key, fallback, tokens) => t(state, key, fallback, tokens),
    setTextWithState,
    openMoment: (momentId, options = {}) => openMoment(state, momentId, options),
    enterImportMode: (momentFile) => enterImportMode(state, momentFile),
    currentImportFile: () => currentImportMomentFile(state),
    previewImport: () => previewMomentImport(state, buildImportContext(state)),
    setEmptyMode: () => {
      state.emptyNode.hidden = false;
      state.emptyNode.textContent = t(state, "missing_moment_param", "Search for a moment by id or title.");
      setTextWithState(state.statusNode, t(state, "missing_moment_param", "Search for a moment by id or title."));
    }
  };
}

function buildActionContext(state) {
  return {
    text: (key, fallback, tokens) => t(state, key, fallback, tokens),
    setTextWithState,
    getFieldNodeValue,
    readDraft: () => readDraft(state),
    validateDraft: () => validateDraft(state),
    draftHasChanges: () => draftHasChanges(state),
    updateEditorState: () => updateDirtyState(state),
    previewMoment: (momentId) => previewMoment(state, momentId),
    renderSummary: () => renderSummary(state),
    renderBuildImpact: () => renderBuildImpact(state),
    fillForm: (record) => fillForm(state, record)
  };
}

function buildSectionContext(state) {
  return {
    text: (key, fallback, tokens) => t(state, key, fallback, tokens),
    draftHasChanges: () => draftHasChanges(state),
    currentMomentIsPublished: () => currentMomentIsPublished(state, buildActionContext(state))
  };
}

function readDraft(state) {
  return readMomentDraft(state, { getFieldNodeValue });
}

function draftHasChanges(state) {
  if (!state.currentRecord) return false;
  return !recordsEqual(readDraft(state), state.currentRecord);
}

function setPopupVisibility(state, visible) {
  setMomentSelectionPopupVisibility(state, visible);
}

function fillForm(state, record) {
  applyMomentRecordToInputs(state, record);
}

function clearFieldMessages(state) {
  clearMomentFieldMessages(state, { setTextWithState });
}

function validateDraft(state) {
  const draft = readDraft(state);
  const errors = validateMomentDraft(draft, {
    t: (key, fallback, tokens) => t(state, key, fallback, tokens)
  });
  updateMomentFieldMessages(state, errors, { setTextWithState });
  return { valid: !errors.size, draft };
}

function renderReadiness(state) {
  renderMomentReadiness(state, buildSectionContext(state));
}

function renderSummary(state) {
  renderMomentSummary(state, buildSectionContext(state));
}

function setEditModeChrome(state) {
  state.isImportMode = false;
  state.saveButton.hidden = false;
  state.publicationButton.hidden = false;
  state.deleteButton.hidden = false;
  state.importPreviewButton.hidden = true;
  state.importApplyButton.hidden = true;
  state.importSourceNode.hidden = true;
  state.readonlyNode.hidden = false;
  state.runtimeStateNode.hidden = false;
  state.buildImpactNode.hidden = false;
  state.sideHeadingNode.textContent = t(state, "side_heading_current", "current record");
  state.importSourceSummaryNode.textContent = "";
  state.importImageGuidanceNode.textContent = "";
}

function enterImportMode(state, momentFile = "") {
  state.isImportMode = true;
  state.currentMomentId = "";
  state.currentRecord = null;
  state.expectedRecordHash = "";
  state.preview = null;
  state.previewReadiness = null;
  state.buildPreview = null;
  state.needsBuild = false;
  state.searchNode.value = "";
  setPopupVisibility(state, false);
  fillForm(state, {
    moment_id: "",
    title: "",
    status: "draft",
    date: "",
    date_display: "",
    published_date: "",
    source_image_file: "",
    image_alt: ""
  });
  clearMomentReadonly(state);
  state.saveButton.hidden = true;
  state.publicationButton.hidden = true;
  state.deleteButton.hidden = true;
  state.importPreviewButton.hidden = false;
  state.importApplyButton.hidden = false;
  state.importSourceNode.hidden = false;
  state.readonlyNode.hidden = true;
  state.runtimeStateNode.hidden = true;
  state.buildImpactNode.hidden = true;
  state.sideHeadingNode.textContent = t(state, "side_heading_import", "import preview");
  if (normalizeText(momentFile)) state.importFileNode.value = momentFile;
  setTextWithState(state.contextNode, t(state, "import_context_hint", "Import a staged moment markdown file as draft source, then review and publish it from this editor."));
  setTextWithState(state.statusNode, t(state, "import_mode_loaded", "Preview the staged moment file below."));
  setTextWithState(state.warningNode, "");
  setTextWithState(state.resultNode, "");
  writeRequestedImportFile(state.importFileNode.value);
  clearFieldMessages(state);
  clearImportPreview(state, buildImportContext(state));
  updateDirtyState(state);
}

function upsertMomentRow(state, momentId, record) {
  const normalized = normalizeMomentRecord(momentId, record);
  state.moments.set(normalized.moment_id, normalized);
  const row = state.momentRows.find((item) => item.moment_id === normalized.moment_id);
  const nextRow = {
    ...normalized,
    search: `${normalized.moment_id} ${normalizeText(normalized.title).toLowerCase()}`
  };
  if (row) Object.assign(row, nextRow);
  else state.momentRows.push(nextRow);
  state.momentRows.sort((a, b) => a.moment_id.localeCompare(b.moment_id));
}

async function completeMomentImport(state, momentId, record) {
  upsertMomentRow(state, momentId, record);
  state.searchNode.value = momentId;
  await openMoment(state, momentId);
}

function updatePublicationControls(state, { dirty, validation }) {
  const hasRecord = Boolean(state.currentRecord);
  const actionContext = buildActionContext(state);
  const canPublish = hasRecord && currentMomentIsDraft(state, actionContext);
  const canUnpublish = hasRecord && currentMomentIsPublished(state, actionContext);
  const label = canUnpublish
    ? t(state, "unpublish_button", "Unpublish")
    : t(state, "publish_button", "Publish");
  state.publicationButton.textContent = label;
  state.publicationButton.hidden = !(canPublish || canUnpublish);
  state.publicationButton.disabled = !(canPublish || canUnpublish)
    || (canPublish && dirty)
    || (canPublish && validation && !validation.valid)
    || state.isSaving
    || state.isBuilding
    || state.isDeleting
    || !state.serverAvailable;
}

function updateDirtyState(state) {
  const dirty = draftHasChanges(state);
  const validation = state.currentRecord ? validateDraft(state) : { valid: true, draft: null };
  if (!state.currentRecord) clearFieldMessages(state);
  setTextWithState(state.warningNode, catalogueDirtyWarningText({
    dirty,
    mode: "single",
    message: t(state, "dirty_warning", "Unsaved source changes.")
  }), dirty ? "warning" : "");
  state.saveButton.disabled = !state.serverAvailable || state.isSaving || state.isDeleting || !state.currentRecord;
  state.deleteButton.disabled = catalogueDeleteDisabled({
    hasRecord: Boolean(state.currentRecord),
    isSaving: state.isSaving,
    isBuilding: state.isBuilding,
    isDeleting: state.isDeleting,
    serverAvailable: state.serverAvailable
  });
  updatePublicationControls(state, { dirty, validation });
  renderReadiness(state);
  updateImportState(state, buildImportContext(state));
}

function onFieldInput(state) {
  if (state.isImportMode) {
    clearImportPreview(state, buildImportContext(state));
    updateDirtyState(state);
    return;
  }
  validateDraft(state);
  updateDirtyState(state);
}

async function previewMoment(state, momentId) {
  if (!state.serverAvailable) return;
  try {
    const payload = await previewCatalogueMoment({ moment_id: momentId });
    state.currentRecord = payload.record || state.currentRecord;
    state.expectedRecordHash = payload.record_hash || state.expectedRecordHash;
    state.preview = payload.preview || null;
    state.previewReadiness = payload.readiness || null;
    state.buildPreview = payload.build || null;
    renderBuildImpact(state);
  } catch (error) {
    console.warn("catalogue_moment_editor: preview failed", error);
    state.serverAvailable = false;
    setTextWithState(state.statusNode, t(state, "save_mode_unavailable_hint", "Local catalogue server unavailable. Save is disabled."), "warning");
    state.saveModeNode.textContent = buildSaveModeText(
      state.config,
      "offline",
      (cfg, key, fallback, tokens) => getStudioText(cfg, `catalogue_moment_editor.${key}`, fallback, tokens)
    );
    updateDirtyState(state);
  }
}

async function openMoment(state, momentId, options = {}) {
  const normalizedId = normalizeMomentId(momentId);
  const record = state.moments.get(normalizedId);
  if (!record) {
    setTextWithState(state.statusNode, t(state, "unknown_moment_error", "Unknown moment id: {moment_id}.", { moment_id: normalizedId }), "error");
    return;
  }
  setEditModeChrome(state);
  clearImportPreview(state, buildImportContext(state));
  state.currentMomentId = normalizedId;
  state.currentRecord = normalizeMomentRecord(normalizedId, record);
  state.expectedRecordHash = await computeRecordHash(state.currentRecord);
  state.preview = null;
  state.previewReadiness = null;
  state.buildPreview = null;
  state.needsBuild = false;
  fillForm(state, state.currentRecord);
  setTextWithState(state.contextNode, t(state, "context_loaded", "Editing source metadata for moment {moment_id}.", { moment_id: normalizedId }));
  setTextWithState(state.statusNode, t(state, "save_status_loaded", "Loaded moment {moment_id}.", { moment_id: normalizedId }), "success");
  setTextWithState(state.resultNode, "");
  if (!options.skipUrl) {
    const url = new URL(window.location.href);
    url.searchParams.set("moment", normalizedId);
    url.searchParams.delete("file");
    window.history.replaceState({}, "", url.toString());
  }
  await previewMoment(state, normalizedId);
  fillForm(state, state.currentRecord);
  validateDraft(state);
  renderSummary(state);
  updateDirtyState(state);
}

function renderBuildImpact(state) {
  renderMomentBuildImpact(state, buildSectionContext(state));
}

function buildMomentRows(payload) {
  const moments = payload && payload.moments && typeof payload.moments === "object" ? payload.moments : {};
  return Object.entries(moments).map(([momentId, record]) => {
    const normalized = normalizeMomentRecord(momentId, record);
    return {
      ...normalized,
      search: `${normalized.moment_id} ${normalizeText(normalized.title).toLowerCase()}`
    };
  }).sort((a, b) => a.moment_id.localeCompare(b.moment_id));
}

function bindEvents(state) {
  bindMomentEditorEvents(state, {
    bindSelectionControls: () => bindMomentSelectionControls(state, buildSelectionContext(state)),
    enterImportMode: () => enterImportMode(state),
    saveCurrentMoment: () => saveCurrentMoment(state, buildActionContext(state)),
    applyPublicationChange: () => applyPublicationChange(state, buildActionContext(state)),
    deleteCurrentMoment: () => deleteCurrentMoment(state, buildActionContext(state)),
    updateImportFile: (value) => {
      writeRequestedImportFile(value);
      setTextWithState(state.importWarningNode, "");
      setTextWithState(state.importResultNode, "");
      clearImportPreview(state, buildImportContext(state));
    },
    previewMomentImport: () => previewMomentImport(state, buildImportContext(state)),
    applyMomentImport: () => applyMomentImport(state, buildImportContext(state)),
    refreshMomentMedia: () => refreshMomentMedia(state, buildActionContext(state)),
    importMomentProse: () => importMomentProse(state, buildActionContext(state))
  });
}

async function init() {
  const elements = collectMomentEditorElements();
  if (!elements) return;
  const {
    root,
    loadingNode,
    emptyNode,
    searchNode,
    popupNode,
    popupListNode,
    openButton,
    newButton,
    saveModeNode,
    contextNode,
    statusNode,
    warningNode,
    resultNode,
    saveButton,
    publicationButton,
    deleteButton,
    fieldsNode,
    readonlyNode,
    sideHeadingNode,
    summaryNode,
    readinessNode,
    runtimeStateNode,
    buildImpactNode,
    importSourceNode,
    importFileLabelNode,
    importFileNode,
    importFileDescriptionNode,
    importSourceSummaryNode,
    importImageGuidanceNode,
    importPreviewButton,
    importApplyButton
  } = elements;
  const state = createMomentEditorState(elements);
  initializeCatalogueEditorRoute(root, "catalogue-moment");

  try {
    await configureCatalogueEditorRouteRuntime(state, {
      namespace: "catalogue_moment_editor",
      saveModeNode: state.saveModeNode,
      applyText: () => {
        state.searchNode.placeholder = t(state, "search_placeholder", "find moment by id or title");
        state.openButton.textContent = t(state, "open_button", "Open");
        state.newButton.textContent = t(state, "new_button", "New");
        state.saveButton.textContent = t(state, "save_button", "Save");
        state.publicationButton.textContent = t(state, "publish_button", "Publish");
        state.deleteButton.textContent = t(state, "delete_button", "Delete");
        state.importFileLabelNode.textContent = t(state, "import_file_label", "moment file");
        state.importFileNode.placeholder = t(state, "import_file_placeholder", "keys.md");
        state.importPreviewButton.textContent = t(state, "import_preview_button", "Preview");
        state.importApplyButton.textContent = t(state, "import_button", "Import");
        state.importFileDescriptionNode.textContent = t(state, "import_file_description", "filename only; the source file is resolved from var/docs/catalogue/import-staging/moments/");

        renderMomentEditorFields(state.fieldsNode, state, {
          onFieldInput: () => onFieldInput(state)
        });
        renderMomentReadonlyFields(state.readonlyNode, state);
        bindEvents(state);
      }
    });
    state.importFileNode.value = readRequestedImportFile();

    if (!state.serverAvailable) {
      setTextWithState(state.statusNode, t(state, "save_mode_unavailable_hint", "Local catalogue server unavailable. Save is disabled."), "warning");
      setTextWithState(state.importStatusNode, t(state, "import_save_mode_unavailable_hint", "Local catalogue server unavailable. Moment import is disabled."), "warning");
      updateDirtyState(state);
      updateImportState(state, buildImportContext(state));
      revealCatalogueEditorRoute(state, {
        loadingNode,
        routeState: MOMENT_ROUTE_STATE
      });
      return;
    }

    await loadCatalogueEditorLookupMaps(state, [
      {
        configKey: "catalogue_moments",
        itemsFromPayload: (payload) => buildMomentRows(payload),
        afterItems: (items) => {
          state.momentRows = items;
          state.moments = new Map(state.momentRows.map((row) => [row.moment_id, row]));
        }
      }
    ]);

    loadingNode.hidden = true;
    root.hidden = false;
    await applyInitialMomentRouteSelection(state, buildSelectionContext(state));
    updateDirtyState(state);
    updateImportState(state, buildImportContext(state));
    await refreshMomentActionBuildPreview(state, buildActionContext(state)).catch((error) => console.warn("catalogue_moment_editor: initial build preview failed", error));
    markRouteReady(state, true);
  } catch (error) {
    console.warn("catalogue_moment_editor: init failed", error);
    loadingNode.hidden = true;
    emptyNode.hidden = false;
    emptyNode.textContent = t(state, "load_failed_error", "Failed to load catalogue source data for the moment editor.");
  }
}

init();
