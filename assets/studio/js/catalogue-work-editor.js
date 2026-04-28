import {
  getStudioRoute,
  getStudioText,
  loadStudioConfig
} from "./studio-config.js";
import {
  loadStudioLookupJson,
  loadStudioLookupRecordJson
} from "./studio-data.js";
import {
  CATALOGUE_WRITE_ENDPOINTS,
  postJson,
  probeCatalogueHealth
} from "./studio-transport.js";
import {
  buildSaveModeText,
  utcTimestamp
} from "./tag-studio-save.js";
import {
  bindPreviewImages,
  buildDetailThumbPreview,
  buildWorkPrimaryPreview,
  loadCatalogueMediaConfig
} from "./catalogue-media-preview.js";
import {
  createStudioModalHost,
  openConfirmModal,
  renderStudioModalFrame
} from "./studio-modal.js";
import {
  WORK_DATE_RE as DATE_RE,
  WORK_DIMENSION_FIELD_KEYS,
  WORK_EDITABLE_FIELDS as EDITABLE_FIELDS,
  WORK_READONLY_FIELDS as READONLY_FIELDS,
  WORK_SERIES_ID_RE as SERIES_ID_RE,
  WORK_STATUS_OPTIONS as STATUS_OPTIONS,
  buildCreateWorkPayload,
  buildWorkDraftFromRecord,
  buildWorkRecordFromDraft,
  canonicalizeWorkScalar as canonicalizeScalar,
  cloneEmbeddedEntries,
  dedupeSeriesIds,
  embeddedEntriesEqual,
  normalizeEmbeddedEntries,
  normalizeSeriesId,
  normalizeText,
  normalizeWorkId,
  parseSeriesIds,
  suggestNextWorkId
} from "./catalogue-work-fields.js";

const SEARCH_LIMIT = 20;
const DETAIL_LIST_LIMIT = 10;
const BULK_PREVIEW_LIMIT = 12;
const DOWNLOAD_FIELDS = ["filename", "label"];
const LINK_FIELDS = ["url", "label"];
const REQUIRED_WORK_FIELDS = ["title", "year", "year_display", "series_ids"];

function escapeHtml(value) {
  return normalizeText(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function toneForReadinessStatus(status) {
  if (status === "ready") return "ready";
  if (status === "unavailable") return "error";
  return "warning";
}

function normalizeDetailId(value) {
  const digits = normalizeText(value).replace(/\D/g, "");
  if (!digits) return "";
  return digits.padStart(3, "0");
}

function normalizeDetailUid(value, currentWorkId = "") {
  const text = normalizeText(value);
  if (!text) return "";
  const match = text.match(/^(\d{5})-(\d{3})$/);
  if (match) return `${match[1]}-${match[2]}`;
  const digits = text.replace(/\D/g, "");
  if (digits.length === 8) {
    return `${digits.slice(0, 5)}-${digits.slice(5)}`;
  }
  if (currentWorkId && digits && digits.length <= 3) {
    return `${normalizeWorkId(currentWorkId)}-${digits.padStart(3, "0")}`;
  }
  return "";
}

async function computeRecordHash(record) {
  if (!globalThis.crypto || !crypto.subtle) return "";
  const json = stableStringify(record);
  const bytes = new TextEncoder().encode(json);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest)).map((value) => value.toString(16).padStart(2, "0")).join("");
}

