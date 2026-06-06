import { getAdminText } from "./admin-config.js";

export function openActivityDetailsModal(state, entry) {
  if (!state || !entry) return Promise.resolve();
  const detailItems = Array.isArray(entry.detail_items)
    ? entry.detail_items.filter((item) => normalizeText(item))
    : [];
  const fallback = normalizeText(entry.script_purpose_label)
    || getAdminText(state.config, "admin_activity.modal_empty_detail", "No detail items recorded.");
  return openNoticeModal({
    root: state.root,
    title: getAdminText(state.config, "admin_activity.modal_title", "Activity details"),
    body: detailItems.length ? detailItems : [fallback],
    closeLabel: getAdminText(state.config, "admin_activity.modal_close_button", "Close")
  });
}

function openNoticeModal(options = {}) {
  const host = ensureHost(options.root);
  const restoreFocus = document.activeElement;
  host.innerHTML = renderNoticeModal(options);
  const modal = host.querySelector("[data-role='admin-modal']");
  const closeButton = host.querySelector("[data-role='modal-cancel']");
  const close = () => {
    host.innerHTML = "";
    document.removeEventListener("keydown", onKeydown);
    if (restoreFocus && typeof restoreFocus.focus === "function") {
      restoreFocus.focus({ preventScroll: true });
    }
  };
  function onKeydown(event) {
    if (event.key === "Escape") close();
  }
  document.addEventListener("keydown", onKeydown);
  closeButton.addEventListener("click", close);
  modal.addEventListener("click", (event) => {
    if (event.target === modal) close();
  });
  closeButton.focus();
  return Promise.resolve({ confirmed: false });
}

function ensureHost(root) {
  const target = root || document.body;
  let host = target.querySelector("[data-admin-modal-host='true']");
  if (host) return host;
  host = document.createElement("div");
  host.setAttribute("data-admin-modal-host", "true");
  target.appendChild(host);
  return host;
}

function renderNoticeModal(options = {}) {
  const title = normalizeText(options.title);
  const closeLabel = normalizeText(options.closeLabel) || "Close";
  const body = Array.isArray(options.body) ? options.body : [options.body];
  const bodyHtml = body
    .map((line) => normalizeText(line))
    .filter(Boolean)
    .map((line) => `<p class="tagStudioModal__label">${escapeHtml(line)}</p>`)
    .join("");
  return `<div class="tagStudioModal" data-role="admin-modal">
    <div class="tagStudioModal__backdrop"></div>
    <div class="tagStudioModal__dialog tagStudioModal__dialog--compact" role="dialog" aria-modal="true" aria-labelledby="adminActivityModalTitle" tabindex="-1">
      <header class="tagStudioModal__header">
        <div class="tagStudioModal__headerCopy">
          <h3 class="tagStudioModal__title" id="adminActivityModalTitle">${escapeHtml(title)}</h3>
        </div>
      </header>
      ${bodyHtml}
      <div class="tagStudioModal__actions">
        <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" data-role="modal-cancel">${escapeHtml(closeLabel)}</button>
      </div>
    </div>
  </div>`;
}

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
