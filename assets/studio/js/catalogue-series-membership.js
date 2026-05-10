import { getStudioRoute } from "./studio-config.js";
import {
  computeRecordHash,
  displayValue,
  stableStringify
} from "./catalogue-editor-records.js";
import {
  normalizeSeriesId,
  normalizeText,
  normalizeWorkId
} from "./catalogue-series-fields.js";

const MEMBER_LIST_LIMIT = 10;

function escapeHtml(value) {
  return normalizeText(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function text(options, key, fallback, tokens = null) {
  if (options && typeof options.text === "function") {
    return options.text(key, fallback, tokens);
  }
  if (!tokens) return fallback;
  return Object.entries(tokens).reduce((value, [token, replacement]) => {
    return value.replace(new RegExp(`\\{${token}\\}`, "g"), () => replacement == null ? "" : String(replacement));
  }, fallback);
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

function setFieldNodeValue(options, node, value) {
  if (options && typeof options.setFieldNodeValue === "function") {
    options.setFieldNodeValue(node, value);
    return;
  }
  if (!node) return;
  const normalized = normalizeText(value);
  if ("value" in node) node.value = normalized;
  else node.textContent = displayValue(normalized);
}

export function getStoredSeriesWorkIds(state, workId) {
  const record = state.workSearchById.get(workId);
  const values = record && Array.isArray(record.series_ids) ? record.series_ids : [];
  return values.map((seriesId) => normalizeSeriesId(seriesId)).filter(Boolean);
}

export function getEditableSeriesMemberEntries(state) {
  return Array.from(state.memberSeriesIdsByWorkId.entries())
    .map(([workId, seriesIds]) => ({ workId, seriesIds: seriesIds.slice() }))
    .sort((a, b) => a.workId.localeCompare(b.workId, undefined, { numeric: true, sensitivity: "base" }));
}

export function getCurrentSeriesMemberEntries(state) {
  return getEditableSeriesMemberEntries(state)
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

export function seriesMembershipHasChanges(state) {
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

export function initializeSeriesMembershipState(state, seriesId) {
  state.memberSeriesIdsByWorkId = new Map();
  state.baselineMemberSeriesIdsByWorkId = new Map();
  const members = state.currentLookup && Array.isArray(state.currentLookup.member_works) ? state.currentLookup.member_works : [];
  for (const member of members) {
    const workId = normalizeWorkId(member && member.work_id);
    if (!workId) continue;
    const seriesIds = Array.isArray(member && member.series_ids)
      ? member.series_ids.map((candidateSeriesId) => normalizeSeriesId(candidateSeriesId)).filter(Boolean)
      : getStoredSeriesWorkIds(state, workId);
    if (!seriesIds.includes(seriesId)) continue;
    state.memberSeriesIdsByWorkId.set(workId, seriesIds.slice());
    state.baselineMemberSeriesIdsByWorkId.set(workId, seriesIds.slice());
  }
}

export function buildSavedSeriesMembershipLookup(state, record, recordHash) {
  return {
    ...(state.currentLookup || {}),
    series: record,
    record_hash: recordHash,
    member_works: getCurrentSeriesMemberEntries(state).map((entry) => ({
      work_id: entry.workId,
      series_ids: entry.seriesIds.slice()
    }))
  };
}

export async function buildChangedSeriesWorkUpdates(state) {
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

export function renderSeriesMemberRows(state, entries, options = {}) {
  const workEditorBase = getStudioRoute(state.config, "catalogue_work_editor");
  return entries.map((entry) => {
    const workId = entry.workId;
    const title = displayValue(entry.record && entry.record.title);
    const isPrimary = entry.position === 0;
    const workHref = `${workEditorBase}?work=${encodeURIComponent(workId)}`;
    const positionText = text(options, "members_position", "position {position}", { position: String(entry.position + 1) });
    return `
      <div class="catalogueSeriesMembers__row">
        <div class="catalogueSeriesMembers__meta">
          <a class="catalogueSeriesMembers__link" href="${escapeHtml(workHref)}">${escapeHtml(workId)}</a>
          <span class="catalogueSeriesMembers__title">${escapeHtml(title)}</span>
          <span class="tagStudioForm__meta">${escapeHtml(positionText)}</span>
          ${isPrimary ? `<span class="tagStudioForm__meta">${escapeHtml(text(options, "members_primary_badge", "primary"))}</span>` : ""}
        </div>
        <div class="catalogueSeriesMembers__actions">
          ${isPrimary ? "" : `<button type="button" class="tagStudio__button" data-member-primary="${escapeHtml(workId)}">${escapeHtml(text(options, "members_action_primary", "Make primary"))}</button>`}
          <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" data-member-remove="${escapeHtml(workId)}">${escapeHtml(text(options, "members_action_remove", "Remove"))}</button>
        </div>
      </div>
    `;
  }).join("");
}

export function updateSeriesMemberList(state, options = {}) {
  const memberEditingEnabled = Boolean(state.currentRecord) && !state.isSaving && !state.isBuilding && !state.isDeleting;
  state.memberSearchNode.disabled = !memberEditingEnabled;
  state.memberAddNode.disabled = !memberEditingEnabled;
  state.memberAddButton.disabled = !memberEditingEnabled;
  const members = getCurrentSeriesMemberEntries(state);
  const truncated = members.length > MEMBER_LIST_LIMIT;
  const query = normalizeWorkId(state.memberSearchNode.value) || normalizeText(state.memberSearchNode.value).toLowerCase();
  const matches = query
    ? members.filter((entry) => entry.workId.includes(query) || normalizeText(entry.record && entry.record.title).toLowerCase().includes(String(query).toLowerCase()))
    : [];
  const moreText = truncated
    ? text(options, "members_more_count", "showing {visible} of {total}", { visible: String(MEMBER_LIST_LIMIT), total: String(members.length) })
    : "";

  const blocks = [];
  if (query) {
    if (matches.length) {
      blocks.push(`<section class="catalogueSeriesMembers__section"><div class="catalogueSeriesMembers__rows">${renderSeriesMemberRows(state, matches, options)}</div></section>`);
    } else {
      blocks.push(`<p class="tagStudioForm__meta">${escapeHtml(text(options, "members_search_no_match", "No matching member work ids."))}</p>`);
    }
  }

  if (!members.length) {
    blocks.push(`<p class="tagStudioForm__meta">${escapeHtml(text(options, "members_empty", "No works currently belong to this series."))}</p>`);
  } else {
    const visible = members.slice(0, MEMBER_LIST_LIMIT);
    blocks.push(`
      <section class="catalogueSeriesMembers__section">
        <div class="catalogueSeriesMembers__rows">${renderSeriesMemberRows(state, visible, options)}</div>
      </section>
    `);
  }

  state.memberSearchRowNode.hidden = !truncated;
  state.memberSearchMetaNode.textContent = moreText;
  if (!truncated && state.memberSearchNode.value) state.memberSearchNode.value = "";
  state.membersMetaNode.textContent = members.length ? `${members.length} total` : "";
  state.membersResultsNode.innerHTML = blocks.join("");
}

export function addSeriesMember(state, options = {}) {
  if (!state.currentSeriesId) return false;
  const workId = normalizeWorkId(state.memberAddNode.value);
  if (!workId) {
    setTextWithState(options, state.membersStatusNode, text(options, "members_add_missing", "Enter a work id to add."), "error");
    return false;
  }
  const workRecord = state.workSearchById.get(workId);
  if (!workRecord) {
    setTextWithState(options, state.membersStatusNode, text(options, "members_add_unknown", "Unknown work id: {work_id}.", { work_id: workId }), "error");
    return false;
  }
  const current = state.memberSeriesIdsByWorkId.get(workId) || getStoredSeriesWorkIds(state, workId);
  if (current.includes(state.currentSeriesId)) {
    setTextWithState(options, state.membersStatusNode, text(options, "members_add_exists", "Work {work_id} is already in this series.", { work_id: workId }), "error");
    return false;
  }
  const currentMemberCount = getCurrentSeriesMemberEntries(state).length;
  state.memberSeriesIdsByWorkId.set(workId, [...current, state.currentSeriesId]);
  if (!currentMemberCount && !normalizeWorkId(state.draft.primary_work_id)) {
    state.draft.primary_work_id = workId;
    setFieldNodeValue(options, state.fieldNodes.get("primary_work_id"), workId);
  }
  state.memberAddNode.value = "";
  setTextWithState(options, state.membersStatusNode, "");
  return true;
}

export function makeSeriesMemberPrimary(state, workId) {
  const current = state.memberSeriesIdsByWorkId.get(workId);
  if (!current || !current.includes(state.currentSeriesId)) return false;
  const next = [state.currentSeriesId, ...current.filter((seriesId) => seriesId !== state.currentSeriesId)];
  state.memberSeriesIdsByWorkId.set(workId, next);
  return true;
}

export function removeSeriesMember(state, workId, options = {}) {
  const currentPrimary = normalizeWorkId(state.draft.primary_work_id);
  if (currentPrimary === workId) {
    setTextWithState(options, state.membersStatusNode, text(options, "members_remove_blocked", "Change primary_work_id before removing work {work_id}.", { work_id: workId }), "error");
    return false;
  }
  const current = state.memberSeriesIdsByWorkId.get(workId);
  if (!current) return false;
  state.memberSeriesIdsByWorkId.set(workId, current.filter((seriesId) => seriesId !== state.currentSeriesId));
  setTextWithState(options, state.membersStatusNode, "");
  return true;
}
