import {
  getStudioDataPath,
  getStudioRoute,
  getStudioText,
  loadStudioConfig
} from "./studio-config.js";
import { fetchJson } from "./studio-data.js";
import {
  CATALOGUE_WRITE_ENDPOINTS,
  postJson,
  probeCatalogueHealth
} from "./studio-transport.js";
import { buildSaveModeText, utcTimestamp } from "./tag-studio-save.js";

const EDITABLE_FIELDS = [
  { key: "title", label: "title", type: "text" },
  { key: "status", label: "status", type: "select", options: ["draft", "published"] },
  { key: "date", label: "date", type: "date" },
  { key: "date_display", label: "date display", type: "text" },
  { key: "published_date", label: "published date", type: "date" },
  { key: "source_image_file", label: "source image file", type: "text" },
  { key: "image_alt", label: "image alt", type: "text" }
];

const READONLY_FIELDS = [
  { key: "moment_id", label: "moment id" }
];

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

function normalizeMomentId(value) {
  return normalizeText(value).toLowerCase().replace(/\.md$/, "");
}

function displayValue(value) {
  const text = normalizeText(value);
  return text || "-";
}

function setTextWithState(node, text, state = "") {
  if (!node) return;
  node.textContent = text || "";
  if (state) node.dataset.state = state;
  else delete node.dataset.state;
}

function t(state, key, fallback, tokens = null) {
  return getStudioText(state.config, `catalogue_moment_editor.${key}`, fallback, tokens);
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

function normalizeRecord(momentId, record) {
  const out = {
    moment_id: normalizeMomentId(record && (record.moment_id || momentId)),
    title: normalizeText(record && record.title),
    status: normalizeText(record && record.status).toLowerCase() || "draft",
    published_date: normalizeText(record && record.published_date) || null,
    date: normalizeText(record && record.date) || null,
    date_display: normalizeText(record && record.date_display) || null,
    image_alt: normalizeText(record && record.image_alt) || null
  };
  const sourceImageFile = normalizeText(record && record.source_image_file);
  if (sourceImageFile && sourceImageFile !== `${out.moment_id}.jpg`) {
    out.source_image_file = sourceImageFile;
  }
  return out;
}

function readDraft(state) {
  const record = { moment_id: state.currentMomentId };
  EDITABLE_FIELDS.forEach((field) => {
    const node = state.fieldNodes.get(field.key);
    record[field.key] = node ? normalizeText(node.value) : "";
  });
  return normalizeRecord(state.currentMomentId, record);
}

function recordsEqual(a, b) {
  return stableStringify(a || {}) === stableStringify(b || {});
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
  const wrapper = document.createElement("label");
  wrapper.className = "tagStudioForm__field catalogueWorkForm__field";
  wrapper.htmlFor = `catalogueMomentField-${field.key}`;

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
  input.addEventListener("input", () => onFieldInput(state, field.key));
  input.addEventListener("change", () => onFieldInput(state, field.key));
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
    node.value = normalizeText(record[field.key]);
  });
  READONLY_FIELDS.forEach((field) => {
    const node = state.readonlyNodes.get(field.key);
    if (node) node.textContent = displayValue(record[field.key]);
  });
}

function clearFieldMessages(state) {
  state.fieldStatusNodes.forEach((node) => setTextWithState(node, ""));
}

function validateDraft(state) {
  clearFieldMessages(state);
  const draft = readDraft(state);
  const errors = [];
  if (!draft.title) errors.push(["title", t(state, "field_required_title", "Enter a title.")]);
  if (!draft.date) errors.push(["date", t(state, "field_required_date", "Enter a date.")]);
  ["date", "published_date"].forEach((key) => {
    const value = normalizeText(draft[key]);
    if (value && !DATE_RE.test(value)) errors.push([key, t(state, "field_invalid_date", "Use YYYY-MM-DD or leave blank.")]);
  });
  if (!["draft", "published"].includes(draft.status)) {
    errors.push(["status", t(state, "field_invalid_status", "Use draft or published.")]);
  }
  if (draft.status === "published" && !draft.published_date) {
    errors.push(["published_date", t(state, "field_required_published_date", "Published moments require a published date.")]);
  }
  errors.forEach(([key, message]) => {
    const node = state.fieldStatusNodes.get(key);
    if (node) setTextWithState(node, message, "error");
  });
  return { valid: !errors.length, draft };
}

