import {
  getStudioText
} from "./studio-config.js";
import {
  buildPublicWorkUrl
} from "./catalogue-public-links.js";
import {
  bindPreviewImages,
  buildWorkPrimaryPreview
} from "./catalogue-media-preview.js";
import {
  normalizeText,
  normalizeWorkId
} from "./catalogue-series-fields.js";
import {
  getCurrentSeriesMemberEntries
} from "./catalogue-series-membership.js";

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

function buildSeriesRecordSummary(record) {
  const title = normalizeText(record && record.title);
  return title || "-";
}

function buildWorkRecordSummary(record, workId) {
  const title = normalizeText(record && record.title);
  const yearDisplay = normalizeText(record && record.year_display) || normalizeText(record && record.year);
  if (title && yearDisplay) return `${title} · ${yearDisplay}`;
  return title || yearDisplay || normalizeText(workId) || "-";
}

function getSeriesPrimaryWorkEntry(state) {
  const explicitWorkId = normalizeWorkId(state.draft && state.draft.primary_work_id)
    || normalizeWorkId(state.currentRecord && state.currentRecord.primary_work_id);
  const members = getCurrentSeriesMemberEntries(state);
  if (explicitWorkId) {
    const member = members.find((entry) => entry.workId === explicitWorkId);
    return {
      workId: explicitWorkId,
      record: member && member.record ? member.record : state.workSearchById.get(explicitWorkId) || {}
    };
  }
  const firstMember = members[0];
  return firstMember
    ? { workId: firstMember.workId, record: firstMember.record || state.workSearchById.get(firstMember.workId) || {} }
    : { workId: "", record: {} };
}

function buildSeriesPrimaryWorkHref(state, workId, record, preview) {
  const isPublished = normalizeText(record && record.status).toLowerCase() === "published";
  if (isPublished) {
    try {
      return buildPublicWorkUrl(state.config, workId);
    } catch (_error) {
      return "";
    }
  }
  return normalizeText(preview && preview.fullSrc);
}

export function updateSeriesSummary(state, options = {}) {
  if (!state.metaNode) return;
  if (state.mode === "new") {
    state.metaNode.textContent = text(state, options, "new_meta", "draft source record");
    return;
  }
  const record = state.currentRecord;
  state.metaNode.textContent = record ? `${record.series_id} · ${buildSeriesRecordSummary(record)}` : "";
}

export function renderSeriesPrimaryWorkPreview(state, options = {}) {
  if (!state.previewNode) return;
  if (state.mode === "new" || !state.currentRecord) {
    state.previewNode.innerHTML = "";
    return;
  }

  const { workId, record } = getSeriesPrimaryWorkEntry(state);
  if (!workId) {
    state.previewNode.innerHTML = "";
    return;
  }

  const preview = buildWorkPrimaryPreview(state.mediaConfig, workId);
  const caption = buildWorkRecordSummary(record, workId);
  const fallbackState = preview.src ? "unavailable" : "not-configured";
  const fallbackText = preview.src
    ? text(state, options, "preview_unavailable", "Preview unavailable.")
    : text(state, options, "preview_not_configured", "Preview not configured.");
  const previewState = preview.src ? "loading" : fallbackState;
  const previewHref = buildSeriesPrimaryWorkHref(state, workId, record, preview);
  const previewTarget = previewHref && normalizeText(record && record.status).toLowerCase() !== "published" ? "_blank" : "";
  const previewRel = previewTarget ? "noopener" : "";
  const frameHtml = `
    <div class="catalogueRecordPreview__frame" data-preview-state="${escapeHtml(previewState)}" data-preview-fallback="${escapeHtml(fallbackState)}">
      ${preview.src ? `<img class="catalogueRecordPreview__media" data-preview-image src="${escapeHtml(preview.src)}" srcset="${escapeHtml(preview.srcset)}" sizes="180px" width="${escapeHtml(String(preview.width || 180))}" alt="${escapeHtml(caption)}">` : ""}
      <div class="catalogueRecordPreview__placeholder">${escapeHtml(fallbackText)}</div>
    </div>
  `;

  state.previewNode.innerHTML = `
    <figure class="catalogueRecordPreview">
      ${previewHref ? `<a class="catalogueRecordPreview__link" href="${escapeHtml(previewHref)}"${previewTarget ? ` target="${escapeHtml(previewTarget)}"` : ""}${previewRel ? ` rel="${escapeHtml(previewRel)}"` : ""}>${frameHtml}</a>` : frameHtml}
      <figcaption class="catalogueRecordPreview__caption">
        <span>${escapeHtml(caption)}</span>
      </figcaption>
    </figure>
  `;
  bindPreviewImages(state.previewNode);
}
