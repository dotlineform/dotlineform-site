import {
  getStudioDataPath,
  getStudioRoute,
  getStudioText,
  loadStudioConfig
} from "./studio-config.js";
import {
  fetchJson,
  loadStudioLookupRecordJson
} from "./studio-data.js";
import {
  CATALOGUE_WRITE_ENDPOINTS,
  postJson,
  probeCatalogueHealth
} from "./studio-transport.js";
import {
  buildSaveModeText,
  utcTimestamp
} from "./tag-studio-save.js";

const EDITABLE_FIELDS = [
  { key: "filename", label: "filename", type: "text" },
  { key: "label", label: "label", type: "text" },
  { key: "status", label: "status", type: "select", options: ["", "draft", "published"] },
  { key: "published_date", label: "published date", type: "date" }
];

const READONLY_FIELDS = [
  { key: "file_uid", label: "file id" },
  { key: "work_id", label: "work id" }
];

const STATUS_OPTIONS = new Set(["", "draft", "published"]);
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const SEARCH_LIMIT = 20;

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function escapeHtml(value) {
  return normalizeText(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function stableStringify(value) {
  if (Array.isArray(value)) return `[${value.map((item) => stableStringify(item)).join(",")}]`;
  if (value && typeof value === "object") {
    const keys = Object.keys(value).sort();
    return `{${keys.map((key) => `${JSON.stringify(key)}:${stableStringify(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

async function computeRecordHash(record) {
  if (!globalThis.crypto || !crypto.subtle) return "";
  const bytes = new TextEncoder().encode(stableStringify(record));
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest)).map((value) => value.toString(16).padStart(2, "0")).join("");
}

function displayValue(value) {
  const text = normalizeText(value);
  return text || "—";
}

function buildSearchToken(value) {
  const text = normalizeText(value);
  if (!text) return "";
  const digits = text.replace(/\D/g, "");
  return digits || text.toLowerCase();
}

function setTextWithState(node, text, state = "") {
  if (!node) return;
  node.textContent = text || "";
  if (state) node.dataset.state = state;
  else delete node.dataset.state;
}

function setPopupVisibility(state, visible) {
  state.popupNode.hidden = !visible;
}

function t(state, key, fallback, tokens = null) {
  return getStudioText(state.config, `catalogue_work_file_editor.${key}`, fallback, tokens);
}

function buildRecordSummary(record) {
  const label = normalizeText(record && record.label);
  const filename = normalizeText(record && record.filename);
  const workId = normalizeText(record && record.work_id);
  if (label && filename && label !== filename) return `${label} · ${filename} · work ${workId || "—"}`;
  return label || filename || (workId ? `work ${workId}` : "—");
}

function getSearchMatches(state, rawQuery) {
  const query = buildSearchToken(rawQuery);
  if (!query) return [];
  const matches = [];
  for (const [fileUid, record] of state.fileSearchByUid.entries()) {
    const label = normalizeText(record && record.label).toLowerCase();
    const filename = normalizeText(record && record.filename).toLowerCase();
    const workId = normalizeText(record && record.work_id);
    if (fileUid.toLowerCase().includes(query) || label.includes(query) || filename.includes(query) || workId.includes(query)) {
      matches.push({ fileUid, record });
    }
  }
  matches.sort((a, b) => a.fileUid.localeCompare(b.fileUid, undefined, { numeric: true, sensitivity: "base" }));
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
  const rows = matches.map(({ fileUid, record }) => `
    <button type="button" class="tagStudioSuggest__workButton" data-file-uid="${escapeHtml(fileUid)}">
      <span class="tagStudioSuggest__workId">${escapeHtml(fileUid)}</span>
      <span class="tagStudioSuggest__workTitle">${escapeHtml(buildRecordSummary(record))}</span>
    </button>
  `);
  state.popupListNode.innerHTML = `<div class="tagStudioSuggest__workRows">${rows.join("")}</div>`;
  setPopupVisibility(state, true);
}

function renderField(field, fieldsNode, state) {
  const wrapper = document.createElement("label");
  wrapper.className = "tagStudioForm__field catalogueWorkForm__field";
  wrapper.htmlFor = `catalogueWorkFileField-${field.key}`;

  const label = document.createElement("span");
  label.className = "tagStudioForm__label";
  label.textContent = field.label;
  wrapper.appendChild(label);

  let input;
  if (field.type === "select") {
    input = document.createElement("select");
    input.className = "tagStudio__input";
    field.options.forEach((optionValue) => {
      const option = document.createElement("option");
      option.value = optionValue;
      option.textContent = optionValue || "(blank)";
      input.appendChild(option);
    });
  } else {
    input = document.createElement("input");
    input.className = "tagStudio__input";
    input.type = field.type === "date" ? "date" : "text";
  }

  input.id = `catalogueWorkFileField-${field.key}`;
  input.dataset.field = field.key;
  wrapper.appendChild(input);

  const message = document.createElement("span");
  message.className = "catalogueWorkForm__fieldStatus";
  wrapper.appendChild(message);

  input.addEventListener("input", () => onFieldInput(state, field.key));
  input.addEventListener("change", () => onFieldInput(state, field.key));
  fieldsNode.appendChild(wrapper);
  state.fieldNodes.set(field.key, input);
  state.fieldStatusNodes.set(field.key, message);
}

function renderReadonlyField(field, readonlyNode, state) {
  const wrapper = document.createElement("div");
  wrapper.className = "tagStudioForm__field";

  const label = document.createElement("span");
  label.className = "tagStudioForm__label";
  label.textContent = field.label;
  wrapper.appendChild(label);

  const value = document.createElement("div");
  value.className = "tagStudio__input tagStudio__input--readonlyDisplay";
  wrapper.appendChild(value);

  readonlyNode.appendChild(wrapper);
  state.readonlyNodes.set(field.key, value);
}

async function loadWorkFileLookupRecord(state, fileUid) {
  return loadStudioLookupRecordJson(state.config, "catalogue_lookup_work_file_base", fileUid, { cache: "no-store" });
}

function buildDraftFromRecord(record) {
  const draft = {};
  EDITABLE_FIELDS.forEach((field) => {
    draft[field.key] = normalizeText(record[field.key]);
  });
  return draft;
}

function applyDraftToInputs(state) {
  EDITABLE_FIELDS.forEach((field) => {
    const node = state.fieldNodes.get(field.key);
    if (node) node.value = normalizeText(state.draft[field.key]);
  });
}

function applyReadonly(state) {
  READONLY_FIELDS.forEach((field) => {
    const node = state.readonlyNodes.get(field.key);
    if (node) node.textContent = displayValue(state.currentRecord ? state.currentRecord[field.key] : "");
  });
}

function draftHasChanges(state) {
  if (!state.baselineDraft) return false;
  return EDITABLE_FIELDS.some((field) => normalizeText(state.draft[field.key]) !== normalizeText(state.baselineDraft[field.key]));
}

function validateDraft(state) {
  const errors = new Map();
  if (!normalizeText(state.draft.filename)) {
    errors.set("filename", t(state, "field_required_filename", "Enter a filename."));
  }
  if (!normalizeText(state.draft.label)) {
    errors.set("label", t(state, "field_required_label", "Enter a label."));
  }
  const status = normalizeText(state.draft.status).toLowerCase();
  if (!STATUS_OPTIONS.has(status)) {
    errors.set("status", t(state, "field_invalid_status", "Use blank, draft, or published."));
  }
  const publishedDate = normalizeText(state.draft.published_date);
  if (publishedDate && !DATE_RE.test(publishedDate)) {
    errors.set("published_date", t(state, "field_invalid_date", "Use YYYY-MM-DD or leave blank."));
  }
  return errors;
}

function updateFieldMessages(state, errors) {
  EDITABLE_FIELDS.forEach((field) => {
    const node = state.fieldStatusNodes.get(field.key);
    if (!node) return;
    const message = errors.get(field.key) || "";
    node.textContent = message;
    node.hidden = !message;
  });
}

function buildPayload(state) {
  return {
    file_uid: state.currentFileUid,
    expected_record_hash: state.currentRecordHash,
    record: {
      file_uid: state.currentFileUid,
      work_id: state.currentWorkId,
      filename: normalizeText(state.draft.filename) || null,
      label: normalizeText(state.draft.label) || null,
      status: normalizeText(state.draft.status).toLowerCase() || null,
      published_date: normalizeText(state.draft.published_date) || null
    }
  };
}

function formatBuildPreview(state, build) {
  if (!build || typeof build !== "object") return "";
  const workIds = Array.isArray(build.work_ids) ? build.work_ids : [];
  const seriesIds = Array.isArray(build.series_ids) ? build.series_ids : [];
  const workText = workIds.length ? workIds.join(", ") : "none";
  const seriesText = seriesIds.length ? seriesIds.join(", ") : "none";
  const searchText = build.rebuild_search ? t(state, "build_preview_search_yes", "yes") : t(state, "build_preview_search_no", "no");
  return t(state, "build_preview_template", "Build preview: work {work_ids}; series {series_ids}; catalogue search {search_rebuild}.", {
    work_ids: workText,
    series_ids: seriesText,
    search_rebuild: searchText
  });
}

function updateSummary(state) {
  const record = state.currentRecord;
  state.metaNode.textContent = record ? `${record.file_uid} · ${displayValue(record.label)}` : "";
  const workEditorRoute = getStudioRoute(state.config, "catalogue_work_editor");
  state.summaryNode.innerHTML = `
    <div class="tagStudioForm__field">
      <span class="tagStudioForm__label">${escapeHtml(t(state, "summary_parent_work", "Open parent work editor"))}</span>
      <div class="tagStudio__input tagStudio__input--readonlyDisplay">
        ${record ? `<a href="${escapeHtml(`${workEditorRoute}?work=${encodeURIComponent(record.work_id)}`)}">${escapeHtml(record.work_id)}</a>` : "—"}
      </div>
    </div>
  `;
  state.runtimeStateNode.textContent = state.rebuildPending
    ? t(state, "summary_rebuild_needed", "source changed; rebuild pending")
    : t(state, "summary_rebuild_current", "source and runtime not yet diverged in this session");
}

function updateEditorState(state) {
  const hasRecord = Boolean(state.currentRecord);
  const errors = hasRecord ? validateDraft(state) : new Map();
  state.validationErrors = errors;
  updateFieldMessages(state, errors);
  updateSummary(state);
  if (!hasRecord) setTextWithState(state.buildImpactNode, "");
  const dirty = hasRecord && draftHasChanges(state);
  setTextWithState(state.warningNode, dirty ? t(state, "dirty_warning", "Unsaved source changes.") : "");
  state.saveButton.disabled = !hasRecord || state.isSaving || state.isDeleting || errors.size > 0 || !dirty || !state.serverAvailable;
  state.buildButton.disabled = !hasRecord || state.isSaving || state.isBuilding || state.isDeleting || errors.size > 0 || !state.serverAvailable;
  state.deleteButton.disabled = !hasRecord || state.isSaving || state.isBuilding || state.isDeleting || !state.serverAvailable;
}

function openWorkFileByUid(state, fileUid) {
  const normalizedFileUid = normalizeText(fileUid);
  if (!normalizedFileUid) return;
  const route = getStudioRoute(state.config, "catalogue_work_file_editor");
  window.location.assign(`${route}?file=${encodeURIComponent(normalizedFileUid)}`);
}

function openRequestedSearch(state, rawValue) {
  const matches = getSearchMatches(state, rawValue);
  const exactMatch = matches.find(({ fileUid }) => normalizeText(fileUid).toLowerCase() === normalizeText(rawValue).toLowerCase());
  const selected = exactMatch || matches[0];
  if (!selected) {
    renderSearchMatches(state, [], t(state, "search_no_match", "No matching work files."));
    return;
  }
  openWorkFileByUid(state, selected.fileUid);
}

function setLoadedRecord(state, fileUid, record, options = {}) {
  state.currentFileUid = fileUid;
  state.currentRecord = record;
  state.currentWorkId = normalizeText(record && record.work_id);
  state.currentLookup = options.lookup || state.currentLookup;
  state.currentRecordHash = normalizeText(options.recordHash || state.currentRecordHash);
  state.baselineDraft = buildDraftFromRecord(record);
  state.draft = { ...state.baselineDraft };
  applyDraftToInputs(state);
  applyReadonly(state);
  if (state.searchNode) state.searchNode.value = fileUid;
  setTextWithState(state.contextNode, t(state, "context_loaded", "Editing source metadata for work file {file_uid}.", { file_uid: fileUid }));
  setTextWithState(state.statusNode, t(state, "save_status_loaded", "Loaded work file {file_uid}.", { file_uid: fileUid }));
  if (!options.keepResult) setTextWithState(state.resultNode, "");
  updateEditorState(state);
}

function onFieldInput(state, fieldKey) {
  const node = state.fieldNodes.get(fieldKey);
  if (!node) return;
  state.draft[fieldKey] = node.value;
  updateEditorState(state);
}

async function refreshBuildPreview(state) {
  if (!state.currentWorkId || !state.serverAvailable) {
    setTextWithState(state.buildImpactNode, "");
    return;
  }
  try {
    const response = await postJson(CATALOGUE_WRITE_ENDPOINTS.buildPreview, { work_id: state.currentWorkId });
    setTextWithState(state.buildImpactNode, formatBuildPreview(state, response && response.build));
  } catch (error) {
    setTextWithState(state.buildImpactNode, `${t(state, "build_preview_failed", "Build preview unavailable.")} ${normalizeText(error && error.message)}`.trim(), "error");
  }
}

async function saveCurrentRecord(state) {
  const errors = validateDraft(state);
  updateFieldMessages(state, errors);
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
  updateEditorState(state);
  setTextWithState(state.statusNode, t(state, "save_status_saving", "Saving source record…"));
  setTextWithState(state.resultNode, "");
  try {
    const response = await postJson(CATALOGUE_WRITE_ENDPOINTS.saveWorkFile, buildPayload(state));
    const lookup = await loadWorkFileLookupRecord(state, state.currentFileUid);
    const record = lookup && lookup.work_file && typeof lookup.work_file === "object" ? lookup.work_file : response.record;
    setLoadedRecord(state, state.currentFileUid, record, {
      recordHash: normalizeText(response.record_hash) || normalizeText(lookup && lookup.record_hash) || await computeRecordHash(record),
      keepResult: true,
      lookup
    });
    state.rebuildPending = Boolean(response.changed);
    await refreshBuildPreview(state);
    const savedAt = normalizeText(response.saved_at_utc || utcTimestamp());
    setTextWithState(state.resultNode, response.changed ? t(state, "save_result_success", "Source saved at {saved_at}. Rebuild needed to update public catalogue.", { saved_at: savedAt }) : t(state, "save_result_unchanged", "Source already matches the current form values."), response.changed ? "success" : "");
    setTextWithState(state.statusNode, t(state, "save_status_loaded", "Loaded work file {file_uid}.", { file_uid: state.currentFileUid }), "success");
  } catch (error) {
    const message = Number(error && error.status) === 409
      ? t(state, "save_status_conflict", "Source record changed since this page loaded. Reload before saving again.")
      : `${t(state, "save_status_failed", "Source save failed.")} ${normalizeText(error && error.message)}`.trim();
    setTextWithState(state.statusNode, message, "error");
  } finally {
    state.isSaving = false;
    updateEditorState(state);
  }
}

async function buildCurrentWork(state) {
  if (!state.currentWorkId || !state.serverAvailable) return;
  state.isBuilding = true;
  updateEditorState(state);
  setTextWithState(state.statusNode, t(state, "build_status_running", "Running scoped rebuild…"));
  setTextWithState(state.resultNode, "");
  try {
    const response = await postJson(CATALOGUE_WRITE_ENDPOINTS.buildApply, { work_id: state.currentWorkId });
    state.rebuildPending = false;
    await refreshBuildPreview(state);
    const completedAt = normalizeText(response.completed_at_utc || utcTimestamp());
    setTextWithState(state.resultNode, t(state, "build_result_success", "Runtime rebuilt at {completed_at}. Build Activity updated.", { completed_at: completedAt }), "success");
    setTextWithState(state.statusNode, t(state, "build_status_success", "Scoped rebuild completed."), "success");
  } catch (error) {
    setTextWithState(state.statusNode, `${t(state, "build_status_failed", "Scoped rebuild failed.")} ${normalizeText(error && error.message)}`.trim(), "error");
  } finally {
    state.isBuilding = false;
    updateEditorState(state);
  }
}

async function saveAndBuild(state) {
  if (draftHasChanges(state)) {
    await saveCurrentRecord(state);
    if (state.statusNode.dataset.state === "error" || draftHasChanges(state)) return;
  }
  await buildCurrentWork(state);
}

async function deleteCurrentRecord(state) {
  if (!state.currentFileUid || !state.serverAvailable) return;
  state.isDeleting = true;
  updateEditorState(state);
  setTextWithState(state.statusNode, t(state, "delete_status_running", "Deleting source record…"));
  setTextWithState(state.resultNode, "");
  try {
    await postJson(CATALOGUE_WRITE_ENDPOINTS.deleteWorkFile, {
      file_uid: state.currentFileUid,
      expected_record_hash: state.currentRecordHash
    });
    const route = getStudioRoute(state.config, "catalogue_work_editor");
    window.location.assign(`${route}?work=${encodeURIComponent(state.currentWorkId)}`);
  } catch (error) {
    const message = Number(error && error.status) === 409
      ? t(state, "delete_status_conflict", "Source record changed since this page loaded. Reload before deleting again.")
      : `${t(state, "delete_status_failed", "Source delete failed.")} ${normalizeText(error && error.message)}`.trim();
    setTextWithState(state.statusNode, message, "error");
    state.isDeleting = false;
    updateEditorState(state);
  }
}

async function init() {
  const root = document.getElementById("catalogueWorkFileRoot");
  const loadingNode = document.getElementById("catalogueWorkFileLoading");
  const emptyNode = document.getElementById("catalogueWorkFileEmpty");
  const fieldsNode = document.getElementById("catalogueWorkFileFields");
  const readonlyNode = document.getElementById("catalogueWorkFileReadonly");
  const searchNode = document.getElementById("catalogueWorkFileSearch");
  const popupNode = document.getElementById("catalogueWorkFilePopup");
  const popupListNode = document.getElementById("catalogueWorkFilePopupList");
  const openButton = document.getElementById("catalogueWorkFileOpen");
  const saveModeNode = document.getElementById("catalogueWorkFileSaveMode");
  const contextNode = document.getElementById("catalogueWorkFileContext");
  const statusNode = document.getElementById("catalogueWorkFileStatus");
  const warningNode = document.getElementById("catalogueWorkFileWarning");
  const resultNode = document.getElementById("catalogueWorkFileResult");
  const metaNode = document.getElementById("catalogueWorkFileMeta");
  const runtimeStateNode = document.getElementById("catalogueWorkFileRuntimeState");
  const buildImpactNode = document.getElementById("catalogueWorkFileBuildImpact");
  const summaryNode = document.getElementById("catalogueWorkFileSummary");
  const saveButton = document.getElementById("catalogueWorkFileSave");
  const buildButton = document.getElementById("catalogueWorkFileBuild");
  const deleteButton = document.getElementById("catalogueWorkFileDelete");
  if (!root || !loadingNode || !emptyNode || !fieldsNode || !readonlyNode || !searchNode || !popupNode || !popupListNode || !openButton || !saveModeNode || !contextNode || !statusNode || !warningNode || !resultNode || !metaNode || !runtimeStateNode || !buildImpactNode || !summaryNode || !saveButton || !buildButton || !deleteButton) {
    return;
  }

  const state = {
    config: null,
    fileSearchByUid: new Map(),
    currentLookup: null,
    currentFileUid: "",
    currentWorkId: "",
    currentRecord: null,
    currentRecordHash: "",
    baselineDraft: null,
    draft: {},
    validationErrors: new Map(),
    rebuildPending: false,
    serverAvailable: false,
    isSaving: false,
    isBuilding: false,
    isDeleting: false,
    fieldNodes: new Map(),
    fieldStatusNodes: new Map(),
    readonlyNodes: new Map(),
    searchNode,
    popupNode,
    popupListNode,
    openButton,
    saveButton,
    buildButton,
    deleteButton,
    contextNode,
    statusNode,
    warningNode,
    resultNode,
    metaNode,
    runtimeStateNode,
    buildImpactNode,
    summaryNode
  };

  EDITABLE_FIELDS.forEach((field) => renderField(field, fieldsNode, state));
  READONLY_FIELDS.forEach((field) => renderReadonlyField(field, readonlyNode, state));

  try {
    const config = await loadStudioConfig();
    state.config = config;
    searchNode.placeholder = t(state, "search_placeholder", "find work file by id, filename, or work id");
    openButton.textContent = t(state, "open_button", "Open");
    saveButton.textContent = t(state, "save_button", "Save");
    buildButton.textContent = t(state, "build_button", "Rebuild");
    deleteButton.textContent = t(state, "delete_button", "Delete");

    const [filesPayload, serverAvailable] = await Promise.all([
      fetchJson(getStudioDataPath(config, "catalogue_work_files"), { cache: "no-store" }),
      probeCatalogueHealth()
    ]);
    const fileRecords = filesPayload && filesPayload.work_files && typeof filesPayload.work_files === "object"
      ? filesPayload.work_files
      : {};
    Object.keys(fileRecords).forEach((key) => {
      const record = fileRecords[key] && typeof fileRecords[key] === "object" ? fileRecords[key] : {};
      const fileUid = normalizeText(record.file_uid || key);
      if (!fileUid) return;
      state.fileSearchByUid.set(fileUid, record);
    });
    state.serverAvailable = Boolean(serverAvailable);
    saveModeNode.textContent = buildSaveModeText(config, serverAvailable ? "post" : "offline", (cfg, key, fallback, tokens) => getStudioText(cfg, `catalogue_work_file_editor.${key}`, fallback, tokens));
    if (!state.serverAvailable) {
      setTextWithState(statusNode, t(state, "save_mode_unavailable_hint", "Local catalogue server unavailable. Save is disabled."), "warn");
    }

    searchNode.addEventListener("input", () => {
      const query = searchNode.value;
      if (!normalizeText(query)) {
        renderSearchMatches(state, [], "");
        return;
      }
      const matches = getSearchMatches(state, query);
      if (!matches.length) {
        renderSearchMatches(state, [], t(state, "search_no_match", "No matching work files."));
        return;
      }
      renderSearchMatches(state, matches);
    });
    searchNode.addEventListener("keydown", (event) => {
      if (event.key !== "Enter") return;
      event.preventDefault();
      openRequestedSearch(state, searchNode.value);
    });
    popupListNode.addEventListener("click", (event) => {
      const button = event.target && event.target.closest ? event.target.closest("[data-file-uid]") : null;
      if (!button) return;
      openWorkFileByUid(state, button.getAttribute("data-file-uid"));
    });
    openButton.addEventListener("click", () => {
      openRequestedSearch(state, searchNode.value);
    });
    document.addEventListener("click", (event) => {
      if (event.target === searchNode || popupNode.contains(event.target)) return;
      setPopupVisibility(state, false);
    });

    const fileUid = normalizeText(new URLSearchParams(window.location.search).get("file"));
    if (!fileUid) {
      setTextWithState(contextNode, t(state, "missing_file_param", "Search for a work file by file id, filename, label, or work id."));
      root.hidden = false;
      loadingNode.hidden = true;
      updateEditorState(state);
      return;
    }

    const lookup = await loadWorkFileLookupRecord(state, fileUid);
    const record = lookup && lookup.work_file && typeof lookup.work_file === "object" ? lookup.work_file : null;
    if (!record) throw new Error(`work file lookup missing record for ${fileUid}`);
    setLoadedRecord(state, fileUid, record, {
      recordHash: normalizeText(lookup.record_hash) || await computeRecordHash(record),
      lookup
    });
    await refreshBuildPreview(state);

    saveButton.addEventListener("click", () => {
      saveCurrentRecord(state).catch((error) => console.warn("catalogue_work_file_editor: unexpected save failure", error));
    });
    buildButton.addEventListener("click", () => {
      saveAndBuild(state).catch((error) => console.warn("catalogue_work_file_editor: unexpected build failure", error));
    });
    deleteButton.addEventListener("click", () => {
      deleteCurrentRecord(state).catch((error) => console.warn("catalogue_work_file_editor: unexpected delete failure", error));
    });

    root.hidden = false;
    loadingNode.hidden = true;
  } catch (error) {
    console.warn("catalogue_work_file_editor: init failed", error);
    loadingNode.textContent = "Failed to load work file editor.";
  }
}

init();
