import {
  getStudioText
} from "./studio-config.js";
import {
  createRecordList,
  createRecordListActions
} from "/shared/frontend/js/record-list.js";
import {
  buildPublicWorkUrl
} from "./catalogue-public-links.js";
import {
  cataloguePreviewFallback,
  catalogueReadinessItem,
  catalogueReadinessItems,
  catalogueReadinessItemSummary,
  catalogueReadinessTone
} from "./catalogue-editor-readiness.js";
import {
  getWorkEmbeddedItems
} from "./catalogue-editor-embedded-items.js";
import {
  bindPreviewImages,
  buildWorkPrimaryPreview
} from "./catalogue-media-preview.js";
import {
  dedupeSeriesIds,
  normalizeText,
  parseSeriesIds
} from "./catalogue-work-fields.js";

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
  return getStudioText(state.config, `catalogue_work_editor.${key}`, fallback, tokens);
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

function runMaybeAsync(result, label) {
  if (result && typeof result.catch === "function") {
    result.catch((error) => console.warn(label, error));
  }
}

function clearRecordListActions(state, key, rootNode) {
  const controller = state[key];
  if (controller && typeof controller.destroy === "function") {
    controller.destroy();
  } else if (rootNode) {
    rootNode.innerHTML = "";
    rootNode.classList.remove("sharedRecordListActions");
    delete rootNode.dataset.recordListActionsId;
  }
  state[key] = null;
}

function isCurrentWorkPublished(state, options) {
  if (options && typeof options.isCurrentWorkPublished === "function") {
    return Boolean(options.isCurrentWorkPublished(state));
  }
  return normalizeText(state.currentRecord && state.currentRecord.status).toLowerCase() === "published";
}

function draftHasConfiguredMediaSource(state) {
  return Boolean(normalizeText(state.draft && state.draft.project_folder) && normalizeText(state.draft && state.draft.project_filename));
}

function cacheBustUrl(url, version) {
  const text = normalizeText(url);
  const token = normalizeText(version);
  if (!text || !token) return text;
  return `${text}${text.includes("?") ? "&" : "?"}v=${encodeURIComponent(token)}`;
}

function cacheBustSrcset(srcset, version) {
  const token = normalizeText(version);
  if (!srcset || !token) return srcset || "";
  return String(srcset).split(",").map((entry) => {
    const parts = entry.trim().split(/\s+/);
    if (!parts[0]) return "";
    return [cacheBustUrl(parts[0], token), ...parts.slice(1)].join(" ");
  }).filter(Boolean).join(", ");
}

export function buildWorkRecordSummary(record) {
  const title = normalizeText(record && record.title);
  const yearDisplay = normalizeText(record && record.year_display);
  if (title && yearDisplay) return `${title} · ${yearDisplay}`;
  return title || yearDisplay || "—";
}

export function buildWorkMediaVersionSummary(record, staged) {
  const confirmed = Math.floor(Number(record && record.media_version));
  if (!Number.isFinite(confirmed) || confirmed < 1) return "";
  return staged
    ? `media version ${confirmed} · staged candidate ${confirmed + 1}`
    : `media version ${confirmed}`;
}

function buildWorkImageDimensionSummary(record) {
  const height = normalizeText(record && record.height_px);
  const width = normalizeText(record && record.width_px);
  return height && width ? `${height} x ${width} px` : "";
}

function stagedWorkMediaDimensions(state, workId) {
  if (!normalizeText(state && state.mediaPreviewVersion)) return "";
  const tasks = state && state.buildPreview && state.buildPreview.local_media && Array.isArray(state.buildPreview.local_media.tasks)
    ? state.buildPreview.local_media.tasks
    : [];
  const task = tasks.find((item) => (
    normalizeText(item && item.kind) === "work" &&
    normalizeText(item && item.id) === normalizeText(workId)
  ));
  const height = normalizeText(task && task.source_height_px);
  const width = normalizeText(task && task.source_width_px);
  return height && width ? `${height} x ${width} px` : "";
}

