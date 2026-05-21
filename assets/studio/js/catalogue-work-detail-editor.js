import {
  getStudioText
} from "./studio-config.js";
import { loadStudioLookupRecordJson } from "./studio-data.js";
import {
  collectRequiredElements,
  configureCatalogueEditorRouteRuntime,
  initializeCatalogueEditorRoute,
  loadCatalogueEditorLookupMaps,
  revealCatalogueEditorRoute,
  setCatalogueEditorTextWithState as setTextWithState,
  showCatalogueEditorInitError,
  syncCatalogueEditorRouteBusyState
} from "./catalogue-editor-route-boot.js";
import {
  catalogueDeleteDisabled,
  catalogueDirtyWarningText,
  catalogueDraftHasChanges,
  catalogueSaveDisabled
} from "./catalogue-editor-dirty-state.js";
import {
  loadCatalogueMediaConfig
} from "./catalogue-media-preview.js";
import {
  WORK_DETAIL_EDITABLE_FIELDS as EDITABLE_FIELDS,
  WORK_DETAIL_STATUS_OPTIONS as STATUS_OPTIONS,
  buildWorkDetailDraftFromRecord,
  canonicalizeWorkDetailScalar as canonicalizeScalar,
  normalizeText,
  normalizeWorkId,
  suggestNextDetailId,
  validateCreateWorkDetailDraft
} from "./catalogue-work-detail-fields.js";
import {
  deleteCurrentDetail,
  refreshWorkDetailBuildPreview,
  refreshWorkDetailMedia,
  saveCurrentDetail,
  applyWorkDetailPublicationChange,
  updateWorkDetailPublishControls
} from "./catalogue-work-detail-actions.js";
import {
  WORK_DETAIL_FORM_FIELDS as FORM_FIELDS,
  applyWorkDetailDraftToInputs,
  applyWorkDetailFieldLabels,
  applyWorkDetailReadonly,
  getWorkDetailFieldNodeValue,
  renderWorkDetailEditorFields,
  renderWorkDetailReadonlyFields,
  setWorkDetailFieldNodeValue,
  setWorkDetailModeFieldAvailability,
  setWorkDetailReadonlyValues,
  updateWorkDetailFieldMessages
} from "./catalogue-work-detail-form.js";
import {
  formatWorkDetailSelectionList,
  renderWorkDetailCurrentPreview,
  renderWorkDetailReadiness,
  updateWorkDetailSummary
} from "./catalogue-work-detail-sections.js";
import {
  applyInitialWorkDetailRouteSelection,
  bindWorkDetailSelectionControls,
  openWorkDetailByUid,
  setWorkDetailSelectionPopupVisibility
} from "./catalogue-work-detail-selection.js";

function buildBulkDraftFromRecords(records) {
  const drafts = records.map((record) => buildWorkDetailDraftFromRecord(record));
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

function routeModeForState(state) {
  if (state.mode === "new") return "new";
  if (state.mode === "bulk") return "bulk";
  if (state.currentRecord) return "single";
  return "empty";
}

function routeRecordLoadedForState(state) {
  if (state.mode === "bulk") return state.bulkDetailUids.length > 0;
  if (state.mode === "single") return Boolean(state.currentRecord);
  return false;
}

function syncRouteBusyState(state) {
  syncCatalogueEditorRouteBusyState(state, {
    route: "catalogue-work-detail",
    mode: routeModeForState,
    recordLoaded: routeRecordLoadedForState
  });
}

function buildDetailSearchRecord(detailUid, record) {
  return {
    detail_uid: detailUid,
    work_id: normalizeText(record && record.work_id),
    detail_id: normalizeText(record && record.detail_id),
    title: normalizeText(record && record.title),
    section_id: normalizeText(record && record.section_id),
    section_title: normalizeText(record && record.section_title),
    sort_order: normalizeText(record && record.sort_order),
    details_subfolder: normalizeText(record && record.details_subfolder),
    project_filename: normalizeText(record && record.project_filename),
    status: normalizeText(record && record.status)
  };
}

async function loadDetailLookupRecord(state, detailUid) {
  return loadStudioLookupRecordJson(state.config, "catalogue_lookup_work_detail_base", detailUid, {
    cache: "no-store",
    catalogueServerAvailable: state.serverAvailable
  });
}

function syncUrl(detailValue, options = {}) {
  const url = new URL(window.location.href);
  if (normalizeText(options.mode).toLowerCase() === "new") {
    url.searchParams.delete("detail");
    url.searchParams.set("mode", "new");
    const workId = normalizeWorkId(options.workId);
    if (workId) url.searchParams.set("work", workId);
    else url.searchParams.delete("work");
  } else if (detailValue) {
    url.searchParams.delete("mode");
    url.searchParams.delete("work");
    url.searchParams.set("detail", detailValue);
  } else {
    url.searchParams.delete("mode");
    url.searchParams.delete("work");
    url.searchParams.delete("detail");
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
    canonicalizeScalar
  });
}

