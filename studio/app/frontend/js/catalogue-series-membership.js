import {
  createRecordList,
  createRecordListActions
} from "/shared/frontend/js/record-list.js";
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

function text(options, key, fallback, tokens = null) {
  if (options && typeof options.text === "function") {
    return options.text(key, fallback, tokens);
  }
  if (!tokens) return fallback;
  return Object.entries(tokens).reduce((value, [token, replacement]) => {
    return value.replace(new RegExp(`\\{${token}\\}`, "g"), () => replacement == null ? "" : String(replacement));
  }, fallback);
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

function clearMemberList(state) {
  if (state.membersListController && typeof state.membersListController.destroy === "function") {
    state.membersListController.destroy();
  } else if (state.membersResultsNode) {
    state.membersResultsNode.innerHTML = "";
  }
  state.membersListController = null;
}

function clearMemberActions(state) {
  if (state.membersActionsController && typeof state.membersActionsController.destroy === "function") {
    state.membersActionsController.destroy();
  } else if (state.membersActionsNode) {
    state.membersActionsNode.innerHTML = "";
  }
  state.membersActionsController = null;
}

function selectedMemberWorkId(records, selectedId) {
  return records.some((record) => record.workId === selectedId) ? selectedId : "";
}

function memberRecords(state, options) {
  return getCurrentSeriesMemberEntries(state).map((entry) => ({
    workId: entry.workId,
    title: displayValue(entry.record && entry.record.title),
    position: text(options, "members_position", "position {position}", { position: String(entry.position + 1) }),
    primary: entry.position === 0 ? text(options, "members_primary_badge", "primary") : ""
  }));
}

function renderMemberActions(state, options, list = null) {
  clearMemberActions(state);
  if (!state.membersActionsNode) return;
  const actions = [
    {
      key: "edit",
      label: "✏️",
      title: text(options, "members_action_edit_unavailable", "Edit member work is not implemented yet."),
      ariaLabel: text(options, "members_action_edit", "Edit"),
      appearance: "icon",
      disabled: () => true
    },
    {
      key: "delete",
      label: "🗑️",
      title: text(options, "members_action_delete_unavailable", "Delete member work is not implemented yet."),
      ariaLabel: text(options, "members_action_delete", "Delete"),
      appearance: "icon",
      tone: "danger",
      disabled: () => true
    },
    {
      key: "new",
      label: "📄",
      title: text(options, "members_action_new_unavailable", "New member work is not implemented yet."),
      ariaLabel: text(options, "members_action_new", "New"),
      appearance: "icon",
      requiresSelection: false,
      disabled: () => true
    }
  ];
  state.membersActionsController = createRecordListActions(state.membersActionsNode, {
    id: "catalogueSeriesMembersActionsList",
    list,
    actions
  });
}

export function updateSeriesMemberList(state, options = {}) {
  if (!state.membersResultsNode) return;
  clearMemberList(state);
  const records = memberRecords(state, options);
  state.selectedMemberWorkId = selectedMemberWorkId(records, state.selectedMemberWorkId);
  state.membersMetaNode.textContent = records.length ? `${records.length} total` : "";
  state.membersListController = createRecordList(state.membersResultsNode, {
    id: "catalogueSeriesMembers",
    records,
    columns: [
      {
        key: "workId",
        label: text(options, "members_work_id_heading", "work"),
        width: "minmax(5rem, 7rem)",
        truncate: false
      },
      {
        key: "title",
        label: text(options, "members_title_heading", "title"),
        width: "minmax(0, 1fr)",
        truncate: true
      },
      {
        key: "position",
        label: text(options, "members_position_heading", "position"),
        width: "minmax(6rem, 8rem)",
        truncate: false
      },
      {
        key: "primary",
        label: text(options, "members_primary_heading", "primary"),
        width: "5rem",
        truncate: false
      }
    ],
    showHeader: false,
    emptyText: text(options, "members_empty", "No works currently belong to this series."),
    selectionMode: "single",
    initialSelection: state.selectedMemberWorkId,
    getRecordId: (record) => record.workId,
    onSelectionChange: ({ selection }) => {
      state.selectedMemberWorkId = selection && selection.record ? selection.record.workId : "";
    }
  });
  renderMemberActions(state, options, state.membersListController);
}