export function formatWorkSelectionList(ids) {
  const items = Array.isArray(ids) ? ids.slice(0, BULK_PREVIEW_LIMIT) : [];
  const suffix = Array.isArray(ids) && ids.length > items.length ? `, +${ids.length - items.length}` : "";
  return `${items.join(", ")}${suffix}`;
}

export function renderWorkCurrentPreview(state, options = {}) {
  if (!state.previewNode) return;
  if (state.mode === "bulk" || !state.currentRecord) {
    state.previewNode.innerHTML = "";
    return;
  }
  const record = state.currentRecord;
  const mediaItem = catalogueReadinessItem(state.buildPreview, "work_media");
  const preview = buildWorkPrimaryPreview(state.mediaConfig, record.work_id, {
    staged: Boolean(normalizeText(state.mediaPreviewVersion)),
    mediaVersion: normalizeText(state.mediaPreviewVersion) ? null : record.media_version
  });
  const previewSrc = cacheBustUrl(preview.src, state.mediaPreviewVersion);
  const previewSrcset = cacheBustSrcset(preview.srcset, state.mediaPreviewVersion);
  const fallback = cataloguePreviewFallback(mediaItem, {
    missingGeneratedText: text(state, options, "preview_generated_missing", "Generated preview unavailable. Source media exists."),
    missingSourceText: text(state, options, "preview_source_missing", "Source media missing."),
    unavailableText: text(state, options, "preview_unavailable", "Preview unavailable."),
    notConfiguredText: text(state, options, "preview_not_configured", "Preview not configured.")
  });
  const caption = buildWorkRecordSummary(record);
  const dimensionCaption = stagedWorkMediaDimensions(state, record.work_id) || buildWorkImageDimensionSummary(record);
  const mediaVersionCaption = buildWorkMediaVersionSummary(record, Boolean(normalizeText(state.mediaPreviewVersion)));
  const canShowGenerated = !mediaItem || normalizeText(mediaItem.status) === "ready";
  const previewState = preview.src && canShowGenerated ? "loading" : fallback.fallbackState;
  const publicHref = buildPublicWorkUrl(state.config, record.work_id);
  const isPublished = normalizeText(record && record.status).toLowerCase() === "published";
  const previewHref = isPublished ? publicHref : normalizeText(preview.fullSrc);
  const previewTarget = isPublished ? "" : "_blank";
  const previewRel = isPublished ? "" : "noopener";
  const mediaSummaryItem = mediaItem ? catalogueReadinessItemSummary(mediaItem, { fallbackSummary: "—" }) : null;
  const mediaRefreshDisabled = (
    !state.serverAvailable ||
    state.isSaving ||
    state.isBuilding ||
    state.isDeleting ||
    !mediaSummaryItem ||
    (!mediaSummaryItem.exists && !draftHasConfiguredMediaSource(state))
  );
  const frameHtml = `
    <div class="catalogueRecordPreview__frame" data-preview-state="${escapeHtml(previewState)}" data-preview-fallback="${escapeHtml(fallback.fallbackState)}">
      ${preview.src && canShowGenerated ? `<img class="catalogueRecordPreview__media" data-preview-image src="${escapeHtml(previewSrc)}" srcset="${escapeHtml(previewSrcset)}" sizes="180px" width="${escapeHtml(String(preview.width || 180))}" alt="${escapeHtml(caption)}">` : ""}
      <div class="catalogueRecordPreview__placeholder">${escapeHtml(fallback.fallbackText)}</div>
    </div>
  `;
  state.previewNode.innerHTML = `
    <figure class="catalogueRecordPreview">
      ${previewHref ? `<a class="catalogueRecordPreview__link" href="${escapeHtml(previewHref)}"${previewTarget ? ` target="${escapeHtml(previewTarget)}"` : ""}${previewRel ? ` rel="${escapeHtml(previewRel)}"` : ""}>${frameHtml}</a>` : frameHtml}
      <figcaption class="catalogueRecordPreview__caption">
        <span>${escapeHtml(caption)}</span>
        ${dimensionCaption ? `<span class="catalogueRecordPreview__captionMeta">${escapeHtml(dimensionCaption)}</span>` : ""}
        ${mediaVersionCaption ? `<span class="catalogueRecordPreview__captionMeta">${escapeHtml(mediaVersionCaption)}</span>` : ""}
      </figcaption>
      <div class="catalogueRecordPreview__actions">
        ${mediaSummaryItem ? `<button type="button" class="studioUi__button studioUi__button--defaultWidth" data-media-refresh="work"${mediaRefreshDisabled ? " disabled" : ""}>${escapeHtml(text(state, options, "media_refresh_button", "Refresh media"))}</button>` : ""}
      </div>
    </figure>
  `;
  bindPreviewImages(state.previewNode);
}

