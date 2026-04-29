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
  SERIES_EDITABLE_FIELDS as EDITABLE_FIELDS,
  SERIES_READONLY_FIELDS as READONLY_FIELDS,
  buildSaveSeriesPayload,
  buildSeriesDraftFromRecord,
  normalizeSeriesId,
  normalizeText,
  normalizeWorkId,
  validateSeriesDraft
} from "./catalogue-series-fields.js";

const SEARCH_LIMIT = 20;
const MEMBER_LIST_LIMIT = 10;

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
  return readiness && Array.isArray(readiness.items) ? readiness.items : [];
}

function renderReadiness(state) {
  if (!state.readinessNode || !state.currentRecord) {
    if (state.readinessNode) state.readinessNode.innerHTML = "";
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
    const proseAction = normalizeText(item && item.key) === "series_prose";
    const proseActionDisabled = actionDisabled || (proseAction && itemStatus !== "ready");
    const disabledNote = proseAction && actionDisabled
      ? (draftHasChanges(state)
        ? t(state, "readiness_save_first", "Save source changes before importing prose.")
        : t(state, "readiness_action_busy", "Wait for the current save or rebuild to finish."))
      : "";
    const proseActionLabel = t(state, "prose_import_button", "Import staged prose");
    return `
      <div class="tagStudioForm__field">
        <span class="tagStudioForm__label">${escapeHtml(title)}</span>
        <div class="tagStudio__input tagStudio__input--readonlyDisplay catalogueReadiness__body">
          <span class="catalogueReadiness__summary" data-tone="${escapeHtml(tone)}">${escapeHtml(summary)}</span>
          ${sourcePath ? `<span class="tagStudioForm__meta catalogueReadiness__path">${escapeHtml(sourcePath)}</span>` : ""}
          ${nextStep ? `<span class="tagStudioForm__meta">${escapeHtml(nextStep)}</span>` : ""}
          ${proseAction ? `<div class="catalogueReadiness__actions"><button type="button" class="tagStudio__button" data-prose-import="series" ${proseActionDisabled ? "disabled" : ""}>${escapeHtml(proseActionLabel)}</button></div>` : ""}
          ${disabledNote ? `<span class="tagStudioForm__meta">${escapeHtml(disabledNote)}</span>` : ""}
        </div>
      </div>
    `;
  }).join("");
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
  if (field.type === "textarea") wrapper.classList.add("tagStudioForm__field--topAligned", "catalogueWorkForm__field--topAligned");
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
    input.type = field.type === "date" ? "date" : "text";
    if (field.type === "number") {
      input.inputMode = field.step && String(field.step).includes(".") ? "decimal" : "numeric";
    }
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

  const value = document.createElement("div");
  value.className = "tagStudio__input tagStudio__input--readonlyDisplay";
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
  return validateSeriesDraft(state.draft, {
    currentMemberWorkIds: new Set(getCurrentMemberEntries(state).map((entry) => entry.workId)),
    t: (key, fallback, tokens = null) => t(state, key, fallback, tokens)
  });
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
  return buildSaveSeriesPayload(state, workUpdates);
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

function applySaveBuildOutcome(state, response) {
  const build = response && response.build && typeof response.build === "object" ? response.build : null;
  if (!response || !response.build_requested || !build) {
    state.rebuildPending = Boolean(response && response.changed);
    return { kind: response && response.changed ? "saved" : "unchanged", stamp: normalizeText(response && response.saved_at_utc) || utcTimestamp() };
  }
  if (build.ok) {
    state.rebuildPending = false;
    state.pendingBuildExtraWorkIds = [];
    return { kind: "saved_and_updated", stamp: normalizeText(build.completed_at_utc || response.saved_at_utc) || utcTimestamp() };
  }
  state.rebuildPending = true;
  return {
    kind: "saved_update_failed",
    stamp: normalizeText(response.saved_at_utc) || utcTimestamp(),
    error: normalizeText(build.error)
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
  const localMedia = build.local_media && typeof build.local_media === "object" ? build.local_media : null;
  const localCounts = localMedia && typeof localMedia.counts === "object" ? localMedia.counts : null;
  const workText = workIds.length ? workIds.join(", ") : "none";
  const seriesText = seriesIds.length ? seriesIds.join(", ") : "none";
  const searchText = build.rebuild_search ? t(state, "build_preview_search_yes", "yes") : t(state, "build_preview_search_no", "no");
  const baseText = t(state, "build_preview_template", "Build preview: work {work_ids}; series {series_ids}; catalogue search {search_rebuild}.", {
    work_ids: workText,
    series_ids: seriesText,
    search_rebuild: searchText
  });
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
      <div class="tagStudio__input tagStudio__input--readonlyDisplay">
        ${record ? `<a href="${escapeHtml(publicHref)}" target="_blank" rel="noopener">${escapeHtml(record.series_id)}</a>` : "—"}
      </div>
    </div>
    <div class="tagStudioForm__field">
      <span class="tagStudioForm__label">${escapeHtml(t(state, "summary_member_count", "member works"))}</span>
      <div class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(String(memberCount))}</div>
    </div>
  `;
  state.runtimeStateNode.textContent = state.rebuildPending
    ? t(state, "summary_rebuild_needed", "source saved; site update pending")
    : t(state, "summary_rebuild_current", "source and public catalogue are aligned in this session");
  renderReadiness(state);
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
          ${isPrimary ? "" : `<button type="button" class="tagStudio__button" data-member-primary="${escapeHtml(workId)}">${escapeHtml(t(state, "members_action_primary", "Make primary"))}</button>`}
          <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" data-member-remove="${escapeHtml(workId)}">${escapeHtml(t(state, "members_action_remove", "Remove"))}</button>
        </div>
      </div>
    `;
  }).join("");
}

