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

const MODE_LABELS = Object.freeze({
  works: "works",
  work_details: "work details"
});

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
  return getStudioText(state.config, `bulk_add_work.${key}`, fallback, tokens);
}

function workbookPath(state, preview = null) {
  if (preview && preview.workbook_path) return preview.workbook_path;
  return normalizeText(state.workbookPath) || "data/works_bulk_import.xlsx";
}

function buildSummaryHtml(state, preview) {
  const summary = preview && preview.summary ? preview.summary : {};
  const fields = [
    { label: t(state, "summary_mode", "mode"), value: MODE_LABELS[preview && preview.mode] || MODE_LABELS[state.mode] || state.mode },
    { label: t(state, "summary_workbook", "workbook"), value: workbookPath(state, preview) },
    { label: t(state, "summary_candidate_rows", "candidate rows"), value: String(Number(summary.candidate_rows) || 0) },
    { label: t(state, "summary_importable", "importable"), value: String(Number(summary.importable_count) || 0) },
    { label: t(state, "summary_duplicates", "duplicates"), value: String(Number(summary.duplicate_count) || 0) },
    { label: t(state, "summary_blocked", "blocked"), value: String(Number(summary.blocked_count) || 0) }
  ];
  return fields.map((field) => `
    <div class="tagStudioForm__field">
      <span class="tagStudioForm__label">${escapeHtml(field.label)}</span>
      <span class="tagStudio__input tagStudioForm__readonly">${escapeHtml(field.value)}</span>
    </div>
  `).join("");
}

function buildReasonList(reasonCounts) {
  const entries = Object.entries(reasonCounts || {});
  if (!entries.length) return "";
  return `
    <ul class="buildActivityEntry__detailList">
      ${entries.map(([reason, count]) => `
        <li class="buildActivityEntry__detailItem">
          <span class="buildActivityEntry__detailLabel">${escapeHtml(reason)}</span>
          <span class="buildActivityEntry__detailValue">${escapeHtml(String(count))}</span>
        </li>
      `).join("")}
    </ul>
  `;
}

function buildBlockedRowsHtml(rows) {
  if (!Array.isArray(rows) || !rows.length) return "";
  return `
    <div class="catalogueWorkDetails__rows">
      ${rows.map((row) => `
        <div class="catalogueWorkDetails__row">
          <span class="catalogueWorkDetails__link">${escapeHtml(row.id || `row ${row.row_number || ""}`)}</span>
          <span class="catalogueWorkDetails__title">${escapeHtml(row.message || "")}</span>
        </div>
      `).join("")}
    </div>
  `;
}

function renderPreviewDetails(state) {
  const preview = state.preview;
  if (!preview) {
    state.previewDetailsNode.innerHTML = `<p class="tagStudioForm__meta">${escapeHtml(t(state, "preview_empty", "Run preview to inspect workbook rows before import."))}</p>`;
    return;
  }

  const sections = [];
  const importableIds = Array.isArray(preview.importable_ids) ? preview.importable_ids : [];
  const duplicates = preview.duplicates || {};
  const blocked = preview.blocked || {};

  sections.push(`
    <section class="catalogueWorkDetails__section">
      <div class="tagStudio__headingRow">
        <h3 class="tagStudioForm__key">${escapeHtml(t(state, "section_importable", "importable"))}</h3>
      </div>
      <p class="tagStudioForm__meta">${escapeHtml(importableIds.length ? importableIds.join(", ") : t(state, "section_none", "none"))}</p>
    </section>
  `);

  sections.push(`
    <section class="catalogueWorkDetails__section">
      <div class="tagStudio__headingRow">
        <h3 class="tagStudioForm__key">${escapeHtml(t(state, "section_duplicates", "duplicates already in source"))}</h3>
      </div>
      <p class="tagStudioForm__meta">${escapeHtml(Array.isArray(duplicates.sample_ids) && duplicates.sample_ids.length ? duplicates.sample_ids.join(", ") : t(state, "section_none", "none"))}</p>
    </section>
  `);

  sections.push(`
    <section class="catalogueWorkDetails__section">
      <div class="tagStudio__headingRow">
        <h3 class="tagStudioForm__key">${escapeHtml(t(state, "section_blocked", "blocked rows"))}</h3>
      </div>
      ${buildReasonList(blocked.reason_counts)}
      ${buildBlockedRowsHtml(blocked.rows)}
      ${(Array.isArray(blocked.validation_errors) && blocked.validation_errors.length) ? `
        <p class="tagStudioForm__meta">${escapeHtml(blocked.validation_errors.join(" | "))}</p>
      ` : ""}
      ${(!blocked.count) ? `<p class="tagStudioForm__meta">${escapeHtml(t(state, "section_none", "none"))}</p>` : ""}
    </section>
  `);

  state.previewDetailsNode.innerHTML = sections.join("");
}

