import {
  getStudioRoute,
  getStudioText,
  loadStudioConfigWithText
} from "./studio-config.js";
import { loadStudioLookupJson } from "./studio-data.js";
import {
  probeCatalogueHealth
} from "./studio-transport.js";
import {
  previewCatalogueMoment
} from "./catalogue-editor-service-client.js";
import {
  catalogueGeneratedStatusText,
  catalogueReadinessItems,
  catalogueReadinessItemSummary,
  catalogueReadinessTone
} from "./catalogue-editor-readiness.js";
import {
  computeRecordHash,
  displayValue,
  recordsEqual
} from "./catalogue-editor-records.js";
import {
  formatCatalogueBuildPreview
} from "./catalogue-editor-modal-formatters.js";
import {
  catalogueDeleteDisabled,
  catalogueDirtyWarningText
} from "./catalogue-editor-dirty-state.js";
import {
  MOMENT_EDITABLE_FIELDS as EDITABLE_FIELDS,
  MOMENT_READONLY_FIELDS as READONLY_FIELDS,
  normalizeMomentId,
  normalizeMomentRecord,
  normalizeText,
  readMomentDraft,
  validateMomentDraft
} from "./catalogue-moment-fields.js";
import {
  applyMomentImport,
  clearImportPreview,
  currentImportMomentFile,
  previewMomentImport,
  readRequestedImportFile,
  updateImportState,
  writeRequestedImportFile
} from "./catalogue-moment-import.js";
import {
  initializeStudioRouteState,
  setStudioRouteBusy,
  setStudioRouteReady
} from "./studio-route-state.js";
import { buildSaveModeText } from "./tag-studio-save.js";
import {
  applyPublicationChange,
  currentMomentIsDraft,
  currentMomentIsPublished,
  deleteCurrentMoment,
  importMomentProse,
  refreshBuildPreview as refreshMomentActionBuildPreview,
  refreshMomentMedia,
  saveCurrentMoment
} from "./catalogue-moment-actions.js";

const SEARCH_LIMIT = 20;

