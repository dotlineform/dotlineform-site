import {
  getStudioDataPath,
  getStudioRoute,
  getStudioText,
  loadStudioConfig
} from "./studio-config.js";
import {
  fetchJson
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
  { key: "status", label: "status", type: "select", options: ["", "draft", "published"] },
  { key: "published_date", label: "published date", type: "date" },
  { key: "series_ids", label: "series ids", type: "text", description: "comma-separated series ids" },
  { key: "project_folder", label: "project folder", type: "text" },
  { key: "project_filename", label: "project filename", type: "text" },
  { key: "title", label: "title", type: "text" },
  { key: "year", label: "year", type: "number", step: "1" },
  { key: "year_display", label: "year display", type: "text" },
  { key: "medium_type", label: "medium type", type: "text" },
  { key: "medium_caption", label: "medium caption", type: "text" },
  { key: "duration", label: "duration", type: "text" },
  { key: "height_cm", label: "height cm", type: "number", step: "any" },
  { key: "width_cm", label: "width cm", type: "number", step: "any" },
  { key: "depth_cm", label: "depth cm", type: "number", step: "any" },
  { key: "storage_location", label: "storage location", type: "text" },
  { key: "work_prose_file", label: "work prose file", type: "text" },
  { key: "notes", label: "notes", type: "textarea" },
  { key: "provenance", label: "provenance", type: "textarea" },
  { key: "artist", label: "artist", type: "text" }
];

const READONLY_FIELDS = [
  { key: "work_id", label: "work id" },
  { key: "width_px", label: "width px" },
  { key: "height_px", label: "height px" }
];

const STATUS_OPTIONS = new Set(["", "draft", "published"]);
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const SERIES_ID_RE = /^\d+$/;
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

function normalizeSeriesId(value) {
  const digits = normalizeText(value).replace(/\D/g, "");
  if (!digits) return "";
  return digits.padStart(3, "0");
}

async function computeRecordHash(record) {
  if (!globalThis.crypto || !crypto.subtle) return "";
  const json = stableStringify(record);
  const bytes = new TextEncoder().encode(json);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest)).map((value) => value.toString(16).padStart(2, "0")).join("");
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

function seriesIdsToText(value) {
  if (!Array.isArray(value)) return "";
  return value.map((item) => normalizeSeriesId(item)).filter(Boolean).join(", ");
}

function canonicalizeScalar(field, value) {
  const text = normalizeText(value);
  if (field.key === "status") {
    return text.toLowerCase();
  }
  if (field.key === "series_ids") {
    return seriesIdsToText(parseSeriesIds(value));
  }
  if (field.type === "number") {
    return text;
  }
  return text;
}

function parseSeriesIds(value) {
  if (Array.isArray(value)) {
    return dedupeSeriesIds(value.map((item) => normalizeSeriesId(item)).filter(Boolean));
  }
  const text = normalizeText(value);
  if (!text) return [];
  return dedupeSeriesIds(text.split(",").map((item) => normalizeSeriesId(item)).filter(Boolean));
}

function dedupeSeriesIds(items) {
  const seen = new Set();
  const out = [];
  items.forEach((item) => {
    if (!item || seen.has(item)) return;
    seen.add(item);
    out.push(item);
  });
  return out;
}

function formatNumberText(value) {
  const text = normalizeText(value);
  return text;
}

function displayValue(value) {
  const text = normalizeText(value);
  return text || "—";
}

function buildRecordSummary(record) {
  const title = normalizeText(record && record.title);
  const yearDisplay = normalizeText(record && record.year_display);
  if (title && yearDisplay) return `${title} · ${yearDisplay}`;
  return title || yearDisplay || "—";
}

function buildSearchToken(value) {
  const text = normalizeText(value);
  if (!text) return "";
  const digits = text.replace(/\D/g, "");
  return digits || text.toLowerCase();
}

