import {
  getStudioRoute,
  getStudioText,
  loadStudioConfig
} from "./studio-config.js";
import { loadStudioLookupJson, loadStudioLookupRecordJson } from "./studio-data.js";
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
  loadCatalogueMediaConfig
} from "./catalogue-media-preview.js";

const EDITABLE_FIELDS = [
  { key: "project_subfolder", label: "project subfolder", type: "text" },
  { key: "project_filename", label: "project filename", type: "text" },
  { key: "title", label: "title", type: "text" },
  { key: "status", label: "status", type: "select", options: ["", "draft", "published"] }
];

const READONLY_FIELDS = [
  { key: "detail_uid", label: "detail id" },
  { key: "work_id", label: "work id" },
  { key: "detail_id", label: "detail row id" },
  { key: "published_date", label: "published date" },
  { key: "width_px", label: "width px" },
  { key: "height_px", label: "height px" }
];

const STATUS_OPTIONS = new Set(["", "draft", "published"]);
const SEARCH_LIMIT = 20;
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

function normalizeDetailId(value) {
  const digits = normalizeText(value).replace(/\D/g, "");
  if (!digits) return "";
  return digits.padStart(3, "0");
}

function normalizeDetailUid(value) {
  const text = normalizeText(value);
  if (!text) return "";
  const match = text.match(/^(\d{5})-(\d{3})$/);
  if (match) return `${match[1]}-${match[2]}`;
  const digits = text.replace(/\D/g, "");
  if (digits.length === 8) {
    return `${digits.slice(0, 5)}-${digits.slice(5)}`;
  }
  return "";
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

async function computeRecordHash(record) {
  if (!globalThis.crypto || !crypto.subtle) return "";
  const json = stableStringify(record);
  const bytes = new TextEncoder().encode(json);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest)).map((value) => value.toString(16).padStart(2, "0")).join("");
}

function displayValue(value) {
  const text = normalizeText(value);
  return text || "—";
}

function getReadinessItems(state) {
  const readiness = state.buildPreview && typeof state.buildPreview === "object" ? state.buildPreview.readiness : null;
  const items = readiness && Array.isArray(readiness.items) ? readiness.items : [];
  return items.filter((item) => normalizeText(item && item.key) === "detail_media");
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
  const mediaItem = getReadinessItem(state, "detail_media");
  const preview = buildDetailThumbPreview(state.mediaConfig, record.detail_uid);
  const fallback = previewFallback(
    state,
    mediaItem,
    t(state, "preview_generated_missing", "Generated preview unavailable. Source media exists."),
    t(state, "preview_source_missing", "Source media missing.")
  );
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
  const items = getReadinessItems(state);
  if (!items.length) {
    state.readinessNode.innerHTML = "";
    return;
  }
  state.readinessNode.innerHTML = items.map((item) => {
    const tone = toneForReadinessStatus(normalizeText(item && item.status));
    const title = normalizeText(item && item.title) || "readiness";
    const summary = normalizeText(item && item.summary) || "—";
    const sourcePath = normalizeText(item && item.source_path);
    const nextStep = normalizeText(item && item.next_step);
    return `
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(title)}</span>
        <div class="tagStudioForm__readonly catalogueReadiness__body">
          <span class="catalogueReadiness__summary" data-tone="${escapeHtml(tone)}">${escapeHtml(summary)}</span>
          ${sourcePath ? `<span class="tagStudioForm__meta catalogueReadiness__path">${escapeHtml(sourcePath)}</span>` : ""}
          ${nextStep ? `<span class="tagStudioForm__meta">${escapeHtml(nextStep)}</span>` : ""}
        </div>
      </div>
    `;
  }).join("");
}

