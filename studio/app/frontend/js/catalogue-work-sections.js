import {
  buildStudioRouteUrl,
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
  displayValue
} from "./catalogue-editor-records.js";
import {
  getWorkEmbeddedItems,
  renderWorkEmbeddedItemRows
} from "./catalogue-editor-embedded-items.js";
import {
  bindPreviewImages,
  buildDetailThumbPreview,
  buildWorkPrimaryPreview
} from "./catalogue-media-preview.js";
import {
  dedupeSeriesIds,
  normalizeText,
  normalizeWorkId,
  parseSeriesIds
} from "./catalogue-work-fields.js";

const DETAIL_LIST_LIMIT = 10;
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

function normalizeDetailId(value) {
  const digits = normalizeText(value).replace(/\D/g, "");
  if (!digits) return "";
  return digits.padStart(3, "0");
}

function normalizeDetailUid(value, currentWorkId = "") {
  const textValue = normalizeText(value);
  if (!textValue) return "";
  const match = textValue.match(/^(\d{5})-(\d{3})$/);
  if (match) return `${match[1]}-${match[2]}`;
  const digits = textValue.replace(/\D/g, "");
  if (digits.length === 8) {
    return `${digits.slice(0, 5)}-${digits.slice(5)}`;
  }
  if (currentWorkId && digits && digits.length <= 3) {
    return `${normalizeWorkId(currentWorkId)}-${digits.padStart(3, "0")}`;
  }
  return "";
}

function compareDetailUid(a, b) {
  return normalizeText(a).localeCompare(normalizeText(b), undefined, { numeric: true, sensitivity: "base" });
}

function isCurrentWorkPublished(state, options) {
  if (options && typeof options.isCurrentWorkPublished === "function") {
    return Boolean(options.isCurrentWorkPublished(state));
  }
  return normalizeText(state.currentRecord && state.currentRecord.status).toLowerCase() === "published";
}

function draftHasChanges(state, options) {
  if (options && typeof options.draftHasChanges === "function") {
    return Boolean(options.draftHasChanges(state));
  }
  return false;
}

function changedWorkFieldNames(state, options) {
  if (options && typeof options.changedWorkFieldNames === "function") {
    return options.changedWorkFieldNames(state);
  }
  return [];
}

export function buildWorkRecordSummary(record) {
  const title = normalizeText(record && record.title);
  const yearDisplay = normalizeText(record && record.year_display);
  if (title && yearDisplay) return `${title} · ${yearDisplay}`;
  return title || yearDisplay || "—";
}

function buildWorkImageDimensionSummary(record) {
  const height = normalizeText(record && record.height_px);
  const width = normalizeText(record && record.width_px);
  return height && width ? `${height} x ${width} px` : "";
}

export function formatWorkSelectionList(ids) {
  const items = Array.isArray(ids) ? ids.slice(0, BULK_PREVIEW_LIMIT) : [];
  const suffix = Array.isArray(ids) && ids.length > items.length ? `, +${ids.length - items.length}` : "";
  return `${items.join(", ")}${suffix}`;
}

function detailSectionLabel(state, options, sectionKey) {
  return normalizeText(sectionKey) || text(state, options, "details_section_blank", "root");
}

function getWorkDetails(state, workId) {
  if (!state.currentLookup || state.currentWorkId !== workId) return [];
  const sections = Array.isArray(state.currentLookup.detail_sections) ? state.currentLookup.detail_sections : [];
  const details = [];
  sections.forEach((section) => {
    const items = Array.isArray(section && section.details) ? section.details : [];
    items.forEach((item) => details.push(item));
  });
  return details.sort((a, b) => compareDetailUid(a.detail_uid, b.detail_uid));
}

