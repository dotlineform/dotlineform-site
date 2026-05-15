import { getStudioText } from "./studio-config.js";
import { buildOfflineAssignmentsExport } from "./tag-assignments-offline.js";
import {
  renderStudioModalActions,
  renderStudioModalFrame
} from "./studio-modal.js";
import { seriesTagsUi } from "./studio-ui.js";

const UI = seriesTagsUi;
const { className: UI_CLASS } = UI;

export function renderSessionModal(state) {
  if (!state.refs.sessionModalHost) return;
  const exportPayload = buildOfflineAssignmentsExport(state.offlineSession);
  const stagedSeriesIds = Object.keys(exportPayload.series || {}).sort();
  const hasStaged = stagedSeriesIds.length > 0;
  const bodyHtml = `
    <div class="tagStudioToolbar seriesTagsSession">
      <div class="tagStudioToolbar__row seriesTagsSession__row" data-role="${UI.role.sessionSummary}">
        <span class="${UI_CLASS.sessionLabel}">${escapeHtml(seriesTagsText(state.config, "session_summary_label", "Offline session"))}</span>
        <span class="${UI_CLASS.sessionValue}">${escapeHtml(seriesTagsText(
          state.config,
          "session_summary_value",
          "{count} staged series",
          { count: String(stagedSeriesIds.length) }
        ))}</span>
        <span class="${UI_CLASS.sessionValue}">${escapeHtml(seriesTagsText(
          state.config,
          "session_updated_value",
          "Updated: {updated_at}",
          { updated_at: exportPayload.updated_at_utc || seriesTagsText(state.config, "session_updated_empty", "not yet") }
        ))}</span>
      </div>
      <div class="tagStudioToolbar__row seriesTagsSession__row" data-role="${UI.role.sessionActions}">
        <button type="button" class="tagStudio__button ${UI_CLASS.sessionAction}" data-session-action="copy"${hasStaged ? "" : " disabled"}>
          ${escapeHtml(seriesTagsText(state.config, "session_copy_button", "Copy JSON"))}
        </button>
        <button type="button" class="tagStudio__button ${UI_CLASS.sessionAction}" data-session-action="download"${hasStaged ? "" : " disabled"}>
          ${escapeHtml(seriesTagsText(state.config, "session_download_button", "Download JSON"))}
        </button>
        <button type="button" class="tagStudio__button ${UI_CLASS.sessionAction}" data-session-action="clear"${hasStaged ? "" : " disabled"}>
          ${escapeHtml(seriesTagsText(state.config, "session_clear_button", "Clear session"))}
        </button>
      </div>
      <p class="tagStudioToolbar__result" data-role="${UI.role.sessionResult}"${state.resultKind ? ` data-state="${escapeHtml(state.resultKind)}"` : ""}>${escapeHtml(state.resultText || "")}</p>
    </div>
  `;
  state.refs.sessionModalHost.innerHTML = renderStudioModalFrame({
    modalRole: UI.role.sessionModal,
    backdropRole: UI.role.closeSessionModal,
    titleId: "seriesTagsSessionModalTitle",
    title: seriesTagsText(state.config, "session_modal_title", "Offline session"),
    bodyHtml,
    hidden: !state.sessionModalOpen,
    actionsHtml: renderStudioModalActions([{
      label: seriesTagsText(state.config, "modal_close_button", "Close"),
      role: UI.role.closeSessionModal
    }])
  });
}

