import {
  buildStudioRouteUrl,
  getStudioText
} from "./studio-config.js";
import {
  createRecordList
} from "/shared/frontend/js/record-list.js";
import {
  displayValue
} from "./catalogue-editor-records.js";
import {
  buildDetailThumbPreview
} from "./catalogue-media-preview.js";
import {
  normalizeText
} from "./catalogue-work-fields.js";

const DETAIL_BROWSER_LIMIT = 10;

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

function clearSectionList(state) {
  if (state.detailBrowserSectionsController && typeof state.detailBrowserSectionsController.destroy === "function") {
    state.detailBrowserSectionsController.destroy();
  } else if (state.detailBrowserSectionsNode) {
    state.detailBrowserSectionsNode.innerHTML = "";
  }
  state.detailBrowserSectionsController = null;
}

function clearImageList(state) {
  if (state.detailBrowserImagesController && typeof state.detailBrowserImagesController.destroy === "function") {
    state.detailBrowserImagesController.destroy();
  } else if (state.detailBrowserImagesNode) {
    state.detailBrowserImagesNode.innerHTML = "";
  }
  state.detailBrowserImagesController = null;
}

function detailSectionId(section, index) {
  return normalizeText(section && (section.section_id || section.section_title)) || `section-${index + 1}`;
}

function detailSectionTitle(section, index) {
  return normalizeText(section && section.section_title)
    || normalizeText(section && section.section_id)
    || `section ${index + 1}`;
}

function detailSectionCount(section) {
  const rawCount = Number(section && section.count);
  if (Number.isFinite(rawCount) && rawCount >= 0) return Math.floor(rawCount);
  return Array.isArray(section && section.details) ? section.details.length : 0;
}

function detailSections(state) {
  return state.currentLookup && Array.isArray(state.currentLookup.detail_sections)
    ? state.currentLookup.detail_sections
    : [];
}

function sectionRows(state) {
  return detailSections(state).map((section, index) => ({
    id: detailSectionId(section, index),
    label: detailSectionTitle(section, index),
    count: detailSectionCount(section),
    section,
    index
  }));
}

function selectedSection(rows, selectedId) {
  if (!rows.length) return null;
  return rows.find((row) => row.id === selectedId) || rows[0];
}

function buildDetailEditorHref(state, detailUid) {
  return buildStudioRouteUrl(state.config, "catalogue_work_detail_editor", {
    detail: detailUid
  });
}

function detailRows(state, options, details) {
  return details.map((detail) => {
    const detailUid = normalizeText(detail && detail.detail_uid);
    const preview = buildDetailThumbPreview(state.mediaConfig, detailUid);
    return {
      detailUid,
      title: displayValue(detail && detail.title),
      editorHref: buildDetailEditorHref(state, detailUid),
      thumbSrc: preview.src,
      thumbSrcset: preview.srcset || "",
      thumbSizes: "48px",
      thumbWidth: 48,
      thumbHeight: 48,
      thumbAlt: "",
      thumbFallback: text(state, options, "detail_browser_preview_missing", "No preview")
    };
  });
}

function selectedDetailId(records, selectedId) {
  return records.some((record) => record.detailUid === selectedId) ? selectedId : "";
}

