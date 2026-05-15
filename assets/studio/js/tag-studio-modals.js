import { getStudioText } from "./studio-config.js";
import { workStateMapToObject } from "./tag-studio-domain.js";
import {
  buildPatchSnippet,
  utcTimestamp
} from "./tag-studio-save.js";
import {
  renderStudioModalActions,
  renderStudioModalFrame
} from "./studio-modal.js";
import { seriesTagEditorUi } from "./studio-ui.js";

const UI = seriesTagEditorUi;
const { className: UI_CLASS, selector: UI_SELECTOR } = UI;

export function renderTagStudioSaveModal(state) {
  const modalTitle = tagStudioText(state.config, "modal_title", "Tag Assignment Patch Preview");
  const modalResolvedLabel = tagStudioText(state.config, "modal_resolved_label", "Resolved tag assignment payload");
  const modalPatchGuidanceLabel = tagStudioText(state.config, "modal_patch_guidance_label", "Patch guidance for tag_assignments.json");
  const modalCopyButton = tagStudioText(state.config, "modal_copy_button", "Copy");
  const modalCloseButton = tagStudioText(state.config, "modal_close_button", "Close");

  return renderStudioModalFrame({
    modalRole: UI.role.modal,
    backdropRole: UI.role.modalClose,
    titleId: "tagStudioModalTitle",
    title: modalTitle,
    bodyHtml: `
      <p class="${UI_CLASS.modalLabel}">${escapeHtml(modalResolvedLabel)}</p>
      <pre class="${UI_CLASS.modalPre}" data-role="${UI.role.modalTags}"></pre>
      <p class="${UI_CLASS.modalLabel}">${escapeHtml(modalPatchGuidanceLabel)}</p>
      <pre class="${UI_CLASS.modalPre}" data-role="${UI.role.modalSnippet}"></pre>
    `,
    actionsHtml: renderStudioModalActions([
      { role: UI.role.modalClose, label: modalCloseButton },
      { role: UI.role.copySnippet, label: modalCopyButton }
    ])
  });
}

export function collectTagStudioSaveModalRefs(root) {
  return {
    modal: root.querySelector(UI_SELECTOR.modal),
    modalDialog: root.querySelector(`${UI_SELECTOR.modal} [role="dialog"]`),
    closeButton: root.querySelector(`${UI_SELECTOR.modal} .tagStudioModal__actions ${UI_SELECTOR.modalClose}`),
    modalTags: root.querySelector(UI_SELECTOR.modalTags),
    modalSnippet: root.querySelector(UI_SELECTOR.modalSnippet),
    copyButton: root.querySelector(UI_SELECTOR.copySnippet)
  };
}

export function wireTagStudioSaveModalEvents(state, callbacks = {}) {
  state.refs.modal.addEventListener("click", (event) => {
    if (!event.target.closest(UI_SELECTOR.modalClose)) return;
    closeTagStudioSaveModal(state);
  });

  state.refs.copyButton.addEventListener("click", () => {
    callbacks.onCopySnippet?.();
  });

  document.addEventListener("keydown", (event) => {
    if (!state.refs.modal || state.refs.modal.hidden) return;
    if (event.key === "Escape") {
      event.preventDefault();
      closeTagStudioSaveModal(state);
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

export function openTagStudioSaveModal(state, diff) {
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
  focusTagStudioSaveModal(state);
}

export function closeTagStudioSaveModal(state) {
  state.refs.modal.hidden = true;
  restoreTagStudioSaveModalFocus(state);
}

function tagStudioText(config, key, fallback, params) {
  return getStudioText(config, `series_tag_editor.${key}`, fallback, params);
}

function escapeHtml(value) {
  return String(value == null ? "" : value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function focusTagStudioSaveModal(state) {
  const target = state.refs.closeButton || state.refs.copyButton || state.refs.modalDialog;
  if (target && typeof target.focus === "function") target.focus();
}

function restoreTagStudioSaveModalFocus(state) {
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
