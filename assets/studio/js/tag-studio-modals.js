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
      { role: UI.role.copySnippet, label: modalCopyButton },
      { role: UI.role.modalClose, label: modalCloseButton }
    ])
  });
}

export function collectTagStudioSaveModalRefs(root) {
  return {
    modal: root.querySelector(UI_SELECTOR.modal),
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
}

export function closeTagStudioSaveModal(state) {
  state.refs.modal.hidden = true;
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