function groupWorkDetailsBySection(details) {
  const groups = new Map();
  details.forEach((detail) => {
    const sectionId = normalizeText(detail && detail.section_id) || normalizeText(detail && detail.project_subfolder);
    const sectionTitle = normalizeText(detail && detail.section_title) || normalizeText(detail && detail.project_subfolder);
    const rawSortOrder = normalizeText(detail && detail.sort_order);
    const key = sectionId || sectionTitle;
    if (!groups.has(key)) {
      groups.set(key, {
        sectionKey: key,
        sectionTitle,
        sortOrder: rawSortOrder && Number.isFinite(Number(rawSortOrder)) ? Number(rawSortOrder) : null,
        items: []
      });
    }
    groups.get(key).items.push(detail);
  });
  return Array.from(groups.values())
    .map((group) => ({
      sectionKey: group.sectionTitle || group.sectionKey,
      sortOrder: group.sortOrder,
      items: group.items.slice().sort((a, b) => compareDetailUid(a.detail_uid, b.detail_uid))
    }))
    .sort((a, b) => {
      if (a.sortOrder !== null && b.sortOrder !== null && a.sortOrder !== b.sortOrder) return a.sortOrder - b.sortOrder;
      if (a.sortOrder !== null && b.sortOrder === null) return -1;
      if (a.sortOrder === null && b.sortOrder !== null) return 1;
      return a.sectionKey.localeCompare(b.sectionKey, undefined, { sensitivity: "base" });
    });
}

function getCurrentWorkDetailMatches(state, rawQuery) {
  const details = getWorkDetails(state, state.currentWorkId);
  const queryText = normalizeText(rawQuery).toLowerCase();
  const normalizedUid = normalizeDetailUid(rawQuery, state.currentWorkId);
  const normalizedDetailId = normalizeDetailId(rawQuery);
  if (!queryText && !normalizedUid && !normalizedDetailId) return [];
  return details.filter((detail) => {
    const detailUid = normalizeText(detail && detail.detail_uid);
    const detailId = normalizeText(detail && detail.detail_id);
    const title = normalizeText(detail && detail.title).toLowerCase();
    return (
      (normalizedUid && detailUid.startsWith(normalizedUid)) ||
      (normalizedDetailId && detailId.startsWith(normalizedDetailId)) ||
      detailUid.toLowerCase().startsWith(queryText) ||
      title.includes(queryText)
    );
  });
}

function buildDetailEditorHref(state, detailUid) {
  return buildStudioRouteUrl(state.config, "catalogue_work_detail_editor", {
    detail: detailUid
  });
}

function renderDetailRows(state, options, details) {
  return details.map((detail) => {
    const detailUid = normalizeText(detail && detail.detail_uid);
    const title = displayValue(detail && detail.title);
    const href = buildDetailEditorHref(state, detailUid);
    const preview = buildDetailThumbPreview(state.mediaConfig, detailUid);
    return `
      <div class="catalogueWorkDetails__row catalogueWorkDetails__row--detail">
        <a class="catalogueThumbPreview" href="${escapeHtml(href)}" data-preview-state="${preview.src ? "loading" : "missing-generated"}" data-preview-fallback="missing-generated" aria-label="${escapeHtml(title)}">
          ${preview.src ? `<img class="catalogueThumbPreview__img" data-preview-image src="${escapeHtml(preview.src)}" srcset="${escapeHtml(preview.srcset || "")}" sizes="48px" width="${escapeHtml(String(preview.width || 48))}" height="${escapeHtml(String(preview.height || 48))}" alt="" loading="lazy" decoding="async">` : ""}
          <span class="catalogueThumbPreview__placeholder">${escapeHtml(text(state, options, "detail_preview_missing", "No preview"))}</span>
        </a>
        <a class="catalogueWorkDetails__link" href="${escapeHtml(href)}">${escapeHtml(detailUid)}</a>
        <span class="catalogueWorkDetails__title">${escapeHtml(title)}</span>
      </div>
    `;
  }).join("");
}

