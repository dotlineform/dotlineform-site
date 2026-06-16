import {
  buildStudioRouteUrl,
  getStudioText
} from "./studio-config.js";
import { displayValue } from "./catalogue-editor-records.js";
import { buildPublicWorkDetailUrl } from "./catalogue-public-links.js";
import {
  normalizeText,
  normalizeWorkId
} from "./catalogue-work-detail-fields.js";

const BULK_PREVIEW_LIMIT = 12;

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
  return getStudioText(state.config, `catalogue_work_detail_editor.${key}`, fallback, tokens);
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

export function buildWorkDetailRecordSummary(record) {
  const title = normalizeText(record && record.title);
  const section = normalizeText(record && record.section_title);
  if (title && section) return `${title} · ${section}`;
  return title || section || "—";
}

function buildParentWorkSummary(record) {
  const workId = normalizeWorkId(record && record.work_id);
  const title = normalizeText(record && record.title);
  const yearDisplay = normalizeText(record && record.year_display);
  const label = [title, yearDisplay].filter(Boolean).join(" · ");
  return label ? `${workId} · ${label}` : workId || "—";
}

export function formatWorkDetailSelectionList(items) {
  const list = Array.isArray(items) ? items.slice(0, BULK_PREVIEW_LIMIT) : [];
  if (!list.length) return "";
  const more = (items.length || 0) - list.length;
  return more > 0 ? `${list.join(", ")} +${more} more` : list.join(", ");
}

export function updateWorkDetailSummary(state, options = {}) {
  if (state.mode === "new") {
    const workId = normalizeWorkId(state.draft.work_id);
    const parentRecord = state.workSearchById.get(workId);
    const parentHref = buildStudioRouteUrl(state.config, "catalogue_work_editor", { work: workId });
    state.summaryNode.innerHTML = `
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(text(state, options, "new_summary_parent_label", "parent work"))}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay">
          ${workId ? `<a href="${escapeHtml(parentHref)}">${escapeHtml(buildParentWorkSummary(parentRecord || { work_id: workId }))}</a>` : "—"}
        </div>
      </div>
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(text(state, options, "new_summary_detail_id_label", "detail id"))}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(displayValue(state.draft.detail_id))}</div>
      </div>
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(text(state, options, "new_summary_next_label", "next step"))}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(text(state, options, "new_summary_next", "Create the detail, then continue editing."))}</div>
      </div>
    `;
    state.runtimeStateNode.textContent = text(state, options, "new_runtime_state", "public site update is unavailable until the draft detail exists");
    setTextWithState(options, state.buildImpactNode, "");
    return;
  }

  if (state.mode === "bulk") {
    const selectedCount = state.bulkDetailUids.length;
    const parentWorkIds = Array.from(new Set(state.bulkDetailUids.map((detailUid) => {
      const record = state.bulkRecords.get(detailUid);
      return normalizeWorkId(record && record.work_id);
    }).filter(Boolean)));
    state.summaryNode.innerHTML = `
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(text(state, options, "bulk_summary_selected", "selected details"))}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(formatWorkDetailSelectionList(state.bulkDetailUids) || "—")}</div>
      </div>
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(text(state, options, "bulk_summary_count", "record count"))}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(String(selectedCount || 0))}</div>
      </div>
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(text(state, options, "bulk_summary_parent_count", "parent works"))}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(formatWorkDetailSelectionList(parentWorkIds) || "—")}</div>
      </div>
    `;
    state.runtimeStateNode.textContent = state.rebuildPending
      ? text(state, options, "summary_rebuild_needed", "public update failed in this session")
      : text(state, options, "summary_rebuild_current", "source and parent work output are aligned in this session");
    return;
  }

  const record = state.currentRecord;
  const publicHref = record ? buildPublicWorkDetailUrl(state.config, record.detail_uid) : "";
  const workEditorHref = record ? buildStudioRouteUrl(state.config, "catalogue_work_editor", { work: record.work_id }) : "";
  state.summaryNode.innerHTML = `
    <div class="tagStudioForm__field">
      <span class="tagStudioForm__label">${escapeHtml(text(state, options, "summary_public_link", "Open public detail page"))}</span>
      <div class="tagStudio__input tagStudio__input--readonlyDisplay">
        ${record ? `<a href="${escapeHtml(publicHref)}" target="_blank" rel="noopener">${escapeHtml(record.detail_uid)}</a>` : "—"}
      </div>
    </div>
    <div class="tagStudioForm__field">
      <span class="tagStudioForm__label">${escapeHtml(text(state, options, "summary_parent_link", "Open work editor"))}</span>
      <div class="tagStudio__input tagStudio__input--readonlyDisplay">
        ${record ? `<a href="${escapeHtml(workEditorHref)}">${escapeHtml(record.work_id)}</a>` : "—"}
      </div>
    </div>
    <div class="tagStudioForm__field">
      <span class="tagStudioForm__label">${escapeHtml(text(state, options, "summary_section_label", "detail section"))}</span>
      <div class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(displayValue(record && (record.section_title || record.project_subfolder)))}</div>
    </div>
  `;

  state.runtimeStateNode.textContent = state.rebuildPending
    ? text(state, options, "summary_rebuild_needed", "public update failed in this session")
    : text(state, options, "summary_rebuild_current", "source and parent work output are aligned in this session");
}
