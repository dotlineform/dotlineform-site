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
import {
  NEW_WORK_DETAIL_EDITABLE_FIELDS as EDITABLE_FIELDS,
  buildCreateWorkDetailPayload,
  normalizeDetailUid,
  normalizeText,
  normalizeWorkId,
  suggestNextDetailId as suggestNextDetailIdFromRecords,
  validateCreateWorkDetailDraft
} from "./catalogue-work-detail-fields.js";

function setTextWithState(node, text, state = "") {
  if (!node) return;
  node.textContent = text || "";
  if (state) node.dataset.state = state;
  else delete node.dataset.state;
}

function t(state, key, fallback, tokens = null) {
  return getStudioText(state.config, `catalogue_new_work_detail_editor.${key}`, fallback, tokens);
}

function renderField(field, fieldsNode, state) {
  const wrapper = document.createElement("label");
  wrapper.className = "tagStudioForm__field catalogueWorkForm__field";
  wrapper.htmlFor = `catalogueNewWorkDetailField-${field.key}`;

  const label = document.createElement("span");
  label.className = "tagStudioForm__label";
  label.textContent = field.label;
  wrapper.appendChild(label);

  const input = document.createElement("input");
  input.className = "tagStudio__input";
  input.type = "text";
  input.id = `catalogueNewWorkDetailField-${field.key}`;
  input.dataset.field = field.key;
  wrapper.appendChild(input);

  const message = document.createElement("span");
  message.className = "catalogueWorkForm__fieldStatus";
  wrapper.appendChild(message);

  input.addEventListener("input", () => {
    state.draft[field.key] = input.value;
    if (field.key === "work_id") {
      updateSuggestedDetailId(state);
    }
    updateEditorState(state);
  });
  input.addEventListener("change", () => {
    state.draft[field.key] = input.value;
    if (field.key === "work_id") {
      updateSuggestedDetailId(state);
    }
    updateEditorState(state);
  });

  fieldsNode.appendChild(wrapper);
  state.fieldNodes.set(field.key, input);
  state.fieldStatusNodes.set(field.key, message);
}

function suggestNextDetailId(state, workId) {
  return suggestNextDetailIdFromRecords(state.detailByUid, workId);
}

function updateSuggestedDetailId(state) {
  const workId = normalizeWorkId(state.draft.work_id);
  state.suggestedDetailId = suggestNextDetailId(state, workId);
  const detailIdNode = state.fieldNodes.get("detail_id");
  if (detailIdNode && !normalizeText(detailIdNode.value) && state.suggestedDetailId) {
    state.draft.detail_id = state.suggestedDetailId;
    detailIdNode.value = state.suggestedDetailId;
  }
}

function validateDraft(state) {
  return validateCreateWorkDetailDraft(state.draft, {
    workById: state.workById,
    detailByUid: state.detailByUid,
    t: (key, fallback, tokens = null) => t(state, key, fallback, tokens)
  });
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
  return buildCreateWorkDetailPayload(state.draft);
}

function updateEditorState(state) {
  const errors = validateDraft(state);
  updateFieldMessages(state, errors);
  state.validationErrors = errors;
  const suggestion = state.suggestedDetailId ? t(state, "suggested_detail_id", "Suggested next detail id: {detail_id}.", { detail_id: state.suggestedDetailId }) : "";
  state.summaryNode.textContent = t(state, "draft_summary", "New details are saved as draft. After create, open the detail editor to add remaining metadata and rebuild from the parent work when ready.") + (suggestion ? ` ${suggestion}` : "");
  state.mediaGuidanceNode.textContent = t(state, "media_guidance", "Source media placement stays unchanged. Use the existing project subfolder and filename conventions rather than uploading media here.");
  const hasChanges = EDITABLE_FIELDS.some((field) => normalizeText(state.draft[field.key]));
  setTextWithState(state.warningNode, hasChanges ? t(state, "dirty_warning", "Unsaved draft detail metadata.") : "");
  state.createButton.disabled = state.isSaving || errors.size > 0 || !state.serverAvailable;
}