function escapeHtml(value) {
  return normalizeText(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function setFieldNodeValue(node, value) {
  const text = normalizeText(value);
  if ("value" in node) {
    node.value = text;
  } else {
    node.textContent = displayValue(text, { emptyText: "-" });
  }
}

function getFieldNodeValue(node) {
  if ("value" in node) return node.value;
  return normalizeText(node.textContent);
}

function setTextWithState(node, text, state = "") {
  if (!node) return;
  node.textContent = text || "";
  if (state) node.dataset.state = state;
  else delete node.dataset.state;
}

function routeModeForState(state) {
  if (state.isImportMode) return "import";
  if (state.currentRecord) return "single";
  return "empty";
}

function routeStateDetail(state) {
  return {
    route: "catalogue-moment",
    mode: routeModeForState(state),
    service: state.serverAvailable ? "available" : "unavailable",
    recordLoaded: Boolean(state.currentRecord)
  };
}

function syncRouteBusyState(state) {
  setStudioRouteBusy(
    state.root,
    Boolean(state.isSaving || state.isBuilding || state.isDeleting || state.importIsBusy),
    routeStateDetail(state)
  );
}

function markRouteReady(state, ready) {
  setStudioRouteReady(state.root, ready, routeStateDetail(state));
}

function t(state, key, fallback, tokens = null) {
  return getStudioText(state.config, `catalogue_moment_editor.${key}`, fallback, tokens);
}

function buildImportContext(state) {
  return {
    text: (key, fallback, tokens) => t(state, key, fallback, tokens),
    setTextWithState,
    syncRouteBusyState: () => syncRouteBusyState(state),
    completeImport: ({ momentId, record }) => completeMomentImport(state, momentId, record)
  };
}

function buildActionContext(state) {
  return {
    text: (key, fallback, tokens) => t(state, key, fallback, tokens),
    setTextWithState,
    getFieldNodeValue,
    readDraft: () => readDraft(state),
    validateDraft: () => validateDraft(state),
    draftHasChanges: () => draftHasChanges(state),
    updateEditorState: () => updateDirtyState(state),
    previewMoment: (momentId) => previewMoment(state, momentId),
    renderSummary: () => renderSummary(state),
    renderBuildImpact: () => renderBuildImpact(state),
    fillForm: (record) => fillForm(state, record)
  };
}

function readDraft(state) {
  return readMomentDraft(state, { getFieldNodeValue });
}

function draftHasChanges(state) {
  if (!state.currentRecord) return false;
  return !recordsEqual(readDraft(state), state.currentRecord);
}

function buildSearchRows(state, query) {
  const needle = normalizeText(query).toLowerCase();
  if (!needle) return [];
  return state.momentRows
    .filter((row) => row.search.includes(needle))
    .slice(0, SEARCH_LIMIT);
}

function setPopupVisibility(state, visible) {
  state.popupNode.hidden = !visible;
}

function renderPopup(state) {
  const rows = buildSearchRows(state, state.searchNode.value);
  if (!rows.length) {
    state.popupListNode.innerHTML = `<p class="tagStudio__popupEmpty">${escapeHtml(t(state, "search_no_match", "No matching moment records."))}</p>`;
    setPopupVisibility(state, Boolean(normalizeText(state.searchNode.value)));
    return;
  }
  state.popupListNode.innerHTML = rows.map((row) => `
    <button type="button" class="tagStudio__popupItem" data-moment-id="${escapeHtml(row.moment_id)}">
      <span class="tagStudio__popupTitle">${escapeHtml(row.title || row.moment_id)}</span>
      <span class="tagStudio__popupMeta">${escapeHtml(row.moment_id)}</span>
    </button>
  `).join("");
  setPopupVisibility(state, true);
}

function renderField(field, state) {
  const wrapper = document.createElement(field.readonly ? "div" : "label");
  wrapper.className = "tagStudioForm__field catalogueWorkForm__field";
  if (!field.readonly) wrapper.htmlFor = `catalogueMomentField-${field.key}`;

  const label = document.createElement("span");
  label.className = "tagStudioForm__label";
  label.textContent = field.label;
  wrapper.appendChild(label);

  let input;
  if (field.readonly) {
    input = document.createElement("span");
    input.className = "tagStudio__input tagStudio__input--readonlyDisplay";
  } else if (field.type === "select") {
    input = document.createElement("select");
    input.className = "tagStudio__input";
    field.options.forEach((optionValue) => {
      const option = document.createElement("option");
      option.value = optionValue;
      option.textContent = optionValue;
      input.appendChild(option);
    });
  } else {
    input = document.createElement("input");
    input.className = "tagStudio__input";
    input.type = field.type === "date" ? "date" : "text";
    input.spellcheck = false;
    input.autocomplete = "off";
  }

  input.id = `catalogueMomentField-${field.key}`;
  input.dataset.field = field.key;
  if (!field.readonly) {
    input.addEventListener("input", () => onFieldInput(state, field.key));
    input.addEventListener("change", () => onFieldInput(state, field.key));
  }
  wrapper.appendChild(input);

  const message = document.createElement("span");
  message.className = "catalogueWorkForm__fieldStatus";
  message.dataset.fieldStatus = field.key;
  wrapper.appendChild(message);

  state.fieldsNode.appendChild(wrapper);
  state.fieldNodes.set(field.key, input);
  state.fieldStatusNodes.set(field.key, message);
}

function renderReadonlyField(field, state) {
  const wrapper = document.createElement("div");
  wrapper.className = "tagStudioForm__field";
  wrapper.innerHTML = `
    <span class="tagStudioForm__label">${escapeHtml(field.label)}</span>
    <div class="tagStudio__input tagStudio__input--readonlyDisplay" data-readonly-field="${escapeHtml(field.key)}">-</div>
  `;
  state.readonlyNode.appendChild(wrapper);
  state.readonlyNodes.set(field.key, wrapper.querySelector("[data-readonly-field]"));
}

function fillForm(state, record) {
  EDITABLE_FIELDS.forEach((field) => {
    const node = state.fieldNodes.get(field.key);
    if (!node) return;
    setFieldNodeValue(node, normalizeText(record[field.key]));
  });
  READONLY_FIELDS.forEach((field) => {
    const node = state.readonlyNodes.get(field.key);
    if (node) node.textContent = displayValue(record[field.key], { emptyText: "-" });
  });
}

function clearFieldMessages(state) {
  state.fieldStatusNodes.forEach((node) => setTextWithState(node, ""));
}

function validateDraft(state) {
  clearFieldMessages(state);
  const draft = readDraft(state);
  const errors = validateMomentDraft(draft, {
    t: (key, fallback, tokens) => t(state, key, fallback, tokens)
  });
  errors.forEach((message, key) => {
    const node = state.fieldStatusNodes.get(key);
    if (node) setTextWithState(node, message, "error");
  });
  return { valid: !errors.size, draft };
}

function renderReadiness(state) {
  const items = catalogueReadinessItems(state.buildPreview, { fallbackReadiness: state.previewReadiness });
  if (!items.length) {
    state.readinessNode.innerHTML = "";
    return;
  }
  const actionDisabled = !state.serverAvailable || state.isSaving || state.isBuilding || draftHasChanges(state);
  state.readinessNode.innerHTML = items.map((item) => {
    const summaryItem = catalogueReadinessItemSummary(item);
    const tone = catalogueReadinessTone(summaryItem.status, { missingFileTone: "error" });
    const proseAction = summaryItem.key === "moment_prose";
    const mediaAction = summaryItem.key === "moment_media";
    const proseActionDisabled = actionDisabled || (proseAction && summaryItem.status !== "ready");
    const mediaActionDisabled = actionDisabled || !summaryItem.exists;
    const disabledNote = actionDisabled && (proseAction || mediaAction)
      ? (draftHasChanges(state)
	      ? (mediaAction ? t(state, "media_refresh_save_first", "Save source changes before refreshing media.") : t(state, "dirty_warning", "Unsaved source changes."))
        : t(state, "readiness_action_busy", "Wait for the current save or public update to finish."))
      : "";
    return `
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(summaryItem.title)}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay catalogueReadiness__body">
          <span class="catalogueReadiness__summary" data-tone="${escapeHtml(tone)}">${escapeHtml(summaryItem.summary)}</span>
          ${summaryItem.sourcePath ? `<span class="tagStudioForm__meta catalogueReadiness__path">${escapeHtml(summaryItem.sourcePath)}</span>` : ""}
          ${summaryItem.nextStep ? `<span class="tagStudioForm__meta">${escapeHtml(summaryItem.nextStep)}</span>` : ""}
          ${proseAction ? `<div class="catalogueReadiness__actions"><button type="button" class="tagStudio__button" data-prose-import="moment" ${proseActionDisabled ? "disabled" : ""}>${escapeHtml(t(state, "prose_import_button", "Import staged prose"))}</button></div>` : ""}
          ${mediaAction ? `<div class="catalogueReadiness__actions"><button type="button" class="tagStudio__button" data-media-refresh="moment" ${mediaActionDisabled ? "disabled" : ""}>${escapeHtml(t(state, "media_refresh_button", "Refresh media"))}</button></div>` : ""}
          ${disabledNote ? `<span class="tagStudioForm__meta">${escapeHtml(disabledNote)}</span>` : ""}
        </div>
      </div>
    `;
  }).join("");
}

function renderSummary(state) {
  const preview = state.preview || {};
  const publicUrl = normalizeText(preview.public_url) || `${getStudioRoute(state.config, "moments_page_base")}${state.currentMomentId}/`;
  const fields = [
    { label: "public URL", value: publicUrl },
    { label: "generated", value: catalogueGeneratedStatusText(preview) },
    { label: "source image", value: preview.source_image_exists ? "source image found" : "source image missing" },
    { label: "prose source", value: preview.source_exists ? "source prose found" : "source prose missing" }
  ];
  state.summaryNode.innerHTML = `
    ${fields.map((field) => `
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(field.label)}</span>
        <span class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(displayValue(field.value, { emptyText: "-" }))}</span>
      </div>
    `).join("")}
    <p class="tagStudioForm__impact"><a href="${escapeHtml(publicUrl)}">${escapeHtml(t(state, "summary_public_link", "Open public moment page"))}</a></p>
  `;
  state.runtimeStateNode.textContent = state.needsBuild
    ? t(state, "summary_rebuild_needed", "public update failed in this session")
    : t(state, "summary_rebuild_current", "source and public moment are aligned in this session");
  renderReadiness(state);
}

