import {
  getStudioText
} from "./studio-config.js";
import {
  buildPublicSeriesUrl
} from "./catalogue-public-links.js";
import {
  catalogueReadinessItems,
  catalogueReadinessItemSummary,
  catalogueReadinessTone
} from "./catalogue-editor-readiness.js";
import { displayValue } from "./catalogue-editor-records.js";
import { getCurrentSeriesMemberEntries } from "./catalogue-series-membership.js";
import { normalizeText } from "./catalogue-series-fields.js";

function escapeHtml(value) {
  return normalizeText(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function text(state, options, key, fallback, tokens = null) {
  if (options && typeof options.text === "function") {
    return options.text(key, fallback, tokens);
  }
  return getStudioText(state.config, `catalogue_series_editor.${key}`, fallback, tokens);
}

function setTextWithState(options, node, value, state = "") {
  if (options && typeof options.setTextWithState === "function") {
    options.setTextWithState(node, value, state);
    return;
  }
  if (!node) return;
  node.textContent = value || "";
  if (state) node.dataset.state = state;
  else delete node.dataset.state;
}

function draftHasChanges(state, options) {
  if (options && typeof options.draftHasChanges === "function") {
    return Boolean(options.draftHasChanges(state));
  }
  return false;
}

export function buildSeriesRecordSummary(record) {
  const title = normalizeText(record && record.title);
  return title || "—";
}

export function renderSeriesReadiness(state, options = {}) {
  if (!state.readinessNode || !state.currentRecord) {
    if (state.readinessNode) state.readinessNode.innerHTML = "";
    return;
  }
  const items = catalogueReadinessItems(state.buildPreview);
  if (!items.length) {
    state.readinessNode.innerHTML = "";
    return;
  }

  const actionDisabled = !state.serverAvailable || state.isSaving || state.isBuilding || draftHasChanges(state, options);
  state.readinessNode.innerHTML = items.map((item) => {
    const summaryItem = catalogueReadinessItemSummary(item, { fallbackSummary: "—" });
    const tone = catalogueReadinessTone(summaryItem.status);
    const proseAction = summaryItem.key === "series_prose";
    const proseActionDisabled = actionDisabled || (proseAction && summaryItem.status !== "ready");
    const disabledNote = proseAction && actionDisabled
      ? (draftHasChanges(state, options)
        ? text(state, options, "readiness_save_first", "Save source changes before importing prose.")
        : text(state, options, "readiness_action_busy", "Wait for the current save or rebuild to finish."))
      : "";
    const proseActionLabel = text(state, options, "prose_import_button", "Import staged prose");
    return `
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(summaryItem.title)}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay catalogueReadiness__body">
          <span class="catalogueReadiness__summary" data-tone="${escapeHtml(tone)}">${escapeHtml(summaryItem.summary)}</span>
          ${summaryItem.sourcePath ? `<span class="tagStudioForm__meta catalogueReadiness__path">${escapeHtml(summaryItem.sourcePath)}</span>` : ""}
          ${summaryItem.nextStep ? `<span class="tagStudioForm__meta">${escapeHtml(summaryItem.nextStep)}</span>` : ""}
          ${proseAction ? `<div class="catalogueReadiness__actions"><button type="button" class="tagStudio__button" data-prose-import="series" ${proseActionDisabled ? "disabled" : ""}>${escapeHtml(proseActionLabel)}</button></div>` : ""}
          ${disabledNote ? `<span class="tagStudioForm__meta">${escapeHtml(disabledNote)}</span>` : ""}
        </div>
      </div>
    `;
  }).join("");
}

export function updateSeriesSummary(state, options = {}) {
  if (state.mode === "new") {
    state.metaNode.textContent = text(state, options, "new_meta", "draft source record");
    state.summaryNode.innerHTML = `
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(text(state, options, "new_summary_series_id_label", "series id"))}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(displayValue(state.draft.series_id))}</div>
      </div>
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(text(state, options, "new_summary_status_label", "status"))}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(text(state, options, "new_summary_status", "draft source record; not published"))}</div>
      </div>
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(text(state, options, "new_summary_next_label", "next step"))}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(text(state, options, "new_summary_next", "Create the draft, then add member works, set primary_work_id, and update the site when ready."))}</div>
      </div>
    `;
    state.runtimeStateNode.textContent = text(state, options, "new_runtime_state", "Public site update is unavailable until the draft series exists.");
    setTextWithState(options, state.buildImpactNode, "");
    renderSeriesReadiness(state, options);
    return;
  }

  const record = state.currentRecord;
  state.metaNode.textContent = record ? `${record.series_id} · ${buildSeriesRecordSummary(record)}` : "";
  const publicHref = record ? buildPublicSeriesUrl(state.config, record.series_id) : "";
  const memberCount = getCurrentSeriesMemberEntries(state).length;
  state.summaryNode.innerHTML = `
    <div class="tagStudioForm__field">
      <span class="tagStudioForm__label">${escapeHtml(text(state, options, "summary_public_link", "Open public series page"))}</span>
      <div class="tagStudio__input tagStudio__input--readonlyDisplay">
        ${record ? `<a href="${escapeHtml(publicHref)}" target="_blank" rel="noopener">${escapeHtml(record.series_id)}</a>` : "—"}
      </div>
    </div>
    <div class="tagStudioForm__field">
      <span class="tagStudioForm__label">${escapeHtml(text(state, options, "summary_member_count", "member works"))}</span>
      <div class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(String(memberCount))}</div>
    </div>
  `;
  state.runtimeStateNode.textContent = state.rebuildPending
    ? text(state, options, "summary_rebuild_needed", "source saved; site update pending")
    : text(state, options, "summary_rebuild_current", "source and public catalogue are aligned in this session");
  renderSeriesReadiness(state, options);
}
