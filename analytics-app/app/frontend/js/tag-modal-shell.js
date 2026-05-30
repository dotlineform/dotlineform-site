export function closeTagModalByKind(state, modalKind, closeHandlers = {}) {
  const closeHandler = closeHandlers[modalKind];
  if (typeof closeHandler === "function") closeHandler(state);
}

export function getOpenTagModalKind(state, modalConfigs = []) {
  return modalConfigs.find((config) => {
    const modal = state.refs[config.modalRef];
    return Boolean(modal && !modal.hidden);
  })?.kind || "";
}

export function getTagModalElement(state, modalKind, modalConfigs = []) {
  const config = modalConfigs.find((item) => item.kind === modalKind);
  return config && state.refs[config.modalRef] ? state.refs[config.modalRef] : null;
}

export function captureTagModalRestoreFocus(state, modalKind, modalConfigs = []) {
  const config = modalConfigs.find((item) => item.kind === modalKind);
  if (!config) return;
  state[config.restoreProp] = document.activeElement;
}

export function syncTagModalFocusAfterOpen(state, modalKind, modalConfigs = []) {
  const config = modalConfigs.find((item) => item.kind === modalKind);
  const modal = getTagModalElement(state, modalKind, modalConfigs);
  if (!config || !modal || modal.hidden) return;
  if (state[config.focusProp] && modal.contains(document.activeElement)) return;
  const target = modal.querySelector(config.focusSelector)
    || modal.querySelector(`[data-role="${config.closeRole}"]`)
    || modal.querySelector("[role='dialog']");
  if (target && typeof target.focus === "function") target.focus();
  state[config.focusProp] = true;
}

export function trapTagModalFocus(event, modal) {
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

export function restoreTagModalFocus(target) {
  try {
    if (target && typeof target.focus === "function" && target.getClientRects().length) {
      target.focus({ preventScroll: true });
    }
  } catch (_error) {
    // Focus return is best effort when a route re-render removes the opener.
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

export function setStatusText(target, kind, message, baseClass) {
  if (!target) return;
  target.textContent = message || "";
  target.className = baseClass || "";
  if (kind) {
    target.dataset.state = kind;
    return;
  }
  delete target.dataset.state;
}

export function classNames(...tokens) {
  return tokens.filter(Boolean).join(" ");
}

export function chipGroupClass(uiClass, group) {
  return `${uiClass.chipGroupPrefix}${group}`;
}

export function stateAttr(stateValue) {
  return stateValue ? ` data-state="${escapeHtml(stateValue)}"` : "";
}

export function escapeHtml(value) {
  return String(value == null ? "" : value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
