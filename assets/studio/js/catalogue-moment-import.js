import {
  getStudioText,
  loadStudioConfig
} from "./studio-config.js";
import {
  CATALOGUE_WRITE_ENDPOINTS,
  postJson,
  probeCatalogueHealth
} from "./studio-transport.js";
import { buildSaveModeText } from "./tag-studio-save.js";

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

function setTextWithState(node, text, state = "") {
  if (!node) return;
  node.textContent = text || "";
  if (state) node.dataset.state = state;
  else delete node.dataset.state;
}

function t(state, key, fallback, tokens = null) {
  return getStudioText(state.config, `catalogue_moment_import.${key}`, fallback, tokens);
}

function normalizeMomentFilename(value) {
  const raw = normalizeText(value).toLowerCase();
  if (!raw) return "";
  return raw.endsWith(".md") ? raw : `${raw}.md`;
}

function currentMomentFile(state) {
  return normalizeText(state.fileNode && state.fileNode.value);
}

function generatedStatusText(state, preview) {
  if (!preview) return t(state, "preview_missing_value", "none");
  const parts = [];
  parts.push(preview.generated_page_exists ? "page yes" : "page no");
  parts.push(preview.generated_json_exists ? "json yes" : "json no");
  return parts.join(" / ");
}

function buildSummaryHtml(state, preview) {
  if (!preview) {
    return `
      <p class="tagStudioForm__meta">${escapeHtml(t(state, "empty_state", "Preview a source file to inspect the resolved moment metadata."))}</p>
    `;
  }

  const fields = [
    { label: t(state, "preview_field_moment_id", "moment id"), value: preview.moment_id },
    { label: t(state, "preview_field_title", "title"), value: preview.title },
    { label: t(state, "preview_field_status", "status"), value: preview.status },
    { label: t(state, "preview_field_date", "date"), value: preview.date },
    { label: t(state, "preview_field_date_display", "date display"), value: preview.date_display },
    { label: t(state, "preview_field_published_date", "published date"), value: preview.published_date },
    { label: t(state, "preview_field_image_file", "image file"), value: preview.image_file },
    {
      label: t(state, "preview_field_image_status", "image status"),
      value: preview.source_image_exists
        ? t(state, "preview_image_present", "source image found")
        : t(state, "preview_image_missing", "no source image found; public page will render without a hero image")
    },
    {
      label: t(state, "preview_field_generated_status", "generated status"),
      value: generatedStatusText(state, preview)
    },
    {
      label: t(state, "preview_field_source_path", "source path"),
      value: preview.source_path
    }
  ];

  return fields.map((field) => `
    <div class="tagStudioForm__field">
      <span class="tagStudioForm__label">${escapeHtml(field.label)}</span>
      <span class="tagStudio__input tagStudioForm__readonly">${escapeHtml(normalizeText(field.value) || t(state, "preview_missing_value", "none"))}</span>
    </div>
  `).join("");
}

