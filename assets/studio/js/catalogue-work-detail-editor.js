import {
  getStudioRoute,
  getStudioText,
  loadStudioConfigWithText
} from "./studio-config.js";
import { loadStudioLookupJson, loadStudioLookupRecordJson } from "./studio-data.js";
import {
  probeCatalogueHealth
} from "./studio-transport.js";
import {
  applyCatalogueBuild,
  applyCatalogueDelete,
  applyCataloguePublication,
  createCatalogueWorkDetail,
  previewCatalogueBuild,
  previewCatalogueDelete,
  previewCataloguePublication,
  saveCatalogueBulkRecords,
  saveCatalogueWorkDetail
} from "./catalogue-editor-service-client.js";
import {
  cataloguePreviewFallback,
  catalogueReadinessItem,
  catalogueReadinessItems,
  catalogueReadinessItemSummary,
  catalogueReadinessTone
} from "./catalogue-editor-readiness.js";
import {
  computeRecordHash,
  displayValue
} from "./catalogue-editor-records.js";
import {
  catalogueDeleteDisabled,
  catalogueDirtyWarningText,
  catalogueDraftHasChanges,
  catalogueSaveDisabled
} from "./catalogue-editor-dirty-state.js";
import {
  formatCatalogueBuildPreview,
  formatCatalogueDeletePreview,
  formatCataloguePublicationPreview
} from "./catalogue-editor-modal-formatters.js";
import {
  initializeStudioRouteState,
  setStudioRouteBusy,
  setStudioRouteReady
} from "./studio-route-state.js";
import {
  buildSaveModeText,
  utcTimestamp
} from "./tag-studio-save.js";
import { buildStudioActivityContext } from "./studio-activity-context.js";
import {
  bindPreviewImages,
  buildDetailThumbPreview,
  loadCatalogueMediaConfig
} from "./catalogue-media-preview.js";
import {
  WORK_DETAIL_EDITABLE_FIELDS as EDITABLE_FIELDS,
  WORK_DETAIL_FIELD_DEFINITIONS,
  WORK_DETAIL_READONLY_FIELDS as READONLY_FIELDS,
  WORK_DETAIL_STATUS_OPTIONS as STATUS_OPTIONS,
  buildCreateWorkDetailPayload,
  buildSaveWorkDetailPayload,
  buildWorkDetailDraftFromRecord,
  canonicalizeWorkDetailScalar as canonicalizeScalar,
  normalizeDetailId,
  normalizeDetailUid,
  normalizeText,
  normalizeWorkId,
  suggestNextDetailId,
  validateCreateWorkDetailDraft
} from "./catalogue-work-detail-fields.js";

const FORM_FIELDS = Object.freeze([
  WORK_DETAIL_FIELD_DEFINITIONS.work_id,
  WORK_DETAIL_FIELD_DEFINITIONS.detail_id,
  ...EDITABLE_FIELDS
]);
const SEARCH_LIMIT = 20;
const BULK_PREVIEW_LIMIT = 12;