function updateState(state) {
  const preview = state.preview;
  state.previewButton.disabled = state.isBusy || !state.serverAvailable;
  state.applyButton.disabled = state.isBusy || !state.serverAvailable || !preview || preview.mode !== state.mode || !preview.ready_to_apply;
  state.summaryNode.innerHTML = buildSummaryHtml(state, preview);
  renderPreviewDetails(state);
}

function clearPreview(state) {
  state.preview = null;
  updateState(state);
}

async function runPreview(state) {
  state.isBusy = true;
  updateState(state);
  setTextWithState(state.statusNode, t(state, "preview_status_running", "Running workbook import preview…"));
  setTextWithState(state.resultNode, "");
  try {
    const response = await postJson(CATALOGUE_WRITE_ENDPOINTS.importPreview, { mode: state.mode });
    state.preview = response && response.preview ? response.preview : null;
    const summary = state.preview && state.preview.summary ? state.preview.summary : {};
    setTextWithState(
      state.statusNode,
      t(state, "preview_status_success", "Preview ready: {importable} importable, {duplicates} duplicates, {blocked} blocked.", {
        importable: Number(summary.importable_count) || 0,
        duplicates: Number(summary.duplicate_count) || 0,
        blocked: Number(summary.blocked_count) || 0
      }),
      "success"
    );
    if (Number(summary.blocked_count) > 0) {
      setTextWithState(
        state.warningNode,
        t(state, "preview_blocked_warning", "Blocked rows must be fixed in {workbook} before apply.", { workbook: workbookPath(state, state.preview) }),
        "warn"
      );
    } else {
      setTextWithState(state.warningNode, "");
    }
  } catch (error) {
    setTextWithState(state.statusNode, `${t(state, "preview_status_failed", "Workbook import preview failed.")} ${normalizeText(error && error.message)}`.trim(), "error");
  } finally {
    state.isBusy = false;
    updateState(state);
  }
}

async function applyImport(state) {
  if (!state.preview || state.preview.mode !== state.mode || !state.preview.ready_to_apply) {
    setTextWithState(state.statusNode, t(state, "apply_requires_preview", "Run preview for the current mode before apply."), "error");
    return;
  }

  state.isBusy = true;
  updateState(state);
  setTextWithState(state.statusNode, t(state, "apply_status_running", "Applying workbook import…"));
  setTextWithState(state.resultNode, "");
  try {
    const response = await postJson(CATALOGUE_WRITE_ENDPOINTS.importApply, { mode: state.mode });
    state.preview = response && response.preview ? response.preview : state.preview;
    setTextWithState(
      state.statusNode,
      t(state, "apply_status_success", "Workbook import completed."),
      "success"
    );
    setTextWithState(
      state.resultNode,
      t(state, "apply_result_success", "Imported {imported} record(s); {duplicates} duplicate record(s) already existed.", {
        imported: Number(response && response.imported_count) || 0,
        duplicates: Number(response && response.duplicate_count) || 0
      }),
      "success"
    );
    setTextWithState(
      state.warningNode,
      t(state, "apply_clear_workbook", "Clear the imported rows from {workbook} after you confirm the result.", { workbook: workbookPath(state, state.preview) }),
      "warn"
    );
  } catch (error) {
    const preview = error && error.payload && error.payload.preview ? error.payload.preview : null;
    if (preview) {
      state.preview = preview;
    }
    setTextWithState(state.statusNode, `${t(state, "apply_status_failed", "Workbook import failed.")} ${normalizeText(error && error.message)}`.trim(), "error");
  } finally {
    state.isBusy = false;
    updateState(state);
  }
}