function validateDraft(state) {
  if (state.mode === "new") {
    return validateCreateWorkDetailDraft(state.draft, {
      workById: state.workSearchById,
      detailByUid: state.detailSearchByUid,
      requirePublishedParent: true,
      t: (key, fallback, tokens = null) => t(state, key, fallback, tokens)
    });
  }
  const errors = new Map();
  const rawSortOrder = normalizeText(state.draft.sort_order);
  if (rawSortOrder && !/^\d+$/.test(rawSortOrder)) {
    if (state.mode !== "bulk" || state.bulkTouchedFields.has("sort_order")) {
      errors.set("sort_order", t(state, "field_invalid_sort_order", "Use a whole number or leave blank."));
    }
  }
  if (state.mode === "bulk" && state.bulkTouchedFields.has("section_title") && !normalizeText(state.draft.section_title)) {
    errors.set("section_title", t(state, "field_required_section_title", "Enter a section title."));
  }
  if (state.mode !== "bulk" && !normalizeText(state.draft.section_title)) {
    errors.set("section_title", t(state, "field_required_section_title", "Enter a section title."));
  }
  if (state.mode === "bulk" && !state.bulkTouchedFields.has("status")) return errors;
  const status = normalizeText(state.draft.status).toLowerCase();
  if (!STATUS_OPTIONS.has(status)) {
    errors.set("status", t(state, "field_invalid_status", "Use blank, draft, or published."));
  }
  return errors;
}

function setLoadedRecord(state, detailUid, record, options = {}) {
  state.mode = "single";
  state.currentDetailUid = detailUid;
  state.currentWorkId = normalizeWorkId(record && record.work_id);
  state.currentRecord = record;
  state.currentLookup = options.lookup || state.currentLookup;
  state.currentRecordHash = normalizeText(options.recordHash || state.currentRecordHash);
  state.bulkDetailUids = [];
  state.bulkRecords = new Map();
  state.bulkRecordHashes = new Map();
  state.bulkMixedFields = new Set();
  state.bulkTouchedFields = new Set();
  state.bulkBuildTargets = [];
  state.baselineDraft = buildWorkDetailDraftFromRecord(record);
  state.draft = { ...state.baselineDraft };
  applyWorkDetailDraftToInputs(state);
  applyWorkDetailReadonly(state);
  syncUrl(detailUid);
  setTextWithState(state.contextNode, t(state, "context_loaded", "Editing source metadata for detail {detail_uid}.", { detail_uid: detailUid }));
  setTextWithState(state.statusNode, t(state, "save_status_loaded", "Loaded detail {detail_uid}.", { detail_uid: detailUid }));
  setTextWithState(state.warningNode, "");
  if (!options.keepResult) setTextWithState(state.resultNode, "");
  updateEditorState(state);
}