function buildStepRows(steps) {
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

function buildDetailSections(state) {
  const preview = state.preview;
  if (!preview) {
    return `
      <p class="tagStudioForm__meta">${escapeHtml(t(state, "empty_state", "Preview a source file to inspect the resolved moment metadata."))}</p>
    `;
  }

  const sections = [];
  const errors = Array.isArray(preview.errors) ? preview.errors : [];
  const build = state.build || {};
  const publicUrl = normalizeText(state.publicUrl || preview.public_url);

  sections.push(`
    <section class="catalogueWorkDetails__section">
      <div class="tagStudio__headingRow">
        <h3 class="tagStudioForm__key">validation</h3>
      </div>
      ${errors.length ? `
        <p class="tagStudioForm__meta">${escapeHtml(t(state, "preview_errors_intro", "Source file issues:"))}</p>
        <div class="catalogueWorkDetails__rows">
          ${errors.map((error) => `
            <div class="catalogueWorkDetails__row">
              <span class="catalogueWorkDetails__link">error</span>
              <span class="catalogueWorkDetails__title">${escapeHtml(error)}</span>
            </div>
          `).join("")}
        </div>
      ` : `
        <p class="tagStudioForm__meta">${escapeHtml(t(state, "preview_status_ready", "Moment source preview ready."))}</p>
      `}
    </section>
  `);

  sections.push(`
    <section class="catalogueWorkDetails__section">
      <div class="tagStudio__headingRow">
        <h3 class="tagStudioForm__key">build scope</h3>
      </div>
      <p class="tagStudioForm__meta">${escapeHtml(normalizeText(build.summary || preview.summary))}</p>
      ${publicUrl ? `
        <p class="tagStudioForm__meta">
          <a href="${escapeHtml(publicUrl)}">${escapeHtml(t(state, "import_result_success_link", "Open public moment"))}</a>
        </p>
      ` : ""}
    </section>
  `);

  if (Array.isArray(state.steps) && state.steps.length) {
    sections.push(`
      <section class="catalogueWorkDetails__section">
        <div class="tagStudio__headingRow">
          <h3 class="tagStudioForm__key">build steps</h3>
        </div>
        ${buildStepRows(state.steps)}
      </section>
    `);
  }

  return sections.join("");
}

function updateState(state) {
  const fileValue = currentMomentFile(state);
  const preview = state.preview;
  const previewMatchesInput = preview && normalizeMomentFilename(preview.moment_file) === normalizeMomentFilename(fileValue);
  state.previewButton.disabled = state.isBusy || !state.serverAvailable || !fileValue;
  state.applyButton.disabled = state.isBusy || !state.serverAvailable || !preview || !previewMatchesInput || !preview.valid;
  state.summaryNode.innerHTML = buildSummaryHtml(state, preview);
  state.detailsNode.innerHTML = buildDetailSections(state);
}

function clearPreview(state) {
  state.preview = null;
  state.build = null;
  state.steps = [];
  state.publicUrl = "";
  updateState(state);
}

async function runPreview(state) {
  const momentFile = currentMomentFile(state);
  if (!momentFile) {
    setTextWithState(state.statusNode, t(state, "file_required", "Enter a moment markdown filename."), "error");
    return;
  }

  state.isBusy = true;
  updateState(state);
  setTextWithState(state.statusNode, t(state, "preview_status_loading", "Loading moment source preview…"));
  setTextWithState(state.warningNode, "");
  setTextWithState(state.resultNode, "");
  try {
    const response = await postJson(CATALOGUE_WRITE_ENDPOINTS.previewMomentImport, { moment_file: momentFile });
    state.preview = response && response.preview ? response.preview : null;
    state.build = response && response.build ? response.build : null;
    state.steps = [];
    state.publicUrl = normalizeText(response && response.preview && response.preview.public_url);
    if (state.preview && state.preview.valid) {
      setTextWithState(state.statusNode, t(state, "preview_status_ready", "Moment source preview ready."), "success");
    } else {
      setTextWithState(state.statusNode, t(state, "preview_status_invalid", "Fix source-file issues before importing the moment."), "warn");
    }
  } catch (error) {
    state.preview = error && error.payload && error.payload.preview ? error.payload.preview : null;
    state.build = null;
    state.steps = [];
    state.publicUrl = "";
    setTextWithState(state.statusNode, `${t(state, "preview_status_failed", "Moment source preview failed.")} ${normalizeText(error && error.message)}`.trim(), "error");
  } finally {
    state.isBusy = false;
    updateState(state);
  }
}

async function applyImport(state) {
  const preview = state.preview;
  const momentFile = currentMomentFile(state);
  if (!preview || normalizeMomentFilename(preview.moment_file) !== normalizeMomentFilename(momentFile)) {
    setTextWithState(state.statusNode, t(state, "import_result_missing_preview", "Preview the source file before importing."), "error");
    return;
  }
  if (!preview.valid) {
    setTextWithState(state.statusNode, t(state, "preview_status_invalid", "Fix source-file issues before importing the moment."), "error");
    return;
  }

  state.isBusy = true;
  updateState(state);
  setTextWithState(state.statusNode, t(state, "import_status_running", "Importing moment and rebuilding catalogue search…"));
  setTextWithState(state.warningNode, "");
  setTextWithState(state.resultNode, "");
  try {
    const response = await postJson(CATALOGUE_WRITE_ENDPOINTS.applyMomentImport, { moment_file: momentFile });
    state.preview = response && response.preview ? response.preview : state.preview;
    state.build = response && response.build ? response.build : state.build;
    state.steps = Array.isArray(response && response.steps) ? response.steps : [];
    state.publicUrl = normalizeText(response && response.public_url);
    setTextWithState(state.statusNode, t(state, "import_status_success", "Moment import completed."), "success");
    setTextWithState(
      state.resultNode,
      t(state, "import_result_success", "Imported {moment_id}. Open the public moment page to confirm the runtime output.", {
        moment_id: normalizeText(response && response.moment_id) || normalizeText(state.preview && state.preview.moment_id)
      }),
      "success"
    );
  } catch (error) {
    const payload = error && error.payload ? error.payload : null;
    state.preview = payload && payload.preview ? payload.preview : state.preview;
    state.build = payload && payload.build ? payload.build : state.build;
    state.steps = Array.isArray(payload && payload.steps) ? payload.steps : [];
    state.publicUrl = normalizeText(payload && payload.public_url);
    setTextWithState(state.statusNode, `${t(state, "import_status_failed", "Moment import failed.")} ${normalizeText(error && error.message)}`.trim(), "error");
  } finally {
    state.isBusy = false;
    updateState(state);
  }
}

function readRequestedFile() {
  try {
    const url = new URL(window.location.href);
    return normalizeText(url.searchParams.get("file"));
  } catch (error) {
    return "";
  }
}

function writeRequestedFile(momentFile) {
  if (!window.history || !window.history.replaceState) return;
  const nextFile = normalizeText(momentFile);
  try {
    const url = new URL(window.location.href);
    if (nextFile) url.searchParams.set("file", nextFile);
    else url.searchParams.delete("file");
    window.history.replaceState({}, "", url.toString());
  } catch (error) {
    // no-op
  }
}

async function init() {
  const root = document.getElementById("catalogueMomentImportRoot");
  const loadingNode = document.getElementById("catalogueMomentImportLoading");
  const emptyNode = document.getElementById("catalogueMomentImportEmpty");
  const saveModeNode = document.getElementById("catalogueMomentImportSaveMode");
  const contextNode = document.getElementById("catalogueMomentImportContext");
  const statusNode = document.getElementById("catalogueMomentImportStatus");
  const warningNode = document.getElementById("catalogueMomentImportWarning");
  const resultNode = document.getElementById("catalogueMomentImportResult");
  const fileLabelNode = document.getElementById("catalogueMomentImportFileLabel");
  const fileNode = document.getElementById("catalogueMomentImportFile");
  const fileDescriptionNode = document.getElementById("catalogueMomentImportFileDescription");
  const sourceSummaryNode = document.getElementById("catalogueMomentImportSourceSummary");
  const imageGuidanceNode = document.getElementById("catalogueMomentImportImageGuidance");
  const previewButton = document.getElementById("catalogueMomentImportPreview");
  const applyButton = document.getElementById("catalogueMomentImportApply");
  const summaryNode = document.getElementById("catalogueMomentImportSummary");
  const detailsNode = document.getElementById("catalogueMomentImportDetails");
  if (!root || !loadingNode || !emptyNode || !saveModeNode || !contextNode || !statusNode || !warningNode || !resultNode || !fileLabelNode || !fileNode || !fileDescriptionNode || !sourceSummaryNode || !imageGuidanceNode || !previewButton || !applyButton || !summaryNode || !detailsNode) {
    return;
  }

  const state = {
    config: null,
    preview: null,
    build: null,
    steps: [],
    publicUrl: "",
    serverAvailable: false,
    isBusy: false,
    fileNode,
    statusNode,
    warningNode,
    resultNode,
    previewButton,
    applyButton,
    summaryNode,
    detailsNode
  };

  try {
    const config = await loadStudioConfig();
    state.config = config;
    state.serverAvailable = Boolean(await probeCatalogueHealth());
    saveModeNode.textContent = buildSaveModeText(config, state.serverAvailable ? "post" : "offline", (cfg, key, fallback, tokens) => getStudioText(cfg, `catalogue_moment_import.${key}`, fallback, tokens));
    fileLabelNode.textContent = t(state, "file_label", "moment file");
    fileNode.placeholder = t(state, "file_placeholder", "keys.md");
    previewButton.textContent = t(state, "preview_button", "Preview Source File");
    applyButton.textContent = t(state, "import_button", "Import + Publish Moment");
    setTextWithState(contextNode, t(state, "context_hint", "Enter a moment markdown filename from the canonical moments source folder. This page previews the existing file and then runs a targeted import/rebuild for that one moment."));
    fileDescriptionNode.textContent = t(state, "file_description", "filename only; the source file is resolved from the canonical moments folder");
    sourceSummaryNode.textContent = t(state, "source_summary", "This workflow reads metadata from the existing source markdown file. Edit the source file directly when prose or front matter needs to change.");
    imageGuidanceNode.textContent = t(state, "image_guidance", "Missing images are acceptable in this phase. The public moment page already handles missing hero images cleanly.");
    if (!state.serverAvailable) {
      setTextWithState(statusNode, t(state, "save_mode_unavailable_hint", "Local catalogue server unavailable. Moment import is disabled."), "warn");
    }

    fileNode.value = readRequestedFile();

    fileNode.addEventListener("input", () => {
      writeRequestedFile(fileNode.value);
      setTextWithState(state.warningNode, "");
      setTextWithState(state.resultNode, "");
      clearPreview(state);
    });
    previewButton.addEventListener("click", () => {
      runPreview(state).catch((error) => console.warn("catalogue_moment_import: unexpected preview failure", error));
    });
    applyButton.addEventListener("click", () => {
      applyImport(state).catch((error) => console.warn("catalogue_moment_import: unexpected apply failure", error));
    });

    updateState(state);
    root.hidden = false;
    loadingNode.hidden = true;
    emptyNode.hidden = true;

    if (currentMomentFile(state) && state.serverAvailable) {
      runPreview(state).catch((error) => console.warn("catalogue_moment_import: initial preview failed", error));
    }
  } catch (error) {
    console.warn("catalogue_moment_import: init failed", error);
    loadingNode.textContent = "Failed to load moment import.";
  }
}

init();