function renderSelectedImages(state, options, row) {
  if (!state.detailBrowserImagesNode || !state.detailBrowserImagesMetaNode) return;
  clearImageList(state);
  if (!row) {
    state.detailBrowserImagesMetaNode.textContent = "";
    state.detailBrowserImagesNode.innerHTML = "";
    state.detailBrowserSelectedDetailUid = "";
    return;
  }
  const details = Array.isArray(row.section && row.section.details) ? row.section.details : [];
  const visible = details.slice(0, DETAIL_BROWSER_LIMIT);
  const records = detailRows(state, options, visible);
  const more = Math.max(0, details.length - visible.length);
  state.detailBrowserImagesMetaNode.textContent = more > 0
    ? text(state, options, "detail_browser_more_count", "showing {visible} of {total}", {
      visible: String(visible.length),
      total: String(details.length)
    })
    : text(state, options, "detail_browser_section_count", "{count} image(s)", {
      count: String(details.length)
    });
  if (!records.length) {
    state.detailBrowserSelectedDetailUid = "";
    state.detailBrowserImagesNode.innerHTML = `<p class="tagStudioForm__meta">${escapeHtml(text(state, options, "detail_browser_section_empty", "No images in the selected section."))}</p>`;
    return;
  }
  state.detailBrowserSelectedDetailUid = selectedDetailId(records, state.detailBrowserSelectedDetailUid);
  state.detailBrowserImagesController = createRecordList(state.detailBrowserImagesNode, {
    id: "catalogueWorkDetailBrowserImages",
    records,
    columns: [
      {
        key: "thumbSrc",
        label: text(state, options, "detail_browser_thumbnail_heading", "thumbnail"),
        width: "48px",
        type: "image",
        srcKey: "thumbSrc",
        srcsetKey: "thumbSrcset",
        sizesKey: "thumbSizes",
        widthKey: "thumbWidth",
        heightKey: "thumbHeight",
        altKey: "thumbAlt",
        fallbackTextKey: "thumbFallback",
        truncate: false
      },
      {
        key: "detailUid",
        label: text(state, options, "detail_browser_detail_heading", "detail"),
        width: "minmax(6rem, 8rem)",
        type: "link",
        hrefKey: "editorHref",
        external: false,
        truncate: false
      },
      {
        key: "title",
        label: text(state, options, "detail_browser_title_heading", "title"),
        width: "minmax(0, 1fr)",
        truncate: true
      }
    ],
    showHeader: false,
    emptyText: "",
    selectionMode: "single",
    initialSelection: state.detailBrowserSelectedDetailUid,
    selectedBackground: "var(--studio-surface-subtle)",
    getRecordId: (record) => record.detailUid,
    onSelectionChange: ({ selection }) => {
      state.detailBrowserSelectedDetailUid = selection && selection.record ? selection.record.detailUid : "";
    }
  });
}

function resetDetailBrowser(state) {
  clearSectionList(state);
  clearImageList(state);
  state.detailBrowserSelectedSectionId = "";
  state.detailBrowserSelectedDetailUid = "";
  if (state.detailBrowserMetaNode) state.detailBrowserMetaNode.textContent = "";
  if (state.detailBrowserImagesMetaNode) state.detailBrowserImagesMetaNode.textContent = "";
  if (state.detailBrowserImagesNode) state.detailBrowserImagesNode.innerHTML = "";
}

export function updateWorkDetailBrowser(state, options = {}) {
  if (!state.detailBrowserPanelNode || !state.detailBrowserSectionsNode || !state.detailBrowserImagesNode) return;
  clearSectionList(state);
  state.detailBrowserPanelNode.hidden = state.mode === "bulk";
  if (!state.currentWorkId || state.mode === "bulk") {
    resetDetailBrowser(state);
    return;
  }

  const rows = sectionRows(state);
  if (!rows.length) {
    state.detailBrowserSelectedSectionId = "";
    state.detailBrowserSelectedDetailUid = "";
    if (state.detailBrowserMetaNode) {
      state.detailBrowserMetaNode.textContent = text(state, options, "detail_browser_empty", "No work details for this work.");
    }
    state.detailBrowserSectionsNode.innerHTML = "";
    renderSelectedImages(state, options, null);
    return;
  }

  const selected = selectedSection(rows, state.detailBrowserSelectedSectionId);
  state.detailBrowserSelectedSectionId = selected ? selected.id : "";
  if (state.detailBrowserMetaNode) {
    const total = rows.reduce((sum, row) => sum + row.count, 0);
    state.detailBrowserMetaNode.textContent = text(state, options, "detail_browser_meta", "{sections} section(s), {images} image(s)", {
      sections: String(rows.length),
      images: String(total)
    });
  }

  state.detailBrowserSectionsController = createRecordList(state.detailBrowserSectionsNode, {
    id: "catalogueWorkDetailBrowserSections",
    records: rows,
    columns: [
      {
        key: "label",
        label: text(state, options, "detail_browser_sections_heading", "sections"),
        width: "minmax(0, 1fr)",
        truncate: true
      },
      {
        key: "count",
        label: text(state, options, "detail_browser_count_heading", "count"),
        width: "4rem",
        truncate: false
      }
    ],
    showHeader: false,
    emptyText: "",
    selectionMode: "single",
    initialSelection: state.detailBrowserSelectedSectionId,
    selectedBackground: "var(--studio-surface-subtle)",
    getRecordId: (record) => record.id,
    onSelectionChange: ({ selection }) => {
      const nextRow = selection && selection.record ? selection.record : selectedSection(rows, "");
      state.detailBrowserSelectedSectionId = nextRow ? nextRow.id : "";
      renderSelectedImages(state, options, nextRow);
    }
  });

  const listSelection = state.detailBrowserSectionsController.selection();
  renderSelectedImages(state, options, listSelection && listSelection.record ? listSelection.record : selected);
}
