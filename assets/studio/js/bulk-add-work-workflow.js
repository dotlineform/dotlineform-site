import {
  applyOperationalRunButtonState
} from "./studio-operational-route.js";

export function normalizeBulkAddWorkText(value) {
  return String(value == null ? "" : value).trim();
}

export function bulkAddWorkWorkbookPath(state, preview = null) {
  if (preview && preview.workbook_path) return preview.workbook_path;
  return normalizeBulkAddWorkText(state.workbookPath) || "data/works_bulk_import.xlsx";
}

export function applyBulkAddWorkRunState(state) {
  const previewState = applyOperationalRunButtonState(state.previewButton, state, {
    serviceAvailable: (routeState) => routeState.serverAvailable,
    isBusy: (routeState) => routeState.isBusy
  });
  const applyState = applyOperationalRunButtonState(state.applyButton, state, {
    serviceAvailable: (routeState) => routeState.serverAvailable,
    isBusy: (routeState) => routeState.isBusy,
    canRun: (routeState) => canApplyBulkAddWorkPreview(routeState)
  });
  return {
    preview: previewState,
    apply: applyState
  };
}

export function canApplyBulkAddWorkPreview(state) {
  const preview = state && state.preview;
  return Boolean(preview && preview.mode === state.mode && preview.ready_to_apply);
}

export function renderBulkAddWorkPreviewState(state, options = {}) {
  state.summaryNode.innerHTML = buildBulkAddWorkSummaryHtml(state, state.preview, options);
  state.previewDetailsNode.innerHTML = buildBulkAddWorkPreviewDetailsHtml(state, state.preview, options);
}

export function projectBulkAddWorkApplyBlocked(state, options = {}) {
  if (canApplyBulkAddWorkPreview(state)) return null;
  return {
    status: {
      state: "error",
      text: text(options, "apply_requires_preview", "Run preview for the current mode before apply.")
    }
  };
}

export function projectBulkAddWorkPreviewStart(options = {}) {
  return {
    status: {
      state: "",
      text: text(options, "preview_status_running", "Running workbook import preview...")
    },
    result: { state: "", text: "" }
  };
}

export function projectBulkAddWorkPreviewSuccess(state, preview, options = {}) {
  const summary = preview && preview.summary ? preview.summary : {};
  const blockedCount = Number(summary.blocked_count) || 0;
  const warning = blockedCount > 0
    ? {
        state: "warn",
        text: text(options, "preview_blocked_warning", "Blocked rows must be fixed in {workbook} before apply.", {
          workbook: bulkAddWorkWorkbookPath(state, preview)
        })
      }
    : { state: "", text: "" };
  return {
    status: {
      state: "success",
      text: text(options, "preview_status_success", "Preview ready: {importable} importable, {duplicates} duplicates, {blocked} blocked.", {
        importable: Number(summary.importable_count) || 0,
        duplicates: Number(summary.duplicate_count) || 0,
        blocked: blockedCount
      })
    },
    warning
  };
}

export function projectBulkAddWorkPreviewFailure(error, options = {}) {
  return {
    status: {
      state: "error",
      text: `${text(options, "preview_status_failed", "Workbook import preview failed.")} ${normalizeBulkAddWorkText(error && error.message)}`.trim()
    }
  };
}

export function projectBulkAddWorkApplyStart(options = {}) {
  return {
    status: {
      state: "",
      text: text(options, "apply_status_running", "Applying workbook import...")
    },
    result: { state: "", text: "" }
  };
}

export function projectBulkAddWorkApplySuccess(state, response, options = {}) {
  return {
    status: {
      state: "success",
      text: text(options, "apply_status_success", "Workbook import completed.")
    },
    result: {
      state: "success",
      text: text(options, "apply_result_success", "Imported {imported} record(s); {duplicates} duplicate record(s) already existed.", {
        imported: Number(response && response.imported_count) || 0,
        duplicates: Number(response && response.duplicate_count) || 0
      })
    },
    warning: {
      state: "warn",
      text: text(options, "apply_clear_workbook", "Clear the imported rows from {workbook} after you confirm the result.", {
        workbook: bulkAddWorkWorkbookPath(state, state.preview)
      })
    }
  };
}

export function projectBulkAddWorkApplyFailure(error, options = {}) {
  return {
    status: {
      state: "error",
      text: `${text(options, "apply_status_failed", "Workbook import failed.")} ${normalizeBulkAddWorkText(error && error.message)}`.trim()
    },
    preview: error && error.payload && error.payload.preview ? error.payload.preview : null
  };
}

