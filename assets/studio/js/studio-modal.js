function ensureHost(options = {}) {
  const root = options.root || document.body;
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
  const kind = status.kind ? ` is-${escapeHtml(status.kind)}` : "";
  return `<p class="tagStudioForm__status${kind}" data-role="modal-status">${escapeHtml(status.message)}</p>`;
}

function renderWarning(warning) {
  if (!warning) {
    return '<p class="tagStudioForm__warning" data-role="modal-warning"></p>';
  }
  return `<p class="tagStudioForm__warning" data-role="modal-warning">${escapeHtml(warning)}</p>`;
}

function renderFields(fields = []) {
  if (!Array.isArray(fields) || !fields.length) return "";
  const rows = fields.map((field, index) => {
    const name = String(field && field.name ? field.name : `field_${index}`);
    const label = String(field && field.label ? field.label : name);
    const value = field && field.value != null ? String(field.value) : "";
    const placeholder = field && field.placeholder ? ` placeholder="${escapeHtml(field.placeholder)}"` : "";
    const rowsAttr = field && field.rows ? ` rows="${escapeHtml(field.rows)}"` : "";
    const readonly = field && field.readonly ? " readonly" : "";

    if (field && field.type === "textarea") {
      return `
        <label class="tagStudioForm__field">
          <span class="tagStudioForm__label">${escapeHtml(label)}</span>
          <textarea class="tagStudio__input tagStudioForm__descriptionInput" data-role="modal-field" data-field-name="${escapeHtml(name)}"${rowsAttr}${readonly}${placeholder}>${escapeHtml(value)}</textarea>
        </label>
      `;
    }

    return `
      <label class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(label)}</span>
        <input class="tagStudio__input${field && field.readonly ? " tagStudioForm__readonly" : ""}" data-role="modal-field" data-field-name="${escapeHtml(name)}" type="${escapeHtml(field && field.type ? field.type : "text")}" value="${escapeHtml(value)}"${readonly}${placeholder}>
      </label>
    `;
  }).join("");

  return `<div class="tagStudioForm__fields">${rows}</div>`;
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
      <button type="button" class="tagStudio__button tagStudio__button--primary" data-role="modal-primary"${primaryAttrs}>${escapeHtml(primaryLabel)}</button>
      <button type="button" class="tagStudio__button" data-role="modal-cancel">${escapeHtml(cancelLabel)}</button>
    </div>
  `;
}

function renderModal(type, options = {}) {
  const title = String(options.title || "");
  const bodyHtml = renderBodyText(options.body);
  const warningHtml = type === "form" ? renderWarning(options.warning) : "";
  const fieldsHtml = type === "form" ? renderFields(options.fields) : "";
  const statusHtml = type === "form" || type === "confirm-detail" ? renderStatus(options.status) : "";
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
        ${warningHtml}
        ${fieldsHtml}
        ${impactHtml}
        ${snippetHtml}
        ${statusHtml}
        ${renderActions(options)}
      </div>
    </div>
  `;
}

function readFieldValues(host) {
  const values = {};
  host.querySelectorAll('[data-role="modal-field"]').forEach((field) => {
    const name = String(field.getAttribute("data-field-name") || "").trim();
    if (!name) return;
    values[name] = "value" in field ? field.value : "";
  });
  return values;
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
  const firstField = host.querySelector('[data-role="modal-field"]:not([readonly])');

  return new Promise((resolve) => {
    const cleanup = () => {
      closeActiveModal(host);
      document.removeEventListener("keydown", onKeydown);
    };

    const submit = () => {
      const values = readFieldValues(host);
      cleanup();
      if (type === "form") {
        resolve({ submitted: true, values });
        return;
      }
      if (type === "patch-preview") {
        resolve({ confirmed: true });
        return;
      }
      resolve({ confirmed: true });
    };

    const cancel = () => {
      cleanup();
      if (type === "form") {
        resolve({ submitted: false, values: {} });
        return;
      }
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

    if (firstField) {
      firstField.focus();
      if (typeof firstField.select === "function") firstField.select();
    } else if (primary) {
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

export function openFormModal(options = {}) {
  return openModal("form", options);
}

export function openPatchPreviewModal(options = {}) {
  return openModal("patch-preview", options);
}
