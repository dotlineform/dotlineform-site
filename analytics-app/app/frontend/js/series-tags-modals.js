import { getAnalyticsText } from "./analytics-config.js";
import {
  renderAnalyticsModalActions,
  renderAnalyticsModalFrame
} from "./analytics-modal.js";
import { seriesTagsUi } from "./analytics-ui.js";

const UI = seriesTagsUi;
const { className: UI_CLASS } = UI;

export function renderSessionModal(state) {
  if (!state.refs.sessionModalHost) return;
  const exportPayload = getSessionExportPayload(state);
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
        <button type="button" class="tagStudio__button tagStudio__button--defaultWidth ${UI_CLASS.sessionAction}" data-session-action="copy"${hasStaged ? "" : " disabled"}>
          ${escapeHtml(seriesTagsText(state.config, "session_copy_button", "Copy JSON"))}
        </button>
        <button type="button" class="tagStudio__button tagStudio__button--defaultWidth ${UI_CLASS.sessionAction}" data-session-action="download"${hasStaged ? "" : " disabled"}>
          ${escapeHtml(seriesTagsText(state.config, "session_download_button", "Download JSON"))}
        </button>
        <button type="button" class="tagStudio__button tagStudio__button--defaultWidth ${UI_CLASS.sessionAction}" data-session-action="clear"${hasStaged ? "" : " disabled"}>
          ${escapeHtml(seriesTagsText(state.config, "session_clear_button", "Clear session"))}
        </button>
      </div>
    </div>
  `;
  state.refs.sessionModalHost.innerHTML = renderAnalyticsModalFrame({
    modalRole: UI.role.sessionModal,
    backdropRole: UI.role.closeSessionModal,
    titleId: "seriesTagsSessionModalTitle",
    title: seriesTagsText(state.config, "session_modal_title", "Offline session"),
    size: "compact",
    bodyHtml,
    statusHtml: renderModalStatus(state, UI.role.sessionResult),
    hidden: !state.sessionModalOpen,
    actionsHtml: renderAnalyticsModalActions([{
      label: seriesTagsText(state.config, "modal_close_button", "Close"),
      role: UI.role.closeSessionModal
    }])
  });
  syncModalFocusAfterRender(state, "session");
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
        <button type="button" class="tagStudio__button tagStudio__button--defaultWidth ${UI_CLASS.sessionAction}" data-import-action="choose-file">
          ${escapeHtml(seriesTagsText(state.config, "session_import_choose_button", "Choose file"))}
        </button>
        <button type="button" class="tagStudio__button tagStudio__button--defaultWidth ${UI_CLASS.sessionAction}" data-import-action="preview-import"${hasFile ? "" : " disabled"}>
          ${escapeHtml(seriesTagsText(state.config, "session_import_preview_button", "Preview import"))}
        </button>
        <span class="${UI_CLASS.sessionValue}">${escapeHtml(
          state.importFile
            ? seriesTagsText(state.config, "session_import_selected_file", "Selected: {filename}", { filename: state.importFile.name })
            : seriesTagsText(state.config, "session_import_no_file", "No import file selected.")
        )}</span>
      </div>
      <div class="seriesTagsSession__review" data-role="${UI.role.sessionReview}">${renderImportReview(state)}</div>
    </div>
  `;
  state.refs.importModalHost.innerHTML = renderAnalyticsModalFrame({
    modalRole: UI.role.importModal,
    backdropRole: UI.role.closeImportModal,
    titleId: "seriesTagsImportModalTitle",
    title: seriesTagsText(state.config, "import_modal_title", "Import assignments"),
    size: "wide",
    bodyHtml,
    statusHtml: renderModalStatus(state, UI.role.importResult),
    hidden: !state.importModalOpen,
    actionsHtml: renderAnalyticsModalActions([
      {
        label: seriesTagsText(state.config, "modal_close_button", "Close"),
        role: UI.role.closeImportModal
      },
      {
        label: seriesTagsText(state.config, "session_import_apply_button", "Apply import"),
        role: UI.role.applyImport,
        primary: true,
        disabled: !canApply
      }
    ])
  });
  syncModalFocusAfterRender(state, "import");
}