function setNewDetailMode(state, workId, options = {}) {
  const normalizedWorkId = normalizeWorkId(workId);
  state.mode = "new";
  state.currentDetailUid = "";
  state.currentWorkId = normalizedWorkId;
  state.currentRecord = null;
  state.currentLookup = null;
  state.currentRecordHash = "";
  state.bulkDetailUids = [];
  state.bulkRecords = new Map();
  state.bulkRecordHashes = new Map();
  state.bulkMixedFields = new Set();
  state.bulkTouchedFields = new Set();
  state.bulkBuildTargets = [];
  state.baselineDraft = {};
  state.draft = {};
  FORM_FIELDS.forEach((field) => {
    state.draft[field.key] = "";
  });
  state.draft.work_id = normalizedWorkId;
  state.draft.detail_id = suggestNextDetailId(state.detailSearchByUid, normalizedWorkId);
  state.draft.status = "draft";
  state.rebuildPending = false;
  state.buildPreview = null;
  applyWorkDetailDraftToInputs(state);
  setWorkDetailReadonlyValues(state, (field) => field.key === "work_id" ? normalizedWorkId : "");
  state.searchNode.value = "";
  setWorkDetailSelectionPopupVisibility(state, false);
  syncUrl("", { mode: "new", workId: normalizedWorkId });
  if (!normalizedWorkId) {
    setTextWithState(state.contextNode, t(state, "new_context_parent_missing", "Open new detail mode from a parent work editor or provide a work id."));
  } else if (!state.workSearchById.has(normalizedWorkId)) {
    setTextWithState(state.contextNode, t(state, "new_context_parent_unknown", "Cannot create a detail because parent work {work_id} was not found.", { work_id: normalizedWorkId }), "error");
  } else if (normalizeText(state.workSearchById.get(normalizedWorkId) && state.workSearchById.get(normalizedWorkId).status).toLowerCase() !== "published") {
    setTextWithState(state.contextNode, t(state, "new_context_parent_unpublished", "Publish work {work_id} before adding work details.", { work_id: normalizedWorkId }), "error");
  } else {
    setTextWithState(state.contextNode, t(state, "new_context_loaded", "Creating a draft detail under work {work_id}.", { work_id: normalizedWorkId }));
  }
  setTextWithState(state.statusNode, "");
  setTextWithState(state.warningNode, "");
  if (!options.keepResult) setTextWithState(state.resultNode, "");
  updateEditorState(state);
}

function setLoadedBulkDetails(state, detailUids, recordsById, recordHashes, options = {}) {
  state.mode = "bulk";
  state.currentDetailUid = "";
  state.currentWorkId = "";
  state.currentRecord = null;
  state.currentLookup = null;
  state.currentRecordHash = "";
  state.bulkDetailUids = detailUids.slice();
  state.bulkRecords = new Map(recordsById);
  state.bulkRecordHashes = new Map(recordHashes);
  state.bulkBuildTargets = Array.isArray(options.buildTargets) ? options.buildTargets.slice() : [];
  const records = detailUids.map((detailUid) => recordsById.get(detailUid)).filter(Boolean);
  const bulkDraft = buildBulkDraftFromRecords(records);
  state.baselineDraft = { ...bulkDraft.draft };
  state.draft = { ...bulkDraft.draft };
  state.bulkMixedFields = bulkDraft.mixedFields;
  state.bulkTouchedFields = new Set();
  applyWorkDetailDraftToInputs(state);
  setWorkDetailReadonlyValues(state, "");
  syncUrl(detailUids.join(","));
  setTextWithState(
    state.contextNode,
    t(state, "bulk_context_loaded", "Bulk editing {count} detail records: {detail_ids}.", {
      count: String(detailUids.length),
      detail_ids: formatWorkDetailSelectionList(detailUids)
    })
  );
  setTextWithState(
    state.statusNode,
    t(state, "bulk_status_loaded", "Loaded {count} detail records.", { count: String(detailUids.length) })
  );
  setTextWithState(state.warningNode, "");
  if (!options.keepResult) setTextWithState(state.resultNode, "");
  updateEditorState(state);
}

