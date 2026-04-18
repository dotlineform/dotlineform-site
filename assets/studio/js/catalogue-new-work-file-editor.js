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
  { key: "filename", label: "filename", type: "text" },
  { key: "label", label: "label", type: "text" }
];

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function normalizeWorkId(value) {
  const digits = normalizeText(value).replace(/\D/g, "");
  if (!digits) return "";
  return digits.padStart(5, "0");
}

function setTextWithState(node, text, state = "") {
  if (!node) return;
  node.textContent = text || "";
  if (state) node.dataset.state = state;
  else delete node.dataset.state;
}

function t(state, key, fallback, tokens = null) {
  return getStudioText(state.config, `catalogue_new_work_file_editor.${key}`, fallback, tokens);
}

function renderField(field, fieldsNode, state) {
  const wrapper = document.createElement("label");
  wrapper.className = "tagStudioForm__field catalogueWorkForm__field";
  const label = document.createElement("span");
  label.className = "tagStudioForm__label";
  label.textContent = field.label;
  wrapper.appendChild(label);
  const input = document.createElement("input");
  input.className = "tagStudio__input";
  input.type = "text";
  wrapper.appendChild(input);
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
  if (!workId) errors.set("work_id", t(state, "field_required_work_id", "Enter a parent work id."));
  else if (!state.workById.has(workId)) errors.set("work_id", t(state, "field_unknown_work_id", "Unknown work id: {work_id}.", { work_id }));
  if (!normalizeText(state.draft.filename)) errors.set("filename", t(state, "field_required_filename", "Enter a filename."));
  if (!normalizeText(state.draft.label)) errors.set("label", t(state, "field_required_label", "Enter a label."));
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
  const workId = normalizeWorkId(state.draft.work_id);
  return {
    work_id: workId,
    record: {
      work_id: workId,
      filename: normalizeText(state.draft.filename) || null,
      label: normalizeText(state.draft.label) || null,
      status: "draft"
    }
  };
}

function updateEditorState(state) {
  const errors = validateDraft(state);
  updateFieldMessages(state, errors);
  state.createButton.disabled = state.isSaving || errors.size > 0 || !state.serverAvailable;
  const hasChanges = EDITABLE_FIELDS.some((field) => normalizeText(state.draft[field.key]));
  setTextWithState(state.warningNode, hasChanges ? t(state, "dirty_warning", "Unsaved draft file metadata.") : "");
  state.summaryNode.textContent = t(state, "draft_summary", "New file records are saved as draft. After create, open the file editor to set publish metadata and rebuild the parent work when ready.");
  state.guidanceNode.textContent = t(state, "guidance", "This only creates catalogue metadata. File placement remains in the existing project path workflow.");
}

async function createRecord(state) {
  const errors = validateDraft(state);
  updateFieldMessages(state, errors);
  if (errors.size > 0) {
    setTextWithState(state.statusNode, t(state, "create_status_validation_error", "Fix validation errors before creating the draft file."), "error");
    return;
  }
  state.isSaving = true;
  updateEditorState(state);
  setTextWithState(state.statusNode, t(state, "create_status_saving", "Creating draft file…"));
  setTextWithState(state.resultNode, "");
  try {
    const response = await postJson(CATALOGUE_WRITE_ENDPOINTS.createWorkFile, buildPayload(state));
    const fileUid = normalizeText(response && response.file_uid);
    const route = getStudioRoute(state.config, "catalogue_work_file_editor");
    setTextWithState(state.resultNode, t(state, "create_result_success", "Created draft file {file_uid}. Opening file editor…", { file_uid }), "success");
    window.location.assign(`${route}?file=${encodeURIComponent(fileUid)}`);
  } catch (error) {
    setTextWithState(state.statusNode, `${t(state, "create_status_failed", "Draft file create failed.")} ${normalizeText(error && error.message)}`.trim(), "error");
  } finally {
    state.isSaving = false;
    updateEditorState(state);
  }
}

async function init() {
  const root = document.getElementById("catalogueNewWorkFileRoot");
  const loadingNode = document.getElementById("catalogueNewWorkFileLoading");
  const fieldsNode = document.getElementById("catalogueNewWorkFileFields");
  const saveModeNode = document.getElementById("catalogueNewWorkFileSaveMode");
  const contextNode = document.getElementById("catalogueNewWorkFileContext");
  const statusNode = document.getElementById("catalogueNewWorkFileStatus");
  const warningNode = document.getElementById("catalogueNewWorkFileWarning");
  const resultNode = document.getElementById("catalogueNewWorkFileResult");
  const summaryNode = document.getElementById("catalogueNewWorkFileSummary");
  const guidanceNode = document.getElementById("catalogueNewWorkFileGuidance");
  const createButton = document.getElementById("catalogueNewWorkFileCreate");
  if (!root || !loadingNode || !fieldsNode || !saveModeNode || !contextNode || !statusNode || !warningNode || !resultNode || !summaryNode || !guidanceNode || !createButton) return;

  const state = {
    config: null,
    draft: {},
    fieldNodes: new Map(),
    fieldStatusNodes: new Map(),
    workById: new Map(),
    serverAvailable: false,
    isSaving: false,
    warningNode,
    statusNode,
    resultNode,
    summaryNode,
    guidanceNode,
    createButton
  };

  EDITABLE_FIELDS.forEach((field) => {
    state.draft[field.key] = "";
    renderField(field, fieldsNode, state);
  });

  try {
    const config = await loadStudioConfig();
    state.config = config;
    createButton.textContent = t(state, "create_button", "Create Draft File");
    const [workPayload, serverAvailable] = await Promise.all([
      loadStudioLookupJson(config, "catalogue_lookup_work_search", { cache: "no-store" }),
      probeCatalogueHealth()
    ]);
    const items = Array.isArray(workPayload && workPayload.items) ? workPayload.items : [];
    items.forEach((record) => {
      const workId = normalizeWorkId(record && record.work_id);
      if (workId) state.workById.set(workId, record);
    });
    const requestedWorkId = normalizeWorkId(new URLSearchParams(window.location.search).get("work"));
    if (requestedWorkId) {
      state.draft.work_id = requestedWorkId;
      const node = state.fieldNodes.get("work_id");
      if (node) node.value = requestedWorkId;
    }
    state.serverAvailable = Boolean(serverAvailable);
    saveModeNode.textContent = buildSaveModeText(config, serverAvailable ? "post" : "offline", (cfg, key, fallback, tokens) => getStudioText(cfg, `catalogue_new_work_file_editor.${key}`, fallback, tokens));
    setTextWithState(contextNode, requestedWorkId ? t(state, "context_hint", "Create a draft file record for the selected work.") : t(state, "missing_work_param", "Open this page from a work editor or provide a work id."));
    if (!state.serverAvailable) {
      setTextWithState(statusNode, t(state, "save_mode_unavailable_hint", "Local catalogue server unavailable. Create is disabled."), "warn");
    }
    createButton.addEventListener("click", () => {
      createRecord(state).catch((error) => console.warn("catalogue_new_work_file_editor: unexpected create failure", error));
    });
    updateEditorState(state);
    root.hidden = false;
    loadingNode.hidden = true;
  } catch (error) {
    console.warn("catalogue_new_work_file_editor: init failed", error);
    loadingNode.textContent = "Failed to load new work file editor.";
  }
}

init();
