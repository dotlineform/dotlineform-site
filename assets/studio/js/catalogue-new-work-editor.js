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
  { key: "work_id", label: "work id", type: "text" },
  { key: "title", label: "title", type: "text" },
  { key: "series_ids", label: "series ids", type: "text", description: "comma-separated series ids" },
  { key: "project_folder", label: "project folder", type: "text" },
  { key: "project_filename", label: "project filename", type: "text" },
  { key: "work_prose_file", label: "work prose file", type: "text" },
  { key: "year", label: "year", type: "number", step: "1" },
  { key: "year_display", label: "year display", type: "text" },
  { key: "medium_type", label: "medium type", type: "text" },
  { key: "medium_caption", label: "medium caption", type: "text" },
  { key: "duration", label: "duration", type: "text" },
  { key: "height_cm", label: "height cm", type: "number", step: "any" },
  { key: "width_cm", label: "width cm", type: "number", step: "any" },
  { key: "depth_cm", label: "depth cm", type: "number", step: "any" },
  { key: "storage_location", label: "storage location", type: "text" },
  { key: "notes", label: "notes", type: "textarea" },
  { key: "provenance", label: "provenance", type: "textarea" },
  { key: "artist", label: "artist", type: "text" }
];

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
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

function parseSeriesIds(value) {
  const text = normalizeText(value);
  if (!text) return [];
  const seen = new Set();
  const out = [];
  text.split(",").map((item) => normalizeSeriesId(item)).filter(Boolean).forEach((seriesId) => {
    if (seen.has(seriesId)) return;
    seen.add(seriesId);
    out.push(seriesId);
  });
  return out;
}

function setTextWithState(node, text, state = "") {
  if (!node) return;
  node.textContent = text || "";
  if (state) node.dataset.state = state;
  else delete node.dataset.state;
}

function t(state, key, fallback, tokens = null) {
  return getStudioText(state.config, `catalogue_new_work_editor.${key}`, fallback, tokens);
}

