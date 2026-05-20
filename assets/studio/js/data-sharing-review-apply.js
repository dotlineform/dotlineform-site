import { getStudioText } from "./studio-config.js";
import { buildStudioActivityContext } from "./studio-activity-context.js";
import {
  DATA_SHARING_ENDPOINTS,
  postJson
} from "./studio-transport.js";
import {
  confirmDataSharingReviewApply,
  showDataSharingReviewResultModal
} from "./data-sharing-review-modals.js";
import {
  selectedDataSharingReviewRecordIndices
} from "./data-sharing-review-render.js";

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function setStatus(node, state, message) {
  if (!node) return;
  node.textContent = normalizeText(message);
  if (state) {
    node.setAttribute("data-state", state);
  } else {
    node.removeAttribute("data-state");
  }
}

function hideResultButton(state) {
  if (!state || !state.resultButton) return;
  state.resultButton.hidden = true;
}

function selectedFileName(state) {
  const filename = normalizeText(state.fileSelect && state.fileSelect.value);
  const file = (state.files || []).find((item) => normalizeText(item.filename) === filename) || null;
  return normalizeText(file && file.filename);
}

function applyIssues(payload, fallbackPrefix) {
  const errors = Array.isArray(payload && payload.errors) ? payload.errors : [];
  const warnings = Array.isArray(payload && payload.warnings) ? payload.warnings : [];
  const skipped = Array.isArray(payload && payload.skipped) ? payload.skipped : [];
  return [
    ...errors.map((item) => ({
      level: "error",
      code: item.reason || item.code || "error",
      doc_id: item.doc_id,
      message: item.message || item.reason || `${fallbackPrefix} error`
    })),
    ...warnings.map((item) => ({
      level: item.level || "warning",
      code: item.reason || item.code || "warning",
      doc_id: item.doc_id,
      message: item.message || item.reason || `${fallbackPrefix} warning`
    })),
    ...skipped.map((item) => ({
      level: "warning",
      code: item.reason || "skipped",
      doc_id: item.doc_id,
      message: item.message || "selected row skipped"
    }))
  ];
}

function countValue(counts, row) {
  const safeCounts = counts && typeof counts === "object" ? counts : {};
  const key = normalizeText(row && row.key);
  if (!key) return "";
  const fallbackKey = normalizeText(row && row.fallback_key);
  return Number(safeCounts[key] || (fallbackKey ? safeCounts[fallbackKey] : 0) || 0);
}

function actionCountRows(action, counts) {
  if (!action.countRows.length) {
    const safeCounts = counts && typeof counts === "object" ? counts : {};
    return Object.keys(safeCounts).map((key) => ({
      label: key.replace(/_/g, " "),
      value: Number(safeCounts[key] || 0)
    }));
  }
  return action.countRows.map((row) => ({
    label: normalizeText(row && row.label) || normalizeText(row && row.key),
    value: countValue(counts, row)
  })).filter((row) => row.label);
}

function actionCountsText(action, counts) {
  const template = normalizeText(action.countText);
  if (!template) return "";
  const safeCounts = counts && typeof counts === "object" ? counts : {};
  return template.replace(/\{([^}]+)\}/g, (_match, key) => String(Number(safeCounts[normalizeText(key)] || 0)));
}

function actionChangeCount(action, counts) {
  const safeCounts = counts && typeof counts === "object" ? counts : {};
  const key = action.noChangeCountKey || (action.countRows[0] && normalizeText(action.countRows[0].key)) || "updates";
  return Number(safeCounts[key] || 0);
}

function renderApplyActionResult(state, action, payload) {
  const countsValue = actionCountsText(action, payload && payload.counts);
  const summary = normalizeText(payload && payload.summary_text);
  showDataSharingReviewResultModal(state, {
    title: action.resultTitle || getStudioText(state.config, "data_sharing_review.apply_result_title", "Apply complete"),
    summary: `${summary} ${countsValue}`.trim(),
    countRows: actionCountRows(action, payload && payload.counts),
    issues: applyIssues(payload || {}, action.id)
  }, {
    restoreFocus: state.actionMenuButton
  });
}