function canonicalizeScalar(field, value) {
  return normalizeText(value);
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

function setTextWithState(node, text, state = "") {
  if (!node) return;
  node.textContent = text || "";
  if (state) node.dataset.state = state;
  else delete node.dataset.state;
}

function setPopupVisibility(state, visible) {
  state.popupNode.hidden = !visible;
}

function renderField(field, fieldsNode, state) {
  const wrapper = document.createElement("label");
  wrapper.className = "tagStudioForm__field catalogueWorkForm__field";
  wrapper.htmlFor = `catalogueWorkDetailField-${field.key}`;

  const label = document.createElement("span");
  label.className = "tagStudioForm__label";
  label.textContent = field.label;
  wrapper.appendChild(label);

  let input;
  if (field.type === "select") {
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

  const value = document.createElement("span");
  value.className = "tagStudio__input tagStudioForm__readonly";
  value.dataset.readonlyField = field.key;
  value.textContent = "—";
  wrapper.appendChild(value);

  readonlyNode.appendChild(wrapper);
  state.readonlyNodes.set(field.key, value);
}

function buildRecordSummary(record) {
  const title = normalizeText(record && record.title);
  const section = normalizeText(record && record.project_subfolder);
  if (title && section) return `${title} · ${section}`;
  return title || section || "—";
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
  return loadStudioLookupRecordJson(state.config, "catalogue_lookup_work_detail_base", detailUid, { cache: "no-store" });
}

function buildDraftFromRecord(record) {
  const draft = {};
  EDITABLE_FIELDS.forEach((field) => {
    draft[field.key] = normalizeText(record[field.key]);
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
      set_fields: setFields
    };
  }

  const draft = state.draft;
  return {
    detail_uid: state.currentDetailUid,
    expected_record_hash: state.currentRecordHash,
    record: {
      detail_uid: state.currentDetailUid,
      work_id: state.currentWorkId,
      detail_id: state.currentRecord.detail_id,
      project_subfolder: normalizeText(draft.project_subfolder) || null,
      project_filename: normalizeText(draft.project_filename) || null,
      title: normalizeText(draft.title) || null,
      status: normalizeText(draft.status).toLowerCase() || null
    }
  };
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

function syncUrl(detailValue) {
  const url = new URL(window.location.href);
  if (detailValue) url.searchParams.set("detail", detailValue);
  else url.searchParams.delete("detail");
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
  const errors = new Map();
  if (state.mode === "bulk" && !state.bulkTouchedFields.has("status")) {
    return errors;
  }
  const status = normalizeText(state.draft.status).toLowerCase();
  if (!STATUS_OPTIONS.has(status)) {
    errors.set("status", t(state, "field_invalid_status", "Use blank, draft, or published."));
  }
  return errors;
}

function updateFieldMessages(state, errors) {
  EDITABLE_FIELDS.forEach((field) => {
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
  if (state.mode === "bulk") {
    const selectedCount = state.bulkDetailUids.length;
    const parentWorkIds = Array.from(new Set(state.bulkDetailUids.map((detailUid) => {
      const record = state.bulkRecords.get(detailUid);
      return normalizeWorkId(record && record.work_id);
    }).filter(Boolean)));
    state.summaryNode.innerHTML = `
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(t(state, "bulk_summary_selected", "selected details"))}</span>
        <span class="tagStudioForm__readonly">${escapeHtml(formatSelectionList(state.bulkDetailUids) || "—")}</span>
      </div>
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(t(state, "bulk_summary_count", "record count"))}</span>
        <span class="tagStudioForm__readonly">${escapeHtml(String(selectedCount || 0))}</span>
      </div>
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(t(state, "bulk_summary_parent_count", "parent works"))}</span>
        <span class="tagStudioForm__readonly">${escapeHtml(formatSelectionList(parentWorkIds) || "—")}</span>
      </div>
    `;
    state.runtimeStateNode.textContent = state.rebuildPending
      ? t(state, "summary_rebuild_needed", "source changed; rebuild pending")
      : t(state, "summary_rebuild_current", "source and runtime not yet diverged in this session");
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
      <span class="tagStudioForm__readonly">
        ${record ? `<a href="${escapeHtml(publicHref)}" target="_blank" rel="noopener">${escapeHtml(record.detail_uid)}</a>` : "—"}
      </span>
    </div>
    <div class="tagStudioForm__field">
      <span class="tagStudioForm__label">${escapeHtml(t(state, "summary_parent_link", "Open work editor"))}</span>
      <span class="tagStudioForm__readonly">
        ${record ? `<a href="${escapeHtml(workEditorHref)}">${escapeHtml(record.work_id)}</a>` : "—"}
      </span>
    </div>
    <div class="tagStudioForm__field">
      <span class="tagStudioForm__label">${escapeHtml(t(state, "summary_section_label", "detail section"))}</span>
      <span class="tagStudioForm__readonly">${escapeHtml(displayValue(record && record.project_subfolder))}</span>
    </div>
  `;

  state.runtimeStateNode.textContent = state.rebuildPending
    ? t(state, "summary_rebuild_needed", "source changed; rebuild pending")
    : t(state, "summary_rebuild_current", "source and runtime not yet diverged in this session");
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
  state.baselineDraft = buildDraftFromRecord(record);
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
  const hasRecord = state.mode === "bulk" ? state.bulkDetailUids.length > 0 : Boolean(state.currentRecord);
  const errors = hasRecord ? validateDraft(state) : new Map();
  state.validationErrors = errors;
  updateFieldMessages(state, errors);
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
  setTextWithState(state.warningNode, dirty ? t(state, "dirty_warning", "Unsaved source changes.") : "");
  if (!dirty && !errors.size && !state.resultNode.textContent && hasRecord) {
    setTextWithState(
      state.statusNode,
      state.mode === "bulk"
        ? t(state, "bulk_status_loaded", "Loaded {count} detail records.", { count: String(state.bulkDetailUids.length) })
        : t(state, "save_status_loaded", "Loaded detail {detail_uid}.", { detail_uid: state.currentDetailUid })
    );
  }

  state.saveButton.disabled = !hasRecord || state.isSaving || errors.size > 0 || !dirty || !state.serverAvailable;
  state.buildButton.disabled = !hasRecord || state.isSaving || state.isBuilding || errors.size > 0 || !state.serverAvailable;
  state.deleteButton.disabled = !Boolean(state.currentRecord) || state.mode === "bulk" || state.isSaving || state.isBuilding || state.isDeleting || !state.serverAvailable;
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
  return getStudioText(state.config, `catalogue_work_detail_editor.${key}`, fallback, tokens);
}

async function refreshBuildPreview(state) {
  if (state.mode === "bulk") {
    const previewTargets = state.rebuildPending && state.bulkBuildTargets.length
      ? state.bulkBuildTargets
      : Array.from(new Set(state.bulkDetailUids.map((detailUid) => {
        const record = state.bulkRecords.get(detailUid);
        return normalizeWorkId(record && record.work_id);
      }).filter(Boolean)));
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
  try {
    const response = await postJson(CATALOGUE_WRITE_ENDPOINTS.buildPreview, {
      work_id: state.currentWorkId,
      detail_uid: state.currentDetailUid
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

async function saveCurrentDetail(state) {
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
  state.buildButton.disabled = true;
  setTextWithState(state.statusNode, t(state, "save_status_saving", "Saving source record…"));
  setTextWithState(state.resultNode, "");

  try {
    if (state.mode === "bulk") {
      const response = await postJson(CATALOGUE_WRITE_ENDPOINTS.bulkSave, buildPayload(state));
      const changedRecords = Array.isArray(response && response.records) ? response.records : [];
      changedRecords.forEach((item) => {
        const detailUid = normalizeDetailUid(item && item.detail_uid);
        const record = item && item.record && typeof item.record === "object" ? item.record : null;
        if (!detailUid || !record) return;
        state.bulkRecords.set(detailUid, record);
        state.bulkRecordHashes.set(detailUid, normalizeText(item.record_hash) || "");
        state.detailSearchByUid.set(detailUid, {
          detail_uid: detailUid,
          work_id: normalizeText(record.work_id),
          detail_id: normalizeText(record.detail_id),
          title: normalizeText(record.title),
          status: normalizeText(record.status)
        });
      });
      state.rebuildPending = Boolean(response.changed);
      state.bulkBuildTargets = Array.isArray(response && response.build_targets) ? response.build_targets : [];
      setLoadedBulkDetails(state, state.bulkDetailUids, state.bulkRecords, state.bulkRecordHashes, {
        keepResult: true,
        buildTargets: state.bulkBuildTargets
      });
      const savedAt = normalizeText(response.saved_at_utc || utcTimestamp());
      const resultText = response.changed
        ? t(state, "bulk_save_result_success", "Saved {count} detail records at {saved_at}. Rebuild needed to update the parent work output.", {
          count: String(response.changed_count || 0),
          saved_at: savedAt
        })
        : t(state, "save_result_unchanged", "Source already matches the current form values.");
      setTextWithState(state.resultNode, resultText, response.changed ? "success" : "");
      setTextWithState(
        state.statusNode,
        t(state, "bulk_status_loaded", "Loaded {count} detail records.", { count: String(state.bulkDetailUids.length) }),
        response.changed ? "success" : ""
      );
      return;
    }

    const response = await postJson(CATALOGUE_WRITE_ENDPOINTS.saveWorkDetail, buildPayload(state));
    const record = response && response.record && typeof response.record === "object" ? response.record : null;
    if (!record) throw new Error("save response missing record");
    state.detailSearchByUid.set(state.currentDetailUid, {
      detail_uid: state.currentDetailUid,
      work_id: normalizeText(record.work_id),
      detail_id: normalizeText(record.detail_id),
      title: normalizeText(record.title),
      status: normalizeText(record.status)
    });
    state.rebuildPending = Boolean(response.changed);
    const lookup = await loadDetailLookupRecord(state, state.currentDetailUid);
    const lookupRecord = lookup && lookup.work_detail && typeof lookup.work_detail === "object" ? lookup.work_detail : record;
    setLoadedRecord(state, state.currentDetailUid, lookupRecord, {
      recordHash: response.record_hash || normalizeText(lookup && lookup.record_hash) || "",
      keepResult: true,
      lookup
    });
    await refreshBuildPreview(state);
    const savedAt = normalizeText(response.saved_at_utc || utcTimestamp());
    const resultText = response.changed
      ? t(state, "save_result_success", "Source saved at {saved_at}. Rebuild needed to update the parent work output.", { saved_at: savedAt })
      : t(state, "save_result_unchanged", "Source already matches the current form values.");
    setTextWithState(state.resultNode, resultText, response.changed ? "success" : "");
    setTextWithState(state.statusNode, t(state, "save_status_loaded", "Loaded detail {detail_uid}.", { detail_uid: state.currentDetailUid }), "success");
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

async function buildCurrentDetail(state) {
  if (state.mode === "bulk") {
    if (!state.bulkDetailUids.length || !state.serverAvailable) return;
  } else if (!state.currentRecord || !state.currentWorkId || !state.serverAvailable) {
    return;
  }
  state.isBuilding = true;
  updateEditorState(state);
  setTextWithState(state.statusNode, t(state, "build_status_running", "Running scoped rebuild…"));
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
        t(state, "bulk_build_result_success", "Runtime rebuilt for {count} parent work scopes at {completed_at}. Build Activity updated.", {
          count: String(buildTargets.length),
          completed_at: completedAt
        }),
        "success"
      );
      setTextWithState(state.statusNode, t(state, "build_status_success", "Scoped rebuild completed."), "success");
      return;
    }

    const response = await postJson(CATALOGUE_WRITE_ENDPOINTS.buildApply, {
      work_id: state.currentWorkId,
      detail_uid: state.currentDetailUid
    });
    state.rebuildPending = false;
    await refreshBuildPreview(state);
    const completedAt = normalizeText(response.completed_at_utc || utcTimestamp());
    setTextWithState(
      state.resultNode,
      t(state, "build_result_success", "Runtime rebuilt at {completed_at}. Build Activity updated.", { completed_at: completedAt }),
      "success"
    );
    setTextWithState(state.statusNode, t(state, "build_status_success", "Scoped rebuild completed."), "success");
  } catch (error) {
    setTextWithState(
      state.statusNode,
      `${t(state, "build_status_failed", "Scoped rebuild failed.")} ${normalizeText(error && error.message)}`.trim(),
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
    const previewResponse = await postJson(CATALOGUE_WRITE_ENDPOINTS.deletePreview, {
      kind: "work_detail",
      detail_uid: state.currentDetailUid,
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
      kind: "work_detail",
      detail_uid: state.currentDetailUid,
      expected_record_hash: state.currentRecordHash
    });
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

async function saveAndBuildCurrentDetail(state) {
  if (state.mode === "bulk") {
    if (!state.bulkDetailUids.length) return;
  } else if (!state.currentRecord) {
    return;
  }
  if (draftHasChanges(state)) {
    await saveCurrentDetail(state);
    if (state.mode === "bulk") {
      if (draftHasChanges(state)) return;
    } else if (!state.currentRecord || draftHasChanges(state)) {
      return;
    }
    if (state.statusNode.dataset.state === "error") return;
  }
  await buildCurrentDetail(state);
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
  const buildButton = document.getElementById("catalogueWorkDetailBuild");
  const deleteButton = document.getElementById("catalogueWorkDetailDelete");
  const saveModeNode = document.getElementById("catalogueWorkDetailSaveMode");
  const contextNode = document.getElementById("catalogueWorkDetailContext");
  const statusNode = document.getElementById("catalogueWorkDetailStatus");
  const warningNode = document.getElementById("catalogueWorkDetailWarning");
  const resultNode = document.getElementById("catalogueWorkDetailResult");
  if (!root || !loadingNode || !emptyNode || !fieldsNode || !readonlyNode || !previewNode || !summaryNode || !readinessNode || !runtimeStateNode || !buildImpactNode || !searchNode || !popupNode || !popupListNode || !openButton || !saveButton || !buildButton || !deleteButton || !saveModeNode || !contextNode || !statusNode || !warningNode || !resultNode) {
    return;
  }

  const state = {
    config: null,
    mode: "single",
    detailSearchByUid: new Map(),
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
    fieldNodes: new Map(),
    fieldStatusNodes: new Map(),
    readonlyNodes: new Map(),
    searchNode,
    popupNode,
    popupListNode,
    saveButton,
    buildButton,
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

  EDITABLE_FIELDS.forEach((field) => renderField(field, fieldsNode, state));
  READONLY_FIELDS.forEach((field) => renderReadonlyField(field, readonlyNode, state));

  try {
    const config = await loadStudioConfig();
    state.config = config;
    searchNode.placeholder = t(state, "search_placeholder", "find detail id(s): 00001-001, 00001-003-005");
    openButton.textContent = t(state, "open_button", "Open");
    saveButton.textContent = t(state, "save_button", "Save Source");
    buildButton.textContent = t(state, "build_button", "Save + Rebuild");
    deleteButton.textContent = t(state, "delete_button", "Delete Source");

    const [detailsPayload, serverAvailable] = await Promise.all([
      loadStudioLookupJson(config, "catalogue_lookup_work_detail_search", { cache: "no-store" }),
      probeCatalogueHealth()
    ]);

    const detailItems = Array.isArray(detailsPayload && detailsPayload.items) ? detailsPayload.items : [];
    detailItems.forEach((record) => {
      if (!record || typeof record !== "object") return;
      const detailUid = normalizeText(record.detail_uid);
      if (!detailUid) return;
      state.detailSearchByUid.set(detailUid, record);
    });
    state.serverAvailable = Boolean(serverAvailable);
    saveModeNode.textContent = buildSaveModeText(config, serverAvailable ? "post" : "offline", (cfg, key, fallback, tokens) => getStudioText(cfg, `catalogue_work_detail_editor.${key}`, fallback, tokens));
    if (!state.serverAvailable) {
      setTextWithState(statusNode, t(state, "save_mode_unavailable_hint", "Local catalogue server unavailable. Save is disabled."), "warn");
    }

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
    saveButton.addEventListener("click", () => saveCurrentDetail(state).catch((error) => {
      console.warn("catalogue_work_detail_editor: unexpected save failure", error);
    }));
    buildButton.addEventListener("click", () => saveAndBuildCurrentDetail(state).catch((error) => {
      console.warn("catalogue_work_detail_editor: unexpected save/build failure", error);
    }));
    deleteButton.addEventListener("click", () => deleteCurrentDetail(state).catch((error) => {
      console.warn("catalogue_work_detail_editor: unexpected delete failure", error);
    }));

    document.addEventListener("click", (event) => {
      if (event.target === searchNode || popupNode.contains(event.target)) return;
      setPopupVisibility(state, false);
    });

    const requestedDetailValue = normalizeText(new URLSearchParams(window.location.search).get("detail"));
    if (requestedDetailValue) {
      openDetailSelection(state, requestedDetailValue).catch((error) => {
        console.warn("catalogue_work_detail_editor: failed to open requested detail selection", error);
      });
    } else {
      setTextWithState(contextNode, t(state, "missing_detail_param", "Search for a work detail by detail id."));
      updateSummary(state);
      updateEditorState(state);
    }

    root.hidden = false;
    loadingNode.hidden = true;
  } catch (error) {
    console.warn("catalogue_work_detail_editor: init failed", error);
    try {
      const config = await loadStudioConfig();
      loadingNode.textContent = getStudioText(config, "catalogue_work_detail_editor.load_failed_error", "Failed to load catalogue source data for the work detail editor.");
    } catch (_configError) {
      loadingNode.textContent = "Failed to load catalogue source data for the work detail editor.";
    }
  }
}

init();