function updateMemberList(state) {
  const members = getCurrentMemberEntries(state);
  const truncated = members.length > MEMBER_LIST_LIMIT;
  const query = normalizeWorkId(state.memberSearchNode.value) || normalizeText(state.memberSearchNode.value).toLowerCase();
  const matches = query
    ? members.filter((entry) => entry.workId.includes(query) || normalizeText(entry.record && entry.record.title).toLowerCase().includes(String(query).toLowerCase()))
    : [];
  const moreText = truncated
    ? t(state, "members_more_count", "showing {visible} of {total}", { visible: String(MEMBER_LIST_LIMIT), total: String(members.length) })
    : "";

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
    blocks.push(`
      <section class="catalogueSeriesMembers__section">
        <div class="catalogueSeriesMembers__rows">${renderMemberRows(state, visible)}</div>
      </section>
    `);
  }

  state.memberSearchRowNode.hidden = !truncated;
  state.memberSearchMetaNode.textContent = moreText;
  if (!truncated && state.memberSearchNode.value) state.memberSearchNode.value = "";
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
  state.deleteButton.disabled = !hasRecord || state.isSaving || state.isBuilding || state.isDeleting || !state.serverAvailable;
  updatePublishControls(state, { hasRecord, dirty, errors });
  renderReadiness(state);
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
  state.baselineDraft = buildSeriesDraftFromRecord(record);
  state.draft = { ...state.baselineDraft };
  initializeMembershipState(state, seriesId);
  applyDraftToInputs(state);
  applyReadonly(state);
  syncUrl(seriesId);
  state.memberSearchNode.value = "";
  state.memberAddNode.value = "";
  state.pendingBuildExtraWorkIds = [];
  if (state.applyBuildNode) state.applyBuildNode.checked = true;
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
    renderReadiness(state);
    return;
  }
  try {
    const response = await postJson(CATALOGUE_WRITE_ENDPOINTS.buildPreview, {
      series_id: state.currentSeriesId,
      extra_work_ids: state.pendingBuildExtraWorkIds
    });
    state.buildPreview = response && response.build ? response.build : null;
    setTextWithState(state.buildImpactNode, formatBuildPreview(state, state.buildPreview));
    renderReadiness(state);
  } catch (error) {
    state.buildPreview = null;
    setTextWithState(state.buildImpactNode, `${t(state, "build_preview_failed", "Build preview unavailable.")} ${normalizeText(error && error.message)}`.trim(), "error");
    renderReadiness(state);
  }
}

