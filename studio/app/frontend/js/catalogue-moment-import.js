import {
  applyCatalogueMomentImport,
  previewCatalogueMomentImport
} from "./catalogue-editor-service-client.js";
import { catalogueGeneratedStatusText } from "./catalogue-editor-readiness.js";
import { displayValue } from "./catalogue-editor-records.js";
import {
  MOMENT_EDITABLE_FIELDS as EDITABLE_FIELDS,
  normalizeMomentFilename,
  normalizeMomentId,
  normalizeMomentRecord,
  normalizeText
} from "./catalogue-moment-fields.js";
import { buildStudioActivityContext } from "./studio-activity-context.js";

function escapeHtml(value) {
  return normalizeText(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function text(context, key, fallback, tokens = null) {
  if (context && typeof context.text === "function") {
    return context.text(key, fallback, tokens);
  }
  if (!tokens) return fallback;
  return Object.entries(tokens).reduce((value, [token, replacement]) => {
    return value.replace(new RegExp(`\\{${token}\\}`, "g"), () => replacement == null ? "" : String(replacement));
  }, fallback);
}

function setTextWithState(context, node, value, state = "") {
  if (context && typeof context.setTextWithState === "function") {
    context.setTextWithState(node, value, state);
    return;
  }
  if (!node) return;
  node.textContent = value || "";
  if (state) node.dataset.state = state;
  else delete node.dataset.state;
}

function setFieldNodeValue(node, value) {
  if (!node) return;
  const normalized = normalizeText(value);
  if ("value" in node) {
    node.value = normalized;
  } else {
    node.textContent = displayValue(normalized, { emptyText: "-" });
  }
}

function getFieldNodeValue(node) {
  if (!node) return "";
  if ("value" in node) return node.value;
  return normalizeText(node.textContent);
}

function buildImportActivityContext(momentId) {
  return buildStudioActivityContext({
    pageId: "catalogue-moment",
    actionId: "import-moment",
    route: "/studio/catalogue-moment/",
    controlId: "catalogueMomentImportApply",
    controlSelector: "#catalogueMomentImportApply",
    recordIdField: "moment_id",
    recordId: momentId
  });
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

function importGeneratedStatusText(context, preview) {
  return catalogueGeneratedStatusText(preview, {
    includeIndex: false,
    missingText: text(context, "import_preview_missing_value", "none")
  });
}

function buildImportSummaryHtml(state, context, preview) {
  if (!preview) {
    return `
      <p class="tagStudioForm__meta">${escapeHtml(text(context, "import_empty_state", "Preview a source file to inspect the resolved moment metadata."))}</p>
    `;
  }

  const fields = [
    { label: text(context, "import_preview_field_moment_id", "moment id"), value: preview.moment_id },
    { label: text(context, "import_preview_field_title", "title"), value: preview.title },
    { label: text(context, "import_preview_field_status", "status"), value: preview.status },
    { label: text(context, "import_preview_field_date", "date"), value: preview.date },
    { label: text(context, "import_preview_field_date_display", "date display"), value: preview.date_display },
    { label: text(context, "import_preview_field_published_date", "published date"), value: preview.published_date },
    { label: text(context, "import_preview_field_image_file", "image file"), value: preview.image_file },
    {
      label: text(context, "import_preview_field_image_status", "image status"),
      value: preview.source_image_exists
        ? text(context, "import_preview_image_present", "source image found")
        : text(context, "import_preview_image_missing", "no source image found; media generation will be blocked")
    },
    {
      label: text(context, "import_preview_field_generated_status", "generated status"),
      value: importGeneratedStatusText(context, preview)
    },
    {
      label: text(context, "import_preview_field_source_path", "source path"),
      value: preview.source_path
    }
  ];

  return fields.map((field) => `
    <div class="tagStudioForm__field">
      <span class="tagStudioForm__label">${escapeHtml(field.label)}</span>
      <span class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(normalizeText(field.value) || text(context, "import_preview_missing_value", "none"))}</span>
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

function buildImportDetailSections(state, context) {
  const preview = state.importPreview;
  if (!preview) {
    return `
      <p class="tagStudioForm__meta">${escapeHtml(text(context, "import_empty_state", "Preview a source file to inspect the resolved moment metadata."))}</p>
    `;
  }

  const sections = [];
  const errors = Array.isArray(preview.errors) ? preview.errors : [];
  const build = state.importBuild || {};
  const sourceResultSummary = normalizeText(build.summary || preview.summary)
    || text(context, "import_source_result_summary", "Import writes draft prose and metadata only. Publish from this editor when ready.");

  sections.push(`
    <section class="catalogueWorkDetails__section">
      <div class="tagStudio__headingRow">
        <h3 class="tagStudioForm__key">validation</h3>
      </div>
      ${errors.length ? `
        <p class="tagStudioForm__meta">${escapeHtml(text(context, "import_preview_errors_intro", "Source file issues:"))}</p>
        <div class="catalogueWorkDetails__rows">
          ${errors.map((error) => `
            <div class="catalogueWorkDetails__row">
              <span class="catalogueWorkDetails__link">error</span>
              <span class="catalogueWorkDetails__title">${escapeHtml(error)}</span>
            </div>
          `).join("")}
        </div>
      ` : `
        <p class="tagStudioForm__meta">${escapeHtml(text(context, "import_preview_status_ready", "Moment source preview ready."))}</p>
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

export function currentImportMomentFile(state) {
  return normalizeText(state.importFileNode && state.importFileNode.value);
}

export function updateImportState(state, context = {}) {
  if (!state.isImportMode) {
    state.importPreviewButton.hidden = true;
    state.importApplyButton.hidden = true;
    state.importSourceNode.hidden = true;
    state.importSourceSummaryNode.textContent = "";
    state.importImageGuidanceNode.textContent = "";
    if (context && typeof context.syncRouteBusyState === "function") context.syncRouteBusyState();
    return;
  }
  const fileValue = currentImportMomentFile(state);
  const preview = state.importPreview;
  const previewMatchesInput = preview && normalizeMomentFilename(preview.moment_file) === normalizeMomentFilename(fileValue);
  const editorBusy = state.isSaving || state.isBuilding || state.isDeleting;
  state.importPreviewButton.hidden = false;
  state.importApplyButton.hidden = false;
  state.importSourceNode.hidden = false;
  state.importSourceSummaryNode.textContent = text(context, "import_source_summary", "Moment prose is imported as body-only Markdown. Metadata is stored in catalogue source JSON, not prose front matter.");
  state.importImageGuidanceNode.textContent = text(context, "import_image_guidance", "Missing images are acceptable in this phase. The public moment page handles missing hero images cleanly.");
  state.importPreviewButton.disabled = state.importIsBusy || editorBusy || !state.serverAvailable || !fileValue;
  state.importApplyButton.disabled = state.importIsBusy || editorBusy || !state.serverAvailable || !preview || !previewMatchesInput || !preview.valid;
  state.summaryNode.innerHTML = buildImportSummaryHtml(state, context, preview);
  state.readinessNode.innerHTML = buildImportDetailSections(state, context);
  if (context && typeof context.syncRouteBusyState === "function") context.syncRouteBusyState();
}

export function clearImportPreview(state, context = {}) {
  state.importPreview = null;
  state.importBuild = null;
  state.importSteps = [];
  updateImportState(state, context);
}

export function readRequestedImportFile() {
  try {
    const url = new URL(window.location.href);
    return normalizeText(url.searchParams.get("file"));
  } catch (error) {
    return "";
  }
}

export function writeRequestedImportFile(momentFile) {
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

export async function previewMomentImport(state, context = {}) {
  const momentFile = currentImportMomentFile(state);
  if (!momentFile) {
    setTextWithState(context, state.importStatusNode, text(context, "import_file_required", "Enter a moment markdown filename."), "error");
    return;
  }

  state.importIsBusy = true;
  updateImportState(state, context);
  setTextWithState(context, state.importStatusNode, text(context, "import_preview_status_loading", "Loading moment source preview..."), "pending");
  setTextWithState(context, state.importWarningNode, "");
  setTextWithState(context, state.importResultNode, "");
  try {
    const response = await previewCatalogueMomentImport({
      moment_file: momentFile,
      metadata: readImportMetadata(state)
    });
    state.importPreview = response && response.preview ? response.preview : null;
    fillImportMetadataFromPreview(state, state.importPreview);
    state.importBuild = response && response.build ? response.build : null;
    state.importSteps = [];
    if (state.importPreview && state.importPreview.valid) {
      setTextWithState(context, state.importStatusNode, text(context, "import_preview_status_ready", "Moment source preview ready."), "success");
    } else {
      setTextWithState(context, state.importStatusNode, text(context, "import_preview_status_invalid", "Fix source-file issues before importing the moment."), "warning");
    }
  } catch (error) {
    state.importPreview = error && error.payload && error.payload.preview ? error.payload.preview : null;
    state.importBuild = null;
    state.importSteps = [];
    setTextWithState(context, state.importStatusNode, `${text(context, "import_preview_status_failed", "Moment source preview failed.")} ${normalizeText(error && error.message)}`.trim(), "error");
  } finally {
    state.importIsBusy = false;
    updateImportState(state, context);
  }
}

export async function applyMomentImport(state, context = {}) {
  const preview = state.importPreview;
  const momentFile = currentImportMomentFile(state);
  if (!preview || normalizeMomentFilename(preview.moment_file) !== normalizeMomentFilename(momentFile)) {
    setTextWithState(context, state.importStatusNode, text(context, "import_result_missing_preview", "Preview the source file before importing."), "error");
    return;
  }
  if (!preview.valid) {
    setTextWithState(context, state.importStatusNode, text(context, "import_preview_status_invalid", "Fix source-file issues before importing the moment."), "error");
    return;
  }

  state.importIsBusy = true;
  updateImportState(state, context);
  setTextWithState(context, state.importStatusNode, text(context, "import_status_running", "Importing draft moment source..."), "pending");
  setTextWithState(context, state.importWarningNode, "");
  setTextWithState(context, state.importResultNode, "");
  try {
    const metadata = readImportMetadata(state);
    const momentId = normalizeMomentId(normalizeMomentFilename(momentFile).replace(/\.md$/i, ""));
    const response = await applyCatalogueMomentImport({
      moment_file: momentFile,
      metadata,
      activity_context: buildImportActivityContext(momentId)
    });
    state.importPreview = response && response.preview ? response.preview : state.importPreview;
    state.importBuild = response && response.build ? response.build : state.importBuild;
    state.importSteps = Array.isArray(response && response.steps) ? response.steps : [];
    const importedMomentId = normalizeMomentId(response && response.moment_id ? response.moment_id : state.importPreview && state.importPreview.moment_id);
    const importedRecord = normalizeMomentRecord(importedMomentId, {
      ...metadata,
      moment_id: importedMomentId,
      status: "draft"
    });
    clearRequestedImportFile();
    if (context && typeof context.completeImport === "function") {
      await context.completeImport({ momentId: importedMomentId, record: importedRecord });
    }
    setTextWithState(context, state.statusNode, text(context, "import_status_success", "Moment import completed."), "success");
    setTextWithState(
      context,
      state.resultNode,
      text(context, "import_result_success", "Imported draft moment {moment_id}.", { moment_id: importedMomentId }),
      "success"
    );
  } catch (error) {
    const payload = error && error.payload ? error.payload : null;
    state.importPreview = payload && payload.preview ? payload.preview : state.importPreview;
    state.importBuild = payload && payload.build ? payload.build : state.importBuild;
    state.importSteps = Array.isArray(payload && payload.steps) ? payload.steps : [];
    setTextWithState(context, state.importStatusNode, `${text(context, "import_status_failed", "Moment import failed.")} ${normalizeText(error && error.message)}`.trim(), "error");
  } finally {
    state.importIsBusy = false;
    updateImportState(state, context);
  }
}
