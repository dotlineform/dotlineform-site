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

function issueList(title, issues) {
  if (!Array.isArray(issues) || !issues.length) return "";
  return [
    `<section class="docsViewerImport__collectionIssues"><h4>${escapeHtml(title)}</h4><ul>`,
    ...issues.map((issue) => `<li>${escapeHtml(issue && issue.message)}</li>`),
    "</ul></section>"
  ].join("");
}

function recordAction(record) {
  return normalizeText(record.action).replace(/-/g, " ");
}

function recordList(records) {
  return [
    '<ol class="docsViewerImport__collectionRecords">',
    ...records.map((record) => {
      const title = normalizeText(record.title) || normalizeText(record.doc_id) || importText("collectionRecordFallback", {
        number: Number(record.record_index) + 1
      });
      const details = [
        normalizeText(record.doc_id),
        record.parent && record.parent.parent_id ? importText("collectionParentMeta", {
          parent_id: normalizeText(record.parent.parent_id)
        }) : "",
        record.media_plans && record.media_plans.length ? importText("collectionMediaCount", {
          count: record.media_plans.length
        }) : ""
      ].filter(Boolean).join(" · ");
      const issues = []
        .concat(Array.isArray(record.errors) ? record.errors : [])
        .concat(Array.isArray(record.warnings) ? record.warnings : []);
      return [
        "<li>",
        `<span class="docsViewerImport__collectionRecordTitle">${escapeHtml(title)}</span>`,
        `<span class="docsViewerImport__collectionRecordAction">${escapeHtml(recordAction(record))}</span>`,
        details ? `<span class="docsViewerImport__collectionRecordMeta">${escapeHtml(details)}</span>` : "",
        issues.length ? `<ul>${issues.map((issue) => `<li>${escapeHtml(issue && issue.message)}</li>`).join("")}</ul>` : "",
        "</li>"
      ].join("");
    }),
    "</ol>"
  ].join("");
}

function confirmationPanel(phase) {
  if (phase === "applying") {
    return `<section class="docsViewerImport__collectionDecision"><p>${escapeHtml(importText("collectionApplyingStatus"))}</p></section>`;
  }
  if (phase !== "confirmation") return "";
  return [
    '<section class="docsViewerImport__collectionDecision">',
    `<p>${escapeHtml(importText("collectionConfirmationMessage"))}</p>`,
    '<div class="docsViewerImport__collectionDecisionActions">',
    `<button type="button" class="docsViewerImport__button" data-collection-command="confirm">${escapeHtml(importText("collectionConfirmButton"))}</button>`,
    `<button type="button" class="docsViewerImport__button" data-collection-command="cancel">${escapeHtml(importText("cancelOverwriteButton"))}</button>`,
    "</div>",
    "</section>"
  ].join("");
}

function resultPanel(result) {
  if (!result || typeof result !== "object") return "";
  const counts = result.counts || {};
  const summary = [
    importText("collectionCreatesCount", { count: Number(counts.created || 0) }),
    importText("collectionOverwrittenCount", { count: Number(counts.overwritten || 0) }),
    importText("collectionFailedCount", { count: Number(counts.failed || 0) }),
    importText("collectionNotAttemptedCount", { count: Number(counts.not_attempted || 0) })
  ].join(" · ");
  const warnings = Array.isArray(result.warnings) ? result.warnings : [];
  return [
    '<section class="docsViewerImport__collectionSummary">',
    `<h3>${escapeHtml(importText("collectionResultHeading"))}</h3>`,
    `<p>${escapeHtml(summary)}</p>`,
    result.report_path ? `<p class="docsViewerImport__meta">${escapeHtml(importText("collectionReportLabel", { path: result.report_path }))}</p>` : "",
    "</section>",
    issueList(importText("collectionWarningsHeading"), warnings),
    recordList(Array.isArray(result.records) ? result.records.map((record) => ({
      ...record,
      action: record.status,
      media_plans: []
    })) : [])
  ].join("");
}

export function renderDocsImportCollectionView(host, viewState, onCommand) {
  if (!host) return;
  const state = viewState || {};
  const plan = state.plan && typeof state.plan === "object" ? state.plan : null;
  host.hidden = !state.active;
  if (!state.active || !plan) {
    host.replaceChildren();
    return;
  }
  if (state.phase === "result") {
    host.innerHTML = resultPanel(state.result);
    return;
  }
  const counts = plan.counts || {};
  const summary = [
    importText("collectionRecordsCount", { count: Number(counts.records || 0) }),
    importText("collectionCreatesCount", { count: Number(counts.creates || 0) }),
    importText("collectionCollisionsCount", { count: Number(counts.collisions || 0) }),
    importText("collectionRecordErrorsCount", { count: Number(counts.record_errors || 0) }),
    importText("collectionMediaPlansCount", { count: Number(counts.media_plans || 0) })
  ].join(" · ");
  const stateMessage = state.phase === "confirmation"
    ? importText("collectionConfirmationMessage")
    : state.phase === "cancelled"
      ? importText("collectionCancelledStatus")
      : "";
  host.innerHTML = [
    '<section class="docsViewerImport__collectionSummary">',
    `<h3>${escapeHtml(importText("collectionPlanHeading"))}</h3>`,
    `<p>${escapeHtml(summary)}</p>`,
    stateMessage ? `<p class="docsViewerImport__meta">${escapeHtml(stateMessage)}</p>` : "",
    "</section>",
    issueList(importText("collectionBlockersHeading"), plan.blockers),
    issueList(importText("collectionWarningsHeading"), plan.warnings),
    recordList(Array.isArray(plan.records) ? plan.records : []),
    confirmationPanel(state.phase),
  ].join("");
  host.querySelectorAll("[data-collection-command]").forEach((button) => {
    button.addEventListener("click", () => {
      if (typeof onCommand !== "function") return;
      onCommand({ type: normalizeText(button.dataset.collectionCommand) });
    });
  });
}