export function wireSeriesTagsModalEvents(state, callbacks = {}) {
  if (state.refs.sessionModalHost) {
    state.refs.sessionModalHost.addEventListener("click", (event) => {
      if (event.target.closest(`[data-role="${UI.role.closeSessionModal}"]`)) {
        closeSeriesTagsModal(state, "session", callbacks);
        return;
      }
      const action = event.target.closest("button[data-session-action]");
      if (!action) return;
      callbacks.onSessionAction?.(String(action.getAttribute("data-session-action") || ""));
    });
  }

  if (state.refs.importModalHost) {
    state.refs.importModalHost.addEventListener("click", (event) => {
      if (event.target.closest(`[data-role="${UI.role.closeImportModal}"]`)) {
        closeSeriesTagsModal(state, "import", callbacks);
        return;
      }
      if (event.target.closest(`[data-role="${UI.role.applyImport}"]`)) {
        callbacks.onImportAction?.("apply-import");
        return;
      }
      const action = event.target.closest("button[data-import-action]");
      if (!action) return;
      const actionName = String(action.getAttribute("data-import-action") || "");
      if (actionName === "choose-file") {
        const input = state.refs.importModalHost.querySelector('input[type="file"]');
        if (input) input.click();
        return;
      }
      callbacks.onImportAction?.(actionName);
    });

    state.refs.importModalHost.addEventListener("change", (event) => {
      const input = event.target;
      if (isFileInput(input)) {
        const files = input.files;
        callbacks.onImportFileChange?.(files && files.length ? files[0] : null);
        return;
      }
      const select = event.target.closest("select[data-import-resolution]");
      if (!select) return;
      const seriesId = normalizeModalValue(select.getAttribute("data-import-resolution"));
      if (!seriesId) return;
      callbacks.onImportResolutionChange?.(seriesId, String(select.value || "skip").trim().toLowerCase());
    });
  }

  document.addEventListener("keydown", (event) => {
    const modalKind = state.importModalOpen ? "import" : state.sessionModalOpen ? "session" : "";
    if (!modalKind) return;

    if (event.key === "Escape") {
      event.preventDefault();
      closeSeriesTagsModal(state, modalKind, callbacks);
      return;
    }

    if (event.key !== "Tab") return;
    trapModalFocus(event, getModalElement(state, modalKind));
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

function renderModalStatus(state, role) {
  const message = String(state.resultText || "");
  const stateAttr = state.resultKind ? ` data-state="${escapeHtml(state.resultKind)}"` : "";
  const hiddenAttr = message ? "" : " hidden";
  return `<p class="tagStudioForm__status tagStudioModal__status" data-role="${escapeHtml(role)}"${stateAttr}${hiddenAttr}>${escapeHtml(message)}</p>`;
}

function closeSeriesTagsModal(state, modalKind, callbacks = {}) {
  const config = modalConfig(modalKind);
  if (!config || !state[config.openProp]) return;
  const restoreTarget = state[config.restoreProp];
  state[config.openProp] = false;
  state[config.focusProp] = false;
  state[config.restoreProp] = null;
  callbacks.onModalStateChange?.();
  restoreModalFocus(restoreTarget);
}

function syncModalFocusAfterRender(state, modalKind) {
  const config = modalConfig(modalKind);
  if (!config || !state[config.openProp]) {
    if (config) state[config.focusProp] = false;
    return;
  }
  const modal = getModalElement(state, modalKind);
  if (!modal) return;
  if (state[config.focusProp] && modal.contains(document.activeElement)) return;
  const target = modal.querySelector(config.focusSelector)
    || modal.querySelector(`[data-role="${config.closeRole}"]`)
    || modal.querySelector("[role='dialog']");
  if (target && typeof target.focus === "function") target.focus();
  state[config.focusProp] = true;
}

function trapModalFocus(event, modal) {
  if (!modal) return;
  const nodes = focusableNodes(modal);
  if (!nodes.length) return;
  const first = nodes[0];
  const last = nodes[nodes.length - 1];
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
    return;
  }
  if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}

function focusableNodes(root) {
  return Array.from(root.querySelectorAll([
    "a[href]",
    "button:not([disabled])",
    "input:not([disabled])",
    "select:not([disabled])",
    "textarea:not([disabled])",
    "[tabindex]:not([tabindex='-1'])"
  ].join(","))).filter((node) => node.getClientRects().length);
}

function getModalElement(state, modalKind) {
  const config = modalConfig(modalKind);
  if (!config || !state.refs[config.hostRef]) return null;
  return state.refs[config.hostRef].querySelector(`[data-role="${config.modalRole}"]`);
}

function restoreModalFocus(target) {
  try {
    if (target && typeof target.focus === "function") {
      target.focus({ preventScroll: true });
    }
  } catch (_error) {
    // Focus return is best effort when a route re-render removes the opener.
  }
}

function modalConfig(modalKind) {
  if (modalKind === "session") {
    return {
      hostRef: "sessionModalHost",
      modalRole: UI.role.sessionModal,
      closeRole: UI.role.closeSessionModal,
      openProp: "sessionModalOpen",
      focusProp: "sessionModalFocusReady",
      restoreProp: "sessionModalRestoreFocus",
      focusSelector: 'button[data-session-action="copy"]:not([disabled])'
    };
  }
  if (modalKind === "import") {
    return {
      hostRef: "importModalHost",
      modalRole: UI.role.importModal,
      closeRole: UI.role.closeImportModal,
      openProp: "importModalOpen",
      focusProp: "importModalFocusReady",
      restoreProp: "importModalRestoreFocus",
      focusSelector: 'button[data-import-action="choose-file"]:not([disabled])'
    };
  }
  return null;
}

function escapeHtml(value) {
  return String(value == null ? "" : value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function seriesTagsText(config, key, fallback, tokens) {
  return getAnalyticsText(config, `series_tags.${key}`, fallback, tokens);
}

function isFileInput(value) {
  return value && value.tagName === "INPUT" && String(value.type || "").toLowerCase() === "file";
}

function normalizeModalValue(value) {
  return String(value == null ? "" : value).trim().toLowerCase();
}

function getSessionExportPayload(state) {
  const session = state && state.offlineSession && typeof state.offlineSession === "object"
    ? state.offlineSession
    : {};
  const series = session.series && typeof session.series === "object"
    ? session.series
    : {};
  return {
    version: String(session.version || "tag_assignments_offline_v1"),
    updated_at_utc: String(session.updated_at_utc || ""),
    series
  };
}
