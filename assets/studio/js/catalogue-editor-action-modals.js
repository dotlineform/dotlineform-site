import { openConfirmModal } from "./studio-modal.js";

function modalBodyLines(message) {
  return String(message || "")
    .split(/\n+/)
    .map((line) => line.trim())
    .filter(Boolean);
}

export async function confirmCatalogueActionModal(state, options = {}) {
  const result = await openConfirmModal({
    root: state && state.root,
    title: options.title,
    body: modalBodyLines(options.message),
    primaryLabel: options.primaryLabel,
    cancelLabel: options.cancelLabel,
    size: options.size || "compact",
    restoreFocus: options.restoreFocus
  });
  return Boolean(result && result.confirmed);
}