function stableStringify(value) {
  if (Array.isArray(value)) {
    return `[${value.map((item) => stableStringify(item)).join(",")}]`;
  }
  if (value && typeof value === "object") {
    const keys = Object.keys(value).sort();
    return `{${keys.map((key) => `${JSON.stringify(key)}:${stableStringify(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

function displayValue(value) {
  const text = normalizeText(value);
  return text || "—";
}

function getReadinessItems(state) {
  const readiness = state.buildPreview && typeof state.buildPreview === "object" ? state.buildPreview.readiness : null;
  return readiness && Array.isArray(readiness.items) ? readiness.items : [];
}

function getReadinessItem(state, key) {
  return getReadinessItems(state).find((item) => normalizeText(item && item.key) === key) || null;
}

function previewFallback(state, item, missingGeneratedText, missingSourceText) {
  const status = normalizeText(item && item.status);
  if (status === "ready" || status === "pending_generation") {
    return {
      fallbackState: "missing-generated",
      fallbackText: status === "pending_generation"
        ? (normalizeText(item && item.summary) || missingGeneratedText)
        : missingGeneratedText
    };
  }
  if (status === "missing_file") {
    return {
      fallbackState: "missing-source",
      fallbackText: missingSourceText
    };
  }
  if (status === "unavailable") {
    return {
      fallbackState: "unavailable",
      fallbackText: normalizeText(item && item.summary) || t(state, "preview_unavailable", "Preview unavailable.")
    };
  }
  return {
    fallbackState: "not-configured",
    fallbackText: normalizeText(item && item.summary) || t(state, "preview_not_configured", "Preview not configured.")
  };
}

function renderCurrentPreview(state) {
  if (!state.previewNode) return;
  if (state.mode === "bulk" || !state.currentRecord) {
    state.previewNode.innerHTML = "";
    return;
  }
  const record = state.currentRecord;
  const mediaItem = getReadinessItem(state, "work_media");
  const preview = buildWorkPrimaryPreview(state.mediaConfig, record.work_id);
  const fallback = previewFallback(
    state,
    mediaItem,
    t(state, "preview_generated_missing", "Generated preview unavailable. Source media exists."),
    t(state, "preview_source_missing", "Source media missing.")
  );
  const caption = buildRecordSummary(record);
  const canShowGenerated = !mediaItem || normalizeText(mediaItem.status) === "ready";
  const previewState = preview.src && canShowGenerated ? "loading" : fallback.fallbackState;
  const publicHref = `${getStudioRoute(state.config, "works_page_base")}${encodeURIComponent(record.work_id)}/`;
  const isPublished = normalizeText(record && record.status).toLowerCase() === "published";
  const previewHref = isPublished ? publicHref : normalizeText(preview.fullSrc);
  const previewTarget = isPublished ? "" : "_blank";
  const previewRel = isPublished ? "" : "noopener";
  const frameHtml = `
    <div class="catalogueRecordPreview__frame" data-preview-state="${escapeHtml(previewState)}" data-preview-fallback="${escapeHtml(fallback.fallbackState)}">
      ${preview.src && canShowGenerated ? `<img class="catalogueRecordPreview__media" data-preview-image src="${escapeHtml(preview.src)}" srcset="${escapeHtml(preview.srcset || "")}" sizes="180px" width="${escapeHtml(String(preview.width || 180))}" height="${escapeHtml(String(preview.height || 180))}" alt="${escapeHtml(caption)}">` : ""}
      <div class="catalogueRecordPreview__placeholder">${escapeHtml(fallback.fallbackText)}</div>
    </div>
  `;
  state.previewNode.innerHTML = `
    <figure class="catalogueRecordPreview">
      ${previewHref ? `<a class="catalogueRecordPreview__link" href="${escapeHtml(previewHref)}"${previewTarget ? ` target="${escapeHtml(previewTarget)}"` : ""}${previewRel ? ` rel="${escapeHtml(previewRel)}"` : ""}>${frameHtml}</a>` : frameHtml}
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
  const items = getReadinessItems(state);
  if (!items.length) {
    state.readinessNode.innerHTML = "";
    return;
  }

  const actionDisabled = !state.serverAvailable || state.isSaving || state.isBuilding || draftHasChanges(state);
  state.readinessNode.innerHTML = items.map((item) => {
    const itemStatus = normalizeText(item && item.status);
    const tone = toneForReadinessStatus(itemStatus);
    const title = normalizeText(item && item.title) || "readiness";
    const summary = normalizeText(item && item.summary) || "—";
    const sourcePath = normalizeText(item && item.source_path);
    const nextStep = normalizeText(item && item.next_step);
    const proseAction = normalizeText(item && item.key) === "work_prose";
    const mediaAction = normalizeText(item && item.key) === "work_media";
    const proseActionDisabled = actionDisabled || (proseAction && itemStatus !== "ready");
    const mediaActionDisabled = actionDisabled || !Boolean(item && item.exists);
    const disabledNote = proseAction && actionDisabled
      ? (draftHasChanges(state)
        ? t(state, "readiness_save_first", "Save source changes before importing prose.")
        : t(state, "readiness_action_busy", "Wait for the current save or rebuild to finish."))
      : mediaAction && actionDisabled
        ? (draftHasChanges(state)
          ? t(state, "media_refresh_save_first", "Save source changes before refreshing media.")
          : t(state, "readiness_action_busy", "Wait for the current save or rebuild to finish."))
      : "";
    const proseActionLabel = t(state, "prose_import_button", "Import staged prose");
    const mediaActionLabel = t(state, "media_refresh_button", "Refresh media");
    return `
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(title)}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay catalogueReadiness__body">
          <span class="catalogueReadiness__summary" data-tone="${escapeHtml(tone)}">${escapeHtml(summary)}</span>
          ${sourcePath ? `<span class="tagStudioForm__meta catalogueReadiness__path">${escapeHtml(sourcePath)}</span>` : ""}
          ${nextStep ? `<span class="tagStudioForm__meta">${escapeHtml(nextStep)}</span>` : ""}
          ${proseAction ? `<div class="catalogueReadiness__actions"><button type="button" class="tagStudio__button" data-prose-import="work" ${proseActionDisabled ? "disabled" : ""}>${escapeHtml(proseActionLabel)}</button></div>` : ""}
          ${mediaAction ? `<div class="catalogueReadiness__actions"><button type="button" class="tagStudio__button" data-media-refresh="work" ${mediaActionDisabled ? "disabled" : ""}>${escapeHtml(mediaActionLabel)}</button></div>` : ""}
          ${disabledNote ? `<span class="tagStudioForm__meta">${escapeHtml(disabledNote)}</span>` : ""}
        </div>
      </div>
    `;
  }).join("");
}

function buildRecordSummary(record) {
  const title = normalizeText(record && record.title);
  const yearDisplay = normalizeText(record && record.year_display);
  if (title && yearDisplay) return `${title} · ${yearDisplay}`;
  return title || yearDisplay || "—";
}

function buildSearchToken(value) {
  const text = normalizeText(value);
  if (!text) return "";
  const digits = text.replace(/\D/g, "");
  return digits || text.toLowerCase();
}

function compareDetailUid(a, b) {
  return normalizeText(a).localeCompare(normalizeText(b), undefined, { numeric: true, sensitivity: "base" });
}

function parseWorkSelection(rawValue) {
  const text = normalizeText(rawValue);
  if (!text) return [];
  const tokens = text.split(",").map((item) => normalizeText(item)).filter(Boolean);
  const workIds = [];
  const seen = new Set();
  tokens.forEach((token) => {
    const rangeMatch = token.match(/^(\d{1,5})\s*-\s*(\d{1,5})$/);
    if (rangeMatch) {
      const start = Number(normalizeWorkId(rangeMatch[1]));
      const end = Number(normalizeWorkId(rangeMatch[2]));
      if (!Number.isFinite(start) || !Number.isFinite(end) || start > end) {
        throw new Error(`Invalid work id range: ${token}`);
      }
      for (let value = start; value <= end; value += 1) {
        const workId = String(value).padStart(5, "0");
        if (seen.has(workId)) continue;
        seen.add(workId);
        workIds.push(workId);
      }
      return;
    }
    const workId = normalizeWorkId(token);
    if (!workId) {
      throw new Error(`Invalid work id: ${token}`);
    }
    if (seen.has(workId)) return;
    seen.add(workId);
    workIds.push(workId);
  });
  return workIds;
}

function formatSelectionList(ids) {
  const items = Array.isArray(ids) ? ids.slice(0, BULK_PREVIEW_LIMIT) : [];
  if (!items.length) return "";
  const more = (ids.length || 0) - items.length;
  return more > 0 ? `${items.join(", ")} +${more} more` : items.join(", ");
}

function isWorkBulkQuery(rawValue) {
  try {
    return parseWorkSelection(rawValue).length > 1;
  } catch (_error) {
    return false;
  }
}

function buildBulkDraftFromRecords(records) {
  const drafts = records.map((record) => buildDraftFromRecord(record));
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

function parseBulkSeriesOperation(value) {
  const text = normalizeText(value);
  if (!text) {
    return { mode: "replace", series_ids: [] };
  }
  const tokens = text.split(",").map((item) => normalizeText(item)).filter(Boolean);
  const signed = tokens.filter((token) => token.startsWith("+") || token.startsWith("-"));
  if (signed.length && signed.length !== tokens.length) {
    throw new Error("Use either plain series ids or only +id/-id entries.");
  }
  if (!signed.length) {
    return { mode: "replace", series_ids: parseSeriesIds(tokens) };
  }
  const addSeriesIds = [];
  const removeSeriesIds = [];
  tokens.forEach((token) => {
    const sign = token[0];
    const seriesId = normalizeSeriesId(token.slice(1));
    if (!seriesId) {
      throw new Error(`Invalid series id entry: ${token}`);
    }
    if (sign === "+") addSeriesIds.push(seriesId);
    if (sign === "-") removeSeriesIds.push(seriesId);
  });
  return {
    mode: "add_remove",
    add_series_ids: dedupeSeriesIds(addSeriesIds),
    remove_series_ids: dedupeSeriesIds(removeSeriesIds)
  };
}

function detailSectionLabel(state, sectionKey) {
  return normalizeText(sectionKey) || t(state, "details_section_blank", "root");
}

function renderField(field, fieldsNode, state) {
  const wrapper = document.createElement("label");
  wrapper.className = "tagStudioForm__field catalogueWorkForm__field";
  if (field.type === "textarea") wrapper.classList.add("tagStudioForm__field--topAligned", "catalogueWorkForm__field--topAligned");
  wrapper.htmlFor = `catalogueWorkField-${field.key}`;

  const label = document.createElement("span");
  label.className = "tagStudioForm__label";
  label.textContent = field.label;
  wrapper.appendChild(label);

  let input;
  if (field.type === "textarea") {
    input = document.createElement("textarea");
    input.className = "tagStudio__input tagStudioForm__descriptionInput";
    input.rows = 4;
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
    input.type = field.type === "date" ? "date" : "text";
    if (field.type === "number") {
      input.inputMode = field.step && String(field.step).includes(".") ? "decimal" : "numeric";
    }
  }

  input.id = `catalogueWorkField-${field.key}`;
  input.dataset.field = field.key;
  if (field.description) {
    input.setAttribute("aria-describedby", `catalogueWorkFieldHelp-${field.key}`);
  }
  wrapper.appendChild(input);

  if (field.description) {
    const help = document.createElement("span");
    help.className = "tagStudioForm__meta catalogueWorkForm__fieldMeta";
    help.id = `catalogueWorkFieldHelp-${field.key}`;
    help.textContent = field.description;
    wrapper.appendChild(help);
  }

  const message = document.createElement("span");
  message.className = "catalogueWorkForm__fieldStatus";
  message.dataset.fieldStatus = field.key;
  wrapper.appendChild(message);

  input.addEventListener("input", () => onFieldInput(state, field.key));
  input.addEventListener("change", () => onFieldInput(state, field.key));
  fieldsNode.appendChild(wrapper);
  state.fieldNodes.set(field.key, input);
  state.fieldStatusNodes.set(field.key, message);
}

function renderReadonlyField(field, readonlyNode, state) {
  const wrapper = document.createElement("div");
  wrapper.className = "tagStudioForm__field";

  const label = document.createElement("span");
  label.className = "tagStudioForm__label";
  label.textContent = field.label;
  wrapper.appendChild(label);

  const value = document.createElement("div");
  value.className = "tagStudio__input tagStudio__input--readonlyDisplay";
  value.dataset.readonlyField = field.key;
  value.textContent = "—";
  wrapper.appendChild(value);

  readonlyNode.appendChild(wrapper);
  state.readonlyNodes.set(field.key, value);
}

function setModeFieldAvailability(state) {
  const statusNode = state.fieldNodes.get("status");
  if (statusNode) {
    statusNode.disabled = state.mode === "new";
  }
  const publishedDateNode = state.fieldNodes.get("published_date");
  if (publishedDateNode) {
    publishedDateNode.disabled = state.mode === "new";
  }
}

function setTextWithState(node, text, state = "") {
  if (!node) return;
  node.textContent = text || "";
  if (state) {
    node.dataset.state = state;
  } else {
    delete node.dataset.state;
  }
}

function setPopupVisibility(state, visible) {
  state.popupNode.hidden = !visible;
}

function setOpenInputMode(state) {
  state.searchNode.placeholder = t(state, "search_placeholder", "find work id(s): 00001, 00003-00005");
  state.searchNode.setAttribute("aria-label", t(state, "search_label", "Find work by id"));
}

function getSearchMatches(state, rawQuery) {
  const query = buildSearchToken(rawQuery);
  if (!query) return [];
  const matches = [];
  for (const [workId, record] of state.workSearchById.entries()) {
    if (workId.includes(query)) {
      matches.push({ workId, record });
      continue;
    }
    if (normalizeWorkId(query) && workId === normalizeWorkId(query)) {
      matches.push({ workId, record });
    }
  }
  matches.sort((a, b) => a.workId.localeCompare(b.workId, undefined, { numeric: true, sensitivity: "base" }));
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

  const rows = matches.map(({ workId, record }) => `
    <button type="button" class="tagStudioSuggest__workButton" data-work-id="${escapeHtml(workId)}">
      <span class="tagStudioSuggest__workId">${escapeHtml(workId)}</span>
      <span class="tagStudioSuggest__workTitle">${escapeHtml(buildRecordSummary(record))}</span>
    </button>
  `);
  state.popupListNode.innerHTML = `<div class="tagStudioSuggest__workRows">${rows.join("")}</div>`;
  setPopupVisibility(state, true);
}

function buildSourceWorkMap(payload) {
  const works = payload && typeof payload.works === "object" && payload.works !== null ? payload.works : {};
  const out = new Map();
  Object.entries(works).forEach(([workId, record]) => {
    const normalizedId = normalizeWorkId(workId);
    if (!normalizedId || !record || typeof record !== "object") return;
    out.set(normalizedId, record);
  });
  return out;
}

function buildDraftFromRecord(record) {
  return buildWorkDraftFromRecord(record, {
    fields: EDITABLE_FIELDS,
    downloadFields: DOWNLOAD_FIELDS,
    linkFields: LINK_FIELDS
  });
}

function applyDraftToInputs(state) {
  EDITABLE_FIELDS.forEach((field) => {
    const node = state.fieldNodes.get(field.key);
    if (!node) return;
    node.value = normalizeText(state.draft[field.key]);
  });
}

function applyReadonly(state) {
  READONLY_FIELDS.forEach((field) => {
    const node = state.readonlyNodes.get(field.key);
    if (!node) return;
    node.textContent = displayValue(state.currentRecord ? state.currentRecord[field.key] : "");
  });
}

function buildSeriesSummaryHtml(state, seriesIds) {
  if (!seriesIds.length) {
    return escapeHtml(t(state, "context_series_empty", "No series assigned."));
  }

  const seriesBase = getStudioRoute(state.config, "series_page_base");
  return seriesIds.map((seriesId) => {
    const seriesRecord = state.seriesById.get(seriesId);
    const label = seriesRecord && seriesRecord.title ? `${seriesId} · ${seriesRecord.title}` : seriesId;
    const href = `${seriesBase}${encodeURIComponent(seriesId)}/`;
    return `<a href="${escapeHtml(href)}" target="_blank" rel="noopener">${escapeHtml(label)}</a>`;
  }).join("<br>");
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

function groupWorkDetailsBySection(state, details) {
  const groups = new Map();
  details.forEach((detail) => {
    const key = normalizeText(detail && detail.project_subfolder);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(detail);
  });
  return Array.from(groups.entries())
    .map(([sectionKey, items]) => ({
      sectionKey,
      items: items.slice().sort((a, b) => compareDetailUid(a.detail_uid, b.detail_uid))
    }))
    .sort((a, b) => a.sectionKey.localeCompare(b.sectionKey, undefined, { sensitivity: "base" }));
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
  const route = getStudioRoute(state.config, "catalogue_work_detail_editor");
  return `${route}?detail=${encodeURIComponent(detailUid)}`;
}

async function loadWorkLookupRecord(state, workId) {
  return loadStudioLookupRecordJson(state.config, "catalogue_lookup_work_base", workId, { cache: "no-store" });
}

function getSourceWorkRecord(state, workId, fallbackRecord = null) {
  const sourceRecord = state.sourceWorkRecordsById.get(workId);
  if (sourceRecord && typeof sourceRecord === "object") return sourceRecord;
  if (fallbackRecord && typeof fallbackRecord === "object") return fallbackRecord;
  return null;
}

function renderDetailRows(state, details) {
  return details.map((detail) => {
    const detailUid = normalizeText(detail && detail.detail_uid);
    const title = displayValue(detail && detail.title);
    const href = buildDetailEditorHref(state, detailUid);
    const preview = buildDetailThumbPreview(state.mediaConfig, detailUid);
    return `
      <div class="catalogueWorkDetails__row catalogueWorkDetails__row--detail">
        <a class="catalogueThumbPreview" href="${escapeHtml(href)}" data-preview-state="${preview.src ? "loading" : "missing-generated"}" data-preview-fallback="missing-generated" aria-label="${escapeHtml(title)}">
          ${preview.src ? `<img class="catalogueThumbPreview__img" data-preview-image src="${escapeHtml(preview.src)}" srcset="${escapeHtml(preview.srcset || "")}" sizes="48px" width="${escapeHtml(String(preview.width || 48))}" height="${escapeHtml(String(preview.height || 48))}" alt="" loading="lazy" decoding="async">` : ""}
          <span class="catalogueThumbPreview__placeholder">${escapeHtml(t(state, "detail_preview_missing", "No preview"))}</span>
        </a>
        <a class="catalogueWorkDetails__link" href="${escapeHtml(href)}">${escapeHtml(detailUid)}</a>
        <span class="catalogueWorkDetails__title">${escapeHtml(title)}</span>
      </div>
    `;
  }).join("");
}

function getWorkFiles(state, workId) {
  if (!state.currentRecord || state.currentWorkId !== workId) return [];
  return cloneEmbeddedEntries(state.draft.downloads, DOWNLOAD_FIELDS);
}

function getWorkLinks(state, workId) {
  if (!state.currentRecord || state.currentWorkId !== workId) return [];
  return cloneEmbeddedEntries(state.draft.links, LINK_FIELDS);
}

function renderWorkFileRows(state, items) {
  const actionDisabled = state.isSaving || state.isBuilding || state.isDeleting || state.mode === "bulk";
  return items.map((item, index) => {
    const filename = displayValue(item && item.filename);
    const label = displayValue(item && item.label);
    return `
      <div class="tagStudioList__row tagStudioList__row--start catalogueWorkDetails__row catalogueWorkDetails__row--metadata">
        <span class="tagStudioList__cell catalogueWorkDetails__link">${escapeHtml(filename)}</span>
        <span class="tagStudioList__cell catalogueWorkDetails__title">${escapeHtml(label)}</span>
        <span class="tagStudioList__cell catalogueWorkDetails__rowActions">
          <button type="button" class="tagStudio__button" data-download-edit="${escapeHtml(String(index))}" ${actionDisabled ? "disabled" : ""}>${escapeHtml(t(state, "files_edit_button", "Edit"))}</button>
          <button type="button" class="tagStudio__button" data-download-delete="${escapeHtml(String(index))}" ${actionDisabled ? "disabled" : ""}>${escapeHtml(t(state, "files_delete_button", "Delete"))}</button>
        </span>
      </div>
    `;
  }).join("");
}

function renderWorkLinkRows(state, items) {
  const actionDisabled = state.isSaving || state.isBuilding || state.isDeleting || state.mode === "bulk";
  return items.map((item, index) => {
    const url = displayValue(item && item.url);
    const label = displayValue(item && item.label);
    return `
      <div class="tagStudioList__row tagStudioList__row--start catalogueWorkDetails__row catalogueWorkDetails__row--metadata">
        <span class="tagStudioList__cell catalogueWorkDetails__link">${escapeHtml(label)}</span>
        <span class="tagStudioList__cell catalogueWorkDetails__title">${escapeHtml(url)}</span>
        <span class="tagStudioList__cell catalogueWorkDetails__rowActions">
          <button type="button" class="tagStudio__button" data-link-edit="${escapeHtml(String(index))}" ${actionDisabled ? "disabled" : ""}>${escapeHtml(t(state, "links_edit_button", "Edit"))}</button>
          <button type="button" class="tagStudio__button" data-link-delete="${escapeHtml(String(index))}" ${actionDisabled ? "disabled" : ""}>${escapeHtml(t(state, "links_delete_button", "Delete"))}</button>
        </span>
      </div>
    `;
  }).join("");
}

function updateDetailSections(state) {
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
    state.detailsResultsNode.innerHTML = `<p class="tagStudioForm__meta">${escapeHtml(t(state, "details_empty", "No work details for this work."))}</p>`;
    return;
  }

  const groups = groupWorkDetailsBySection(state, details);
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
            <h3 class="tagStudioForm__key">${escapeHtml(t(state, "details_search_results", "matching details"))}</h3>
          </div>
          <div class="catalogueWorkDetails__rows">${renderDetailRows(state, matches)}</div>
        </section>
      `);
    } else {
      blocks.push(`<p class="tagStudioForm__meta">${escapeHtml(t(state, "details_search_no_match", "No matching detail ids for this work."))}</p>`);
    }
  }

  groups.forEach((group) => {
    const visible = group.items.slice(0, DETAIL_LIST_LIMIT);
    const moreText = group.items.length > DETAIL_LIST_LIMIT
      ? t(state, "details_more_count", "showing {visible} of {total}", {
        visible: String(visible.length),
        total: String(group.items.length)
      })
      : "";
    blocks.push(`
      <section class="catalogueWorkDetails__section">
        <div class="tagStudio__headingRow">
          <h3 class="tagStudioForm__key">${escapeHtml(detailSectionLabel(state, group.sectionKey))}</h3>
          ${moreText ? `<span class="tagStudioForm__meta">${escapeHtml(moreText)}</span>` : ""}
        </div>
        <div class="catalogueWorkDetails__rows">${renderDetailRows(state, visible)}</div>
      </section>
    `);
  });

  state.detailsMetaNode.textContent = `${details.length} total`;
  state.detailsResultsNode.innerHTML = blocks.join("");
  bindPreviewImages(state.detailsResultsNode);
}

