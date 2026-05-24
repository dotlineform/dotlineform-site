import {
  getStudioText
} from "./studio-config.js";
import {
  probeStudioHealth
} from "./studio-transport.js";
import {
  buildSaveModeText as buildTagStudioSaveModeText,
  buildTagSaveSuccessMessage,
  postTags,
  utcTimestamp
} from "./tag-studio-save.js";
import {
  applyPersistedBaseline,
  buildPersistedSeriesRow,
  buildStateDiff
} from "./tag-studio-state.js";
import { buildStudioActivityContext } from "./studio-activity-context.js";

export function renderTagStudioSaveMode(state) {
  if (!state.refs || !state.refs.saveMode) return;
  state.refs.saveMode.textContent = buildTagStudioSaveModeText(state.config, state.saveMode, studioText);
}

export function syncTagStudioOfflineAutosave(state, callbacks = {}) {
  clearTagStudioOfflineAutosave(state);
}

export function clearTagStudioOfflineAutosave(state) {
  if (!state.offlineAutosaveTimer) return;
  window.clearTimeout(state.offlineAutosaveTimer);
  state.offlineAutosaveTimer = 0;
}

export async function probeTagStudioSaveMode(state, callbacks = {}) {
  if (state.saveModeProbePending) return;
  state.saveModeProbePending = true;
  const ok = await probeStudioHealth(500, { config: state.config });
  state.saveModeProbePending = false;
  state.lastSaveModeHealthOk = ok;
  state.saveMode = ok && !state.hasOfflineStagedSeries ? "post" : "offline";
  state.saveModeResolved = true;

  const importMessage = studioText(
    state.config,
    "save_result_server_available_import",
    "Local server now available. Apply offline changes using Series Tags > Import."
  );
  if (ok && state.hasOfflineStagedSeries) {
    if (!state.serverAvailableWhileOfflineNotified) {
      state.serverAvailableWhileOfflineNotified = true;
      setSaveResult(callbacks, state, "success", importMessage);
    }
  } else {
    if (state.serverAvailableWhileOfflineNotified && state.refs.saveResult && state.refs.saveResult.textContent === importMessage) {
      setSaveResult(callbacks, state, "", "");
    }
    state.serverAvailableWhileOfflineNotified = false;
  }

  renderTagStudioSaveMode(state);
  renderAll(callbacks, state);
  syncRouteBusyState(callbacks, state);
}

export async function stageTagStudioOfflineState(state, options = {}, callbacks = {}) {
  clearTagStudioOfflineAutosave(state);

  const diff = buildStateDiff(state);
  if (!diff.seriesChanged && !diff.changedWorkIds.length) {
    if (options.manual) {
      setStatus(state, "warn", studioText(state.config, "save_status_no_changes", "No changes to save."));
      renderStatus(callbacks, state);
    }
    return false;
  }

  const stagedAt = utcTimestamp();
  const stagedRow = buildPersistedSeriesRow(diff);
  const workflow = await import("./tag-assignments-offline-session.js");
  const result = workflow.stageTagAssignmentsOfflineSeries({
    seriesId: state.seriesId,
    baseUpdatedAt: state.offlineBaseSeriesUpdatedAt,
    baseRow: state.offlineBaseSeriesRow,
    stagedRow,
    stagedAt
  });

  state.offlineSession = result.session;
  state.hasOfflineStagedSeries = !result.seriesCleared;
  applyPersistedBaseline(state, diff);

  if (options.manual) {
    const removedCount = diff.changedWorkIds.filter((workId) => !diff.nextWorkStateById.has(workId)).length;
    const savedCount = diff.changedWorkIds.length - removedCount;
    setStatus(
      state,
      "success",
      buildTagSaveSuccessMessage(
        state.config,
        { seriesSaved: diff.seriesChanged, savedCount, removedCount, savedAt: stagedAt },
        studioText
      )
    );
  }

  setSaveResult(
    callbacks,
    state,
    "success",
    result.seriesCleared
      ? studioText(state.config, "save_result_offline_cleared", "Series matches repo data. Offline session entry cleared.")
      : studioText(state.config, "save_result_offline_staged", "Changes are staged in the offline session.")
  );
  renderAll(callbacks, state);
  return true;
}