function renderField(field, fieldsNode, state) {
  const wrapper = document.createElement("label");
  wrapper.className = "tagStudioForm__field catalogueWorkForm__field";
  wrapper.htmlFor = `catalogueNewWorkField-${field.key}`;

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
    input.type = field.type === "number" ? "number" : "text";
    if (field.step) input.step = field.step;
  }

  input.id = `catalogueNewWorkField-${field.key}`;
  input.dataset.field = field.key;
  wrapper.appendChild(input);

  if (field.description) {
    const help = document.createElement("span");
    help.className = "tagStudioForm__meta catalogueWorkForm__fieldMeta";
    help.textContent = field.description;
    wrapper.appendChild(help);
  }

  const message = document.createElement("span");
  message.className = "catalogueWorkForm__fieldStatus";
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
  const workId = normalizeWorkId(state.draft.work_id);
  if (!workId) {
    errors.set("work_id", t(state, "field_required_work_id", "Enter a work id."));
  } else if (state.workById.has(workId)) {
    errors.set("work_id", t(state, "field_duplicate_work_id", "Work id already exists."));
  }
  if (!normalizeText(state.draft.title)) {
    errors.set("title", t(state, "field_required_title", "Enter a title."));
  }
  const year = normalizeText(state.draft.year);
  if (year && !/^-?\d+$/.test(year)) {
    errors.set("year", t(state, "field_invalid_year", "Use a whole year or leave blank."));
  }
  ["height_cm", "width_cm", "depth_cm"].forEach((fieldKey) => {
    const value = normalizeText(state.draft[fieldKey]);
    if (value && !Number.isFinite(Number(value))) {
      errors.set(fieldKey, "Use a number or leave blank.");
    }
  });
  const seriesText = normalizeText(state.draft.series_ids);
  if (seriesText) {
    const parts = seriesText.split(",").map((item) => normalizeText(item)).filter(Boolean);
    for (const part of parts) {
      if (!/^\d+$/.test(part)) {
        errors.set("series_ids", t(state, "field_invalid_series_id", "Use comma-separated numeric series ids."));
        break;
      }
      const seriesId = normalizeSeriesId(part);
      if (!state.seriesById.has(seriesId)) {
        errors.set("series_ids", t(state, "field_unknown_series_id", "Unknown series id: {series_id}.", { series_id }));
        break;
      }
    }
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

function suggestNextWorkId(workItems) {
  let maxNumericId = 0;
  workItems.forEach((record) => {
    const workId = normalizeWorkId(record && record.work_id);
    if (!/^\d+$/.test(workId)) return;
    maxNumericId = Math.max(maxNumericId, Number(workId));
  });
  if (maxNumericId <= 0) return "00001";
  return String(maxNumericId + 1).padStart(5, "0");
}

function buildPayload(state) {
  return {
    work_id: normalizeWorkId(state.draft.work_id),
    record: {
      work_id: normalizeWorkId(state.draft.work_id),
      status: "draft",
      published_date: null,
      series_ids: parseSeriesIds(state.draft.series_ids),
      project_folder: normalizeText(state.draft.project_folder) || null,
      project_filename: normalizeText(state.draft.project_filename) || null,
      title: normalizeText(state.draft.title) || null,
      year: normalizeText(state.draft.year) ? Number(state.draft.year) : null,
      year_display: normalizeText(state.draft.year_display) || null,
      medium_type: normalizeText(state.draft.medium_type) || null,
      medium_caption: normalizeText(state.draft.medium_caption) || null,
      duration: normalizeText(state.draft.duration) || null,
      height_cm: normalizeText(state.draft.height_cm) ? Number(state.draft.height_cm) : null,
      width_cm: normalizeText(state.draft.width_cm) ? Number(state.draft.width_cm) : null,
      depth_cm: normalizeText(state.draft.depth_cm) ? Number(state.draft.depth_cm) : null,
      storage_location: normalizeText(state.draft.storage_location) || null,
      work_prose_file: normalizeText(state.draft.work_prose_file) || null,
      notes: normalizeText(state.draft.notes) || null,
      provenance: normalizeText(state.draft.provenance) || null,
      artist: normalizeText(state.draft.artist) || null
    }
  };
}

function updateEditorState(state) {
  const errors = validateDraft(state);
  updateFieldMessages(state, errors);
  state.validationErrors = errors;
  const suggestion = state.nextSuggestedWorkId ? t(state, "suggested_work_id", "Suggested next id: {work_id}.", { work_id: state.nextSuggestedWorkId }) : "";
  state.summaryNode.textContent = t(state, "draft_summary", "New works are saved as draft. After create, open the work editor to add remaining metadata, details, and rebuild when ready.") + (suggestion ? ` ${suggestion}` : "");
  state.mediaGuidanceNode.textContent = t(state, "media_guidance", "Source media placement stays unchanged. Use the existing project folder and filename conventions rather than uploading media here.");
  const hasChanges = EDITABLE_FIELDS.some((field) => normalizeText(state.draft[field.key]));
  setTextWithState(state.warningNode, hasChanges ? t(state, "dirty_warning", "Unsaved draft work metadata.") : "");
  state.createButton.disabled = state.isSaving || errors.size > 0 || !state.serverAvailable;
}

async function createWork(state) {
  const errors = validateDraft(state);
  updateFieldMessages(state, errors);
  if (errors.size > 0) {
    setTextWithState(state.statusNode, t(state, "create_status_validation_error", "Fix validation errors before creating the draft work."), "error");
    updateEditorState(state);
    return;
  }

  state.isSaving = true;
  updateEditorState(state);
  setTextWithState(state.statusNode, t(state, "create_status_saving", "Creating draft work…"));
  setTextWithState(state.resultNode, "");

  try {
    const response = await postJson(CATALOGUE_WRITE_ENDPOINTS.createWork, buildPayload(state));
    const workId = normalizeWorkId(response && response.work_id);
    const route = getStudioRoute(state.config, "catalogue_work_editor");
    setTextWithState(state.resultNode, t(state, "create_result_success", "Created draft work {work_id}. Opening work editor…", { work_id }), "success");
    setTextWithState(state.statusNode, t(state, "create_status_success", "Created draft work {work_id}.", { work_id }), "success");
    window.location.assign(`${route}?work=${encodeURIComponent(workId)}`);
  } catch (error) {
    setTextWithState(state.statusNode, `${t(state, "create_status_failed", "Draft work create failed.")} ${normalizeText(error && error.message)}`.trim(), "error");
  } finally {
    state.isSaving = false;
    updateEditorState(state);
  }
}

async function init() {
  const root = document.getElementById("catalogueNewWorkRoot");
  const loadingNode = document.getElementById("catalogueNewWorkLoading");
  const fieldsNode = document.getElementById("catalogueNewWorkFields");
  const saveModeNode = document.getElementById("catalogueNewWorkSaveMode");
  const contextNode = document.getElementById("catalogueNewWorkContext");
  const statusNode = document.getElementById("catalogueNewWorkStatus");
  const warningNode = document.getElementById("catalogueNewWorkWarning");
  const resultNode = document.getElementById("catalogueNewWorkResult");
  const summaryNode = document.getElementById("catalogueNewWorkSummary");
  const mediaGuidanceNode = document.getElementById("catalogueNewWorkMediaGuidance");
  const createButton = document.getElementById("catalogueNewWorkCreate");
  if (!root || !loadingNode || !fieldsNode || !saveModeNode || !contextNode || !statusNode || !warningNode || !resultNode || !summaryNode || !mediaGuidanceNode || !createButton) {
    return;
  }

  const state = {
    config: null,
    draft: {},
    validationErrors: new Map(),
    fieldNodes: new Map(),
    fieldStatusNodes: new Map(),
    workById: new Map(),
    seriesById: new Map(),
    nextSuggestedWorkId: "",
    serverAvailable: false,
    isSaving: false,
    statusNode,
    warningNode,
    resultNode,
    summaryNode,
    mediaGuidanceNode,
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

    const [workPayload, seriesPayload, serverAvailable] = await Promise.all([
      loadStudioLookupJson(config, "catalogue_lookup_work_search", { cache: "no-store" }),
      loadStudioLookupJson(config, "catalogue_lookup_series_search", { cache: "no-store" }),
      probeCatalogueHealth()
    ]);

    const workItems = Array.isArray(workPayload && workPayload.items) ? workPayload.items : [];
    workItems.forEach((record) => {
      const workId = normalizeWorkId(record && record.work_id);
      if (!workId) return;
      state.workById.set(workId, record);
    });
    const seriesItems = Array.isArray(seriesPayload && seriesPayload.items) ? seriesPayload.items : [];
    seriesItems.forEach((record) => {
      const seriesId = normalizeSeriesId(record && record.series_id);
      if (!seriesId) return;
      state.seriesById.set(seriesId, record);
    });

    state.nextSuggestedWorkId = suggestNextWorkId(workItems);
    if (state.nextSuggestedWorkId) {
      state.draft.work_id = state.nextSuggestedWorkId;
      const node = state.fieldNodes.get("work_id");
      if (node) node.value = state.nextSuggestedWorkId;
    }

    state.serverAvailable = Boolean(serverAvailable);
    saveModeNode.textContent = buildSaveModeText(config, serverAvailable ? "post" : "offline", (cfg, key, fallback, tokens) => getStudioText(cfg, `catalogue_new_work_editor.${key}`, fallback, tokens));
    setTextWithState(contextNode, t(state, "context_hint", "Create a draft work first. Media files remain in the existing source path workflow and can be added later."));
    if (!state.serverAvailable) {
      setTextWithState(statusNode, t(state, "save_mode_unavailable_hint", "Local catalogue server unavailable. Create is disabled."), "warn");
    }

    createButton.addEventListener("click", () => {
      createWork(state).catch((error) => console.warn("catalogue_new_work_editor: unexpected create failure", error));
    });

    updateEditorState(state);
    root.hidden = false;
    loadingNode.hidden = true;
  } catch (error) {
    console.warn("catalogue_new_work_editor: init failed", error);
    loadingNode.textContent = "Failed to load new work editor.";
  }
}

init();
