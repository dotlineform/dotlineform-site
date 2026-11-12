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

export function sharedWorkGalleryIds(records) {
  return records[0].gallery_ids.filter(id => records.every(record => record.gallery_ids.includes(id))).sort();
}

/** Compare saved values exactly, treating both absent and null dimensions as blank. */
function buildBulkDraftFromRecords(records) {
  const first = records[0];
  const firstDraft = buildWorkDraftFromRecord(first, { fields: EDITABLE_FIELDS });
  const draft = {};
  const mixedFields = new Set();
  EDITABLE_FIELDS.forEach((field) => {
    if (field.key === "gallery_ids") {
      draft.gallery_ids = sharedWorkGalleryIds(records);
      return;
    }
    const key = field.key;
    const dimension = key === "height_cm" || key === "width_cm";
    const firstValue = dimension ? first[key] ?? null : first[key];
    const allSame = records.every(record => (dimension ? record[key] ?? null : record[key]) === firstValue);
    if (allSame) {
      draft[key] = firstDraft[key];
    } else {
      draft[key] = "";
      mixedFields.add(key);
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
  state.bulkBrowseKind = "";
  state.bulkRecords = new Map();
  state.bulkTouchedFields = new Set();
  state.bulkMixedFields = new Set();
}

export function workBulkEditingPaused(state) {
  return state.mode === "bulk" && state.bulkBrowseKind !== state.browseKind;
}

export function workSaveBlockReason(state) {
  if (workBulkEditingPaused(state)) {
    const origin = state.bulkBrowseKind === "gallery" ? "Gallery" : "Series";
    return `Return to ${origin} view or select Works from the current list to continue bulk editing.`;
  }
  if (state.browseKind !== "gallery") return "";
  if (state.mode === "new") return "Return to Series view to save the new Work.";
  if (state.mode === "single" && state.currentRecord
    && normalizeSeriesId(state.draft.series_id) !== state.currentRecord.series_id) {
    return "Return to Series view to save the Series change.";
  }
  return "";
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
  state.root.dataset.workSaving = String(state.isSaving);
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
  state.pendingSourceFolder = null;
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

export function setLoadedBulkWorks(state, workIds, recordsById, options = {}) {
  clearWorkMediaIntent(state);
  state.mode = "bulk";
  state.currentWorkId = "";
  state.currentRecord = null;
  state.bulkWorkIds = workIds.slice();
  state.bulkBrowseKind = state.browseKind;
  state.bulkRecords = new Map(recordsById);
  const records = workIds.map((workId) => recordsById.get(workId));
  const { draft: bulkDraft, mixedFields } = buildBulkDraftFromRecords(records);
  state.baselineDraft = { ...bulkDraft };
  state.draft = { ...bulkDraft };
  state.bulkTouchedFields = new Set();
  state.bulkMixedFields = mixedFields;
  state.pendingSourceFolder = null;
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
  if (state.browseKind === "gallery") return;
  clearWorkMediaIntent(state);
  state.pendingSourceFolder = null;
  state.mode = "new";
  state.currentWorkId = "";
  state.currentRecord = null;
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
  state.pendingSourceFolder = null;
  state.mode = "single";
  state.currentWorkId = "";
  state.currentRecord = null;
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
