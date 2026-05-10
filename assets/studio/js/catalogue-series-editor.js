import {
  getStudioRoute,
  getStudioText,
  loadStudioConfigWithText
} from "./studio-config.js";
import { loadStudioLookupJson, loadStudioLookupRecordJson } from "./studio-data.js";
import {
  probeCatalogueHealth
} from "./studio-transport.js";
import {
  catalogueReadinessItems,
  catalogueReadinessItemSummary,
  catalogueReadinessTone
} from "./catalogue-editor-readiness.js";
import {
  displayValue
} from "./catalogue-editor-records.js";
import {
  catalogueDeleteDisabled,
  catalogueDirtyWarningText,
  catalogueDraftHasChanges,
  catalogueSaveDisabled
} from "./catalogue-editor-dirty-state.js";
import {
  initializeStudioRouteState,
  setStudioRouteBusy,
  setStudioRouteReady
} from "./studio-route-state.js";
import {
  buildSaveModeText
} from "./tag-studio-save.js";
import {
  SERIES_EDITABLE_FIELDS as EDITABLE_FIELDS,
  SERIES_READONLY_FIELDS as READONLY_FIELDS,
  buildSeriesDraftFromRecord,
  getSeriesTypeOptions,
  normalizeSeriesId,
  normalizeText,
  normalizeWorkId,
  suggestNextSeriesId,
  validateCreateSeriesDraft,
  validateSeriesDraft
} from "./catalogue-series-fields.js";
import {
  addSeriesMember,
  getCurrentSeriesMemberEntries,
  initializeSeriesMembershipState,
  makeSeriesMemberPrimary,
  removeSeriesMember,
  seriesMembershipHasChanges,
  updateSeriesMemberList
} from "./catalogue-series-membership.js";
import {
  applyPublicationChange,
  currentSeriesIsDraft,
  currentSeriesIsPublished,
  deleteCurrentSeries,
  importSeriesProse,
  refreshBuildPreview as refreshSeriesActionBuildPreview,
  saveCurrentSeries
} from "./catalogue-series-actions.js";
import {
  applyInitialSeriesRouteSelection,
  bindSeriesSelectionControls,
  openSeriesById as openSeriesSelectionById,
  setSeriesSelectionPopupVisibility
} from "./catalogue-series-selection.js";