function renderField(field, fieldsNode, state) {
  const wrapper = document.createElement("label");
  wrapper.className = "tagStudioForm__field catalogueWorkForm__field";
  wrapper.htmlFor = `catalogueWorkField-${field.key}`;

  const label = document.createElement("span");
  label.className = "tagStudioForm__label";
  label.textContent = field.label;
  wrapper.appendChild(label);

  let input;
  if (field.type === "textarea") {
    input = document.createElement("textarea");
    input.className = "tagStudio__input tagStudioForm__descriptionInput";
    input.rows = 4;
  } else if (field.type === "select") {
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
    input.type = field.type === "date" ? "date" : (field.type === "number" ? "number" : "text");
    if (field.step) input.step = field.step;
  }

  input.id = `catalogueWorkField-${field.key}`;
  input.dataset.field = field.key;
  if (field.description) {
    input.setAttribute("aria-describedby", `catalogueWorkFieldHelp-${field.key}`);
  }
  wrapper.appendChild(input);

  if (field.description) {
    const help = document.createElement("span");
    help.className = "tagStudioForm__meta catalogueWorkForm__fieldMeta";
    help.id = `catalogueWorkFieldHelp-${field.key}`;
    help.textContent = field.description;
    wrapper.appendChild(help);
  }

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

function setTextWithState(node, text, state = "") {
  if (!node) return;
  node.textContent = text || "";
  if (state) {
    node.dataset.state = state;
  } else {
    delete node.dataset.state;
  }
}

function setPopupVisibility(state, visible) {
  state.popupNode.hidden = !visible;
}

function getSearchMatches(state, rawQuery) {
  const query = buildSearchToken(rawQuery);
  if (!query) return [];
  const matches = [];
  for (const [workId, record] of state.worksById.entries()) {
    if (workId.includes(query)) {
      matches.push({ workId, record });
      continue;
    }
    if (normalizeWorkId(query) && workId === normalizeWorkId(query)) {
      matches.push({ workId, record });
    }
  }
  matches.sort((a, b) => a.workId.localeCompare(b.workId, undefined, { numeric: true, sensitivity: "base" }));
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

  const rows = matches.map(({ workId, record }) => `
    <button type="button" class="tagStudioSuggest__workButton" data-work-id="${escapeHtml(workId)}">
      <span class="tagStudioSuggest__workId">${escapeHtml(workId)}</span>
      <span class="tagStudioSuggest__workTitle">${escapeHtml(buildRecordSummary(record))}</span>
    </button>
  `);
  state.popupListNode.innerHTML = `<div class="tagStudioSuggest__workRows">${rows.join("")}</div>`;
  setPopupVisibility(state, true);
}

function buildDraftFromRecord(record) {
  const draft = {};
  EDITABLE_FIELDS.forEach((field) => {
    if (field.key === "series_ids") {
      draft[field.key] = seriesIdsToText(record[field.key]);
      return;
    }
    draft[field.key] = formatNumberText(record[field.key]);
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

function buildSeriesSummaryHtml(state, seriesIds) {
  if (!seriesIds.length) {
    return escapeHtml(t(state, "context_series_empty", "No series assigned."));
  }

  const seriesBase = getStudioRoute(state.config, "series_page_base");
  return seriesIds.map((seriesId) => {
    const seriesRecord = state.seriesById.get(seriesId);
    const label = seriesRecord && seriesRecord.title ? `${seriesId} · ${seriesRecord.title}` : seriesId;
    const href = `${seriesBase}${encodeURIComponent(seriesId)}/`;
    return `<a href="${escapeHtml(href)}" target="_blank" rel="noopener">${escapeHtml(label)}</a>`;
  }).join("<br>");
}

function updateSummary(state) {
  const record = state.currentRecord;
  state.metaNode.textContent = record
    ? `${record.work_id} · ${buildRecordSummary(record)}`
    : "";

  const seriesIds = parseSeriesIds(state.draft.series_ids);
  const workBase = getStudioRoute(state.config, "works_page_base");
  const publicHref = record ? `${workBase}${encodeURIComponent(record.work_id)}/` : "";
  state.summaryNode.innerHTML = `
    <div class="tagStudioForm__field">
      <span class="tagStudioForm__label">${escapeHtml(t(state, "summary_public_link", "Open public work page"))}</span>
      <span class="tagStudioForm__readonly">
        ${record ? `<a href="${escapeHtml(publicHref)}" target="_blank" rel="noopener">${escapeHtml(record.work_id)}</a>` : "—"}
      </span>
    </div>
    <div class="tagStudioForm__field">
      <span class="tagStudioForm__label">${escapeHtml(t(state, "summary_series_label", "series"))}</span>
      <span class="tagStudioForm__readonly catalogueWorkSummary__series">${buildSeriesSummaryHtml(state, seriesIds)}</span>
    </div>
  `;

  state.runtimeStateNode.textContent = state.rebuildPending
    ? t(state, "summary_rebuild_needed", "source changed; rebuild pending")
    : t(state, "summary_rebuild_current", "source and runtime not yet diverged in this session");
}

function syncUrl(workId) {
  const url = new URL(window.location.href);
  if (workId) {
    url.searchParams.set("work", workId);
  } else {
    url.searchParams.delete("work");
  }
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

  const publishedDate = normalizeText(state.draft.published_date);
  if (publishedDate && !DATE_RE.test(publishedDate)) {
    errors.set("published_date", t(state, "field_invalid_date", "Use YYYY-MM-DD or leave blank."));
  }

  const year = normalizeText(state.draft.year);
  if (year && !/^-?\d+$/.test(year)) {
    errors.set("year", t(state, "field_invalid_year", "Use a whole year or leave blank."));
  }

  ["height_cm", "width_cm", "depth_cm"].forEach((fieldKey) => {
    const value = normalizeText(state.draft[fieldKey]);
    if (value && !Number.isFinite(Number(value))) {
      errors.set(fieldKey, t(state, "field_invalid_number", "Use a number or leave blank."));
    }
  });

  const seriesText = normalizeText(state.draft.series_ids);
  if (seriesText) {
    const parts = seriesText.split(",").map((item) => normalizeText(item)).filter(Boolean);
    for (const part of parts) {
      if (!SERIES_ID_RE.test(part)) {
        errors.set("series_ids", t(state, "field_invalid_series_id", "Use comma-separated numeric series ids."));
        break;
      }
      const normalizedId = normalizeSeriesId(part);
      if (!state.seriesById.has(normalizedId)) {
        errors.set("series_ids", t(state, "field_unknown_series_id", "Unknown series id: {series_id}.", { series_id: normalizedId }));
        break;
      }
    }
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

function buildPayload(state) {
  const draft = state.draft;
  return {
    work_id: state.currentWorkId,
    expected_record_hash: state.currentRecordHash,
    record: {
      status: normalizeText(draft.status).toLowerCase() || null,
      published_date: normalizeText(draft.published_date) || null,
      series_ids: parseSeriesIds(draft.series_ids),
      project_folder: normalizeText(draft.project_folder) || null,
      project_filename: normalizeText(draft.project_filename) || null,
      title: normalizeText(draft.title) || null,
      year: normalizeText(draft.year) ? Number(draft.year) : null,
      year_display: normalizeText(draft.year_display) || null,
      medium_type: normalizeText(draft.medium_type) || null,
      medium_caption: normalizeText(draft.medium_caption) || null,
      duration: normalizeText(draft.duration) || null,
      height_cm: normalizeText(draft.height_cm) ? Number(draft.height_cm) : null,
      width_cm: normalizeText(draft.width_cm) ? Number(draft.width_cm) : null,
      depth_cm: normalizeText(draft.depth_cm) ? Number(draft.depth_cm) : null,
      storage_location: normalizeText(draft.storage_location) || null,
      work_prose_file: normalizeText(draft.work_prose_file) || null,
      notes: normalizeText(draft.notes) || null,
      provenance: normalizeText(draft.provenance) || null,
      artist: normalizeText(draft.artist) || null
    }
  };
}

function setLoadedRecord(state, workId, record, options = {}) {
  state.currentWorkId = workId;
  state.currentRecord = record;
  state.currentRecordHash = normalizeText(options.recordHash || state.currentRecordHash);
  state.baselineDraft = buildDraftFromRecord(record);
  state.draft = { ...state.baselineDraft };
  applyDraftToInputs(state);
  applyReadonly(state);
  syncUrl(workId);
  setTextWithState(state.contextNode, t(state, "context_loaded", "Editing source metadata for work {work_id}.", { work_id: workId }));
  setTextWithState(state.statusNode, t(state, "save_status_loaded", "Loaded work {work_id}.", { work_id: workId }));
  setTextWithState(state.warningNode, "");
  if (!options.keepResult) {
    setTextWithState(state.resultNode, "");
  }
  updateEditorState(state);
}

function updateEditorState(state) {
  const hasRecord = Boolean(state.currentRecord);
  const errors = hasRecord ? validateDraft(state) : new Map();
  state.validationErrors = errors;
  updateFieldMessages(state, errors);
  updateSummary(state);

  const dirty = hasRecord && draftHasChanges(state);
  setTextWithState(state.warningNode, dirty ? t(state, "dirty_warning", "Unsaved source changes.") : "");
  if (!dirty && !errors.size && !state.resultNode.textContent && hasRecord) {
    setTextWithState(state.statusNode, t(state, "save_status_loaded", "Loaded work {work_id}.", { work_id: state.currentWorkId }));
  }

  state.saveButton.disabled = !hasRecord || state.isSaving || errors.size > 0 || !dirty || !state.serverAvailable;
}

function onFieldInput(state, fieldKey) {
  const node = state.fieldNodes.get(fieldKey);
  if (!node) return;
  state.draft[fieldKey] = node.value;
  updateEditorState(state);
}

function t(state, key, fallback, tokens = null) {
  return getStudioText(state.config, `catalogue_work_editor.${key}`, fallback, tokens);
}

async function saveCurrentWork(state) {
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
  setTextWithState(state.statusNode, t(state, "save_status_saving", "Saving source record…"));
  setTextWithState(state.resultNode, "");

  try {
    const payload = buildPayload(state);
    const response = await postJson(CATALOGUE_WRITE_ENDPOINTS.saveWork, payload);
    const record = response && response.record && typeof response.record === "object" ? response.record : null;
    if (!record) {
      throw new Error("save response missing record");
    }
    state.worksById.set(state.currentWorkId, record);
    state.rebuildPending = Boolean(response.changed);
    setLoadedRecord(state, state.currentWorkId, record, {
      recordHash: response.record_hash || "",
      keepResult: true
    });
    const savedAt = normalizeText(response.saved_at_utc || utcTimestamp());
    const resultText = response.changed
      ? t(state, "save_result_success", "Source saved at {saved_at}. Rebuild needed to update public catalogue.", { saved_at: savedAt })
      : t(state, "save_result_unchanged", "Source already matches the current form values.");
    setTextWithState(state.resultNode, resultText, response.changed ? "success" : "");
    setTextWithState(state.statusNode, t(state, "save_status_loaded", "Loaded work {work_id}.", { work_id: state.currentWorkId }), "success");
  } catch (error) {
    const isConflict = Number(error && error.status) === 409;
    const message = isConflict
      ? t(state, "save_status_conflict", "Source record changed since this page loaded. Reload the work before saving again.")
      : `${t(state, "save_status_failed", "Source save failed.")} ${normalizeText(error && error.message)}`.trim();
    setTextWithState(state.statusNode, message, "error");
  } finally {
    state.isSaving = false;
    updateEditorState(state);
  }
}

async function openWorkById(state, requestedWorkId) {
  const workId = normalizeWorkId(requestedWorkId);
  if (!workId) {
    renderSearchMatches(state, [], t(state, "search_empty", "Enter a work id."));
    return;
  }

  const record = state.worksById.get(workId);
  if (!record) {
    const matches = getSearchMatches(state, requestedWorkId);
    if (matches.length) {
      renderSearchMatches(state, matches);
    } else {
      renderSearchMatches(state, [], t(state, "unknown_work_error", "Unknown work id: {work_id}.", { work_id }));
    }
    return;
  }

  state.searchNode.value = workId;
  setPopupVisibility(state, false);
  const recordHash = await computeRecordHash(record);
  setLoadedRecord(state, workId, record, { recordHash });
}

async function init() {
  const root = document.getElementById("catalogueWorkRoot");
  const loadingNode = document.getElementById("catalogueWorkLoading");
  const emptyNode = document.getElementById("catalogueWorkEmpty");
  const fieldsNode = document.getElementById("catalogueWorkFields");
  const readonlyNode = document.getElementById("catalogueWorkReadonly");
  const summaryNode = document.getElementById("catalogueWorkSummary");
  const runtimeStateNode = document.getElementById("catalogueWorkRuntimeState");
  const searchNode = document.getElementById("catalogueWorkSearch");
  const popupNode = document.getElementById("catalogueWorkPopup");
  const popupListNode = document.getElementById("catalogueWorkPopupList");
  const openButton = document.getElementById("catalogueWorkOpen");
  const saveButton = document.getElementById("catalogueWorkSave");
  const saveModeNode = document.getElementById("catalogueWorkSaveMode");
  const contextNode = document.getElementById("catalogueWorkContext");
  const statusNode = document.getElementById("catalogueWorkStatus");
  const warningNode = document.getElementById("catalogueWorkWarning");
  const resultNode = document.getElementById("catalogueWorkResult");
  const metaNode = document.getElementById("catalogueWorkMeta");
  if (!root || !loadingNode || !emptyNode || !fieldsNode || !readonlyNode || !summaryNode || !runtimeStateNode || !searchNode || !popupNode || !popupListNode || !openButton || !saveButton || !saveModeNode || !contextNode || !statusNode || !warningNode || !resultNode || !metaNode) {
    return;
  }

  const state = {
    config: null,
    worksById: new Map(),
    seriesById: new Map(),
    currentWorkId: "",
    currentRecord: null,
    currentRecordHash: "",
    baselineDraft: null,
    draft: {},
    validationErrors: new Map(),
    rebuildPending: false,
    isSaving: false,
    serverAvailable: false,
    fieldNodes: new Map(),
    fieldStatusNodes: new Map(),
    readonlyNodes: new Map(),
    searchNode,
    popupNode,
    popupListNode,
    saveButton,
    saveModeNode,
    contextNode,
    statusNode,
    warningNode,
    resultNode,
    summaryNode,
    runtimeStateNode,
    metaNode
  };

  EDITABLE_FIELDS.forEach((field) => renderField(field, fieldsNode, state));
  READONLY_FIELDS.forEach((field) => renderReadonlyField(field, readonlyNode, state));

  try {
    const config = await loadStudioConfig();
    state.config = config;
    searchNode.placeholder = t(state, "search_placeholder", "find work by id");
    openButton.textContent = t(state, "open_button", "Open");
    saveButton.textContent = t(state, "save_button", "Save Source");

    const [worksPayload, seriesPayload, serverAvailable] = await Promise.all([
      fetchJson(getStudioDataPath(config, "catalogue_works"), { cache: "no-store" }),
      fetchJson(getStudioDataPath(config, "catalogue_series"), { cache: "no-store" }),
      probeCatalogueHealth()
    ]);

    Object.entries(worksPayload && worksPayload.works && typeof worksPayload.works === "object" ? worksPayload.works : {}).forEach(([workId, record]) => {
      if (!record || typeof record !== "object") return;
      state.worksById.set(normalizeWorkId(workId), record);
    });
    Object.entries(seriesPayload && seriesPayload.series && typeof seriesPayload.series === "object" ? seriesPayload.series : {}).forEach(([seriesId, record]) => {
      if (!record || typeof record !== "object") return;
      state.seriesById.set(normalizeSeriesId(seriesId), record);
    });
    state.serverAvailable = Boolean(serverAvailable);
    saveModeNode.textContent = buildSaveModeText(config, serverAvailable ? "post" : "offline", (cfg, key, fallback, tokens) => getStudioText(cfg, `catalogue_work_editor.${key}`, fallback, tokens));
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
        renderSearchMatches(state, [], t(state, "search_no_match", "No matching work ids."));
        return;
      }
      renderSearchMatches(state, matches);
    });

    searchNode.addEventListener("keydown", (event) => {
      if (event.key !== "Enter") return;
      event.preventDefault();
      openWorkById(state, searchNode.value).catch((error) => {
        console.warn("catalogue_work_editor: failed to open requested work", error);
      });
    });

    popupListNode.addEventListener("click", (event) => {
      const button = event.target && event.target.closest ? event.target.closest("[data-work-id]") : null;
      if (!button) return;
      openWorkById(state, button.getAttribute("data-work-id")).catch((error) => {
        console.warn("catalogue_work_editor: failed to open selected work", error);
      });
    });

    openButton.addEventListener("click", () => {
      openWorkById(state, searchNode.value).catch((error) => {
        console.warn("catalogue_work_editor: failed to open requested work", error);
      });
    });
    saveButton.addEventListener("click", () => saveCurrentWork(state).catch((error) => {
      console.warn("catalogue_work_editor: unexpected save failure", error);
    }));

    document.addEventListener("click", (event) => {
      if (event.target === searchNode || popupNode.contains(event.target)) return;
      setPopupVisibility(state, false);
    });

    const requestedWorkId = normalizeWorkId(new URLSearchParams(window.location.search).get("work"));
    if (requestedWorkId) {
      openWorkById(state, requestedWorkId).catch((error) => {
        console.warn("catalogue_work_editor: failed to open requested work", error);
      });
    } else {
      setTextWithState(contextNode, t(state, "missing_work_param", "Search for a work by work id."));
      updateSummary(state);
      updateEditorState(state);
    }

    root.hidden = false;
    loadingNode.hidden = true;
  } catch (error) {
    console.warn("catalogue_work_editor: init failed", error);
    try {
      const config = await loadStudioConfig();
      loadingNode.textContent = getStudioText(config, "catalogue_work_editor.load_failed_error", "Failed to load catalogue source data for the work editor.");
    } catch (_configError) {
      loadingNode.textContent = "Failed to load catalogue source data for the work editor.";
    }
  }
}

init();
