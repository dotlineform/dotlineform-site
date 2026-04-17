import {
  getStudioRoute,
  getStudioText,
  loadStudioConfig
} from "./studio-config.js";
import { loadStudioLookupJson, loadStudioLookupRecordJson } from "./studio-data.js";
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
  { key: "project_subfolder", label: "project subfolder", type: "text" },
  { key: "project_filename", label: "project filename", type: "text" },
  { key: "title", label: "title", type: "text" },
  { key: "status", label: "status", type: "select", options: ["", "draft", "published"] }
];

const READONLY_FIELDS = [
  { key: "detail_uid", label: "detail id" },
  { key: "work_id", label: "work id" },
  { key: "detail_id", label: "detail row id" },
  { key: "published_date", label: "published date" },
  { key: "width_px", label: "width px" },
  { key: "height_px", label: "height px" }
];

const STATUS_OPTIONS = new Set(["", "draft", "published"]);
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

function normalizeWorkId(value) {
  const digits = normalizeText(value).replace(/\D/g, "");
  if (!digits) return "";
  return digits.padStart(5, "0");
}

function normalizeDetailId(value) {
  const digits = normalizeText(value).replace(/\D/g, "");
  if (!digits) return "";
  return digits.padStart(3, "0");
}

function normalizeDetailUid(value) {
  const text = normalizeText(value);
  if (!text) return "";
  const match = text.match(/^(\d{5})-(\d{3})$/);
  if (match) return `${match[1]}-${match[2]}`;
  const digits = text.replace(/\D/g, "");
  if (digits.length === 8) {
    return `${digits.slice(0, 5)}-${digits.slice(5)}`;
  }
  return "";
}

function stableStringify(value) {
  if (Array.isArray(value)) {
    return `[${value.map((item) => stableStringify(item)).join(",")}]`;
  }
  if (value && typeof value === "object") {
    const keys = Object.keys(value).sort();
    return `{${keys.map((key) => `${JSON.stringify(key)}:${stableStringify(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

async function computeRecordHash(record) {
  if (!globalThis.crypto || !crypto.subtle) return "";
  const json = stableStringify(record);
  const bytes = new TextEncoder().encode(json);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest)).map((value) => value.toString(16).padStart(2, "0")).join("");
}

function displayValue(value) {
  const text = normalizeText(value);
  return text || "—";
}

function canonicalizeScalar(field, value) {
  return normalizeText(value);
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

function renderField(field, fieldsNode, state) {
  const wrapper = document.createElement("label");
  wrapper.className = "tagStudioForm__field catalogueWorkForm__field";
  wrapper.htmlFor = `catalogueWorkDetailField-${field.key}`;

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
    input.type = "text";
  }

  input.id = `catalogueWorkDetailField-${field.key}`;
  input.dataset.field = field.key;
  wrapper.appendChild(input);

  const message = document.createElement("span");
  message.className = "catalogueWorkForm__fieldStatus";
  message.dataset.fieldStatus = field.key;
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

  const value = document.createElement("span");
  value.className = "tagStudio__input tagStudioForm__readonly";
  value.dataset.readonlyField = field.key;
  value.textContent = "—";
  wrapper.appendChild(value);

  readonlyNode.appendChild(wrapper);
  state.readonlyNodes.set(field.key, value);
}

function buildRecordSummary(record) {
  const title = normalizeText(record && record.title);
  const section = normalizeText(record && record.project_subfolder);
  if (title && section) return `${title} · ${section}`;
  return title || section || "—";
}

function getSearchMatches(state, rawQuery) {
  const query = normalizeText(rawQuery).toLowerCase();
  const normalizedUid = normalizeDetailUid(rawQuery);
  const normalizedDetailId = normalizeDetailId(rawQuery);
  if (!query && !normalizedUid && !normalizedDetailId) return [];
  const matches = [];
  for (const [detailUid, record] of state.detailSearchByUid.entries()) {
    const detailId = normalizeText(record && record.detail_id);
    const title = normalizeText(record && record.title).toLowerCase();
    if (
      (normalizedUid && detailUid.startsWith(normalizedUid)) ||
      (normalizedDetailId && detailId.startsWith(normalizedDetailId)) ||
      detailUid.toLowerCase().startsWith(query) ||
      title.includes(query)
    ) {
      matches.push({ detailUid, record });
    }
  }
  matches.sort((a, b) => a.detailUid.localeCompare(b.detailUid, undefined, { numeric: true, sensitivity: "base" }));
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

  const rows = matches.map(({ detailUid, record }) => `
    <button type="button" class="tagStudioSuggest__workButton" data-detail-uid="${escapeHtml(detailUid)}">
      <span class="tagStudioSuggest__workId">${escapeHtml(detailUid)}</span>
      <span class="tagStudioSuggest__workTitle">${escapeHtml(buildRecordSummary(record))}</span>
    </button>
  `);
  state.popupListNode.innerHTML = `<div class="tagStudioSuggest__workRows">${rows.join("")}</div>`;
  setPopupVisibility(state, true);
}

async function loadDetailLookupRecord(state, detailUid) {
  return loadStudioLookupRecordJson(state.config, "catalogue_lookup_work_detail_base", detailUid, { cache: "no-store" });
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
    if (!node) return;
    node.value = normalizeText(state.draft[field.key]);
  });
}

