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

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function escapeHtml(value) {
  return String(value == null ? "" : value)
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
  const message = normalizeText(status && status.message);
  const stateAttr = status && status.kind ? ` data-state="${escapeHtml(status.kind)}"` : "";
  const hiddenAttr = message ? "" : " hidden";
  return `<p class="tagStudioForm__status tagStudioModal__status" data-role="modal-status"${stateAttr}${hiddenAttr}>${escapeHtml(message)}</p>`;
}

function renderSnippet(snippet) {
  if (!snippet) return "";
  return `<pre class="tagStudioModal__pre" data-role="modal-snippet">${escapeHtml(snippet)}</pre>`;
}

function renderActions(options = {}) {
  const primaryLabel = String(options.primaryLabel || "OK");
  const cancelLabel = String(options.cancelLabel || "Cancel");
  const cancelDefault = normalizeText(options.defaultAction).toLowerCase() === "cancel";
  const primaryAttrs = options.primaryDisabled ? " disabled" : "";
  const cancelClass = [
    "tagStudio__button",
    "tagStudio__button--defaultWidth",
    cancelDefault ? "tagStudio__button--defaultAction" : ""
  ].filter(Boolean).join(" ");
  const primaryClass = [
    "tagStudio__button",
    "tagStudio__button--defaultWidth",
    cancelDefault ? "" : "tagStudio__button--defaultAction"
  ].filter(Boolean).join(" ");
  return `
    <div class="tagStudioModal__actions">
      <button type="button" class="${escapeHtml(cancelClass)}" data-role="modal-cancel">${escapeHtml(cancelLabel)}</button>
      <button type="button" class="${escapeHtml(primaryClass)}" data-role="modal-primary"${primaryAttrs}>${escapeHtml(primaryLabel)}</button>
    </div>
  `;
}

function renderCloseAction(options = {}) {
  const closeLabel = String(options.closeLabel || options.cancelLabel || "Close");
  return `
    <div class="tagStudioModal__actions">
      <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" data-role="modal-cancel">${escapeHtml(closeLabel)}</button>
    </div>
  `;
}

function renderActionList(actions = []) {
  if (!Array.isArray(actions) || !actions.length) return "";
  return actions.map((action, index) => {
    const label = String(action && action.label ? action.label : `Action ${index + 1}`);
    const classes = ["tagStudio__button", "tagStudio__button--defaultWidth"];
    if (action && action.primary) classes.push("tagStudio__button--defaultAction");
    if (action && action.className) classes.push(String(action.className));
    const roleAttr = action && action.role ? ` data-role="${escapeHtml(action.role)}"` : "";
    const disabledAttr = action && action.disabled ? " disabled" : "";
    const type = action && action.type ? String(action.type) : "button";
    return `<button type="${escapeHtml(type)}" class="${escapeHtml(classes.join(" "))}"${roleAttr}${disabledAttr}>${escapeHtml(label)}</button>`;
  }).join("");
}

export function renderStudioModalActions(actions = []) {
  return `<div class="tagStudioModal__actions">${renderActionList(actions)}</div>`;
}

