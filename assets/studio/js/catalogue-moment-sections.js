import {
  buildPublicCatalogueUrl,
  buildPublicMomentUrl
} from "./catalogue-public-links.js";
import {
  catalogueGeneratedStatusText,
  catalogueReadinessItems,
  catalogueReadinessItemSummary,
  catalogueReadinessTone
} from "./catalogue-editor-readiness.js";
import { displayValue } from "./catalogue-editor-records.js";
import {
  formatCatalogueBuildPreview
} from "./catalogue-editor-modal-formatters.js";
import { normalizeText } from "./catalogue-moment-fields.js";

function escapeHtml(value) {
  return normalizeText(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function text(options, key, fallback, tokens = null) {
  if (options && typeof options.text === "function") {
    return options.text(key, fallback, tokens);
  }
  if (!tokens) return fallback;
  return Object.entries(tokens).reduce((value, [token, replacement]) => {
    return value.replace(new RegExp(`\\{${token}\\}`, "g"), () => replacement == null ? "" : String(replacement));
  }, fallback);
}

function draftHasChanges(options) {
  return Boolean(options && typeof options.draftHasChanges === "function" && options.draftHasChanges());
}

function currentMomentIsPublished(options) {
  return Boolean(options && typeof options.currentMomentIsPublished === "function" && options.currentMomentIsPublished());
}

export function renderMomentReadiness(state, options = {}) {
  const items = catalogueReadinessItems(state.buildPreview, { fallbackReadiness: state.previewReadiness });
  if (!items.length) {
    state.readinessNode.innerHTML = "";
    return;
  }
  const dirty = draftHasChanges(options);
  const actionDisabled = !state.serverAvailable || state.isSaving || state.isBuilding || dirty;
  state.readinessNode.innerHTML = items.map((item) => {
    const summaryItem = catalogueReadinessItemSummary(item);
    const tone = catalogueReadinessTone(summaryItem.status, { missingFileTone: "error" });
    const proseAction = summaryItem.key === "moment_prose";
    const mediaAction = summaryItem.key === "moment_media";
    const proseActionDisabled = actionDisabled || (proseAction && summaryItem.status !== "ready");
    const mediaActionDisabled = actionDisabled || !summaryItem.exists;
    const disabledNote = actionDisabled && (proseAction || mediaAction)
      ? (dirty
        ? (mediaAction ? text(options, "media_refresh_save_first", "Save source changes before refreshing media.") : text(options, "dirty_warning", "Unsaved source changes."))
        : text(options, "readiness_action_busy", "Wait for the current save or public update to finish."))
      : "";
    return `
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(summaryItem.title)}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay catalogueReadiness__body">
          <span class="catalogueReadiness__summary" data-tone="${escapeHtml(tone)}">${escapeHtml(summaryItem.summary)}</span>
          ${summaryItem.sourcePath ? `<span class="tagStudioForm__meta catalogueReadiness__path">${escapeHtml(summaryItem.sourcePath)}</span>` : ""}
          ${summaryItem.nextStep ? `<span class="tagStudioForm__meta">${escapeHtml(summaryItem.nextStep)}</span>` : ""}
          ${proseAction ? `<div class="catalogueReadiness__actions"><button type="button" class="tagStudio__button" data-prose-import="moment" ${proseActionDisabled ? "disabled" : ""}>${escapeHtml(text(options, "prose_import_button", "Import staged prose"))}</button></div>` : ""}
          ${mediaAction ? `<div class="catalogueReadiness__actions"><button type="button" class="tagStudio__button" data-media-refresh="moment" ${mediaActionDisabled ? "disabled" : ""}>${escapeHtml(text(options, "media_refresh_button", "Refresh media"))}</button></div>` : ""}
          ${disabledNote ? `<span class="tagStudioForm__meta">${escapeHtml(disabledNote)}</span>` : ""}
        </div>
      </div>
    `;
  }).join("");
}

export function renderMomentSummary(state, options = {}) {
  const preview = state.preview || {};
  const previewPublicUrl = normalizeText(preview.public_url);
  const publicUrl = previewPublicUrl
    ? buildPublicCatalogueUrl(state.config, previewPublicUrl)
    : buildPublicMomentUrl(state.config, state.currentMomentId);
  const fields = [
    { label: "public URL", value: publicUrl },
    { label: "generated", value: catalogueGeneratedStatusText(preview) },
    { label: "source image", value: preview.source_image_exists ? "source image found" : "source image missing" },
    { label: "prose source", value: preview.source_exists ? "source prose found" : "source prose missing" }
  ];
  state.summaryNode.innerHTML = `
    ${fields.map((field) => `
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(field.label)}</span>
        <span class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(displayValue(field.value, { emptyText: "-" }))}</span>
      </div>
    `).join("")}
    <p class="tagStudioForm__impact"><a href="${escapeHtml(publicUrl)}">${escapeHtml(text(options, "summary_public_link", "Open public moment page"))}</a></p>
  `;
  state.runtimeStateNode.textContent = state.needsBuild
    ? text(options, "summary_rebuild_needed", "public update failed in this session")
    : text(options, "summary_rebuild_current", "source and public moment are aligned in this session");
  renderMomentReadiness(state, options);
}

export function renderMomentBuildImpact(state, options = {}) {
  if (!currentMomentIsPublished(options)) {
    state.buildImpactNode.textContent = text(options, "build_preview_unpublished", "Public update unavailable while the moment is not published.");
    return;
  }
  if (!state.buildPreview) {
    state.buildImpactNode.textContent = "";
    return;
  }
  state.buildImpactNode.textContent = formatCatalogueBuildPreview(state.buildPreview, {
    text: (key, fallback, tokens) => text(options, key, fallback, tokens),
    target: "moment",
    fallbackMomentId: state.currentMomentId,
    defaultTemplate: "Public update preview: moment {moment_ids}; catalogue search {search_rebuild}."
  });
}
