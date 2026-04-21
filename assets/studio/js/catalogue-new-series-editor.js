import {
  getStudioRoute,
  getStudioText,
  loadStudioConfig
} from "./studio-config.js";
import { loadStudioLookupJson } from "./studio-data.js";
import {
  CATALOGUE_WRITE_ENDPOINTS,
  postJson,
  probeCatalogueHealth
} from "./studio-transport.js";
import { buildSaveModeText } from "./tag-studio-save.js";

const EDITABLE_FIELDS = [
  { key: "series_id", label: "series id", type: "text" },
  { key: "title", label: "title", type: "text" },
  { key: "series_type", label: "series type", type: "text" },
  { key: "year", label: "year", type: "number", step: "1" },
  { key: "year_display", label: "year display", type: "text" },
  { key: "series_prose_file", label: "series prose file", type: "text" },
  { key: "sort_fields", label: "sort fields", type: "text" },
  { key: "notes", label: "notes", type: "textarea" }
];

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function normalizeSeriesId(value) {
  const digits = normalizeText(value).replace(/\D/g, "");
  if (digits) return digits.padStart(3, "0");
  return normalizeText(value).toLowerCase();
}

function setTextWithState(node, text, state = "") {
  if (!node) return;
  node.textContent = text || "";
  if (state) node.dataset.state = state;
  else delete node.dataset.state;
}

function t(state, key, fallback, tokens = null) {
  return getStudioText(state.config, `catalogue_new_series_editor.${key}`, fallback, tokens);
}

function renderField(field, fieldsNode, state) {
  const wrapper = document.createElement("label");
  wrapper.className = "tagStudioForm__field catalogueWorkForm__field";
  if (field.type === "textarea") wrapper.classList.add("tagStudioForm__field--topAligned", "catalogueWorkForm__field--topAligned");
  wrapper.htmlFor = `catalogueNewSeriesField-${field.key}`;

  const label = document.createElement("span");
  label.className = "tagStudioForm__label";
  label.textContent = field.label;
  wrapper.appendChild(label);

  let input;
  if (field.type === "textarea") {
    input = document.createElement("textarea");
    input.className = "tagStudio__input tagStudioForm__descriptionInput";
    input.rows = 4;
  } else {
    input = document.createElement("input");
    input.className = "tagStudio__input";
    input.type = "text";
    if (field.type === "number") {
      input.inputMode = field.step && String(field.step).includes(".") ? "decimal" : "numeric";
    }
  }

  input.id = `catalogueNewSeriesField-${field.key}`;
  input.dataset.field = field.key;
  wrapper.appendChild(input);

  const message = document.createElement("span");
  message.className = "catalogueWorkForm__fieldStatus";
  message.dataset.fieldStatus = field.key;
  wrapper.appendChild(message);

  input.addEventListener("input", () => {
    state.draft[field.key] = input.value;
    updateEditorState(state);
  });
  input.addEventListener("change", () => {
    state.draft[field.key] = input.value;
    updateEditorState(state);
  });

  fieldsNode.appendChild(wrapper);
  state.fieldNodes.set(field.key, input);
  state.fieldStatusNodes.set(field.key, message);
}