function updateEditorState(state) {
  const hasRecord = state.mode === "new" ? true : state.mode === "bulk" ? state.bulkDetailUids.length > 0 : Boolean(state.currentRecord);
  const errors = hasRecord ? validateDraft(state) : new Map();
  state.validationErrors = errors;
  updateWorkDetailFieldMessages(state, errors, buildWorkDetailFormContext(state));
  setWorkDetailModeFieldAvailability(state);
  updateSummary(state);
  if (!hasRecord) {
    setTextWithState(state.buildImpactNode, "");
  } else if (state.mode === "bulk") {
    const previewTargets = state.rebuildPending && state.bulkBuildTargets.length
      ? state.bulkBuildTargets
      : Array.from(new Set(state.bulkDetailUids.map((detailUid) => {
        const record = state.bulkRecords.get(detailUid);
        return normalizeWorkId(record && record.work_id);
      }).filter(Boolean)));
    setTextWithState(
      state.buildImpactNode,
      t(state, "bulk_build_preview", "Build preview: {count} parent work scopes will be rebuilt.", {
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
    const firstError = errors.size ? Array.from(errors.values()).find(Boolean) : "";
    setTextWithState(
      state.statusNode,
      firstError || (state.serverAvailable ? "" : t(state, "create_mode_unavailable_hint", "Local catalogue server unavailable. Create is disabled.")),
      firstError ? "error" : state.serverAvailable ? "" : "warn"
    );
  } else if (!dirty && !errors.size && !state.resultNode.textContent && hasRecord) {
    setTextWithState(
      state.statusNode,
      state.mode === "bulk"
        ? t(state, "bulk_status_loaded", "Loaded {count} detail records.", { count: String(state.bulkDetailUids.length) })
        : t(state, "save_status_loaded", "Loaded detail {detail_uid}.", { detail_uid: state.currentDetailUid })
    );
  }

  state.searchNode.disabled = state.mode === "new";
  state.openButton.disabled = state.mode === "new";
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
  updateWorkDetailPublishControls(state, buildWorkDetailActionContext(state), { hasRecord, dirty, errors });
  renderReadiness(state);
  syncRouteBusyState(state);
}

function onFieldInput(state, fieldKey) {
  const node = state.fieldNodes.get(fieldKey);
  if (!node) return;
  if (state.mode === "new" && fieldKey === "status") {
    state.draft.status = "draft";
    setWorkDetailFieldNodeValue(node, "draft");
    updateEditorState(state);
    return;
  }
  state.draft[fieldKey] = getWorkDetailFieldNodeValue(node);
  if (state.mode === "bulk") {
    state.bulkTouchedFields.add(fieldKey);
  }
  updateEditorState(state);
}

function t(state, key, fallback, tokens = null) {
  return getStudioText(state.config, `catalogue_work_detail_editor.${key}`, fallback, tokens);
}

function buildWorkDetailSectionContext(state) {
  return {
    text: (key, fallback, tokens = null) => t(state, key, fallback, tokens),
    setTextWithState,
    draftHasChanges: () => draftHasChanges(state)
  };
}

function renderCurrentPreview(state) {
  renderWorkDetailCurrentPreview(state, buildWorkDetailSectionContext(state));
}

function renderReadiness(state) {
  renderWorkDetailReadiness(state, buildWorkDetailSectionContext(state));
}

function updateSummary(state) {
  updateWorkDetailSummary(state, buildWorkDetailSectionContext(state));
}

function buildWorkDetailFormContext(state) {
  return {
    text: (key, fallback, tokens = null) => t(state, key, fallback, tokens),
    onFieldInput: (fieldKey) => onFieldInput(state, fieldKey)
  };
}

function buildWorkDetailActionContext(state) {
  return {
    text: (key, fallback, tokens = null) => t(state, key, fallback, tokens),
    setTextWithState,
    draftHasChanges: () => draftHasChanges(state),
    validateDraft: () => validateDraft(state),
    updateFieldMessages: (errors) => updateWorkDetailFieldMessages(state, errors, buildWorkDetailFormContext(state)),
    updateEditorState: () => updateEditorState(state),
    syncRouteBusyState: () => syncRouteBusyState(state),
    renderCurrentPreview: () => renderCurrentPreview(state),
    renderReadiness: () => renderReadiness(state),
    setLoadedBulkDetails: (detailUids, recordsById, recordHashes, options = {}) => {
      setLoadedBulkDetails(state, detailUids, recordsById, recordHashes, options);
    },
    setLoadedRecord: (detailUid, record, options = {}) => {
      setLoadedRecord(state, detailUid, record, options);
    },
    buildDetailSearchRecord,
    loadDetailLookupRecord: (detailUid) => loadDetailLookupRecord(state, detailUid),
    openDetailByUid: (detailUid) => openWorkDetailByUid(state, detailUid, buildWorkDetailSelectionContext(state))
  };
}

function refreshBuildPreview(state) {
  return refreshWorkDetailBuildPreview(state, buildWorkDetailActionContext(state));
}

function buildWorkDetailSelectionContext(state) {
  return {
    text: (key, fallback, tokens = null) => t(state, key, fallback, tokens),
    loadDetailLookupRecord: (detailUid) => loadDetailLookupRecord(state, detailUid),
    setLoadedBulkDetails: (detailUids, recordsById, recordHashes, options = {}) => {
      setLoadedBulkDetails(state, detailUids, recordsById, recordHashes, options);
    },
    setLoadedRecord: (detailUid, record, options = {}) => {
      setLoadedRecord(state, detailUid, record, options);
    },
    setNewDetailMode: (workId, options = {}) => {
      setNewDetailMode(state, workId, options);
    },
    refreshBuildPreview: () => refreshBuildPreview(state),
    setTextWithState,
    updateSummary: () => updateSummary(state),
    updateEditorState: () => updateEditorState(state)
  };
}

async function init() {
  const elements = collectRequiredElements({
    root: "catalogueWorkDetailRoot",
    loadingNode: "catalogueWorkDetailLoading",
    emptyNode: "catalogueWorkDetailEmpty",
    fieldsNode: "catalogueWorkDetailFields",
    readonlyNode: "catalogueWorkDetailReadonly",
    previewNode: "catalogueWorkDetailPreview",
    summaryNode: "catalogueWorkDetailSummary",
    readinessNode: "catalogueWorkDetailReadiness",
    runtimeStateNode: "catalogueWorkDetailRuntimeState",
    buildImpactNode: "catalogueWorkDetailBuildImpact",
    searchNode: "catalogueWorkDetailSearchGlobal",
    popupNode: "catalogueWorkDetailPopup",
    popupListNode: "catalogueWorkDetailPopupList",
    openButton: "catalogueWorkDetailOpen",
    saveButton: "catalogueWorkDetailSave",
    publicationButton: "catalogueWorkDetailPublication",
    deleteButton: "catalogueWorkDetailDelete",
    saveModeNode: "catalogueWorkDetailSaveMode",
    contextNode: "catalogueWorkDetailContext",
    statusNode: "catalogueWorkDetailStatus",
    warningNode: "catalogueWorkDetailWarning",
    resultNode: "catalogueWorkDetailResult"
  });
  if (!elements) return;
  const {
    root,
    loadingNode,
    emptyNode,
    fieldsNode,
    readonlyNode,
    previewNode,
    summaryNode,
    readinessNode,
    runtimeStateNode,
    buildImpactNode,
    searchNode,
    popupNode,
    popupListNode,
    openButton,
    saveButton,
    publicationButton,
    deleteButton,
    saveModeNode,
    contextNode,
    statusNode,
    warningNode,
    resultNode
  } = elements;

  const state = {
    config: null,
    mode: "single",
    detailSearchByUid: new Map(),
    workSearchById: new Map(),
    currentLookup: null,
    currentDetailUid: "",
    currentWorkId: "",
    currentRecord: null,
    currentRecordHash: "",
    bulkDetailUids: [],
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
    buildPreview: null,
    isSaving: false,
    isBuilding: false,
    isDeleting: false,
    serverAvailable: false,
    root,
    fieldWrappers: new Map(),
    fieldNodes: new Map(),
    fieldStatusNodes: new Map(),
    readonlyNodes: new Map(),
    searchNode,
    popupNode,
    popupListNode,
    openButton,
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
    buildImpactNode
  };
  initializeCatalogueEditorRoute(root, "catalogue-work-detail");

  const formContext = buildWorkDetailFormContext(state);
  renderWorkDetailEditorFields(fieldsNode, state, formContext);
  renderWorkDetailReadonlyFields(readonlyNode, state, formContext);

  try {
    await configureCatalogueEditorRouteRuntime(state, {
      namespace: "catalogue_work_detail_editor",
      saveModeNode,
      applyText: () => {
        applyWorkDetailFieldLabels(state, formContext);
        searchNode.placeholder = t(state, "search_placeholder", "find detail id(s): 00001-001, 00001-003-005");
        openButton.textContent = t(state, "open_button", "Open");
        saveButton.textContent = t(state, "save_button", "Save");
        publicationButton.textContent = t(state, "publish_button", "Publish");
        deleteButton.textContent = t(state, "delete_button", "Delete");
      }
    });
    if (!state.serverAvailable) {
      setTextWithState(statusNode, t(state, "save_mode_unavailable_hint", "Local catalogue server unavailable. Save is disabled."), "warn");
      updateEditorState(state);
      revealCatalogueEditorRoute(state, {
        loadingNode,
        routeState: {
          route: "catalogue-work-detail",
          mode: routeModeForState,
          recordLoaded: routeRecordLoadedForState
        }
      });
      return;
    }

    await loadCatalogueEditorLookupMaps(state, [
      {
        configKey: "catalogue_lookup_work_detail_search",
        target: state.detailSearchByUid,
        normalizeKey: (record) => normalizeText(record.detail_uid)
      },
      {
        configKey: "catalogue_lookup_work_search",
        target: state.workSearchById,
        normalizeKey: (record) => normalizeWorkId(record.work_id)
      }
    ]);
    const selectionContext = buildWorkDetailSelectionContext(state);
    const actionContext = buildWorkDetailActionContext(state);
    bindWorkDetailSelectionControls(state, selectionContext);
    readinessNode.addEventListener("click", (event) => {
      const button = event.target && event.target.closest ? event.target.closest("[data-media-refresh]") : null;
      if (!button) return;
      refreshWorkDetailMedia(state, actionContext).catch((error) => {
        console.warn("catalogue_work_detail_editor: unexpected media refresh failure", error);
      });
    });
    saveButton.addEventListener("click", () => saveCurrentDetail(state, actionContext).catch((error) => {
      console.warn("catalogue_work_detail_editor: unexpected save failure", error);
    }));
    publicationButton.addEventListener("click", () => applyWorkDetailPublicationChange(state, actionContext).catch((error) => {
      console.warn("catalogue_work_detail_editor: unexpected publication failure", error);
    }));
    deleteButton.addEventListener("click", () => deleteCurrentDetail(state, actionContext).catch((error) => {
      console.warn("catalogue_work_detail_editor: unexpected delete failure", error);
    }));

    await applyInitialWorkDetailRouteSelection(state, selectionContext);

    revealCatalogueEditorRoute(state, {
      loadingNode,
      routeState: {
        route: "catalogue-work-detail",
        mode: routeModeForState,
        recordLoaded: routeRecordLoadedForState
      }
    });
  } catch (error) {
    console.warn("catalogue_work_detail_editor: init failed", error);
    await showCatalogueEditorInitError(
      loadingNode,
      "catalogue_work_detail_editor",
      "Failed to load catalogue source data for the work detail editor."
    );
  }
}

init();
