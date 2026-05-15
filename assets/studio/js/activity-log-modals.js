import { getStudioText } from "./studio-config.js";
import { openNoticeModal } from "./studio-modal.js";

export function openActivityDetailsModal(state, entry) {
  if (!state || !entry) return Promise.resolve();
  const detailItems = Array.isArray(entry.detail_items)
    ? entry.detail_items.filter((item) => normalizeText(item))
    : [];
  const fallback = normalizeText(entry.script_purpose_label)
    || getStudioText(state.config, "activity_log.modal_empty_detail", "No detail items recorded.");
  return openNoticeModal({
    root: state.root,
    title: getStudioText(state.config, "activity_log.modal_title", "Activity details"),
    body: detailItems.length ? detailItems : [fallback],
    closeLabel: getStudioText(state.config, "activity_log.modal_close_button", "Close")
  });
}

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}