function validateDraft(state) {
  const errors = new Map();
  const seriesId = normalizeSeriesId(state.draft.series_id);
  if (!seriesId) {
    errors.set("series_id", t(state, "field_required_series_id", "Enter a series id."));
  } else if (state.seriesById.has(seriesId)) {
    errors.set("series_id", t(state, "field_duplicate_series_id", "Series id already exists."));
  }

  if (!normalizeText(state.draft.title)) {
    errors.set("title", t(state, "field_required_title", "Enter a title."));
  }

  const year = normalizeText(state.draft.year);
  if (year && !/^-?\d+$/.test(year)) {
    errors.set("year", t(state, "field_invalid_year", "Use a whole year or leave blank."));
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

function updateEditorState(state) {
  const errors = validateDraft(state);
  updateFieldMessages(state, errors);
  state.validationErrors = errors;

  const seriesId = normalizeSeriesId(state.draft.series_id);
  const suggestion = state.nextSuggestedSeriesId ? t(state, "suggested_series_id", "Suggested next id: {series_id}.", { series_id: state.nextSuggestedSeriesId }) : "";
  state.summaryNode.textContent = t(
    state,
    "draft_summary",
    "New series are saved as draft. After create, open the series editor to add member works, set primary_work_id, and run rebuild.",
  ) + (suggestion ? ` ${suggestion}` : "");

  const hasChanges = EDITABLE_FIELDS.some((field) => normalizeText(state.draft[field.key]));
  setTextWithState(state.warningNode, hasChanges ? t(state, "dirty_warning", "Unsaved draft series metadata.") : "");
  state.createButton.disabled = state.isSaving || errors.size > 0 || !state.serverAvailable;
}

function buildPayload(state) {
  return {
    series_id: normalizeSeriesId(state.draft.series_id),
    record: {
      title: normalizeText(state.draft.title) || null,
      series_type: normalizeText(state.draft.series_type) || null,
      status: "draft",
      published_date: null,
      year: normalizeText(state.draft.year) ? Number(state.draft.year) : null,
      year_display: normalizeText(state.draft.year_display) || null,
      primary_work_id: null,
      series_prose_file: normalizeText(state.draft.series_prose_file) || null,
      sort_fields: normalizeText(state.draft.sort_fields) || null,
      notes: normalizeText(state.draft.notes) || null
    }
  };
}

function suggestNextSeriesId(seriesItems) {
  let maxNumericId = 0;
  seriesItems.forEach((record) => {
    const seriesId = normalizeSeriesId(record && record.series_id);
    if (!/^\d+$/.test(seriesId)) return;
    maxNumericId = Math.max(maxNumericId, Number(seriesId));
  });
  if (maxNumericId <= 0) return "001";
  return String(maxNumericId + 1).padStart(3, "0");
}

async function createSeries(state) {
  const errors = validateDraft(state);
  updateFieldMessages(state, errors);
  if (errors.size > 0) {
    setTextWithState(state.statusNode, t(state, "create_status_validation_error", "Fix validation errors before creating the draft series."), "error");
    updateEditorState(state);
    return;
  }

  state.isSaving = true;
  updateEditorState(state);
  setTextWithState(state.statusNode, t(state, "create_status_saving", "Creating draft series…"));
  setTextWithState(state.resultNode, "");

  try {
    const response = await postJson(CATALOGUE_WRITE_ENDPOINTS.createSeries, buildPayload(state));
    const seriesId = normalizeSeriesId(response && response.series_id);
    const seriesTitle = normalizeText(response && response.record && response.record.title);
    const editorRoute = getStudioRoute(state.config, "catalogue_series_editor");
    const targetUrl = `${editorRoute}?series=${encodeURIComponent(seriesId)}`;
    setTextWithState(state.resultNode, t(state, "create_result_success", "Created draft series {series_id}. Opening series editor…", { series_id: seriesId }), "success");
    setTextWithState(state.statusNode, t(state, "create_status_success", "Created draft series {series_id}.", { series_id: seriesId }), "success");
    state.seriesById.set(seriesId, { series_id: seriesId, title: seriesTitle });
    window.location.assign(targetUrl);
  } catch (error) {
    setTextWithState(state.statusNode, `${t(state, "create_status_failed", "Draft series create failed.")} ${normalizeText(error && error.message)}`.trim(), "error");
  } finally {
    state.isSaving = false;
    updateEditorState(state);
  }
}

async function init() {
  const root = document.getElementById("catalogueNewSeriesRoot");
  const loadingNode = document.getElementById("catalogueNewSeriesLoading");
  const emptyNode = document.getElementById("catalogueNewSeriesEmpty");
  const fieldsNode = document.getElementById("catalogueNewSeriesFields");
  const saveModeNode = document.getElementById("catalogueNewSeriesSaveMode");
  const contextNode = document.getElementById("catalogueNewSeriesContext");
  const statusNode = document.getElementById("catalogueNewSeriesStatus");
  const warningNode = document.getElementById("catalogueNewSeriesWarning");
  const resultNode = document.getElementById("catalogueNewSeriesResult");
  const summaryNode = document.getElementById("catalogueNewSeriesSummary");
  const createButton = document.getElementById("catalogueNewSeriesCreate");
  if (!root || !loadingNode || !emptyNode || !fieldsNode || !saveModeNode || !contextNode || !statusNode || !warningNode || !resultNode || !summaryNode || !createButton) {
    return;
  }

  const state = {
    config: null,
    draft: {},
    validationErrors: new Map(),
    fieldNodes: new Map(),
    fieldStatusNodes: new Map(),
    seriesById: new Map(),
    nextSuggestedSeriesId: "",
    serverAvailable: false,
    isSaving: false,
    saveModeNode,
    contextNode,
    statusNode,
    warningNode,
    resultNode,
    summaryNode,
    createButton
  };

  EDITABLE_FIELDS.forEach((field) => {
    state.draft[field.key] = "";
    renderField(field, fieldsNode, state);
  });

  try {
    const config = await loadStudioConfig();
    state.config = config;
    createButton.textContent = t(state, "create_button", "Create");

    const [seriesPayload, serverAvailable] = await Promise.all([
      loadStudioLookupJson(config, "catalogue_lookup_series_search", { cache: "no-store" }),
      probeCatalogueHealth()
    ]);

    const seriesItems = Array.isArray(seriesPayload && seriesPayload.items) ? seriesPayload.items : [];
    seriesItems.forEach((record) => {
      const seriesId = normalizeSeriesId(record && record.series_id);
      if (!seriesId) return;
      state.seriesById.set(seriesId, record);
    });
    state.nextSuggestedSeriesId = suggestNextSeriesId(seriesItems);
    if (state.nextSuggestedSeriesId) {
      state.draft.series_id = state.nextSuggestedSeriesId;
      const seriesIdNode = state.fieldNodes.get("series_id");
      if (seriesIdNode) seriesIdNode.value = state.nextSuggestedSeriesId;
    }

    state.serverAvailable = Boolean(serverAvailable);
    saveModeNode.textContent = buildSaveModeText(config, serverAvailable ? "post" : "offline", (cfg, key, fallback, tokens) => getStudioText(cfg, `catalogue_new_series_editor.${key}`, fallback, tokens));
    setTextWithState(contextNode, t(state, "context_hint", "Create a draft series first. Add member works and primary_work_id in the series editor after save."));
    if (!state.serverAvailable) {
      setTextWithState(statusNode, t(state, "save_mode_unavailable_hint", "Local catalogue server unavailable. Create is disabled."), "warn");
    }

    createButton.addEventListener("click", () => {
      createSeries(state).catch((error) => console.warn("catalogue_new_series_editor: unexpected create failure", error));
    });

    updateEditorState(state);
    root.hidden = false;
    loadingNode.hidden = true;
  } catch (error) {
    console.warn("catalogue_new_series_editor: init failed", error);
    loadingNode.textContent = "Failed to load new series editor.";
  }
}

init();