export function renderStudioModalFrame(options = {}) {
  const modalRole = options.modalRole ? ` data-role="${escapeHtml(options.modalRole)}"` : "";
  const backdropRole = options.backdropRole ? ` data-role="${escapeHtml(options.backdropRole)}"` : "";
  const sizeClass = options.size ? ` tagStudioModal__dialog--${escapeHtml(options.size)}` : "";
  const dialogClass = options.dialogClass ? ` ${escapeHtml(options.dialogClass)}` : "";
  const hiddenAttr = options.hidden === false ? "" : " hidden";
  const titleId = String(options.titleId || "studioModalTitle");
  const titleRole = options.titleRole ? ` data-role="${escapeHtml(options.titleRole)}"` : "";
  const title = String(options.title || "");
  const meta = normalizeText(options.meta);
  const bodyHtml = String(options.bodyHtml || "");
  const statusHtml = options.statusHtml || (options.status || options.includeStatus ? renderStatus(options.status) : "");
  const actionsHtml = options.actionsHtml || renderStudioModalActions(options.actions || []);
  const contentHtml = `
        <header class="tagStudioModal__header">
          <div class="tagStudioModal__headerCopy">
            <h3 class="tagStudioModal__title" id="${escapeHtml(titleId)}"${titleRole}>${escapeHtml(title)}</h3>
            ${meta ? `<p class="tagStudioModal__meta">${escapeHtml(meta)}</p>` : ""}
          </div>
        </header>
        ${bodyHtml}
        ${statusHtml}
        ${actionsHtml}
  `;
  return `
    <div class="tagStudioModal"${modalRole}${hiddenAttr}>
      <div class="tagStudioModal__backdrop"${backdropRole}></div>
      <div class="tagStudioModal__dialog${sizeClass}${dialogClass}" role="dialog" aria-modal="true" aria-labelledby="${escapeHtml(titleId)}" tabindex="-1">
        ${options.form ? `<form class="tagStudioModal__form" data-role="modal-form">${contentHtml}</form>` : contentHtml}
      </div>
    </div>
  `;
}

export function activateStudioModalFrame(host, options = {}) {
  const restoreFocus = options.restoreFocus || document.activeElement;
  const modal = host && host.querySelector('[data-role="studio-modal"], .tagStudioModal');
  const dialog = host && host.querySelector('[role="dialog"]');
  const form = host && host.querySelector('[data-role="modal-form"]');
  const cancelRoles = Array.isArray(options.cancelRoles) && options.cancelRoles.length
    ? options.cancelRoles
    : ["modal-cancel"];
  const submitRoles = Array.isArray(options.submitRoles) && options.submitRoles.length
    ? options.submitRoles
    : ["modal-primary"];
  const cancelNodes = cancelRoles.flatMap((role) => Array.from(host.querySelectorAll(`[data-role="${role}"]`)));
  const submitNodes = submitRoles.flatMap((role) => Array.from(host.querySelectorAll(`[data-role="${role}"]`)));
  let settled = false;
  let resolvePromise = null;

  const promise = new Promise((resolve) => {
    resolvePromise = resolve;
  });

  const cleanup = (restore = true) => {
    closeActiveModal(host);
    document.removeEventListener("keydown", onKeydownCapture, true);
    document.removeEventListener("keydown", onKeydown);
    document.removeEventListener("focusin", onFocusIn);
    if (!restore) return;
    try {
      if (restoreFocus && typeof restoreFocus.focus === "function") {
        restoreFocus.focus({ preventScroll: true });
      }
    } catch (_error) {
      // Focus return is best effort for removed or disabled opener controls.
    }
  };

  const settle = (result = { confirmed: false }, settleOptions = {}) => {
    if (settled) return;
    settled = true;
    cleanup(settleOptions.restoreFocus !== false);
    if (resolvePromise) resolvePromise(result);
  };

  const api = {
    host,
    modal,
    dialog,
    setStatus(kind, message) {
      setRoleMessage(host, "modal-status", "tagStudioForm__status tagStudioModal__status", kind, message);
    },
    cancel(settleOptions = {}) {
      settle({ confirmed: false }, settleOptions);
    },
    close(result = { confirmed: false }, settleOptions = {}) {
      settle(result, settleOptions);
    }
  };

  const submit = async () => {
    if (settled) return;
    if (typeof options.onSubmit === "function") {
      const result = await options.onSubmit(api);
      if (result === false) return;
      if (result && typeof result === "object" && result.ok === false) {
        if ("status" in result) api.setStatus(result.statusKind || "error", result.status || "");
        return;
      }
      settle({ confirmed: true, ...(result && typeof result === "object" ? result : {}) });
      return;
    }
    settle({ confirmed: true });
  };

  api.submit = submit;

  function trapTab(event) {
    if (event.key !== "Tab" || !modal) return;
    const nodes = focusableNodes(modal);
    if (!nodes.length) return;
    event.preventDefault();
    if (!modal.contains(document.activeElement)) {
      nodes[0].focus();
      return;
    }
    const currentIndex = nodes.indexOf(document.activeElement);
    const fallbackIndex = event.shiftKey ? nodes.length : -1;
    const index = currentIndex >= 0 ? currentIndex : fallbackIndex;
    const nextIndex = event.shiftKey
      ? (index - 1 + nodes.length) % nodes.length
      : (index + 1) % nodes.length;
    nodes[nextIndex].focus();
  }

  function onKeydownCapture(event) {
    trapTab(event);
  }

  function onKeydown(event) {
    if (event.key === "Escape") {
      event.preventDefault();
      api.cancel();
      return;
    }
    if (event.key === "Enter" && options.submitOnEnter !== false) {
      const target = event.target;
      const tagName = target && target.tagName ? target.tagName.toLowerCase() : "";
      if (tagName === "textarea" || tagName === "button") return;
      event.preventDefault();
      submit();
    }
  }

  function onFocusIn(event) {
    if (!modal || !event.target || modal.contains(event.target)) return;
    const nodes = focusableNodes(modal);
    if (nodes.length) nodes[0].focus();
  }

  document.addEventListener("keydown", onKeydownCapture, true);
  document.addEventListener("keydown", onKeydown);
  document.addEventListener("focusin", onFocusIn);

  cancelNodes.forEach((node) => {
    node.addEventListener("click", () => api.cancel());
  });
  submitNodes.forEach((node) => {
    node.addEventListener("click", submit);
  });
  if (form) {
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      submit();
    });
  }
  if (modal) {
    modal.addEventListener("click", (event) => {
      if (event.target === modal) api.cancel();
    });
  }

  const focusTarget = options.focusSelector ? host.querySelector(options.focusSelector) : null;
  const cancelDefault = normalizeText(options.defaultAction).toLowerCase() === "cancel";
  const defaultActionTarget = cancelDefault
    ? cancelNodes[cancelNodes.length - 1]
    : submitNodes[0];
  const fallbackActionTarget = cancelDefault
    ? submitNodes[0]
    : cancelNodes[cancelNodes.length - 1];
  const initialFocus = focusTarget || defaultActionTarget || fallbackActionTarget || dialog;
  if (initialFocus && typeof initialFocus.focus === "function") initialFocus.focus();
  if (options.selectInitialFocus && initialFocus && typeof initialFocus.select === "function") initialFocus.select();
  if (typeof options.onOpen === "function") options.onOpen(api);

  return {
    promise,
    api,
    submit,
    cancel: api.cancel,
    close: api.close,
    destroy(destroyOptions = {}) {
      settle({ confirmed: false }, { restoreFocus: Boolean(destroyOptions.restoreFocus) });
    }
  };
}

