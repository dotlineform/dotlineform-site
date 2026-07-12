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

function recordAction(record, decisions) {
  const decision = normalizeText(decisions && decisions[record.record_index]);
  return decision || normalizeText(record.action).replace(/-/g, " ");
}

function decisionLabel(action) {
  if (action === "overwrite") return importText("collectionOverwriteButton");
  if (action === "skip") return importText("collectionSkipButton");
  return action;
}

function recordList(records, decisions) {
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
        `<span class="docsViewerImport__collectionRecordAction">${escapeHtml(recordAction(record, decisions))}</span>`,
        details ? `<span class="docsViewerImport__collectionRecordMeta">${escapeHtml(details)}</span>` : "",
        issues.length ? `<ul>${issues.map((issue) => `<li>${escapeHtml(issue && issue.message)}</li>`).join("")}</ul>` : "",
        "</li>"
      ].join("");
    }),
    "</ol>"
  ].join("");
}

function decisionPanel(decision) {
  if (!decision) return "";
  const record = decision.record;
  const label = normalizeText(record.title) || normalizeText(record.doc_id) || importText("collectionRecordFallback", {
    number: Number(record.record_index) + 1
  });
  const collision = record.collision && record.collision.exists;
  const allowed = Array.isArray(record.allowed_actions) ? record.allowed_actions : [];
  const buttons = allowed
    .filter((action) => action !== "cancel")
    .map((action) => `<button type="button" class="docsViewerImport__button" data-collection-decision="${escapeHtml(action)}">${escapeHtml(decisionLabel(action))}</button>`);
  buttons.push(`<button type="button" class="docsViewerImport__button" data-collection-decision="cancel">${escapeHtml(importText("cancelOverwriteButton"))}</button>`);
  return [
    '<section class="docsViewerImport__collectionDecision">',
    `<h4>${escapeHtml(collision ? importText("collectionResolveCollisionHeading") : importText("collectionResolveRecordErrorHeading"))}</h4>`,
    `<p>${escapeHtml(label)}</p>`,
    collision ? [
      '<label class="docsViewerImport__toggle">',
      '<input type="checkbox" data-collection-apply-all>',
      `<span>${escapeHtml(importText("collectionApplyAllLabel"))}</span>`,
      "</label>"
    ].join("") : "",
    `<div class="docsViewerImport__collectionDecisionActions">${buttons.join("")}</div>`,
    "</section>"
  ].join("");
}

export function renderDocsImportCollectionView(host, viewState, onDecision) {
  if (!host) return;
  const state = viewState || {};
  const plan = state.plan && typeof state.plan === "object" ? state.plan : null;
  host.hidden = !state.active;
  if (!state.active || !plan) {
    host.replaceChildren();
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
    recordList(Array.isArray(plan.records) ? plan.records : [], state.decisions || {}),
    decisionPanel(state.currentDecision),
  ].join("");
  host.querySelectorAll("[data-collection-decision]").forEach((button) => {
    button.addEventListener("click", () => {
      if (typeof onDecision !== "function") return;
      onDecision({
        action: normalizeText(button.dataset.collectionDecision),
        applyToAll: Boolean(host.querySelector("[data-collection-apply-all]")?.checked)
      });
    });
  });
}
import {
  importText
} from "./docs-html-import-text.js";
