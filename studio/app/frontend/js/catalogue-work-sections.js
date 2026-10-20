import {
  createRecordList,
  createRecordListActions
} from "/shared/frontend/js/record-list.js";

import {
  getWorkEmbeddedItems
} from "./catalogue-editor-embedded-items.js";
import {
  bindPreviewImages,
  buildWorkPrimaryPreview
} from "./catalogue-media-preview.js";
import { normalizeText } from "./catalogue-work-fields.js";
import { workPixelsToCm } from "./catalogue-work-image-preview.js";

const BULK_PREVIEW_LIMIT = 12;

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
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


/** Display completed Work fields directly; authoring owns their completion. */
export function buildWorkRecordSummary(record) {
  return `${record.title} · ${record.year_display}`;
}

function buildWorkImageDimensionSummary(record) {
  return `${record.height_px} × ${record.width_px} px`;
}


export function formatWorkSelectionList(ids) {
  const items = Array.isArray(ids) ? ids.slice(0, BULK_PREVIEW_LIMIT) : [];
  const suffix = Array.isArray(ids) && ids.length > items.length ? `, +${ids.length - items.length}` : "";
  return `${items.join(", ")}${suffix}`;
}

export function renderWorkCurrentPreview(state) {
  if (!state.previewNode) return;
  const transient = state.imagePreview;
  if (state.mode === "bulk" || (!state.currentRecord && !transient)) {
    state.previewNode.innerHTML = "";
    return;
  }
  const record = state.currentRecord;
  const preview = transient ? {
    src: transient.url, srcset: "", width: 512, fullSrc: ""
  } : buildWorkPrimaryPreview(state.mediaConfig, record.work_id, {
    mediaVersion: record.media_version, imageStaged: record.image_staged
  });
  const fallback = {
    fallbackState: transient || preview.src ? "unavailable" : "not-configured",
    fallbackText: transient
      ? transient.status === "pending"
        ? `Preparing preview for ${transient.filename}…`
        : transient.error || "Preview image unavailable."
      : preview.src
        ? "Preview image unavailable."
        : "Preview not configured."
  };
  const caption = transient ? transient.filename : buildWorkRecordSummary(record);
  const dimensions = transient ? (transient.status === "ready" ? transient : null) : record;
  const hasDimensions = dimensions?.width_px != null && dimensions?.height_px != null;
  const dimensionCaption = hasDimensions ? buildWorkImageDimensionSummary(dimensions) : "";
  const cmCaption = hasDimensions
    ? `${workPixelsToCm(dimensions.height_px).toFixed(1)} × ${workPixelsToCm(dimensions.width_px).toFixed(1)} cm at 300 dpi`
    : "";
  const canShowGenerated = Boolean(preview.src);
  const previewState = canShowGenerated || transient?.status === "pending" ? "loading" : fallback.fallbackState;
  const previewHref = normalizeText(preview.fullSrc);
  const previewTarget = "_blank";
  const previewRel = "noopener";
  const frameHtml = `
    <div class="catalogueRecordPreview__frame" data-preview-state="${escapeHtml(previewState)}" data-preview-fallback="${escapeHtml(fallback.fallbackState)}">
      ${preview.src && canShowGenerated ? `<img class="catalogueRecordPreview__media" data-preview-image src="${escapeHtml(preview.src)}" srcset="${escapeHtml(preview.srcset)}" sizes="180px" width="${escapeHtml(String(preview.width || 180))}" alt="${escapeHtml(caption)}">` : ""}
      <div class="catalogueRecordPreview__placeholder">${escapeHtml(fallback.fallbackText)}</div>
    </div>
  `;
  state.previewNode.innerHTML = `
    <figure class="catalogueRecordPreview">
      ${previewHref ? `<a class="catalogueRecordPreview__link" href="${escapeHtml(previewHref)}"${previewTarget ? ` target="${escapeHtml(previewTarget)}"` : ""}${previewRel ? ` rel="${escapeHtml(previewRel)}"` : ""}>${frameHtml}</a>` : frameHtml}
      <figcaption class="catalogueRecordPreview__caption">
        <span>${escapeHtml(caption)}</span>
        ${dimensionCaption ? `<span class="catalogueRecordPreview__captionMeta">${escapeHtml(dimensionCaption)}</span>` : ""}
        ${cmCaption ? `<span class="catalogueRecordPreview__captionMeta">${escapeHtml(cmCaption)}</span>` : ""}
      </figcaption>
    </figure>
  `;
  bindPreviewImages(state.previewNode);
}

function buildWorkDownloadHref(state, filename) {
  const runtime = state.config && state.config.app && state.config.app.runtime;
  const mediaConfig = runtime && runtime.media && typeof runtime.media === "object" ? runtime.media : {};
  const media = mediaConfig.media && typeof mediaConfig.media === "object" ? mediaConfig.media : mediaConfig;
  const base = normalizeText(media.base).replace(/\/+$/, "");
  const download = state.currentRecord?.downloads?.find(item => item.filename === filename);
  const selected = download?.staged ? mediaConfig.staged?.works_files : media.works_files;
  const worksFiles = normalizeText(selected).replace(/^\/?/, "/").replace(/\/+$/, "");
  if (!worksFiles) return "";
  return `${base}${worksFiles}/${encodeURIComponent(filename)}`;
}