export function renderWorkCurrentPreview(state, options = {}) {
  if (!state.previewNode) return;
  if (state.mode === "bulk" || !state.currentRecord) {
    state.previewNode.innerHTML = "";
    return;
  }
  const record = state.currentRecord;
  const mediaItem = catalogueReadinessItem(state.buildPreview, "work_media");
  const preview = buildWorkPrimaryPreview(state.mediaConfig, record.work_id);
  const fallback = cataloguePreviewFallback(mediaItem, {
    missingGeneratedText: text(state, options, "preview_generated_missing", "Generated preview unavailable. Source media exists."),
    missingSourceText: text(state, options, "preview_source_missing", "Source media missing."),
    unavailableText: text(state, options, "preview_unavailable", "Preview unavailable."),
    notConfiguredText: text(state, options, "preview_not_configured", "Preview not configured.")
  });
  const caption = buildWorkRecordSummary(record);
  const dimensionCaption = buildWorkImageDimensionSummary(record);
  const canShowGenerated = !mediaItem || normalizeText(mediaItem.status) === "ready";
  const previewState = preview.src && canShowGenerated ? "loading" : fallback.fallbackState;
  const publicHref = buildPublicWorkUrl(state.config, record.work_id);
  const isPublished = normalizeText(record && record.status).toLowerCase() === "published";
  const previewHref = isPublished ? publicHref : normalizeText(preview.fullSrc);
  const previewTarget = isPublished ? "" : "_blank";
  const previewRel = isPublished ? "" : "noopener";
  const changedFields = changedWorkFieldNames(state, options);
  const mediaSummaryItem = mediaItem ? catalogueReadinessItemSummary(mediaItem, { fallbackSummary: "—" }) : null;
  const mediaRefreshDisabled = (
    !state.serverAvailable ||
    state.isSaving ||
    state.isBuilding ||
    state.isDeleting ||
    draftHasChanges(state, options) ||
    !mediaSummaryItem ||
    !mediaSummaryItem.exists
  );
  const previewDisabled = (
    !state.serverAvailable ||
    state.isSaving ||
    state.isBuilding ||
    state.isDeleting ||
    state.isPreviewingBuild ||
    state.validationErrors.size > 0 ||
    !isPublished ||
    !changedFields.length
  );
  const frameHtml = `
    <div class="catalogueRecordPreview__frame" data-preview-state="${escapeHtml(previewState)}" data-preview-fallback="${escapeHtml(fallback.fallbackState)}">
      ${preview.src && canShowGenerated ? `<img class="catalogueRecordPreview__media" data-preview-image src="${escapeHtml(preview.src)}" srcset="${escapeHtml(preview.srcset || "")}" sizes="180px" width="${escapeHtml(String(preview.width || 180))}" alt="${escapeHtml(caption)}">` : ""}
      <div class="catalogueRecordPreview__placeholder">${escapeHtml(fallback.fallbackText)}</div>
    </div>
  `;
  state.previewNode.innerHTML = `
    <figure class="catalogueRecordPreview">
      ${previewHref ? `<a class="catalogueRecordPreview__link" href="${escapeHtml(previewHref)}"${previewTarget ? ` target="${escapeHtml(previewTarget)}"` : ""}${previewRel ? ` rel="${escapeHtml(previewRel)}"` : ""}>${frameHtml}</a>` : frameHtml}
      <figcaption class="catalogueRecordPreview__caption">
        <span>${escapeHtml(caption)}</span>
        ${dimensionCaption ? `<span class="catalogueRecordPreview__captionMeta">${escapeHtml(dimensionCaption)}</span>` : ""}
      </figcaption>
      <div class="catalogueRecordPreview__actions">
        <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" data-action="preview-build-impact"${previewDisabled ? " disabled" : ""}>${escapeHtml(text(state, options, "build_preview_button", "Preview update"))}</button>
        ${mediaSummaryItem ? `<button type="button" class="tagStudio__button tagStudio__button--defaultWidth" data-media-refresh="work"${mediaRefreshDisabled ? " disabled" : ""}>${escapeHtml(text(state, options, "media_refresh_button", "Refresh media"))}</button>` : ""}
      </div>
    </figure>
  `;
  const previewButton = state.previewNode.querySelector('[data-action="preview-build-impact"]');
  if (previewButton && typeof options.onPreviewBuildImpact === "function") {
    previewButton.addEventListener("click", () => {
      Promise.resolve(options.onPreviewBuildImpact(state)).catch((error) => {
        console.warn("catalogue_work_editor: unexpected build preview failure", error);
      });
    });
  }
  bindPreviewImages(state.previewNode);
}

export function renderWorkReadiness(state, options = {}) {
  if (!state.readinessNode) return;
  if (state.mode === "bulk" || !state.currentRecord) {
    state.readinessNode.innerHTML = "";
    return;
  }
  const items = catalogueReadinessItems(state.buildPreview)
    .filter((item) => !["work_media", "work_prose"].includes(normalizeText(item && item.key)));
  if (!items.length) {
    state.readinessNode.innerHTML = "";
    return;
  }

  state.readinessNode.innerHTML = items.map((item) => {
    const summaryItem = catalogueReadinessItemSummary(item, { fallbackSummary: "—" });
    const tone = catalogueReadinessTone(summaryItem.status);
    return `
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(summaryItem.title)}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay catalogueReadiness__body">
          <span class="catalogueReadiness__summary" data-tone="${escapeHtml(tone)}">${escapeHtml(summaryItem.summary)}</span>
          ${summaryItem.sourcePath ? `<span class="tagStudioForm__meta catalogueReadiness__path">${escapeHtml(summaryItem.sourcePath)}</span>` : ""}
          ${summaryItem.nextStep ? `<span class="tagStudioForm__meta">${escapeHtml(summaryItem.nextStep)}</span>` : ""}
        </div>
      </div>
    `;
  }).join("");
}