function toneForReadinessStatus(status) {
  if (status === "ready") return "ready";
  if (status === "unavailable" || status === "missing_file") return "error";
  return "warning";
}

function getReadinessItems(state) {
  const source = state.buildPreview && state.buildPreview.readiness ? state.buildPreview.readiness : state.previewReadiness;
  return source && Array.isArray(source.items) ? source.items : [];
}

function renderReadiness(state) {
  const items = getReadinessItems(state);
  if (!items.length) {
    state.readinessNode.innerHTML = "";
    return;
  }
  const actionDisabled = !state.serverAvailable || state.isSaving || state.isBuilding || draftHasChanges(state);
  state.readinessNode.innerHTML = items.map((item) => {
    const itemStatus = normalizeText(item && item.status);
    const tone = toneForReadinessStatus(itemStatus);
    const proseAction = normalizeText(item && item.key) === "moment_prose";
    const proseActionDisabled = actionDisabled || (proseAction && itemStatus !== "ready");
    const disabledNote = proseAction && actionDisabled ? t(state, "dirty_warning", "Unsaved source changes.") : "";
    return `
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(item && item.title ? item.title : "readiness")}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay catalogueReadiness__body">
          <span class="catalogueReadiness__summary" data-tone="${escapeHtml(tone)}">${escapeHtml(item && item.summary ? item.summary : "-")}</span>
          ${item && item.source_path ? `<span class="tagStudioForm__meta catalogueReadiness__path">${escapeHtml(item.source_path)}</span>` : ""}
          ${item && item.next_step ? `<span class="tagStudioForm__meta">${escapeHtml(item.next_step)}</span>` : ""}
          ${proseAction ? `<div class="catalogueReadiness__actions"><button type="button" class="tagStudio__button" data-prose-import="moment" ${proseActionDisabled ? "disabled" : ""}>${escapeHtml(t(state, "prose_import_button", "Import staged prose"))}</button></div>` : ""}
          ${disabledNote ? `<span class="tagStudioForm__meta">${escapeHtml(disabledNote)}</span>` : ""}
        </div>
      </div>
    `;
  }).join("");
}

function generatedStatusText(preview) {
  if (!preview) return "-";
  return [
    preview.generated_page_exists ? "page yes" : "page no",
    preview.generated_json_exists ? "json yes" : "json no",
    preview.in_moments_index ? "index yes" : "index no"
  ].join(" / ");
}

function renderSummary(state) {
  const preview = state.preview || {};
  const publicUrl = normalizeText(preview.public_url) || `${getStudioRoute(state.config, "moments_page_base")}${state.currentMomentId}/`;
  const fields = [
    { label: "public URL", value: publicUrl },
    { label: "generated", value: generatedStatusText(preview) },
    { label: "source image", value: preview.source_image_exists ? "source image found" : "source image missing" },
    { label: "prose source", value: preview.source_exists ? "source prose found" : "source prose missing" }
  ];
  state.summaryNode.innerHTML = `
    ${fields.map((field) => `
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(field.label)}</span>
        <span class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(displayValue(field.value))}</span>
      </div>
    `).join("")}
    <p class="tagStudioForm__impact"><a href="${escapeHtml(publicUrl)}">${escapeHtml(t(state, "summary_public_link", "Open public moment page"))}</a></p>
  `;
  state.runtimeStateNode.textContent = state.needsBuild
    ? t(state, "summary_rebuild_needed", "source saved; site update pending")
    : t(state, "summary_rebuild_current", "source and public moment are aligned in this session");
  renderReadiness(state);
}

function updateDirtyState(state) {
  const dirty = draftHasChanges(state);
  setTextWithState(state.warningNode, dirty ? t(state, "dirty_warning", "Unsaved source changes.") : "", dirty ? "warning" : "");
  state.saveButton.disabled = !state.serverAvailable || state.isSaving || !state.currentRecord;
  state.buildButton.disabled = !state.serverAvailable || state.isBuilding || dirty || !state.currentRecord;
  renderReadiness(state);
}

function onFieldInput(state) {
  validateDraft(state);
  updateDirtyState(state);
}

