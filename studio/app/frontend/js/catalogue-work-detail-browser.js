import { getStudioText } from "./studio-config.js";
import {
  createRecordList,
  createRecordListActions
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

function clearActions(state) {
  if (state.detailBrowserActionsController && typeof state.detailBrowserActionsController.destroy === "function") {
    state.detailBrowserActionsController.destroy();
  } else if (state.detailBrowserActionsNode) {
    state.detailBrowserActionsNode.innerHTML = "";
  }
  state.detailBrowserActionsController = null;
}

function searchDigits(value) {
  const digits = normalizeText(value).replace(/\D/g, "");
  return digits.slice(-3);
}

function detailRowDigits(detail) {
  const detailIdDigits = searchDigits(detail && detail.detail_id);
  if (detailIdDigits) return detailIdDigits.padStart(3, "0");
  return searchDigits(detail && detail.detail_uid).padStart(3, "0");
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

function allDetails(state) {
  const details = [];
  detailSections(state).forEach((section) => {
    const items = Array.isArray(section && section.details) ? section.details : [];
    items.forEach((detail) => details.push(detail));
  });
  return details;
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

function canCreateDetail(state, options) {
  if (options && typeof options.isCurrentWorkPublished === "function") {
    return Boolean(options.isCurrentWorkPublished(state));
  }
  return normalizeText(state.currentRecord && state.currentRecord.status).toLowerCase() === "published";
}

function detailRows(state, options, details) {
  return details.map((detail) => {
    const detailUid = normalizeText(detail && detail.detail_uid);
    const preview = buildDetailThumbPreview(state.mediaConfig, detailUid);
    return {
      detailUid,
      title: displayValue(detail && detail.title),
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

function detailBrowserSearchQuery(state) {
  return searchDigits(state.detailBrowserSearchNode && state.detailBrowserSearchNode.value);
}

function syncDetailBrowserSearchControl(state, query) {
  if (!state.detailBrowserSearchNode) return;
  if (state.detailBrowserSearchNode.value !== query) {
    state.detailBrowserSearchNode.value = query;
  }
  if (state.detailBrowserSearchClearNode) {
    state.detailBrowserSearchClearNode.hidden = !query;
  }
}

function renderDetailActions(state, options, { list = null, hasDetails = false } = {}) {
  if (!state.detailBrowserActionsNode) return;
  clearActions(state);
  if (!state.currentWorkId) return;
  const createEnabled = canCreateDetail(state, options);
  const actions = [
    ...(hasDetails ? [
      {
        key: "edit",
        label: "✏️",
        title: text(state, options, "detail_browser_edit_button", "Edit"),
        ariaLabel: text(state, options, "detail_browser_edit_button", "Edit"),
        appearance: "icon"
      },
      {
        key: "delete",
        label: "🗑️",
        title: text(state, options, "detail_browser_delete_button", "Delete"),
        ariaLabel: text(state, options, "detail_browser_delete_button", "Delete"),
        appearance: "icon",
        tone: "danger"
      }
    ] : []),
    {
      key: "new",
      label: "📄",
      title: createEnabled
        ? text(state, options, "detail_browser_new_button", "New")
        : text(state, options, "details_new_unavailable_draft", "Publish this work before adding work details."),
      ariaLabel: text(state, options, "detail_browser_new_button", "New"),
      appearance: "icon",
      requiresSelection: false,
      disabled: () => !createEnabled
    }
  ];
  state.detailBrowserActionsController = createRecordListActions(state.detailBrowserActionsNode, {
    id: "catalogueWorkDetailBrowserActionsList",
    list,
    actions,
    onAction: ({ actionKey, selection }) => {
      if (actionKey === "new") {
        if (!canCreateDetail(state, options)) return;
        return;
      }
      const detailUid = selection && selection.record ? selection.record.detailUid : "";
      if (!detailUid) return;
    }
  });
}

function selectedDetailId(records, selectedId) {
  return records.some((record) => record.detailUid === selectedId) ? selectedId : "";
}

function renderSelectedImages(state, options, row) {
  if (!state.detailBrowserImagesNode) return;
  clearImageList(state);
  const query = detailBrowserSearchQuery(state);
  syncDetailBrowserSearchControl(state, query);
  if (!row && !query) {
    state.detailBrowserImagesNode.innerHTML = "";
    state.detailBrowserSelectedDetailUid = "";
    return;
  }
  const details = query
    ? allDetails(state).filter((detail) => detailRowDigits(detail).includes(query))
    : (Array.isArray(row.section && row.section.details) ? row.section.details : []);
  const visible = query ? details : details.slice(0, DETAIL_BROWSER_LIMIT);
  const records = detailRows(state, options, visible);
  if (!records.length) {
    state.detailBrowserSelectedDetailUid = "";
    state.detailBrowserImagesNode.innerHTML = `<p class="tagStudioForm__meta">${escapeHtml(query
      ? text(state, options, "detail_browser_search_empty", "No matching detail ids.")
      : text(state, options, "detail_browser_section_empty", "No images in the selected section."))}</p>`;
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
    getRecordId: (record) => record.detailUid,
    onSelectionChange: ({ selection }) => {
      state.detailBrowserSelectedDetailUid = selection && selection.record ? selection.record.detailUid : "";
    }
  });
}

function resetDetailBrowser(state) {
  clearSectionList(state);
  clearImageList(state);
  clearActions(state);
  state.detailBrowserSelectedSectionId = "";
  state.detailBrowserSelectedDetailUid = "";
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
  const hasDetails = rows.some((row) => row.count > 0);
  if (!rows.length) {
    state.detailBrowserSelectedSectionId = "";
    state.detailBrowserSelectedDetailUid = "";
    state.detailBrowserSectionsNode.innerHTML = `<p class="tagStudioForm__meta">${escapeHtml(text(state, options, "detail_browser_empty", "No work details for this work."))}</p>`;
    renderSelectedImages(state, options, null);
    renderDetailActions(state, options, { hasDetails: false });
    return;
  }

  const selected = selectedSection(rows, state.detailBrowserSelectedSectionId);
  state.detailBrowserSelectedSectionId = selected ? selected.id : "";

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
    getRecordId: (record) => record.id,
    onSelectionChange: ({ selection }) => {
      const nextRow = selection && selection.record ? selection.record : selectedSection(rows, "");
      state.detailBrowserSelectedSectionId = nextRow ? nextRow.id : "";
      renderSelectedImages(state, options, nextRow);
      renderDetailActions(state, options, {
        list: state.detailBrowserImagesController,
        hasDetails
      });
    }
  });

  const listSelection = state.detailBrowserSectionsController.selection();
  renderSelectedImages(state, options, listSelection && listSelection.record ? listSelection.record : selected);
  renderDetailActions(state, options, {
    list: state.detailBrowserImagesController,
    hasDetails
  });
}
