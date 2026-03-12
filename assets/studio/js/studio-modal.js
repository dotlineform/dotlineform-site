function ensureHost(options = {}) {
  const root = options.root
    || document.querySelector(".tagStudioPage, .tagRegistryPage, .tagAliasesPage, .seriesTagsPage")
    || document.body;
  let host = root.querySelector('[data-studio-modal-host="true"]');
  if (host) return host;

  host = document.createElement("div");
  host.setAttribute("data-studio-modal-host", "true");
  root.appendChild(host);
  return host;
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function renderBodyText(body) {
  if (!body) return "";
  const lines = Array.isArray(body) ? body : [body];
  return lines
    .map((line) => String(line || "").trim())
    .filter(Boolean)
    .map((line) => `<p class="tagStudioModal__label">${escapeHtml(line)}</p>`)
    .join("");
}

function renderStatus(status) {
  if (!status || !status.message) {
    return '<p class="tagStudioForm__status" data-role="modal-status"></p>';
  }
  const stateAttr = status.kind ? ` data-state="${escapeHtml(status.kind)}"` : "";
  return `<p class="tagStudioForm__status" data-role="modal-status"${stateAttr}>${escapeHtml(status.message)}</p>`;
}

function renderSnippet(snippet) {
  if (!snippet) return "";
  return `<pre class="tagStudioModal__pre" data-role="modal-snippet">${escapeHtml(snippet)}</pre>`;
}

function renderActions(options = {}) {
  const primaryLabel = String(options.primaryLabel || "OK");
  const cancelLabel = String(options.cancelLabel || "Cancel");
  const primaryAttrs = options.primaryDisabled ? " disabled" : "";
  return `
    <div class="tagStudioModal__actions">
      <button type="button" class="tagStudio__button" data-role="modal-primary"${primaryAttrs}>${escapeHtml(primaryLabel)}</button>
      <button type="button" class="tagStudio__button" data-role="modal-cancel">${escapeHtml(cancelLabel)}</button>
    </div>
  `;
}

function renderActionList(actions = []) {
  if (!Array.isArray(actions) || !actions.length) return "";
  return actions.map((action, index) => {
    const label = String(action && action.label ? action.label : `Action ${index + 1}`);
    const classes = ["tagStudio__button"];
    const roleAttr = action && action.role ? ` data-role="${escapeHtml(action.role)}"` : "";
    const disabledAttr = action && action.disabled ? " disabled" : "";
    return `<button type="button" class="${classes.join(" ")}"${roleAttr}${disabledAttr}>${escapeHtml(label)}</button>`;
  }).join("");
}

export function renderStudioModalActions(actions = []) {
  return `<div class="tagStudioModal__actions">${renderActionList(actions)}</div>`;
}

export function renderStudioModalFrame(options = {}) {
  const modalRole = options.modalRole ? ` data-role="${escapeHtml(options.modalRole)}"` : "";
  const backdropRole = options.backdropRole ? ` data-role="${escapeHtml(options.backdropRole)}"` : "";
  const dialogClass = options.dialogClass ? ` ${escapeHtml(options.dialogClass)}` : "";
  const hiddenAttr = options.hidden === false ? "" : " hidden";
  const titleId = String(options.titleId || "studioModalTitle");
  const titleRole = options.titleRole ? ` data-role="${escapeHtml(options.titleRole)}"` : "";
  const title = String(options.title || "");
  const bodyHtml = String(options.bodyHtml || "");
  const actionsHtml = options.actionsHtml || renderStudioModalActions(options.actions || []);
  return `
    <div class="tagStudioModal"${modalRole}${hiddenAttr}>
      <div class="tagStudioModal__backdrop"${backdropRole}></div>
      <div class="tagStudioModal__dialog${dialogClass}" role="dialog" aria-modal="true" aria-labelledby="${escapeHtml(titleId)}">
        <h3 id="${escapeHtml(titleId)}"${titleRole}>${escapeHtml(title)}</h3>
        ${bodyHtml}
        ${actionsHtml}
      </div>
    </div>
  `;
}

function renderModal(type, options = {}) {
  const title = String(options.title || "");
  const bodyHtml = renderBodyText(options.body);
  const statusHtml = type === "confirm-detail" ? renderStatus(options.status) : "";
  const impactHtml = type === "confirm-detail" && options.impact
    ? `<p class="tagStudioForm__impact" data-role="modal-impact">${escapeHtml(options.impact)}</p>`
    : "";
  const snippetHtml = type === "patch-preview" ? renderSnippet(options.snippet) : "";

  return `
    <div class="tagStudioModal" data-role="studio-modal">
      <div class="tagStudioModal__backdrop" data-role="modal-cancel"></div>
      <div class="tagStudioModal__dialog" role="dialog" aria-modal="true" aria-labelledby="studioModalTitle">
        <h3 id="studioModalTitle">${escapeHtml(title)}</h3>
        ${bodyHtml}
        ${impactHtml}
        ${snippetHtml}
        ${statusHtml}
        ${renderActions(options)}
      </div>
    </div>
  `;
}

function setRoleMessage(host, role, className, kind, message) {
  const target = host.querySelector(`[data-role="${role}"]`);
  if (!target) return;
  target.textContent = message || "";
  target.className = className;
  if (kind) {
    target.dataset.state = kind;
    return;
  }
  delete target.dataset.state;
}

function closeActiveModal(host) {
  host.innerHTML = "";
}

function openModal(type, options = {}) {
  const host = ensureHost(options);
  closeActiveModal(host);
  host.innerHTML = renderModal(type, options);

  const modal = host.querySelector('[data-role="studio-modal"]');
  const primary = host.querySelector('[data-role="modal-primary"]');
  const cancelButtons = host.querySelectorAll('[data-role="modal-cancel"]');

  return new Promise((resolve) => {
    const cleanup = () => {
      closeActiveModal(host);
      document.removeEventListener("keydown", onKeydown);
    };

    const api = {
      setStatus(kind, message) {
        setRoleMessage(host, "modal-status", "tagStudioForm__status", kind, message);
      }
    };

    const submit = async () => {
      if (typeof options.onSubmit === "function") {
        const result = await options.onSubmit(api);
        if (result === false) return;
        if (result && typeof result === "object" && result.ok === false) {
          if ("status" in result) api.setStatus(result.statusKind || "error", result.status || "");
          return;
        }
      }
      cleanup();
      if (type === "patch-preview") {
        resolve({ confirmed: true });
        return;
      }
      resolve({ confirmed: true });
    };

    const cancel = () => {
      cleanup();
      resolve({ confirmed: false });
    };

    const onKeydown = (event) => {
      if (event.key === "Escape") {
        event.preventDefault();
        cancel();
      }
    };

    document.addEventListener("keydown", onKeydown);

    cancelButtons.forEach((button) => {
      button.addEventListener("click", cancel);
    });
    if (primary) {
      primary.addEventListener("click", submit);
    }

    if (modal) {
      modal.addEventListener("click", (event) => {
        if (event.target === modal) cancel();
      });
    }

    if (primary) {
      primary.focus();
    }
  });
}

export function createStudioModalHost(options = {}) {
  return ensureHost(options);
}

export function openConfirmModal(options = {}) {
  return openModal("confirm", options);
}

export function openConfirmDetailModal(options = {}) {
  return openModal("confirm-detail", options);
}

export function openPatchPreviewModal(options = {}) {
  return openModal("patch-preview", options);
}