export async function handleTagStudioSave(state, callbacks = {}) {
  state.isBusy = true;
  syncRouteBusyState(callbacks, state);
  try {
    return await handleTagStudioSaveInner(state, callbacks);
  } finally {
    state.isBusy = false;
    syncRouteBusyState(callbacks, state);
  }
}

async function handleTagStudioSaveInner(state, callbacks) {
  const diff = buildStateDiff(state);
  if (!diff.seriesChanged && !diff.changedWorkIds.length) {
    setStatus(state, "warn", studioText(state.config, "save_status_no_changes", "No changes to save."));
    renderStatus(callbacks, state);
    return;
  }

  if (state.saveMode === "post") {
    try {
      const results = [];
      const activityContext = buildStudioActivityContext({
        pageId: "series-tag-editor",
        actionId: "save-series-tags",
        route: "/studio/analytics/series-tag-editor/",
        controlId: "save",
        controlSelector: "[data-role=\"save\"]",
        recordIdField: "series_id",
        recordId: state.seriesId
      });
      if (diff.seriesChanged) {
        results.push(await postTags(state.seriesId, null, diff.nextSeriesRows, false, utcTimestamp, undefined, activityContext, state.config));
      }
      for (const workId of diff.changedWorkIds) {
        const nextTags = diff.nextWorkStateById.get(workId) || [];
        const keepWork = diff.nextWorkStateById.has(workId);
        results.push(await postTags(state.seriesId, workId, nextTags, keepWork, utcTimestamp, undefined, activityContext, state.config));
      }
      const lastResult = results[results.length - 1] || {};
      const savedAt = String(lastResult.updated_at_utc || utcTimestamp());
      const removedCount = results.filter((result) => result && result.deleted).length;
      const savedCount = diff.changedWorkIds.length - removedCount;
      setStatus(
        state,
        "success",
        buildTagSaveSuccessMessage(
          state.config,
          { seriesSaved: diff.seriesChanged, savedCount, removedCount, savedAt },
          studioText
        )
      );
      setSaveResult(callbacks, state, "", "");
      renderStatus(callbacks, state);
      applyPersistedBaseline(state, diff);
      renderAll(callbacks, state);
      return;
    } catch (error) {
      state.saveMode = "offline";
      state.saveModeResolved = true;
      renderTagStudioSaveMode(state);
      setStatus(state, "error", studioText(state.config, "save_status_local_failed", "Local save failed. Switched to offline mode."));
      setSaveResult(callbacks, state, "warn", studioText(state.config, "save_result_local_failed", "Local server save failed. Press Save again to stage these changes in the offline session."));
      renderAll(callbacks, state);
      return;
    }
  }

  await stageTagStudioOfflineState(state, { manual: true }, callbacks);
}

function setStatus(state, kind, text) {
  state.statusKind = kind || "";
  state.statusText = text || "";
}

function renderStatus(callbacks, state) {
  if (typeof callbacks.renderStatus === "function") callbacks.renderStatus(state);
}

function renderAll(callbacks, state) {
  if (typeof callbacks.renderAll === "function") callbacks.renderAll(state);
}

function setSaveResult(callbacks, state, kind, text) {
  if (typeof callbacks.setSaveResult === "function") callbacks.setSaveResult(state, kind, text);
}

function syncRouteBusyState(callbacks, state) {
  if (typeof callbacks.syncRouteBusyState === "function") callbacks.syncRouteBusyState(state);
}

function studioText(config, key, fallback, tokens) {
  return getStudioText(config, `series_tag_editor.${key}`, fallback, tokens);
}