function updateWorkFilesSection(state) {
  if (!state.filesResultsNode || !state.filesMetaNode) return;
  if (!state.currentWorkId) {
    state.filesMetaNode.textContent = "";
    state.filesResultsNode.innerHTML = "";
    return;
  }
  const items = getWorkFiles(state, state.currentWorkId);
  const error = state.validationErrors.get("downloads") || "";
  if (error) state.filesMetaNode.dataset.state = "error";
  else delete state.filesMetaNode.dataset.state;
  if (!items.length) {
    state.filesMetaNode.textContent = error;
    state.filesResultsNode.innerHTML = `<p class="tagStudioForm__meta">${escapeHtml(t(state, "files_empty", "No work files for this work."))}</p>`;
    return;
  }
  state.filesMetaNode.textContent = error || `${items.length} total`;
  state.filesResultsNode.innerHTML = `
    <section class="catalogueWorkDetails__section">
      <div class="tagStudioList catalogueWorkDetails__rows">${renderWorkFileRows(state, items)}</div>
    </section>
  `;
}

function updateWorkLinksSection(state) {
  if (!state.linksResultsNode || !state.linksMetaNode) return;
  if (!state.currentWorkId) {
    state.linksMetaNode.textContent = "";
    state.linksResultsNode.innerHTML = "";
    return;
  }
  const items = getWorkLinks(state, state.currentWorkId);
  const error = state.validationErrors.get("links") || "";
  if (error) state.linksMetaNode.dataset.state = "error";
  else delete state.linksMetaNode.dataset.state;
  if (!items.length) {
    state.linksMetaNode.textContent = error;
    state.linksResultsNode.innerHTML = `<p class="tagStudioForm__meta">${escapeHtml(t(state, "links_empty", "No work links for this work."))}</p>`;
    return;
  }
  state.linksMetaNode.textContent = error || `${items.length} total`;
  state.linksResultsNode.innerHTML = `
    <section class="catalogueWorkDetails__section">
      <div class="tagStudioList catalogueWorkDetails__rows">${renderWorkLinkRows(state, items)}</div>
    </section>
  `;
}

function closeEntryModal(state) {
  if (state.modalHost) state.modalHost.innerHTML = "";
  document.removeEventListener("keydown", state.activeModalKeydown);
  state.activeModalKeydown = null;
}

function modalFieldHtml({ fieldId, label, value, type = "text" }) {
  return `
    <label class="tagStudioForm__field" for="${escapeHtml(fieldId)}">
      <span class="tagStudioForm__label">${escapeHtml(label)}</span>
      <input class="tagStudio__input" id="${escapeHtml(fieldId)}" type="${escapeHtml(type)}" value="${escapeHtml(value)}">
    </label>
  `;
}

function openEmbeddedEntryModal(state, kind, index = null) {
  if (!state.currentRecord || state.mode === "bulk") return;
  const isDownload = kind === "download";
  const entriesKey = isDownload ? "downloads" : "links";
  const fields = isDownload ? DOWNLOAD_FIELDS : LINK_FIELDS;
  const entries = cloneEmbeddedEntries(state.draft[entriesKey], fields);
  const editing = Number.isInteger(index) && index >= 0 && index < entries.length;
  const current = editing ? entries[index] : {};
  const title = isDownload
    ? (editing ? t(state, "files_edit_modal_title", "Edit download") : t(state, "files_add_modal_title", "Add download"))
    : (editing ? t(state, "links_edit_modal_title", "Edit link") : t(state, "links_add_modal_title", "Add link"));
  const firstField = isDownload
    ? { fieldId: "catalogueWorkDownloadFilename", label: t(state, "files_filename_label", "filename"), key: "filename", value: current.filename || "" }
    : { fieldId: "catalogueWorkLinkUrl", label: t(state, "links_url_label", "URL"), key: "url", value: current.url || "", type: "url" };
  const secondField = isDownload
    ? { fieldId: "catalogueWorkDownloadLabel", label: t(state, "files_label_label", "label"), key: "label", value: current.label || "" }
    : { fieldId: "catalogueWorkLinkLabel", label: t(state, "links_label_label", "label"), key: "label", value: current.label || "" };
  const statusId = isDownload ? "catalogueWorkDownloadModalStatus" : "catalogueWorkLinkModalStatus";

  closeEntryModal(state);
  state.modalHost.innerHTML = renderStudioModalFrame({
    hidden: false,
    title,
    titleId: isDownload ? "catalogueWorkDownloadModalTitle" : "catalogueWorkLinkModalTitle",
    modalRole: isDownload ? "download-modal" : "link-modal",
    backdropRole: "entry-modal-cancel",
    bodyHtml: `
      <div class="tagStudioForm__fields">
        ${modalFieldHtml(firstField)}
        ${modalFieldHtml(secondField)}
      </div>
      <p class="tagStudioForm__status" id="${escapeHtml(statusId)}"></p>
    `,
    actions: [
      { role: "entry-modal-save", label: t(state, "entry_modal_save_button", "Save") },
      { role: "entry-modal-cancel", label: t(state, "entry_modal_cancel_button", "Cancel") }
    ]
  });

  const firstNode = state.modalHost.querySelector(`#${firstField.fieldId}`);
  const secondNode = state.modalHost.querySelector(`#${secondField.fieldId}`);
  const statusNode = state.modalHost.querySelector(`#${statusId}`);
  const saveNode = state.modalHost.querySelector('[data-role="entry-modal-save"]');
  const cancelNodes = state.modalHost.querySelectorAll('[data-role="entry-modal-cancel"]');

  const setModalStatus = (message) => {
    if (!statusNode) return;
    statusNode.textContent = message || "";
    if (message) {
      statusNode.dataset.state = "error";
    } else {
      delete statusNode.dataset.state;
    }
  };

  const submit = () => {
    const firstValue = normalizeText(firstNode && firstNode.value);
    const secondValue = normalizeText(secondNode && secondNode.value);
    if (!firstValue) {
      setModalStatus(isDownload
        ? t(state, "files_invalid_filename", "Each download needs a filename.")
        : t(state, "links_invalid_url", "Each link needs a URL."));
      return;
    }
    if (!secondValue) {
      setModalStatus(isDownload
        ? t(state, "files_invalid_label", "Each download needs a label.")
        : t(state, "links_invalid_label", "Each link needs a label."));
      return;
    }
    const nextEntry = isDownload
      ? { filename: firstValue, label: secondValue }
      : { url: firstValue, label: secondValue };
    if (editing) {
      entries[index] = nextEntry;
    } else {
      entries.push(nextEntry);
    }
    state.draft[entriesKey] = entries;
    closeEntryModal(state);
    updateEditorState(state);
  };

  state.activeModalKeydown = (event) => {
    if (event.key === "Escape") {
      event.preventDefault();
      closeEntryModal(state);
    }
    if (event.key === "Enter" && event.target && event.target.tagName === "INPUT") {
      event.preventDefault();
      submit();
    }
  };
  document.addEventListener("keydown", state.activeModalKeydown);
  cancelNodes.forEach((button) => button.addEventListener("click", () => closeEntryModal(state)));
  if (saveNode) saveNode.addEventListener("click", submit);
  if (firstNode) firstNode.focus();
}

async function deleteEmbeddedEntry(state, kind, index) {
  if (!state.currentRecord || state.mode === "bulk") return;
  const isDownload = kind === "download";
  const entriesKey = isDownload ? "downloads" : "links";
  const fields = isDownload ? DOWNLOAD_FIELDS : LINK_FIELDS;
  const entries = cloneEmbeddedEntries(state.draft[entriesKey], fields);
  if (!Number.isInteger(index) || index < 0 || index >= entries.length) return;
  const label = isDownload
    ? normalizeText(entries[index].label || entries[index].filename)
    : normalizeText(entries[index].label || entries[index].url);
  const result = await openConfirmModal({
    root: state.root,
    title: isDownload ? t(state, "files_delete_modal_title", "Delete download") : t(state, "links_delete_modal_title", "Delete link"),
    body: isDownload
      ? t(state, "files_delete_modal_body", "Delete download {label}?", { label })
      : t(state, "links_delete_modal_body", "Delete link {label}?", { label }),
    primaryLabel: t(state, "entry_modal_delete_button", "Delete"),
    cancelLabel: t(state, "entry_modal_cancel_button", "Cancel")
  });
  if (!result || !result.confirmed) return;
  entries.splice(index, 1);
  state.draft[entriesKey] = entries;
  updateEditorState(state);
}