export function renderWorkReadiness(state, options = {}) {
  if (!state.readinessNode) return;
  if (state.mode === "bulk" || !state.currentRecord) {
    state.readinessNode.innerHTML = "";
    return;
  }
  const items = catalogueReadinessItems(state.buildPreview)
    .filter((item) => normalizeText(item && item.key) !== "work_media");
  if (!items.length) {
    state.readinessNode.innerHTML = "";
    return;
  }

  state.readinessNode.innerHTML = items.map((item) => {
    const summaryItem = catalogueReadinessItemSummary(item, { fallbackSummary: "—" });
    const tone = catalogueReadinessTone(summaryItem.status);
    return `
      <div class="studioForm__field">
        <span class="studioForm__label">${escapeHtml(summaryItem.title)}</span>
        <div class="studioUi__input studioUi__input--readonlyDisplay catalogueReadiness__body">
          <span class="catalogueReadiness__summary" data-tone="${escapeHtml(tone)}">${escapeHtml(summaryItem.summary)}</span>
          ${summaryItem.sourcePath ? `<span class="studioForm__meta catalogueReadiness__path">${escapeHtml(summaryItem.sourcePath)}</span>` : ""}
          ${summaryItem.nextStep ? `<span class="studioForm__meta">${escapeHtml(summaryItem.nextStep)}</span>` : ""}
        </div>
      </div>
    `;
  }).join("");
}

function buildWorkDownloadHref(state, filename, options = {}) {
  if (!normalizeText(filename)) return "";
  if (!isCurrentWorkPublished(state, options)) return "";
  const runtime = state.config && state.config.app && state.config.app.runtime;
  const mediaConfig = runtime && runtime.media && typeof runtime.media === "object" ? runtime.media : {};
  const media = mediaConfig.media && typeof mediaConfig.media === "object" ? mediaConfig.media : mediaConfig;
  const base = normalizeText(media.base).replace(/\/+$/, "");
  const worksFiles = normalizeText(media.works_files || (media.paths && media.paths.works_files)).replace(/^\/?/, "/").replace(/\/+$/, "");
  if (!base || !worksFiles) return "";
  return `${base}${worksFiles}/${encodeURIComponent(normalizeText(filename))}`;
}

function buildWorkResourceRows(state, options = {}) {
  const downloads = getWorkEmbeddedItems(state.draft, "download").map((item, index) => ({
    kind: "download",
    index,
    type: "📄",
    label: item.label || "",
    target: item.filename || "",
    targetHref: buildWorkDownloadHref(state, item.filename, options)
  }));
  const links = getWorkEmbeddedItems(state.draft, "link").map((item, index) => ({
    kind: "link",
    index,
    type: "🔗",
    label: item.label || "",
    target: item.url || "",
    targetHref: item.url || ""
  }));
  return downloads.concat(links);
}

