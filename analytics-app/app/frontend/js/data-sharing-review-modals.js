import { getAnalyticsText } from "./analytics-config.js";
import { openConfirmDetailModal } from "./analytics-modal.js";

export function confirmDataSharingReviewApply(state, action, preflight, countsTextValue) {
  const confirmation = actionConfirmation(action);
  return openConfirmDetailModal({
    root: state.root,
    title: normalizeText(confirmation.title)
      || getAnalyticsText(state.config, "data_sharing_review.apply_confirm_title", "Apply returned changes?"),
    body: [
      normalizeText(preflight && preflight.summary_text) || normalizeText(countsTextValue),
      normalizeText(countsTextValue),
      normalizeText(confirmation.body)
    ].filter(Boolean),
    primaryLabel: normalizeText(confirmation.primary_label)
      || getAnalyticsText(state.config, "data_sharing_review.apply_confirm_ok", "OK"),
    cancelLabel: normalizeText(confirmation.cancel_label)
      || getAnalyticsText(state.config, "data_sharing_review.apply_confirm_cancel", "Cancel")
  });
}

function actionConfirmation(action) {
  return action && action.confirmation && typeof action.confirmation === "object" ? action.confirmation : {};
}

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}
