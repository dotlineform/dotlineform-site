import {
  getStudioText
} from "./studio-config.js";
import {
  probeStudioTagHealth
} from "./studio-transport.js";
import {
  buildTagSaveSuccessMessage,
  postTags,
  utcTimestamp
} from "./analytics-tag-editor-save.js";
import {
  applyPersistedBaseline,
  buildStateDiff
} from "./analytics-tag-editor-state.js";
import { buildStudioActivityContext } from "./studio-activity-context.js";

export async function probeAnalyticsTagEditorService(state, callbacks = {}) {
  if (state.serviceProbePending) return;
  state.serviceProbePending = true;
  const ok = await probeStudioTagHealth(500, { config: state.config });
  state.serviceProbePending = false;
  state.serviceAvailable = ok;
  syncRouteBusyState(callbacks, state);
}

export async function handleAnalyticsTagEditorSave(state, callbacks = {}) {
  state.isBusy = true;
  syncRouteBusyState(callbacks, state);
  try {
    return await handleAnalyticsTagEditorSaveInner(state, callbacks);
  } finally {
    state.isBusy = false;
    syncRouteBusyState(callbacks, state);
  }
}

async function handleAnalyticsTagEditorSaveInner(state, callbacks) {
  const diff = buildStateDiff(state);
  if (!diff.seriesChanged && !diff.changedWorkIds.length) {
    setStatus(state, "warn", analyticsTagEditorText(state.config, "save_status_no_changes", "No changes to save."));
    renderStatus(callbacks, state);
    return;
  }

  try {
    const results = [];
    const saveTags = typeof callbacks.postTags === "function" ? callbacks.postTags : postTags;
    const activityContext = buildStudioActivityContext({
      pageId: "series-tag-editor",
      actionId: "save-series-tags",
      route: "/studio/series-tag-editor/",
      controlId: "save",
      controlSelector: "[data-role=\"save\"]",
      recordIdField: "series_id",
      recordId: state.seriesId
    });
    if (diff.seriesChanged) {
      results.push(await saveTags(state.seriesId, null, diff.nextSeriesRows, false, utcTimestamp, undefined, activityContext, state.config));
    }
    for (const workId of diff.changedWorkIds) {
      const nextTags = diff.nextWorkStateById.get(workId) || [];
      const keepWork = diff.nextWorkStateById.has(workId);
      results.push(await saveTags(state.seriesId, workId, nextTags, keepWork, utcTimestamp, undefined, activityContext, state.config));
    }
    const lastResult = results[results.length - 1] || {};
    const savedAt = String(lastResult.updated_at_utc || utcTimestamp());
    const removedCount = results.filter((result) => result && result.deleted).length;
    const savedCount = diff.changedWorkIds.length - removedCount;
    state.serviceAvailable = true;
    setStatus(
      state,
      "success",
      buildTagSaveSuccessMessage(
        state.config,
        { seriesSaved: diff.seriesChanged, savedCount, removedCount, savedAt },
        analyticsTagEditorText
      )
    );
    setSaveResult(callbacks, state, "", "");
    renderStatus(callbacks, state);
    applyPersistedBaseline(state, diff);
    renderAll(callbacks, state);
  } catch (error) {
    state.serviceAvailable = false;
    setStatus(state, "error", analyticsTagEditorText(state.config, "save_status_local_failed", "Local save failed."));
    setSaveResult(
      callbacks,
      state,
      "warn",
      analyticsTagEditorText(state.config, "save_result_local_failed", "Changes remain unsaved in this editor.")
    );
    renderAll(callbacks, state);
  }
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

function analyticsTagEditorText(config, key, fallback, tokens) {
  return getStudioText(config, `series_tag_editor.${key}`, fallback, tokens);
}