function renderModal(type, options = {}) {
  const title = String(options.title || "");
  const bodyHtml = options.bodyHtml ? String(options.bodyHtml) : renderBodyText(options.body);
  const statusHtml = type === "confirm-detail" || options.includeStatus ? renderStatus(options.status) : "";
  const impactHtml = type === "confirm-detail" && options.impact
    ? `<p class="tagStudioForm__impact" data-role="modal-impact">${escapeHtml(options.impact)}</p>`
    : "";
  const snippetHtml = type === "patch-preview" ? renderSnippet(options.snippet) : "";
  const actionsHtml = type === "notice" ? renderCloseAction(options) : renderActions(options);

  return renderStudioModalFrame({
    hidden: false,
    modalRole: "studio-modal",
    backdropRole: "modal-cancel",
    closeLabel: options.closeLabel || options.cancelLabel || "Close",
    titleId: options.titleId || "studioModalTitle",
    title,
    meta: options.meta,
    size: options.size,
    bodyHtml: `${bodyHtml}${impactHtml}${snippetHtml}`,
    statusHtml,
    actionsHtml
  });
}

function setRoleMessage(host, role, className, kind, message) {
  const target = host.querySelector(`[data-role="${role}"]`);
  if (!target) return;
  target.textContent = message || "";
  target.className = className;
  target.hidden = !message;
  if (kind) {
    target.dataset.state = kind;
    return;
  }
  delete target.dataset.state;
}