export function updateWorkDetailSections(state, options = {}) {
  if (!state.detailsResultsNode || !state.detailsMetaNode || !state.detailSearchRowNode) return;
  if (!state.currentWorkId) {
    if (state.detailSearchNode) state.detailSearchNode.value = "";
    state.detailSearchRowNode.hidden = true;
    state.detailsMetaNode.textContent = "";
    state.detailsResultsNode.innerHTML = "";
    return;
  }

  const details = getWorkDetails(state, state.currentWorkId);
  if (!details.length) {
    if (state.detailSearchNode) state.detailSearchNode.value = "";
    state.detailSearchRowNode.hidden = true;
    state.detailsMetaNode.textContent = "";
    state.detailsResultsNode.innerHTML = `<p class="tagStudioForm__meta">${escapeHtml(text(state, options, "details_empty", "No work details for this work."))}</p>`;
    return;
  }

  const groups = groupWorkDetailsBySection(details);
  const showDetailSearch = groups.some((group) => group.items.length > DETAIL_LIST_LIMIT);
  if (!showDetailSearch && state.detailSearchNode) {
    state.detailSearchNode.value = "";
  }
  state.detailSearchRowNode.hidden = !showDetailSearch;
  const query = showDetailSearch ? normalizeText(state.detailSearchNode && state.detailSearchNode.value) : "";
  const blocks = [];

  if (query) {
    const matches = getCurrentWorkDetailMatches(state, query);
    if (matches.length) {
      blocks.push(`
        <section class="catalogueWorkDetails__section">
          <div class="tagStudio__headingRow">
            <h3 class="tagStudioForm__key">${escapeHtml(text(state, options, "details_search_results", "matching details"))}</h3>
          </div>
          <div class="catalogueWorkDetails__rows">${renderDetailRows(state, options, matches)}</div>
        </section>
      `);
    } else {
      blocks.push(`<p class="tagStudioForm__meta">${escapeHtml(text(state, options, "details_search_no_match", "No matching detail ids for this work."))}</p>`);
    }
  }

  groups.forEach((group) => {
    const visible = group.items.slice(0, DETAIL_LIST_LIMIT);
    const moreText = group.items.length > DETAIL_LIST_LIMIT
      ? text(state, options, "details_more_count", "showing {visible} of {total}", {
        visible: String(visible.length),
        total: String(group.items.length)
      })
      : "";
    blocks.push(`
      <section class="catalogueWorkDetails__section">
        <div class="tagStudio__headingRow">
          <h3 class="tagStudioForm__key">${escapeHtml(detailSectionLabel(state, options, group.sectionKey))}</h3>
          ${moreText ? `<span class="tagStudioForm__meta">${escapeHtml(moreText)}</span>` : ""}
        </div>
        <div class="catalogueWorkDetails__rows">${renderDetailRows(state, options, visible)}</div>
      </section>
    `);
  });

  state.detailsMetaNode.textContent = `${details.length} total`;
  state.detailsResultsNode.innerHTML = blocks.join("");
  bindPreviewImages(state.detailsResultsNode);
}

