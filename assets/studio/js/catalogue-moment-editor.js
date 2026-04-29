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
  { key: "status", label: "status", type: "text", readonly: true },
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

function normalizeMomentFilename(value) {
  const raw = normalizeText(value).toLowerCase();
  if (!raw) return "";
  return raw.endsWith(".md") ? raw : `${raw}.md`;
}

function displayValue(value) {
  const text = normalizeText(value);
  return text || "-";
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
    record[field.key] = node ? normalizeText(getFieldNodeValue(node)) : "";
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
    const mediaAction = normalizeText(item && item.key) === "moment_media";
    const proseActionDisabled = actionDisabled || (proseAction && itemStatus !== "ready");
    const mediaActionDisabled = actionDisabled || !Boolean(item && item.exists);
    const disabledNote = actionDisabled && (proseAction || mediaAction)
      ? (draftHasChanges(state)
	      ? (mediaAction ? t(state, "media_refresh_save_first", "Save source changes before refreshing media.") : t(state, "dirty_warning", "Unsaved source changes."))
        : t(state, "readiness_action_busy", "Wait for the current save or public update to finish."))
      : "";
    return `
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(item && item.title ? item.title : "readiness")}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay catalogueReadiness__body">
          <span class="catalogueReadiness__summary" data-tone="${escapeHtml(tone)}">${escapeHtml(item && item.summary ? item.summary : "-")}</span>
          ${item && item.source_path ? `<span class="tagStudioForm__meta catalogueReadiness__path">${escapeHtml(item.source_path)}</span>` : ""}
          ${item && item.next_step ? `<span class="tagStudioForm__meta">${escapeHtml(item.next_step)}</span>` : ""}
          ${proseAction ? `<div class="catalogueReadiness__actions"><button type="button" class="tagStudio__button" data-prose-import="moment" ${proseActionDisabled ? "disabled" : ""}>${escapeHtml(t(state, "prose_import_button", "Import staged prose"))}</button></div>` : ""}
          ${mediaAction ? `<div class="catalogueReadiness__actions"><button type="button" class="tagStudio__button" data-media-refresh="moment" ${mediaActionDisabled ? "disabled" : ""}>${escapeHtml(t(state, "media_refresh_button", "Refresh media"))}</button></div>` : ""}
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
    ? t(state, "summary_rebuild_needed", "public update failed in this session")
    : t(state, "summary_rebuild_current", "source and public moment are aligned in this session");
  renderReadiness(state);
}

function currentImportMomentFile(state) {
  return normalizeText(state.importFileNode && state.importFileNode.value);
}

function readImportMetadata(state) {
  const metadata = { moment_id: normalizeMomentId(currentImportMomentFile(state)) };
  EDITABLE_FIELDS.forEach((field) => {
    const node = state.fieldNodes.get(field.key);
    metadata[field.key] = node ? normalizeText(getFieldNodeValue(node)) : "";
  });
  metadata.status = "draft";
  return metadata;
}

function fillImportMetadataFromPreview(state, preview) {
  if (!preview) return;
  const mapping = {
    title: preview.title,
    status: preview.status,
    date: preview.date,
    date_display: preview.date_display,
    published_date: preview.published_date,
    source_image_file: preview.image_file,
    image_alt: preview.image_alt
  };
  Object.entries(mapping).forEach(([key, value]) => {
    const node = state.fieldNodes.get(key);
    if (node && (!normalizeText(getFieldNodeValue(node)) || key === "status") && normalizeText(value)) {
      setFieldNodeValue(node, key === "status" ? "draft" : value);
    }
  });
}

function importGeneratedStatusText(state, preview) {
  if (!preview) return t(state, "import_preview_missing_value", "none");
  return [
    preview.generated_page_exists ? "page yes" : "page no",
    preview.generated_json_exists ? "json yes" : "json no"
  ].join(" / ");
}

function buildImportSummaryHtml(state, preview) {
  if (!preview) {
    return `
      <p class="tagStudioForm__meta">${escapeHtml(t(state, "import_empty_state", "Preview a source file to inspect the resolved moment metadata."))}</p>
    `;
  }

  const fields = [
    { label: t(state, "import_preview_field_moment_id", "moment id"), value: preview.moment_id },
    { label: t(state, "import_preview_field_title", "title"), value: preview.title },
    { label: t(state, "import_preview_field_status", "status"), value: preview.status },
    { label: t(state, "import_preview_field_date", "date"), value: preview.date },
    { label: t(state, "import_preview_field_date_display", "date display"), value: preview.date_display },
    { label: t(state, "import_preview_field_published_date", "published date"), value: preview.published_date },
    { label: t(state, "import_preview_field_image_file", "image file"), value: preview.image_file },
    {
      label: t(state, "import_preview_field_image_status", "image status"),
      value: preview.source_image_exists
        ? t(state, "import_preview_image_present", "source image found")
        : t(state, "import_preview_image_missing", "no source image found; media generation will be blocked")
    },
    {
      label: t(state, "import_preview_field_generated_status", "generated status"),
      value: importGeneratedStatusText(state, preview)
    },
    {
      label: t(state, "import_preview_field_source_path", "source path"),
      value: preview.source_path
    }
  ];

  return fields.map((field) => `
    <div class="tagStudioForm__field">
      <span class="tagStudioForm__label">${escapeHtml(field.label)}</span>
      <span class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(normalizeText(field.value) || t(state, "import_preview_missing_value", "none"))}</span>
    </div>
  `).join("");
}

function buildImportStepRows(steps) {
  if (!Array.isArray(steps) || !steps.length) return "";
  return `
    <div class="catalogueWorkDetails__rows">
      ${steps.map((step) => `
        <div class="catalogueWorkDetails__row">
          <span class="catalogueWorkDetails__link">${escapeHtml(step && step.label ? step.label : "step")}</span>
          <span class="catalogueWorkDetails__title">${escapeHtml(step && step.status ? step.status : "")}</span>
        </div>
      `).join("")}
    </div>
  `;
}

function buildImportDetailSections(state) {
  const preview = state.importPreview;
  if (!preview) {
    return `
      <p class="tagStudioForm__meta">${escapeHtml(t(state, "import_empty_state", "Preview a source file to inspect the resolved moment metadata."))}</p>
    `;
  }

  const sections = [];
  const errors = Array.isArray(preview.errors) ? preview.errors : [];
  const build = state.importBuild || {};
  const sourceResultSummary = normalizeText(build.summary || preview.summary)
    || t(state, "import_source_result_summary", "Import writes draft prose and metadata only. Publish from this editor when ready.");

  sections.push(`
    <section class="catalogueWorkDetails__section">
      <div class="tagStudio__headingRow">
        <h3 class="tagStudioForm__key">validation</h3>
      </div>
      ${errors.length ? `
        <p class="tagStudioForm__meta">${escapeHtml(t(state, "import_preview_errors_intro", "Source file issues:"))}</p>
        <div class="catalogueWorkDetails__rows">
          ${errors.map((error) => `
            <div class="catalogueWorkDetails__row">
              <span class="catalogueWorkDetails__link">error</span>
              <span class="catalogueWorkDetails__title">${escapeHtml(error)}</span>
            </div>
          `).join("")}
        </div>
      ` : `
        <p class="tagStudioForm__meta">${escapeHtml(t(state, "import_preview_status_ready", "Moment source preview ready."))}</p>
      `}
    </section>
  `);

  sections.push(`
    <section class="catalogueWorkDetails__section">
      <div class="tagStudio__headingRow">
        <h3 class="tagStudioForm__key">source result</h3>
      </div>
      <p class="tagStudioForm__meta">${escapeHtml(sourceResultSummary)}</p>
    </section>
  `);

  if (Array.isArray(state.importSteps) && state.importSteps.length) {
    sections.push(`
      <section class="catalogueWorkDetails__section">
        <div class="tagStudio__headingRow">
          <h3 class="tagStudioForm__key">import steps</h3>
        </div>
        ${buildImportStepRows(state.importSteps)}
      </section>
    `);
  }

  return sections.join("");
}

function updateImportState(state) {
  if (!state.isImportMode) {
    state.importPreviewButton.hidden = true;
    state.importApplyButton.hidden = true;
    state.importSourceNode.hidden = true;
    state.importSourceSummaryNode.textContent = "";
    state.importImageGuidanceNode.textContent = "";
    return;
  }
  const fileValue = currentImportMomentFile(state);
  const preview = state.importPreview;
  const previewMatchesInput = preview && normalizeMomentFilename(preview.moment_file) === normalizeMomentFilename(fileValue);
  const editorBusy = state.isSaving || state.isBuilding || state.isDeleting;
  state.importPreviewButton.hidden = false;
  state.importApplyButton.hidden = false;
  state.importSourceNode.hidden = false;
  state.importSourceSummaryNode.textContent = t(state, "import_source_summary", "Moment prose is imported as body-only Markdown. Metadata is stored in catalogue source JSON, not prose front matter.");
  state.importImageGuidanceNode.textContent = t(state, "import_image_guidance", "Missing images are acceptable in this phase. The public moment page handles missing hero images cleanly.");
  state.importPreviewButton.disabled = state.importIsBusy || editorBusy || !state.serverAvailable || !fileValue;
  state.importApplyButton.disabled = state.importIsBusy || editorBusy || !state.serverAvailable || !preview || !previewMatchesInput || !preview.valid;
  state.summaryNode.innerHTML = buildImportSummaryHtml(state, preview);
  state.readinessNode.innerHTML = buildImportDetailSections(state);
}

function clearImportPreview(state) {
  state.importPreview = null;
  state.importBuild = null;
  state.importSteps = [];
  updateImportState(state);
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
  clearImportPreview(state);
  updateDirtyState(state);
}

function readRequestedImportFile() {
  try {
    const url = new URL(window.location.href);
    return normalizeText(url.searchParams.get("file"));
  } catch (error) {
    return "";
  }
}

function writeRequestedImportFile(momentFile) {
  if (!window.history || !window.history.replaceState) return;
  const nextFile = normalizeText(momentFile);
  try {
    const url = new URL(window.location.href);
    if (nextFile) url.searchParams.set("file", nextFile);
    else url.searchParams.delete("file");
    window.history.replaceState({}, "", url.toString());
  } catch (error) {
    // URL updates are progressive enhancement only.
  }
}

function clearRequestedImportFile() {
  if (!window.history || !window.history.replaceState) return;
  try {
    const url = new URL(window.location.href);
    url.searchParams.delete("file");
    window.history.replaceState({}, "", url.toString());
  } catch (error) {
    // URL updates are progressive enhancement only.
  }
}

function upsertMomentRow(state, momentId, record) {
  const normalized = normalizeRecord(momentId, record);
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

async function previewMomentImport(state) {
  const momentFile = currentImportMomentFile(state);
  if (!momentFile) {
    setTextWithState(state.importStatusNode, t(state, "import_file_required", "Enter a moment markdown filename."), "error");
    return;
  }

  state.importIsBusy = true;
  updateImportState(state);
  setTextWithState(state.importStatusNode, t(state, "import_preview_status_loading", "Loading moment source preview..."), "pending");
  setTextWithState(state.importWarningNode, "");
  setTextWithState(state.importResultNode, "");
  try {
    const response = await postJson(CATALOGUE_WRITE_ENDPOINTS.previewMomentImport, {
      moment_file: momentFile,
      metadata: readImportMetadata(state)
    });
    state.importPreview = response && response.preview ? response.preview : null;
    fillImportMetadataFromPreview(state, state.importPreview);
    state.importBuild = response && response.build ? response.build : null;
    state.importSteps = [];
    if (state.importPreview && state.importPreview.valid) {
      setTextWithState(state.importStatusNode, t(state, "import_preview_status_ready", "Moment source preview ready."), "success");
    } else {
      setTextWithState(state.importStatusNode, t(state, "import_preview_status_invalid", "Fix source-file issues before importing the moment."), "warning");
    }
  } catch (error) {
    state.importPreview = error && error.payload && error.payload.preview ? error.payload.preview : null;
    state.importBuild = null;
    state.importSteps = [];
    setTextWithState(state.importStatusNode, `${t(state, "import_preview_status_failed", "Moment source preview failed.")} ${normalizeText(error && error.message)}`.trim(), "error");
  } finally {
    state.importIsBusy = false;
    updateImportState(state);
  }
}

async function applyMomentImport(state) {
  const preview = state.importPreview;
  const momentFile = currentImportMomentFile(state);
  if (!preview || normalizeMomentFilename(preview.moment_file) !== normalizeMomentFilename(momentFile)) {
    setTextWithState(state.importStatusNode, t(state, "import_result_missing_preview", "Preview the source file before importing."), "error");
    return;
  }
  if (!preview.valid) {
    setTextWithState(state.importStatusNode, t(state, "import_preview_status_invalid", "Fix source-file issues before importing the moment."), "error");
    return;
  }

  state.importIsBusy = true;
  updateImportState(state);
  setTextWithState(state.importStatusNode, t(state, "import_status_running", "Importing draft moment source..."), "pending");
  setTextWithState(state.importWarningNode, "");
  setTextWithState(state.importResultNode, "");
  try {
    const metadata = readImportMetadata(state);
    const response = await postJson(CATALOGUE_WRITE_ENDPOINTS.applyMomentImport, {
      moment_file: momentFile,
      metadata
    });
    state.importPreview = response && response.preview ? response.preview : state.importPreview;
    state.importBuild = response && response.build ? response.build : state.importBuild;
    state.importSteps = Array.isArray(response && response.steps) ? response.steps : [];
    const momentId = normalizeMomentId(response && response.moment_id ? response.moment_id : state.importPreview && state.importPreview.moment_id);
    const importedRecord = normalizeRecord(momentId, {
      ...metadata,
      moment_id: momentId,
      status: "draft"
    });
    upsertMomentRow(state, momentId, importedRecord);
    state.searchNode.value = momentId;
    clearRequestedImportFile();
    await openMoment(state, momentId);
    setTextWithState(state.statusNode, t(state, "import_status_success", "Moment import completed."), "success");
    setTextWithState(
      state.resultNode,
      t(state, "import_result_success", "Imported draft moment {moment_id}.", { moment_id }),
      "success"
    );
  } catch (error) {
    const payload = error && error.payload ? error.payload : null;
    state.importPreview = payload && payload.preview ? payload.preview : state.importPreview;
    state.importBuild = payload && payload.build ? payload.build : state.importBuild;
    state.importSteps = Array.isArray(payload && payload.steps) ? payload.steps : [];
    setTextWithState(state.importStatusNode, `${t(state, "import_status_failed", "Moment import failed.")} ${normalizeText(error && error.message)}`.trim(), "error");
  } finally {
    state.importIsBusy = false;
    updateImportState(state);
  }
}

function currentMomentIsPublished(state) {
  return normalizeText(readDraft(state).status).toLowerCase() === "published";
}

function currentMomentIsDraft(state) {
  return normalizeText(readDraft(state).status).toLowerCase() === "draft";
}

function updatePublicationControls(state, { dirty, validation }) {
  const hasRecord = Boolean(state.currentRecord);
  const canPublish = hasRecord && currentMomentIsDraft(state);
  const canUnpublish = hasRecord && currentMomentIsPublished(state);
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
  setTextWithState(state.warningNode, dirty ? t(state, "dirty_warning", "Unsaved source changes.") : "", dirty ? "warning" : "");
  state.saveButton.disabled = !state.serverAvailable || state.isSaving || state.isDeleting || !state.currentRecord;
  state.deleteButton.disabled = !state.serverAvailable || state.isSaving || state.isBuilding || state.isDeleting || !state.currentRecord;
  updatePublicationControls(state, { dirty, validation });
  renderReadiness(state);
  updateImportState(state);
}

function applySaveBuildOutcome(state, payload) {
  if (!currentMomentIsPublished(state)) {
    state.needsBuild = false;
    return payload && payload.changed ? "saved_unpublished" : "unchanged";
  }
  if (payload && payload.build && !payload.build.ok) {
    state.needsBuild = true;
    return "partial";
  }
  state.needsBuild = false;
  return payload && payload.changed ? "applied" : "unchanged";
}

function onFieldInput(state) {
  if (state.isImportMode) {
    clearImportPreview(state);
    updateDirtyState(state);
    return;
  }
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
  setEditModeChrome(state);
  clearImportPreview(state);
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
  if (!currentMomentIsPublished(state)) {
    state.buildImpactNode.textContent = t(state, "build_preview_unpublished", "Public update unavailable while the moment is not published.");
    return;
  }
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
    "Public update preview: moment {moment_ids}; catalogue search {search_rebuild}.",
    { moment_ids: momentIds || "none", search_rebuild: search }
  );
}

async function refreshBuildPreview(state) {
  if (!state.currentMomentId || !state.serverAvailable) return;
  if (!currentMomentIsPublished(state)) {
    state.buildPreview = null;
    renderBuildImpact(state);
    renderSummary(state);
    return;
  }
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
  const applyBuild = currentMomentIsPublished(state);
  setTextWithState(
    state.statusNode,
    applyBuild ? t(state, "save_status_saving_and_updating", "Saving source record and updating public moment...") : t(state, "save_status_saving", "Saving source record..."),
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
    const outcome = applySaveBuildOutcome(state, payload);
    if (outcome === "partial") {
      setTextWithState(state.resultNode, t(state, "save_result_success_partial", "Source changes were saved at {saved_at}, but the public update failed.", { saved_at: payload.saved_at_utc || utcTimestamp() }), "warning");
    } else if (outcome === "applied") {
      setTextWithState(state.resultNode, t(state, "save_result_success_applied", "Saved source changes and updated the public moment at {saved_at}.", { saved_at: payload.saved_at_utc || utcTimestamp() }), "success");
    } else if (outcome === "saved_unpublished") {
      setTextWithState(state.resultNode, t(state, "save_result_success_unpublished", "Source saved at {saved_at}.", { saved_at: payload.saved_at_utc || utcTimestamp() }), "success");
    } else {
      setTextWithState(state.resultNode, t(state, "save_result_success", "Source saved at {saved_at}.", { saved_at: payload.saved_at_utc || utcTimestamp() }), "success");
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

async function applyPublicationChange(state) {
  if (!state.currentRecord || !state.currentMomentId || !state.serverAvailable || state.isBuilding) return;
  const action = currentMomentIsPublished(state) ? "unpublish" : currentMomentIsDraft(state) ? "publish" : "";
  if (!action) {
    setTextWithState(state.statusNode, t(state, "publication_status_invalid", "Publication is available only for draft or published moments."), "error");
    return;
  }
  if (action === "publish" && draftHasChanges(state)) {
    setTextWithState(state.statusNode, t(state, "publication_save_first", "Save source changes before publishing."), "error");
    return;
  }
  if (action === "publish") {
    const validation = validateDraft(state);
    if (!validation.valid) {
      setTextWithState(state.statusNode, t(state, "publication_status_validation_error", "Fix validation errors before changing publication state."), "error");
      updateDirtyState(state);
      return;
    }
  }
  state.isBuilding = true;
  updateDirtyState(state);
  setTextWithState(
    state.statusNode,
    action === "publish"
      ? t(state, "publication_preview_publish_running", "Preparing publish preview...")
      : t(state, "publication_preview_unpublish_running", "Preparing unpublish preview..."),
    "pending"
  );
  setTextWithState(state.resultNode, "");
  try {
    const request = {
      kind: "moment",
      action,
      moment_id: state.currentMomentId,
      expected_record_hash: state.expectedRecordHash
    };
    const previewResponse = await postJson(CATALOGUE_WRITE_ENDPOINTS.publicationPreview, request);
    const preview = previewResponse && previewResponse.preview ? previewResponse.preview : null;
    const blockers = Array.isArray(preview && preview.blockers) ? preview.blockers : [];
    if ((preview && preview.blocked) || blockers.length) {
      const message = blockers[0] || t(state, "publication_status_blocked", "Publication change is blocked.");
      setTextWithState(state.statusNode, message, "error");
      return;
    }
    if (action === "unpublish") {
      const summary = normalizeText(preview && preview.summary) || t(state, "unpublish_confirm_default", "Unpublish this moment?");
      const dirtyNote = draftHasChanges(state) ? `\n\n${t(state, "unpublish_confirm_dirty_note", "Unsaved form changes will be discarded.")}` : "";
      if (!window.confirm(`${summary}${dirtyNote}`)) {
        setTextWithState(state.statusNode, t(state, "publication_status_cancelled", "Publication change cancelled."), "warning");
        return;
      }
    }

    setTextWithState(
      state.statusNode,
      action === "publish"
        ? t(state, "publication_publish_running", "Publishing moment...")
        : t(state, "publication_unpublish_running", "Unpublishing moment..."),
      "pending"
    );
    const payload = await postJson(CATALOGUE_WRITE_ENDPOINTS.publicationApply, request);
    const record = payload && payload.record && typeof payload.record === "object" ? payload.record : null;
    if (!record) throw new Error("publication response missing record");
    state.currentRecord = normalizeRecord(state.currentMomentId, record);
    state.expectedRecordHash = payload.record_hash || await computeRecordHash(state.currentRecord);
    state.moments.set(state.currentMomentId, state.currentRecord);
    const row = state.momentRows.find((item) => item.moment_id === state.currentMomentId);
    if (row) {
      Object.assign(row, state.currentRecord, {
        search: `${state.currentMomentId} ${normalizeText(state.currentRecord.title).toLowerCase()}`
      });
    }
    fillForm(state, state.currentRecord);
    state.needsBuild = payload.status === "public_update_failed";
    await previewMoment(state, state.currentMomentId);
    renderSummary(state);
    if (payload.status === "public_update_failed") {
      const error = normalizeText(payload.public_update && payload.public_update.error);
      setTextWithState(state.statusNode, `${t(state, "publication_status_public_failed", "Publication state changed, but the public update failed.")} ${error}`.trim(), "error");
      setTextWithState(state.resultNode, t(state, "publication_result_public_failed", "Source status changed, but public artifacts did not finish updating."), "warning");
      return;
    }
    if (action === "publish") {
      setTextWithState(state.statusNode, t(state, "publication_status_published", "Moment published."), "success");
      setTextWithState(state.resultNode, t(state, "publication_result_published", "Moment is published and public output has been updated."), "success");
    } else {
      setTextWithState(state.statusNode, t(state, "publication_status_unpublished", "Moment unpublished."), "success");
      setTextWithState(state.resultNode, t(state, "publication_result_unpublished", "Moment is draft again and public output has been cleaned up."), "success");
    }
  } catch (error) {
    const message = Number(error && error.status) === 409
      ? t(state, "publication_status_conflict", "Source record changed since this page loaded. Reload before changing publication state.")
      : `${t(state, "publication_status_failed", "Publication change failed.")} ${normalizeText(error && error.message)}`.trim();
    setTextWithState(state.statusNode, message, "error");
  } finally {
    state.isBuilding = false;
    updateDirtyState(state);
  }
}

function countMediaItems(media, group) {
  const values = media && media[group] && typeof media[group] === "object" ? media[group] : {};
  return Object.values(values).reduce((total, items) => total + (Array.isArray(items) ? items.length : 0), 0);
}

async function refreshMomentMedia(state) {
  if (!state.currentMomentId || !state.serverAvailable || state.isBuilding || draftHasChanges(state)) return;
  state.isBuilding = true;
  updateDirtyState(state);
  setTextWithState(state.statusNode, t(state, "media_refresh_status_running", "Refreshing media..."), "pending");
  setTextWithState(state.resultNode, "");
  try {
    const payload = await postJson(CATALOGUE_WRITE_ENDPOINTS.buildApply, {
      moment_id: state.currentMomentId,
      media_only: true,
      force: true
    });
    const blockedCount = countMediaItems(payload && payload.media, "blocked");
    await previewMoment(state, state.currentMomentId);
    renderSummary(state);
    if (blockedCount > 0) {
      setTextWithState(state.statusNode, t(state, "media_refresh_status_blocked", "Media refresh blocked."), "error");
      setTextWithState(state.resultNode, normalizeText(payload && payload.media && payload.media.summary), "error");
      return;
    }
    setTextWithState(state.statusNode, t(state, "media_refresh_status_success", "Media refresh completed."), "success");
    setTextWithState(state.resultNode, t(state, "media_refresh_result_success", "Thumbnails updated; primary variants staged for publishing."), "success");
  } catch (error) {
    setTextWithState(state.statusNode, `${t(state, "media_refresh_status_failed", "Media refresh failed.")} ${normalizeText(error && error.message)}`.trim(), "error");
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

async function deleteMoment(state) {
  if (!state.currentRecord || !state.serverAvailable || state.isDeleting) return;
  state.isDeleting = true;
  updateDirtyState(state);
  setTextWithState(state.statusNode, t(state, "delete_status_running", "Preparing delete preview..."), "pending");
  setTextWithState(state.resultNode, "");
  try {
    const previewResponse = await postJson(CATALOGUE_WRITE_ENDPOINTS.deletePreview, {
      kind: "moment",
      moment_id: state.currentMomentId,
      expected_record_hash: state.expectedRecordHash
    });
    const preview = previewResponse && previewResponse.preview ? previewResponse.preview : null;
    const blockers = Array.isArray(preview && preview.blockers) ? preview.blockers : [];
    const validationErrors = Array.isArray(preview && preview.validation_errors) ? preview.validation_errors : [];
    if ((preview && preview.blocked) || blockers.length || validationErrors.length) {
      const message = blockers[0] || validationErrors[0] || t(state, "delete_status_blocked", "Delete is blocked.");
      setTextWithState(state.statusNode, message, "error");
      state.isDeleting = false;
      updateDirtyState(state);
      return;
    }
    const summary = normalizeText(preview && preview.summary) || t(state, "delete_confirm_default", "Delete this source record?");
    if (!window.confirm(summary)) {
      setTextWithState(state.statusNode, t(state, "delete_status_cancelled", "Delete cancelled."), "warning");
      state.isDeleting = false;
      updateDirtyState(state);
      return;
    }
    setTextWithState(state.statusNode, t(state, "delete_status_deleting", "Deleting source record..."), "pending");
    await postJson(CATALOGUE_WRITE_ENDPOINTS.deleteApply, {
      kind: "moment",
      moment_id: state.currentMomentId,
      expected_record_hash: state.expectedRecordHash
    });
    const route = getStudioRoute(state.config, "catalogue_status");
    window.location.assign(route);
  } catch (error) {
    const message = Number(error && error.status) === 409
      ? t(state, "delete_status_conflict", "Source record changed since this page loaded. Reload before deleting again.")
      : `${t(state, "delete_status_failed", "Source delete failed.")} ${normalizeText(error && error.message)}`.trim();
    setTextWithState(state.statusNode, message, "error");
    state.isDeleting = false;
    updateDirtyState(state);
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
  state.newButton.addEventListener("click", () => enterImportMode(state));
  state.saveButton.addEventListener("click", () => saveMoment(state));
  state.publicationButton.addEventListener("click", () => applyPublicationChange(state).catch((error) => console.warn("catalogue_moment_editor: publication failed", error)));
  state.deleteButton.addEventListener("click", () => deleteMoment(state).catch((error) => console.warn("catalogue_moment_editor: delete failed", error)));
  state.importFileNode.addEventListener("input", () => {
    writeRequestedImportFile(state.importFileNode.value);
    setTextWithState(state.importWarningNode, "");
    setTextWithState(state.importResultNode, "");
    clearImportPreview(state);
  });
  state.importPreviewButton.addEventListener("click", () => {
    previewMomentImport(state).catch((error) => console.warn("catalogue_moment_editor: import preview failed", error));
  });
  state.importApplyButton.addEventListener("click", () => {
    applyMomentImport(state).catch((error) => console.warn("catalogue_moment_editor: import apply failed", error));
  });
  state.readinessNode.addEventListener("click", (event) => {
    const mediaButton = event.target && event.target.closest ? event.target.closest("[data-media-refresh]") : null;
    if (mediaButton) {
      refreshMomentMedia(state).catch((error) => console.warn("catalogue_moment_editor: media refresh failed", error));
      return;
    }
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

    const momentsPath = getStudioDataPath(state.config, "catalogue_moments");
    const payload = await fetchJson(momentsPath, { cache: "no-store" });
    state.momentRows = buildMomentRows(payload);
    state.moments = new Map(state.momentRows.map((row) => [row.moment_id, row]));

    loadingNode.hidden = true;
    root.hidden = false;
    if (!state.serverAvailable) {
      setTextWithState(state.statusNode, t(state, "save_mode_unavailable_hint", "Local catalogue server unavailable. Save is disabled."), "warning");
      setTextWithState(state.importStatusNode, t(state, "import_save_mode_unavailable_hint", "Local catalogue server unavailable. Moment import is disabled."), "warning");
    }

    const initialMoment = normalizeMomentId(new URLSearchParams(window.location.search).get("moment"));
    const initialImportFile = currentImportMomentFile(state);
    if (initialMoment) {
      state.searchNode.value = initialMoment;
      await openMoment(state, initialMoment, { skipUrl: true });
    } else if (initialImportFile) {
      emptyNode.hidden = true;
      enterImportMode(state, initialImportFile);
    } else {
      emptyNode.hidden = false;
      emptyNode.textContent = t(state, "missing_moment_param", "Search for a moment by id or title.");
      setTextWithState(state.statusNode, t(state, "missing_moment_param", "Search for a moment by id or title."));
    }
    updateDirtyState(state);
    updateImportState(state);
    if (currentImportMomentFile(state) && state.serverAvailable) {
      previewMomentImport(state).catch((error) => console.warn("catalogue_moment_editor: initial import preview failed", error));
    }
    refreshBuildPreview(state).catch((error) => console.warn("catalogue_moment_editor: initial build preview failed", error));
  } catch (error) {
    console.warn("catalogue_moment_editor: init failed", error);
    loadingNode.hidden = true;
    emptyNode.hidden = false;
    emptyNode.textContent = t(state, "load_failed_error", "Failed to load catalogue source data for the moment editor.");
  }
}

init();
