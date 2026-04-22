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

const EDITABLE_FIELDS = [
  { key: "status", label: "status", type: "select", options: ["", "draft", "published"] },
  { key: "published_date", label: "published date", type: "date" },
  { key: "series_ids", label: "series ids", type: "text", description: "comma-separated series ids" },
  { key: "project_folder", label: "project folder", type: "text" },
  { key: "project_filename", label: "project filename", type: "text" },
  { key: "title", label: "title", type: "text" },
  { key: "year", label: "year", type: "number", step: "1" },
  { key: "year_display", label: "year display", type: "text" },
  { key: "medium_type", label: "medium type", type: "text" },
  { key: "medium_caption", label: "medium caption", type: "text" },
  { key: "duration", label: "duration", type: "text" },
  { key: "height_cm", label: "height cm", type: "number", step: "any" },
  { key: "width_cm", label: "width cm", type: "number", step: "any" },
  { key: "depth_cm", label: "depth cm", type: "number", step: "any" },
  { key: "storage_location", label: "storage location", type: "text" },
  { key: "work_prose_file", label: "work prose file", type: "text" },
  { key: "notes", label: "notes", type: "textarea" },
  { key: "provenance", label: "provenance", type: "textarea" },
  { key: "artist", label: "artist", type: "text" }
];

const READONLY_FIELDS = [
  { key: "work_id", label: "work id" },
  { key: "width_px", label: "width px" },
  { key: "height_px", label: "height px" }
];

const STATUS_OPTIONS = new Set(["", "draft", "published"]);
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const SERIES_ID_RE = /^\d+$/;
const SEARCH_LIMIT = 20;
const DETAIL_LIST_LIMIT = 10;
const BULK_PREVIEW_LIMIT = 12;

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

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

function normalizeWorkId(value) {
  const digits = normalizeText(value).replace(/\D/g, "");
  if (!digits) return "";
  return digits.padStart(5, "0");
}