function actionActivityContext(state, action, stagedFilename) {
  const controlSelector = normalizeText(action.controlSelector) || `#${action.controlId}`;
  return buildStudioActivityContext({
    pageId: "data-sharing-review",
    actionId: action.activityActionId,
    route: "/studio/data-sharing/review/",
    controlId: action.controlId,
    controlSelector,
    recordIdField: "staged_filename",
    recordId: stagedFilename
  });
}

export async function runDataSharingReviewApplyAction(state, actionId, lifecycle = {}) {
  const setControlsDisabled = lifecycle.setControlsDisabled || (() => {});
  const syncRouteBusyState = lifecycle.syncRouteBusyState || (() => {});
  if (!state.serviceAvailable || state.isRunning) return;
  const action = state.applyActions.find((item) => item.id === actionId);
  if (!action || action.status !== "active") return;
  hideResultButton(state);
  const stagedFilename = selectedFileName(state);
  const recordIndices = selectedDataSharingReviewRecordIndices(state);
  if (!stagedFilename || !recordIndices.length) {
    setStatus(
      state.statusNode,
      "error",
      action.selectionRequiredMessage || getStudioText(state.config, "data_sharing_review.apply_selection_required", "Select at least one review row.")
    );
    return;
  }

  state.isRunning = true;
  setControlsDisabled(state, true);
  syncRouteBusyState(state);
  setStatus(
    state.statusNode,
    "",
    action.preflightStatus || getStudioText(state.config, "data_sharing_review.apply_preflight_status", "Checking selected rows...")
  );

  try {
    const preflight = await postJson(DATA_SHARING_ENDPOINTS.apply, {
      data_domain: state.scope,
      operation: "apply",
      apply_action: action.id,
      staged_filename: stagedFilename,
      record_indices: recordIndices,
      confirm: false
    });
    const countsTextValue = actionCountsText(action, preflight.counts);
    if (!preflight.ok || actionChangeCount(action, preflight.counts) < 1) {
      setStatus(state.statusNode, preflight.ok ? "warn" : "error", preflight.summary_text || countsTextValue);
      renderApplyActionResult(state, action, preflight);
      return;
    }

    const confirm = await confirmDataSharingReviewApply(state, action, preflight, countsTextValue);
    if (!confirm.confirmed) {
      setStatus(
        state.statusNode,
        "",
        action.cancelledStatus || getStudioText(state.config, "data_sharing_review.apply_cancelled", "Apply cancelled.")
      );
      return;
    }

    setStatus(
      state.statusNode,
      "",
      action.runningStatus || getStudioText(state.config, "data_sharing_review.apply_running_status", "Applying selected changes...")
    );
    const applied = await postJson(DATA_SHARING_ENDPOINTS.apply, {
      data_domain: state.scope,
      operation: "apply",
      apply_action: action.id,
      staged_filename: stagedFilename,
      record_indices: recordIndices,
      confirm: true,
      activity_context: actionActivityContext(state, action, stagedFilename)
    });
    renderApplyActionResult(state, action, applied);
    setStatus(
      state.statusNode,
      "success",
      applied.summary_text || action.successStatus || getStudioText(state.config, "data_sharing_review.apply_success", "Changes applied.")
    );
  } catch (error) {
    const payload = error && error.payload ? error.payload : {};
    const message = normalizeText(payload.summary_text) || normalizeText(error && error.message)
      || action.failedStatus || getStudioText(state.config, "data_sharing_review.apply_failed", "Apply failed.");
    renderApplyActionResult(state, action, { ...payload, summary_text: message });
    setStatus(state.statusNode, "error", message);
  } finally {
    state.isRunning = false;
    setControlsDisabled(state, false);
    syncRouteBusyState(state);
  }
}
