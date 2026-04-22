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
  { key: "url", label: "url", type: "text" },
  { key: "label", label: "label", type: "text" },
  { key: "status", label: "status", type: "select", options: ["", "draft", "published"] },
  { key: "published_date", label: "published date", type: "date" }
];

const READONLY_FIELDS = [
  { key: "link_uid", label: "link id" },
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
  return getStudioText(state.config, `catalogue_work_link_editor.${key}`, fallback, tokens);
}

function buildRecordSummary(record) {
  const label = normalizeText(record && record.label);
  const url = normalizeText(record && record.url);
  const workId = normalizeText(record && record.work_id);
  if (label && url) return `${label} · ${url} · work ${workId || "—"}`;
  return label || url || (workId ? `work ${workId}` : "—");
}

function getSearchMatches(state, rawQuery) {
  const query = buildSearchToken(rawQuery);
  if (!query) return [];
  const matches = [];
  for (const [linkUid, record] of state.linkSearchByUid.entries()) {
    const label = normalizeText(record && record.label).toLowerCase();
    const url = normalizeText(record && record.url).toLowerCase();
    const workId = normalizeText(record && record.work_id);
    if (linkUid.toLowerCase().includes(query) || label.includes(query) || url.includes(query) || workId.includes(query)) {
      matches.push({ linkUid, record });
    }
  }
  matches.sort((a, b) => a.linkUid.localeCompare(b.linkUid, undefined, { numeric: true, sensitivity: "base" }));
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
  const rows = matches.map(({ linkUid, record }) => `
    <button type="button" class="tagStudioSuggest__workButton" data-link-uid="${escapeHtml(linkUid)}">
      <span class="tagStudioSuggest__workId">${escapeHtml(linkUid)}</span>
      <span class="tagStudioSuggest__workTitle">${escapeHtml(buildRecordSummary(record))}</span>
    </button>
  `);
  state.popupListNode.innerHTML = `<div class="tagStudioSuggest__workRows">${rows.join("")}</div>`;
  setPopupVisibility(state, true);
}

function renderField(field, fieldsNode, state) {
  const wrapper = document.createElement("label");
  wrapper.className = "tagStudioForm__field catalogueWorkForm__field";
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
  wrapper.appendChild(input);
  const message = document.createElement("span");
  message.className = "catalogueWorkForm__fieldStatus";
  wrapper.appendChild(message);
  input.addEventListener("input", () => onFieldInput(state, field.key, input.value));
  input.addEventListener("change", () => onFieldInput(state, field.key, input.value));
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

async function loadWorkLinkLookupRecord(state, linkUid) {
  return loadStudioLookupRecordJson(state.config, "catalogue_lookup_work_link_base", linkUid, { cache: "no-store" });
}

function buildDraftFromRecord(record) {
  const draft = {};
  EDITABLE_FIELDS.forEach((field) => { draft[field.key] = normalizeText(record[field.key]); });
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
  if (!normalizeText(state.draft.url)) errors.set("url", t(state, "field_required_url", "Enter a URL."));
  if (!normalizeText(state.draft.label)) errors.set("label", t(state, "field_required_label", "Enter a label."));
  const status = normalizeText(state.draft.status).toLowerCase();
  if (!STATUS_OPTIONS.has(status)) errors.set("status", t(state, "field_invalid_status", "Use blank, draft, or published."));
  const publishedDate = normalizeText(state.draft.published_date);
  if (publishedDate && !DATE_RE.test(publishedDate)) errors.set("published_date", t(state, "field_invalid_date", "Use YYYY-MM-DD or leave blank."));
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
    link_uid: state.currentLinkUid,
    expected_record_hash: state.currentRecordHash,
    apply_build: applyBuildRequested(state),
    record: {
      link_uid: state.currentLinkUid,
      work_id: state.currentWorkId,
      url: normalizeText(state.draft.url) || null,
      label: normalizeText(state.draft.label) || null,
      status: normalizeText(state.draft.status).toLowerCase() || null,
      published_date: normalizeText(state.draft.published_date) || null
    }
  };
}

function applyBuildRequested(state) {
  return Boolean(state.applyBuildNode && state.applyBuildNode.checked);
}

function updatePublishControls(state, { hasRecord, dirty, errors }) {
  const showUpdate = hasRecord && state.rebuildPending;
  state.buildButton.hidden = !showUpdate;
  state.buildButton.disabled = !showUpdate || dirty || errors.size > 0 || state.isSaving || state.isBuilding || state.isDeleting || !state.serverAvailable;
  if (state.runtimeActionsNode) {
    state.runtimeActionsNode.hidden = !showUpdate;
  }
  if (state.applyBuildNode) {
    state.applyBuildNode.disabled = !hasRecord || state.isSaving || state.isBuilding || state.isDeleting || !state.serverAvailable;
  }
}