function setEditModeChrome(state) {
  state.isImportMode = false;
  state.saveButton.hidden = false;
  state.publicationButton.hidden = false;
  state.deleteButton.hidden = false;
  state.importPreviewButton.hidden = true;
  state.importApplyButton.hidden = true;
  state.importSourceNode.hidden = true;
  state.readonlyNode.hidden = false;
  state.runtimeStateNode.hidden = false;
  state.buildImpactNode.hidden = false;
  state.sideHeadingNode.textContent = t(state, "side_heading_current", "current record");
  state.importSourceSummaryNode.textContent = "";
  state.importImageGuidanceNode.textContent = "";
}

function enterImportMode(state, momentFile = "") {
  state.isImportMode = true;
  state.currentMomentId = "";
  state.currentRecord = null;
  state.expectedRecordHash = "";
  state.preview = null;
  state.previewReadiness = null;
  state.buildPreview = null;
  state.needsBuild = false;
  state.searchNode.value = "";
  setPopupVisibility(state, false);
  fillForm(state, {
    moment_id: "",
    title: "",
    status: "draft",
    date: "",
    date_display: "",
    published_date: "",
    source_image_file: "",
    image_alt: ""
  });
  state.readonlyNodes.forEach((node) => {
    node.textContent = "-";
  });
  state.saveButton.hidden = true;
  state.publicationButton.hidden = true;
  state.deleteButton.hidden = true;
  state.importPreviewButton.hidden = false;
  state.importApplyButton.hidden = false;
  state.importSourceNode.hidden = false;
  state.readonlyNode.hidden = true;
  state.runtimeStateNode.hidden = true;
  state.buildImpactNode.hidden = true;
  state.sideHeadingNode.textContent = t(state, "side_heading_import", "import preview");
  if (normalizeText(momentFile)) state.importFileNode.value = momentFile;
  setTextWithState(state.contextNode, t(state, "import_context_hint", "Import a staged moment markdown file as draft source, then review and publish it from this editor."));
  setTextWithState(state.statusNode, t(state, "import_mode_loaded", "Preview the staged moment file below."));
  setTextWithState(state.warningNode, "");
  setTextWithState(state.resultNode, "");
  writeRequestedImportFile(state.importFileNode.value);
  clearFieldMessages(state);
  clearImportPreview(state, buildImportContext(state));
  updateDirtyState(state);
}