export function updateWorkFilesSection(state, options = {}) {
  if (!state.filesResultsNode || !state.filesMetaNode) return;
  if (!state.currentWorkId) {
    state.filesMetaNode.textContent = "";
    state.filesResultsNode.innerHTML = "";
    return;
  }
  const items = state.currentRecord ? getWorkEmbeddedItems(state.draft, "download") : [];
  const error = state.validationErrors.get("downloads") || "";
  if (error) state.filesMetaNode.dataset.state = "error";
  else delete state.filesMetaNode.dataset.state;
  if (!items.length) {
    state.filesMetaNode.textContent = error;
    state.filesResultsNode.innerHTML = `<p class="tagStudioForm__meta">${escapeHtml(text(state, options, "files_empty", "No work files for this work."))}</p>`;
    return;
  }
  state.filesMetaNode.textContent = error || `${items.length} total`;
  const actionDisabled = state.isSaving || state.isBuilding || state.isDeleting || state.mode === "bulk";
  state.filesResultsNode.innerHTML = `
    <section class="catalogueWorkDetails__section">
      <div class="catalogueWorkDetails__rows" data-role="catalogue-work-downloads-list"></div>
      <div class="catalogueWorkDetails__rowActions" data-role="catalogue-work-downloads-actions" aria-label="Download actions"></div>
    </section>
  `;
  const listRoot = state.filesResultsNode.querySelector('[data-role="catalogue-work-downloads-list"]');
  const actionsRoot = state.filesResultsNode.querySelector('[data-role="catalogue-work-downloads-actions"]');
  const list = createRecordList(listRoot, {
    id: "catalogueWorkDownloads",
    records: items,
    selectionMode: "single",
    clearSelectionOnBlur: true,
    columns: [
      {
        key: "filename",
        label: text(state, options, "files_filename_label", "filename"),
        truncate: true
      },
      {
        key: "label",
        label: text(state, options, "files_label_label", "label"),
        truncate: true
      }
    ],
    getRecordId: (_record, index) => `download-${index}`
  });
  createRecordListActions(actionsRoot, {
    id: "catalogueWorkDownloadsActions",
    list,
    actions: [
      {
        key: "edit",
        label: text(state, options, "files_edit_button", "Edit"),
        className: "tagStudio__button",
        disabled: () => actionDisabled
      },
      {
        key: "delete",
        label: text(state, options, "files_delete_button", "Delete"),
        className: "tagStudio__button",
        tone: "danger",
        disabled: () => actionDisabled
      }
    ],
    onAction: ({ actionKey, selection }) => {
      if (!selection) return;
      if (actionKey === "edit" && typeof options.openEmbeddedEntryModal === "function") {
        runMaybeAsync(
          options.openEmbeddedEntryModal("download", selection.index),
          "catalogue_work_sections: failed to edit download"
        );
      }
      if (actionKey === "delete" && typeof options.deleteEmbeddedEntry === "function") {
        runMaybeAsync(
          options.deleteEmbeddedEntry("download", selection.index),
          "catalogue_work_sections: failed to delete download"
        );
      }
    }
  });
}

export function updateWorkLinksSection(state, options = {}) {
  if (!state.linksResultsNode || !state.linksMetaNode) return;
  if (!state.currentWorkId) {
    state.linksMetaNode.textContent = "";
    state.linksResultsNode.innerHTML = "";
    return;
  }
  const items = state.currentRecord ? getWorkEmbeddedItems(state.draft, "link") : [];
  const error = state.validationErrors.get("links") || "";
  if (error) state.linksMetaNode.dataset.state = "error";
  else delete state.linksMetaNode.dataset.state;
  if (!items.length) {
    state.linksMetaNode.textContent = error;
    state.linksResultsNode.innerHTML = `<p class="tagStudioForm__meta">${escapeHtml(text(state, options, "links_empty", "No work links for this work."))}</p>`;
    return;
  }
  state.linksMetaNode.textContent = error || `${items.length} total`;
  state.linksResultsNode.innerHTML = `
    <section class="catalogueWorkDetails__section">
      <div class="tagStudioList catalogueWorkDetails__rows">${renderWorkEmbeddedItemRows("link", items, {
        actionDisabled: state.isSaving || state.isBuilding || state.isDeleting || state.mode === "bulk",
        text: (key, fallback, tokens) => text(state, options, key, fallback, tokens)
      })}</div>
    </section>
  `;
}