async function previewMoment(state, momentId) {
  if (!state.serverAvailable) return;
  try {
    const payload = await postJson(CATALOGUE_WRITE_ENDPOINTS.previewMoment, { moment_id: momentId });
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
  state.currentMomentId = normalizedId;
  state.currentRecord = normalizeRecord(normalizedId, record);
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
    window.history.replaceState({}, "", url.toString());
  }
  await previewMoment(state, normalizedId);
  fillForm(state, state.currentRecord);
  validateDraft(state);
  renderSummary(state);
  updateDirtyState(state);
}

function renderBuildImpact(state) {
  if (!state.buildPreview) {
    state.buildImpactNode.textContent = "";
    return;
  }
  const momentIds = Array.isArray(state.buildPreview.moment_ids) ? state.buildPreview.moment_ids.join(", ") : state.currentMomentId;
  const search = state.buildPreview.rebuild_search
    ? t(state, "build_preview_search_yes", "yes")
    : t(state, "build_preview_search_no", "no");
  state.buildImpactNode.textContent = t(
    state,
    "build_preview_template",
    "Site update preview: moment {moment_ids}; catalogue search {search_rebuild}.",
    { moment_ids: momentIds || "none", search_rebuild: search }
  );
}

async function refreshBuildPreview(state) {
  if (!state.currentMomentId || !state.serverAvailable) return;
  try {
    const payload = await postJson(CATALOGUE_WRITE_ENDPOINTS.buildPreview, { moment_id: state.currentMomentId });
    state.buildPreview = payload.build || null;
    renderBuildImpact(state);
    renderSummary(state);
  } catch (error) {
    console.warn("catalogue_moment_editor: build preview failed", error);
    state.buildImpactNode.textContent = t(state, "build_preview_failed", "Build preview unavailable.");
  }
}

async function saveMoment(state) {
  if (!state.currentRecord || state.isSaving) return;
  const validation = validateDraft(state);
  if (!validation.valid) {
    setTextWithState(state.statusNode, t(state, "save_status_validation_error", "Fix validation errors before saving."), "error");
    return;
  }
  if (!draftHasChanges(state)) {
    setTextWithState(state.statusNode, t(state, "save_status_no_changes", "No changes to save."), "warning");
    setTextWithState(state.resultNode, t(state, "save_result_unchanged", "Source already matches the current form values."));
    return;
  }

  state.isSaving = true;
  updateDirtyState(state);
  const applyBuild = Boolean(state.applyBuildNode && state.applyBuildNode.checked);
  setTextWithState(
    state.statusNode,
    applyBuild ? t(state, "save_status_saving_and_updating", "Saving source record and updating site...") : t(state, "save_status_saving", "Saving source record..."),
    "pending"
  );
  try {
    const payload = await postJson(CATALOGUE_WRITE_ENDPOINTS.saveMoment, {
      moment_id: state.currentMomentId,
      expected_record_hash: state.expectedRecordHash,
      record: validation.draft,
      apply_build: applyBuild
    });
    state.currentRecord = payload.record || validation.draft;
    state.expectedRecordHash = payload.record_hash || await computeRecordHash(state.currentRecord);
    state.moments.set(state.currentMomentId, state.currentRecord);
    state.needsBuild = Boolean(payload.changed && !applyBuild);
    if (payload.build && !payload.build.ok) {
      state.needsBuild = true;
      setTextWithState(state.resultNode, t(state, "save_result_success_partial", "Source changes were saved at {saved_at}, but the site update failed. Retry Update site now.", { saved_at: payload.saved_at_utc || utcTimestamp() }), "warning");
    } else if (payload.changed && applyBuild) {
      setTextWithState(state.resultNode, t(state, "save_result_success_applied", "Saved source changes and updated the public moment at {saved_at}.", { saved_at: payload.saved_at_utc || utcTimestamp() }), "success");
    } else {
      setTextWithState(state.resultNode, t(state, "save_result_success", "Source saved at {saved_at}. Public moment update still pending.", { saved_at: payload.saved_at_utc || utcTimestamp() }), "success");
    }
    setTextWithState(state.statusNode, "Saved.", "success");
    await previewMoment(state, state.currentMomentId);
    renderSummary(state);
  } catch (error) {
    if (error && error.status === 409) {
      setTextWithState(state.statusNode, t(state, "save_status_conflict", "Source record changed since this page loaded. Reload the moment before saving again."), "error");
    } else {
      setTextWithState(state.statusNode, `${t(state, "save_status_failed", "Source save failed.")} ${normalizeText(error && error.message)}`.trim(), "error");
    }
  } finally {
    state.isSaving = false;
    updateDirtyState(state);
  }
}