function upsertMomentRow(state, momentId, record) {
  const normalized = normalizeMomentRecord(momentId, record);
  state.moments.set(normalized.moment_id, normalized);
  const row = state.momentRows.find((item) => item.moment_id === normalized.moment_id);
  const nextRow = {
    ...normalized,
    search: `${normalized.moment_id} ${normalizeText(normalized.title).toLowerCase()}`
  };
  if (row) Object.assign(row, nextRow);
  else state.momentRows.push(nextRow);
  state.momentRows.sort((a, b) => a.moment_id.localeCompare(b.moment_id));
}

async function completeMomentImport(state, momentId, record) {
  upsertMomentRow(state, momentId, record);
  state.searchNode.value = momentId;
  await openMoment(state, momentId);
}

function updatePublicationControls(state, { dirty, validation }) {
  const hasRecord = Boolean(state.currentRecord);
  const actionContext = buildActionContext(state);
  const canPublish = hasRecord && currentMomentIsDraft(state, actionContext);
  const canUnpublish = hasRecord && currentMomentIsPublished(state, actionContext);
  const label = canUnpublish
    ? t(state, "unpublish_button", "Unpublish")
    : t(state, "publish_button", "Publish");
  state.publicationButton.textContent = label;
  state.publicationButton.hidden = !(canPublish || canUnpublish);
  state.publicationButton.disabled = !(canPublish || canUnpublish)
    || (canPublish && dirty)
    || (canPublish && validation && !validation.valid)
    || state.isSaving
    || state.isBuilding
    || state.isDeleting
    || !state.serverAvailable;
}