function escapeHtml(value) {
  return normalizeText(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function renderCurrentPreview(state) {
  if (!state.previewNode) return;
  if (state.mode === "bulk" || !state.currentRecord) {
    state.previewNode.innerHTML = "";
    return;
  }
  const record = state.currentRecord;
  const mediaItem = catalogueReadinessItem(state.buildPreview, "detail_media", { keys: ["detail_media"] });
  const preview = buildDetailThumbPreview(state.mediaConfig, record.detail_uid);
  const fallback = cataloguePreviewFallback(mediaItem, {
    missingGeneratedText: t(state, "preview_generated_missing", "Generated preview unavailable. Source media exists."),
    missingSourceText: t(state, "preview_source_missing", "Source media missing."),
    unavailableText: t(state, "preview_unavailable", "Preview unavailable."),
    notConfiguredText: t(state, "preview_not_configured", "Preview not configured.")
  });
  const caption = buildRecordSummary(record);
  const canShowGenerated = !mediaItem || normalizeText(mediaItem.status) === "ready";
  const previewState = preview.src && canShowGenerated ? "loading" : fallback.fallbackState;
  state.previewNode.innerHTML = `
    <figure class="catalogueRecordPreview">
      <div class="catalogueRecordPreview__frame" data-preview-state="${escapeHtml(previewState)}" data-preview-fallback="${escapeHtml(fallback.fallbackState)}">
        ${preview.src && canShowGenerated ? `<img class="catalogueRecordPreview__media" data-preview-image src="${escapeHtml(preview.src)}" srcset="${escapeHtml(preview.srcset || "")}" sizes="180px" width="${escapeHtml(String(preview.width || 96))}" height="${escapeHtml(String(preview.height || 96))}" alt="${escapeHtml(caption)}">` : ""}
        <div class="catalogueRecordPreview__placeholder">${escapeHtml(fallback.fallbackText)}</div>
      </div>
      <figcaption class="catalogueRecordPreview__caption">${escapeHtml(caption)}</figcaption>
    </figure>
  `;
  bindPreviewImages(state.previewNode);
}

function renderReadiness(state) {
  if (!state.readinessNode) return;
  if (state.mode === "bulk" || !state.currentRecord) {
    state.readinessNode.innerHTML = "";
    return;
  }
  const items = catalogueReadinessItems(state.buildPreview, { keys: ["detail_media"] });
  if (!items.length) {
    state.readinessNode.innerHTML = "";
    return;
  }
  const actionDisabled = !state.serverAvailable || state.isSaving || state.isBuilding || draftHasChanges(state);
  state.readinessNode.innerHTML = items.map((item) => {
    const summaryItem = catalogueReadinessItemSummary(item, { fallbackSummary: "—" });
    const tone = catalogueReadinessTone(summaryItem.status);
    const mediaAction = summaryItem.key === "detail_media";
    const mediaActionDisabled = actionDisabled || !summaryItem.exists;
    const disabledNote = mediaAction && actionDisabled
      ? (draftHasChanges(state)
        ? t(state, "media_refresh_save_first", "Save source changes before refreshing media.")
        : t(state, "readiness_action_busy", "Wait for the current save or rebuild to finish."))
      : "";
    const mediaActionLabel = t(state, "media_refresh_button", "Refresh media");
    return `
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(summaryItem.title)}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay catalogueReadiness__body">
          <span class="catalogueReadiness__summary" data-tone="${escapeHtml(tone)}">${escapeHtml(summaryItem.summary)}</span>
          ${summaryItem.sourcePath ? `<span class="tagStudioForm__meta catalogueReadiness__path">${escapeHtml(summaryItem.sourcePath)}</span>` : ""}
          ${summaryItem.nextStep ? `<span class="tagStudioForm__meta">${escapeHtml(summaryItem.nextStep)}</span>` : ""}
          ${mediaAction ? `<div class="catalogueReadiness__actions"><button type="button" class="tagStudio__button" data-media-refresh="detail" ${mediaActionDisabled ? "disabled" : ""}>${escapeHtml(mediaActionLabel)}</button></div>` : ""}
          ${disabledNote ? `<span class="tagStudioForm__meta">${escapeHtml(disabledNote)}</span>` : ""}
        </div>
      </div>
    `;
  }).join("");
}

function parseDetailSelection(rawValue) {
  const text = normalizeText(rawValue);
  if (!text) return [];
  const tokens = text.split(",").map((item) => normalizeText(item)).filter(Boolean);
  const detailUids = [];
  const seen = new Set();
  tokens.forEach((token) => {
    const rangeMatch = token.match(/^(\d{5})-(\d{3})-(\d{3})$/);
    if (rangeMatch) {
      const workId = normalizeWorkId(rangeMatch[1]);
      const start = Number(rangeMatch[2]);
      const end = Number(rangeMatch[3]);
      if (!Number.isFinite(start) || !Number.isFinite(end) || start > end) {
        throw new Error(`Invalid detail range: ${token}`);
      }
      for (let value = start; value <= end; value += 1) {
        const detailUid = `${workId}-${String(value).padStart(3, "0")}`;
        if (seen.has(detailUid)) continue;
        seen.add(detailUid);
        detailUids.push(detailUid);
      }
      return;
    }
    const detailUid = normalizeDetailUid(token);
    if (!detailUid) {
      throw new Error(`Invalid detail id: ${token}`);
    }
    if (seen.has(detailUid)) return;
    seen.add(detailUid);
    detailUids.push(detailUid);
  });
  return detailUids;
}

function isDetailBulkQuery(rawValue) {
  try {
    return parseDetailSelection(rawValue).length > 1;
  } catch (_error) {
    return false;
  }
}

function formatSelectionList(items) {
  const list = Array.isArray(items) ? items.slice(0, BULK_PREVIEW_LIMIT) : [];
  if (!list.length) return "";
  const more = (items.length || 0) - list.length;
  return more > 0 ? `${list.join(", ")} +${more} more` : list.join(", ");
}

function buildBulkDraftFromRecords(records) {
  const drafts = records.map((record) => buildWorkDetailDraftFromRecord(record));
  const draft = {};
  const mixedFields = new Set();
  EDITABLE_FIELDS.forEach((field) => {
    const values = drafts.map((item) => canonicalizeScalar(field, item[field.key]));
    const first = values[0] || "";
    const allSame = values.every((value) => value === first);
    if (allSame) {
      draft[field.key] = drafts[0][field.key];
    } else {
      draft[field.key] = "";
      mixedFields.add(field.key);
    }
  });
  return { draft, mixedFields };
}

function setFieldNodeValue(node, value) {
  const text = normalizeText(value);
  if ("value" in node) {
    node.value = text;
  } else {
    node.textContent = displayValue(text);
  }
}

function getFieldNodeValue(node) {
  if ("value" in node) return node.value;
  return normalizeText(node.textContent);
}

function setTextWithState(node, text, state = "") {
  if (!node) return;
  node.textContent = text || "";
  if (state) node.dataset.state = state;
  else delete node.dataset.state;
}

function routeModeForState(state) {
  if (state.mode === "new") return "new";
  if (state.mode === "bulk") return "bulk";
  if (state.currentRecord) return "single";
  return "empty";
}

function routeRecordLoadedForState(state) {
  if (state.mode === "bulk") return state.bulkDetailUids.length > 0;
  if (state.mode === "single") return Boolean(state.currentRecord);
  return false;
}

function routeStateDetail(state) {
  return {
    route: "catalogue-work-detail",
    mode: routeModeForState(state),
    service: state.serverAvailable ? "available" : "unavailable",
    recordLoaded: routeRecordLoadedForState(state)
  };
}

function syncRouteBusyState(state) {
  setStudioRouteBusy(
    state.root,
    Boolean(state.isSaving || state.isBuilding || state.isDeleting),
    routeStateDetail(state)
  );
}

function markRouteReady(state, ready) {
  setStudioRouteReady(state.root, ready, routeStateDetail(state));
}

function setPopupVisibility(state, visible) {
  state.popupNode.hidden = !visible;
}

function renderField(field, fieldsNode, state) {
  const wrapper = document.createElement(field.readonly ? "div" : "label");
  wrapper.className = "tagStudioForm__field catalogueWorkForm__field";
  if (!field.readonly) wrapper.htmlFor = `catalogueWorkDetailField-${field.key}`;

  const label = document.createElement("span");
  label.className = "tagStudioForm__label";
  label.dataset.fieldLabel = field.key;
  label.textContent = t(state, `field_label_${field.key}`, field.label);
  wrapper.appendChild(label);

  let input;
  if (field.readonly) {
    input = document.createElement("span");
    input.className = "tagStudio__input tagStudio__input--readonlyDisplay";
  } else if (field.type === "select") {
    input = document.createElement("select");
    input.className = "tagStudio__input";
    field.options.forEach((optionValue) => {
      const option = document.createElement("option");
      option.value = optionValue;
      option.textContent = optionValue || "(blank)";
      input.appendChild(option);
    });
  } else {
    input = document.createElement("input");
    input.className = "tagStudio__input";
    input.type = "text";
  }

  input.id = `catalogueWorkDetailField-${field.key}`;
  input.dataset.field = field.key;
  wrapper.appendChild(input);

  const message = document.createElement("span");
  message.className = "catalogueWorkForm__fieldStatus";
  message.dataset.fieldStatus = field.key;
  wrapper.appendChild(message);

  if (!field.readonly) {
    input.addEventListener("input", () => onFieldInput(state, field.key));
    input.addEventListener("change", () => onFieldInput(state, field.key));
  }
  fieldsNode.appendChild(wrapper);
  state.fieldWrappers.set(field.key, wrapper);
  state.fieldNodes.set(field.key, input);
  state.fieldStatusNodes.set(field.key, message);
}

function renderReadonlyField(field, readonlyNode, state) {
  const wrapper = document.createElement("div");
  wrapper.className = "tagStudioForm__field";

  const label = document.createElement("span");
  label.className = "tagStudioForm__label";
  label.dataset.fieldLabel = field.key;
  label.textContent = t(state, `field_label_${field.key}`, field.label);
  wrapper.appendChild(label);

  const value = document.createElement("div");
  value.className = "tagStudio__input tagStudio__input--readonlyDisplay";
  value.dataset.readonlyField = field.key;
  value.textContent = "—";
  wrapper.appendChild(value);

  readonlyNode.appendChild(wrapper);
  state.readonlyNodes.set(field.key, value);
}

function applyFieldLabels(state) {
  [...FORM_FIELDS, ...READONLY_FIELDS].forEach((field) => {
    const labels = document.querySelectorAll(`[data-field-label="${field.key}"]`);
    labels.forEach((label) => {
      label.textContent = t(state, `field_label_${field.key}`, field.label);
    });
  });
}

function buildRecordSummary(record) {
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

function buildDetailSearchRecord(detailUid, record) {
  return {
    detail_uid: detailUid,
    work_id: normalizeText(record && record.work_id),
    detail_id: normalizeText(record && record.detail_id),
    title: normalizeText(record && record.title),
    section_id: normalizeText(record && record.section_id),
    section_title: normalizeText(record && record.section_title),
    sort_order: normalizeText(record && record.sort_order),
    details_subfolder: normalizeText(record && record.details_subfolder),
    project_filename: normalizeText(record && record.project_filename),
    status: normalizeText(record && record.status)
  };
}

function getSearchMatches(state, rawQuery) {
  const query = normalizeText(rawQuery).toLowerCase();
  const normalizedUid = normalizeDetailUid(rawQuery);
  const normalizedDetailId = normalizeDetailId(rawQuery);
  if (!query && !normalizedUid && !normalizedDetailId) return [];
  const matches = [];
  for (const [detailUid, record] of state.detailSearchByUid.entries()) {
    const detailId = normalizeText(record && record.detail_id);
    const title = normalizeText(record && record.title).toLowerCase();
    if (
      (normalizedUid && detailUid.startsWith(normalizedUid)) ||
      (normalizedDetailId && detailId.startsWith(normalizedDetailId)) ||
      detailUid.toLowerCase().startsWith(query) ||
      title.includes(query)
    ) {
      matches.push({ detailUid, record });
    }
  }
  matches.sort((a, b) => a.detailUid.localeCompare(b.detailUid, undefined, { numeric: true, sensitivity: "base" }));
  return matches.slice(0, SEARCH_LIMIT);
}

function renderSearchMatches(state, matches, message = "") {
  if (!matches.length && !message) {
    state.popupListNode.innerHTML = "";
    setPopupVisibility(state, false);
    return;
  }

  if (!matches.length) {
    state.popupListNode.innerHTML = `<p class="tagStudioForm__meta">${escapeHtml(message)}</p>`;
    setPopupVisibility(state, true);
    return;
  }

  const rows = matches.map(({ detailUid, record }) => `
    <button type="button" class="tagStudioSuggest__workButton" data-detail-uid="${escapeHtml(detailUid)}">
      <span class="tagStudioSuggest__workId">${escapeHtml(detailUid)}</span>
      <span class="tagStudioSuggest__workTitle">${escapeHtml(buildRecordSummary(record))}</span>
    </button>
  `);
  state.popupListNode.innerHTML = `<div class="tagStudioSuggest__workRows">${rows.join("")}</div>`;
  setPopupVisibility(state, true);
}

async function loadDetailLookupRecord(state, detailUid) {
  return loadStudioLookupRecordJson(state.config, "catalogue_lookup_work_detail_base", detailUid, {
    cache: "no-store",
    catalogueServerAvailable: state.serverAvailable
  });
}

function applyDraftToInputs(state) {
  FORM_FIELDS.forEach((field) => {
    const node = state.fieldNodes.get(field.key);
    if (!node) return;
    setFieldNodeValue(node, normalizeText(state.draft[field.key]));
  });
}

function applyReadonly(state) {
  READONLY_FIELDS.forEach((field) => {
    const node = state.readonlyNodes.get(field.key);
    if (!node) return;
    node.textContent = displayValue(state.currentRecord ? state.currentRecord[field.key] : "");
  });
}

function setModeFieldAvailability(state) {
  FORM_FIELDS.forEach((field) => {
    const wrapper = state.fieldWrappers.get(field.key);
    const node = state.fieldNodes.get(field.key);
    const newModeOnly = field.key === "work_id" || field.key === "detail_id";
    if (wrapper) wrapper.hidden = newModeOnly && state.mode !== "new";
    if (!node) return;
    if ("disabled" in node) node.disabled = state.isSaving || state.isBuilding || state.isDeleting;
    if (state.mode === "new" && (field.key === "work_id" || field.key === "status")) {
      if ("disabled" in node) node.disabled = true;
    }
  });
}

function buildPayload(state) {
  if (state.mode === "bulk") {
    const setFields = {};
    EDITABLE_FIELDS.forEach((field) => {
      if (!state.bulkTouchedFields.has(field.key)) return;
      setFields[field.key] = field.key === "status"
        ? normalizeText(state.draft[field.key]).toLowerCase() || null
        : normalizeText(state.draft[field.key]) || null;
    });
    const expectedRecordHashes = {};
    state.bulkDetailUids.forEach((detailUid) => {
      expectedRecordHashes[detailUid] = state.bulkRecordHashes.get(detailUid) || "";
    });
    return {
      kind: "work_details",
      ids: state.bulkDetailUids.slice(),
      expected_record_hashes: expectedRecordHashes,
      apply_build: bulkSelectionHasPublishedRecords(state),
      set_fields: setFields
    };
  }

  const draft = state.draft;
  return {
    ...buildSaveWorkDetailPayload({ ...state, draft, applyBuild: currentDetailIsPublished(state) }),
    activity_context: buildWorkDetailActivityContext("save-work-detail", "catalogueWorkDetailSave", "#catalogueWorkDetailSave", state.currentDetailUid)
  };
}

function buildWorkDetailActivityContext(actionId, controlId, controlSelector, detailUid) {
  return buildStudioActivityContext({
    pageId: "catalogue-work-detail",
    actionId,
    route: "/studio/catalogue-work-detail/",
    controlId,
    controlSelector,
    recordIdField: "detail_uid",
    recordId: detailUid
  });
}

function currentDetailIsPublished(state) {
  return normalizeText(state.draft && state.draft.status).toLowerCase() === "published";
}

function currentDetailIsDraft(state) {
  return normalizeText(state.draft && state.draft.status).toLowerCase() === "draft";
}

function bulkSelectionHasPublishedRecords(state) {
  if (state.mode !== "bulk") return false;
  return state.bulkDetailUids.some((detailUid) => {
    const record = state.bulkRecords.get(detailUid);
    return normalizeText(record && record.status).toLowerCase() === "published";
  });
}

function bulkPublishedBuildTargets(state) {
  return state.bulkDetailUids
    .filter((detailUid) => {
      const record = state.bulkRecords.get(detailUid);
      return normalizeText(record && record.status).toLowerCase() === "published";
    })
    .map((detailUid) => {
      const record = state.bulkRecords.get(detailUid);
      return { work_id: normalizeWorkId(record && record.work_id), extra_series_ids: [] };
    })
    .filter((target) => target.work_id);
}

function updatePublishControls(state, { hasRecord, dirty, errors }) {
  const canPublish = state.mode === "single" && hasRecord && currentDetailIsDraft(state);
  const canUnpublish = state.mode === "single" && hasRecord && currentDetailIsPublished(state);
  const label = canUnpublish
    ? t(state, "unpublish_button", "Unpublish")
    : t(state, "publish_button", "Publish");
  state.publicationButton.textContent = label;
  state.publicationButton.hidden = !(canPublish || canUnpublish);
  state.publicationButton.disabled = !(canPublish || canUnpublish)
    || (canPublish && dirty)
    || (canPublish && errors.size > 0)
    || state.isSaving
    || state.isBuilding
    || state.isDeleting
    || !state.serverAvailable;
}

function applySingleSaveBuildOutcome(state, response) {
  const build = response && response.build && typeof response.build === "object" ? response.build : null;
  if (!currentDetailIsPublished(state)) {
    state.rebuildPending = false;
    return { kind: response && response.changed ? "saved_unpublished" : "unchanged", stamp: normalizeText(response && response.saved_at_utc) || utcTimestamp() };
  }
  if (!response || !response.build_requested || !build) {
    state.rebuildPending = Boolean(response && response.changed);
    return { kind: response && response.changed ? "saved" : "unchanged", stamp: normalizeText(response && response.saved_at_utc) || utcTimestamp() };
  }
  if (build.ok) {
    state.rebuildPending = false;
    return { kind: "saved_and_updated", stamp: normalizeText(build.completed_at_utc || response.saved_at_utc) || utcTimestamp() };
  }
  state.rebuildPending = true;
  return {
    kind: "saved_update_failed",
    stamp: normalizeText(response.saved_at_utc) || utcTimestamp(),
    error: normalizeText(build.error)
  };
}

function applyBulkSaveBuildOutcome(state, response, fallbackBuildTargets) {
  const build = response && response.build && typeof response.build === "object" ? response.build : null;
  if (!bulkSelectionHasPublishedRecords(state)) {
    state.rebuildPending = false;
    state.bulkBuildTargets = [];
    return { kind: response && response.changed ? "saved_unpublished" : "unchanged", stamp: normalizeText(response && response.saved_at_utc) || utcTimestamp() };
  }
  if (!response || !response.build_requested || !build) {
    state.rebuildPending = Boolean(response && response.changed);
    state.bulkBuildTargets = Array.isArray(response && response.build_targets) ? response.build_targets : fallbackBuildTargets;
    return { kind: response && response.changed ? "saved" : "unchanged", stamp: normalizeText(response && response.saved_at_utc) || utcTimestamp() };
  }
  if (build.ok) {
    state.rebuildPending = false;
    state.bulkBuildTargets = [];
    return { kind: "saved_and_updated", stamp: normalizeText(build.completed_at_utc || response.saved_at_utc) || utcTimestamp() };
  }
  state.rebuildPending = true;
  state.bulkBuildTargets = Array.isArray(build.remaining_targets) ? build.remaining_targets : fallbackBuildTargets;
  return {
    kind: "saved_update_failed",
    stamp: normalizeText(response.saved_at_utc) || utcTimestamp(),
    error: normalizeText(build.error)
  };
}

function syncUrl(detailValue, options = {}) {
  const url = new URL(window.location.href);
  if (normalizeText(options.mode).toLowerCase() === "new") {
    url.searchParams.delete("detail");
    url.searchParams.set("mode", "new");
    const workId = normalizeWorkId(options.workId);
    if (workId) url.searchParams.set("work", workId);
    else url.searchParams.delete("work");
  } else if (detailValue) {
    url.searchParams.delete("mode");
    url.searchParams.delete("work");
    url.searchParams.set("detail", detailValue);
  } else {
    url.searchParams.delete("mode");
    url.searchParams.delete("work");
    url.searchParams.delete("detail");
  }
  window.history.replaceState({}, "", url.toString());
}

function draftHasChanges(state) {
  return catalogueDraftHasChanges({
    mode: state.mode,
    fields: EDITABLE_FIELDS,
    draft: state.draft,
    baselineDraft: state.baselineDraft,
    touchedFields: state.bulkTouchedFields,
    canonicalizeScalar
  });
}

function validateDraft(state) {
  if (state.mode === "new") {
    return validateCreateWorkDetailDraft(state.draft, {
      workById: state.workSearchById,
      detailByUid: state.detailSearchByUid,
      requirePublishedParent: true,
      t: (key, fallback, tokens = null) => t(state, key, fallback, tokens)
    });
  }
  const errors = new Map();
  const rawSortOrder = normalizeText(state.draft.sort_order);
  if (rawSortOrder && !/^\d+$/.test(rawSortOrder)) {
    if (state.mode !== "bulk" || state.bulkTouchedFields.has("sort_order")) {
      errors.set("sort_order", t(state, "field_invalid_sort_order", "Use a whole number or leave blank."));
    }
  }
  if (state.mode === "bulk" && state.bulkTouchedFields.has("section_title") && !normalizeText(state.draft.section_title)) {
    errors.set("section_title", t(state, "field_required_section_title", "Enter a section title."));
  }
  if (state.mode !== "bulk" && !normalizeText(state.draft.section_title)) {
    errors.set("section_title", t(state, "field_required_section_title", "Enter a section title."));
  }
  if (state.mode === "bulk" && !state.bulkTouchedFields.has("status")) return errors;
  const status = normalizeText(state.draft.status).toLowerCase();
  if (!STATUS_OPTIONS.has(status)) {
    errors.set("status", t(state, "field_invalid_status", "Use blank, draft, or published."));
  }
  return errors;
}

function updateFieldMessages(state, errors) {
  FORM_FIELDS.forEach((field) => {
    const messageNode = state.fieldStatusNodes.get(field.key);
    if (!messageNode) return;
    let message = errors.get(field.key) || "";
    if (!message && state.mode === "bulk" && state.bulkMixedFields.has(field.key) && !state.bulkTouchedFields.has(field.key)) {
      message = t(state, "bulk_field_mixed", "Mixed values across selection. Leave untouched to preserve per-record values.");
    }
    messageNode.textContent = message;
    messageNode.hidden = !message;
  });
}

function updateSummary(state) {
  if (state.mode === "new") {
    const workId = normalizeWorkId(state.draft.work_id);
    const parentRecord = state.workSearchById.get(workId);
    const workEditorBase = getStudioRoute(state.config, "catalogue_work_editor");
    const parentHref = workId ? `${workEditorBase}?work=${encodeURIComponent(workId)}` : workEditorBase;
    state.summaryNode.innerHTML = `
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(t(state, "new_summary_parent_label", "parent work"))}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay">
          ${workId ? `<a href="${escapeHtml(parentHref)}">${escapeHtml(buildParentWorkSummary(parentRecord || { work_id: workId }))}</a>` : "—"}
        </div>
      </div>
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(t(state, "new_summary_detail_id_label", "detail id"))}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(displayValue(state.draft.detail_id))}</div>
      </div>
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(t(state, "new_summary_status_label", "status"))}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(t(state, "new_summary_status", "draft source record; not published"))}</div>
      </div>
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(t(state, "new_summary_next_label", "next step"))}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(t(state, "new_summary_next", "Create the draft, then continue editing and update the parent work when ready."))}</div>
      </div>
    `;
    state.runtimeStateNode.textContent = t(state, "new_runtime_state", "public site update is unavailable until the draft detail exists");
    setTextWithState(state.buildImpactNode, "");
    renderCurrentPreview(state);
    renderReadiness(state);
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
        <span class="tagStudioForm__label">${escapeHtml(t(state, "bulk_summary_selected", "selected details"))}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(formatSelectionList(state.bulkDetailUids) || "—")}</div>
      </div>
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(t(state, "bulk_summary_count", "record count"))}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(String(selectedCount || 0))}</div>
      </div>
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(t(state, "bulk_summary_parent_count", "parent works"))}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(formatSelectionList(parentWorkIds) || "—")}</div>
      </div>
    `;
    state.runtimeStateNode.textContent = state.rebuildPending
      ? t(state, "summary_rebuild_needed", "public update failed in this session")
      : t(state, "summary_rebuild_current", "source and parent work output are aligned in this session");
    renderCurrentPreview(state);
    renderReadiness(state);
    return;
  }

  const record = state.currentRecord;
  const publicBase = getStudioRoute(state.config, "work_details_page_base");
  const workEditorBase = getStudioRoute(state.config, "catalogue_work_editor");
  const publicHref = record ? `${publicBase}${encodeURIComponent(record.detail_uid)}/` : "";
  const workEditorHref = record ? `${workEditorBase}?work=${encodeURIComponent(record.work_id)}` : "";
  state.summaryNode.innerHTML = `
    <div class="tagStudioForm__field">
      <span class="tagStudioForm__label">${escapeHtml(t(state, "summary_public_link", "Open public detail page"))}</span>
      <div class="tagStudio__input tagStudio__input--readonlyDisplay">
        ${record ? `<a href="${escapeHtml(publicHref)}" target="_blank" rel="noopener">${escapeHtml(record.detail_uid)}</a>` : "—"}
      </div>
    </div>
    <div class="tagStudioForm__field">
      <span class="tagStudioForm__label">${escapeHtml(t(state, "summary_parent_link", "Open work editor"))}</span>
      <div class="tagStudio__input tagStudio__input--readonlyDisplay">
        ${record ? `<a href="${escapeHtml(workEditorHref)}">${escapeHtml(record.work_id)}</a>` : "—"}
      </div>
    </div>
    <div class="tagStudioForm__field">
      <span class="tagStudioForm__label">${escapeHtml(t(state, "summary_section_label", "detail section"))}</span>
      <div class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(displayValue(record && (record.section_title || record.project_subfolder)))}</div>
    </div>
  `;

  state.runtimeStateNode.textContent = state.rebuildPending
    ? t(state, "summary_rebuild_needed", "public update failed in this session")
    : t(state, "summary_rebuild_current", "source and parent work output are aligned in this session");
  renderCurrentPreview(state);
  renderReadiness(state);
}

function setLoadedRecord(state, detailUid, record, options = {}) {
  state.mode = "single";
  state.currentDetailUid = detailUid;
  state.currentWorkId = normalizeWorkId(record && record.work_id);
  state.currentRecord = record;
  state.currentLookup = options.lookup || state.currentLookup;
  state.currentRecordHash = normalizeText(options.recordHash || state.currentRecordHash);
  state.bulkDetailUids = [];
  state.bulkRecords = new Map();
  state.bulkRecordHashes = new Map();
  state.bulkMixedFields = new Set();
  state.bulkTouchedFields = new Set();
  state.bulkBuildTargets = [];
  state.baselineDraft = buildWorkDetailDraftFromRecord(record);
  state.draft = { ...state.baselineDraft };
  applyDraftToInputs(state);
  applyReadonly(state);
  syncUrl(detailUid);
  setTextWithState(state.contextNode, t(state, "context_loaded", "Editing source metadata for detail {detail_uid}.", { detail_uid: detailUid }));
  setTextWithState(state.statusNode, t(state, "save_status_loaded", "Loaded detail {detail_uid}.", { detail_uid: detailUid }));
  setTextWithState(state.warningNode, "");
  if (!options.keepResult) setTextWithState(state.resultNode, "");
  updateEditorState(state);
}

function setNewDetailMode(state, workId, options = {}) {
  const normalizedWorkId = normalizeWorkId(workId);
  state.mode = "new";
  state.currentDetailUid = "";
  state.currentWorkId = normalizedWorkId;
  state.currentRecord = null;
  state.currentLookup = null;
  state.currentRecordHash = "";
  state.bulkDetailUids = [];
  state.bulkRecords = new Map();
  state.bulkRecordHashes = new Map();
  state.bulkMixedFields = new Set();
  state.bulkTouchedFields = new Set();
  state.bulkBuildTargets = [];
  state.baselineDraft = {};
  state.draft = {};
  FORM_FIELDS.forEach((field) => {
    state.draft[field.key] = "";
  });
  state.draft.work_id = normalizedWorkId;
  state.draft.detail_id = suggestNextDetailId(state.detailSearchByUid, normalizedWorkId);
  state.draft.status = "draft";
  state.rebuildPending = false;
  state.buildPreview = null;
  applyDraftToInputs(state);
  READONLY_FIELDS.forEach((field) => {
    const node = state.readonlyNodes.get(field.key);
    if (node) node.textContent = field.key === "work_id" ? displayValue(normalizedWorkId) : "—";
  });
  state.searchNode.value = "";
  setPopupVisibility(state, false);
  syncUrl("", { mode: "new", workId: normalizedWorkId });
  if (!normalizedWorkId) {
    setTextWithState(state.contextNode, t(state, "new_context_parent_missing", "Open new detail mode from a parent work editor or provide a work id."));
  } else if (!state.workSearchById.has(normalizedWorkId)) {
    setTextWithState(state.contextNode, t(state, "new_context_parent_unknown", "Cannot create a detail because parent work {work_id} was not found.", { work_id: normalizedWorkId }), "error");
  } else if (normalizeText(state.workSearchById.get(normalizedWorkId) && state.workSearchById.get(normalizedWorkId).status).toLowerCase() !== "published") {
    setTextWithState(state.contextNode, t(state, "new_context_parent_unpublished", "Publish work {work_id} before adding work details.", { work_id: normalizedWorkId }), "error");
  } else {
    setTextWithState(state.contextNode, t(state, "new_context_loaded", "Creating a draft detail under work {work_id}.", { work_id: normalizedWorkId }));
  }
  setTextWithState(state.statusNode, "");
  setTextWithState(state.warningNode, "");
  if (!options.keepResult) setTextWithState(state.resultNode, "");
  updateEditorState(state);
}

function setLoadedBulkDetails(state, detailUids, recordsById, recordHashes, options = {}) {
  state.mode = "bulk";
  state.currentDetailUid = "";
  state.currentWorkId = "";
  state.currentRecord = null;
  state.currentLookup = null;
  state.currentRecordHash = "";
  state.bulkDetailUids = detailUids.slice();
  state.bulkRecords = new Map(recordsById);
  state.bulkRecordHashes = new Map(recordHashes);
  state.bulkBuildTargets = Array.isArray(options.buildTargets) ? options.buildTargets.slice() : [];
  const records = detailUids.map((detailUid) => recordsById.get(detailUid)).filter(Boolean);
  const bulkDraft = buildBulkDraftFromRecords(records);
  state.baselineDraft = { ...bulkDraft.draft };
  state.draft = { ...bulkDraft.draft };
  state.bulkMixedFields = bulkDraft.mixedFields;
  state.bulkTouchedFields = new Set();
  applyDraftToInputs(state);
  READONLY_FIELDS.forEach((field) => {
    const node = state.readonlyNodes.get(field.key);
    if (node) node.textContent = "—";
  });
  syncUrl(detailUids.join(","));
  setTextWithState(
    state.contextNode,
    t(state, "bulk_context_loaded", "Bulk editing {count} detail records: {detail_ids}.", {
      count: String(detailUids.length),
      detail_ids: formatSelectionList(detailUids)
    })
  );
  setTextWithState(
    state.statusNode,
    t(state, "bulk_status_loaded", "Loaded {count} detail records.", { count: String(detailUids.length) })
  );
  setTextWithState(state.warningNode, "");
  if (!options.keepResult) setTextWithState(state.resultNode, "");
  updateEditorState(state);
}

function updateEditorState(state) {
  const hasRecord = state.mode === "new" ? true : state.mode === "bulk" ? state.bulkDetailUids.length > 0 : Boolean(state.currentRecord);
  const errors = hasRecord ? validateDraft(state) : new Map();
  state.validationErrors = errors;
  updateFieldMessages(state, errors);
  setModeFieldAvailability(state);
  updateSummary(state);
  if (!hasRecord) {
    setTextWithState(state.buildImpactNode, "");
  } else if (state.mode === "bulk") {
    const previewTargets = state.rebuildPending && state.bulkBuildTargets.length
      ? state.bulkBuildTargets
      : Array.from(new Set(state.bulkDetailUids.map((detailUid) => {
        const record = state.bulkRecords.get(detailUid);
        return normalizeWorkId(record && record.work_id);
      }).filter(Boolean)));
    setTextWithState(
      state.buildImpactNode,
      t(state, "bulk_build_preview", "Build preview: {count} parent work scopes will be rebuilt.", {
        count: String(previewTargets.length)
      })
    );
  }

  const dirty = hasRecord && draftHasChanges(state);
  setTextWithState(state.warningNode, catalogueDirtyWarningText({
    dirty,
    mode: state.mode,
    message: t(state, "dirty_warning", "Unsaved source changes.")
  }));
  if (state.mode === "new" && !state.resultNode.textContent) {
    const firstError = errors.size ? Array.from(errors.values()).find(Boolean) : "";
    setTextWithState(
      state.statusNode,
      firstError || (state.serverAvailable ? "" : t(state, "create_mode_unavailable_hint", "Local catalogue server unavailable. Create is disabled.")),
      firstError ? "error" : state.serverAvailable ? "" : "warn"
    );
  } else if (!dirty && !errors.size && !state.resultNode.textContent && hasRecord) {
    setTextWithState(
      state.statusNode,
      state.mode === "bulk"
        ? t(state, "bulk_status_loaded", "Loaded {count} detail records.", { count: String(state.bulkDetailUids.length) })
        : t(state, "save_status_loaded", "Loaded detail {detail_uid}.", { detail_uid: state.currentDetailUid })
    );
  }

  state.searchNode.disabled = state.mode === "new";
  state.openButton.disabled = state.mode === "new";
  state.saveButton.textContent = state.mode === "new"
    ? t(state, "create_button", "Create")
    : t(state, "save_button", "Save");
  state.saveButton.disabled = catalogueSaveDisabled({
    hasRecord,
    isSaving: state.isSaving,
    hasErrors: errors.size > 0,
    dirty,
    serverAvailable: state.serverAvailable
  });
  state.deleteButton.disabled = catalogueDeleteDisabled({
    hasRecord: Boolean(state.currentRecord),
    mode: state.mode,
    isSaving: state.isSaving,
    isBuilding: state.isBuilding,
    isDeleting: state.isDeleting,
    serverAvailable: state.serverAvailable
  });
  updatePublishControls(state, { hasRecord, dirty, errors });
  renderReadiness(state);
  syncRouteBusyState(state);
}

function onFieldInput(state, fieldKey) {
  const node = state.fieldNodes.get(fieldKey);
  if (!node) return;
  if (state.mode === "new" && fieldKey === "status") {
    state.draft.status = "draft";
    setFieldNodeValue(node, "draft");
    updateEditorState(state);
    return;
  }
  state.draft[fieldKey] = getFieldNodeValue(node);
  if (state.mode === "bulk") {
    state.bulkTouchedFields.add(fieldKey);
  }
  updateEditorState(state);
}

function t(state, key, fallback, tokens = null) {
  return getStudioText(state.config, `catalogue_work_detail_editor.${key}`, fallback, tokens);
}

async function refreshBuildPreview(state) {
  if (state.mode === "bulk") {
    const previewTargets = state.rebuildPending && state.bulkBuildTargets.length
      ? state.bulkBuildTargets
      : bulkPublishedBuildTargets(state);
    state.buildPreview = null;
    setTextWithState(
      state.buildImpactNode,
      previewTargets.length
        ? t(state, "bulk_build_preview", "Build preview: {count} parent work scopes will be rebuilt.", {
          count: String(previewTargets.length)
        })
        : ""
    );
    renderCurrentPreview(state);
    return;
  }
  if (!state.currentWorkId || !state.serverAvailable) {
    state.buildPreview = null;
    setTextWithState(state.buildImpactNode, "");
    renderCurrentPreview(state);
    renderReadiness(state);
    return;
  }
  if (!currentDetailIsPublished(state)) {
    state.buildPreview = null;
    setTextWithState(state.buildImpactNode, t(state, "build_preview_unpublished", "Public update unavailable while the detail is not published."));
    renderCurrentPreview(state);
    renderReadiness(state);
    return;
  }
  try {
    const response = await previewCatalogueBuild({
      work_id: state.currentWorkId,
      detail_uid: state.currentDetailUid
    });
    state.buildPreview = response && response.build ? response.build : null;
    setTextWithState(state.buildImpactNode, formatCatalogueBuildPreview(state.buildPreview, {
      text: (key, fallback, tokens) => t(state, key, fallback, tokens),
      defaultTemplate: "Build preview: work {work_ids}; series {series_ids}; catalogue search {search_rebuild}."
    }));
    renderCurrentPreview(state);
    renderReadiness(state);
  } catch (error) {
    state.buildPreview = null;
    setTextWithState(
      state.buildImpactNode,
      `${t(state, "build_preview_failed", "Build preview unavailable.")} ${normalizeText(error && error.message)}`.trim(),
      "error"
    );
    renderCurrentPreview(state);
    renderReadiness(state);
  }
}

async function saveCurrentDetail(state) {
  if (state.mode === "new") {
    await createCurrentDetail(state);
    return;
  }
  if (state.mode === "bulk") {
    if (!state.bulkDetailUids.length) return;
  } else if (!state.currentRecord) {
    return;
  }
  const errors = validateDraft(state);
  updateFieldMessages(state, errors);
  if (errors.size > 0) {
    setTextWithState(state.statusNode, t(state, "save_status_validation_error", "Fix validation errors before saving."), "error");
    updateEditorState(state);
    return;
  }

  if (!draftHasChanges(state)) {
    setTextWithState(state.statusNode, t(state, "save_status_no_changes", "No changes to save."));
    setTextWithState(state.resultNode, t(state, "save_result_unchanged", "Source already matches the current form values."));
    updateEditorState(state);
    return;
  }

  state.isSaving = true;
  state.saveButton.disabled = true;
  syncRouteBusyState(state);
  setTextWithState(
    state.statusNode,
    (state.mode === "bulk" ? bulkSelectionHasPublishedRecords(state) : currentDetailIsPublished(state))
      ? t(state, "save_status_saving_and_updating", "Saving source record and updating parent work output…")
      : t(state, "save_status_saving", "Saving source record…")
  );
  setTextWithState(state.resultNode, "");

  try {
    if (state.mode === "bulk") {
      const response = await saveCatalogueBulkRecords(buildPayload(state));
      const changedRecords = Array.isArray(response && response.records) ? response.records : [];
      changedRecords.forEach((item) => {
        const detailUid = normalizeDetailUid(item && item.detail_uid);
        const record = item && item.record && typeof item.record === "object" ? item.record : null;
        if (!detailUid || !record) return;
        state.bulkRecords.set(detailUid, record);
        state.bulkRecordHashes.set(detailUid, normalizeText(item.record_hash) || "");
        state.detailSearchByUid.set(detailUid, buildDetailSearchRecord(detailUid, record));
      });
      const fallbackBuildTargets = Array.isArray(response && response.build_targets) ? response.build_targets : [];
      const outcome = applyBulkSaveBuildOutcome(state, response, fallbackBuildTargets);
      setLoadedBulkDetails(state, state.bulkDetailUids, state.bulkRecords, state.bulkRecordHashes, {
        keepResult: true,
        buildTargets: state.bulkBuildTargets
      });
      if (outcome.kind === "saved_and_updated") {
        setTextWithState(
          state.resultNode,
          t(state, "bulk_save_result_success_applied", "Saved {count} detail records and updated the parent work output at {saved_at}.", {
            count: String(response.changed_count || 0),
            saved_at: outcome.stamp
          }),
          "success"
        );
        setTextWithState(state.statusNode, t(state, "build_status_success", "Site update completed."), "success");
      } else if (outcome.kind === "saved_update_failed") {
        setTextWithState(
          state.resultNode,
          t(state, "bulk_save_result_success_partial", "Saved {count} detail records at {saved_at}, but the public update failed.", {
            count: String(response.changed_count || 0),
            saved_at: outcome.stamp
          }),
          "warn"
        );
        setTextWithState(state.statusNode, `${t(state, "build_status_failed", "Site update failed.")} ${outcome.error}`.trim(), "error");
      } else if (outcome.kind === "saved_unpublished") {
        setTextWithState(
          state.resultNode,
          response.changed
            ? t(state, "bulk_save_result_success_unpublished", "Saved {count} draft detail records at {saved_at}.", {
              count: String(response.changed_count || 0),
              saved_at: outcome.stamp
            })
            : t(state, "save_result_unchanged", "Source already matches the current form values."),
          response.changed ? "success" : ""
        );
        setTextWithState(
          state.statusNode,
          t(state, "bulk_status_loaded", "Loaded {count} detail records.", { count: String(state.bulkDetailUids.length) }),
          response.changed ? "success" : ""
        );
      } else {
        setTextWithState(
          state.resultNode,
          response.changed
            ? t(state, "bulk_save_result_success", "Saved {count} detail records at {saved_at}. Parent-work update still pending.", {
              count: String(response.changed_count || 0),
              saved_at: outcome.stamp
            })
            : t(state, "save_result_unchanged", "Source already matches the current form values."),
          response.changed ? "success" : ""
        );
        setTextWithState(
          state.statusNode,
          t(state, "bulk_status_loaded", "Loaded {count} detail records.", { count: String(state.bulkDetailUids.length) }),
          response.changed ? "success" : ""
        );
      }
      return;
    }

    const response = await saveCatalogueWorkDetail(buildPayload(state));
    const record = response && response.record && typeof response.record === "object" ? response.record : null;
    if (!record) throw new Error("save response missing record");
    state.detailSearchByUid.set(state.currentDetailUid, buildDetailSearchRecord(state.currentDetailUid, record));
    const outcome = applySingleSaveBuildOutcome(state, response);
    const recordHash = normalizeText(response.record_hash) || await computeRecordHash(record);
    setLoadedRecord(state, state.currentDetailUid, record, {
      recordHash,
      keepResult: true,
      lookup: {
        work_detail: record,
        record_hash: recordHash
      }
    });
    await refreshBuildPreview(state);
    if (outcome.kind === "saved_and_updated") {
      setTextWithState(
        state.resultNode,
        t(state, "save_result_success_applied", "Saved source changes and updated the parent work output at {saved_at}.", { saved_at: outcome.stamp }),
        "success"
      );
      setTextWithState(state.statusNode, t(state, "build_status_success", "Site update completed."), "success");
    } else if (outcome.kind === "saved_update_failed") {
      setTextWithState(
        state.resultNode,
        t(state, "save_result_success_partial", "Source changes were saved at {saved_at}, but the public update failed.", { saved_at: outcome.stamp }),
        "warn"
      );
      setTextWithState(state.statusNode, `${t(state, "build_status_failed", "Site update failed.")} ${outcome.error}`.trim(), "error");
    } else if (outcome.kind === "saved_unpublished") {
      setTextWithState(
        state.resultNode,
        t(state, "save_result_success_unpublished", "Source saved at {saved_at}.", { saved_at: outcome.stamp }),
        response.changed ? "success" : ""
      );
      setTextWithState(state.statusNode, t(state, "save_status_loaded", "Loaded detail {detail_uid}.", { detail_uid: state.currentDetailUid }), "success");
    } else {
      setTextWithState(
        state.resultNode,
        response.changed
          ? t(state, "save_result_success", "Source saved at {saved_at}. Parent-work update still pending.", { saved_at: outcome.stamp })
          : t(state, "save_result_unchanged", "Source already matches the current form values."),
        response.changed ? "success" : ""
      );
      setTextWithState(state.statusNode, t(state, "save_status_loaded", "Loaded detail {detail_uid}.", { detail_uid: state.currentDetailUid }), "success");
    }
  } catch (error) {
    const isConflict = Number(error && error.status) === 409;
    const message = isConflict
      ? t(state, "save_status_conflict", "Source record changed since this page loaded. Reload the detail before saving again.")
      : `${t(state, "save_status_failed", "Source save failed.")} ${normalizeText(error && error.message)}`.trim();
    setTextWithState(state.statusNode, message, "error");
  } finally {
    state.isSaving = false;
    updateEditorState(state);
  }
}

async function createCurrentDetail(state) {
  if (state.mode !== "new") return;
  const errors = validateDraft(state);
  updateFieldMessages(state, errors);
  if (errors.size > 0) {
    const workIdError = errors.get("work_id") || "";
    setTextWithState(
      state.statusNode,
      workIdError || t(state, "create_status_validation_error", "Fix validation errors before creating the draft detail."),
      "error"
    );
    updateEditorState(state);
    return;
  }

  state.isSaving = true;
  updateEditorState(state);
  setTextWithState(state.statusNode, t(state, "create_status_saving", "Creating draft detail..."));
  setTextWithState(state.resultNode, "");

  try {
    const requestedDetailUid = normalizeDetailUid(`${normalizeWorkId(state.draft.work_id)}-${normalizeDetailId(state.draft.detail_id)}`);
    const response = await createCatalogueWorkDetail({
      ...buildCreateWorkDetailPayload(state.draft),
      activity_context: buildWorkDetailActivityContext("create-work-detail", "catalogueWorkDetailSave", "#catalogueWorkDetailSave", requestedDetailUid)
    });
    const detailUid = normalizeDetailUid(response && response.detail_uid);
    const record = response && response.record && typeof response.record === "object" ? response.record : null;
    if (!detailUid) {
      throw new Error("create response missing detail id");
    }
    if (record) {
      state.detailSearchByUid.set(detailUid, buildDetailSearchRecord(detailUid, record));
    }
    state.isSaving = false;
    syncRouteBusyState(state);
    await openDetailByUid(state, detailUid);
    setTextWithState(state.resultNode, t(state, "create_result_success", "Created draft detail {detail_uid}. Opening edit mode...", { detail_uid: detailUid }), "success");
    setTextWithState(state.statusNode, t(state, "create_status_success", "Created draft detail {detail_uid}.", { detail_uid: detailUid }), "success");
  } catch (error) {
    const message = `${t(state, "create_status_failed", "Draft detail create failed.")} ${normalizeText(error && error.message)}`.trim();
    setTextWithState(state.statusNode, message, "error");
    setTextWithState(state.resultNode, message, "error");
    state.isSaving = false;
    updateEditorState(state);
  }
}

async function buildCurrentDetail(state) {
  if (state.mode === "bulk") {
    if (!state.bulkDetailUids.length || !state.serverAvailable) return;
  } else if (!state.currentRecord || !state.currentWorkId || !state.serverAvailable) {
    return;
  }
  state.isBuilding = true;
  updateEditorState(state);
  setTextWithState(state.statusNode, t(state, "build_status_running", "Updating site…"));
  setTextWithState(state.resultNode, "");
  try {
    if (state.mode === "bulk") {
      const buildTargets = state.rebuildPending && state.bulkBuildTargets.length
        ? state.bulkBuildTargets
        : Array.from(new Set(state.bulkDetailUids.map((detailUid) => {
          const record = state.bulkRecords.get(detailUid);
          return normalizeWorkId(record && record.work_id);
        }).filter(Boolean))).map((workId) => ({ work_id: workId, extra_series_ids: [] }));
      for (const target of buildTargets) {
        await applyCatalogueBuild({
          work_id: target.work_id,
          extra_series_ids: Array.isArray(target.extra_series_ids) ? target.extra_series_ids : []
        });
      }
      state.rebuildPending = false;
      state.bulkBuildTargets = [];
      await refreshBuildPreview(state);
      const completedAt = utcTimestamp();
      setTextWithState(
        state.resultNode,
        t(state, "bulk_build_result_success", "Updated {count} parent work scopes at {completed_at}. Studio Activity updated.", {
          count: String(buildTargets.length),
          completed_at: completedAt
        }),
        "success"
      );
      setTextWithState(state.statusNode, t(state, "build_status_success", "Site update completed."), "success");
      return;
    }

    const response = await applyCatalogueBuild({
      work_id: state.currentWorkId,
      detail_uid: state.currentDetailUid
    });
    state.rebuildPending = false;
    await refreshBuildPreview(state);
    const completedAt = normalizeText(response.completed_at_utc || utcTimestamp());
    setTextWithState(
      state.resultNode,
      t(state, "build_result_success", "Parent work output updated at {completed_at}. Studio Activity updated.", { completed_at: completedAt }),
      "success"
    );
    setTextWithState(state.statusNode, t(state, "build_status_success", "Site update completed."), "success");
  } catch (error) {
    setTextWithState(
      state.statusNode,
      `${t(state, "build_status_failed", "Site update failed.")} ${normalizeText(error && error.message)}`.trim(),
      "error"
    );
  } finally {
    state.isBuilding = false;
    updateEditorState(state);
  }
}

async function applyPublicationChange(state) {
  if (state.mode !== "single" || !state.currentRecord || !state.currentDetailUid || !state.serverAvailable) return;
  const action = currentDetailIsPublished(state) ? "unpublish" : currentDetailIsDraft(state) ? "publish" : "";
  if (!action) {
    setTextWithState(state.statusNode, t(state, "publication_status_invalid", "Publication is available only for draft or published details."), "error");
    return;
  }
  if (action === "publish" && draftHasChanges(state)) {
    setTextWithState(state.statusNode, t(state, "publication_save_first", "Save source changes before publishing."), "error");
    return;
  }

  if (action === "publish") {
    const errors = validateDraft(state);
    updateFieldMessages(state, errors);
    if (errors.size > 0) {
      setTextWithState(state.statusNode, t(state, "publication_status_validation_error", "Fix validation errors before changing publication state."), "error");
      updateEditorState(state);
      return;
    }
  }

  state.isBuilding = true;
  updateEditorState(state);
  setTextWithState(
    state.statusNode,
    action === "publish"
      ? t(state, "publication_preview_publish_running", "Preparing publish preview…")
      : t(state, "publication_preview_unpublish_running", "Preparing unpublish preview…")
  );
  setTextWithState(state.resultNode, "");

  try {
    const request = {
      kind: "work_detail",
      action,
      detail_uid: state.currentDetailUid,
      expected_record_hash: state.currentRecordHash,
      activity_context: buildWorkDetailActivityContext(`${action}-work-detail`, "catalogueWorkDetailPublication", "#catalogueWorkDetailPublication", state.currentDetailUid)
    };
    const previewResponse = await previewCataloguePublication(request);
    const preview = previewResponse && previewResponse.preview ? previewResponse.preview : null;
    const blockers = Array.isArray(preview && preview.blockers) ? preview.blockers : [];
    if ((preview && preview.blocked) || blockers.length) {
      const message = blockers[0] || t(state, "publication_status_blocked", "Publication change is blocked.");
      setTextWithState(state.statusNode, message, "error");
      return;
    }

    if (action === "unpublish") {
      const summary = formatCataloguePublicationPreview(preview, {
        text: (key, fallback, tokens) => t(state, key, fallback, tokens),
        defaultText: "Unpublish this detail?",
        includeDirtyNote: draftHasChanges(state)
      });
      if (!window.confirm(summary)) {
        setTextWithState(state.statusNode, t(state, "publication_status_cancelled", "Publication change cancelled."));
        return;
      }
    }

    setTextWithState(
      state.statusNode,
      action === "publish"
        ? t(state, "publication_publish_running", "Publishing detail…")
        : t(state, "publication_unpublish_running", "Unpublishing detail…")
    );
    const response = await applyCataloguePublication(request);
    const record = response && response.record && typeof response.record === "object" ? response.record : null;
    if (!record) throw new Error("publication response missing record");

    const detailUid = state.currentDetailUid;
    const recordHash = normalizeText(response.record_hash) || await computeRecordHash(record);
    state.detailSearchByUid.set(detailUid, buildDetailSearchRecord(detailUid, record));
    state.rebuildPending = response.status === "public_update_failed";
    const lookup = await loadDetailLookupRecord(state, detailUid).catch(() => null);
    setLoadedRecord(state, detailUid, record, {
      recordHash,
      keepResult: true,
      lookup: lookup || {
        work_detail: record,
        record_hash: recordHash
      }
    });
    await refreshBuildPreview(state);

    if (response.status === "public_update_failed") {
      const error = normalizeText(response.public_update && response.public_update.error);
      setTextWithState(state.statusNode, `${t(state, "publication_status_public_failed", "Publication state changed, but the public update failed.")} ${error}`.trim(), "error");
      setTextWithState(state.resultNode, t(state, "publication_result_public_failed", "Source status changed, but public artifacts did not finish updating."), "warn");
      return;
    }

    if (action === "publish") {
      setTextWithState(state.statusNode, t(state, "publication_status_published", "Detail published."), "success");
      setTextWithState(state.resultNode, t(state, "publication_result_published", "Detail is published and parent work output has been updated."), "success");
    } else {
      setTextWithState(state.statusNode, t(state, "publication_status_unpublished", "Detail unpublished."), "success");
      setTextWithState(state.resultNode, t(state, "publication_result_unpublished", "Detail is draft again and public output has been cleaned up."), "success");
    }
  } catch (error) {
    const message = Number(error && error.status) === 409
      ? t(state, "publication_status_conflict", "Source record changed since this page loaded. Reload before changing publication state.")
      : `${t(state, "publication_status_failed", "Publication change failed.")} ${normalizeText(error && error.message)}`.trim();
    setTextWithState(state.statusNode, message, "error");
  } finally {
    state.isBuilding = false;
    updateEditorState(state);
  }
}

function countMediaItems(media, group) {
  const values = media && media[group] && typeof media[group] === "object" ? media[group] : {};
  return Object.values(values).reduce((total, items) => total + (Array.isArray(items) ? items.length : 0), 0);
}

async function refreshDetailMedia(state) {
  if (!state.currentRecord || !state.currentWorkId || !state.currentDetailUid || !state.serverAvailable || draftHasChanges(state)) return;
  state.isBuilding = true;
  updateEditorState(state);
  setTextWithState(state.statusNode, t(state, "media_refresh_status_running", "Refreshing media…"));
  setTextWithState(state.resultNode, "");
  try {
    const response = await applyCatalogueBuild({
      work_id: state.currentWorkId,
      detail_uid: state.currentDetailUid,
      media_only: true,
      force: true
    });
    const blockedCount = countMediaItems(response && response.media, "blocked");
    await refreshBuildPreview(state);
    if (blockedCount > 0) {
      setTextWithState(state.statusNode, t(state, "media_refresh_status_blocked", "Media refresh blocked."), "error");
      setTextWithState(state.resultNode, normalizeText(response && response.media && response.media.summary), "error");
      return;
    }
    setTextWithState(state.statusNode, t(state, "media_refresh_status_success", "Media refresh completed."), "success");
    setTextWithState(state.resultNode, t(state, "media_refresh_result_success", "Thumbnails updated; primary variants staged for publishing."), "success");
  } catch (error) {
    setTextWithState(
      state.statusNode,
      `${t(state, "media_refresh_status_failed", "Media refresh failed.")} ${normalizeText(error && error.message)}`.trim(),
      "error"
    );
  } finally {
    state.isBuilding = false;
    updateEditorState(state);
  }
}

async function deleteCurrentDetail(state) {
  if (!state.currentRecord || state.mode === "bulk" || !state.serverAvailable) return;
  state.isDeleting = true;
  updateEditorState(state);
  setTextWithState(state.statusNode, t(state, "delete_status_running", "Preparing delete preview…"));
  setTextWithState(state.resultNode, "");
  try {
    const request = {
      kind: "work_detail",
      detail_uid: state.currentDetailUid,
      expected_record_hash: state.currentRecordHash,
      activity_context: buildWorkDetailActivityContext("delete-work-detail", "catalogueWorkDetailDelete", "#catalogueWorkDetailDelete", state.currentDetailUid)
    };
    const previewResponse = await previewCatalogueDelete(request);
    const preview = previewResponse && previewResponse.preview ? previewResponse.preview : null;
    const blockers = Array.isArray(preview && preview.blockers) ? preview.blockers : [];
    const validationErrors = Array.isArray(preview && preview.validation_errors) ? preview.validation_errors : [];
    if ((preview && preview.blocked) || blockers.length || validationErrors.length) {
      const message = blockers[0] || validationErrors[0] || t(state, "delete_status_blocked", "Delete is blocked.");
      setTextWithState(state.statusNode, message, "error");
      state.isDeleting = false;
      updateEditorState(state);
      return;
    }
    const summary = formatCatalogueDeletePreview(preview, {
      text: (key, fallback, tokens) => t(state, key, fallback, tokens),
      defaultText: "Delete this source record?"
    });
    if (!window.confirm(summary)) {
      setTextWithState(state.statusNode, t(state, "delete_status_cancelled", "Delete cancelled."));
      state.isDeleting = false;
      updateEditorState(state);
      return;
    }
    setTextWithState(state.statusNode, t(state, "delete_status_running", "Deleting source record…"));
    await applyCatalogueDelete(request);
    const route = getStudioRoute(state.config, "catalogue_work_editor");
    window.location.assign(`${route}?work=${encodeURIComponent(state.currentWorkId)}`);
  } catch (error) {
    const message = Number(error && error.status) === 409
      ? t(state, "delete_status_conflict", "Source record changed since this page loaded. Reload before deleting again.")
      : `${t(state, "delete_status_failed", "Source delete failed.")} ${normalizeText(error && error.message)}`.trim();
    setTextWithState(state.statusNode, message, "error");
    state.isDeleting = false;
    updateEditorState(state);
  }
}

async function openDetailSelection(state, requestedValue) {
  let detailUids;
  try {
    detailUids = parseDetailSelection(requestedValue);
  } catch (error) {
    renderSearchMatches(state, [], normalizeText(error && error.message) || t(state, "search_empty", "Enter a detail id."));
    return;
  }

  if (!detailUids.length) {
    renderSearchMatches(state, [], t(state, "search_empty", "Enter a detail id."));
    return;
  }
  if (detailUids.length === 1) {
    await openDetailByUid(state, detailUids[0]);
    return;
  }

  const unknown = detailUids.find((detailUid) => !state.detailSearchByUid.has(detailUid));
  if (unknown) {
    renderSearchMatches(state, [], t(state, "unknown_detail_error", "Unknown detail id: {detail_uid}.", { detail_uid: unknown }));
    return;
  }

  state.searchNode.value = detailUids.join(", ");
  setPopupVisibility(state, false);
  state.rebuildPending = false;
  const lookups = await Promise.all(detailUids.map((detailUid) => loadDetailLookupRecord(state, detailUid)));
  const recordsById = new Map();
  const recordHashes = new Map();
  for (let index = 0; index < detailUids.length; index += 1) {
    const detailUid = detailUids[index];
    const lookup = lookups[index];
    const record = lookup && lookup.work_detail && typeof lookup.work_detail === "object" ? lookup.work_detail : null;
    if (!record) {
      throw new Error(`detail lookup missing record for ${detailUid}`);
    }
    recordsById.set(detailUid, record);
    recordHashes.set(detailUid, normalizeText(lookup.record_hash) || await computeRecordHash(record));
  }
  setLoadedBulkDetails(state, detailUids, recordsById, recordHashes);
  await refreshBuildPreview(state);
}

async function openDetailByUid(state, requestedDetailUid) {
  const detailUid = normalizeDetailUid(requestedDetailUid);
  if (!detailUid) {
    renderSearchMatches(state, [], t(state, "search_empty", "Enter a detail id."));
    return;
  }

  const searchRecord = state.detailSearchByUid.get(detailUid);
  if (!searchRecord) {
    const matches = getSearchMatches(state, requestedDetailUid);
    if (matches.length) renderSearchMatches(state, matches);
    else renderSearchMatches(state, [], t(state, "unknown_detail_error", "Unknown detail id: {detail_uid}.", { detail_uid: detailUid }));
    return;
  }

  state.searchNode.value = detailUid;
  setPopupVisibility(state, false);
  state.rebuildPending = false;
  const lookup = await loadDetailLookupRecord(state, detailUid);
  const record = lookup && lookup.work_detail && typeof lookup.work_detail === "object" ? lookup.work_detail : null;
  if (!record) {
    throw new Error(`detail lookup missing record for ${detailUid}`);
  }
  setLoadedRecord(state, detailUid, record, {
    recordHash: normalizeText(lookup.record_hash) || await computeRecordHash(record),
    lookup
  });
  await refreshBuildPreview(state);
}

async function init() {
  const root = document.getElementById("catalogueWorkDetailRoot");
  const loadingNode = document.getElementById("catalogueWorkDetailLoading");
  const emptyNode = document.getElementById("catalogueWorkDetailEmpty");
  const fieldsNode = document.getElementById("catalogueWorkDetailFields");
  const readonlyNode = document.getElementById("catalogueWorkDetailReadonly");
  const previewNode = document.getElementById("catalogueWorkDetailPreview");
  const summaryNode = document.getElementById("catalogueWorkDetailSummary");
  const readinessNode = document.getElementById("catalogueWorkDetailReadiness");
  const runtimeStateNode = document.getElementById("catalogueWorkDetailRuntimeState");
  const buildImpactNode = document.getElementById("catalogueWorkDetailBuildImpact");
  const searchNode = document.getElementById("catalogueWorkDetailSearchGlobal");
  const popupNode = document.getElementById("catalogueWorkDetailPopup");
  const popupListNode = document.getElementById("catalogueWorkDetailPopupList");
  const openButton = document.getElementById("catalogueWorkDetailOpen");
  const saveButton = document.getElementById("catalogueWorkDetailSave");
  const publicationButton = document.getElementById("catalogueWorkDetailPublication");
  const deleteButton = document.getElementById("catalogueWorkDetailDelete");
  const saveModeNode = document.getElementById("catalogueWorkDetailSaveMode");
  const contextNode = document.getElementById("catalogueWorkDetailContext");
  const statusNode = document.getElementById("catalogueWorkDetailStatus");
  const warningNode = document.getElementById("catalogueWorkDetailWarning");
  const resultNode = document.getElementById("catalogueWorkDetailResult");
  if (!root || !loadingNode || !emptyNode || !fieldsNode || !readonlyNode || !previewNode || !summaryNode || !readinessNode || !runtimeStateNode || !buildImpactNode || !searchNode || !popupNode || !popupListNode || !openButton || !saveButton || !publicationButton || !deleteButton || !saveModeNode || !contextNode || !statusNode || !warningNode || !resultNode) {
    return;
  }

  const state = {
    config: null,
    mode: "single",
    detailSearchByUid: new Map(),
    workSearchById: new Map(),
    currentLookup: null,
    currentDetailUid: "",
    currentWorkId: "",
    currentRecord: null,
    currentRecordHash: "",
    bulkDetailUids: [],
    bulkRecords: new Map(),
    bulkRecordHashes: new Map(),
    bulkMixedFields: new Set(),
    bulkTouchedFields: new Set(),
    bulkBuildTargets: [],
    baselineDraft: null,
    draft: {},
    validationErrors: new Map(),
    mediaConfig: loadCatalogueMediaConfig(root),
    rebuildPending: false,
    buildPreview: null,
    isSaving: false,
    isBuilding: false,
    isDeleting: false,
    serverAvailable: false,
    root,
    fieldWrappers: new Map(),
    fieldNodes: new Map(),
    fieldStatusNodes: new Map(),
    readonlyNodes: new Map(),
    searchNode,
    popupNode,
    popupListNode,
    openButton,
    saveButton,
    publicationButton,
    deleteButton,
    saveModeNode,
    contextNode,
    statusNode,
    warningNode,
    resultNode,
    previewNode,
    summaryNode,
    readinessNode,
    runtimeStateNode,
    buildImpactNode
  };
  initializeStudioRouteState(root, { route: "catalogue-work-detail" });

  FORM_FIELDS.forEach((field) => renderField(field, fieldsNode, state));
  READONLY_FIELDS.forEach((field) => renderReadonlyField(field, readonlyNode, state));

  try {
    const config = await loadStudioConfigWithText("catalogue_work_detail_editor");
    state.config = config;
    applyFieldLabels(state);
    searchNode.placeholder = t(state, "search_placeholder", "find detail id(s): 00001-001, 00001-003-005");
    openButton.textContent = t(state, "open_button", "Open");
    saveButton.textContent = t(state, "save_button", "Save");
    publicationButton.textContent = t(state, "publish_button", "Publish");
    deleteButton.textContent = t(state, "delete_button", "Delete");

    const serverAvailable = await probeCatalogueHealth();
    state.serverAvailable = Boolean(serverAvailable);
    saveModeNode.textContent = buildSaveModeText(config, state.serverAvailable ? "post" : "offline", (cfg, key, fallback, tokens) => getStudioText(cfg, `catalogue_work_detail_editor.${key}`, fallback, tokens));
    if (!state.serverAvailable) {
      setTextWithState(statusNode, t(state, "save_mode_unavailable_hint", "Local catalogue server unavailable. Save is disabled."), "warn");
      updateEditorState(state);
      root.hidden = false;
      loadingNode.hidden = true;
      markRouteReady(state, true);
      return;
    }

    const serverReadOptions = { cache: "no-store", catalogueServerAvailable: state.serverAvailable };
    const [detailsPayload, worksPayload] = await Promise.all([
      loadStudioLookupJson(config, "catalogue_lookup_work_detail_search", serverReadOptions),
      loadStudioLookupJson(config, "catalogue_lookup_work_search", serverReadOptions)
    ]);

    const detailItems = Array.isArray(detailsPayload && detailsPayload.items) ? detailsPayload.items : [];
    detailItems.forEach((record) => {
      if (!record || typeof record !== "object") return;
      const detailUid = normalizeText(record.detail_uid);
      if (!detailUid) return;
      state.detailSearchByUid.set(detailUid, record);
    });
    const workItems = Array.isArray(worksPayload && worksPayload.items) ? worksPayload.items : [];
    workItems.forEach((record) => {
      if (!record || typeof record !== "object") return;
      const workId = normalizeWorkId(record.work_id);
      if (!workId) return;
      state.workSearchById.set(workId, record);
    });
    searchNode.addEventListener("input", () => {
      const query = searchNode.value;
      if (!normalizeText(query)) {
        renderSearchMatches(state, [], "");
        return;
      }
      if (isDetailBulkQuery(query)) {
        renderSearchMatches(state, [], "");
        return;
      }
      const matches = getSearchMatches(state, query);
      if (!matches.length) {
        renderSearchMatches(state, [], t(state, "search_no_match", "No matching detail ids."));
        return;
      }
      renderSearchMatches(state, matches);
    });

    searchNode.addEventListener("keydown", (event) => {
      if (event.key !== "Enter") return;
      event.preventDefault();
      openDetailSelection(state, searchNode.value).catch((error) => {
        console.warn("catalogue_work_detail_editor: failed to open requested detail selection", error);
      });
    });

    popupListNode.addEventListener("click", (event) => {
      const button = event.target && event.target.closest ? event.target.closest("[data-detail-uid]") : null;
      if (!button) return;
      openDetailByUid(state, button.getAttribute("data-detail-uid")).catch((error) => {
        console.warn("catalogue_work_detail_editor: failed to open selected detail", error);
      });
    });

    openButton.addEventListener("click", () => {
      openDetailSelection(state, searchNode.value).catch((error) => {
        console.warn("catalogue_work_detail_editor: failed to open requested detail selection", error);
      });
    });
    readinessNode.addEventListener("click", (event) => {
      const button = event.target && event.target.closest ? event.target.closest("[data-media-refresh]") : null;
      if (!button) return;
      refreshDetailMedia(state).catch((error) => {
        console.warn("catalogue_work_detail_editor: unexpected media refresh failure", error);
      });
    });
    saveButton.addEventListener("click", () => saveCurrentDetail(state).catch((error) => {
      console.warn("catalogue_work_detail_editor: unexpected save failure", error);
    }));
    publicationButton.addEventListener("click", () => applyPublicationChange(state).catch((error) => {
      console.warn("catalogue_work_detail_editor: unexpected publication failure", error);
    }));
    deleteButton.addEventListener("click", () => deleteCurrentDetail(state).catch((error) => {
      console.warn("catalogue_work_detail_editor: unexpected delete failure", error);
    }));

    document.addEventListener("click", (event) => {
      if (event.target === searchNode || popupNode.contains(event.target)) return;
      setPopupVisibility(state, false);
    });

    const params = new URLSearchParams(window.location.search);
    const requestedMode = normalizeText(params.get("mode")).toLowerCase();
    const requestedWorkValue = normalizeText(params.get("work"));
    const requestedDetailValue = normalizeText(params.get("detail"));
    if (requestedMode === "new") {
      setNewDetailMode(state, requestedWorkValue);
    } else if (requestedDetailValue) {
      await openDetailSelection(state, requestedDetailValue).catch((error) => {
        console.warn("catalogue_work_detail_editor: failed to open requested detail selection", error);
        setTextWithState(
          state.statusNode,
          `${t(state, "load_requested_detail_failed", "Failed to load the requested detail.")} ${normalizeText(error && error.message)}`.trim(),
          "error"
        );
      });
    } else {
      setTextWithState(contextNode, t(state, "missing_detail_param", "Search for a work detail by detail id."));
      updateSummary(state);
      updateEditorState(state);
    }

    root.hidden = false;
    loadingNode.hidden = true;
    markRouteReady(state, true);
  } catch (error) {
    console.warn("catalogue_work_detail_editor: init failed", error);
    try {
      const config = await loadStudioConfigWithText("catalogue_work_detail_editor");
      loadingNode.textContent = getStudioText(config, "catalogue_work_detail_editor.load_failed_error", "Failed to load catalogue source data for the work detail editor.");
    } catch (_configError) {
      loadingNode.textContent = "Failed to load catalogue source data for the work detail editor.";
    }
  }
}

init();