function buildWorkResourceRows(state, options = {}) {
  const downloads = getWorkEmbeddedItems(state.draft, "download").map((item, index) => ({
    kind: "download",
    index,
    type: "File",
    label: item.label,
    targetHref: state.pendingAttachments.has(item.filename) ? "" : buildWorkDownloadHref(state, item.filename, options)
  }));
  const links = getWorkEmbeddedItems(state.draft, "link").map((item, index) => ({
    kind: "link",
    index,
    type: "Link",
    label: item.label,
    targetHref: item.url
  }));
  return downloads.concat(links);
}

export function updateWorkResourcesSection(state, options = {}) {
  if (!state.resourcesResultsNode || !state.resourcesMetaNode) return;
  clearRecordListActions(state, "resourcesActionsController", state.resourcesActionsNode);
  if (!state.currentWorkId && state.mode !== "new") {
    state.resourcesMetaNode.textContent = "";
    state.resourcesResultsNode.innerHTML = "";
    return;
  }
  const items = state.currentRecord || state.mode === "new" ? buildWorkResourceRows(state, options) : [];
  const errors = [
    state.validationErrors.get("downloads") || "",
    state.validationErrors.get("links") || ""
  ].filter(Boolean);
  const error = errors.join(" ");
  if (error) state.resourcesMetaNode.dataset.state = "error";
  else delete state.resourcesMetaNode.dataset.state;
  state.resourcesMetaNode.textContent = error;
  const actionDisabled = state.isSaving || state.isBuilding || state.isDeleting || state.mode === "bulk";
  const addDisabled = (state.mode !== "new" && !state.currentRecord) || actionDisabled || !state.serverAvailable;
  state.resourcesResultsNode.innerHTML = `
    <section class="catalogueWorkResources__section">
      <div class="catalogueWorkResources__rows" data-role="catalogue-work-resources-list"></div>
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
        type: "icon",
        iconClass: record => `studioUi__icon studioUi__icon--small studioUi__icon--${record.kind === "download" ? "file" : "link"}`,
        width: "2rem",
        truncate: false
      },
      {
        key: "label",
        label: "label",
        formatText: value => value,
        width: "minmax(0, 1fr)",
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
      className: "studioUi__iconButton",
      iconClass: "studioUi__icon studioUi__icon--pen",
      title: "Edit",
      ariaLabel: "Edit",
      appearance: "icon",
      disabled: () => actionDisabled
    },
    {
      key: "delete",
      className: "studioUi__iconButton",
      iconClass: "studioUi__icon studioUi__icon--trash",
      title: "Delete",
      ariaLabel: "Delete",
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
        className: "studioUi__iconButton",
        iconClass: "studioUi__icon studioUi__icon--paperclip",
        title: "Add file",
        ariaLabel: "Add file",
        appearance: "icon",
        requiresSelection: false,
        disabled: () => addDisabled
      },
      {
        key: "new-link",
        className: "studioUi__iconButton",
        iconClass: "studioUi__icon studioUi__icon--link",
        title: "Add link",
        ariaLabel: "Add link",
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
    state.layout.setPreviewAvailable(true);
    state.metaNode.hidden = true;
    state.metaNode.textContent = "";
    state.summaryNode.innerHTML = "";
    if (state.resourcesPanelNode) state.resourcesPanelNode.hidden = false;
    updateWorkResourcesSection(state, options);
    renderWorkCurrentPreview(state);
    return;
  }

  if (state.mode === "bulk") {
    state.layout.setPreviewAvailable(true);
    const selectedCount = state.bulkWorkIds.length;
    const selectedRecords = state.bulkWorkIds.map((workId) => state.bulkRecords.get(workId));
    const seriesIds = Array.from(new Set(selectedRecords.map(record => record.series_id).filter(id => id !== null && id !== undefined)));
    const seriesTitles = seriesIds.map(seriesId => state.seriesById.get(seriesId).title);
    state.metaNode.hidden = false;
    state.metaNode.textContent = selectedCount
      ? `${selectedCount} works selected`
      : "";
    state.summaryNode.innerHTML = `
      <div class="studioForm__field">
        <span class="studioForm__label">selected works</span>
        <div class="studioUi__input studioUi__input--readonlyDisplay">${escapeHtml(formatWorkSelectionList(state.bulkWorkIds) || "—")}</div>
      </div>
      <div class="studioForm__field">
        <span class="studioForm__label">record count</span>
        <div class="studioUi__input studioUi__input--readonlyDisplay">${escapeHtml(String(selectedCount || 0))}</div>
      </div>
      <div class="studioForm__field">
        <span class="studioForm__label">series</span>
        <div class="studioUi__input studioUi__input--readonlyDisplay catalogueWorkSummary__series">${escapeHtml(seriesTitles.length ? seriesTitles.join(", ") : "—")}</div>
      </div>
    `;
    if (state.resourcesPanelNode) state.resourcesPanelNode.hidden = true;
    renderWorkCurrentPreview(state);
    return;
  }

  state.metaNode.textContent = "";
  state.metaNode.hidden = true;
  state.layout.setPreviewAvailable(Boolean(state.currentRecord));

  state.summaryNode.innerHTML = "";

  if (state.resourcesPanelNode) state.resourcesPanelNode.hidden = !state.currentRecord;
  updateWorkResourcesSection(state, options);
  renderWorkCurrentPreview(state);
}