function updateDirtyState(state) {
  const dirty = draftHasChanges(state);
  const validation = state.currentRecord ? validateDraft(state) : { valid: true, draft: null };
  if (!state.currentRecord) clearFieldMessages(state);
  setTextWithState(state.warningNode, catalogueDirtyWarningText({
    dirty,
    mode: "single",
    message: t(state, "dirty_warning", "Unsaved source changes.")
  }), dirty ? "warning" : "");
  state.saveButton.disabled = !state.serverAvailable || state.isSaving || state.isDeleting || !state.currentRecord;
  state.deleteButton.disabled = catalogueDeleteDisabled({
    hasRecord: Boolean(state.currentRecord),
    isSaving: state.isSaving,
    isBuilding: state.isBuilding,
    isDeleting: state.isDeleting,
    serverAvailable: state.serverAvailable
  });
  updatePublicationControls(state, { dirty, validation });
  renderReadiness(state);
  updateImportState(state, buildImportContext(state));
}

function onFieldInput(state) {
  if (state.isImportMode) {
    clearImportPreview(state, buildImportContext(state));
    updateDirtyState(state);
    return;
  }
  validateDraft(state);
  updateDirtyState(state);
}

async function previewMoment(state, momentId) {
  if (!state.serverAvailable) return;
  try {
    const payload = await previewCatalogueMoment({ moment_id: momentId });
    state.currentRecord = payload.record || state.currentRecord;
    state.expectedRecordHash = payload.record_hash || state.expectedRecordHash;
    state.preview = payload.preview || null;
    state.previewReadiness = payload.readiness || null;
    state.buildPreview = payload.build || null;
    renderBuildImpact(state);
  } catch (error) {
    console.warn("catalogue_moment_editor: preview failed", error);
    state.serverAvailable = false;
    setTextWithState(state.statusNode, t(state, "save_mode_unavailable_hint", "Local catalogue server unavailable. Save is disabled."), "warning");
    state.saveModeNode.textContent = buildSaveModeText(
      state.config,
      "offline",
      (cfg, key, fallback, tokens) => getStudioText(cfg, `catalogue_moment_editor.${key}`, fallback, tokens)
    );
    updateDirtyState(state);
  }
}

