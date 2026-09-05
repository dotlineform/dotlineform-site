import {
  buildStudioRouteUrl
} from "./studio-config.js";
import { openConfirmModal } from "./studio-modal.js";
import {
  createRecordList,
  createRecordListActions
} from "/shared/frontend/js/record-list.js";
import { displayValue } from "./catalogue-editor-records.js";
import {
  buildWorkThumbPreview
} from "./catalogue-media-preview.js";
import { normalizeSeriesId, normalizeWorkId } from "./catalogue-series-fields.js";

function text(options, key, fallback, tokens = null) {
  if (options && typeof options.text === "function") {
    return options.text(key, fallback, tokens);
  }
  if (!tokens) return fallback;
  return Object.entries(tokens).reduce((value, [token, replacement]) => {
    return value.replace(new RegExp(`\\{${token}\\}`, "g"), () => replacement == null ? "" : String(replacement));
  }, fallback);
}

export function getStoredWorkSeriesId(state, workId) { return normalizeSeriesId(state.workSearchById.get(workId)?.series_id); }

export function getEditableSeriesMemberEntries(state) {
  return Array.from(state.memberSeriesByWorkId, ([workId, seriesId]) => ({workId, seriesId})).sort((a,b) => a.workId.localeCompare(b.workId));
}

export function getCurrentSeriesMemberEntries(state) {
  return getEditableSeriesMemberEntries(state).filter(entry => entry.seriesId === state.currentSeriesId).map(entry => ({...entry, record: state.workSearchById.get(entry.workId) || {}}));
}

export function seriesMembershipHasChanges(state) {
  return Array.from(state.memberSeriesByWorkId).some(([workId, seriesId]) => seriesId !== state.baselineMemberSeriesByWorkId.get(workId));
}

export function initializeSeriesMembershipState(state, seriesId) {
  state.memberSeriesByWorkId = new Map();
  state.baselineMemberSeriesByWorkId = new Map();
  for (const member of state.currentLookup?.member_works || []) {
    const workId = normalizeWorkId(member.work_id);
    if (!workId || member.series_id !== seriesId) continue;
    state.workSearchById.set(workId, member);
    state.memberSeriesByWorkId.set(workId, seriesId);
    state.baselineMemberSeriesByWorkId.set(workId, seriesId);
  }
}

export function buildSavedSeriesMembershipLookup(state, record, recordHash) {
  return {...state.currentLookup, series: record, record_hash: recordHash,
    member_works: getCurrentSeriesMemberEntries(state).map(entry => ({...entry.record, work_id: entry.workId, series_id: entry.seriesId}))};
}

export function buildChangedSeriesWorkUpdates(state) {
  return Array.from(state.memberSeriesByWorkId).filter(([workId, seriesId]) => seriesId !== state.baselineMemberSeriesByWorkId.get(workId)).map(([workId, seriesId]) => {
    const hash = state.workSearchById.get(workId)?.record_hash;
    if (!hash) throw new Error("Reload work " + workId + " before changing its membership.");
    return {work_id: workId, series_id: seriesId || null, expected_record_hash: hash};
  });
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


async function removeSelectedMemberFromSeries(state, selection, options) {
  const workId = normalizeWorkId(selection && selection.record && selection.record.workId);
  if (!workId || !state.currentSeriesId) return;
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
  state.memberSeriesByWorkId.set(workId, "");
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
