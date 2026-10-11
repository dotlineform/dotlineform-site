import {
  createCatalogueEditorRouteStateOptions,
  initializeCatalogueEditorRoute,
  syncCatalogueEditorRouteBusyState
} from "./catalogue-editor-route-boot.js";
import {
  WORK_DOWNLOAD_FIELDS as DOWNLOAD_FIELDS,
  WORK_LINK_FIELDS as LINK_FIELDS
} from "./catalogue-editor-embedded-items.js";
import { clearWorkMediaIntent } from "./catalogue-work-attachments.js";
import {
  buildWorkDraftFromRecord,
  WORK_EDITABLE_FIELDS as EDITABLE_FIELDS,
  canonicalizeWorkScalar as canonicalizeScalar,
  normalizeSeriesId,
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
  EDITABLE_FIELDS.forEach((field) => {
    if (field.key === "gallery_ids") {
      draft.gallery_ids = (drafts[0]?.gallery_ids || []).filter(id => drafts.every(item => item.gallery_ids.includes(id)));
      return;
    }
    const values = drafts.map((item) => canonicalizeScalar(field, item[field.key]));
    const first = values[0] || "";
    const allSame = values.every((value) => value === first);
    if (allSame) {
      draft[field.key] = drafts[0][field.key];
    } else {
      draft[field.key] = "";
    }
  });
  return draft;
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
  state.bulkTouchedFields = new Set();
}

const WORK_ROUTE_STATE = createCatalogueEditorRouteStateOptions({
  route: "catalogue-work",
  bulkIdsKey: "bulkWorkIds",
  busyKeys: ["isSaving", "isBuilding", "isDeleting"]
});

export function initializeWorkRouteState(root) {
  initializeCatalogueEditorRoute(root, "catalogue-work");
}

export function syncWorkRouteBusyState(state) {
  syncCatalogueEditorRouteBusyState(state, WORK_ROUTE_STATE);
}

export function setLoadedWorkRecord(state, workId, record, options = {}) {
  if (!options.preserveMediaIntent) clearWorkMediaIntent(state);
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
    ""
  );
  callback(options, "setTextWithState", state.warningNode, "");
  if (!options.keepResult) {
    callback(options, "setTextWithState", state.resultNode, "");
  }
  callback(options, "updateEditorState");
}

export function setLoadedBulkWorks(state, workIds, recordsById, recordHashes, options = {}) {
  clearWorkMediaIntent(state);
  state.mode = "bulk";
  state.currentWorkId = "";
  state.currentRecord = null;
  state.currentLookup = null;
  state.currentRecordHash = "";
  state.bulkWorkIds = workIds.slice();
  state.bulkRecords = new Map(recordsById);
  state.bulkRecordHashes = new Map(recordHashes);
  const records = workIds.map((workId) => recordsById.get(workId)).filter(Boolean);
  const bulkDraft = buildBulkDraftFromRecords(records);
  state.baselineDraft = { ...bulkDraft };
  state.draft = { ...bulkDraft };
  state.bulkTouchedFields = new Set();
  callback(options, "setOpenInputMode");
  callback(options, "applyDraftToInputs");
  callback(options, "clearReadonlyFields");
  syncUrl(workIds.join(","));
  callback(
    options,
    "setTextWithState",
    state.statusNode,
    ""
  );
  callback(options, "setTextWithState", state.warningNode, "");
  if (!options.keepResult) {
    callback(options, "setTextWithState", state.resultNode, "");
  }
  callback(options, "updateEditorState");
}

/** Start a pristine draft whose suggested ID and optional Series are its initial baseline. */
export function setNewWorkMode(state, options = {}) {
  clearWorkMediaIntent(state);
  state.mode = "new";
  state.currentWorkId = "";
  state.currentRecord = null;
  state.currentLookup = null;
  state.currentRecordHash = "";
  resetBulkState(state);
  state.draft = {};
  EDITABLE_FIELDS.forEach((field) => {
    state.draft[field.key] = "";
  });
  state.draft.gallery_ids = [];
  state.draft.downloads = [];
  state.draft.links = [];
  state.draft.series_id = normalizeSeriesId(options.seriesId);
  state.draft.work_id = normalizeWorkId(options.workId) || state.nextSuggestedWorkId || suggestNextWorkId(Array.from(state.workSearchById.values()));
  state.baselineDraft = { ...buildDraftFromRecord(state.draft), work_id: state.draft.work_id };
  state.searchNode.value = state.draft.work_id;
  state.searchNode.placeholder = "new work id";
  state.searchNode.setAttribute("aria-label", "New work id");
  callback(options, "applyDraftToInputs");
  callback(options, "clearReadonlyFields");
  callback(options, "setPopupVisibility", false);
  syncUrl("", "new");
  callback(options, "setTextWithState", state.statusNode, "");
  callback(options, "setTextWithState", state.warningNode, "");
  if (!options.keepResult) {
    callback(options, "setTextWithState", state.resultNode, "");
  }
  callback(options, "updateEditorState");
}

export function setEmptySearchMode(state, options = {}) {
  clearWorkMediaIntent(state);
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
  state.draft.gallery_ids = [];
  state.draft.downloads = [];
  state.draft.links = [];
  callback(options, "setOpenInputMode");
  if (!options.keepSearchValue) {
    state.searchNode.value = "";
  }
  callback(options, "applyDraftToInputs");
  callback(options, "clearReadonlyFields");
  callback(options, "setPopupVisibility", false);
  syncUrl("");
  callback(options, "setTextWithState", state.statusNode, "Search for a work by work id.");
  callback(options, "setTextWithState", state.warningNode, "");
  if (!options.keepResult) {
    callback(options, "setTextWithState", state.resultNode, "");
  }
  callback(options, "updateEditorState");
}