function updateSummary(state) {
  if (state.mode === "new") {
    state.metaNode.textContent = t(state, "new_meta", "Creating a draft work.");
    state.summaryNode.innerHTML = `
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(t(state, "new_summary_status_label", "status"))}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(t(state, "new_summary_status", "draft source record; not published"))}</div>
      </div>
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(t(state, "new_summary_next_label", "next step"))}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(t(state, "new_summary_next", "Create the draft, then continue editing or publish from edit mode."))}</div>
      </div>
    `;
    state.runtimeStateNode.textContent = t(state, "new_runtime_state", "public site update is unavailable until the draft exists");
    setTextWithState(state.buildImpactNode, "");
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
    updateDetailSections(state);
    updateWorkFilesSection(state);
    updateWorkLinksSection(state);
    renderCurrentPreview(state);
    renderReadiness(state);
    return;
  }

  if (state.mode === "bulk") {
    const selectedCount = state.bulkWorkIds.length;
    const selectedRecords = state.bulkWorkIds.map((workId) => state.bulkRecords.get(workId)).filter(Boolean);
    const seriesIds = dedupeSeriesIds(
      selectedRecords.flatMap((record) => parseSeriesIds(record && record.series_ids))
    );
    state.metaNode.textContent = selectedCount
      ? t(state, "bulk_meta", "{count} works selected", { count: String(selectedCount) })
      : "";
    state.summaryNode.innerHTML = `
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(t(state, "bulk_summary_selected", "selected works"))}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(formatSelectionList(state.bulkWorkIds) || "—")}</div>
      </div>
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(t(state, "bulk_summary_count", "record count"))}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(String(selectedCount || 0))}</div>
      </div>
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(t(state, "summary_series_label", "series"))}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay catalogueWorkSummary__series">${escapeHtml(seriesIds.length ? formatSelectionList(seriesIds) : "—")}</div>
      </div>
    `;
    state.runtimeStateNode.textContent = state.rebuildPending
      ? t(state, "summary_rebuild_needed", "source saved; site update pending")
      : t(state, "summary_rebuild_current", "source and public catalogue are aligned in this session");
    if (state.newDetailLinkNode) {
      state.newDetailLinkNode.removeAttribute("aria-disabled");
      state.newDetailLinkNode.href = getStudioRoute(state.config, "catalogue_new_work_detail_editor");
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
    renderCurrentPreview(state);
    renderReadiness(state);
    return;
  }

  const record = state.currentRecord;
  state.metaNode.textContent = record
    ? `${record.work_id} · ${buildRecordSummary(record)}`
    : "";

  const seriesIds = parseSeriesIds(state.draft.series_ids);
  const workBase = getStudioRoute(state.config, "works_page_base");
  const publicHref = record ? `${workBase}${encodeURIComponent(record.work_id)}/` : "";
  state.summaryNode.innerHTML = `
    <div class="tagStudioForm__field">
      <span class="tagStudioForm__label">${escapeHtml(t(state, "summary_public_link", "Open public work page"))}</span>
      <div class="tagStudio__input tagStudio__input--readonlyDisplay">
        ${record ? `<a href="${escapeHtml(publicHref)}" target="_blank" rel="noopener">${escapeHtml(record.work_id)}</a>` : "—"}
      </div>
    </div>
    <div class="tagStudioForm__field">
      <span class="tagStudioForm__label">${escapeHtml(t(state, "summary_series_label", "series"))}</span>
      <div class="tagStudio__input tagStudio__input--readonlyDisplay catalogueWorkSummary__series">${buildSeriesSummaryHtml(state, seriesIds)}</div>
    </div>
  `;

  state.runtimeStateNode.textContent = state.rebuildPending
    ? t(state, "summary_rebuild_needed", "source saved; site update pending")
    : t(state, "summary_rebuild_current", "source and public catalogue are aligned in this session");
  if (state.newDetailLinkNode) {
    const base = getStudioRoute(state.config, "catalogue_new_work_detail_editor");
    state.newDetailLinkNode.removeAttribute("aria-disabled");
    state.newDetailLinkNode.href = record ? `${base}?work=${encodeURIComponent(record.work_id)}` : base;
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
  updateDetailSections(state);
  updateWorkFilesSection(state);
  updateWorkLinksSection(state);
  renderCurrentPreview(state);
  renderReadiness(state);
}

function formatBuildPreview(state, build) {
  if (!build || typeof build !== "object") return "";
  const workIds = Array.isArray(build.work_ids) ? build.work_ids : [];
  const seriesIds = Array.isArray(build.series_ids) ? build.series_ids : [];
  const localMedia = build.local_media && typeof build.local_media === "object" ? build.local_media : null;
  const localCounts = localMedia && typeof localMedia.counts === "object" ? localMedia.counts : null;
  const workText = workIds.length ? workIds.join(", ") : "none";
  const seriesText = seriesIds.length ? seriesIds.join(", ") : "none";
  const searchText = build.rebuild_search ? t(state, "build_preview_search_yes", "yes") : t(state, "build_preview_search_no", "no");
  const baseText = t(
    state,
    "build_preview_template",
    "Build preview: work {work_ids}; series {series_ids}; catalogue search {search_rebuild}.",
    {
      work_ids: workText,
      series_ids: seriesText,
      search_rebuild: searchText
    }
  );
  if (!localCounts) return baseText;
  const pending = Number(localCounts.pending) || 0;
  const blocked = Number(localCounts.blocked) || 0;
  const unavailable = Number(localCounts.unavailable) || 0;
  const current = Number(localCounts.current) || 0;
  const mediaParts = [];
  if (pending) mediaParts.push(`local media pending ${pending}`);
  if (blocked) mediaParts.push(`local media blocked ${blocked}`);
  if (unavailable) mediaParts.push(`local media unavailable ${unavailable}`);
  if (!pending && !blocked && !unavailable && current) mediaParts.push(`local media current ${current}`);
  return mediaParts.length ? `${baseText} ${mediaParts.join("; ")}.` : baseText;
}

function syncUrl(workValue, mode = "") {
  const url = new URL(window.location.href);
  if (mode === "new") {
    url.searchParams.delete("work");
    url.searchParams.set("mode", "new");
  } else if (workValue) {
    url.searchParams.delete("mode");
    url.searchParams.set("work", workValue);
  } else {
    url.searchParams.delete("mode");
    url.searchParams.delete("work");
  }
  window.history.replaceState({}, "", url.toString());
}

function draftHasChanges(state) {
  if (state.mode === "new") {
    return Boolean(
      normalizeWorkId(state.draft.work_id) ||
      EDITABLE_FIELDS.some((field) => normalizeText(state.draft[field.key]))
    );
  }
  if (state.mode === "bulk") {
    return state.bulkTouchedFields.size > 0;
  }
  if (!state.baselineDraft) return false;
  return (
    EDITABLE_FIELDS.some((field) => canonicalizeScalar(field, state.draft[field.key]) !== canonicalizeScalar(field, state.baselineDraft[field.key])) ||
    !embeddedEntriesEqual(state.draft.downloads, state.baselineDraft.downloads, DOWNLOAD_FIELDS) ||
    !embeddedEntriesEqual(state.draft.links, state.baselineDraft.links, LINK_FIELDS)
  );
}

function validateDraft(state) {
  if (state.mode === "new") {
    const errors = new Map();
    const workId = normalizeWorkId(state.draft.work_id);
    if (!workId) {
      errors.set("work_id", t(state, "field_required_work_id", "Enter a work id."));
    } else if (state.workSearchById.has(workId) || state.sourceWorkRecordsById.has(workId)) {
      errors.set("work_id", t(state, "field_duplicate_work_id", "Work id already exists."));
    }

    REQUIRED_WORK_FIELDS.forEach((fieldKey) => {
      if (fieldKey === "series_ids") {
        if (!parseSeriesIds(state.draft.series_ids).length) {
          errors.set("series_ids", t(state, "field_required_series_ids", "Enter at least one series id."));
        }
        return;
      }
      if (!normalizeText(state.draft[fieldKey])) {
        const label = fieldKey.replace(/_/g, " ");
        errors.set(fieldKey, t(state, `field_required_${fieldKey}`, "Enter {field}.", { field: label }));
      }
    });

    const year = normalizeText(state.draft.year);
    if (year && !/^-?\d+$/.test(year)) {
      errors.set("year", t(state, "field_invalid_year", "Use a whole year or leave blank."));
    }

    WORK_DIMENSION_FIELD_KEYS.forEach((fieldKey) => {
      const value = normalizeText(state.draft[fieldKey]);
      if (value && !Number.isFinite(Number(value))) {
        errors.set(fieldKey, t(state, "field_invalid_number", "Use a number or leave blank."));
      }
    });

    const seriesText = normalizeText(state.draft.series_ids);
    if (seriesText) {
      const parts = seriesText.split(",").map((item) => normalizeText(item)).filter(Boolean);
      for (const part of parts) {
        if (!SERIES_ID_RE.test(part)) {
          errors.set("series_ids", t(state, "field_invalid_series_id", "Use comma-separated numeric series ids."));
          break;
        }
        const normalizedId = normalizeSeriesId(part);
        if (!state.seriesById.has(normalizedId)) {
          errors.set("series_ids", t(state, "field_unknown_series_id", "Unknown series id: {series_id}.", { series_id: normalizedId }));
          break;
        }
      }
    }
    return errors;
  }

  if (state.mode === "bulk") {
    const errors = new Map();
    if (state.bulkTouchedFields.has("status")) {
      const status = normalizeText(state.draft.status).toLowerCase();
      if (!STATUS_OPTIONS.has(status)) {
        errors.set("status", t(state, "field_invalid_status", "Use blank, draft, or published."));
      }
    }

    if (state.bulkTouchedFields.has("published_date")) {
      const publishedDate = normalizeText(state.draft.published_date);
      if (publishedDate && !DATE_RE.test(publishedDate)) {
        errors.set("published_date", t(state, "field_invalid_date", "Use YYYY-MM-DD or leave blank."));
      }
    }

    if (state.bulkTouchedFields.has("year")) {
      const year = normalizeText(state.draft.year);
      if (year && !/^-?\d+$/.test(year)) {
        errors.set("year", t(state, "field_invalid_year", "Use a whole year or leave blank."));
      }
    }

    WORK_DIMENSION_FIELD_KEYS.forEach((fieldKey) => {
      if (!state.bulkTouchedFields.has(fieldKey)) return;
      const value = normalizeText(state.draft[fieldKey]);
      if (value && !Number.isFinite(Number(value))) {
        errors.set(fieldKey, t(state, "field_invalid_number", "Use a number or leave blank."));
      }
    });

    if (state.bulkTouchedFields.has("series_ids")) {
      try {
        const operation = parseBulkSeriesOperation(state.draft.series_ids);
        const seriesIds = operation.mode === "replace"
          ? operation.series_ids
          : [...operation.add_series_ids, ...operation.remove_series_ids];
        for (const seriesId of seriesIds) {
          if (!state.seriesById.has(seriesId)) {
            errors.set("series_ids", t(state, "field_unknown_series_id", "Unknown series id: {series_id}.", { series_id: seriesId }));
            break;
          }
        }
      } catch (error) {
        errors.set(
          "series_ids",
          normalizeText(error && error.message) || t(state, "field_invalid_series_id", "Use comma-separated numeric series ids.")
        );
      }
    }

    return errors;
  }

  const errors = new Map();
  const status = normalizeText(state.draft.status).toLowerCase();
  if (!STATUS_OPTIONS.has(status)) {
    errors.set("status", t(state, "field_invalid_status", "Use blank, draft, or published."));
  }

  const publishedDate = normalizeText(state.draft.published_date);
  if (publishedDate && !DATE_RE.test(publishedDate)) {
    errors.set("published_date", t(state, "field_invalid_date", "Use YYYY-MM-DD or leave blank."));
  }

  const year = normalizeText(state.draft.year);
  if (year && !/^-?\d+$/.test(year)) {
    errors.set("year", t(state, "field_invalid_year", "Use a whole year or leave blank."));
  }

  WORK_DIMENSION_FIELD_KEYS.forEach((fieldKey) => {
    const value = normalizeText(state.draft[fieldKey]);
    if (value && !Number.isFinite(Number(value))) {
      errors.set(fieldKey, t(state, "field_invalid_number", "Use a number or leave blank."));
    }
  });

  const seriesText = normalizeText(state.draft.series_ids);
  if (seriesText) {
    const parts = seriesText.split(",").map((item) => normalizeText(item)).filter(Boolean);
    for (const part of parts) {
      if (!SERIES_ID_RE.test(part)) {
        errors.set("series_ids", t(state, "field_invalid_series_id", "Use comma-separated numeric series ids."));
        break;
      }
      const normalizedId = normalizeSeriesId(part);
      if (!state.seriesById.has(normalizedId)) {
        errors.set("series_ids", t(state, "field_unknown_series_id", "Unknown series id: {series_id}.", { series_id: normalizedId }));
        break;
      }
    }
  }

  normalizeEmbeddedEntries(state.draft.downloads, DOWNLOAD_FIELDS).forEach((item, index) => {
    if (!normalizeText(item.filename)) {
      errors.set("downloads", t(state, "files_invalid_filename", "Each download needs a filename."));
    } else if (!normalizeText(item.label)) {
      errors.set("downloads", t(state, "files_invalid_label", "Each download needs a label."));
    }
  });

  normalizeEmbeddedEntries(state.draft.links, LINK_FIELDS).forEach((item, index) => {
    if (!normalizeText(item.url)) {
      errors.set("links", t(state, "links_invalid_url", "Each link needs a URL."));
    } else if (!normalizeText(item.label)) {
      errors.set("links", t(state, "links_invalid_label", "Each link needs a label."));
    }
  });

  return errors;
}

function updateFieldMessages(state, errors) {
  EDITABLE_FIELDS.forEach((field) => {
    const messageNode = state.fieldStatusNodes.get(field.key);
    if (!messageNode) return;
    let message = errors.get(field.key) || "";
    if (!message && state.mode === "bulk" && state.bulkMixedFields.has(field.key) && !state.bulkTouchedFields.has(field.key)) {
      message = field.key === "series_ids"
        ? t(state, "bulk_field_mixed_series", "Mixed values across selection. Leave untouched to preserve, use plain ids to replace, or +id/-id to add or remove.")
        : t(state, "bulk_field_mixed", "Mixed values across selection. Leave untouched to preserve per-record values.");
    }
    messageNode.textContent = message;
    messageNode.hidden = !message;
  });
}

function buildPayload(state) {
  if (state.mode === "bulk") {
    const setFields = {};
    EDITABLE_FIELDS.forEach((field) => {
      if (!state.bulkTouchedFields.has(field.key) || field.key === "series_ids") return;
      const value = state.draft[field.key];
      if (field.key === "status") {
        setFields.status = normalizeText(value).toLowerCase() || null;
        return;
      }
      if (field.key === "year") {
        setFields.year = normalizeText(value) ? Number(value) : null;
        return;
      }
      if (WORK_DIMENSION_FIELD_KEYS.includes(field.key)) {
        setFields[field.key] = normalizeText(value) ? Number(value) : null;
        return;
      }
      setFields[field.key] = normalizeText(value) || null;
    });

    const expectedRecordHashes = {};
    state.bulkWorkIds.forEach((workId) => {
      expectedRecordHashes[workId] = state.bulkRecordHashes.get(workId) || "";
    });

    const payload = {
      kind: "works",
      ids: state.bulkWorkIds.slice(),
      expected_record_hashes: expectedRecordHashes,
      apply_build: applyBuildRequested(state),
      set_fields: setFields
    };
    if (state.bulkTouchedFields.has("series_ids")) {
      payload.series_operation = parseBulkSeriesOperation(state.draft.series_ids);
    }
    return payload;
  }

  const draft = state.draft;
  return {
    work_id: state.currentWorkId,
    expected_record_hash: state.currentRecordHash,
    apply_build: applyBuildRequested(state),
    extra_series_ids: state.pendingBuildExtraSeriesIds.slice(),
    record: buildWorkRecordFromDraft(draft, {
      downloadFields: DOWNLOAD_FIELDS,
      linkFields: LINK_FIELDS
    })
  };
}

function applyBuildRequested(state) {
  return Boolean(state.applyBuildNode && state.applyBuildNode.checked);
}

function updatePublishControls(state, { hasRecord, dirty, errors }) {
  const showUpdate = state.mode !== "new" && hasRecord && state.rebuildPending;
  state.buildButton.hidden = !showUpdate;
  state.buildButton.disabled = !showUpdate || dirty || errors.size > 0 || state.isSaving || state.isBuilding || state.isDeleting || !state.serverAvailable;
  if (state.runtimeActionsNode) state.runtimeActionsNode.hidden = !showUpdate;
  if (state.applyBuildNode) {
    state.applyBuildNode.disabled = state.mode === "new" || !hasRecord || state.isSaving || state.isBuilding || state.isDeleting || !state.serverAvailable;
  }
}

function applySingleSaveBuildOutcome(state, response) {
  const build = response && response.build && typeof response.build === "object" ? response.build : null;
  if (!response || !response.build_requested || !build) {
    state.rebuildPending = Boolean(response && response.changed);
    return { kind: response && response.changed ? "saved" : "unchanged", stamp: normalizeText(response && response.saved_at_utc) || utcTimestamp() };
  }
  if (build.ok) {
    state.rebuildPending = false;
    state.pendingBuildExtraSeriesIds = [];
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
  if (!response || !response.build_requested || !build) {
    state.rebuildPending = Boolean(response && response.changed);
    state.bulkBuildTargets = fallbackBuildTargets;
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

function setLoadedRecord(state, workId, record, options = {}) {
  state.mode = "single";
  state.currentWorkId = workId;
  state.currentRecord = record;
  state.currentLookup = options.lookup || state.currentLookup;
  state.currentRecordHash = normalizeText(options.recordHash || state.currentRecordHash);
  state.bulkWorkIds = [];
  state.bulkRecords = new Map();
  state.bulkRecordHashes = new Map();
  state.bulkMixedFields = new Set();
  state.bulkTouchedFields = new Set();
  state.bulkBuildTargets = [];
  state.baselineDraft = buildDraftFromRecord(record);
  state.draft = { ...state.baselineDraft };
  setOpenInputMode(state);
  if (state.applyBuildNode) state.applyBuildNode.checked = true;
  applyDraftToInputs(state);
  applyReadonly(state);
  syncUrl(workId);
  setTextWithState(state.contextNode, t(state, "context_loaded", "Editing source metadata for work {work_id}.", { work_id: workId }));
  setTextWithState(state.statusNode, t(state, "save_status_loaded", "Loaded work {work_id}.", { work_id: workId }));
  setTextWithState(state.warningNode, "");
  if (!options.keepResult) {
    setTextWithState(state.resultNode, "");
  }
  updateEditorState(state);
}

function setLoadedBulkWorks(state, workIds, recordsById, recordHashes, options = {}) {
  state.mode = "bulk";
  state.currentWorkId = "";
  state.currentRecord = null;
  state.currentLookup = null;
  state.currentRecordHash = "";
  state.bulkWorkIds = workIds.slice();
  state.bulkRecords = new Map(recordsById);
  state.bulkRecordHashes = new Map(recordHashes);
  state.bulkBuildTargets = Array.isArray(options.buildTargets) ? options.buildTargets.slice() : [];
  const records = workIds.map((workId) => recordsById.get(workId)).filter(Boolean);
  const bulkDraft = buildBulkDraftFromRecords(records);
  state.baselineDraft = { ...bulkDraft.draft };
  state.draft = { ...bulkDraft.draft };
  state.bulkMixedFields = bulkDraft.mixedFields;
  state.bulkTouchedFields = new Set();
  setOpenInputMode(state);
  if (state.applyBuildNode) state.applyBuildNode.checked = false;
  applyDraftToInputs(state);
  READONLY_FIELDS.forEach((field) => {
    const node = state.readonlyNodes.get(field.key);
    if (node) node.textContent = "—";
  });
  syncUrl(workIds.join(","));
  setTextWithState(
    state.contextNode,
    t(state, "bulk_context_loaded", "Bulk editing {count} work records: {work_ids}.", {
      count: String(workIds.length),
      work_ids: formatSelectionList(workIds)
    })
  );
  setTextWithState(
    state.statusNode,
    t(state, "bulk_status_loaded", "Loaded {count} work records.", { count: String(workIds.length) })
  );
  setTextWithState(state.warningNode, "");
  if (!options.keepResult) {
    setTextWithState(state.resultNode, "");
  }
  updateEditorState(state);
}

function setNewWorkMode(state, options = {}) {
  state.mode = "new";
  state.currentWorkId = "";
  state.currentRecord = null;
  state.currentLookup = null;
  state.currentRecordHash = "";
  state.bulkWorkIds = [];
  state.bulkRecords = new Map();
  state.bulkRecordHashes = new Map();
  state.bulkMixedFields = new Set();
  state.bulkTouchedFields = new Set();
  state.bulkBuildTargets = [];
  state.baselineDraft = {};
  state.draft = {};
  EDITABLE_FIELDS.forEach((field) => {
    state.draft[field.key] = "";
  });
  state.draft.status = "draft";
  state.draft.published_date = "";
  state.draft.downloads = [];
  state.draft.links = [];
  state.draft.work_id = normalizeWorkId(options.workId) || state.nextSuggestedWorkId || suggestNextWorkId(Array.from(state.workSearchById.values()));
  state.searchNode.value = state.draft.work_id;
  state.searchNode.placeholder = t(state, "new_work_id_placeholder", "new work id");
  state.searchNode.setAttribute("aria-label", t(state, "new_work_id_label", "New work id"));
  state.detailSearchNode.value = "";
  state.pendingBuildExtraSeriesIds = [];
  state.rebuildPending = false;
  state.buildPreview = null;
  if (state.applyBuildNode) state.applyBuildNode.checked = false;
  applyDraftToInputs(state);
  READONLY_FIELDS.forEach((field) => {
    const node = state.readonlyNodes.get(field.key);
    if (node) node.textContent = "—";
  });
  setPopupVisibility(state, false);
  syncUrl("", "new");
  setTextWithState(state.contextNode, t(state, "new_context_loaded", "Creating a draft work source record."));
  setTextWithState(state.statusNode, "");
  setTextWithState(state.warningNode, "");
  if (!options.keepResult) {
    setTextWithState(state.resultNode, "");
  }
  updateEditorState(state);
}

function setEmptySearchMode(state, options = {}) {
  state.mode = "single";
  state.currentWorkId = "";
  state.currentRecord = null;
  state.currentLookup = null;
  state.currentRecordHash = "";
  state.bulkWorkIds = [];
  state.bulkRecords = new Map();
  state.bulkRecordHashes = new Map();
  state.bulkMixedFields = new Set();
  state.bulkTouchedFields = new Set();
  state.bulkBuildTargets = [];
  state.baselineDraft = null;
  state.draft = {};
  EDITABLE_FIELDS.forEach((field) => {
    state.draft[field.key] = "";
  });
  state.draft.downloads = [];
  state.draft.links = [];
  state.detailSearchNode.value = "";
  state.pendingBuildExtraSeriesIds = [];
  state.rebuildPending = false;
  state.buildPreview = null;
  setOpenInputMode(state);
  if (!options.keepSearchValue) {
    state.searchNode.value = "";
  }
  if (state.applyBuildNode) state.applyBuildNode.checked = true;
  applyDraftToInputs(state);
  READONLY_FIELDS.forEach((field) => {
    const node = state.readonlyNodes.get(field.key);
    if (node) node.textContent = "—";
  });
  setPopupVisibility(state, false);
  syncUrl("");
  setTextWithState(state.contextNode, t(state, "missing_work_param", "Search for a work by work id."));
  setTextWithState(state.warningNode, "");
  if (!options.keepResult) {
    setTextWithState(state.resultNode, "");
  }
  updateEditorState(state);
}

function updateEditorState(state) {
  const hasRecord = state.mode === "new" ? true : state.mode === "bulk" ? state.bulkWorkIds.length > 0 : Boolean(state.currentRecord);
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
      : state.bulkWorkIds.map((workId) => ({ work_id: workId, extra_series_ids: [] }));
    setTextWithState(
      state.buildImpactNode,
      t(state, "bulk_build_preview", "Build preview: {count} work scopes will be rebuilt.", {
        count: String(previewTargets.length)
      })
    );
  }

  const dirty = hasRecord && draftHasChanges(state);
  setTextWithState(state.warningNode, dirty ? t(state, "dirty_warning", "Unsaved source changes.") : "");
  if (state.mode === "new" && !state.resultNode.textContent) {
    setTextWithState(
      state.statusNode,
      state.serverAvailable
        ? t(state, "new_status_ready", "Create a draft work source record.")
        : t(state, "save_mode_unavailable_hint", "Local catalogue server unavailable. Save is disabled."),
      state.serverAvailable ? "" : "warn"
    );
  } else if (!dirty && !errors.size && !state.resultNode.textContent && hasRecord) {
    setTextWithState(
      state.statusNode,
      state.mode === "bulk"
        ? t(state, "bulk_status_loaded", "Loaded {count} work records.", { count: String(state.bulkWorkIds.length) })
        : t(state, "save_status_loaded", "Loaded work {work_id}.", { work_id: state.currentWorkId })
    );
  }

  state.saveButton.textContent = state.mode === "new"
    ? t(state, "create_button", "Create")
    : t(state, "save_button", "Save");
  state.saveButton.disabled = !hasRecord || state.isSaving || errors.size > 0 || !dirty || !state.serverAvailable;
  state.deleteButton.disabled = !Boolean(state.currentRecord) || state.mode === "bulk" || state.isSaving || state.isBuilding || state.isDeleting || !state.serverAvailable;
  updatePublishControls(state, { hasRecord, dirty, errors });
  renderReadiness(state);
}

function onFieldInput(state, fieldKey) {
  const node = state.fieldNodes.get(fieldKey);
  if (!node) return;
  if (state.mode === "new" && fieldKey === "status") {
    state.draft.status = "draft";
    node.value = "draft";
    updateEditorState(state);
    return;
  }
  if (state.mode === "new" && fieldKey === "published_date") {
    state.draft.published_date = "";
    node.value = "";
    updateEditorState(state);
    return;
  }
  state.draft[fieldKey] = node.value;
  if (state.mode === "bulk") {
    state.bulkTouchedFields.add(fieldKey);
  }
  updateEditorState(state);
}

function t(state, key, fallback, tokens = null) {
  return getStudioText(state.config, `catalogue_work_editor.${key}`, fallback, tokens);
}

async function saveCurrentWork(state) {
  if (state.mode === "new") {
    await createCurrentWork(state);
    return;
  }
  if (state.mode === "bulk") {
    if (!state.bulkWorkIds.length) return;
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
    if (applyBuildRequested(state) && state.rebuildPending) {
      await buildCurrentWork(state);
      return;
    }
    setTextWithState(state.statusNode, t(state, "save_status_no_changes", "No changes to save."));
    setTextWithState(state.resultNode, t(state, "save_result_unchanged", "Source already matches the current form values."));
    updateEditorState(state);
    return;
  }

  state.isSaving = true;
  state.saveButton.disabled = true;
  state.buildButton.disabled = true;
  setTextWithState(
    state.statusNode,
    applyBuildRequested(state)
      ? t(state, "save_status_saving_and_updating", "Saving source record and updating site…")
      : t(state, "save_status_saving", "Saving source record…")
  );
  setTextWithState(state.resultNode, "");

  try {
    if (state.mode === "bulk") {
      const response = await postJson(CATALOGUE_WRITE_ENDPOINTS.bulkSave, buildPayload(state));
      const changedRecords = Array.isArray(response && response.records) ? response.records : [];
      changedRecords.forEach((item) => {
        const workId = normalizeWorkId(item && item.work_id);
        const record = item && item.record && typeof item.record === "object" ? item.record : null;
        if (!workId || !record) return;
        state.sourceWorkRecordsById.set(workId, record);
        state.bulkRecords.set(workId, record);
        state.bulkRecordHashes.set(workId, normalizeText(item.record_hash) || "");
        state.workSearchById.set(workId, {
          work_id: workId,
          title: normalizeText(record.title),
          year_display: normalizeText(record.year_display),
          status: normalizeText(record.status),
          series_ids: Array.isArray(record.series_ids) ? record.series_ids.slice() : [],
          record_hash: normalizeText(item.record_hash)
        });
      });
      const fallbackBuildTargets = Array.isArray(response && response.build_targets) ? response.build_targets : [];
      const outcome = applyBulkSaveBuildOutcome(state, response, fallbackBuildTargets);
      setLoadedBulkWorks(state, state.bulkWorkIds, state.bulkRecords, state.bulkRecordHashes, {
        keepResult: true,
        buildTargets: state.bulkBuildTargets
      });
      if (outcome.kind === "saved_and_updated") {
        setTextWithState(
          state.resultNode,
          t(state, "bulk_save_result_success_applied", "Saved {count} work records and updated the public catalogue at {saved_at}.", {
            count: String(response.changed_count || 0),
            saved_at: outcome.stamp
          }),
          "success"
        );
        setTextWithState(state.statusNode, t(state, "build_status_success", "Site update completed."), "success");
      } else if (outcome.kind === "saved_update_failed") {
        setTextWithState(
          state.resultNode,
          t(state, "bulk_save_result_success_partial", "Saved {count} work records at {saved_at}, but the site update failed. Retry Update site now.", {
            count: String(response.changed_count || 0),
            saved_at: outcome.stamp
          }),
          "warn"
        );
        setTextWithState(state.statusNode, `${t(state, "build_status_failed", "Site update failed.")} ${outcome.error}`.trim(), "error");
      } else {
        setTextWithState(
          state.resultNode,
          response.changed
            ? t(state, "bulk_save_result_success", "Saved {count} work records at {saved_at}. Public catalogue update still pending.", {
              count: String(response.changed_count || 0),
              saved_at: outcome.stamp
            })
            : t(state, "save_result_unchanged", "Source already matches the current form values."),
          response.changed ? "success" : ""
        );
        setTextWithState(
          state.statusNode,
          t(state, "bulk_status_loaded", "Loaded {count} work records.", { count: String(state.bulkWorkIds.length) }),
          response.changed ? "success" : ""
        );
      }
      return;
    }

    const previousSeriesIds = parseSeriesIds(state.baselineDraft && state.baselineDraft.series_ids);
    const nextSeriesIds = parseSeriesIds(state.draft.series_ids);
    const payload = buildPayload(state);
    const response = await postJson(CATALOGUE_WRITE_ENDPOINTS.saveWork, payload);
    const record = response && response.record && typeof response.record === "object" ? response.record : null;
    if (!record) {
      throw new Error("save response missing record");
    }
    state.sourceWorkRecordsById.set(state.currentWorkId, record);
    state.workSearchById.set(state.currentWorkId, {
      work_id: state.currentWorkId,
      title: normalizeText(record.title),
      year_display: normalizeText(record.year_display),
      status: normalizeText(record.status),
      series_ids: Array.isArray(record.series_ids) ? record.series_ids.slice() : [],
      record_hash: normalizeText(response.record_hash)
    });
    const outcome = applySingleSaveBuildOutcome(state, response);
    if (response.changed && outcome.kind !== "saved_and_updated") {
      state.pendingBuildExtraSeriesIds = dedupeSeriesIds([
        ...state.pendingBuildExtraSeriesIds,
        ...previousSeriesIds,
        ...nextSeriesIds
      ]).filter((seriesId) => !nextSeriesIds.includes(seriesId));
    }
    const lookup = await loadWorkLookupRecord(state, state.currentWorkId);
    setLoadedRecord(state, state.currentWorkId, record, {
      recordHash: response.record_hash || normalizeText(lookup && lookup.record_hash) || "",
      keepResult: true,
      lookup
    });
    await refreshBuildPreview(state);
    if (outcome.kind === "saved_and_updated") {
      setTextWithState(
        state.resultNode,
        t(state, "save_result_success_applied", "Saved source changes and updated the public catalogue at {saved_at}.", { saved_at: outcome.stamp }),
        "success"
      );
      setTextWithState(state.statusNode, t(state, "build_status_success", "Site update completed."), "success");
    } else if (outcome.kind === "saved_update_failed") {
      setTextWithState(
        state.resultNode,
        t(state, "save_result_success_partial", "Source changes were saved at {saved_at}, but the site update failed. Retry Update site now.", { saved_at: outcome.stamp }),
        "warn"
      );
      setTextWithState(state.statusNode, `${t(state, "build_status_failed", "Site update failed.")} ${outcome.error}`.trim(), "error");
    } else {
      setTextWithState(
        state.resultNode,
        response.changed
          ? t(state, "save_result_success", "Source saved at {saved_at}. Public catalogue update still pending.", { saved_at: outcome.stamp })
          : t(state, "save_result_unchanged", "Source already matches the current form values."),
        response.changed ? "success" : ""
      );
      setTextWithState(state.statusNode, t(state, "save_status_loaded", "Loaded work {work_id}.", { work_id: state.currentWorkId }), "success");
    }
  } catch (error) {
    const isConflict = Number(error && error.status) === 409;
    const message = isConflict
      ? t(state, "save_status_conflict", "Source record changed since this page loaded. Reload the work before saving again.")
      : `${t(state, "save_status_failed", "Source save failed.")} ${normalizeText(error && error.message)}`.trim();
    setTextWithState(state.statusNode, message, "error");
  } finally {
    state.isSaving = false;
    updateEditorState(state);
  }
}

async function createCurrentWork(state) {
  if (state.mode !== "new") return;
  const errors = validateDraft(state);
  updateFieldMessages(state, errors);
  if (errors.size > 0) {
    const workIdError = errors.get("work_id") || "";
    setTextWithState(
      state.statusNode,
      workIdError || t(state, "create_status_validation_error", "Fix validation errors before creating the draft work."),
      "error"
    );
    updateEditorState(state);
    return;
  }

  state.isSaving = true;
  updateEditorState(state);
  setTextWithState(state.statusNode, t(state, "create_status_saving", "Creating draft work..."));
  setTextWithState(state.resultNode, "");

  try {
    const response = await postJson(CATALOGUE_WRITE_ENDPOINTS.createWork, buildCreateWorkPayload(state.draft));
    const workId = normalizeWorkId(response && response.work_id);
    const record = response && response.record && typeof response.record === "object" ? response.record : null;
    if (!workId) {
      throw new Error("create response missing work id");
    }
    if (record) {
      state.sourceWorkRecordsById.set(workId, record);
      state.workSearchById.set(workId, {
        work_id: workId,
        title: normalizeText(record.title),
        year_display: normalizeText(record.year_display),
        status: normalizeText(record.status),
        series_ids: Array.isArray(record.series_ids) ? record.series_ids.slice() : [],
        record_hash: normalizeText(response.record_hash)
      });
    }
    state.isSaving = false;
    await openWorkById(state, workId);
    setTextWithState(state.resultNode, t(state, "create_result_success", "Created draft work {work_id}. Opening edit mode...", { work_id: workId }), "success");
    setTextWithState(state.statusNode, t(state, "create_status_success", "Created draft work {work_id}.", { work_id: workId }), "success");
  } catch (error) {
    setTextWithState(state.statusNode, `${t(state, "create_status_failed", "Draft work create failed.")} ${normalizeText(error && error.message)}`.trim(), "error");
    state.isSaving = false;
    updateEditorState(state);
  }
}

async function refreshBuildPreview(state) {
  if (state.mode === "bulk") {
    const previewTargets = state.rebuildPending && state.bulkBuildTargets.length
      ? state.bulkBuildTargets
      : state.bulkWorkIds.map((workId) => ({ work_id: workId, extra_series_ids: [] }));
    setTextWithState(
      state.buildImpactNode,
      previewTargets.length
        ? t(state, "bulk_build_preview", "Build preview: {count} work scopes will be rebuilt.", {
          count: String(previewTargets.length)
        })
        : ""
    );
    state.buildPreview = null;
    renderCurrentPreview(state);
    renderReadiness(state);
    return;
  }
  if (!state.currentWorkId || !state.serverAvailable) {
    setTextWithState(state.buildImpactNode, "");
    state.buildPreview = null;
    renderCurrentPreview(state);
    renderReadiness(state);
    return;
  }
  try {
    const response = await postJson(CATALOGUE_WRITE_ENDPOINTS.buildPreview, {
      work_id: state.currentWorkId,
      extra_series_ids: state.pendingBuildExtraSeriesIds
    });
    state.buildPreview = response && response.build ? response.build : null;
    setTextWithState(state.buildImpactNode, formatBuildPreview(state, state.buildPreview));
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

async function importWorkProse(state) {
  if (!state.currentRecord || !state.currentWorkId || !state.serverAvailable) return;
  if (draftHasChanges(state)) {
    setTextWithState(state.statusNode, t(state, "prose_import_save_first", "Save source changes before importing prose."), "error");
    return;
  }

  state.isBuilding = true;
  updateEditorState(state);
  setTextWithState(state.statusNode, t(state, "prose_import_preview_running", "Previewing staged prose…"));
  setTextWithState(state.resultNode, "");
  try {
    const preview = await postJson(CATALOGUE_WRITE_ENDPOINTS.previewProseImport, {
      target_kind: "work",
      work_id: state.currentWorkId
    });
    if (!preview.valid) {
      const errors = Array.isArray(preview.errors) ? preview.errors.join(" ") : "";
      throw new Error(errors || t(state, "prose_import_preview_invalid", "Staged prose is not ready to import."));
    }
    let confirmOverwrite = false;
    if (preview.overwrite_required) {
      const message = t(
        state,
        "prose_import_confirm_overwrite",
        "Overwrite existing prose source at {target_path} with staged file {staging_path}?",
        {
          target_path: normalizeText(preview.target_path),
          staging_path: normalizeText(preview.staging_path)
        }
      );
      confirmOverwrite = window.confirm(message);
      if (!confirmOverwrite) {
        setTextWithState(state.statusNode, t(state, "prose_import_overwrite_cancelled", "Prose import cancelled."), "warning");
        return;
      }
    }
    setTextWithState(state.statusNode, t(state, "prose_import_running", "Importing staged prose…"));
    const importResponse = await postJson(CATALOGUE_WRITE_ENDPOINTS.applyProseImport, {
      target_kind: "work",
      work_id: state.currentWorkId,
      confirm_overwrite: confirmOverwrite
    });
    await refreshBuildPreview(state);
    const completedAt = normalizeText(importResponse.imported_at_utc || utcTimestamp());
    setTextWithState(
      state.resultNode,
      t(state, "prose_import_result_success", "Prose imported to {target_path} at {completed_at}. The next site update will publish it.", {
        completed_at: completedAt,
        target_path: normalizeText(importResponse.target_path)
      }),
      "success"
    );
    setTextWithState(state.statusNode, t(state, "prose_import_status_success", "Prose import completed."), "success");
  } catch (error) {
    setTextWithState(
      state.statusNode,
      `${t(state, "prose_import_status_failed", "Prose import failed.")} ${normalizeText(error && error.message)}`.trim(),
      "error"
    );
  } finally {
    state.isBuilding = false;
    updateEditorState(state);
  }
}

async function buildCurrentWork(state) {
  if (state.mode === "bulk") {
    if (!state.bulkWorkIds.length || !state.serverAvailable) return;
  } else if (!state.currentRecord || !state.serverAvailable) {
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
        : state.bulkWorkIds.map((workId) => ({ work_id: workId, extra_series_ids: [] }));
      for (const target of buildTargets) {
        await postJson(CATALOGUE_WRITE_ENDPOINTS.buildApply, {
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
        t(state, "bulk_build_result_success", "Updated {count} work scopes at {completed_at}. Build Activity updated.", {
          count: String(buildTargets.length),
          completed_at: completedAt
        }),
        "success"
      );
      setTextWithState(state.statusNode, t(state, "build_status_success", "Site update completed."), "success");
      return;
    }

    const response = await postJson(CATALOGUE_WRITE_ENDPOINTS.buildApply, {
      work_id: state.currentWorkId,
      extra_series_ids: state.pendingBuildExtraSeriesIds
    });
    state.rebuildPending = false;
    state.pendingBuildExtraSeriesIds = [];
    await refreshBuildPreview(state);
    const completedAt = normalizeText(response.completed_at_utc || utcTimestamp());
    setTextWithState(
      state.resultNode,
      t(state, "build_result_success", "Public catalogue updated at {completed_at}. Build Activity updated.", { completed_at: completedAt }),
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

function countMediaItems(media, group) {
  const values = media && media[group] && typeof media[group] === "object" ? media[group] : {};
  return Object.values(values).reduce((total, items) => total + (Array.isArray(items) ? items.length : 0), 0);
}

async function refreshWorkMedia(state) {
  if (!state.currentRecord || !state.currentWorkId || !state.serverAvailable || draftHasChanges(state)) return;
  state.isBuilding = true;
  updateEditorState(state);
  setTextWithState(state.statusNode, t(state, "media_refresh_status_running", "Refreshing media…"));
  setTextWithState(state.resultNode, "");
  try {
    const response = await postJson(CATALOGUE_WRITE_ENDPOINTS.buildApply, {
      work_id: state.currentWorkId,
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

async function deleteCurrentWork(state) {
  if (!state.currentRecord || state.mode === "bulk" || !state.serverAvailable) return;
  state.isDeleting = true;
  updateEditorState(state);
  setTextWithState(state.statusNode, t(state, "delete_status_running", "Preparing delete preview…"));
  setTextWithState(state.resultNode, "");
  try {
    const previewResponse = await postJson(CATALOGUE_WRITE_ENDPOINTS.deletePreview, {
      kind: "work",
      work_id: state.currentWorkId,
      expected_record_hash: state.currentRecordHash
    });
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
    const summary = normalizeText(preview && preview.summary) || t(state, "delete_confirm_default", "Delete this source record?");
    if (!window.confirm(summary)) {
      setTextWithState(state.statusNode, t(state, "delete_status_cancelled", "Delete cancelled."));
      state.isDeleting = false;
      updateEditorState(state);
      return;
    }
    setTextWithState(state.statusNode, t(state, "delete_status_running", "Deleting source record…"));
    await postJson(CATALOGUE_WRITE_ENDPOINTS.deleteApply, {
      kind: "work",
      work_id: state.currentWorkId,
      expected_record_hash: state.currentRecordHash
    });
    const route = getStudioRoute(state.config, "catalogue_status");
    window.location.assign(route);
  } catch (error) {
    const message = Number(error && error.status) === 409
      ? t(state, "delete_status_conflict", "Source record changed since this page loaded. Reload before deleting again.")
      : `${t(state, "delete_status_failed", "Source delete failed.")} ${normalizeText(error && error.message)}`.trim();
    setTextWithState(state.statusNode, message, "error");
    state.isDeleting = false;
    updateEditorState(state);
  }
}

async function openWorkSelection(state, requestedValue) {
  let workIds;
  try {
    workIds = parseWorkSelection(requestedValue);
  } catch (error) {
    renderSearchMatches(state, [], normalizeText(error && error.message) || t(state, "search_empty", "Enter a work id."));
    return;
  }

  if (!workIds.length) {
    renderSearchMatches(state, [], t(state, "search_empty", "Enter a work id."));
    return;
  }
  if (workIds.length === 1) {
    await openWorkById(state, workIds[0]);
    return;
  }

  const unknown = workIds.find((workId) => !state.workSearchById.has(workId));
  if (unknown) {
    renderSearchMatches(state, [], t(state, "unknown_work_error", "Unknown work id: {work_id}.", { work_id: unknown }));
    return;
  }

  state.searchNode.value = workIds.join(", ");
  state.detailSearchNode.value = "";
  setPopupVisibility(state, false);
  state.pendingBuildExtraSeriesIds = [];
  state.rebuildPending = false;
  const lookups = await Promise.all(workIds.map((workId) => loadWorkLookupRecord(state, workId)));
  const recordsById = new Map();
  const recordHashes = new Map();
  for (let index = 0; index < workIds.length; index += 1) {
    const workId = workIds[index];
    const lookup = lookups[index];
    const fallbackRecord = lookup && lookup.work && typeof lookup.work === "object" ? lookup.work : null;
    const record = getSourceWorkRecord(state, workId, fallbackRecord);
    if (!record) {
      throw new Error(`work source missing record for ${workId}`);
    }
    recordsById.set(workId, record);
    recordHashes.set(workId, await computeRecordHash(record));
  }
  setLoadedBulkWorks(state, workIds, recordsById, recordHashes);
  await refreshBuildPreview(state);
}

async function openWorkById(state, requestedWorkId) {
  const workId = normalizeWorkId(requestedWorkId);
  if (!workId) {
    renderSearchMatches(state, [], t(state, "search_empty", "Enter a work id."));
    return;
  }

  const searchRecord = state.workSearchById.get(workId);
  if (!searchRecord) {
    const matches = getSearchMatches(state, requestedWorkId);
    if (matches.length) {
      renderSearchMatches(state, matches);
    } else {
      renderSearchMatches(state, [], t(state, "unknown_work_error", "Unknown work id: {work_id}.", { work_id }));
    }
    return;
  }

  state.searchNode.value = workId;
  state.detailSearchNode.value = "";
  setPopupVisibility(state, false);
  state.pendingBuildExtraSeriesIds = [];
  state.rebuildPending = false;
  const lookup = await loadWorkLookupRecord(state, workId);
  const fallbackRecord = lookup && lookup.work && typeof lookup.work === "object" ? lookup.work : null;
  const record = getSourceWorkRecord(state, workId, fallbackRecord);
  if (!record) {
    throw new Error(`work source missing record for ${workId}`);
  }
  setLoadedRecord(state, workId, record, {
    recordHash: await computeRecordHash(record),
    lookup
  });
  await refreshBuildPreview(state);
}

async function init() {
  const root = document.getElementById("catalogueWorkRoot");
  const loadingNode = document.getElementById("catalogueWorkLoading");
  const emptyNode = document.getElementById("catalogueWorkEmpty");
  const fieldsNode = document.getElementById("catalogueWorkFields");
  const readonlyNode = document.getElementById("catalogueWorkReadonly");
  const previewNode = document.getElementById("catalogueWorkPreview");
  const summaryNode = document.getElementById("catalogueWorkSummary");
  const readinessNode = document.getElementById("catalogueWorkReadiness");
  const runtimeStateNode = document.getElementById("catalogueWorkRuntimeState");
  const buildImpactNode = document.getElementById("catalogueWorkBuildImpact");
  const detailsHeadingNode = document.getElementById("catalogueWorkDetailsHeading");
  const newDetailLinkNode = document.getElementById("catalogueWorkNewDetailLink");
  const detailSearchRowNode = document.getElementById("catalogueWorkDetailsSearchRow");
  const detailSearchNode = document.getElementById("catalogueWorkDetailSearch");
  const detailsMetaNode = document.getElementById("catalogueWorkDetailsMeta");
  const detailsResultsNode = document.getElementById("catalogueWorkDetailsResults");
  const filesHeadingNode = document.getElementById("catalogueWorkFilesHeading");
  const newFileLinkNode = document.getElementById("catalogueWorkNewFileLink");
  const filesMetaNode = document.getElementById("catalogueWorkFilesMeta");
  const filesResultsNode = document.getElementById("catalogueWorkFilesResults");
  const linksHeadingNode = document.getElementById("catalogueWorkLinksHeading");
  const newLinkLinkNode = document.getElementById("catalogueWorkNewLinkLink");
  const linksMetaNode = document.getElementById("catalogueWorkLinksMeta");
  const linksResultsNode = document.getElementById("catalogueWorkLinksResults");
  const searchNode = document.getElementById("catalogueWorkSearch");
  const popupNode = document.getElementById("catalogueWorkPopup");
  const popupListNode = document.getElementById("catalogueWorkPopupList");
  const openButton = document.getElementById("catalogueWorkOpen");
  const newButton = document.getElementById("catalogueWorkNew");
  const saveButton = document.getElementById("catalogueWorkSave");
  const buildButton = document.getElementById("catalogueWorkBuild");
  const deleteButton = document.getElementById("catalogueWorkDelete");
  const runtimeActionsNode = buildButton ? buildButton.closest(".catalogueWorkPage__runtimeActions") : null;
  const applyBuildNode = document.getElementById("catalogueWorkApplyBuild");
  const applyBuildLabelNode = document.getElementById("catalogueWorkApplyBuildLabel");
  const saveModeNode = document.getElementById("catalogueWorkSaveMode");
  const contextNode = document.getElementById("catalogueWorkContext");
  const statusNode = document.getElementById("catalogueWorkStatus");
  const warningNode = document.getElementById("catalogueWorkWarning");
  const resultNode = document.getElementById("catalogueWorkResult");
  const metaNode = document.getElementById("catalogueWorkMeta");
  if (!root || !loadingNode || !emptyNode || !fieldsNode || !readonlyNode || !previewNode || !summaryNode || !readinessNode || !runtimeStateNode || !buildImpactNode || !detailsHeadingNode || !newDetailLinkNode || !detailSearchRowNode || !detailSearchNode || !detailsMetaNode || !detailsResultsNode || !filesHeadingNode || !newFileLinkNode || !filesMetaNode || !filesResultsNode || !linksHeadingNode || !newLinkLinkNode || !linksMetaNode || !linksResultsNode || !searchNode || !popupNode || !popupListNode || !openButton || !newButton || !saveButton || !buildButton || !deleteButton || !runtimeActionsNode || !applyBuildNode || !applyBuildLabelNode || !saveModeNode || !contextNode || !statusNode || !warningNode || !resultNode || !metaNode) {
    return;
  }

  const state = {
    root,
    config: null,
    mode: "single",
    workSearchById: new Map(),
    seriesById: new Map(),
    sourceWorkRecordsById: new Map(),
    currentLookup: null,
    currentWorkId: "",
    currentRecord: null,
    currentRecordHash: "",
    nextSuggestedWorkId: "",
    bulkWorkIds: [],
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
    pendingBuildExtraSeriesIds: [],
    buildPreview: null,
    isSaving: false,
    isBuilding: false,
    isDeleting: false,
    serverAvailable: false,
    modalHost: createStudioModalHost({ root }),
    activeModalKeydown: null,
    fieldNodes: new Map(),
    fieldStatusNodes: new Map(),
    readonlyNodes: new Map(),
    searchNode,
    popupNode,
    popupListNode,
    openButton,
    newButton,
    saveButton,
    buildButton,
    deleteButton,
    applyBuildNode,
    applyBuildLabelNode,
    runtimeActionsNode,
    saveModeNode,
    contextNode,
    statusNode,
    warningNode,
    resultNode,
    previewNode,
    summaryNode,
    readinessNode,
    runtimeStateNode,
    buildImpactNode,
    detailSearchRowNode,
    detailSearchNode,
    detailsMetaNode,
    detailsResultsNode,
    detailsPanelNode: detailsResultsNode.closest("section"),
    newDetailLinkNode,
    filesMetaNode,
    filesResultsNode,
    filesPanelNode: filesResultsNode.closest("section"),
    newFileLinkNode,
    linksMetaNode,
    linksResultsNode,
    linksPanelNode: linksResultsNode.closest("section"),
    newLinkLinkNode,
    metaNode
  };

  EDITABLE_FIELDS.forEach((field) => renderField(field, fieldsNode, state));
  READONLY_FIELDS.forEach((field) => renderReadonlyField(field, readonlyNode, state));

  try {
    const config = await loadStudioConfig();
    state.config = config;
    setOpenInputMode(state);
    detailsHeadingNode.textContent = t(state, "details_heading", "work details");
    newDetailLinkNode.textContent = t(state, "details_new_link", "new work detail →");
    detailSearchNode.placeholder = t(state, "details_search_placeholder", "find detail by id");
    filesHeadingNode.textContent = t(state, "files_heading", "downloads");
    newFileLinkNode.textContent = t(state, "files_add_button", "Add file");
    linksHeadingNode.textContent = t(state, "links_heading", "links");
    newLinkLinkNode.textContent = t(state, "links_add_button", "Add link");
    openButton.textContent = t(state, "open_button", "Open");
    newButton.textContent = t(state, "new_button", "New");
    saveButton.textContent = t(state, "save_button", "Save");
    buildButton.textContent = t(state, "build_button", "Update site now");
    applyBuildLabelNode.textContent = t(state, "build_button", "Update site now");
    deleteButton.textContent = t(state, "delete_button", "Delete");

    const [worksPayload, worksSourcePayload, seriesPayload, serverAvailable] = await Promise.all([
      loadStudioLookupJson(config, "catalogue_lookup_work_search", { cache: "no-store" }),
      loadStudioLookupJson(config, "catalogue_works", { cache: "no-store" }),
      loadStudioLookupJson(config, "catalogue_lookup_series_search", { cache: "no-store" }),
      probeCatalogueHealth()
    ]);

    const workItems = Array.isArray(worksPayload && worksPayload.items) ? worksPayload.items : [];
    state.nextSuggestedWorkId = suggestNextWorkId(workItems);
    workItems.forEach((record) => {
      if (!record || typeof record !== "object") return;
      const workId = normalizeWorkId(record.work_id);
      if (!workId) return;
      state.workSearchById.set(workId, record);
    });
    state.sourceWorkRecordsById = buildSourceWorkMap(worksSourcePayload);
    const seriesItems = Array.isArray(seriesPayload && seriesPayload.items) ? seriesPayload.items : [];
    seriesItems.forEach((record) => {
      if (!record || typeof record !== "object") return;
      const seriesId = normalizeSeriesId(record.series_id);
      if (!seriesId) return;
      state.seriesById.set(seriesId, record);
    });
    state.serverAvailable = Boolean(serverAvailable);
    saveModeNode.textContent = buildSaveModeText(config, serverAvailable ? "post" : "offline", (cfg, key, fallback, tokens) => getStudioText(cfg, `catalogue_work_editor.${key}`, fallback, tokens));
    if (!state.serverAvailable) {
      setTextWithState(statusNode, t(state, "save_mode_unavailable_hint", "Local catalogue server unavailable. Save is disabled."), "warn");
    }

    searchNode.addEventListener("input", () => {
      const query = searchNode.value;
      if (state.mode === "new") {
        state.draft.work_id = normalizeWorkId(query);
        setPopupVisibility(state, false);
        updateEditorState(state);
        return;
      }
      if (!normalizeText(query)) {
        renderSearchMatches(state, [], "");
        return;
      }
      if (isWorkBulkQuery(query)) {
        renderSearchMatches(state, [], "");
        return;
      }
      const matches = getSearchMatches(state, query);
      if (!matches.length) {
        renderSearchMatches(state, [], t(state, "search_no_match", "No matching work ids."));
        return;
      }
      renderSearchMatches(state, matches);
    });

    searchNode.addEventListener("keydown", (event) => {
      if (event.key !== "Enter") return;
      event.preventDefault();
      if (state.mode === "new") {
        saveCurrentWork(state).catch((error) => {
          console.warn("catalogue_work_editor: unexpected create failure", error);
        });
        return;
      }
      openWorkSelection(state, searchNode.value).catch((error) => {
        console.warn("catalogue_work_editor: failed to open requested work selection", error);
      });
    });

    detailSearchNode.addEventListener("input", () => {
      updateDetailSections(state);
    });

    newFileLinkNode.addEventListener("click", () => openEmbeddedEntryModal(state, "download"));
    newLinkLinkNode.addEventListener("click", () => openEmbeddedEntryModal(state, "link"));

    filesResultsNode.addEventListener("click", (event) => {
      const editButton = event.target && event.target.closest ? event.target.closest("[data-download-edit]") : null;
      if (editButton) {
        openEmbeddedEntryModal(state, "download", Number(editButton.getAttribute("data-download-edit")));
        return;
      }
      const deleteButtonNode = event.target && event.target.closest ? event.target.closest("[data-download-delete]") : null;
      if (deleteButtonNode) {
        deleteEmbeddedEntry(state, "download", Number(deleteButtonNode.getAttribute("data-download-delete"))).catch((error) => {
          console.warn("catalogue_work_editor: failed to delete download", error);
        });
      }
    });

    linksResultsNode.addEventListener("click", (event) => {
      const editButton = event.target && event.target.closest ? event.target.closest("[data-link-edit]") : null;
      if (editButton) {
        openEmbeddedEntryModal(state, "link", Number(editButton.getAttribute("data-link-edit")));
        return;
      }
      const deleteButtonNode = event.target && event.target.closest ? event.target.closest("[data-link-delete]") : null;
      if (deleteButtonNode) {
        deleteEmbeddedEntry(state, "link", Number(deleteButtonNode.getAttribute("data-link-delete"))).catch((error) => {
          console.warn("catalogue_work_editor: failed to delete link", error);
        });
      }
    });

    popupListNode.addEventListener("click", (event) => {
      const button = event.target && event.target.closest ? event.target.closest("[data-work-id]") : null;
      if (!button) return;
      openWorkById(state, button.getAttribute("data-work-id")).catch((error) => {
        console.warn("catalogue_work_editor: failed to open selected work", error);
      });
    });

    openButton.addEventListener("click", () => {
      if (state.mode === "new") {
        setEmptySearchMode(state, { keepSearchValue: true });
      }
      openWorkSelection(state, searchNode.value).catch((error) => {
        console.warn("catalogue_work_editor: failed to open requested work selection", error);
      });
    });
    newButton.addEventListener("click", () => {
      setNewWorkMode(state);
    });
    readinessNode.addEventListener("click", (event) => {
      const mediaButton = event.target && event.target.closest ? event.target.closest("[data-media-refresh]") : null;
      if (mediaButton) {
        refreshWorkMedia(state).catch((error) => {
          console.warn("catalogue_work_editor: unexpected media refresh failure", error);
        });
        return;
      }
      const proseButton = event.target && event.target.closest ? event.target.closest("[data-prose-import]") : null;
      if (!proseButton) return;
      importWorkProse(state).catch((error) => {
        console.warn("catalogue_work_editor: unexpected prose import failure", error);
      });
    });
    saveButton.addEventListener("click", () => saveCurrentWork(state).catch((error) => {
      console.warn("catalogue_work_editor: unexpected save failure", error);
    }));
    buildButton.addEventListener("click", () => buildCurrentWork(state).catch((error) => {
      console.warn("catalogue_work_editor: unexpected save/build failure", error);
    }));
    deleteButton.addEventListener("click", () => deleteCurrentWork(state).catch((error) => {
      console.warn("catalogue_work_editor: unexpected delete failure", error);
    }));

    document.addEventListener("click", (event) => {
      if (event.target === searchNode || popupNode.contains(event.target)) return;
      setPopupVisibility(state, false);
    });

    const params = new URLSearchParams(window.location.search);
    const requestedMode = normalizeText(params.get("mode")).toLowerCase();
    const requestedWorkValue = normalizeText(params.get("work"));
    if (requestedWorkValue) {
      openWorkSelection(state, requestedWorkValue).catch((error) => {
        console.warn("catalogue_work_editor: failed to open requested work selection", error);
      });
    } else if (requestedMode === "new") {
      setNewWorkMode(state);
    } else {
      setEmptySearchMode(state);
    }

    root.hidden = false;
    loadingNode.hidden = true;
  } catch (error) {
    console.warn("catalogue_work_editor: init failed", error);
    try {
      const config = await loadStudioConfig();
      loadingNode.textContent = getStudioText(config, "catalogue_work_editor.load_failed_error", "Failed to load catalogue source data for the work editor.");
    } catch (_configError) {
      loadingNode.textContent = "Failed to load catalogue source data for the work editor.";
    }
  }
}

init();