function applySaveBuildOutcome(state, response) {
  const build = response && response.build && typeof response.build === "object" ? response.build : null;
  if (!response || !response.build_requested || !build) {
    state.rebuildPending = Boolean(response && response.changed);
    return { kind: response && response.changed ? "saved" : "unchanged", stamp: normalizeText(response && response.saved_at_utc) || utcTimestamp() };
  }
  if (build.ok) {
    state.rebuildPending = false;
    return { kind: "saved_and_updated", stamp: normalizeText(build.completed_at_utc || response.saved_at_utc) || utcTimestamp() };
  }
  state.rebuildPending = true;
  return {
    kind: "saved_update_failed",
    stamp: normalizeText(response.saved_at_utc) || utcTimestamp(),
    error: normalizeText(build.error)
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
  state.metaNode.textContent = record ? `${record.link_uid} · ${displayValue(record.label)}` : "";
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
    ? t(state, "summary_rebuild_needed", "source saved; site update pending")
    : t(state, "summary_rebuild_current", "source and public catalogue are aligned in this session");
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
  state.deleteButton.disabled = !hasRecord || state.isSaving || state.isBuilding || state.isDeleting || !state.serverAvailable;
  updatePublishControls(state, { hasRecord, dirty, errors });
}

function openWorkLinkByUid(state, linkUid) {
  const normalizedLinkUid = normalizeText(linkUid);
  if (!normalizedLinkUid) return;
  const route = getStudioRoute(state.config, "catalogue_work_link_editor");
  window.location.assign(`${route}?link=${encodeURIComponent(normalizedLinkUid)}`);
}

function openRequestedSearch(state, rawValue) {
  const matches = getSearchMatches(state, rawValue);
  const exactMatch = matches.find(({ linkUid }) => normalizeText(linkUid).toLowerCase() === normalizeText(rawValue).toLowerCase());
  const selected = exactMatch || matches[0];
  if (!selected) {
    renderSearchMatches(state, [], t(state, "search_no_match", "No matching work links."));
    return;
  }
  openWorkLinkByUid(state, selected.linkUid);
}

function setLoadedRecord(state, linkUid, record, options = {}) {
  state.currentLinkUid = linkUid;
  state.currentRecord = record;
  state.currentWorkId = normalizeText(record && record.work_id);
  state.currentLookup = options.lookup || state.currentLookup;
  state.currentRecordHash = normalizeText(options.recordHash || state.currentRecordHash);
  state.baselineDraft = buildDraftFromRecord(record);
  state.draft = { ...state.baselineDraft };
  if (state.applyBuildNode) state.applyBuildNode.checked = true;
  applyDraftToInputs(state);
  applyReadonly(state);
  if (state.searchNode) state.searchNode.value = linkUid;
  setTextWithState(state.contextNode, t(state, "context_loaded", "Editing source metadata for work link {link_uid}.", { link_uid: linkUid }));
  setTextWithState(state.statusNode, t(state, "save_status_loaded", "Loaded work link {link_uid}.", { link_uid: linkUid }));
  if (!options.keepResult) setTextWithState(state.resultNode, "");
  updateEditorState(state);
}

function onFieldInput(state, fieldKey, value) {
  state.draft[fieldKey] = value;
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
    return;
  }
  if (!draftHasChanges(state)) {
    if (applyBuildRequested(state) && state.rebuildPending) {
      await buildCurrentWork(state);
      return;
    }
    setTextWithState(state.statusNode, t(state, "save_status_no_changes", "No changes to save."));
    setTextWithState(state.resultNode, t(state, "save_result_unchanged", "Source already matches the current form values."));
    return;
  }
  state.isSaving = true;
  updateEditorState(state);
  setTextWithState(
    state.statusNode,
    applyBuildRequested(state)
      ? t(state, "save_status_saving_and_updating", "Saving source record and updating site…")
      : t(state, "save_status_saving", "Saving source record…")
  );
  setTextWithState(state.resultNode, "");
  try {
    const response = await postJson(CATALOGUE_WRITE_ENDPOINTS.saveWorkLink, buildPayload(state));
    const lookup = await loadWorkLinkLookupRecord(state, state.currentLinkUid);
    const record = lookup && lookup.work_link && typeof lookup.work_link === "object" ? lookup.work_link : response.record;
    setLoadedRecord(state, state.currentLinkUid, record, {
      recordHash: normalizeText(response.record_hash) || normalizeText(lookup && lookup.record_hash) || await computeRecordHash(record),
      keepResult: true,
      lookup
    });
    const outcome = applySaveBuildOutcome(state, response);
    await refreshBuildPreview(state);
    if (outcome.kind === "saved_and_updated") {
      setTextWithState(
        state.resultNode,
        t(state, "save_result_success_applied", "Saved source changes and updated the public catalogue at {saved_at}.", { saved_at: outcome.stamp }),
        "success"
      );
      setTextWithState(state.statusNode, t(state, "build_status_success", "Site update completed."), "success");
    } else if (outcome.kind === "saved_update_failed") {
      setTextWithState(
        state.resultNode,
        t(state, "save_result_success_partial", "Source changes were saved at {saved_at}, but the public catalogue update failed. Retry Update site now.", { saved_at: outcome.stamp }),
        "warn"
      );
      setTextWithState(
        state.statusNode,
        `${t(state, "build_status_failed", "Site update failed.")} ${outcome.error}`.trim(),
        "error"
      );
    } else {
      setTextWithState(
        state.resultNode,
        response.changed
          ? t(state, "save_result_success", "Source saved at {saved_at}. Public catalogue update still pending.", { saved_at: outcome.stamp })
          : t(state, "save_result_unchanged", "Source already matches the current form values."),
        response.changed ? "success" : ""
      );
      setTextWithState(state.statusNode, t(state, "save_status_loaded", "Loaded work link {link_uid}.", { link_uid: state.currentLinkUid }), "success");
    }
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
  setTextWithState(state.statusNode, t(state, "build_status_running", "Updating site…"));
  setTextWithState(state.resultNode, "");
  try {
    const response = await postJson(CATALOGUE_WRITE_ENDPOINTS.buildApply, { work_id: state.currentWorkId });
    state.rebuildPending = false;
    await refreshBuildPreview(state);
    const completedAt = normalizeText(response.completed_at_utc || utcTimestamp());
    setTextWithState(state.resultNode, t(state, "build_result_success", "Public catalogue updated at {completed_at}. Build Activity updated.", { completed_at: completedAt }), "success");
    setTextWithState(state.statusNode, t(state, "build_status_success", "Site update completed."), "success");
  } catch (error) {
    setTextWithState(state.statusNode, `${t(state, "build_status_failed", "Site update failed.")} ${normalizeText(error && error.message)}`.trim(), "error");
  } finally {
    state.isBuilding = false;
    updateEditorState(state);
  }
}

async function deleteCurrentRecord(state) {
  if (!state.currentLinkUid || !state.serverAvailable) return;
  state.isDeleting = true;
  updateEditorState(state);
  setTextWithState(state.statusNode, t(state, "delete_status_running", "Deleting source record…"));
  setTextWithState(state.resultNode, "");
  try {
    await postJson(CATALOGUE_WRITE_ENDPOINTS.deleteWorkLink, {
      link_uid: state.currentLinkUid,
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
  const root = document.getElementById("catalogueWorkLinkRoot");
  const loadingNode = document.getElementById("catalogueWorkLinkLoading");
  const emptyNode = document.getElementById("catalogueWorkLinkEmpty");
  const fieldsNode = document.getElementById("catalogueWorkLinkFields");
  const readonlyNode = document.getElementById("catalogueWorkLinkReadonly");
  const searchNode = document.getElementById("catalogueWorkLinkSearch");
  const popupNode = document.getElementById("catalogueWorkLinkPopup");
  const popupListNode = document.getElementById("catalogueWorkLinkPopupList");
  const openButton = document.getElementById("catalogueWorkLinkOpen");
  const saveModeNode = document.getElementById("catalogueWorkLinkSaveMode");
  const contextNode = document.getElementById("catalogueWorkLinkContext");
  const statusNode = document.getElementById("catalogueWorkLinkStatus");
  const warningNode = document.getElementById("catalogueWorkLinkWarning");
  const resultNode = document.getElementById("catalogueWorkLinkResult");
  const metaNode = document.getElementById("catalogueWorkLinkMeta");
  const runtimeStateNode = document.getElementById("catalogueWorkLinkRuntimeState");
  const buildImpactNode = document.getElementById("catalogueWorkLinkBuildImpact");
  const summaryNode = document.getElementById("catalogueWorkLinkSummary");
  const saveButton = document.getElementById("catalogueWorkLinkSave");
  const buildButton = document.getElementById("catalogueWorkLinkBuild");
  const deleteButton = document.getElementById("catalogueWorkLinkDelete");
  const runtimeActionsNode = buildButton ? buildButton.closest(".catalogueWorkPage__runtimeActions") : null;
  const applyBuildNode = document.getElementById("catalogueWorkLinkApplyBuild");
  const applyBuildLabelNode = document.getElementById("catalogueWorkLinkApplyBuildLabel");
  if (!root || !loadingNode || !emptyNode || !fieldsNode || !readonlyNode || !searchNode || !popupNode || !popupListNode || !openButton || !saveModeNode || !contextNode || !statusNode || !warningNode || !resultNode || !metaNode || !runtimeStateNode || !buildImpactNode || !summaryNode || !saveButton || !buildButton || !deleteButton || !runtimeActionsNode || !applyBuildNode || !applyBuildLabelNode) return;

  const state = {
    config: null,
    linkSearchByUid: new Map(),
    currentLookup: null,
    currentLinkUid: "",
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
    applyBuildNode,
    applyBuildLabelNode,
    runtimeActionsNode,
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
    searchNode.placeholder = t(state, "search_placeholder", "find work link by id, label, URL, or work id");
    openButton.textContent = t(state, "open_button", "Open");
    saveButton.textContent = t(state, "save_button", "Save");
    buildButton.textContent = t(state, "build_button", "Update site now");
    applyBuildLabelNode.textContent = t(state, "build_button", "Update site now");
    deleteButton.textContent = t(state, "delete_button", "Delete");
    const [linksPayload, serverAvailable] = await Promise.all([
      fetchJson(getStudioDataPath(config, "catalogue_work_links"), { cache: "no-store" }),
      probeCatalogueHealth()
    ]);
    const linkRecords = linksPayload && linksPayload.work_links && typeof linksPayload.work_links === "object"
      ? linksPayload.work_links
      : {};
    Object.keys(linkRecords).forEach((key) => {
      const record = linkRecords[key] && typeof linkRecords[key] === "object" ? linkRecords[key] : {};
      const linkUid = normalizeText(record.link_uid || key);
      if (!linkUid) return;
      state.linkSearchByUid.set(linkUid, record);
    });
    state.serverAvailable = Boolean(serverAvailable);
    saveModeNode.textContent = buildSaveModeText(config, serverAvailable ? "post" : "offline", (cfg, key, fallback, tokens) => getStudioText(cfg, `catalogue_work_link_editor.${key}`, fallback, tokens));
    if (!state.serverAvailable) setTextWithState(statusNode, t(state, "save_mode_unavailable_hint", "Local catalogue server unavailable. Save is disabled."), "warn");
    searchNode.addEventListener("input", () => {
      const query = searchNode.value;
      if (!normalizeText(query)) {
        renderSearchMatches(state, [], "");
        return;
      }
      const matches = getSearchMatches(state, query);
      if (!matches.length) {
        renderSearchMatches(state, [], t(state, "search_no_match", "No matching work links."));
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
      const button = event.target && event.target.closest ? event.target.closest("[data-link-uid]") : null;
      if (!button) return;
      openWorkLinkByUid(state, button.getAttribute("data-link-uid"));
    });
    openButton.addEventListener("click", () => {
      openRequestedSearch(state, searchNode.value);
    });
    document.addEventListener("click", (event) => {
      if (event.target === searchNode || popupNode.contains(event.target)) return;
      setPopupVisibility(state, false);
    });
    const linkUid = normalizeText(new URLSearchParams(window.location.search).get("link"));
    if (!linkUid) {
      setTextWithState(contextNode, t(state, "missing_link_param", "Search for a work link by link id, label, URL, or work id."));
      root.hidden = false;
      loadingNode.hidden = true;
      updateEditorState(state);
      return;
    }
    const lookup = await loadWorkLinkLookupRecord(state, linkUid);
    const record = lookup && lookup.work_link && typeof lookup.work_link === "object" ? lookup.work_link : null;
    if (!record) throw new Error(`work link lookup missing record for ${linkUid}`);
    setLoadedRecord(state, linkUid, record, {
      recordHash: normalizeText(lookup.record_hash) || await computeRecordHash(record),
      lookup
    });
    await refreshBuildPreview(state);
    saveButton.addEventListener("click", () => { saveCurrentRecord(state).catch((error) => console.warn("catalogue_work_link_editor: unexpected save failure", error)); });
    buildButton.addEventListener("click", () => { buildCurrentWork(state).catch((error) => console.warn("catalogue_work_link_editor: unexpected build failure", error)); });
    deleteButton.addEventListener("click", () => { deleteCurrentRecord(state).catch((error) => console.warn("catalogue_work_link_editor: unexpected delete failure", error)); });
    root.hidden = false;
    loadingNode.hidden = true;
  } catch (error) {
    console.warn("catalogue_work_link_editor: init failed", error);
    loadingNode.textContent = "Failed to load work link editor.";
  }
}

init();