function applyReadonly(state) {
  READONLY_FIELDS.forEach((field) => {
    const node = state.readonlyNodes.get(field.key);
    if (!node) return;
    node.textContent = displayValue(state.currentRecord ? state.currentRecord[field.key] : "");
  });
}

function buildPayload(state) {
  const draft = state.draft;
  return {
    detail_uid: state.currentDetailUid,
    expected_record_hash: state.currentRecordHash,
    record: {
      detail_uid: state.currentDetailUid,
      work_id: state.currentWorkId,
      detail_id: state.currentRecord.detail_id,
      project_subfolder: normalizeText(draft.project_subfolder) || null,
      project_filename: normalizeText(draft.project_filename) || null,
      title: normalizeText(draft.title) || null,
      status: normalizeText(draft.status).toLowerCase() || null
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
  return t(
    state,
    "build_preview_template",
    "Build preview: work {work_ids}; series {series_ids}; catalogue search {search_rebuild}.",
    {
      work_ids: workText,
      series_ids: seriesText,
      search_rebuild: searchText
    }
  );
}

function syncUrl(detailUid) {
  const url = new URL(window.location.href);
  if (detailUid) url.searchParams.set("detail", detailUid);
  else url.searchParams.delete("detail");
  window.history.replaceState({}, "", url.toString());
}

function draftHasChanges(state) {
  if (!state.baselineDraft) return false;
  return EDITABLE_FIELDS.some((field) => canonicalizeScalar(field, state.draft[field.key]) !== canonicalizeScalar(field, state.baselineDraft[field.key]));
}

function validateDraft(state) {
  const errors = new Map();
  const status = normalizeText(state.draft.status).toLowerCase();
  if (!STATUS_OPTIONS.has(status)) {
    errors.set("status", t(state, "field_invalid_status", "Use blank, draft, or published."));
  }
  return errors;
}

function updateFieldMessages(state, errors) {
  EDITABLE_FIELDS.forEach((field) => {
    const messageNode = state.fieldStatusNodes.get(field.key);
    if (!messageNode) return;
    const message = errors.get(field.key) || "";
    messageNode.textContent = message;
    messageNode.hidden = !message;
  });
}

function updateSummary(state) {
  const record = state.currentRecord;
  state.metaNode.textContent = record
    ? `${record.detail_uid} · ${buildRecordSummary(record)}`
    : "";

  const publicBase = getStudioRoute(state.config, "work_details_page_base");
  const workEditorBase = getStudioRoute(state.config, "catalogue_work_editor");
  const publicHref = record ? `${publicBase}${encodeURIComponent(record.detail_uid)}/` : "";
  const workEditorHref = record ? `${workEditorBase}?work=${encodeURIComponent(record.work_id)}` : "";
  state.summaryNode.innerHTML = `
    <div class="tagStudioForm__field">
      <span class="tagStudioForm__label">${escapeHtml(t(state, "summary_public_link", "Open public detail page"))}</span>
      <span class="tagStudioForm__readonly">
        ${record ? `<a href="${escapeHtml(publicHref)}" target="_blank" rel="noopener">${escapeHtml(record.detail_uid)}</a>` : "—"}
      </span>
    </div>
    <div class="tagStudioForm__field">
      <span class="tagStudioForm__label">${escapeHtml(t(state, "summary_parent_link", "Open work editor"))}</span>
      <span class="tagStudioForm__readonly">
        ${record ? `<a href="${escapeHtml(workEditorHref)}">${escapeHtml(record.work_id)}</a>` : "—"}
      </span>
    </div>
    <div class="tagStudioForm__field">
      <span class="tagStudioForm__label">${escapeHtml(t(state, "summary_section_label", "detail section"))}</span>
      <span class="tagStudioForm__readonly">${escapeHtml(displayValue(record && record.project_subfolder))}</span>
    </div>
  `;

  state.runtimeStateNode.textContent = state.rebuildPending
    ? t(state, "summary_rebuild_needed", "source changed; rebuild pending")
    : t(state, "summary_rebuild_current", "source and runtime not yet diverged in this session");
}

function setLoadedRecord(state, detailUid, record, options = {}) {
  state.currentDetailUid = detailUid;
  state.currentWorkId = normalizeWorkId(record && record.work_id);
  state.currentRecord = record;
  state.currentLookup = options.lookup || state.currentLookup;
  state.currentRecordHash = normalizeText(options.recordHash || state.currentRecordHash);
  state.baselineDraft = buildDraftFromRecord(record);
  state.draft = { ...state.baselineDraft };
  applyDraftToInputs(state);
  applyReadonly(state);
  syncUrl(detailUid);
  setTextWithState(state.contextNode, t(state, "context_loaded", "Editing source metadata for detail {detail_uid}.", { detail_uid: detailUid }));
  setTextWithState(state.statusNode, t(state, "save_status_loaded", "Loaded detail {detail_uid}.", { detail_uid: detailUid }));
  setTextWithState(state.warningNode, "");
  if (!options.keepResult) setTextWithState(state.resultNode, "");
  updateEditorState(state);
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
  if (!dirty && !errors.size && !state.resultNode.textContent && hasRecord) {
    setTextWithState(state.statusNode, t(state, "save_status_loaded", "Loaded detail {detail_uid}.", { detail_uid: state.currentDetailUid }));
  }

  state.saveButton.disabled = !hasRecord || state.isSaving || errors.size > 0 || !dirty || !state.serverAvailable;
  state.buildButton.disabled = !hasRecord || state.isSaving || state.isBuilding || errors.size > 0 || !state.serverAvailable;
}

function onFieldInput(state, fieldKey) {
  const node = state.fieldNodes.get(fieldKey);
  if (!node) return;
  state.draft[fieldKey] = node.value;
  updateEditorState(state);
}

function t(state, key, fallback, tokens = null) {
  return getStudioText(state.config, `catalogue_work_detail_editor.${key}`, fallback, tokens);
}

async function refreshBuildPreview(state) {
  if (!state.currentWorkId || !state.serverAvailable) {
    state.buildPreview = null;
    setTextWithState(state.buildImpactNode, "");
    return;
  }
  try {
    const response = await postJson(CATALOGUE_WRITE_ENDPOINTS.buildPreview, { work_id: state.currentWorkId });
    state.buildPreview = response && response.build ? response.build : null;
    setTextWithState(state.buildImpactNode, formatBuildPreview(state, state.buildPreview));
  } catch (error) {
    state.buildPreview = null;
    setTextWithState(
      state.buildImpactNode,
      `${t(state, "build_preview_failed", "Build preview unavailable.")} ${normalizeText(error && error.message)}`.trim(),
      "error"
    );
  }
}

async function saveCurrentDetail(state) {
  if (!state.currentRecord) return;
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
  state.saveButton.disabled = true;
  state.buildButton.disabled = true;
  setTextWithState(state.statusNode, t(state, "save_status_saving", "Saving source record…"));
  setTextWithState(state.resultNode, "");

  try {
    const response = await postJson(CATALOGUE_WRITE_ENDPOINTS.saveWorkDetail, buildPayload(state));
    const record = response && response.record && typeof response.record === "object" ? response.record : null;
    if (!record) throw new Error("save response missing record");
    state.detailSearchByUid.set(state.currentDetailUid, {
      detail_uid: state.currentDetailUid,
      work_id: normalizeText(record.work_id),
      detail_id: normalizeText(record.detail_id),
      title: normalizeText(record.title),
      status: normalizeText(record.status)
    });
    state.rebuildPending = Boolean(response.changed);
    const lookup = await loadDetailLookupRecord(state, state.currentDetailUid);
    const lookupRecord = lookup && lookup.work_detail && typeof lookup.work_detail === "object" ? lookup.work_detail : record;
    setLoadedRecord(state, state.currentDetailUid, lookupRecord, {
      recordHash: response.record_hash || normalizeText(lookup && lookup.record_hash) || "",
      keepResult: true,
      lookup
    });
    await refreshBuildPreview(state);
    const savedAt = normalizeText(response.saved_at_utc || utcTimestamp());
    const resultText = response.changed
      ? t(state, "save_result_success", "Source saved at {saved_at}. Rebuild needed to update the parent work output.", { saved_at: savedAt })
      : t(state, "save_result_unchanged", "Source already matches the current form values.");
    setTextWithState(state.resultNode, resultText, response.changed ? "success" : "");
    setTextWithState(state.statusNode, t(state, "save_status_loaded", "Loaded detail {detail_uid}.", { detail_uid: state.currentDetailUid }), "success");
  } catch (error) {
    const isConflict = Number(error && error.status) === 409;
    const message = isConflict
      ? t(state, "save_status_conflict", "Source record changed since this page loaded. Reload the detail before saving again.")
      : `${t(state, "save_status_failed", "Source save failed.")} ${normalizeText(error && error.message)}`.trim();
    setTextWithState(state.statusNode, message, "error");
  } finally {
    state.isSaving = false;
    updateEditorState(state);
  }
}

async function buildCurrentDetail(state) {
  if (!state.currentRecord || !state.currentWorkId || !state.serverAvailable) return;
  state.isBuilding = true;
  updateEditorState(state);
  setTextWithState(state.statusNode, t(state, "build_status_running", "Running scoped rebuild…"));
  setTextWithState(state.resultNode, "");
  try {
    const response = await postJson(CATALOGUE_WRITE_ENDPOINTS.buildApply, { work_id: state.currentWorkId });
    state.rebuildPending = false;
    await refreshBuildPreview(state);
    const completedAt = normalizeText(response.completed_at_utc || utcTimestamp());
    setTextWithState(
      state.resultNode,
      t(state, "build_result_success", "Runtime rebuilt at {completed_at}. Build Activity updated.", { completed_at: completedAt }),
      "success"
    );
    setTextWithState(state.statusNode, t(state, "build_status_success", "Scoped rebuild completed."), "success");
  } catch (error) {
    setTextWithState(
      state.statusNode,
      `${t(state, "build_status_failed", "Scoped rebuild failed.")} ${normalizeText(error && error.message)}`.trim(),
      "error"
    );
  } finally {
    state.isBuilding = false;
    updateEditorState(state);
  }
}

async function saveAndBuildCurrentDetail(state) {
  if (!state.currentRecord) return;
  if (draftHasChanges(state)) {
    await saveCurrentDetail(state);
    if (!state.currentRecord || draftHasChanges(state)) return;
    if (state.statusNode.dataset.state === "error") return;
  }
  await buildCurrentDetail(state);
}

async function openDetailByUid(state, requestedDetailUid) {
  const detailUid = normalizeDetailUid(requestedDetailUid);
  if (!detailUid) {
    renderSearchMatches(state, [], t(state, "search_empty", "Enter a detail id."));
    return;
  }

  const searchRecord = state.detailSearchByUid.get(detailUid);
  if (!searchRecord) {
    const matches = getSearchMatches(state, requestedDetailUid);
    if (matches.length) renderSearchMatches(state, matches);
    else renderSearchMatches(state, [], t(state, "unknown_detail_error", "Unknown detail id: {detail_uid}.", { detail_uid: detailUid }));
    return;
  }

  state.searchNode.value = detailUid;
  setPopupVisibility(state, false);
  state.rebuildPending = false;
  const lookup = await loadDetailLookupRecord(state, detailUid);
  const record = lookup && lookup.work_detail && typeof lookup.work_detail === "object" ? lookup.work_detail : null;
  if (!record) {
    throw new Error(`detail lookup missing record for ${detailUid}`);
  }
  setLoadedRecord(state, detailUid, record, {
    recordHash: normalizeText(lookup.record_hash) || await computeRecordHash(record),
    lookup
  });
  await refreshBuildPreview(state);
}

async function init() {
  const root = document.getElementById("catalogueWorkDetailRoot");
  const loadingNode = document.getElementById("catalogueWorkDetailLoading");
  const emptyNode = document.getElementById("catalogueWorkDetailEmpty");
  const fieldsNode = document.getElementById("catalogueWorkDetailFields");
  const readonlyNode = document.getElementById("catalogueWorkDetailReadonly");
  const summaryNode = document.getElementById("catalogueWorkDetailSummary");
  const runtimeStateNode = document.getElementById("catalogueWorkDetailRuntimeState");
  const buildImpactNode = document.getElementById("catalogueWorkDetailBuildImpact");
  const searchNode = document.getElementById("catalogueWorkDetailSearchGlobal");
  const popupNode = document.getElementById("catalogueWorkDetailPopup");
  const popupListNode = document.getElementById("catalogueWorkDetailPopupList");
  const openButton = document.getElementById("catalogueWorkDetailOpen");
  const saveButton = document.getElementById("catalogueWorkDetailSave");
  const buildButton = document.getElementById("catalogueWorkDetailBuild");
  const saveModeNode = document.getElementById("catalogueWorkDetailSaveMode");
  const contextNode = document.getElementById("catalogueWorkDetailContext");
  const statusNode = document.getElementById("catalogueWorkDetailStatus");
  const warningNode = document.getElementById("catalogueWorkDetailWarning");
  const resultNode = document.getElementById("catalogueWorkDetailResult");
  const metaNode = document.getElementById("catalogueWorkDetailMeta");
  if (!root || !loadingNode || !emptyNode || !fieldsNode || !readonlyNode || !summaryNode || !runtimeStateNode || !buildImpactNode || !searchNode || !popupNode || !popupListNode || !openButton || !saveButton || !buildButton || !saveModeNode || !contextNode || !statusNode || !warningNode || !resultNode || !metaNode) {
    return;
  }

  const state = {
    config: null,
    detailSearchByUid: new Map(),
    currentLookup: null,
    currentDetailUid: "",
    currentWorkId: "",
    currentRecord: null,
    currentRecordHash: "",
    baselineDraft: null,
    draft: {},
    validationErrors: new Map(),
    rebuildPending: false,
    buildPreview: null,
    isSaving: false,
    isBuilding: false,
    serverAvailable: false,
    fieldNodes: new Map(),
    fieldStatusNodes: new Map(),
    readonlyNodes: new Map(),
    searchNode,
    popupNode,
    popupListNode,
    saveButton,
    buildButton,
    saveModeNode,
    contextNode,
    statusNode,
    warningNode,
    resultNode,
    summaryNode,
    runtimeStateNode,
    buildImpactNode,
    metaNode
  };

  EDITABLE_FIELDS.forEach((field) => renderField(field, fieldsNode, state));
  READONLY_FIELDS.forEach((field) => renderReadonlyField(field, readonlyNode, state));

  try {
    const config = await loadStudioConfig();
    state.config = config;
    searchNode.placeholder = t(state, "search_placeholder", "find detail by id");
    openButton.textContent = t(state, "open_button", "Open");
    saveButton.textContent = t(state, "save_button", "Save Source");
    buildButton.textContent = t(state, "build_button", "Save + Rebuild");

    const [detailsPayload, serverAvailable] = await Promise.all([
      loadStudioLookupJson(config, "catalogue_lookup_work_detail_search", { cache: "no-store" }),
      probeCatalogueHealth()
    ]);

    const detailItems = Array.isArray(detailsPayload && detailsPayload.items) ? detailsPayload.items : [];
    detailItems.forEach((record) => {
      if (!record || typeof record !== "object") return;
      const detailUid = normalizeText(record.detail_uid);
      if (!detailUid) return;
      state.detailSearchByUid.set(detailUid, record);
    });
    state.serverAvailable = Boolean(serverAvailable);
    saveModeNode.textContent = buildSaveModeText(config, serverAvailable ? "post" : "offline", (cfg, key, fallback, tokens) => getStudioText(cfg, `catalogue_work_detail_editor.${key}`, fallback, tokens));
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
        renderSearchMatches(state, [], t(state, "search_no_match", "No matching detail ids."));
        return;
      }
      renderSearchMatches(state, matches);
    });

    searchNode.addEventListener("keydown", (event) => {
      if (event.key !== "Enter") return;
      event.preventDefault();
      openDetailByUid(state, searchNode.value).catch((error) => {
        console.warn("catalogue_work_detail_editor: failed to open requested detail", error);
      });
    });

    popupListNode.addEventListener("click", (event) => {
      const button = event.target && event.target.closest ? event.target.closest("[data-detail-uid]") : null;
      if (!button) return;
      openDetailByUid(state, button.getAttribute("data-detail-uid")).catch((error) => {
        console.warn("catalogue_work_detail_editor: failed to open selected detail", error);
      });
    });

    openButton.addEventListener("click", () => {
      openDetailByUid(state, searchNode.value).catch((error) => {
        console.warn("catalogue_work_detail_editor: failed to open requested detail", error);
      });
    });
    saveButton.addEventListener("click", () => saveCurrentDetail(state).catch((error) => {
      console.warn("catalogue_work_detail_editor: unexpected save failure", error);
    }));
    buildButton.addEventListener("click", () => saveAndBuildCurrentDetail(state).catch((error) => {
      console.warn("catalogue_work_detail_editor: unexpected save/build failure", error);
    }));

    document.addEventListener("click", (event) => {
      if (event.target === searchNode || popupNode.contains(event.target)) return;
      setPopupVisibility(state, false);
    });

    const requestedDetailUid = normalizeDetailUid(new URLSearchParams(window.location.search).get("detail"));
    if (requestedDetailUid) {
      openDetailByUid(state, requestedDetailUid).catch((error) => {
        console.warn("catalogue_work_detail_editor: failed to open requested detail", error);
      });
    } else {
      setTextWithState(contextNode, t(state, "missing_detail_param", "Search for a work detail by detail id."));
      updateSummary(state);
      updateEditorState(state);
    }

    root.hidden = false;
    loadingNode.hidden = true;
  } catch (error) {
    console.warn("catalogue_work_detail_editor: init failed", error);
    try {
      const config = await loadStudioConfig();
      loadingNode.textContent = getStudioText(config, "catalogue_work_detail_editor.load_failed_error", "Failed to load catalogue source data for the work detail editor.");
    } catch (_configError) {
      loadingNode.textContent = "Failed to load catalogue source data for the work detail editor.";
    }
  }
}

init();
