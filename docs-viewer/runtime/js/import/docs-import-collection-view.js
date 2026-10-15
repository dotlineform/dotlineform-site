import {
  docsImportResultDestination
} from "../management/docs-viewer-management-import-result.js";

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
      const title = normalizeText(record.title) || normalizeText(record.doc_id) || `Record ${Number(record.record_index) + 1}`;
      const details = [
        normalizeText(record.doc_id),
        record.parent && record.parent.parent_id ? `parent ${normalizeText(record.parent.parent_id)}` : "",
        record.media_plans && record.media_plans.length ? `${record.media_plans.length} media` : ""
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

function confirmationPanel(phase, renderActions) {
  if (phase !== "confirmation" || renderActions === false) return "";
  return [
    '<section class="docsViewerImport__collectionDecision">',
    '<p>This complete package is ready to import. Content, summaries, and hierarchy changes will be applied together.</p>',
    '<div class="docsViewerImport__collectionDecisionActions">',
    '<button type="button" class="docsViewerImport__button" data-collection-command="cancel">Cancel</button>',
    '<button type="button" class="docsViewerImport__button" data-collection-command="confirm">Confirm import</button>',
    "</div>",
    "</section>"
  ].join("");
}

function resultPanel(result, phase, renderActions) {
  if (!result || typeof result !== "object") return "";
  const counts = result.counts || {};
  const summary = [
    `${Number(counts.created || 0)} creates`,
    `${Number(counts.overwritten || 0)} overwritten`,
    `${Number(counts.failed || 0)} failed`,
    `${Number(counts.not_attempted || 0)} not attempted`
  ].join(" · ");
  const warnings = Array.isArray(result.warnings) ? result.warnings : [];
  const destinationLink = (() => {
    try {
      const destination = docsImportResultDestination(result, { collection: true });
      return (
        `<p><a href="${escapeHtml(destination.href)}" data-collection-destination-link="true">`
        + `${escapeHtml(destination.label)}</a></p>`
      );
    } catch (_error) {
      return "";
    }
  })();
  return [
    '<section class="docsViewerImport__collectionSummary">',
    '<h3>Collection result</h3>',
    `<p>${escapeHtml(summary)}</p>`,
    destinationLink,
    "</section>",
    issueList("Warnings", warnings),
    recordList(Array.isArray(result.records) ? result.records.map((record) => ({
      ...record,
      action: record.status,
      media_plans: []
    })) : []),
    phase === "projection_error" && renderActions !== false
      ? [
          '<section class="docsViewerImport__collectionDecision">',
          '<p>Package import completed, but the collection report refresh failed. Retry the report refresh without importing again.</p>',
          '<div class="docsViewerImport__collectionDecisionActions">',
          '<button type="button" class="docsViewerImport__button" data-collection-command="retry-refresh">Retry report refresh</button>',
          "</div>",
          "</section>"
        ].join("")
      : ""
  ].join("");
}

export function renderDocsImportCollectionView(host, viewState, onCommand, options = {}) {
  if (!host) return;
  const state = viewState || {};
  const plan = state.plan && typeof state.plan === "object" ? state.plan : null;
  host.hidden = !state.active;
  if (!state.active || !plan) {
    host.replaceChildren();
    return;
  }
  if (state.phase === "result" || state.phase === "projection_error") {
    host.innerHTML = resultPanel(state.result, state.phase, options.renderActions);
  } else {
    const counts = plan.counts || {};
    const summary = [
      `${Number(counts.records || 0)} records`,
      `${Number(counts.creates || 0)} creates`,
      `${Number(counts.collisions || 0)} collisions`,
      `${Number(counts.record_errors || 0)} record errors`,
      `${Number(counts.media_plans || 0)} media plans`
    ].join(" · ");
    const stateMessage = state.phase === "confirmation"
      ? "This complete package is ready to import. Content, summaries, and hierarchy changes will be applied together."
      : state.phase === "cancelled"
        ? "Collection import cancelled before apply."
        : "";
    host.innerHTML = [
      '<section class="docsViewerImport__collectionSummary">',
      '<h3>Collection plan</h3>',
      `<p>${escapeHtml(summary)}</p>`,
      stateMessage ? `<p class="docsViewerImport__meta">${escapeHtml(stateMessage)}</p>` : "",
      "</section>",
      issueList("Blockers", plan.blockers),
      issueList("Warnings", plan.warnings),
      recordList(Array.isArray(plan.records) ? plan.records : []),
      confirmationPanel(state.phase, options.renderActions),
    ].join("");
  }
  host.querySelectorAll("[data-collection-command]").forEach((button) => {
    button.addEventListener("click", () => {
      if (typeof onCommand !== "function") return;
      onCommand({ type: normalizeText(button.dataset.collectionCommand) });
    });
  });
}
