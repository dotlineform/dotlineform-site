import {
  catalogueEditorRecordLoaded,
  catalogueEditorRouteMode,
  catalogueEditorRouteStateDetail,
  createCatalogueEditorRouteStateOptions,
  initializeCatalogueEditorRoute,
  markCatalogueEditorRouteReady,
  syncCatalogueEditorRouteBusyState
} from "./catalogue-editor-route-boot.js";
import {
  WORK_DOWNLOAD_FIELDS as DOWNLOAD_FIELDS,
  WORK_LINK_FIELDS as LINK_FIELDS
} from "./catalogue-editor-embedded-items.js";
import {
  buildWorkDraftFromRecord,
  WORK_EDITABLE_FIELDS as EDITABLE_FIELDS,
  canonicalizeWorkScalar as canonicalizeScalar,
  normalizeText,
  normalizeWorkId,
  suggestNextWorkId
} from "./catalogue-work-fields.js";

function callback(options, name, ...args) {
  if (options && typeof options[name] === "function") {
    return options[name](...args);
  }
  return undefined;
}

function text(options, key, fallback, tokens = null) {
  if (options && typeof options.text === "function") {
    return options.text(key, fallback, tokens);
  }
  if (!tokens) return fallback;
  return Object.entries(tokens).reduce((value, [token, replacement]) => {
    return value.replace(new RegExp(`\\{${token}\\}`, "g"), () => replacement == null ? "" : String(replacement));
  }, fallback);
}

function buildDraftFromRecord(record) {
  return buildWorkDraftFromRecord(record, {
    fields: EDITABLE_FIELDS,
    downloadFields: DOWNLOAD_FIELDS,
    linkFields: LINK_FIELDS
  });
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

function resetBulkState(state) {
  state.bulkWorkIds = [];
  state.bulkRecords = new Map();
  state.bulkRecordHashes = new Map();
  state.bulkMixedFields = new Set();
  state.bulkTouchedFields = new Set();
  state.bulkBuildTargets = [];
}

function clearBuildState(state) {
  state.pendingBuildExtraSeriesIds = [];
  state.rebuildPending = false;
  state.buildPreview = null;
}

const WORK_ROUTE_STATE = createCatalogueEditorRouteStateOptions({
  route: "catalogue-work",
  bulkIdsKey: "bulkWorkIds",
  busyKeys: ["isSaving", "isBuilding", "isPreviewingBuild", "isDeleting"]
});

export function initializeWorkRouteState(root) {
  initializeCatalogueEditorRoute(root, "catalogue-work");
}

export function routeModeForWorkState(state) {
  return catalogueEditorRouteMode(state, WORK_ROUTE_STATE);
}

export function routeRecordLoadedForWorkState(state) {
  return catalogueEditorRecordLoaded(state, WORK_ROUTE_STATE);
}

export function workRouteStateDetail(state) {
  return catalogueEditorRouteStateDetail(state, WORK_ROUTE_STATE);
}

export function syncWorkRouteBusyState(state) {
  syncCatalogueEditorRouteBusyState(state, WORK_ROUTE_STATE);
}

export function markWorkRouteReady(state, ready) {
  markCatalogueEditorRouteReady(state, ready, WORK_ROUTE_STATE);
}

export function setLoadedWorkRecord(state, workId, record, options = {}) {
  state.mode = "single";
  state.currentWorkId = workId;
  state.currentRecord = record;
  state.currentLookup = options.lookup || state.currentLookup;
  state.currentRecordHash = normalizeText(options.recordHash || state.currentRecordHash);
  resetBulkState(state);
  state.baselineDraft = buildDraftFromRecord(record);
  state.draft = { ...state.baselineDraft };
  callback(options, "setOpenInputMode");
  callback(options, "applyDraftToInputs");
  callback(options, "applyReadonly");
  syncUrl(workId);
  callback(
    options,
    "setTextWithState",
    state.statusNode,
    text(options, "save_status_loaded", "Loaded work {work_id}.", { work_id: workId })
  );
  callback(options, "setTextWithState", state.warningNode, "");
  if (!options.keepResult) {
    callback(options, "setTextWithState", state.resultNode, "");
  }
  callback(options, "updateEditorState");
}

export function setLoadedBulkWorks(state, workIds, recordsById, recordHashes, options = {}) {
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
  callback(options, "setOpenInputMode");
  callback(options, "applyDraftToInputs");
  callback(options, "clearReadonlyFields");
  syncUrl(workIds.join(","));
  callback(
    options,
    "setTextWithState",
    state.statusNode,
    text(options, "bulk_status_loaded", "Loaded {count} work records.", { count: String(workIds.length) })
  );
  callback(options, "setTextWithState", state.warningNode, "");
  if (!options.keepResult) {
    callback(options, "setTextWithState", state.resultNode, "");
  }
  callback(options, "updateEditorState");
}

export function setNewWorkMode(state, options = {}) {
  state.mode = "new";
  state.currentWorkId = "";
  state.currentRecord = null;
  state.currentLookup = null;
  state.currentRecordHash = "";
  resetBulkState(state);
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
  state.searchNode.placeholder = text(options, "new_work_id_placeholder", "new work id");
  state.searchNode.setAttribute("aria-label", text(options, "new_work_id_label", "New work id"));
  state.detailSearchNode.value = "";
  clearBuildState(state);
  callback(options, "applyDraftToInputs");
  callback(options, "clearReadonlyFields");
  callback(options, "setPopupVisibility", false);
  syncUrl("", "new");
  callback(options, "setTextWithState", state.statusNode, text(options, "new_status_loaded", "Creating a draft work source record."));
  callback(options, "setTextWithState", state.warningNode, "");
  if (!options.keepResult) {
    callback(options, "setTextWithState", state.resultNode, "");
  }
  callback(options, "updateEditorState");
}

export function setEmptySearchMode(state, options = {}) {
  state.mode = "single";
  state.currentWorkId = "";
  state.currentRecord = null;
  state.currentLookup = null;
  state.currentRecordHash = "";
  resetBulkState(state);
  state.baselineDraft = null;
  state.draft = {};
  EDITABLE_FIELDS.forEach((field) => {
    state.draft[field.key] = "";
  });
  state.draft.downloads = [];
  state.draft.links = [];
  state.detailSearchNode.value = "";
  clearBuildState(state);
  callback(options, "setOpenInputMode");
  if (!options.keepSearchValue) {
    state.searchNode.value = "";
  }
  callback(options, "applyDraftToInputs");
  callback(options, "clearReadonlyFields");
  callback(options, "setPopupVisibility", false);
  syncUrl("");
  callback(options, "setTextWithState", state.statusNode, text(options, "missing_work_param", "Search for a work by work id."));
  callback(options, "setTextWithState", state.warningNode, "");
  if (!options.keepResult) {
    callback(options, "setTextWithState", state.resultNode, "");
  }
  callback(options, "updateEditorState");
}