function normalizeSeriesId(value) {
  const digits = normalizeText(value).replace(/\D/g, "");
  if (!digits) return "";
  return digits.padStart(3, "0");
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

function seriesIdsToText(value) {
  if (!Array.isArray(value)) return "";
  return value.map((item) => normalizeSeriesId(item)).filter(Boolean).join(", ");
}

function canonicalizeScalar(field, value) {
  const text = normalizeText(value);
  if (field.key === "status") {
    return text.toLowerCase();
  }
  if (field.key === "series_ids") {
    return seriesIdsToText(parseSeriesIds(value));
  }
  if (field.type === "number") {
    return text;
  }
  return text;
}

function parseSeriesIds(value) {
  if (Array.isArray(value)) {
    return dedupeSeriesIds(value.map((item) => normalizeSeriesId(item)).filter(Boolean));
  }
  const text = normalizeText(value);
  if (!text) return [];
  return dedupeSeriesIds(text.split(",").map((item) => normalizeSeriesId(item)).filter(Boolean));
}

function dedupeSeriesIds(items) {
  const seen = new Set();
  const out = [];
  items.forEach((item) => {
    if (!item || seen.has(item)) return;
    seen.add(item);
    out.push(item);
  });
  return out;
}

function formatNumberText(value) {
  const text = normalizeText(value);
  return text;
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
    const tone = toneForReadinessStatus(normalizeText(item && item.status));
    const title = normalizeText(item && item.title) || "readiness";
    const summary = normalizeText(item && item.summary) || "—";
    const sourcePath = normalizeText(item && item.source_path);
    const nextStep = normalizeText(item && item.next_step);
    const action = item && item.action && typeof item.action === "object" ? item.action : null;
    const proseAction = action && action.kind === "prose-import" && normalizeText(action.target_kind) === "work";
    const disabledNote = proseAction && actionDisabled
      ? (draftHasChanges(state)
        ? t(state, "readiness_save_first", "Save source changes before importing prose.")
        : t(state, "readiness_action_busy", "Wait for the current save or rebuild to finish."))
      : "";
    return `
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(title)}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay catalogueReadiness__body">
          <span class="catalogueReadiness__summary" data-tone="${escapeHtml(tone)}">${escapeHtml(summary)}</span>
          ${sourcePath ? `<span class="tagStudioForm__meta catalogueReadiness__path">${escapeHtml(sourcePath)}</span>` : ""}
          ${nextStep ? `<span class="tagStudioForm__meta">${escapeHtml(nextStep)}</span>` : ""}
          ${proseAction ? `<div class="catalogueReadiness__actions"><button type="button" class="tagStudio__button" data-prose-import="work" ${actionDisabled ? "disabled" : ""}>${escapeHtml(normalizeText(action.label) || "Import prose + rebuild")}</button></div>` : ""}
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
  const draft = {};
  EDITABLE_FIELDS.forEach((field) => {
    if (field.key === "series_ids") {
      draft[field.key] = seriesIdsToText(record[field.key]);
      return;
    }
    draft[field.key] = formatNumberText(record[field.key]);
  });
  return draft;
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

function buildWorkFileEditorHref(state, fileUid) {
  const route = getStudioRoute(state.config, "catalogue_work_file_editor");
  return `${route}?file=${encodeURIComponent(fileUid)}`;
}

function buildWorkLinkEditorHref(state, linkUid) {
  const route = getStudioRoute(state.config, "catalogue_work_link_editor");
  return `${route}?link=${encodeURIComponent(linkUid)}`;
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
  if (!state.currentLookup || state.currentWorkId !== workId) return [];
  const items = Array.isArray(state.currentLookup.work_files) ? state.currentLookup.work_files : [];
  return items.slice().sort((a, b) => normalizeText(a && a.file_uid).localeCompare(normalizeText(b && b.file_uid), undefined, { numeric: true, sensitivity: "base" }));
}

function getWorkLinks(state, workId) {
  if (!state.currentLookup || state.currentWorkId !== workId) return [];
  const items = Array.isArray(state.currentLookup.work_links) ? state.currentLookup.work_links : [];
  return items.slice().sort((a, b) => normalizeText(a && a.link_uid).localeCompare(normalizeText(b && b.link_uid), undefined, { numeric: true, sensitivity: "base" }));
}

function renderWorkFileRows(state, items) {
  return items.map((item) => {
    const fileUid = normalizeText(item && item.file_uid);
    const label = displayValue(item && item.label);
    const href = buildWorkFileEditorHref(state, fileUid);
    return `
      <div class="catalogueWorkDetails__row">
        <a class="catalogueWorkDetails__link" href="${escapeHtml(href)}">${escapeHtml(fileUid)}</a>
        <span class="catalogueWorkDetails__title">${escapeHtml(label)}</span>
      </div>
    `;
  }).join("");
}

function renderWorkLinkRows(state, items) {
  return items.map((item) => {
    const linkUid = normalizeText(item && item.link_uid);
    const label = displayValue(item && item.label);
    const href = buildWorkLinkEditorHref(state, linkUid);
    return `
      <div class="catalogueWorkDetails__row">
        <a class="catalogueWorkDetails__link" href="${escapeHtml(href)}">${escapeHtml(linkUid)}</a>
        <span class="catalogueWorkDetails__title">${escapeHtml(label)}</span>
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
  if (!items.length) {
    state.filesMetaNode.textContent = "";
    state.filesResultsNode.innerHTML = `<p class="tagStudioForm__meta">${escapeHtml(t(state, "files_empty", "No work files for this work."))}</p>`;
    return;
  }
  state.filesMetaNode.textContent = `${items.length} total`;
  state.filesResultsNode.innerHTML = `
    <section class="catalogueWorkDetails__section">
      <div class="catalogueWorkDetails__rows">${renderWorkFileRows(state, items)}</div>
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
  if (!items.length) {
    state.linksMetaNode.textContent = "";
    state.linksResultsNode.innerHTML = `<p class="tagStudioForm__meta">${escapeHtml(t(state, "links_empty", "No work links for this work."))}</p>`;
    return;
  }
  state.linksMetaNode.textContent = `${items.length} total`;
  state.linksResultsNode.innerHTML = `
    <section class="catalogueWorkDetails__section">
      <div class="catalogueWorkDetails__rows">${renderWorkLinkRows(state, items)}</div>
    </section>
  `;
}

function updateSummary(state) {
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
      state.newDetailLinkNode.href = getStudioRoute(state.config, "catalogue_new_work_detail_editor");
    }
    if (state.newFileLinkNode) {
      state.newFileLinkNode.href = getStudioRoute(state.config, "catalogue_new_work_file_editor");
    }
    if (state.newLinkLinkNode) {
      state.newLinkLinkNode.href = getStudioRoute(state.config, "catalogue_new_work_link_editor");
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
    state.newDetailLinkNode.href = record ? `${base}?work=${encodeURIComponent(record.work_id)}` : base;
  }
  if (state.newFileLinkNode) {
    const base = getStudioRoute(state.config, "catalogue_new_work_file_editor");
    state.newFileLinkNode.href = record ? `${base}?work=${encodeURIComponent(record.work_id)}` : base;
  }
  if (state.newLinkLinkNode) {
    const base = getStudioRoute(state.config, "catalogue_new_work_link_editor");
    state.newLinkLinkNode.href = record ? `${base}?work=${encodeURIComponent(record.work_id)}` : base;
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

function syncUrl(workValue) {
  const url = new URL(window.location.href);
  if (workValue) {
    url.searchParams.set("work", workValue);
  } else {
    url.searchParams.delete("work");
  }
  window.history.replaceState({}, "", url.toString());
}

function draftHasChanges(state) {
  if (state.mode === "bulk") {
    return state.bulkTouchedFields.size > 0;
  }
  if (!state.baselineDraft) return false;
  return EDITABLE_FIELDS.some((field) => canonicalizeScalar(field, state.draft[field.key]) !== canonicalizeScalar(field, state.baselineDraft[field.key]));
}

function validateDraft(state) {
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

    ["height_cm", "width_cm", "depth_cm"].forEach((fieldKey) => {
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

  ["height_cm", "width_cm", "depth_cm"].forEach((fieldKey) => {
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
      if (["height_cm", "width_cm", "depth_cm"].includes(field.key)) {
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
    record: {
      status: normalizeText(draft.status).toLowerCase() || null,
      published_date: normalizeText(draft.published_date) || null,
      series_ids: parseSeriesIds(draft.series_ids),
      project_folder: normalizeText(draft.project_folder) || null,
      project_filename: normalizeText(draft.project_filename) || null,
      title: normalizeText(draft.title) || null,
      year: normalizeText(draft.year) ? Number(draft.year) : null,
      year_display: normalizeText(draft.year_display) || null,
      medium_type: normalizeText(draft.medium_type) || null,
      medium_caption: normalizeText(draft.medium_caption) || null,
      duration: normalizeText(draft.duration) || null,
      height_cm: normalizeText(draft.height_cm) ? Number(draft.height_cm) : null,
      width_cm: normalizeText(draft.width_cm) ? Number(draft.width_cm) : null,
      depth_cm: normalizeText(draft.depth_cm) ? Number(draft.depth_cm) : null,
      storage_location: normalizeText(draft.storage_location) || null,
      work_prose_file: normalizeText(draft.work_prose_file) || null,
      notes: normalizeText(draft.notes) || null,
      provenance: normalizeText(draft.provenance) || null,
      artist: normalizeText(draft.artist) || null
    }
  };
}

function applyBuildRequested(state) {
  return Boolean(state.applyBuildNode && state.applyBuildNode.checked);
}

function updatePublishControls(state, { hasRecord, dirty, errors }) {
  const showUpdate = hasRecord && state.rebuildPending;
  state.buildButton.hidden = !showUpdate;
  state.buildButton.disabled = !showUpdate || dirty || errors.size > 0 || state.isSaving || state.isBuilding || state.isDeleting || !state.serverAvailable;
  if (state.runtimeActionsNode) state.runtimeActionsNode.hidden = !showUpdate;
  if (state.applyBuildNode) {
    state.applyBuildNode.disabled = !hasRecord || state.isSaving || state.isBuilding || state.isDeleting || !state.serverAvailable;
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

function updateEditorState(state) {
  const hasRecord = state.mode === "bulk" ? state.bulkWorkIds.length > 0 : Boolean(state.currentRecord);
  const errors = hasRecord ? validateDraft(state) : new Map();
  state.validationErrors = errors;
  updateFieldMessages(state, errors);
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
  if (!dirty && !errors.size && !state.resultNode.textContent && hasRecord) {
    setTextWithState(
      state.statusNode,
      state.mode === "bulk"
        ? t(state, "bulk_status_loaded", "Loaded {count} work records.", { count: String(state.bulkWorkIds.length) })
        : t(state, "save_status_loaded", "Loaded work {work_id}.", { work_id: state.currentWorkId })
    );
  }

  state.saveButton.disabled = !hasRecord || state.isSaving || errors.size > 0 || !dirty || !state.serverAvailable;
  state.deleteButton.disabled = !Boolean(state.currentRecord) || state.mode === "bulk" || state.isSaving || state.isBuilding || state.isDeleting || !state.serverAvailable;
  updatePublishControls(state, { hasRecord, dirty, errors });
  renderReadiness(state);
}

function onFieldInput(state, fieldKey) {
  const node = state.fieldNodes.get(fieldKey);
  if (!node) return;
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
  const proseItem = getReadinessItems(state).find((item) => normalizeText(item && item.key) === "work_prose");
  if (!proseItem || normalizeText(proseItem.status) !== "ready") {
    setTextWithState(state.statusNode, t(state, "prose_import_not_ready", "No ready work prose source is configured for this record."), "error");
    return;
  }

  state.isBuilding = true;
  updateEditorState(state);
  setTextWithState(state.statusNode, t(state, "prose_import_running", "Importing prose and rebuilding…"));
  setTextWithState(state.resultNode, "");
  try {
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
      t(state, "prose_import_result_success", "Prose imported and runtime rebuilt at {completed_at}. Build Activity updated.", { completed_at: completedAt }),
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
  if (!root || !loadingNode || !emptyNode || !fieldsNode || !readonlyNode || !previewNode || !summaryNode || !readinessNode || !runtimeStateNode || !buildImpactNode || !detailsHeadingNode || !newDetailLinkNode || !detailSearchRowNode || !detailSearchNode || !detailsMetaNode || !detailsResultsNode || !filesHeadingNode || !newFileLinkNode || !filesMetaNode || !filesResultsNode || !linksHeadingNode || !newLinkLinkNode || !linksMetaNode || !linksResultsNode || !searchNode || !popupNode || !popupListNode || !openButton || !saveButton || !buildButton || !deleteButton || !runtimeActionsNode || !applyBuildNode || !applyBuildLabelNode || !saveModeNode || !contextNode || !statusNode || !warningNode || !resultNode || !metaNode) {
    return;
  }

  const state = {
    config: null,
    mode: "single",
    workSearchById: new Map(),
    seriesById: new Map(),
    sourceWorkRecordsById: new Map(),
    currentLookup: null,
    currentWorkId: "",
    currentRecord: null,
    currentRecordHash: "",
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
    fieldNodes: new Map(),
    fieldStatusNodes: new Map(),
    readonlyNodes: new Map(),
    searchNode,
    popupNode,
    popupListNode,
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
    searchNode.placeholder = t(state, "search_placeholder", "find work id(s): 00001, 00003-00005");
    detailsHeadingNode.textContent = t(state, "details_heading", "work details");
    newDetailLinkNode.textContent = t(state, "details_new_link", "new work detail →");
    detailSearchNode.placeholder = t(state, "details_search_placeholder", "find detail by id");
    filesHeadingNode.textContent = t(state, "files_heading", "work files");
    newFileLinkNode.textContent = t(state, "files_new_link", "new file →");
    linksHeadingNode.textContent = t(state, "links_heading", "work links");
    newLinkLinkNode.textContent = t(state, "links_new_link", "new link →");
    openButton.textContent = t(state, "open_button", "Open");
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
      openWorkSelection(state, searchNode.value).catch((error) => {
        console.warn("catalogue_work_editor: failed to open requested work selection", error);
      });
    });

    detailSearchNode.addEventListener("input", () => {
      updateDetailSections(state);
    });

    popupListNode.addEventListener("click", (event) => {
      const button = event.target && event.target.closest ? event.target.closest("[data-work-id]") : null;
      if (!button) return;
      openWorkById(state, button.getAttribute("data-work-id")).catch((error) => {
        console.warn("catalogue_work_editor: failed to open selected work", error);
      });
    });

    openButton.addEventListener("click", () => {
      openWorkSelection(state, searchNode.value).catch((error) => {
        console.warn("catalogue_work_editor: failed to open requested work selection", error);
      });
    });
    readinessNode.addEventListener("click", (event) => {
      const button = event.target && event.target.closest ? event.target.closest("[data-prose-import]") : null;
      if (!button) return;
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

    const requestedWorkValue = normalizeText(new URLSearchParams(window.location.search).get("work"));
    if (requestedWorkValue) {
      openWorkSelection(state, requestedWorkValue).catch((error) => {
        console.warn("catalogue_work_editor: failed to open requested work selection", error);
      });
    } else {
      setTextWithState(contextNode, t(state, "missing_work_param", "Search for a work by work id."));
      updateSummary(state);
      updateEditorState(state);
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