async function init() {
  const root = document.getElementById("bulkAddWorkRoot");
  const loadingNode = document.getElementById("bulkAddWorkLoading");
  const modeNode = document.getElementById("bulkAddWorkMode");
  const saveModeNode = document.getElementById("bulkAddWorkSaveMode");
  const contextNode = document.getElementById("bulkAddWorkContext");
  const statusNode = document.getElementById("bulkAddWorkStatus");
  const warningNode = document.getElementById("bulkAddWorkWarning");
  const resultNode = document.getElementById("bulkAddWorkResult");
  const workbookNode = document.getElementById("bulkAddWorkWorkbook");
  const summaryNode = document.getElementById("bulkAddWorkSummary");
  const previewDetailsNode = document.getElementById("bulkAddWorkPreviewDetails");
  const previewButton = document.getElementById("bulkAddWorkPreview");
  const applyButton = document.getElementById("bulkAddWorkApply");
  if (!root || !loadingNode || !modeNode || !saveModeNode || !contextNode || !statusNode || !warningNode || !resultNode || !workbookNode || !summaryNode || !previewDetailsNode || !previewButton || !applyButton) {
    return;
  }

  const state = {
    config: null,
    mode: "works",
    preview: null,
    serverAvailable: false,
    isBusy: false,
    statusNode,
    warningNode,
    resultNode,
    workbookNode,
    summaryNode,
    previewDetailsNode,
    previewButton,
    applyButton,
    workbookPath: normalizeText(root.dataset.workbookPath) || "data/works_bulk_import.xlsx"
  };

  try {
    const config = await loadStudioConfig();
    state.config = config;
    state.serverAvailable = Boolean(await probeCatalogueHealth());
    saveModeNode.textContent = buildSaveModeText(config, state.serverAvailable ? "post" : "offline", (cfg, key, fallback, tokens) => getStudioText(cfg, `bulk_add_work.${key}`, fallback, tokens));
    workbookNode.textContent = state.workbookPath;
    setTextWithState(
      contextNode,
      t(state, "context_hint", "Bulk import is one-way from {workbook} into canonical JSON. Use works mode for new works and work details mode for new detail rows.", { workbook: state.workbookPath })
    );
    if (!state.serverAvailable) {
      setTextWithState(statusNode, t(state, "save_mode_unavailable_hint", "Local catalogue server unavailable. Import is disabled."), "warn");
    }

    modeNode.addEventListener("change", () => {
      state.mode = normalizeText(modeNode.value) || "works";
      setTextWithState(state.resultNode, "");
      setTextWithState(state.warningNode, "");
      clearPreview(state);
    });
    previewButton.addEventListener("click", () => {
      runPreview(state).catch((error) => console.warn("bulk_add_work: unexpected preview failure", error));
    });
    applyButton.addEventListener("click", () => {
      applyImport(state).catch((error) => console.warn("bulk_add_work: unexpected apply failure", error));
    });

    updateState(state);
    root.hidden = false;
    loadingNode.hidden = true;
  } catch (error) {
    console.warn("bulk_add_work: init failed", error);
    loadingNode.textContent = "Failed to load bulk add work.";
  }
}

init();