export function updateWorkResourcesSection(state, options = {}) {
  if (!state.resourcesResultsNode || !state.resourcesMetaNode) return;
  clearRecordListActions(state, "resourcesActionsController", state.resourcesActionsNode);
  if (!state.currentWorkId) {
    state.resourcesMetaNode.textContent = "";
    state.resourcesResultsNode.innerHTML = "";
    return;
  }
  const items = state.currentRecord ? buildWorkResourceRows(state, options) : [];
  const errors = [
    state.validationErrors.get("downloads") || "",
    state.validationErrors.get("links") || ""
  ].filter(Boolean);
  const error = errors.join(" ");
  if (error) state.resourcesMetaNode.dataset.state = "error";
  else delete state.resourcesMetaNode.dataset.state;
  state.resourcesMetaNode.textContent = error;
  const actionDisabled = state.isSaving || state.isBuilding || state.isDeleting || state.mode === "bulk";
  const addDisabled = !state.currentRecord || actionDisabled;
  state.resourcesResultsNode.innerHTML = `
    <section class="catalogueWorkDetails__section">
      <div class="catalogueWorkDetails__rows" data-role="catalogue-work-resources-list"></div>
    </section>
  `;
  const listRoot = state.resourcesResultsNode.querySelector('[data-role="catalogue-work-resources-list"]');
  const list = createRecordList(listRoot, {
    id: "catalogueWorkResources",
    records: items,
    emptyText: "",
    selectionMode: "single",
    clearSelectionOnBlur: true,
    showHeader: false,
    columns: [
      {
        key: "type",
        label: "type",
        width: "2rem",
        truncate: false
      },
      {
        key: "label",
        label: "label",
        width: "minmax(4.5rem, 0.7fr)",
        truncate: true
      },
      {
        key: "target",
        label: "file / URL",
        width: "minmax(9rem, 1.3fr)",
        type: "link",
        hrefKey: "targetHref",
        truncate: true
      }
    ],
    getRecordId: (record) => `${record.kind}-${record.index}`
  });
  const rowActions = items.length ? [
    {
      key: "edit",
      label: "✏️",
      title: text(state, options, "files_edit_button", "Edit"),
      ariaLabel: text(state, options, "files_edit_button", "Edit"),
      appearance: "icon",
      disabled: () => actionDisabled
    },
    {
      key: "delete",
      label: "🗑️",
      title: text(state, options, "files_delete_button", "Delete"),
      ariaLabel: text(state, options, "files_delete_button", "Delete"),
      appearance: "icon",
      tone: "danger",
      disabled: () => actionDisabled
    }
  ] : [];
  state.resourcesActionsController = createRecordListActions(state.resourcesActionsNode, {
    id: "catalogueWorkResourcesActions",
    list,
    actions: [
      ...rowActions,
      {
        key: "new-download",
        label: "📄",
        title: text(state, options, "files_add_button", "Add file"),
        ariaLabel: text(state, options, "files_add_button", "Add file"),
        appearance: "icon",
        requiresSelection: false,
        disabled: () => addDisabled
      },
      {
        key: "new-link",
        label: "🔗",
        title: text(state, options, "links_add_button", "Add link"),
        ariaLabel: text(state, options, "links_add_button", "Add link"),
        appearance: "icon",
        requiresSelection: false,
        disabled: () => addDisabled
      }
    ],
    onAction: ({ actionKey, selection }) => {
      if (actionKey === "new-download" && typeof options.openEmbeddedEntryModal === "function") {
        runMaybeAsync(
          options.openEmbeddedEntryModal("download"),
          "catalogue_work_sections: failed to add download"
        );
        return;
      }
      if (actionKey === "new-link" && typeof options.openEmbeddedEntryModal === "function") {
        runMaybeAsync(
          options.openEmbeddedEntryModal("link"),
          "catalogue_work_sections: failed to add link"
        );
        return;
      }
      if (!selection) return;
      const selected = selection.record || {};
      const selectedKind = selected.kind === "link" ? "link" : "download";
      const selectedIndex = Number.isInteger(selected.index) ? selected.index : 0;
      if (actionKey === "edit" && typeof options.openEmbeddedEntryModal === "function") {
        runMaybeAsync(
          options.openEmbeddedEntryModal(selectedKind, selectedIndex),
          "catalogue_work_sections: failed to edit resource"
        );
      }
      if (actionKey === "delete" && typeof options.deleteEmbeddedEntry === "function") {
        runMaybeAsync(
          options.deleteEmbeddedEntry(selectedKind, selectedIndex),
          "catalogue_work_sections: failed to delete resource"
        );
      }
    }
  });
}