async function openMoment(state, momentId, options = {}) {
  const normalizedId = normalizeMomentId(momentId);
  const record = state.moments.get(normalizedId);
  if (!record) {
    setTextWithState(state.statusNode, t(state, "unknown_moment_error", "Unknown moment id: {moment_id}.", { moment_id: normalizedId }), "error");
    return;
  }
  setEditModeChrome(state);
  clearImportPreview(state, buildImportContext(state));
  state.currentMomentId = normalizedId;
  state.currentRecord = normalizeMomentRecord(normalizedId, record);
  state.expectedRecordHash = await computeRecordHash(state.currentRecord);
  state.preview = null;
  state.previewReadiness = null;
  state.buildPreview = null;
  state.needsBuild = false;
  fillForm(state, state.currentRecord);
  setTextWithState(state.contextNode, t(state, "context_loaded", "Editing source metadata for moment {moment_id}.", { moment_id: normalizedId }));
  setTextWithState(state.statusNode, t(state, "save_status_loaded", "Loaded moment {moment_id}.", { moment_id: normalizedId }), "success");
  setTextWithState(state.resultNode, "");
  if (!options.skipUrl) {
    const url = new URL(window.location.href);
    url.searchParams.set("moment", normalizedId);
    url.searchParams.delete("file");
    window.history.replaceState({}, "", url.toString());
  }
  await previewMoment(state, normalizedId);
  fillForm(state, state.currentRecord);
  validateDraft(state);
  renderSummary(state);
  updateDirtyState(state);
}

function renderBuildImpact(state) {
  if (!currentMomentIsPublished(state, buildActionContext(state))) {
    state.buildImpactNode.textContent = t(state, "build_preview_unpublished", "Public update unavailable while the moment is not published.");
    return;
  }
  if (!state.buildPreview) {
    state.buildImpactNode.textContent = "";
    return;
  }
  state.buildImpactNode.textContent = formatCatalogueBuildPreview(state.buildPreview, {
    text: (key, fallback, tokens) => t(state, key, fallback, tokens),
    target: "moment",
    fallbackMomentId: state.currentMomentId,
    defaultTemplate: "Public update preview: moment {moment_ids}; catalogue search {search_rebuild}."
  });
}

function buildMomentRows(payload) {
  const moments = payload && payload.moments && typeof payload.moments === "object" ? payload.moments : {};
  return Object.entries(moments).map(([momentId, record]) => {
    const normalized = normalizeMomentRecord(momentId, record);
    return {
      ...normalized,
      search: `${normalized.moment_id} ${normalizeText(normalized.title).toLowerCase()}`
    };
  }).sort((a, b) => a.moment_id.localeCompare(b.moment_id));
}

function bindEvents(state) {
  state.searchNode.addEventListener("input", () => renderPopup(state));
  state.searchNode.addEventListener("focus", () => renderPopup(state));
  state.popupListNode.addEventListener("click", (event) => {
    const button = event.target && event.target.closest ? event.target.closest("[data-moment-id]") : null;
    if (!button) return;
    state.searchNode.value = button.dataset.momentId || "";
    setPopupVisibility(state, false);
    openMoment(state, state.searchNode.value).catch((error) => console.warn("catalogue_moment_editor: open failed", error));
  });
  state.openButton.addEventListener("click", () => {
    const value = normalizeMomentId(state.searchNode.value);
    if (!value) {
      setTextWithState(state.statusNode, t(state, "search_empty", "Enter a moment id or title."), "warning");
      return;
    }
    const exact = state.moments.has(value) ? value : "";
    const match = exact || (buildSearchRows(state, value)[0] || {}).moment_id || "";
    openMoment(state, match || value).catch((error) => console.warn("catalogue_moment_editor: open failed", error));
  });
  state.newButton.addEventListener("click", () => enterImportMode(state));
  state.saveButton.addEventListener("click", () => saveCurrentMoment(state, buildActionContext(state)));
  state.publicationButton.addEventListener("click", () => applyPublicationChange(state, buildActionContext(state)).catch((error) => console.warn("catalogue_moment_editor: publication failed", error)));
  state.deleteButton.addEventListener("click", () => deleteCurrentMoment(state, buildActionContext(state)).catch((error) => console.warn("catalogue_moment_editor: delete failed", error)));
  state.importFileNode.addEventListener("input", () => {
    writeRequestedImportFile(state.importFileNode.value);
    setTextWithState(state.importWarningNode, "");
    setTextWithState(state.importResultNode, "");
    clearImportPreview(state, buildImportContext(state));
  });
  state.importPreviewButton.addEventListener("click", () => {
    previewMomentImport(state, buildImportContext(state)).catch((error) => console.warn("catalogue_moment_editor: import preview failed", error));
  });
  state.importApplyButton.addEventListener("click", () => {
    applyMomentImport(state, buildImportContext(state)).catch((error) => console.warn("catalogue_moment_editor: import apply failed", error));
  });
  state.readinessNode.addEventListener("click", (event) => {
    const mediaButton = event.target && event.target.closest ? event.target.closest("[data-media-refresh]") : null;
    if (mediaButton) {
      refreshMomentMedia(state, buildActionContext(state)).catch((error) => console.warn("catalogue_moment_editor: media refresh failed", error));
      return;
    }
    const button = event.target && event.target.closest ? event.target.closest("[data-prose-import]") : null;
    if (!button) return;
    importMomentProse(state, buildActionContext(state)).catch((error) => console.warn("catalogue_moment_editor: prose import failed", error));
  });
}