async function buildMoment(state) {
  if (!state.currentMomentId || state.isBuilding || draftHasChanges(state)) return;
  state.isBuilding = true;
  updateDirtyState(state);
  setTextWithState(state.statusNode, t(state, "build_status_running", "Updating site..."), "pending");
  try {
    const payload = await postJson(CATALOGUE_WRITE_ENDPOINTS.buildApply, { moment_id: state.currentMomentId });
    state.needsBuild = false;
    state.buildPreview = payload.build || state.buildPreview;
    setTextWithState(state.statusNode, t(state, "build_status_success", "Site update completed."), "success");
    setTextWithState(state.resultNode, t(state, "build_result_success", "Public moment updated at {completed_at}. Build Activity updated.", { completed_at: payload.completed_at_utc || utcTimestamp() }), "success");
    await previewMoment(state, state.currentMomentId);
    renderSummary(state);
  } catch (error) {
    setTextWithState(state.statusNode, `${t(state, "build_status_failed", "Site update failed.")} ${normalizeText(error && error.message)}`.trim(), "error");
  } finally {
    state.isBuilding = false;
    updateDirtyState(state);
  }
}

async function importMomentProse(state) {
  if (!state.currentMomentId || draftHasChanges(state)) {
    setTextWithState(state.statusNode, t(state, "dirty_warning", "Unsaved source changes."), "error");
    return;
  }
  setTextWithState(state.statusNode, t(state, "prose_import_preview_running", "Previewing staged prose..."), "pending");
  try {
    const preview = await postJson(CATALOGUE_WRITE_ENDPOINTS.previewProseImport, {
      target_kind: "moment",
      moment_id: state.currentMomentId
    });
    if (!preview.valid) {
      const errors = Array.isArray(preview.errors) ? preview.errors.join("; ") : "";
      throw new Error(errors || t(state, "prose_import_preview_invalid", "Staged prose is not ready to import."));
    }
    if (preview.overwrite_required) {
      const confirmed = window.confirm(t(
        state,
        "prose_import_confirm_overwrite",
        "Overwrite existing prose source at {target_path} with staged file {staging_path}?",
        { target_path: preview.target_path, staging_path: preview.staging_path }
      ));
      if (!confirmed) {
        setTextWithState(state.statusNode, t(state, "prose_import_overwrite_cancelled", "Prose import cancelled."), "warning");
        return;
      }
    }
    setTextWithState(state.statusNode, t(state, "prose_import_running", "Importing staged prose..."), "pending");
    const payload = await postJson(CATALOGUE_WRITE_ENDPOINTS.applyProseImport, {
      target_kind: "moment",
      moment_id: state.currentMomentId,
      confirm_overwrite: Boolean(preview.overwrite_required)
    });
    state.needsBuild = Boolean(payload.changed);
    setTextWithState(state.statusNode, t(state, "prose_import_status_success", "Prose import completed."), "success");
    setTextWithState(
      state.resultNode,
      t(state, "prose_import_result_success", "Prose imported to {target_path} at {completed_at}. The next site update will publish it.", {
        target_path: payload.target_path,
        completed_at: payload.imported_at_utc || utcTimestamp()
      }),
      "success"
    );
    await previewMoment(state, state.currentMomentId);
    renderSummary(state);
  } catch (error) {
    setTextWithState(state.statusNode, `${t(state, "prose_import_status_failed", "Prose import failed.")} ${normalizeText(error && error.message)}`.trim(), "error");
  }
}

