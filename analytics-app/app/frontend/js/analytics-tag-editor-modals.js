import { getAnalyticsText } from "./analytics-config.js";
import { workStateMapToObject } from "./analytics-tag-editor-domain.js";
import {
  buildPatchSnippet,
  utcTimestamp
} from "./analytics-tag-editor-save.js";
import {
  renderAnalyticsModalActions,
  renderAnalyticsModalFrame
} from "./analytics-modal.js";
import { seriesTagEditorUi } from "./analytics-ui.js";

const UI = seriesTagEditorUi;
const { className: UI_CLASS, selector: UI_SELECTOR } = UI;

export function renderAnalyticsTagEditorSaveModal(state) {
  const modalTitle = analyticsTagEditorText(state.config, "modal_title", "Tag Assignment Patch Preview");
  const modalResolvedLabel = analyticsTagEditorText(state.config, "modal_resolved_label", "Resolved tag assignment payload");
  const modalPatchGuidanceLabel = analyticsTagEditorText(state.config, "modal_patch_guidance_label", "Patch guidance for tag_assignments.json");
  const modalCopyButton = analyticsTagEditorText(state.config, "modal_copy_button", "Copy");
  const modalCloseButton = analyticsTagEditorText(state.config, "modal_close_button", "Close");

  return renderAnalyticsModalFrame({
    modalRole: UI.role.modal,
    backdropRole: UI.role.modalClose,
    titleId: "analyticsModalTitle",
    title: modalTitle,
    bodyHtml: `
      <p class="${UI_CLASS.modalLabel}">${escapeHtml(modalResolvedLabel)}</p>
      <pre class="${UI_CLASS.modalPre}" data-role="${UI.role.modalTags}"></pre>
      <p class="${UI_CLASS.modalLabel}">${escapeHtml(modalPatchGuidanceLabel)}</p>
      <pre class="${UI_CLASS.modalPre}" data-role="${UI.role.modalSnippet}"></pre>
    `,
    actionsHtml: renderAnalyticsModalActions([
      { role: UI.role.modalClose, label: modalCloseButton },
      { role: UI.role.copySnippet, label: modalCopyButton }
    ])
  });
}

export function collectAnalyticsTagEditorSaveModalRefs(root) {
  return {
    modal: root.querySelector(UI_SELECTOR.modal),
    modalDialog: root.querySelector(`${UI_SELECTOR.modal} [role="dialog"]`),
    closeButton: root.querySelector(`${UI_SELECTOR.modal} .analyticsModal__actions ${UI_SELECTOR.modalClose}`),
    modalTags: root.querySelector(UI_SELECTOR.modalTags),
    modalSnippet: root.querySelector(UI_SELECTOR.modalSnippet),
    copyButton: root.querySelector(UI_SELECTOR.copySnippet)
  };
}

export function wireAnalyticsTagEditorSaveModalEvents(state, callbacks = {}) {
  state.refs.modal.addEventListener("click", (event) => {
    if (!event.target.closest(UI_SELECTOR.modalClose)) return;
    closeAnalyticsTagEditorSaveModal(state);
  });

  state.refs.copyButton.addEventListener("click", () => {
    callbacks.onCopySnippet?.();
  });

  document.addEventListener("keydown", (event) => {
    if (!state.refs.modal || state.refs.modal.hidden) return;
    if (event.key === "Escape") {
      event.preventDefault();
      closeAnalyticsTagEditorSaveModal(state);
      return;
    }
    if (event.key !== "Tab") return;

    const nodes = focusableNodes(state.refs.modal);
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
  });
}

export function openAnalyticsTagEditorSaveModal(state, diff) {
  const timestamp = utcTimestamp();
  const snippet = buildPatchSnippet(
    state.seriesId,
    diff,
    timestamp
  );
  state.modalSnippet = snippet;

  state.refs.modalTags.textContent = JSON.stringify({
    series_tags: diff.nextSeriesRows,
    work_overrides: workStateMapToObject(diff.nextWorkStateById)
  }, null, 2);
  state.refs.modalSnippet.textContent = snippet;
  state.refs.modal.hidden = false;
  state.saveModalRestoreFocus = document.activeElement;
  focusAnalyticsTagEditorSaveModal(state);
}

export function closeAnalyticsTagEditorSaveModal(state) {
  state.refs.modal.hidden = true;
  restoreAnalyticsTagEditorSaveModalFocus(state);
}

function analyticsTagEditorText(config, key, fallback, params) {
  return getAnalyticsText(config, `series_tag_editor.${key}`, fallback, params);
}

function escapeHtml(value) {
  return String(value == null ? "" : value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function focusAnalyticsTagEditorSaveModal(state) {
  const target = state.refs.closeButton || state.refs.copyButton || state.refs.modalDialog;
  if (target && typeof target.focus === "function") target.focus();
}

function restoreAnalyticsTagEditorSaveModalFocus(state) {
  const restoreTarget = state.saveModalRestoreFocus;
  state.saveModalRestoreFocus = null;
  try {
    if (restoreTarget && typeof restoreTarget.focus === "function") {
      restoreTarget.focus({ preventScroll: true });
    }
  } catch (_error) {
    // The opener may have been removed or disabled by a route re-render.
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