function escapeHtml(value) {
  return normalizeText(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function renderReadiness(state) {
  if (!state.readinessNode || !state.currentRecord) {
    if (state.readinessNode) state.readinessNode.innerHTML = "";
    return;
  }
  const items = catalogueReadinessItems(state.buildPreview);
  if (!items.length) {
    state.readinessNode.innerHTML = "";
    return;
  }

  const actionDisabled = !state.serverAvailable || state.isSaving || state.isBuilding || draftHasChanges(state);
  state.readinessNode.innerHTML = items.map((item) => {
    const summaryItem = catalogueReadinessItemSummary(item, { fallbackSummary: "—" });
    const tone = catalogueReadinessTone(summaryItem.status);
    const proseAction = summaryItem.key === "series_prose";
    const proseActionDisabled = actionDisabled || (proseAction && summaryItem.status !== "ready");
    const disabledNote = proseAction && actionDisabled
      ? (draftHasChanges(state)
        ? t(state, "readiness_save_first", "Save source changes before importing prose.")
        : t(state, "readiness_action_busy", "Wait for the current save or rebuild to finish."))
      : "";
    const proseActionLabel = t(state, "prose_import_button", "Import staged prose");
    return `
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(summaryItem.title)}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay catalogueReadiness__body">
          <span class="catalogueReadiness__summary" data-tone="${escapeHtml(tone)}">${escapeHtml(summaryItem.summary)}</span>
          ${summaryItem.sourcePath ? `<span class="tagStudioForm__meta catalogueReadiness__path">${escapeHtml(summaryItem.sourcePath)}</span>` : ""}
          ${summaryItem.nextStep ? `<span class="tagStudioForm__meta">${escapeHtml(summaryItem.nextStep)}</span>` : ""}
          ${proseAction ? `<div class="catalogueReadiness__actions"><button type="button" class="tagStudio__button" data-prose-import="series" ${proseActionDisabled ? "disabled" : ""}>${escapeHtml(proseActionLabel)}</button></div>` : ""}
          ${disabledNote ? `<span class="tagStudioForm__meta">${escapeHtml(disabledNote)}</span>` : ""}
        </div>
      </div>
    `;
  }).join("");
}

function setTextWithState(node, text, state = "") {
  if (!node) return;
  node.textContent = text || "";
  if (state) node.dataset.state = state;
  else delete node.dataset.state;
}

function routeModeForState(state) {
  if (state.mode === "new") return "new";
  if (state.currentRecord) return "single";
  return "empty";
}

function routeStateDetail(state) {
  return {
    route: "catalogue-series",
    mode: routeModeForState(state),
    service: state.serverAvailable ? "available" : "unavailable",
    recordLoaded: Boolean(state.currentRecord)
  };
}

function syncRouteBusyState(state) {
  setStudioRouteBusy(
    state.root,
    Boolean(state.isSaving || state.isBuilding || state.isDeleting),
    routeStateDetail(state)
  );
}

function markRouteReady(state, ready) {
  setStudioRouteReady(state.root, ready, routeStateDetail(state));
}

function setOpenInputMode(state) {
  state.searchNode.placeholder = t(state, "search_placeholder", "find series by title");
  state.searchNode.setAttribute("aria-label", t(state, "search_label", "Find series by title"));
}

function setNewInputMode(state) {
  state.searchNode.placeholder = t(state, "new_series_id_placeholder", "new series id");
  state.searchNode.setAttribute("aria-label", t(state, "new_series_id_label", "New series id"));
}

function refreshSeriesTypeOptions(state) {
  const node = state.fieldNodes.get("series_type");
  if (!node || node.tagName !== "SELECT") return;
  const current = normalizeText(node.value || state.draft.series_type).toLowerCase();
  node.innerHTML = "";
  const options = state.seriesTypeOptions.slice();
  if (current && !options.includes(current)) options.push(current);
  options.forEach((optionValue) => {
    const option = document.createElement("option");
    option.value = optionValue;
    option.textContent = optionValue || "(blank)";
    node.appendChild(option);
  });
  if (current) node.value = current;
}

function renderField(field, fieldsNode, state) {
  const wrapper = document.createElement(field.readonly ? "div" : "label");
  wrapper.className = "tagStudioForm__field catalogueWorkForm__field";
  if (field.type === "textarea") wrapper.classList.add("tagStudioForm__field--topAligned", "catalogueWorkForm__field--topAligned");
  if (!field.readonly) wrapper.htmlFor = `catalogueSeriesField-${field.key}`;

  const label = document.createElement("span");
  label.className = "tagStudioForm__label";
  label.textContent = field.label;
  wrapper.appendChild(label);

  let input;
  if (field.readonly) {
    input = document.createElement("span");
    input.className = "tagStudio__input tagStudio__input--readonlyDisplay";
  } else if (field.type === "textarea") {
    input = document.createElement("textarea");
    input.className = "tagStudio__input tagStudioForm__descriptionInput";
    input.rows = 4;
  } else if (field.type === "select") {
    input = document.createElement("select");
    input.className = "tagStudio__input";
    const options = field.key === "series_type" ? state.seriesTypeOptions : field.options;
    options.forEach((optionValue) => {
      const option = document.createElement("option");
      option.value = optionValue;
      option.textContent = optionValue || "(blank)";
      input.appendChild(option);
    });
  } else {
    input = document.createElement("input");
    input.className = "tagStudio__input";
    input.type = field.type === "date" ? "date" : "text";
    if (field.type === "number") {
      input.inputMode = field.step && String(field.step).includes(".") ? "decimal" : "numeric";
    }
  }

  input.id = `catalogueSeriesField-${field.key}`;
  input.dataset.field = field.key;
  wrapper.appendChild(input);

  const message = document.createElement("span");
  message.className = "catalogueWorkForm__fieldStatus";
  message.dataset.fieldStatus = field.key;
  wrapper.appendChild(message);

  if (!field.readonly) {
    input.addEventListener("input", () => onFieldInput(state, field.key));
    input.addEventListener("change", () => onFieldInput(state, field.key));
  }
  fieldsNode.appendChild(wrapper);
  state.fieldNodes.set(field.key, input);
  state.fieldStatusNodes.set(field.key, message);
}

function setFieldNodeValue(node, value) {
  const text = normalizeText(value);
  if ("value" in node) {
    node.value = text;
  } else {
    node.textContent = displayValue(text);
  }
}

function getFieldNodeValue(node) {
  if ("value" in node) return node.value;
  return normalizeText(node.textContent);
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
  value.textContent = "—";
  wrapper.appendChild(value);

  readonlyNode.appendChild(wrapper);
  state.readonlyNodes.set(field.key, value);
}

function t(state, key, fallback, tokens = null) {
  return getStudioText(state.config, `catalogue_series_editor.${key}`, fallback, tokens);
}

function buildRecordSummary(record) {
  const title = normalizeText(record && record.title);
  return title || "—";
}

function membershipOptions(state) {
  return {
    text: (key, fallback, tokens = null) => t(state, key, fallback, tokens),
    setTextWithState,
    setFieldNodeValue
  };
}

async function loadSeriesLookupRecord(state, seriesId) {
  return loadStudioLookupRecordJson(state.config, "catalogue_lookup_series_base", seriesId, {
    cache: "no-store",
    catalogueServerAvailable: state.serverAvailable
  });
}

function applyDraftToInputs(state) {
  refreshSeriesTypeOptions(state);
  EDITABLE_FIELDS.forEach((field) => {
    const node = state.fieldNodes.get(field.key);
    if (!node) return;
    setFieldNodeValue(node, normalizeText(state.draft[field.key]));
  });
}

function applyReadonly(state) {
  READONLY_FIELDS.forEach((field) => {
    const node = state.readonlyNodes.get(field.key);
    if (!node) return;
    node.textContent = displayValue(state.currentRecord ? state.currentRecord[field.key] : "");
  });
}

function draftHasChanges(state) {
  return catalogueDraftHasChanges({
    mode: state.mode,
    fields: EDITABLE_FIELDS,
    draft: state.draft,
    baselineDraft: state.baselineDraft,
    extraComparisons: [
      {
        key: "members",
        changed: () => seriesMembershipHasChanges(state)
      }
    ]
  });
}

function validateDraft(state) {
  if (state.mode === "new") {
    return validateCreateSeriesDraft(
      { ...state.draft, series_id: state.searchNode.value },
      {
        seriesById: state.seriesById,
        seriesTypeOptions: state.seriesTypeOptions,
        t: (key, fallback, tokens = null) => t(state, key, fallback, tokens)
      }
    );
  }
  return validateSeriesDraft(state.draft, {
    currentMemberWorkIds: new Set(getCurrentSeriesMemberEntries(state).map((entry) => entry.workId)),
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

function setModeFieldAvailability(state) {
  EDITABLE_FIELDS.forEach((field) => {
    const node = state.fieldNodes.get(field.key);
    if (!node) return;
    let disabled = state.isSaving || state.isBuilding || state.isDeleting;
    if (state.mode === "new" && (field.key === "status" || field.key === "published_date" || field.key === "primary_work_id")) {
      disabled = true;
    }
    if ("disabled" in node) node.disabled = disabled;
    if (field.readonly) {
      if ("disabled" in node) node.disabled = false;
      if ("readOnly" in node) node.readOnly = true;
    }
  });
}

function updatePublishControls(state, { hasRecord, dirty, errors }) {
  const canPublish = hasRecord && state.mode !== "new" && currentSeriesIsDraft(state);
  const canUnpublish = hasRecord && state.mode !== "new" && currentSeriesIsPublished(state);
  const label = canUnpublish
    ? t(state, "unpublish_button", "Unpublish")
    : t(state, "publish_button", "Publish");
  state.publicationButton.textContent = label;
  state.publicationButton.hidden = !(canPublish || canUnpublish);
  state.publicationButton.disabled = !(canPublish || canUnpublish)
    || (canPublish && dirty)
    || (canPublish && errors.size > 0)
    || state.isSaving
    || state.isBuilding
    || state.isDeleting
    || !state.serverAvailable;
}

function syncUrl(seriesId, mode = "") {
  const url = new URL(window.location.href);
  if (seriesId) url.searchParams.set("series", seriesId);
  else url.searchParams.delete("series");
  if (mode) url.searchParams.set("mode", mode);
  else url.searchParams.delete("mode");
  window.history.replaceState({}, "", url.toString());
}

function updateSummary(state) {
  if (state.mode === "new") {
    state.metaNode.textContent = t(state, "new_meta", "draft source record");
    state.summaryNode.innerHTML = `
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(t(state, "new_summary_series_id_label", "series id"))}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(displayValue(state.draft.series_id))}</div>
      </div>
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(t(state, "new_summary_status_label", "status"))}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(t(state, "new_summary_status", "draft source record; not published"))}</div>
      </div>
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(t(state, "new_summary_next_label", "next step"))}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(t(state, "new_summary_next", "Create the draft, then add member works, set primary_work_id, and update the site when ready."))}</div>
      </div>
    `;
    state.runtimeStateNode.textContent = t(state, "new_runtime_state", "Public site update is unavailable until the draft series exists.");
    setTextWithState(state.buildImpactNode, "");
    renderReadiness(state);
    return;
  }

  const record = state.currentRecord;
  state.metaNode.textContent = record ? `${record.series_id} · ${buildRecordSummary(record)}` : "";
  const publicHref = record ? `${getStudioRoute(state.config, "series_page_base")}${encodeURIComponent(record.series_id)}/` : "";
  const memberCount = getCurrentSeriesMemberEntries(state).length;
  state.summaryNode.innerHTML = `
    <div class="tagStudioForm__field">
      <span class="tagStudioForm__label">${escapeHtml(t(state, "summary_public_link", "Open public series page"))}</span>
      <div class="tagStudio__input tagStudio__input--readonlyDisplay">
        ${record ? `<a href="${escapeHtml(publicHref)}" target="_blank" rel="noopener">${escapeHtml(record.series_id)}</a>` : "—"}
      </div>
    </div>
    <div class="tagStudioForm__field">
      <span class="tagStudioForm__label">${escapeHtml(t(state, "summary_member_count", "member works"))}</span>
      <div class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(String(memberCount))}</div>
    </div>
  `;
  state.runtimeStateNode.textContent = state.rebuildPending
    ? t(state, "summary_rebuild_needed", "source saved; site update pending")
    : t(state, "summary_rebuild_current", "source and public catalogue are aligned in this session");
  renderReadiness(state);
}

function updateEditorState(state) {
  const hasRecord = state.mode === "new" ? true : Boolean(state.currentRecord);
  const errors = hasRecord ? validateDraft(state) : new Map();
  state.validationErrors = errors;
  updateFieldMessages(state, errors);
  setModeFieldAvailability(state);
  updateSummary(state);
  updateSeriesMemberList(state, membershipOptions(state));
  if (!hasRecord) setTextWithState(state.buildImpactNode, "");

  const dirty = hasRecord && draftHasChanges(state);
  setTextWithState(state.warningNode, catalogueDirtyWarningText({
    dirty,
    mode: state.mode,
    message: t(state, "dirty_warning", "Unsaved source changes.")
  }));
  if (state.mode === "new" && !state.resultNode.textContent) {
    const firstError = errors.size ? Array.from(errors.values()).find(Boolean) : "";
    setTextWithState(
      state.statusNode,
      firstError || (state.serverAvailable ? "" : t(state, "create_mode_unavailable_hint", "Local catalogue server unavailable. Create is disabled.")),
      firstError ? "error" : state.serverAvailable ? "" : "warn"
    );
  } else if (!dirty && !errors.size && !state.resultNode.textContent && hasRecord) {
    setTextWithState(state.statusNode, t(state, "save_status_loaded", "Loaded series {series_id}.", { series_id: state.currentSeriesId }));
  }

  state.saveButton.textContent = state.mode === "new"
    ? t(state, "create_button", "Create")
    : t(state, "save_button", "Save");
  state.saveButton.disabled = catalogueSaveDisabled({
    hasRecord,
    isSaving: state.isSaving,
    hasErrors: errors.size > 0,
    dirty,
    serverAvailable: state.serverAvailable
  });
  state.deleteButton.disabled = catalogueDeleteDisabled({
    hasRecord: Boolean(state.currentRecord),
    mode: state.mode,
    isSaving: state.isSaving,
    isBuilding: state.isBuilding,
    isDeleting: state.isDeleting,
    serverAvailable: state.serverAvailable
  });
  updatePublishControls(state, { hasRecord, dirty, errors });
  renderReadiness(state);
  syncRouteBusyState(state);
}

function onFieldInput(state, fieldKey) {
  const node = state.fieldNodes.get(fieldKey);
  if (!node) return;
  if (state.mode === "new" && fieldKey === "status") {
    state.draft.status = "draft";
    setFieldNodeValue(node, "draft");
    updateEditorState(state);
    return;
  }
  if (state.mode === "new" && (fieldKey === "published_date" || fieldKey === "primary_work_id")) {
    state.draft[fieldKey] = "";
    setFieldNodeValue(node, "");
    updateEditorState(state);
    return;
  }
  state.draft[fieldKey] = getFieldNodeValue(node);
  updateEditorState(state);
}

function setLoadedSeries(state, seriesId, record, options = {}) {
  state.mode = "single";
  state.currentSeriesId = seriesId;
  state.currentRecord = record;
  state.currentLookup = options.lookup || state.currentLookup;
  state.currentRecordHash = normalizeText(options.recordHash || state.currentRecordHash);
  state.baselineDraft = buildSeriesDraftFromRecord(record);
  state.draft = { ...state.baselineDraft };
  initializeSeriesMembershipState(state, seriesId);
  applyDraftToInputs(state);
  applyReadonly(state);
  syncUrl(seriesId);
  state.memberSearchNode.value = "";
  state.memberAddNode.value = "";
  state.pendingBuildExtraWorkIds = Array.isArray(options.pendingBuildExtraWorkIds) ? options.pendingBuildExtraWorkIds.slice() : [];
  setTextWithState(state.membersStatusNode, "");
  setOpenInputMode(state);
  setTextWithState(state.contextNode, t(state, "context_loaded", "Editing source metadata for series {series_id}.", { series_id: seriesId }));
  setTextWithState(state.statusNode, t(state, "save_status_loaded", "Loaded series {series_id}.", { series_id: seriesId }));
  setTextWithState(state.warningNode, "");
  if (!options.keepResult) setTextWithState(state.resultNode, "");
  updateEditorState(state);
}

function setNewSeriesMode(state, options = {}) {
  state.mode = "new";
  state.currentSeriesId = "";
  state.currentRecord = null;
  state.currentLookup = null;
  state.currentRecordHash = "";
  state.baselineDraft = {};
  state.draft = {};
  EDITABLE_FIELDS.forEach((field) => {
    state.draft[field.key] = "";
  });
  state.draft.series_id = normalizeSeriesId(options.seriesId) || state.nextSuggestedSeriesId || suggestNextSeriesId(Array.from(state.seriesById.values()));
  state.draft.series_type = state.seriesTypeOptions[0] || "primary";
  state.draft.status = "draft";
  state.draft.published_date = "";
  state.draft.primary_work_id = "";
  state.memberSeriesIdsByWorkId = new Map();
  state.baselineMemberSeriesIdsByWorkId = new Map();
  state.pendingBuildExtraWorkIds = [];
  state.rebuildPending = false;
  state.buildPreview = null;
  state.searchNode.value = state.draft.series_id;
  setNewInputMode(state);
  applyDraftToInputs(state);
  READONLY_FIELDS.forEach((field) => {
    const node = state.readonlyNodes.get(field.key);
    if (node) node.textContent = "—";
  });
  setSeriesSelectionPopupVisibility(state, false);
  syncUrl("", "new");
  state.memberSearchNode.value = "";
  state.memberAddNode.value = "";
  setTextWithState(state.membersStatusNode, "");
  setTextWithState(state.contextNode, t(state, "new_context_loaded", "Creating a draft series source record."));
  setTextWithState(state.statusNode, "");
  setTextWithState(state.warningNode, "");
  if (!options.keepResult) setTextWithState(state.resultNode, "");
  updateEditorState(state);
}

function setEmptySearchMode(state, options = {}) {
  state.mode = "single";
  state.currentSeriesId = "";
  state.currentRecord = null;
  state.currentLookup = null;
  state.currentRecordHash = "";
  state.baselineDraft = null;
  state.draft = {};
  EDITABLE_FIELDS.forEach((field) => {
    state.draft[field.key] = "";
  });
  state.memberSeriesIdsByWorkId = new Map();
  state.baselineMemberSeriesIdsByWorkId = new Map();
  state.pendingBuildExtraWorkIds = [];
  state.rebuildPending = false;
  state.buildPreview = null;
  setOpenInputMode(state);
  if (!options.keepSearchValue) state.searchNode.value = "";
  applyDraftToInputs(state);
  READONLY_FIELDS.forEach((field) => {
    const node = state.readonlyNodes.get(field.key);
    if (node) node.textContent = "—";
  });
  setSeriesSelectionPopupVisibility(state, false);
  syncUrl("");
  state.memberSearchNode.value = "";
  state.memberAddNode.value = "";
  setTextWithState(state.membersStatusNode, "");
  setTextWithState(state.contextNode, t(state, "missing_series_param", "Search for a series by title."));
  setTextWithState(state.warningNode, "");
  if (!options.keepResult) setTextWithState(state.resultNode, "");
  updateEditorState(state);
}

function buildSeriesActionContext(state) {
  return {
    text: (key, fallback, tokens = null) => t(state, key, fallback, tokens),
    setTextWithState,
    draftHasChanges: () => draftHasChanges(state),
    validateDraft: () => validateDraft(state),
    updateFieldMessages: (errors) => updateFieldMessages(state, errors),
    updateEditorState: () => updateEditorState(state),
    syncRouteBusyState: () => syncRouteBusyState(state),
    renderReadiness: () => renderReadiness(state),
    setLoadedSeries: (seriesId, record, options = {}) => {
      setLoadedSeries(state, seriesId, record, options);
    },
    openSeriesById: (seriesId) => openSeriesById(state, seriesId)
  };
}

function refreshBuildPreview(state) {
  return refreshSeriesActionBuildPreview(state, buildSeriesActionContext(state));
}

function buildSeriesSelectionContext(state) {
  return {
    text: (key, fallback, tokens = null) => t(state, key, fallback, tokens),
    loadSeriesLookupRecord: (seriesId) => loadSeriesLookupRecord(state, seriesId),
    setLoadedSeries: (seriesId, record, options = {}) => {
      setLoadedSeries(state, seriesId, record, options);
    },
    refreshBuildPreview: () => refreshBuildPreview(state),
    updateEditorState: () => updateEditorState(state),
    saveCurrentSeries: () => saveCurrentSeries(state, buildSeriesActionContext(state)),
    setEmptySearchMode: (options = {}) => setEmptySearchMode(state, options),
    setNewSeriesMode: (options = {}) => setNewSeriesMode(state, options),
    setTextWithState
  };
}

function openSeriesById(state, requestedSeriesId) {
  return openSeriesSelectionById(state, requestedSeriesId, buildSeriesSelectionContext(state));
}

async function init() {
  const root = document.getElementById("catalogueSeriesRoot");
  const loadingNode = document.getElementById("catalogueSeriesLoading");
  const emptyNode = document.getElementById("catalogueSeriesEmpty");
  const fieldsNode = document.getElementById("catalogueSeriesFields");
  const readonlyNode = document.getElementById("catalogueSeriesReadonly");
  const summaryNode = document.getElementById("catalogueSeriesSummary");
  const readinessNode = document.getElementById("catalogueSeriesReadiness");
  const runtimeStateNode = document.getElementById("catalogueSeriesRuntimeState");
  const buildImpactNode = document.getElementById("catalogueSeriesBuildImpact");
  const searchNode = document.getElementById("catalogueSeriesSearch");
  const popupNode = document.getElementById("catalogueSeriesPopup");
  const popupListNode = document.getElementById("catalogueSeriesPopupList");
  const openButton = document.getElementById("catalogueSeriesOpen");
  const newButton = document.getElementById("catalogueSeriesNew");
  const saveButton = document.getElementById("catalogueSeriesSave");
  const publicationButton = document.getElementById("catalogueSeriesPublication");
  const deleteButton = document.getElementById("catalogueSeriesDelete");
  const saveModeNode = document.getElementById("catalogueSeriesSaveMode");
  const contextNode = document.getElementById("catalogueSeriesContext");
  const statusNode = document.getElementById("catalogueSeriesStatus");
  const warningNode = document.getElementById("catalogueSeriesWarning");
  const resultNode = document.getElementById("catalogueSeriesResult");
  const metaNode = document.getElementById("catalogueSeriesMeta");
  const membersHeadingNode = document.getElementById("catalogueSeriesMembersHeading");
  const memberSearchRowNode = document.getElementById("catalogueSeriesMemberSearchRow");
  const memberSearchNode = document.getElementById("catalogueSeriesMemberSearch");
  const memberSearchMetaNode = document.getElementById("catalogueSeriesMemberSearchMeta");
  const memberAddNode = document.getElementById("catalogueSeriesMemberAdd");
  const memberAddButton = document.getElementById("catalogueSeriesMemberAddButton");
  const membersMetaNode = document.getElementById("catalogueSeriesMembersMeta");
  const membersStatusNode = document.getElementById("catalogueSeriesMembersStatus");
  const membersResultsNode = document.getElementById("catalogueSeriesMembersResults");
  if (!root || !loadingNode || !emptyNode || !fieldsNode || !readonlyNode || !summaryNode || !readinessNode || !runtimeStateNode || !buildImpactNode || !searchNode || !popupNode || !popupListNode || !openButton || !newButton || !saveButton || !publicationButton || !deleteButton || !saveModeNode || !contextNode || !statusNode || !warningNode || !resultNode || !metaNode || !membersHeadingNode || !memberSearchRowNode || !memberSearchNode || !memberSearchMetaNode || !memberAddNode || !memberAddButton || !membersMetaNode || !membersStatusNode || !membersResultsNode) {
    return;
  }

  const state = {
    config: null,
    mode: "single",
    seriesById: new Map(),
    workSearchById: new Map(),
    seriesTypeOptions: getSeriesTypeOptions(null),
    nextSuggestedSeriesId: "",
    currentLookup: null,
    currentSeriesId: "",
    currentRecord: null,
    currentRecordHash: "",
    baselineDraft: null,
    draft: {},
    validationErrors: new Map(),
    rebuildPending: false,
    pendingBuildExtraWorkIds: [],
    buildPreview: null,
    isSaving: false,
    isBuilding: false,
    isDeleting: false,
    serverAvailable: false,
    root,
    fieldNodes: new Map(),
    fieldStatusNodes: new Map(),
    readonlyNodes: new Map(),
    memberSeriesIdsByWorkId: new Map(),
    baselineMemberSeriesIdsByWorkId: new Map(),
    searchNode,
    popupNode,
    popupListNode,
    openButton,
    newButton,
    saveButton,
    publicationButton,
    deleteButton,
    saveModeNode,
    contextNode,
    statusNode,
    warningNode,
    resultNode,
    summaryNode,
    readinessNode,
    runtimeStateNode,
    buildImpactNode,
    metaNode,
    memberSearchRowNode,
    memberSearchNode,
    memberSearchMetaNode,
    memberAddNode,
    memberAddButton,
    membersMetaNode,
    membersStatusNode,
    membersResultsNode
  };
  initializeStudioRouteState(root, { route: "catalogue-series" });

  EDITABLE_FIELDS.forEach((field) => renderField(field, fieldsNode, state));
  READONLY_FIELDS.forEach((field) => renderReadonlyField(field, readonlyNode, state));

  try {
    const config = await loadStudioConfigWithText("catalogue_series_editor");
    state.config = config;
    state.seriesTypeOptions = getSeriesTypeOptions(config);
    refreshSeriesTypeOptions(state);
    searchNode.placeholder = t(state, "search_placeholder", "find series by title");
    openButton.textContent = t(state, "open_button", "Open");
    newButton.textContent = t(state, "new_button", "New");
    saveButton.textContent = t(state, "save_button", "Save");
    publicationButton.textContent = t(state, "publish_button", "Publish");
    deleteButton.textContent = t(state, "delete_button", "Delete");
    membersHeadingNode.textContent = t(state, "members_heading", "member works");
    memberSearchNode.placeholder = t(state, "members_search_placeholder", "find member work by id");
    memberAddNode.placeholder = t(state, "members_add_placeholder", "add work by id");
    memberAddButton.textContent = t(state, "members_add_button", "Add");

    const serverAvailable = await probeCatalogueHealth();
    state.serverAvailable = Boolean(serverAvailable);
    saveModeNode.textContent = buildSaveModeText(config, state.serverAvailable ? "post" : "offline", (cfg, key, fallback, tokens) => getStudioText(cfg, `catalogue_series_editor.${key}`, fallback, tokens));
    if (!state.serverAvailable) {
      setTextWithState(statusNode, t(state, "save_mode_unavailable_hint", "Local catalogue server unavailable. Save is disabled."), "warn");
      updateEditorState(state);
      root.hidden = false;
      loadingNode.hidden = true;
      markRouteReady(state, true);
      return;
    }

    const serverReadOptions = { cache: "no-store", catalogueServerAvailable: state.serverAvailable };
    const [seriesPayload, worksPayload] = await Promise.all([
      loadStudioLookupJson(config, "catalogue_lookup_series_search", serverReadOptions),
      loadStudioLookupJson(config, "catalogue_lookup_work_search", serverReadOptions)
    ]);

    const seriesItems = Array.isArray(seriesPayload && seriesPayload.items) ? seriesPayload.items : [];
    seriesItems.forEach((record) => {
      if (!record || typeof record !== "object") return;
      const seriesId = normalizeSeriesId(record.series_id);
      if (!seriesId) return;
      state.seriesById.set(seriesId, record);
    });
    state.nextSuggestedSeriesId = suggestNextSeriesId(seriesItems);
    const workItems = Array.isArray(worksPayload && worksPayload.items) ? worksPayload.items : [];
    workItems.forEach((record) => {
      if (!record || typeof record !== "object") return;
      const workId = normalizeWorkId(record.work_id);
      if (!workId) return;
      state.workSearchById.set(workId, record);
    });
    bindSeriesSelectionControls(state, buildSeriesSelectionContext(state));
    readinessNode.addEventListener("click", (event) => {
      const button = event.target && event.target.closest ? event.target.closest("[data-prose-import]") : null;
      if (!button) return;
      importSeriesProse(state, buildSeriesActionContext(state)).catch((error) => console.warn("catalogue_series_editor: unexpected prose import failure", error));
    });
    newButton.addEventListener("click", () => setNewSeriesMode(state));
    saveButton.addEventListener("click", () => saveCurrentSeries(state, buildSeriesActionContext(state)).catch((error) => console.warn("catalogue_series_editor: unexpected save failure", error)));
    publicationButton.addEventListener("click", () => applyPublicationChange(state, buildSeriesActionContext(state)).catch((error) => console.warn("catalogue_series_editor: unexpected publication failure", error)));
    deleteButton.addEventListener("click", () => deleteCurrentSeries(state, buildSeriesActionContext(state)).catch((error) => console.warn("catalogue_series_editor: unexpected delete failure", error)));
    memberSearchNode.addEventListener("input", () => updateSeriesMemberList(state, membershipOptions(state)));
    memberAddButton.addEventListener("click", () => {
      if (addSeriesMember(state, membershipOptions(state))) updateEditorState(state);
    });
    memberAddNode.addEventListener("keydown", (event) => {
      if (event.key !== "Enter") return;
      event.preventDefault();
      if (addSeriesMember(state, membershipOptions(state))) updateEditorState(state);
    });
    membersResultsNode.addEventListener("click", (event) => {
      const primaryButton = event.target && event.target.closest ? event.target.closest("[data-member-primary]") : null;
      if (primaryButton) {
        if (makeSeriesMemberPrimary(state, normalizeWorkId(primaryButton.getAttribute("data-member-primary")))) updateEditorState(state);
        return;
      }
      const removeButton = event.target && event.target.closest ? event.target.closest("[data-member-remove]") : null;
      if (removeButton) {
        if (removeSeriesMember(state, normalizeWorkId(removeButton.getAttribute("data-member-remove")), membershipOptions(state))) updateEditorState(state);
      }
    });

    await applyInitialSeriesRouteSelection(state, buildSeriesSelectionContext(state));

    root.hidden = false;
    loadingNode.hidden = true;
    markRouteReady(state, true);
  } catch (error) {
    console.warn("catalogue_series_editor: init failed", error);
    try {
      const config = await loadStudioConfigWithText("catalogue_series_editor");
      loadingNode.textContent = getStudioText(config, "catalogue_series_editor.load_failed_error", "Failed to load catalogue source data for the series editor.");
    } catch (_configError) {
      loadingNode.textContent = "Failed to load catalogue source data for the series editor.";
    }
  }
}

init();