export function renderImportModal(state) {
  if (!state.refs.importModalHost) return;
  const preview = state.importPreview;
  const hasFile = Boolean(state.importFile);
  const canApply = Boolean(preview && (Number(preview.applicable_count) > 0 || Number(preview.conflict_count) > 0));
  const bodyHtml = `
    <div class="tagStudioToolbar tagStudioToolbar--modalImport seriesTagsSession">
      <div class="tagStudioToolbar__row seriesTagsSession__row" data-role="${UI.role.sessionImport}">
        <input type="file" accept="application/json,.json" hidden>
        <button type="button" class="tagStudio__button ${UI_CLASS.sessionAction}" data-import-action="choose-file">
          ${escapeHtml(seriesTagsText(state.config, "session_import_choose_button", "Choose file"))}
        </button>
        <button type="button" class="tagStudio__button ${UI_CLASS.sessionAction}" data-import-action="preview-import"${hasFile ? "" : " disabled"}>
          ${escapeHtml(seriesTagsText(state.config, "session_import_preview_button", "Preview import"))}
        </button>
        <button type="button" class="tagStudio__button ${UI_CLASS.sessionAction}" data-import-action="apply-import"${canApply ? "" : " disabled"}>
          ${escapeHtml(seriesTagsText(state.config, "session_import_apply_button", "Apply import"))}
        </button>
        <span class="${UI_CLASS.sessionValue}">${escapeHtml(
          state.importFile
            ? seriesTagsText(state.config, "session_import_selected_file", "Selected: {filename}", { filename: state.importFile.name })
            : seriesTagsText(state.config, "session_import_no_file", "No import file selected.")
        )}</span>
      </div>
      <div class="seriesTagsSession__review" data-role="${UI.role.sessionReview}">${renderImportReview(state)}</div>
      <p class="tagStudioToolbar__result" data-role="${UI.role.importResult}"${state.resultKind ? ` data-state="${escapeHtml(state.resultKind)}"` : ""}>${escapeHtml(state.resultText || "")}</p>
    </div>
  `;
  state.refs.importModalHost.innerHTML = renderStudioModalFrame({
    modalRole: UI.role.importModal,
    backdropRole: UI.role.closeImportModal,
    titleId: "seriesTagsImportModalTitle",
    title: seriesTagsText(state.config, "import_modal_title", "Import assignments"),
    bodyHtml,
    hidden: !state.importModalOpen,
    actionsHtml: renderStudioModalActions([{
      label: seriesTagsText(state.config, "modal_close_button", "Close"),
      role: UI.role.closeImportModal
    }])
  });
}

function renderImportReview(state) {
  const preview = state.importPreview;
  if (!preview) return "";

  const rows = (preview.series || []).map((row) => renderImportReviewRow(state, row)).join("");
  return `
    <div class="seriesTagsSession__reviewList">
      ${rows}
    </div>
  `;
}

function renderImportReviewRow(state, row) {
  const seriesId = String(row && row.series_id || "").trim();
  const status = String(row && row.status || "").trim();
  const invalidWorkIds = Array.isArray(row && row.invalid_work_ids) ? row.invalid_work_ids : [];
  const resolutionControl = status === "conflict"
    ? `
      <label class="${UI_CLASS.sessionReviewMeta}">
        <span>${escapeHtml(seriesTagsText(state.config, "session_import_resolution_label", "resolution"))}</span>
        <select class="${UI_CLASS.sessionReviewSelect}" data-import-resolution="${escapeHtml(seriesId)}">
          <option value="skip"${String(state.importResolutions[seriesId] || "skip") === "skip" ? " selected" : ""}>${escapeHtml(seriesTagsText(state.config, "session_import_resolution_skip", "skip"))}</option>
          <option value="overwrite"${String(state.importResolutions[seriesId] || "skip") === "overwrite" ? " selected" : ""}>${escapeHtml(seriesTagsText(state.config, "session_import_resolution_overwrite", "overwrite"))}</option>
        </select>
      </label>
    `
    : "";
  const detail = status === "invalid" && invalidWorkIds.length
    ? seriesTagsText(state.config, "session_import_invalid_work_ids", "Invalid works: {work_ids}", { work_ids: invalidWorkIds.join(", ") })
    : seriesTagsText(state.config, `session_import_status_${status}`, status || "unknown");

  return `
    <div class="${UI_CLASS.sessionReviewItem}">
      <div class="${UI_CLASS.sessionReviewMeta}">
        <strong>${escapeHtml(seriesId)}</strong>
        <span>${escapeHtml(detail)}</span>
      </div>
      ${resolutionControl}
    </div>
  `;
}

function escapeHtml(value) {
  return String(value == null ? "" : value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function seriesTagsText(config, key, fallback, tokens) {
  return getStudioText(config, `series_tags.${key}`, fallback, tokens);
}