async function createDetail(state) {
  const errors = validateDraft(state);
  updateFieldMessages(state, errors);
  if (errors.size > 0) {
    setTextWithState(state.statusNode, t(state, "create_status_validation_error", "Fix validation errors before creating the draft detail."), "error");
    updateEditorState(state);
    return;
  }

  state.isSaving = true;
  updateEditorState(state);
  setTextWithState(state.statusNode, t(state, "create_status_saving", "Creating draft detail…"));
  setTextWithState(state.resultNode, "");

  try {
    const response = await postJson(CATALOGUE_WRITE_ENDPOINTS.createWorkDetail, buildPayload(state));
    const detailUid = normalizeText(response && response.detail_uid);
    const route = getStudioRoute(state.config, "catalogue_work_detail_editor");
    setTextWithState(state.resultNode, t(state, "create_result_success", "Created draft detail {detail_uid}. Opening detail editor…", { detail_uid: detailUid }), "success");
    setTextWithState(state.statusNode, t(state, "create_status_success", "Created draft detail {detail_uid}.", { detail_uid: detailUid }), "success");
    window.location.assign(`${route}?detail=${encodeURIComponent(detailUid)}`);
  } catch (error) {
    setTextWithState(state.statusNode, `${t(state, "create_status_failed", "Draft detail create failed.")} ${normalizeText(error && error.message)}`.trim(), "error");
  } finally {
    state.isSaving = false;
    updateEditorState(state);
  }
}

async function init() {
  const root = document.getElementById("catalogueNewWorkDetailRoot");
  const loadingNode = document.getElementById("catalogueNewWorkDetailLoading");
  const fieldsNode = document.getElementById("catalogueNewWorkDetailFields");
  const saveModeNode = document.getElementById("catalogueNewWorkDetailSaveMode");
  const contextNode = document.getElementById("catalogueNewWorkDetailContext");
  const statusNode = document.getElementById("catalogueNewWorkDetailStatus");
  const warningNode = document.getElementById("catalogueNewWorkDetailWarning");
  const resultNode = document.getElementById("catalogueNewWorkDetailResult");
  const summaryNode = document.getElementById("catalogueNewWorkDetailSummary");
  const mediaGuidanceNode = document.getElementById("catalogueNewWorkDetailMediaGuidance");
  const createButton = document.getElementById("catalogueNewWorkDetailCreate");
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
    detailByUid: new Map(),
    suggestedDetailId: "",
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

    const [workPayload, detailPayload, serverAvailable] = await Promise.all([
      loadStudioLookupJson(config, "catalogue_lookup_work_search", { cache: "no-store" }),
      loadStudioLookupJson(config, "catalogue_lookup_work_detail_search", { cache: "no-store" }),
      probeCatalogueHealth()
    ]);

    const workItems = Array.isArray(workPayload && workPayload.items) ? workPayload.items : [];
    workItems.forEach((record) => {
      const workId = normalizeWorkId(record && record.work_id);
      if (!workId) return;
      state.workById.set(workId, record);
    });
    const detailItems = Array.isArray(detailPayload && detailPayload.items) ? detailPayload.items : [];
    detailItems.forEach((record) => {
      const detailUid = normalizeDetailUid(record && record.work_id, record && record.detail_id);
      if (!detailUid) return;
      state.detailByUid.set(detailUid, record);
    });

    const requestedWorkId = normalizeWorkId(new URLSearchParams(window.location.search).get("work"));
    if (requestedWorkId) {
      state.draft.work_id = requestedWorkId;
      const workIdNode = state.fieldNodes.get("work_id");
      if (workIdNode) workIdNode.value = requestedWorkId;
      updateSuggestedDetailId(state);
    }

    state.serverAvailable = Boolean(serverAvailable);
    saveModeNode.textContent = buildSaveModeText(config, serverAvailable ? "post" : "offline", (cfg, key, fallback, tokens) => getStudioText(cfg, `catalogue_new_work_detail_editor.${key}`, fallback, tokens));
    if (requestedWorkId) {
      setTextWithState(contextNode, t(state, "context_hint", "Create a draft detail under the selected work. Media files remain in the existing source path workflow and can be added later."));
    } else {
      setTextWithState(contextNode, t(state, "missing_work_param", "Open this page from a work editor or provide a work id."));
    }
    if (!state.serverAvailable) {
      setTextWithState(statusNode, t(state, "save_mode_unavailable_hint", "Local catalogue server unavailable. Create is disabled."), "warn");
    }

    createButton.addEventListener("click", () => {
      createDetail(state).catch((error) => console.warn("catalogue_new_work_detail_editor: unexpected create failure", error));
    });

    updateEditorState(state);
    root.hidden = false;
    loadingNode.hidden = true;
  } catch (error) {
    console.warn("catalogue_new_work_detail_editor: init failed", error);
    loadingNode.textContent = "Failed to load new work detail editor.";
  }
}

init();
