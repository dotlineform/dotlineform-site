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

/** Compare saved values exactly, with blank dimensions sharing their prepared control value. */
function buildBulkDraftFromRecords(records) {
  const drafts = records.map((record) => buildDraftFromRecord(record));
  const draft = {};
  const mixedFields = new Set();
  EDITABLE_FIELDS.forEach((field) => {
    if (field.key === "series_id") {
      // Only the displayed Series member list supplies bulk selections.
      draft.series_id = drafts[0].series_id;
      return;
    }
    if (field.key === "gallery_ids") {
      draft.gallery_ids = (drafts[0]?.gallery_ids || []).filter(id => drafts.every(item => item.gallery_ids.includes(id)));
      return;
    }
    const compared = field.key === "height_cm" || field.key === "width_cm" ? drafts : records;
    const first = compared[0]?.[field.key];
    const allSame = compared.every((record) => record[field.key] === first);
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

/** Update the browsed Series bookmark while preserving Work/New state, without navigation. */
export function syncWorkSeriesUrl(seriesId) {
  const url = new URL(window.location.href);
  if (seriesId) url.searchParams.set("series", seriesId);
  else url.searchParams.delete("series");
  window.history.replaceState({}, "", url.toString());
}

function resetBulkState(state) {
  state.bulkWorkIds = [];
  state.bulkRecords = new Map();
  state.bulkRecordHashes = new Map();
  state.bulkTouchedFields = new Set();
  state.bulkMixedFields = new Set();
  state.bulkSourceFolder = null;
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
  else {
    // Canonical Save succeeded: returned dimensions are now saved values,
    // even when incomplete media processing retains the temporary preview.
    state.automaticDimensionFields.clear();
    state.manualDimensionFields.clear();
  }
  state.mode = "single";
  state.currentWorkId = workId;
  state.currentRecord = record;
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
  state.currentRecordHash = "";
  state.bulkWorkIds = workIds.slice();
  state.bulkRecords = new Map(recordsById);
  state.bulkRecordHashes = new Map(recordHashes);
  const records = workIds.map((workId) => recordsById.get(workId)).filter(Boolean);
  const { draft: bulkDraft, mixedFields } = buildBulkDraftFromRecords(records);
  state.baselineDraft = { ...bulkDraft };
  state.draft = { ...bulkDraft };
  state.bulkTouchedFields = new Set();
  state.bulkMixedFields = mixedFields;
  state.bulkSourceFolder = null;
  state.searchNode.value = "";
  callback(options, "setOpenInputMode");
  callback(options, "applyDraftToInputs");
  callback(options, "clearReadonlyFields");
  syncUrl("");
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
  state.baselineDraft = { ...state.draft, gallery_ids: [], downloads: [], links: [] };
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