function closeActiveModal(host) {
  host.innerHTML = "";
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

function openModal(type, options = {}) {
  const host = ensureHost(options);
  const restoreFocus = options.restoreFocus || document.activeElement;
  closeActiveModal(host);
  host.innerHTML = renderModal(type, options);

  const controller = activateStudioModalFrame(host, {
    ...options,
    restoreFocus,
    async onSubmit(api) {
      if (typeof options.onSubmit === "function") {
        return options.onSubmit(api);
      }
      if (type === "patch-preview") return {};
      return {};
    }
  });
  return controller.promise;
}

function fieldId(options, fallback) {
  return escapeHtml(normalizeText(options.inputId) || fallback);
}

function renderTextInputBody(options = {}) {
  const inputId = fieldId(options, "studioModalInput");
  const bodyHtml = options.bodyHtml ? String(options.bodyHtml) : renderBodyText(options.body);
  return `
    ${bodyHtml}
    <label class="tagStudioForm__field" for="${inputId}">
      <span class="tagStudioForm__label">${escapeHtml(options.label || "Title")}</span>
      <input class="tagStudio__input" id="${inputId}" type="text" autocomplete="off" spellcheck="false" value="${escapeHtml(options.initialValue || "")}">
    </label>
  `;
}

function renderChoiceBody(options = {}) {
  const name = escapeHtml(normalizeText(options.name) || "studioModalChoice");
  const selected = normalizeText(options.value);
  const choices = Array.isArray(options.choices) ? options.choices : [];
  const bodyHtml = options.bodyHtml ? String(options.bodyHtml) : renderBodyText(options.body);
  return `
    ${bodyHtml}
    <div class="tagStudioModal__choices">
      ${choices.map((choice) => {
        const value = normalizeText(choice && choice.value);
        const label = normalizeText(choice && choice.label) || value;
        const checkedAttr = value === selected ? " checked" : "";
        return `
          <label class="tagStudioForm__field tagStudioModal__choice">
            <input type="radio" name="${name}" value="${escapeHtml(value)}"${checkedAttr}>
            <span>${escapeHtml(label)}</span>
          </label>
        `;
      }).join("")}
    </div>
  `;
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

export function openNoticeModal(options = {}) {
  return openModal("notice", options);
}

export function openTextInputModal(options = {}) {
  const inputId = normalizeText(options.inputId) || "studioModalInput";
  return openModal("text-input", {
    ...options,
    title: options.title,
    bodyHtml: renderTextInputBody({ ...options, inputId }),
    includeStatus: true,
    focusSelector: `#${inputId}`,
    selectInitialFocus: options.selectInitialFocus !== false,
    async onSubmit(api) {
      const input = api.host.querySelector(`#${inputId}`);
      const value = normalizeText(input && input.value) || normalizeText(options.defaultValue);
      if (options.required && !value) {
        api.setStatus("error", options.requiredMessage || "Enter a value.");
        if (input) input.focus();
        return false;
      }
      if (typeof options.onSubmit === "function") {
        const result = await options.onSubmit({ ...api, value, input });
        return result === undefined ? { value } : result;
      }
      return { value };
    }
  });
}

export function openChoiceModal(options = {}) {
  const name = normalizeText(options.name) || "studioModalChoice";
  return openModal("choice", {
    ...options,
    bodyHtml: renderChoiceBody({ ...options, name }),
    includeStatus: true,
    focusSelector: `input[name="${name}"]`,
    async onSubmit(api) {
      const input = api.host.querySelector(`input[name="${name}"]:checked`);
      const value = normalizeText(input && input.value);
      if (options.required !== false && !value) {
        api.setStatus("error", options.requiredMessage || "Choose an option.");
        return false;
      }
      if (typeof options.onSubmit === "function") {
        const result = await options.onSubmit({ ...api, value, input });
        return result === undefined ? { value } : result;
      }
      return { value };
    }
  });
}