async function init() {
  const root = document.getElementById("catalogueMomentRoot");
  const loadingNode = document.getElementById("catalogueMomentLoading");
  const emptyNode = document.getElementById("catalogueMomentEmpty");
  const state = {
    config: await loadStudioConfigWithText("catalogue_moment_editor"),
    root,
    loadingNode,
    emptyNode,
    searchNode: document.getElementById("catalogueMomentSearch"),
    popupNode: document.getElementById("catalogueMomentPopup"),
    popupListNode: document.getElementById("catalogueMomentPopupList"),
    openButton: document.getElementById("catalogueMomentOpen"),
    newButton: document.getElementById("catalogueMomentNew"),
    saveModeNode: document.getElementById("catalogueMomentSaveMode"),
    contextNode: document.getElementById("catalogueMomentContext"),
    statusNode: document.getElementById("catalogueMomentStatus"),
    warningNode: document.getElementById("catalogueMomentWarning"),
    resultNode: document.getElementById("catalogueMomentResult"),
    saveButton: document.getElementById("catalogueMomentSave"),
    publicationButton: document.getElementById("catalogueMomentPublication"),
    deleteButton: document.getElementById("catalogueMomentDelete"),
    fieldsNode: document.getElementById("catalogueMomentFields"),
    readonlyNode: document.getElementById("catalogueMomentReadonly"),
    sideHeadingNode: document.getElementById("catalogueMomentSideHeading"),
    summaryNode: document.getElementById("catalogueMomentSummary"),
    readinessNode: document.getElementById("catalogueMomentReadiness"),
    runtimeStateNode: document.getElementById("catalogueMomentRuntimeState"),
    buildImpactNode: document.getElementById("catalogueMomentBuildImpact"),
    importSourceNode: document.getElementById("catalogueMomentImportSource"),
    importStatusNode: document.getElementById("catalogueMomentStatus"),
    importWarningNode: document.getElementById("catalogueMomentWarning"),
    importResultNode: document.getElementById("catalogueMomentResult"),
    importFileLabelNode: document.getElementById("catalogueMomentImportFileLabel"),
    importFileNode: document.getElementById("catalogueMomentImportFile"),
    importFileDescriptionNode: document.getElementById("catalogueMomentImportFileDescription"),
    importSourceSummaryNode: document.getElementById("catalogueMomentImportSourceSummary"),
    importImageGuidanceNode: document.getElementById("catalogueMomentImportImageGuidance"),
    importPreviewButton: document.getElementById("catalogueMomentImportPreview"),
    importApplyButton: document.getElementById("catalogueMomentImportApply"),
    fieldNodes: new Map(),
    fieldStatusNodes: new Map(),
    readonlyNodes: new Map(),
    moments: new Map(),
    momentRows: [],
    currentMomentId: "",
    currentRecord: null,
    expectedRecordHash: "",
    preview: null,
    previewReadiness: null,
    buildPreview: null,
    importPreview: null,
    importBuild: null,
    importSteps: [],
    needsBuild: false,
    serverAvailable: false,
    isSaving: false,
    isDeleting: false,
    isBuilding: false,
    importIsBusy: false,
    isImportMode: false
  };
  initializeStudioRouteState(root, { route: "catalogue-moment" });

  try {
    state.serverAvailable = await probeCatalogueHealth();
    state.saveModeNode.textContent = buildSaveModeText(
      state.config,
      state.serverAvailable ? "post" : "offline",
      (cfg, key, fallback, tokens) => getStudioText(cfg, `catalogue_moment_editor.${key}`, fallback, tokens)
    );
    state.searchNode.placeholder = t(state, "search_placeholder", "find moment by id or title");
    state.openButton.textContent = t(state, "open_button", "Open");
    state.newButton.textContent = t(state, "new_button", "New");
    state.saveButton.textContent = t(state, "save_button", "Save");
    state.publicationButton.textContent = t(state, "publish_button", "Publish");
    state.deleteButton.textContent = t(state, "delete_button", "Delete");
    state.importFileLabelNode.textContent = t(state, "import_file_label", "moment file");
    state.importFileNode.placeholder = t(state, "import_file_placeholder", "keys.md");
    state.importPreviewButton.textContent = t(state, "import_preview_button", "Preview");
    state.importApplyButton.textContent = t(state, "import_button", "Import");
    state.importFileDescriptionNode.textContent = t(state, "import_file_description", "filename only; the source file is resolved from var/docs/catalogue/import-staging/moments/");

    EDITABLE_FIELDS.forEach((field) => renderField(field, state));
    READONLY_FIELDS.forEach((field) => renderReadonlyField(field, state));
    bindEvents(state);
    state.importFileNode.value = readRequestedImportFile();

    if (!state.serverAvailable) {
      setTextWithState(state.statusNode, t(state, "save_mode_unavailable_hint", "Local catalogue server unavailable. Save is disabled."), "warning");
      setTextWithState(state.importStatusNode, t(state, "import_save_mode_unavailable_hint", "Local catalogue server unavailable. Moment import is disabled."), "warning");
      updateDirtyState(state);
      updateImportState(state, buildImportContext(state));
      loadingNode.hidden = true;
      root.hidden = false;
      markRouteReady(state, true);
      return;
    }

    const payload = await loadStudioLookupJson(state.config, "catalogue_moments", {
      cache: "no-store",
      catalogueServerAvailable: state.serverAvailable
    });
    state.momentRows = buildMomentRows(payload);
    state.moments = new Map(state.momentRows.map((row) => [row.moment_id, row]));

    loadingNode.hidden = true;
    root.hidden = false;
    const initialMoment = normalizeMomentId(new URLSearchParams(window.location.search).get("moment"));
    const initialImportFile = currentImportMomentFile(state);
    if (initialMoment) {
      state.searchNode.value = initialMoment;
      await openMoment(state, initialMoment, { skipUrl: true });
    } else if (initialImportFile) {
      emptyNode.hidden = true;
      enterImportMode(state, initialImportFile);
      await previewMomentImport(state, buildImportContext(state));
    } else {
      emptyNode.hidden = false;
      emptyNode.textContent = t(state, "missing_moment_param", "Search for a moment by id or title.");
      setTextWithState(state.statusNode, t(state, "missing_moment_param", "Search for a moment by id or title."));
    }
    updateDirtyState(state);
    updateImportState(state, buildImportContext(state));
    await refreshMomentActionBuildPreview(state, buildActionContext(state)).catch((error) => console.warn("catalogue_moment_editor: initial build preview failed", error));
    markRouteReady(state, true);
  } catch (error) {
    console.warn("catalogue_moment_editor: init failed", error);
    loadingNode.hidden = true;
    emptyNode.hidden = false;
    emptyNode.textContent = t(state, "load_failed_error", "Failed to load catalogue source data for the moment editor.");
  }
}

init();