async function importSeriesProse(state) {
  if (!state.currentRecord || !state.currentSeriesId || !state.serverAvailable) return;
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
      target_kind: "series",
      series_id: state.currentSeriesId
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
      target_kind: "series",
      series_id: state.currentSeriesId,
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
    if (applyBuildRequested(state) && state.rebuildPending) {
      await buildCurrentSeries(state);
      return;
    }
    setTextWithState(state.statusNode, t(state, "save_status_no_changes", "No changes to save."));
    setTextWithState(state.resultNode, t(state, "save_result_unchanged", "Source already matches the current form values."));
    updateEditorState(state);
    return;
  }

  state.isSaving = true;
  updateEditorState(state);
  setTextWithState(
    state.statusNode,
    applyBuildRequested(state)
      ? t(state, "save_status_saving_and_updating", "Saving source record and updating site…")
      : t(state, "save_status_saving", "Saving source record…")
  );
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
    const outcome = applySaveBuildOutcome(state, response);
    if (response.changed && outcome.kind !== "saved_and_updated") {
      state.pendingBuildExtraWorkIds = Array.from(previousMembers).filter((workId) => !currentMembers.has(workId));
    }
    const lookup = await loadSeriesLookupRecord(state, state.currentSeriesId);
    const lookupRecord = lookup && lookup.series && typeof lookup.series === "object" ? lookup.series : record;
    setLoadedSeries(state, state.currentSeriesId, lookupRecord, {
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
      setTextWithState(state.statusNode, t(state, "save_status_loaded", "Loaded series {series_id}.", { series_id: state.currentSeriesId }), "success");
    }
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
  setTextWithState(state.statusNode, t(state, "build_status_running", "Updating site…"));
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
    setTextWithState(state.resultNode, t(state, "build_result_success", "Public catalogue updated at {completed_at}. Build Activity updated.", { completed_at: completedAt }), "success");
    setTextWithState(state.statusNode, t(state, "build_status_success", "Site update completed."), "success");
  } catch (error) {
    setTextWithState(state.statusNode, `${t(state, "build_status_failed", "Site update failed.")} ${normalizeText(error && error.message)}`.trim(), "error");
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
  const readinessNode = document.getElementById("catalogueSeriesReadiness");
  const runtimeStateNode = document.getElementById("catalogueSeriesRuntimeState");
  const buildImpactNode = document.getElementById("catalogueSeriesBuildImpact");
  const searchNode = document.getElementById("catalogueSeriesSearch");
  const popupNode = document.getElementById("catalogueSeriesPopup");
  const popupListNode = document.getElementById("catalogueSeriesPopupList");
  const openButton = document.getElementById("catalogueSeriesOpen");
  const saveButton = document.getElementById("catalogueSeriesSave");
  const buildButton = document.getElementById("catalogueSeriesBuild");
  const deleteButton = document.getElementById("catalogueSeriesDelete");
  const runtimeActionsNode = buildButton ? buildButton.closest(".catalogueWorkPage__runtimeActions") : null;
  const applyBuildNode = document.getElementById("catalogueSeriesApplyBuild");
  const applyBuildLabelNode = document.getElementById("catalogueSeriesApplyBuildLabel");
  const saveModeNode = document.getElementById("catalogueSeriesSaveMode");
  const contextNode = document.getElementById("catalogueSeriesContext");
  const statusNode = document.getElementById("catalogueSeriesStatus");
  const warningNode = document.getElementById("catalogueSeriesWarning");
  const resultNode = document.getElementById("catalogueSeriesResult");
  const metaNode = document.getElementById("catalogueSeriesMeta");
  const membersHeadingNode = document.getElementById("catalogueSeriesMembersHeading");
  const memberSearchRowNode = document.getElementById("catalogueSeriesMemberSearchRow");
  const memberSearchNode = document.getElementById("catalogueSeriesMemberSearch");
  const memberSearchMetaNode = document.getElementById("catalogueSeriesMemberSearchMeta");
  const memberAddNode = document.getElementById("catalogueSeriesMemberAdd");
  const memberAddButton = document.getElementById("catalogueSeriesMemberAddButton");
  const membersMetaNode = document.getElementById("catalogueSeriesMembersMeta");
  const membersStatusNode = document.getElementById("catalogueSeriesMembersStatus");
  const membersResultsNode = document.getElementById("catalogueSeriesMembersResults");
  if (!root || !loadingNode || !emptyNode || !fieldsNode || !readonlyNode || !summaryNode || !readinessNode || !runtimeStateNode || !buildImpactNode || !searchNode || !popupNode || !popupListNode || !openButton || !saveButton || !buildButton || !deleteButton || !runtimeActionsNode || !applyBuildNode || !applyBuildLabelNode || !saveModeNode || !contextNode || !statusNode || !warningNode || !resultNode || !metaNode || !membersHeadingNode || !memberSearchRowNode || !memberSearchNode || !memberSearchMetaNode || !memberAddNode || !memberAddButton || !membersMetaNode || !membersStatusNode || !membersResultsNode) {
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
    applyBuildNode,
    applyBuildLabelNode,
    runtimeActionsNode,
    saveModeNode,
    contextNode,
    statusNode,
    warningNode,
    resultNode,
    summaryNode,
    readinessNode,
    runtimeStateNode,
    buildImpactNode,
    metaNode,
    memberSearchRowNode,
    memberSearchNode,
    memberSearchMetaNode,
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
    saveButton.textContent = t(state, "save_button", "Save");
    buildButton.textContent = t(state, "build_button", "Update site now");
    applyBuildLabelNode.textContent = t(state, "build_button", "Update site now");
    deleteButton.textContent = t(state, "delete_button", "Delete");
    membersHeadingNode.textContent = t(state, "members_heading", "member works");
    memberSearchNode.placeholder = t(state, "members_search_placeholder", "find member work by id");
    memberAddNode.placeholder = t(state, "members_add_placeholder", "add work by id");
    memberAddButton.textContent = t(state, "members_add_button", "Add");

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
    readinessNode.addEventListener("click", (event) => {
      const button = event.target && event.target.closest ? event.target.closest("[data-prose-import]") : null;
      if (!button) return;
      importSeriesProse(state).catch((error) => console.warn("catalogue_series_editor: unexpected prose import failure", error));
    });
    saveButton.addEventListener("click", () => saveCurrentSeries(state).catch((error) => console.warn("catalogue_series_editor: unexpected save failure", error)));
    buildButton.addEventListener("click", () => buildCurrentSeries(state).catch((error) => console.warn("catalogue_series_editor: unexpected save/build failure", error)));
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
