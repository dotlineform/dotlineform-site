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

const EDITABLE_FIELDS = [
  { key: "title", label: "title", type: "text" },
  { key: "series_type", label: "series type", type: "text" },
  { key: "status", label: "status", type: "select", options: ["", "draft", "published"] },
  { key: "published_date", label: "published date", type: "date" },
  { key: "year", label: "year", type: "number", step: "1" },
  { key: "year_display", label: "year display", type: "text" },
  { key: "primary_work_id", label: "primary work id", type: "text" },
  { key: "series_prose_file", label: "series prose file", type: "text" },
  { key: "sort_fields", label: "sort fields", type: "text" },
  { key: "notes", label: "notes", type: "textarea" }
];

const READONLY_FIELDS = [
  { key: "series_id", label: "series id" }
];

const STATUS_OPTIONS = new Set(["", "draft", "published"]);
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const SEARCH_LIMIT = 20;
const MEMBER_LIST_LIMIT = 10;

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

function normalizeSeriesId(value) {
  const digits = normalizeText(value).replace(/\D/g, "");
  if (digits) return digits.padStart(3, "0");
  return normalizeText(value).toLowerCase();
}

function normalizeWorkId(value) {
  const digits = normalizeText(value).replace(/\D/g, "");
  if (!digits) return "";
  return digits.padStart(5, "0");
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

function buildSearchToken(value) {
  const text = normalizeText(value);
  if (!text) return "";
  return text.toLowerCase();
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
  wrapper.htmlFor = `catalogueSeriesField-${field.key}`;

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
    input.type = field.type === "date" ? "date" : (field.type === "number" ? "number" : "text");
    if (field.step) input.step = field.step;
  }

  input.id = `catalogueSeriesField-${field.key}`;
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
  value.textContent = "—";
  wrapper.appendChild(value);

  readonlyNode.appendChild(wrapper);
  state.readonlyNodes.set(field.key, value);
}

function t(state, key, fallback, tokens = null) {
  return getStudioText(state.config, `catalogue_series_editor.${key}`, fallback, tokens);
}

function buildRecordSummary(record) {
  const title = normalizeText(record && record.title);
  return title || "—";
}

function getSearchMatches(state, rawQuery) {
  const query = buildSearchToken(rawQuery);
  if (!query) return [];
  const matches = [];
  for (const [seriesId, record] of state.seriesById.entries()) {
    const title = normalizeText(record && record.title).toLowerCase();
    if (seriesId.includes(query) || title.includes(query)) {
      matches.push({ seriesId, record });
    }
  }
  matches.sort((a, b) => a.seriesId.localeCompare(b.seriesId, undefined, { numeric: true, sensitivity: "base" }));
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
  const rows = matches.map(({ seriesId, record }) => `
    <button type="button" class="tagStudioSuggest__workButton" data-series-id="${escapeHtml(seriesId)}">
      <span class="tagStudioSuggest__workId">${escapeHtml(seriesId)}</span>
      <span class="tagStudioSuggest__workTitle">${escapeHtml(buildRecordSummary(record))}</span>
    </button>
  `);
  state.popupListNode.innerHTML = `<div class="tagStudioSuggest__workRows">${rows.join("")}</div>`;
  setPopupVisibility(state, true);
}