function buildMomentRows(payload) {
  const moments = payload && payload.moments && typeof payload.moments === "object" ? payload.moments : {};
  return Object.entries(moments).map(([momentId, record]) => {
    const normalized = normalizeRecord(momentId, record);
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
  state.saveButton.addEventListener("click", () => saveMoment(state));
  state.buildButton.addEventListener("click", () => buildMoment(state));
  state.readinessNode.addEventListener("click", (event) => {
    const button = event.target && event.target.closest ? event.target.closest("[data-prose-import]") : null;
    if (!button) return;
    importMomentProse(state).catch((error) => console.warn("catalogue_moment_editor: prose import failed", error));
  });
}

async function init() {
  const root = document.getElementById("catalogueMomentRoot");
  const loadingNode = document.getElementById("catalogueMomentLoading");
  const emptyNode = document.getElementById("catalogueMomentEmpty");
  const state = {
    config: await loadStudioConfig(),
    root,
    loadingNode,
    emptyNode,
    searchNode: document.getElementById("catalogueMomentSearch"),
    popupNode: document.getElementById("catalogueMomentPopup"),
    popupListNode: document.getElementById("catalogueMomentPopupList"),
    openButton: document.getElementById("catalogueMomentOpen"),
    saveModeNode: document.getElementById("catalogueMomentSaveMode"),
    contextNode: document.getElementById("catalogueMomentContext"),
    statusNode: document.getElementById("catalogueMomentStatus"),
    warningNode: document.getElementById("catalogueMomentWarning"),
    resultNode: document.getElementById("catalogueMomentResult"),
    saveButton: document.getElementById("catalogueMomentSave"),
    buildButton: document.getElementById("catalogueMomentBuild"),
    applyBuildNode: document.getElementById("catalogueMomentApplyBuild"),
    fieldsNode: document.getElementById("catalogueMomentFields"),
    readonlyNode: document.getElementById("catalogueMomentReadonly"),
    summaryNode: document.getElementById("catalogueMomentSummary"),
    readinessNode: document.getElementById("catalogueMomentReadiness"),
    runtimeStateNode: document.getElementById("catalogueMomentRuntimeState"),
    buildImpactNode: document.getElementById("catalogueMomentBuildImpact"),
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
    needsBuild: false,
    serverAvailable: false,
    isSaving: false,
    isBuilding: false
  };

  try {
    state.serverAvailable = await probeCatalogueHealth();
    state.saveModeNode.textContent = buildSaveModeText(
      state.config,
      state.serverAvailable ? "post" : "offline",
      (cfg, key, fallback, tokens) => getStudioText(cfg, `catalogue_moment_editor.${key}`, fallback, tokens)
    );
    state.searchNode.placeholder = t(state, "search_placeholder", "find moment by id or title");
    state.openButton.textContent = t(state, "open_button", "Open");
    state.saveButton.textContent = t(state, "save_button", "Save");
    state.buildButton.textContent = t(state, "build_button", "Update site now");
    document.getElementById("catalogueMomentApplyBuildLabel").textContent = t(state, "build_button", "Update site now");

    EDITABLE_FIELDS.forEach((field) => renderField(field, state));
    READONLY_FIELDS.forEach((field) => renderReadonlyField(field, state));
    bindEvents(state);

    const momentsPath = getStudioDataPath(state.config, "catalogue_moments");
    const payload = await fetchJson(momentsPath, { cache: "no-store" });
    state.momentRows = buildMomentRows(payload);
    state.moments = new Map(state.momentRows.map((row) => [row.moment_id, row]));

    loadingNode.hidden = true;
    root.hidden = false;
    if (!state.serverAvailable) {
      setTextWithState(state.statusNode, t(state, "save_mode_unavailable_hint", "Local catalogue server unavailable. Save is disabled."), "warning");
    }

    const initialMoment = normalizeMomentId(new URLSearchParams(window.location.search).get("moment"));
    if (initialMoment) {
      state.searchNode.value = initialMoment;
      await openMoment(state, initialMoment, { skipUrl: true });
    } else {
      emptyNode.hidden = false;
      emptyNode.textContent = t(state, "missing_moment_param", "Search for a moment by id or title.");
      setTextWithState(state.statusNode, t(state, "missing_moment_param", "Search for a moment by id or title."));
    }
    updateDirtyState(state);
    refreshBuildPreview(state).catch((error) => console.warn("catalogue_moment_editor: initial build preview failed", error));
  } catch (error) {
    console.warn("catalogue_moment_editor: init failed", error);
    loadingNode.hidden = true;
    emptyNode.hidden = false;
    emptyNode.textContent = t(state, "load_failed_error", "Failed to load catalogue source data for the moment editor.");
  }
}

init();
