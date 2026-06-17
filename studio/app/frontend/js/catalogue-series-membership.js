import {
  buildStudioRouteUrl
} from "./studio-config.js";
import {
  openConfirmModal,
  openNoticeModal
} from "./studio-modal.js";
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
  buildWorkThumbPreview
} from "./catalogue-media-preview.js";
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
      return {
        workId,
        seriesIds,
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
  return getCurrentSeriesMemberEntries(state).map((entry) => {
    const preview = buildWorkThumbPreview(state.mediaConfig, entry.workId);
    return {
      workId: entry.workId,
      title: displayValue(entry.record && entry.record.title),
      thumbSrc: preview.src,
      thumbSrcset: preview.srcset || "",
      thumbSizes: "48px",
      thumbWidth: 48,
      thumbHeight: 48,
      thumbAlt: "",
      thumbFallback: text(options, "members_preview_missing", "No preview")
    };
  });
}

function memberRemoveBlocker(state, workId, seriesIds, options) {
  const primaryWorkId = normalizeWorkId(state.draft && state.draft.primary_work_id);
  const isPrimary = Boolean(primaryWorkId && primaryWorkId === workId);
  const hasOtherSeries = seriesIds.some((seriesId) => seriesId !== state.currentSeriesId);
  if (isPrimary && !hasOtherSeries) {
    return text(
      options,
      "members_remove_blocked_primary_only",
      "work {work_id} is the primary work for this series, and it is only associated with this series.",
      { work_id: workId }
    );
  }
  if (isPrimary) {
    return text(
      options,
      "members_remove_blocked_primary",
      "work {work_id} is the primary work for this series, please set a different primary work before removing from the series",
      { work_id: workId }
    );
  }
  if (!hasOtherSeries) {
    return text(
      options,
      "members_remove_blocked_only_series",
      "work {work_id} is only associated with this series, so use the works editor to unpublish or delete it completely.",
      { work_id: workId }
    );
  }
  return "";
}

async function removeSelectedMemberFromSeries(state, selection, options) {
  const workId = normalizeWorkId(selection && selection.record && selection.record.workId);
  if (!workId || !state.currentSeriesId) return;
  const seriesIds = (state.memberSeriesIdsByWorkId.get(workId) || [])
    .map((seriesId) => normalizeSeriesId(seriesId))
    .filter(Boolean);
  const blocker = memberRemoveBlocker(state, workId, seriesIds, options);
  if (blocker) {
    await openNoticeModal({
      root: state.root,
      title: text(options, "members_remove_blocked_title", "Cannot remove work"),
      body: [blocker],
      closeLabel: text(options, "modal_close_button", "Close"),
      size: "compact"
    });
    return;
  }
  const result = await openConfirmModal({
    root: state.root,
    title: text(options, "members_remove_confirm_title", "Remove work from series?"),
    body: [
      text(options, "members_remove_confirm_message", "Remove work {work_id} from this series?", { work_id: workId }),
      text(options, "members_remove_confirm_note", "This does not delete the work source record. Save to persist the membership change.")
    ],
    primaryLabel: text(options, "members_remove_confirm_button", "Remove"),
    cancelLabel: text(options, "confirm_cancel_button", "Cancel"),
    defaultAction: "cancel",
    size: "compact"
  });
  if (!result || !result.confirmed) return;
  const nextSeriesIds = seriesIds.filter((seriesId) => seriesId !== state.currentSeriesId);
  state.memberSeriesIdsByWorkId.set(workId, nextSeriesIds);
  state.selectedMemberWorkId = "";
  if (typeof options.setTextWithState === "function") {
    options.setTextWithState(
      state.statusNode,
      text(options, "members_remove_staged", "Removed work {work_id} from this series. Save to persist the membership change.", { work_id: workId }),
      "warn"
    );
  }
  if (typeof options.updateEditorState === "function") options.updateEditorState();
}

function renderMemberActions(state, options, list = null) {
  clearMemberActions(state);
  if (!state.membersActionsNode) return;
  const canCreateMemberWork = Boolean(state.currentRecord && state.currentSeriesId);
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
      title: text(options, "members_action_remove", "Remove from this series"),
      ariaLabel: text(options, "members_action_remove", "Remove"),
      appearance: "icon",
      tone: "danger"
    },
    {
      key: "new",
      label: "📄",
      title: canCreateMemberWork
        ? text(options, "members_action_new", "New")
        : text(options, "members_action_new_unavailable", "Open a saved series before adding member works."),
      ariaLabel: text(options, "members_action_new", "New"),
      appearance: "icon",
      requiresSelection: false,
      disabled: () => !canCreateMemberWork
    }
  ];
  state.membersActionsController = createRecordListActions(state.membersActionsNode, {
    id: "catalogueSeriesMembersActionsList",
    list,
    actions,
    onAction: ({ actionKey, selection }) => {
      if (actionKey === "delete") {
        void removeSelectedMemberFromSeries(state, selection, options);
        return;
      }
      if (actionKey !== "new" || !canCreateMemberWork) return;
      const href = buildStudioRouteUrl(state.config, "catalogue_work_editor", {
        mode: "new",
        series: state.currentSeriesId
      });
      if (href && typeof window !== "undefined" && typeof window.open === "function") {
        window.open(href, "_blank", "noopener");
      }
    }
  });
}

export function updateSeriesMemberList(state, options = {}) {
  if (!state.membersResultsNode) return;
  clearMemberList(state);
  const records = memberRecords(state, options);
  state.selectedMemberWorkId = selectedMemberWorkId(records, state.selectedMemberWorkId);
  state.membersMetaNode.textContent = "";
  state.membersListController = createRecordList(state.membersResultsNode, {
    id: "catalogueSeriesMembers",
    records,
    columns: [
      {
        key: "thumbSrc",
        label: text(options, "members_thumbnail_heading", "thumbnail"),
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
        key: "workId",
        label: text(options, "members_work_id_heading", "work"),
        width: "minmax(3.5rem, 4.9rem)",
        truncate: false
      },
      {
        key: "title",
        label: text(options, "members_title_heading", "title"),
        width: "minmax(0, 1fr)",
        truncate: true
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
