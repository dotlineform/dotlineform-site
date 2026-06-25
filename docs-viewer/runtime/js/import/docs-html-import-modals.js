import {
  importText
} from "./docs-html-import-text.js";

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

function createModalHost(options = {}) {
  const root = options.root || document.body;
  let host = root.querySelector('[data-docs-viewer-modal-host="true"]');
  if (host) return host;

  host = document.createElement("div");
  host.setAttribute("data-docs-viewer-modal-host", "true");
  root.appendChild(host);
  return host;
}

function renderModalActions(actions = []) {
  if (!Array.isArray(actions) || !actions.length) return "";
  return `<div class="docsViewer__modalActions">${actions.map((action, index) => {
    const label = String(action && action.label ? action.label : `Action ${index + 1}`);
    const roleAttr = action && action.role ? ` data-role="${escapeHtml(action.role)}"` : "";
    const disabledAttr = action && action.disabled ? " disabled" : "";
    return `<button type="button" class="docsViewer__actionButton docsViewer__actionButton--defaultWidth"${roleAttr}${disabledAttr}>${escapeHtml(label)}</button>`;
  }).join("")}</div>`;
}

function renderModalFrame(options = {}) {
  const modalRole = options.modalRole ? ` data-role="${escapeHtml(options.modalRole)}"` : "";
  const backdropRole = options.backdropRole ? ` data-role="${escapeHtml(options.backdropRole)}"` : "";
  const sizeClass = options.size ? ` docsViewer__modalCard--${escapeHtml(options.size)}` : "";
  const dialogClass = options.dialogClass ? ` ${escapeHtml(options.dialogClass)}` : "";
  const hiddenAttr = options.hidden === false ? "" : " hidden";
  const titleId = String(options.titleId || "docsViewerImportModalTitle");
  const titleRole = options.titleRole ? ` data-role="${escapeHtml(options.titleRole)}"` : "";
  const title = String(options.title || "");
  const bodyHtml = String(options.bodyHtml || "");
  const actionsHtml = options.actionsHtml || renderModalActions(options.actions || []);
  return `
    <div class="docsViewer__modal"${modalRole}${hiddenAttr}>
      <div class="docsViewer__modalBackdrop"${backdropRole}></div>
      <div class="docsViewer__modalCard${sizeClass}${dialogClass}" role="dialog" aria-modal="true" aria-labelledby="${escapeHtml(titleId)}">
        <div class="docsViewer__modalHeader">
          <div class="docsViewer__modalHeaderCopy">
            <h2 class="docsViewer__modalTitle" id="${escapeHtml(titleId)}"${titleRole}>${escapeHtml(title)}</h2>
          </div>
        </div>
        <form class="docsViewer__modalForm" data-role="filename-conflict-form">
          ${bodyHtml}
          ${actionsHtml}
        </form>
      </div>
    </div>
  `;
}

function focusableControls(container) {
  if (!container) return [];
  return Array.from(container.querySelectorAll([
    "button:not([disabled])",
    "input:not([disabled])",
    "select:not([disabled])",
    "textarea:not([disabled])",
    "a[href]",
    "[tabindex]:not([tabindex='-1'])"
  ].join(","))).filter((node) => {
    return !node.hidden && node.getClientRects && node.getClientRects().length;
  });
}

function trapModalFocus(event, modal) {
  if (!modal || event.key !== "Tab") return false;
  const controls = focusableControls(modal);
  if (!controls.length) return false;
  const first = controls[0];
  const last = controls[controls.length - 1];
  const active = document.activeElement;
  if (!modal.contains(active)) {
    event.preventDefault();
    first.focus();
    return true;
  }
  if (event.shiftKey && active === first) {
    event.preventDefault();
    last.focus();
    return true;
  }
  if (!event.shiftKey && active === last) {
    event.preventDefault();
    first.focus();
    return true;
  }
  return false;
}