export function updateWorkSummary(state, options = {}) {
  if (state.mode === "new") {
    state.metaNode.hidden = false;
    state.metaNode.textContent = text(state, options, "new_meta", "Creating a draft work.");
    state.summaryNode.innerHTML = `
      <div class="studioForm__field">
        <span class="studioForm__label">${escapeHtml(text(state, options, "new_summary_status_label", "status"))}</span>
        <div class="studioUi__input studioUi__input--readonlyDisplay">${escapeHtml(text(state, options, "new_summary_status", "draft source record; not published"))}</div>
      </div>
      <div class="studioForm__field">
        <span class="studioForm__label">${escapeHtml(text(state, options, "new_summary_next_label", "next step"))}</span>
        <div class="studioUi__input studioUi__input--readonlyDisplay">${escapeHtml(text(state, options, "new_summary_next", "Create the draft, then continue editing or publish from edit mode."))}</div>
      </div>
    `;
    state.runtimeStateNode.textContent = text(state, options, "new_runtime_state", "public site update is unavailable until the draft exists");
    setTextWithState(options, state.buildImpactNode, "");
    if (state.resourcesPanelNode) state.resourcesPanelNode.hidden = false;
    updateWorkResourcesSection(state, options);
    renderWorkCurrentPreview(state, options);
    renderWorkReadiness(state, options);
    return;
  }

  if (state.mode === "bulk") {
    const selectedCount = state.bulkWorkIds.length;
    const selectedRecords = state.bulkWorkIds.map((workId) => state.bulkRecords.get(workId)).filter(Boolean);
    const seriesIds = dedupeSeriesIds(
      selectedRecords.flatMap((record) => parseSeriesIds(record && record.series_ids))
    );
    state.metaNode.hidden = false;
    state.metaNode.textContent = selectedCount
      ? text(state, options, "bulk_meta", "{count} works selected", { count: String(selectedCount) })
      : "";
    state.summaryNode.innerHTML = `
      <div class="studioForm__field">
        <span class="studioForm__label">${escapeHtml(text(state, options, "bulk_summary_selected", "selected works"))}</span>
        <div class="studioUi__input studioUi__input--readonlyDisplay">${escapeHtml(formatWorkSelectionList(state.bulkWorkIds) || "—")}</div>
      </div>
      <div class="studioForm__field">
        <span class="studioForm__label">${escapeHtml(text(state, options, "bulk_summary_count", "record count"))}</span>
        <div class="studioUi__input studioUi__input--readonlyDisplay">${escapeHtml(String(selectedCount || 0))}</div>
      </div>
      <div class="studioForm__field">
        <span class="studioForm__label">${escapeHtml(text(state, options, "summary_series_label", "series"))}</span>
        <div class="studioUi__input studioUi__input--readonlyDisplay catalogueWorkSummary__series">${escapeHtml(seriesIds.length ? formatWorkSelectionList(seriesIds) : "—")}</div>
      </div>
    `;
    state.runtimeStateNode.textContent = state.rebuildPending
      ? text(state, options, "summary_rebuild_needed", "public update failed in this session")
      : "";
    if (state.resourcesPanelNode) state.resourcesPanelNode.hidden = true;
    renderWorkCurrentPreview(state, options);
    renderWorkReadiness(state, options);
    return;
  }

  state.metaNode.textContent = "";
  state.metaNode.hidden = true;

  state.summaryNode.innerHTML = "";

  state.runtimeStateNode.textContent = state.rebuildPending
    ? text(state, options, "summary_rebuild_needed", "public update failed in this session")
    : "";
  if (state.resourcesPanelNode) state.resourcesPanelNode.hidden = false;
  updateWorkResourcesSection(state, options);
  renderWorkCurrentPreview(state, options);
  renderWorkReadiness(state, options);
}