async function loadSeriesLookupRecord(state, seriesId) {
  return loadStudioLookupRecordJson(state.config, "catalogue_lookup_series_base", seriesId, { cache: "no-store" });
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

function getStoredWorkSeriesIds(state, workId) {
  const record = state.workSearchById.get(workId);
  const values = record && Array.isArray(record.series_ids) ? record.series_ids : [];
  return values.map((seriesId) => normalizeSeriesId(seriesId)).filter(Boolean);
}

function getEditableMembershipEntries(state) {
  return Array.from(state.memberSeriesIdsByWorkId.entries())
    .map(([workId, seriesIds]) => ({ workId, seriesIds: seriesIds.slice() }))
    .sort((a, b) => a.workId.localeCompare(b.workId, undefined, { numeric: true, sensitivity: "base" }));
}

function getCurrentMemberEntries(state) {
  return getEditableMembershipEntries(state)
    .filter(({ seriesIds }) => seriesIds.includes(state.currentSeriesId))
    .map(({ workId, seriesIds }) => {
      const record = state.workSearchById.get(workId) || {};
      const position = seriesIds.indexOf(state.currentSeriesId);
      return {
        workId,
        seriesIds,
        position,
        record,
      };
    });
}

function membershipHasChanges(state) {
  const allWorkIds = new Set([
    ...Array.from(state.memberSeriesIdsByWorkId.keys()),
    ...Array.from(state.baselineMemberSeriesIdsByWorkId.keys())
  ]);
  for (const workId of allWorkIds) {
    const current = state.memberSeriesIdsByWorkId.get(workId) || [];
    const baseline = state.baselineMemberSeriesIdsByWorkId.get(workId) || [];
    if (stableStringify(current) !== stableStringify(baseline)) return true;
  }
  return false;
}

function draftHasChanges(state) {
  if (!state.baselineDraft) return false;
  return EDITABLE_FIELDS.some((field) => normalizeText(state.draft[field.key]) !== normalizeText(state.baselineDraft[field.key])) || membershipHasChanges(state);
}

function validateDraft(state) {
  const errors = new Map();
  const status = normalizeText(state.draft.status).toLowerCase();
  if (!STATUS_OPTIONS.has(status)) {
    errors.set("status", t(state, "field_invalid_status", "Use blank, draft, or published."));
  }
  const publishedDate = normalizeText(state.draft.published_date);
  if (publishedDate && !DATE_RE.test(publishedDate)) {
    errors.set("published_date", "Use YYYY-MM-DD or leave blank.");
  }
  const year = normalizeText(state.draft.year);
  if (year && !/^-?\d+$/.test(year)) {
    errors.set("year", t(state, "field_invalid_year", "Use a whole year or leave blank."));
  }
  const primaryWorkId = normalizeWorkId(state.draft.primary_work_id);
  const currentMembers = new Set(getCurrentMemberEntries(state).map((entry) => entry.workId));
  if (status === "published" && !primaryWorkId) {
    errors.set("primary_work_id", t(state, "field_required_primary_work_publish", "Published series must have a primary work that belongs to this series."));
  } else if (primaryWorkId && !currentMembers.has(primaryWorkId)) {
    errors.set("primary_work_id", t(state, "field_invalid_primary_work", "Primary work must be a current member of this series."));
  }
  return errors;
}

function updateFieldMessages(state, errors) {
  EDITABLE_FIELDS.forEach((field) => {
    const node = state.fieldStatusNodes.get(field.key);
    if (!node) return;
    const message = errors.get(field.key) || "";
    node.textContent = message;
    node.hidden = !message;
  });
}

function buildPayload(state, workUpdates) {
  return {
    series_id: state.currentSeriesId,
    expected_record_hash: state.currentRecordHash,
    record: {
      title: normalizeText(state.draft.title) || null,
      series_type: normalizeText(state.draft.series_type) || null,
      status: normalizeText(state.draft.status).toLowerCase() || null,
      published_date: normalizeText(state.draft.published_date) || null,
      year: normalizeText(state.draft.year) ? Number(state.draft.year) : null,
      year_display: normalizeText(state.draft.year_display) || null,
      primary_work_id: normalizeWorkId(state.draft.primary_work_id) || null,
      series_prose_file: normalizeText(state.draft.series_prose_file) || null,
      sort_fields: normalizeText(state.draft.sort_fields) || null,
      notes: normalizeText(state.draft.notes) || null
    },
    work_updates: workUpdates
  };
}

async function buildChangedWorkUpdates(state) {
  const updates = [];
  for (const [workId, seriesIds] of state.memberSeriesIdsByWorkId.entries()) {
    const baseline = state.baselineMemberSeriesIdsByWorkId.get(workId) || [];
    if (stableStringify(seriesIds) === stableStringify(baseline)) continue;
    const currentRecord = state.workSearchById.get(workId);
    if (!currentRecord) continue;
    updates.push({
      work_id: workId,
      series_ids: seriesIds,
      expected_record_hash: normalizeText(currentRecord.record_hash) || await computeRecordHash(currentRecord)
    });
  }
  return updates;
}

function formatBuildPreview(state, build) {
  if (!build || typeof build !== "object") return "";
  const workIds = Array.isArray(build.work_ids) ? build.work_ids : [];
  const seriesIds = Array.isArray(build.series_ids) ? build.series_ids : [];
  const workText = workIds.length ? workIds.join(", ") : "none";
  const seriesText = seriesIds.length ? seriesIds.join(", ") : "none";
  const searchText = build.rebuild_search ? t(state, "build_preview_search_yes", "yes") : t(state, "build_preview_search_no", "no");
  return t(state, "build_preview_template", "Build preview: work {work_ids}; series {series_ids}; catalogue search {search_rebuild}.", {
    work_ids: workText,
    series_ids: seriesText,
    search_rebuild: searchText
  });
}

function syncUrl(seriesId) {
  const url = new URL(window.location.href);
  if (seriesId) url.searchParams.set("series", seriesId);
  else url.searchParams.delete("series");
  window.history.replaceState({}, "", url.toString());
}

function updateSummary(state) {
  const record = state.currentRecord;
  state.metaNode.textContent = record ? `${record.series_id} · ${buildRecordSummary(record)}` : "";
  const publicHref = record ? `${getStudioRoute(state.config, "series_page_base")}${encodeURIComponent(record.series_id)}/` : "";
  const memberCount = getCurrentMemberEntries(state).length;
  state.summaryNode.innerHTML = `
    <div class="tagStudioForm__field">
      <span class="tagStudioForm__label">${escapeHtml(t(state, "summary_public_link", "Open public series page"))}</span>
      <span class="tagStudioForm__readonly">
        ${record ? `<a href="${escapeHtml(publicHref)}" target="_blank" rel="noopener">${escapeHtml(record.series_id)}</a>` : "—"}
      </span>
    </div>
    <div class="tagStudioForm__field">
      <span class="tagStudioForm__label">${escapeHtml(t(state, "summary_member_count", "member works"))}</span>
      <span class="tagStudioForm__readonly">${escapeHtml(String(memberCount))}</span>
    </div>
  `;
  state.runtimeStateNode.textContent = state.rebuildPending
    ? t(state, "summary_rebuild_needed", "source changed; rebuild pending")
    : t(state, "summary_rebuild_current", "source and runtime not yet diverged in this session");
}

function renderMemberRows(state, entries) {
  const workEditorBase = getStudioRoute(state.config, "catalogue_work_editor");
  return entries.map((entry) => {
    const workId = entry.workId;
    const title = displayValue(entry.record && entry.record.title);
    const isPrimary = entry.position === 0;
    const workHref = `${workEditorBase}?work=${encodeURIComponent(workId)}`;
    const positionText = t(state, "members_position", "position {position}", { position: String(entry.position + 1) });
    return `
      <div class="catalogueSeriesMembers__row">
        <div class="catalogueSeriesMembers__meta">
          <a class="catalogueSeriesMembers__link" href="${escapeHtml(workHref)}">${escapeHtml(workId)}</a>
          <span class="catalogueSeriesMembers__title">${escapeHtml(title)}</span>
          <span class="tagStudioForm__meta">${escapeHtml(positionText)}</span>
          ${isPrimary ? `<span class="tagStudioForm__meta">${escapeHtml(t(state, "members_primary_badge", "primary"))}</span>` : ""}
        </div>
        <div class="catalogueSeriesMembers__actions">
          <a class="tagStudio__button" href="${escapeHtml(workHref)}">${escapeHtml(t(state, "members_action_open", "Open work"))}</a>
          ${isPrimary ? "" : `<button type="button" class="tagStudio__button" data-member-primary="${escapeHtml(workId)}">${escapeHtml(t(state, "members_action_primary", "Make primary"))}</button>`}
          <button type="button" class="tagStudio__button" data-member-remove="${escapeHtml(workId)}">${escapeHtml(t(state, "members_action_remove", "Remove"))}</button>
        </div>
      </div>
    `;
  }).join("");
}

function updateMemberList(state) {
  const members = getCurrentMemberEntries(state);
  const query = normalizeWorkId(state.memberSearchNode.value) || normalizeText(state.memberSearchNode.value).toLowerCase();
  const matches = query
    ? members.filter((entry) => entry.workId.includes(query) || normalizeText(entry.record && entry.record.title).toLowerCase().includes(String(query).toLowerCase()))
    : [];

  const blocks = [];
  if (query) {
    if (matches.length) {
      blocks.push(`<section class="catalogueSeriesMembers__section"><div class="catalogueSeriesMembers__rows">${renderMemberRows(state, matches)}</div></section>`);
    } else {
      blocks.push(`<p class="tagStudioForm__meta">${escapeHtml(t(state, "members_search_no_match", "No matching member work ids."))}</p>`);
    }
  }

  if (!members.length) {
    blocks.push(`<p class="tagStudioForm__meta">${escapeHtml(t(state, "members_empty", "No works currently belong to this series."))}</p>`);
  } else {
    const visible = members.slice(0, MEMBER_LIST_LIMIT);
    const moreText = members.length > MEMBER_LIST_LIMIT
      ? t(state, "members_more_count", "showing {visible} of {total}", { visible: String(visible.length), total: String(members.length) })
      : "";
    blocks.push(`
      <section class="catalogueSeriesMembers__section">
        <div class="tagStudio__headingRow">
          <h3 class="tagStudioForm__key">${escapeHtml(t(state, "members_heading", "member works"))}</h3>
          ${moreText ? `<span class="tagStudioForm__meta">${escapeHtml(moreText)}</span>` : ""}
        </div>
        <div class="catalogueSeriesMembers__rows">${renderMemberRows(state, visible)}</div>
      </section>
    `);
  }

  state.membersMetaNode.textContent = members.length ? `${members.length} total` : "";
  state.membersResultsNode.innerHTML = blocks.join("");
}

function updateEditorState(state) {
  const hasRecord = Boolean(state.currentRecord);
  const errors = hasRecord ? validateDraft(state) : new Map();
  state.validationErrors = errors;
  updateFieldMessages(state, errors);
  updateSummary(state);
  updateMemberList(state);
  if (!hasRecord) setTextWithState(state.buildImpactNode, "");

  const dirty = hasRecord && draftHasChanges(state);
  setTextWithState(state.warningNode, dirty ? t(state, "dirty_warning", "Unsaved source changes.") : "");
  if (!dirty && !errors.size && !state.resultNode.textContent && hasRecord) {
    setTextWithState(state.statusNode, t(state, "save_status_loaded", "Loaded series {series_id}.", { series_id: state.currentSeriesId }));
  }

  state.saveButton.disabled = !hasRecord || state.isSaving || errors.size > 0 || !dirty || !state.serverAvailable;
  state.buildButton.disabled = !hasRecord || state.isSaving || state.isBuilding || errors.size > 0 || !state.serverAvailable;
  state.deleteButton.disabled = !hasRecord || state.isSaving || state.isBuilding || state.isDeleting || !state.serverAvailable;
}

function onFieldInput(state, fieldKey) {
  const node = state.fieldNodes.get(fieldKey);
  if (!node) return;
  state.draft[fieldKey] = node.value;
  updateEditorState(state);
}

function initializeMembershipState(state, seriesId) {
  state.memberSeriesIdsByWorkId = new Map();
  state.baselineMemberSeriesIdsByWorkId = new Map();
  const members = state.currentLookup && Array.isArray(state.currentLookup.member_works) ? state.currentLookup.member_works : [];
  for (const member of members) {
    const workId = normalizeWorkId(member && member.work_id);
    if (!workId) continue;
    const seriesIds = Array.isArray(member && member.series_ids)
      ? member.series_ids.map((seriesId) => normalizeSeriesId(seriesId)).filter(Boolean)
      : getStoredWorkSeriesIds(state, workId);
    if (!seriesIds.includes(seriesId)) continue;
    state.memberSeriesIdsByWorkId.set(workId, seriesIds.slice());
    state.baselineMemberSeriesIdsByWorkId.set(workId, seriesIds.slice());
  }
}

function setLoadedSeries(state, seriesId, record, options = {}) {
  state.currentSeriesId = seriesId;
  state.currentRecord = record;
  state.currentLookup = options.lookup || state.currentLookup;
  state.currentRecordHash = normalizeText(options.recordHash || state.currentRecordHash);
  state.baselineDraft = buildDraftFromRecord(record);
  state.draft = { ...state.baselineDraft };
  initializeMembershipState(state, seriesId);
  applyDraftToInputs(state);
  applyReadonly(state);
  syncUrl(seriesId);
  state.memberSearchNode.value = "";
  state.memberAddNode.value = "";
  state.pendingBuildExtraWorkIds = [];
  setTextWithState(state.membersStatusNode, "");
  setTextWithState(state.contextNode, t(state, "context_loaded", "Editing source metadata for series {series_id}.", { series_id: seriesId }));
  setTextWithState(state.statusNode, t(state, "save_status_loaded", "Loaded series {series_id}.", { series_id: seriesId }));
  setTextWithState(state.warningNode, "");
  if (!options.keepResult) setTextWithState(state.resultNode, "");
  updateEditorState(state);
}

async function refreshBuildPreview(state) {
  if (!state.currentSeriesId || !state.serverAvailable) {
    state.buildPreview = null;
    setTextWithState(state.buildImpactNode, "");
    return;
  }
  try {
    const response = await postJson(CATALOGUE_WRITE_ENDPOINTS.buildPreview, {
      series_id: state.currentSeriesId,
      extra_work_ids: state.pendingBuildExtraWorkIds
    });
    state.buildPreview = response && response.build ? response.build : null;
    setTextWithState(state.buildImpactNode, formatBuildPreview(state, state.buildPreview));
  } catch (error) {
    state.buildPreview = null;
    setTextWithState(state.buildImpactNode, `${t(state, "build_preview_failed", "Build preview unavailable.")} ${normalizeText(error && error.message)}`.trim(), "error");
  }
}

function addWorkToSeries(state) {
  if (!state.currentSeriesId) return;
  const workId = normalizeWorkId(state.memberAddNode.value);
  if (!workId) {
    setTextWithState(state.membersStatusNode, t(state, "members_add_missing", "Enter a work id to add."), "error");
    return;
  }
  const workRecord = state.workSearchById.get(workId);
  if (!workRecord) {
    setTextWithState(state.membersStatusNode, t(state, "members_add_unknown", "Unknown work id: {work_id}.", { work_id }), "error");
    return;
  }
  const current = state.memberSeriesIdsByWorkId.get(workId) || getStoredWorkSeriesIds(state, workId);
  if (current.includes(state.currentSeriesId)) {
    setTextWithState(state.membersStatusNode, t(state, "members_add_exists", "Work {work_id} is already in this series.", { work_id }), "error");
    return;
  }
  state.memberSeriesIdsByWorkId.set(workId, [...current, state.currentSeriesId]);
  state.memberAddNode.value = "";
  setTextWithState(state.membersStatusNode, "");
  updateEditorState(state);
}

function makeMemberPrimary(state, workId) {
  const current = state.memberSeriesIdsByWorkId.get(workId);
  if (!current || !current.includes(state.currentSeriesId)) return;
  const next = [state.currentSeriesId, ...current.filter((seriesId) => seriesId !== state.currentSeriesId)];
  state.memberSeriesIdsByWorkId.set(workId, next);
  updateEditorState(state);
}

function removeMember(state, workId) {
  const currentPrimary = normalizeWorkId(state.draft.primary_work_id);
  if (currentPrimary === workId) {
    setTextWithState(state.membersStatusNode, t(state, "members_remove_blocked", "Change primary_work_id before removing work {work_id}.", { work_id }), "error");
    return;
  }
  const current = state.memberSeriesIdsByWorkId.get(workId);
  if (!current) return;
  state.memberSeriesIdsByWorkId.set(workId, current.filter((seriesId) => seriesId !== state.currentSeriesId));
  setTextWithState(state.membersStatusNode, "");
  updateEditorState(state);
}

async function saveCurrentSeries(state) {
  if (!state.currentRecord) return;
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
  updateEditorState(state);
  setTextWithState(state.statusNode, t(state, "save_status_saving", "Saving source record…"));
  setTextWithState(state.resultNode, "");

  try {
    const previousMembers = new Set(Array.from(state.baselineMemberSeriesIdsByWorkId.keys()).filter((workId) => (state.baselineMemberSeriesIdsByWorkId.get(workId) || []).includes(state.currentSeriesId)));
    const currentMembers = new Set(getCurrentMemberEntries(state).map((entry) => entry.workId));
    const response = await postJson(CATALOGUE_WRITE_ENDPOINTS.saveSeries, buildPayload(state, await buildChangedWorkUpdates(state)));
    const record = response && response.record && typeof response.record === "object" ? response.record : null;
    if (!record) throw new Error("save response missing record");
    state.seriesById.set(state.currentSeriesId, {
      series_id: state.currentSeriesId,
      title: normalizeText(record.title),
      status: normalizeText(record.status),
      primary_work_id: normalizeText(record.primary_work_id),
      record_hash: normalizeText(response.record_hash)
    });
    const workRecords = Array.isArray(response.work_records) ? response.work_records : [];
    workRecords.forEach((entry) => {
      if (!entry || typeof entry !== "object") return;
      const workId = normalizeWorkId(entry.work_id);
      const workRecord = entry.record;
      if (!workId || !workRecord || typeof workRecord !== "object") return;
      state.workSearchById.set(workId, {
        work_id: workId,
        title: normalizeText(workRecord.title),
        year_display: normalizeText(workRecord.year_display),
        status: normalizeText(workRecord.status),
        series_ids: Array.isArray(workRecord.series_ids) ? workRecord.series_ids.slice() : [],
        record_hash: entry.record_hash || state.workSearchById.get(workId)?.record_hash || ""
      });
    });
    state.rebuildPending = Boolean(response.changed);
    if (response.changed) {
      state.pendingBuildExtraWorkIds = Array.from(previousMembers).filter((workId) => !currentMembers.has(workId));
    }
    const lookup = await loadSeriesLookupRecord(state, state.currentSeriesId);
    const lookupRecord = lookup && lookup.series && typeof lookup.series === "object" ? lookup.series : record;
    setLoadedSeries(state, state.currentSeriesId, lookupRecord, {
      recordHash: response.record_hash || normalizeText(lookup && lookup.record_hash) || "",
      keepResult: true,
      lookup
    });
    state.rebuildPending = Boolean(response.changed);
    state.pendingBuildExtraWorkIds = Array.from(previousMembers).filter((workId) => !currentMembers.has(workId));
    await refreshBuildPreview(state);
    const savedAt = normalizeText(response.saved_at_utc || utcTimestamp());
    const resultText = response.changed
      ? t(state, "save_result_success", "Source saved at {saved_at}. Rebuild needed to update public catalogue.", { saved_at: savedAt })
      : t(state, "save_result_unchanged", "Source already matches the current form values.");
    setTextWithState(state.resultNode, resultText, response.changed ? "success" : "");
    setTextWithState(state.statusNode, t(state, "save_status_loaded", "Loaded series {series_id}.", { series_id: state.currentSeriesId }), "success");
  } catch (error) {
    const isConflict = Number(error && error.status) === 409;
    const message = isConflict
      ? t(state, "save_status_conflict", "Source record changed since this page loaded. Reload the series before saving again.")
      : `${t(state, "save_status_failed", "Source save failed.")} ${normalizeText(error && error.message)}`.trim();
    setTextWithState(state.statusNode, message, "error");
  } finally {
    state.isSaving = false;
    updateEditorState(state);
  }
}

async function buildCurrentSeries(state) {
  if (!state.currentRecord || !state.currentSeriesId || !state.serverAvailable) return;
  state.isBuilding = true;
  updateEditorState(state);
  setTextWithState(state.statusNode, t(state, "build_status_running", "Running scoped rebuild…"));
  setTextWithState(state.resultNode, "");
  try {
    const response = await postJson(CATALOGUE_WRITE_ENDPOINTS.buildApply, {
      series_id: state.currentSeriesId,
      extra_work_ids: state.pendingBuildExtraWorkIds
    });
    state.rebuildPending = false;
    state.pendingBuildExtraWorkIds = [];
    await refreshBuildPreview(state);
    const completedAt = normalizeText(response.completed_at_utc || utcTimestamp());
    setTextWithState(state.resultNode, t(state, "build_result_success", "Runtime rebuilt at {completed_at}. Build Activity updated.", { completed_at: completedAt }), "success");
    setTextWithState(state.statusNode, t(state, "build_status_success", "Scoped rebuild completed."), "success");
  } catch (error) {
    setTextWithState(state.statusNode, `${t(state, "build_status_failed", "Scoped rebuild failed.")} ${normalizeText(error && error.message)}`.trim(), "error");
  } finally {
    state.isBuilding = false;
    updateEditorState(state);
  }
}

async function deleteCurrentSeries(state) {
  if (!state.currentRecord || !state.currentSeriesId || !state.serverAvailable) return;
  state.isDeleting = true;
  updateEditorState(state);
  setTextWithState(state.statusNode, t(state, "delete_status_running", "Preparing delete preview…"));
  setTextWithState(state.resultNode, "");
  try {
    const previewResponse = await postJson(CATALOGUE_WRITE_ENDPOINTS.deletePreview, {
      kind: "series",
      series_id: state.currentSeriesId,
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
      kind: "series",
      series_id: state.currentSeriesId,
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

async function saveAndBuildCurrentSeries(state) {
  if (!state.currentRecord) return;
  if (draftHasChanges(state)) {
    await saveCurrentSeries(state);
    if (!state.currentRecord || draftHasChanges(state)) return;
    if (state.statusNode.dataset.state === "error") return;
  }
  await buildCurrentSeries(state);
}

async function openSeriesById(state, requestedSeriesId) {
  const seriesId = normalizeSeriesId(requestedSeriesId);
  if (!seriesId) {
    renderSearchMatches(state, [], t(state, "search_empty", "Enter a series title or id."));
    return;
  }
  const searchRecord = state.seriesById.get(seriesId);
  if (!searchRecord) {
    const matches = getSearchMatches(state, requestedSeriesId);
    if (matches.length) renderSearchMatches(state, matches);
    else renderSearchMatches(state, [], t(state, "unknown_series_error", "Unknown series id: {series_id}.", { series_id }));
    return;
  }
  state.searchNode.value = `${seriesId} ${normalizeText(searchRecord.title)}`.trim();
  setPopupVisibility(state, false);
  state.rebuildPending = false;
  const lookup = await loadSeriesLookupRecord(state, seriesId);
  const record = lookup && lookup.series && typeof lookup.series === "object" ? lookup.series : null;
  if (!record) {
    throw new Error(`series lookup missing record for ${seriesId}`);
  }
  setLoadedSeries(state, seriesId, record, {
    recordHash: normalizeText(lookup.record_hash) || normalizeText(searchRecord.record_hash) || await computeRecordHash(record),
    lookup
  });
  await refreshBuildPreview(state);
}

async function init() {
  const root = document.getElementById("catalogueSeriesRoot");
  const loadingNode = document.getElementById("catalogueSeriesLoading");
  const emptyNode = document.getElementById("catalogueSeriesEmpty");
  const fieldsNode = document.getElementById("catalogueSeriesFields");
  const readonlyNode = document.getElementById("catalogueSeriesReadonly");
  const summaryNode = document.getElementById("catalogueSeriesSummary");
  const runtimeStateNode = document.getElementById("catalogueSeriesRuntimeState");
  const buildImpactNode = document.getElementById("catalogueSeriesBuildImpact");
  const searchNode = document.getElementById("catalogueSeriesSearch");
  const popupNode = document.getElementById("catalogueSeriesPopup");
  const popupListNode = document.getElementById("catalogueSeriesPopupList");
  const openButton = document.getElementById("catalogueSeriesOpen");
  const saveButton = document.getElementById("catalogueSeriesSave");
  const buildButton = document.getElementById("catalogueSeriesBuild");
  const deleteButton = document.getElementById("catalogueSeriesDelete");
  const saveModeNode = document.getElementById("catalogueSeriesSaveMode");
  const contextNode = document.getElementById("catalogueSeriesContext");
  const statusNode = document.getElementById("catalogueSeriesStatus");
  const warningNode = document.getElementById("catalogueSeriesWarning");
  const resultNode = document.getElementById("catalogueSeriesResult");
  const metaNode = document.getElementById("catalogueSeriesMeta");
  const membersHeadingNode = document.getElementById("catalogueSeriesMembersHeading");
  const memberSearchNode = document.getElementById("catalogueSeriesMemberSearch");
  const memberAddNode = document.getElementById("catalogueSeriesMemberAdd");
  const memberAddButton = document.getElementById("catalogueSeriesMemberAddButton");
  const membersMetaNode = document.getElementById("catalogueSeriesMembersMeta");
  const membersStatusNode = document.getElementById("catalogueSeriesMembersStatus");
  const membersResultsNode = document.getElementById("catalogueSeriesMembersResults");
  if (!root || !loadingNode || !emptyNode || !fieldsNode || !readonlyNode || !summaryNode || !runtimeStateNode || !buildImpactNode || !searchNode || !popupNode || !popupListNode || !openButton || !saveButton || !buildButton || !deleteButton || !saveModeNode || !contextNode || !statusNode || !warningNode || !resultNode || !metaNode || !membersHeadingNode || !memberSearchNode || !memberAddNode || !memberAddButton || !membersMetaNode || !membersStatusNode || !membersResultsNode) {
    return;
  }

  const state = {
    config: null,
    seriesById: new Map(),
    workSearchById: new Map(),
    currentLookup: null,
    currentSeriesId: "",
    currentRecord: null,
    currentRecordHash: "",
    baselineDraft: null,
    draft: {},
    validationErrors: new Map(),
    rebuildPending: false,
    pendingBuildExtraWorkIds: [],
    buildPreview: null,
    isSaving: false,
    isBuilding: false,
    isDeleting: false,
    serverAvailable: false,
    fieldNodes: new Map(),
    fieldStatusNodes: new Map(),
    readonlyNodes: new Map(),
    memberSeriesIdsByWorkId: new Map(),
    baselineMemberSeriesIdsByWorkId: new Map(),
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
    summaryNode,
    runtimeStateNode,
    buildImpactNode,
    metaNode,
    memberSearchNode,
    memberAddNode,
    membersMetaNode,
    membersStatusNode,
    membersResultsNode
  };

  EDITABLE_FIELDS.forEach((field) => renderField(field, fieldsNode, state));
  READONLY_FIELDS.forEach((field) => renderReadonlyField(field, readonlyNode, state));

  try {
    const config = await loadStudioConfig();
    state.config = config;
    searchNode.placeholder = t(state, "search_placeholder", "find series by title");
    openButton.textContent = t(state, "open_button", "Open");
    saveButton.textContent = t(state, "save_button", "Save Source");
    buildButton.textContent = t(state, "build_button", "Save + Rebuild");
    deleteButton.textContent = t(state, "delete_button", "Delete Source");
    membersHeadingNode.textContent = t(state, "members_heading", "member works");
    memberSearchNode.placeholder = t(state, "members_search_placeholder", "find member work by id");
    memberAddNode.placeholder = t(state, "members_add_placeholder", "add work by id");
    memberAddButton.textContent = t(state, "members_add_button", "Add Work");

    const [seriesPayload, worksPayload, serverAvailable] = await Promise.all([
      loadStudioLookupJson(config, "catalogue_lookup_series_search", { cache: "no-store" }),
      loadStudioLookupJson(config, "catalogue_lookup_work_search", { cache: "no-store" }),
      probeCatalogueHealth()
    ]);

    const seriesItems = Array.isArray(seriesPayload && seriesPayload.items) ? seriesPayload.items : [];
    seriesItems.forEach((record) => {
      if (!record || typeof record !== "object") return;
      const seriesId = normalizeSeriesId(record.series_id);
      if (!seriesId) return;
      state.seriesById.set(seriesId, record);
    });
    const workItems = Array.isArray(worksPayload && worksPayload.items) ? worksPayload.items : [];
    workItems.forEach((record) => {
      if (!record || typeof record !== "object") return;
      const workId = normalizeWorkId(record.work_id);
      if (!workId) return;
      state.workSearchById.set(workId, record);
    });
    state.serverAvailable = Boolean(serverAvailable);
    saveModeNode.textContent = buildSaveModeText(config, serverAvailable ? "post" : "offline", (cfg, key, fallback, tokens) => getStudioText(cfg, `catalogue_series_editor.${key}`, fallback, tokens));
    if (!state.serverAvailable) {
      setTextWithState(statusNode, t(state, "save_mode_unavailable_hint", "Local catalogue server unavailable. Save is disabled."), "warn");
    }

    searchNode.addEventListener("input", () => {
      const query = searchNode.value;
      if (!normalizeText(query)) {
        renderSearchMatches(state, [], "");
        return;
      }
      const matches = getSearchMatches(state, query);
      if (!matches.length) {
        renderSearchMatches(state, [], t(state, "search_no_match", "No matching series records."));
        return;
      }
      renderSearchMatches(state, matches);
    });

    searchNode.addEventListener("keydown", (event) => {
      if (event.key !== "Enter") return;
      event.preventDefault();
      const matches = getSearchMatches(state, searchNode.value);
      if (matches[0]) {
        openSeriesById(state, matches[0].seriesId).catch((error) => console.warn("catalogue_series_editor: failed to open requested series", error));
      }
    });

    popupListNode.addEventListener("click", (event) => {
      const button = event.target && event.target.closest ? event.target.closest("[data-series-id]") : null;
      if (!button) return;
      openSeriesById(state, button.getAttribute("data-series-id")).catch((error) => console.warn("catalogue_series_editor: failed to open selected series", error));
    });

    openButton.addEventListener("click", () => {
      const matches = getSearchMatches(state, searchNode.value);
      if (matches[0]) {
        openSeriesById(state, matches[0].seriesId).catch((error) => console.warn("catalogue_series_editor: failed to open requested series", error));
      }
    });
    saveButton.addEventListener("click", () => saveCurrentSeries(state).catch((error) => console.warn("catalogue_series_editor: unexpected save failure", error)));
    buildButton.addEventListener("click", () => saveAndBuildCurrentSeries(state).catch((error) => console.warn("catalogue_series_editor: unexpected save/build failure", error)));
    deleteButton.addEventListener("click", () => deleteCurrentSeries(state).catch((error) => console.warn("catalogue_series_editor: unexpected delete failure", error)));
    memberSearchNode.addEventListener("input", () => updateMemberList(state));
    memberAddButton.addEventListener("click", () => addWorkToSeries(state));
    memberAddNode.addEventListener("keydown", (event) => {
      if (event.key !== "Enter") return;
      event.preventDefault();
      addWorkToSeries(state);
    });
    membersResultsNode.addEventListener("click", (event) => {
      const primaryButton = event.target && event.target.closest ? event.target.closest("[data-member-primary]") : null;
      if (primaryButton) {
        makeMemberPrimary(state, normalizeWorkId(primaryButton.getAttribute("data-member-primary")));
        return;
      }
      const removeButton = event.target && event.target.closest ? event.target.closest("[data-member-remove]") : null;
      if (removeButton) {
        removeMember(state, normalizeWorkId(removeButton.getAttribute("data-member-remove")));
      }
    });

    document.addEventListener("click", (event) => {
      if (event.target === searchNode || popupNode.contains(event.target)) return;
      setPopupVisibility(state, false);
    });

    const requestedSeriesId = normalizeSeriesId(new URLSearchParams(window.location.search).get("series"));
    if (requestedSeriesId && state.seriesById.has(requestedSeriesId)) {
      openSeriesById(state, requestedSeriesId).catch((error) => console.warn("catalogue_series_editor: failed to open requested series", error));
    } else {
      setTextWithState(contextNode, t(state, "missing_series_param", "Search for a series by title."));
      updateSummary(state);
      updateEditorState(state);
    }

    root.hidden = false;
    loadingNode.hidden = true;
  } catch (error) {
    console.warn("catalogue_series_editor: init failed", error);
    try {
      const config = await loadStudioConfig();
      loadingNode.textContent = getStudioText(config, "catalogue_series_editor.load_failed_error", "Failed to load catalogue source data for the series editor.");
    } catch (_configError) {
      loadingNode.textContent = "Failed to load catalogue source data for the series editor.";
    }
  }
}

init();