export function openReplacementDocIdModal(options = {}) {
  const collision = options.payload && options.payload.collision && typeof options.payload.collision === "object"
    ? options.payload.collision
    : {};
  const preview = options.payload && options.payload.import_preview && typeof options.payload.import_preview === "object"
    ? options.payload.import_preview
    : {};
  const currentDocId = normalizeText(collision.doc_id || preview.proposed_doc_id);
  const inputId = "docsHtmlImportReplacementDocId";
  const statusRole = "filename-conflict-status";
  const host = createModalHost({ root: options.root });

  const actions = [
    { role: "filename-conflict-cancel", label: importText("filenameConflictCancelButton") },
    { role: "filename-conflict-replace", label: importText("filenameConflictReplaceButton") },
    {
      role: "filename-conflict-replace-all",
      label: importText("filenameConflictReplaceAllButton")
    }
  ];
  actions.push({ role: "filename-conflict-ok", label: importText("filenameConflictOkButton") });

  host.innerHTML = renderModalFrame({
    hidden: false,
    title: importText("filenameConflictHeading"),
    modalRole: "docs-import-filename-conflict-modal",
    backdropRole: "filename-conflict-cancel",
    bodyHtml: `
      <p class="docsViewer__modalNote muted small">${escapeHtml(importText(
        "filenameConflictBody",
        { doc_id: currentDocId }
      ))}</p>
      <label class="docsViewer__field" for="${inputId}">
        <span class="docsViewer__fieldLabel">${escapeHtml(importText("replacementDocIdLabel"))}</span>
        <input class="docsViewer__fieldInput" id="${inputId}" type="text" autocomplete="off" spellcheck="false" value="${escapeHtml(currentDocId)}">
      </label>
      <p class="docsViewer__modalNote muted small" data-role="${statusRole}" hidden></p>
    `,
    size: "compact",
    actions
  });

  const modal = host.querySelector('[data-role="docs-import-filename-conflict-modal"]');
  const form = host.querySelector('[data-role="filename-conflict-form"]');
  const input = host.querySelector(`#${inputId}`);
  const statusNode = host.querySelector(`[data-role="${statusRole}"]`);
  const okButton = host.querySelector('[data-role="filename-conflict-ok"]');
  const replaceButton = host.querySelector('[data-role="filename-conflict-replace"]');
  const replaceAllButton = host.querySelector('[data-role="filename-conflict-replace-all"]');
  const cancelNodes = host.querySelectorAll('[data-role="filename-conflict-cancel"]');
  const restoreFocus = document.activeElement;

  return new Promise((resolve) => {
    const cleanup = () => {
      host.innerHTML = "";
      document.removeEventListener("keydown", onKeydown);
      try {
        if (restoreFocus && typeof restoreFocus.focus === "function") {
          restoreFocus.focus({ preventScroll: true });
        }
      } catch (_error) {
        // Focus return is best effort.
      }
    };
    const close = (value) => {
      cleanup();
      resolve(value);
    };
    const setModalStatus = (message) => {
      if (!statusNode) return;
      statusNode.textContent = message || "";
      statusNode.hidden = !message;
      if (message) {
        statusNode.dataset.state = "error";
      } else {
        delete statusNode.dataset.state;
      }
    };
    const submitReplacement = () => {
      const value = normalizeText(input && input.value);
      if (!value) {
        setModalStatus(importText("replacementDocIdRequired"));
        if (input) input.focus();
        return;
      }
      close({ action: "rename", replacementDocId: value });
    };
    const submitReplace = () => close({ action: "replace", overwriteDocId: currentDocId });
    const submitReplaceAll = () => close({ action: "replaceAll", overwriteDocId: currentDocId });
    const cancel = () => close({ action: "cancel" });
    const onKeydown = (event) => {
      if (trapModalFocus(event, modal)) return;
      if (event.key === "Escape") {
        event.preventDefault();
        cancel();
      }
    };

    document.addEventListener("keydown", onKeydown);
    if (okButton) okButton.addEventListener("click", submitReplacement);
    if (replaceButton) replaceButton.addEventListener("click", submitReplace);
    if (replaceAllButton) replaceAllButton.addEventListener("click", submitReplaceAll);
    cancelNodes.forEach((node) => node.addEventListener("click", cancel));
    if (form) {
      form.addEventListener("submit", (event) => {
        event.preventDefault();
        submitReplacement();
      });
    }

    window.setTimeout(() => {
      try {
        if (!input) return;
        input.focus();
        input.select();
      } catch (_error) {
        // Focus is a convenience only.
      }
    }, 0);
  });
}