export function updateWorkSummary(state, options = {}) {
  if (state.mode === "new") {
    state.metaNode.textContent = text(state, options, "new_meta", "Creating a draft work.");
    state.summaryNode.innerHTML = `
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(text(state, options, "new_summary_status_label", "status"))}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(text(state, options, "new_summary_status", "draft source record; not published"))}</div>
      </div>
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(text(state, options, "new_summary_next_label", "next step"))}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(text(state, options, "new_summary_next", "Create the draft, then continue editing or publish from edit mode."))}</div>
      </div>
    `;
    state.runtimeStateNode.textContent = text(state, options, "new_runtime_state", "public site update is unavailable until the draft exists");
    setTextWithState(options, state.buildImpactNode, "");
    if (state.newDetailLinkNode) {
      state.newDetailLinkNode.removeAttribute("href");
      state.newDetailLinkNode.setAttribute("aria-disabled", "true");
    }
    if (state.newFileLinkNode) {
      state.newFileLinkNode.disabled = true;
    }
    if (state.newLinkLinkNode) {
      state.newLinkLinkNode.disabled = true;
    }
    if (state.detailsPanelNode) state.detailsPanelNode.hidden = false;
    if (state.filesPanelNode) state.filesPanelNode.hidden = false;
    if (state.linksPanelNode) state.linksPanelNode.hidden = false;
    updateWorkDetailSections(state, options);
    updateWorkFilesSection(state, options);
    updateWorkLinksSection(state, options);
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
    state.metaNode.textContent = selectedCount
      ? text(state, options, "bulk_meta", "{count} works selected", { count: String(selectedCount) })
      : "";
    state.summaryNode.innerHTML = `
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(text(state, options, "bulk_summary_selected", "selected works"))}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(formatWorkSelectionList(state.bulkWorkIds) || "—")}</div>
      </div>
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(text(state, options, "bulk_summary_count", "record count"))}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(String(selectedCount || 0))}</div>
      </div>
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(text(state, options, "summary_series_label", "series"))}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay catalogueWorkSummary__series">${escapeHtml(seriesIds.length ? formatWorkSelectionList(seriesIds) : "—")}</div>
      </div>
    `;
    state.runtimeStateNode.textContent = state.rebuildPending
      ? text(state, options, "summary_rebuild_needed", "public update failed in this session")
      : "";
    if (state.newDetailLinkNode) {
      state.newDetailLinkNode.removeAttribute("aria-disabled");
      state.newDetailLinkNode.href = buildStudioRouteUrl(state.config, "catalogue_work_detail_editor");
    }
    if (state.newFileLinkNode) {
      state.newFileLinkNode.disabled = true;
    }
    if (state.newLinkLinkNode) {
      state.newLinkLinkNode.disabled = true;
    }
    if (state.detailsPanelNode) state.detailsPanelNode.hidden = true;
    if (state.filesPanelNode) state.filesPanelNode.hidden = true;
    if (state.linksPanelNode) state.linksPanelNode.hidden = true;
    renderWorkCurrentPreview(state, options);
    renderWorkReadiness(state, options);
    return;
  }

  const record = state.currentRecord;
  state.metaNode.textContent = record
    ? `${record.work_id} · ${buildWorkRecordSummary(record)}`
    : "";

  state.summaryNode.innerHTML = "";

  state.runtimeStateNode.textContent = state.rebuildPending
    ? text(state, options, "summary_rebuild_needed", "public update failed in this session")
    : "";
  if (state.newDetailLinkNode) {
    if (record && isCurrentWorkPublished(state, options)) {
      state.newDetailLinkNode.removeAttribute("aria-disabled");
      state.newDetailLinkNode.removeAttribute("title");
      state.newDetailLinkNode.href = buildStudioRouteUrl(state.config, "catalogue_work_detail_editor", {
        work: record.work_id,
        mode: "new"
      });
    } else {
      state.newDetailLinkNode.setAttribute("aria-disabled", "true");
      state.newDetailLinkNode.title = text(state, options, "details_new_unavailable_draft", "Publish this work before adding work details.");
      state.newDetailLinkNode.removeAttribute("href");
    }
  }
  if (state.newFileLinkNode) {
    state.newFileLinkNode.disabled = !record || state.isSaving || state.isBuilding || state.isDeleting;
  }
  if (state.newLinkLinkNode) {
    state.newLinkLinkNode.disabled = !record || state.isSaving || state.isBuilding || state.isDeleting;
  }
  if (state.detailsPanelNode) state.detailsPanelNode.hidden = false;
  if (state.filesPanelNode) state.filesPanelNode.hidden = false;
  if (state.linksPanelNode) state.linksPanelNode.hidden = false;
  updateWorkDetailSections(state, options);
  updateWorkFilesSection(state, options);
  updateWorkLinksSection(state, options);
  renderWorkCurrentPreview(state, options);
  renderWorkReadiness(state, options);
}
