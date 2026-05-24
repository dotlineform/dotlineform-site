import { getStudioText } from "./studio-config.js";
import { openConfirmDetailModal, openNoticeModal } from "./studio-modal.js";

export function showDataSharingReviewResultModal(state, { title, summary, countRows, issues }, options = {}) {
  const summaryHtml = normalizeText(summary)
    ? `<p class="tagStudioModal__label dataSharingReviewResultModal__summary">${escapeHtml(summary)}</p>`
    : "";
  const bodyHtml = `
    ${summaryHtml}
    ${countRowsHtml(countRows)}
    ${issuesHtml(state, issues)}
  `;
  return openNoticeModal({
    root: state.root,
    title,
    bodyHtml,
    restoreFocus: options.restoreFocus,
    closeLabel: getStudioText(state.config, "data_sharing_review.result_close_button", "Close")
  }).catch((error) => console.warn("data_sharing_review: result modal failed", error));
}

export function confirmDataSharingReviewApply(state, action, preflight, countsTextValue) {
  const confirmation = actionConfirmation(action);
  return openConfirmDetailModal({
    root: state.root,
    title: normalizeText(confirmation.title)
      || getStudioText(state.config, "data_sharing_review.apply_confirm_title", "Apply returned changes?"),
    body: [
      normalizeText(preflight && preflight.summary_text) || normalizeText(countsTextValue),
      normalizeText(countsTextValue),
      normalizeText(confirmation.body)
    ].filter(Boolean),
    primaryLabel: normalizeText(confirmation.primary_label)
      || getStudioText(state.config, "data_sharing_review.apply_confirm_ok", "OK"),
    cancelLabel: normalizeText(confirmation.cancel_label)
      || getStudioText(state.config, "data_sharing_review.apply_confirm_cancel", "Cancel")
  });
}

function countRowsHtml(rows) {
  const items = Array.isArray(rows) ? rows : [];
  if (!items.length) return "";
  return `
    <dl class="dataSharingReviewResultModal__counts">
      ${items.map((row) => `
        <div>
          <dt>${escapeHtml(row.label)}</dt>
          <dd>${escapeHtml(row.value)}</dd>
        </div>
      `).join("")}
    </dl>
  `;
}

function issuesHtml(state, issues) {
  const items = issueItems(issues);
  if (!items.length) return "";
  const heading = getStudioText(state.config, "data_sharing_review.issues_heading", "Issues");
  return `
    <div class="dataSharingReviewResultModal__issues">
      <h4>${escapeHtml(heading)}</h4>
      <ul>${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
    </div>
  `;
}

function issueItems(issues) {
  return Array.isArray(issues) ? issues.map(issueLabel).filter(Boolean) : [];
}

function issueLabel(issue) {
  const code = normalizeText(issue && issue.code);
  const level = normalizeText(issue && issue.level);
  const docId = normalizeText(issue && issue.doc_id);
  const message = normalizeText(issue && issue.message);
  const prefix = [level, code].filter(Boolean).join(" ");
  const suffix = docId ? ` (${docId})` : "";
  return `${prefix ? `${prefix}: ` : ""}${message}${suffix}`;
}

function actionConfirmation(action) {
  return action && action.confirmation && typeof action.confirmation === "object" ? action.confirmation : {};
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