export function applyBulkAddWorkStatusProjection(state, projection) {
  if (!projection) return;
  if (projection.status) setTextWithState(state.statusNode, projection.status.text, projection.status.state);
  if (projection.result) setTextWithState(state.resultNode, projection.result.text, projection.result.state);
  if (projection.warning) setTextWithState(state.warningNode, projection.warning.text, projection.warning.state);
}

function buildBulkAddWorkSummaryHtml(state, preview, options) {
  const summary = preview && preview.summary ? preview.summary : {};
  const fields = [
    { label: text(options, "summary_mode", "mode"), value: modeLabel(state, preview && preview.mode ? preview.mode : state.mode, options) },
    { label: text(options, "summary_workbook", "workbook"), value: bulkAddWorkWorkbookPath(state, preview) },
    { label: text(options, "summary_candidate_rows", "candidate rows"), value: String(Number(summary.candidate_rows) || 0) },
    { label: text(options, "summary_importable", "importable"), value: String(Number(summary.importable_count) || 0) },
    { label: text(options, "summary_duplicates", "duplicates"), value: String(Number(summary.duplicate_count) || 0) },
    { label: text(options, "summary_blocked", "blocked"), value: String(Number(summary.blocked_count) || 0) }
  ];
  return fields.map((field) => `
    <div class="tagStudioForm__field">
      <span class="tagStudioForm__label">${escapeHtml(field.label)}</span>
      <span class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(field.value)}</span>
    </div>
  `).join("");
}

function buildBulkAddWorkPreviewDetailsHtml(state, preview, options) {
  if (!preview) {
    return `<p class="tagStudioForm__meta">${escapeHtml(text(options, "preview_empty", "Run preview to inspect workbook rows before import."))}</p>`;
  }

  const sections = [];
  const importableIds = Array.isArray(preview.importable_ids) ? preview.importable_ids : [];
  const duplicates = preview.duplicates || {};
  const blocked = preview.blocked || {};

  sections.push(`
    <section class="catalogueWorkDetails__section">
      <div class="tagStudio__headingRow">
        <h3 class="tagStudioForm__key">${escapeHtml(text(options, "section_importable", "importable"))}</h3>
      </div>
      <p class="tagStudioForm__meta">${escapeHtml(importableIds.length ? importableIds.join(", ") : text(options, "section_none", "none"))}</p>
    </section>
  `);

  sections.push(`
    <section class="catalogueWorkDetails__section">
      <div class="tagStudio__headingRow">
        <h3 class="tagStudioForm__key">${escapeHtml(text(options, "section_duplicates", "duplicates already in source"))}</h3>
      </div>
      <p class="tagStudioForm__meta">${escapeHtml(Array.isArray(duplicates.sample_ids) && duplicates.sample_ids.length ? duplicates.sample_ids.join(", ") : text(options, "section_none", "none"))}</p>
    </section>
  `);

  sections.push(`
    <section class="catalogueWorkDetails__section">
      <div class="tagStudio__headingRow">
        <h3 class="tagStudioForm__key">${escapeHtml(text(options, "section_blocked", "blocked rows"))}</h3>
      </div>
      ${buildReasonList(blocked.reason_counts)}
      ${buildBlockedRowsHtml(blocked.rows)}
      ${(Array.isArray(blocked.validation_errors) && blocked.validation_errors.length) ? `
        <p class="tagStudioForm__meta">${escapeHtml(blocked.validation_errors.join(" | "))}</p>
      ` : ""}
      ${(!blocked.count) ? `<p class="tagStudioForm__meta">${escapeHtml(text(options, "section_none", "none"))}</p>` : ""}
    </section>
  `);

  return sections.join("");
}

function modeLabel(state, mode, options) {
  if (mode === "work_details") return text(options, "mode_option_work_details", "work details");
  return text(options, "mode_option_works", "works");
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

function setTextWithState(node, value, state = "") {
  if (!node) return;
  node.textContent = value || "";
  if (state) node.dataset.state = state;
  else delete node.dataset.state;
}

function text(options, key, fallback, tokens) {
  return typeof options.text === "function" ? options.text(key, fallback, tokens) : fallback;
}

function escapeHtml(value) {
  return normalizeBulkAddWorkText(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
