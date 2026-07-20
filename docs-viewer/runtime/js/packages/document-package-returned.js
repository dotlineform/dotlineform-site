import {
  applyReturnedDocumentPackage,
  getDocumentPackageConfig,
  getReturnedDocumentPackages,
  inspectReturnedDocumentPackage,
  reviewReturnedDocumentPackage
} from "./document-package-client.js";
import {
  confirmDocumentPackageApply,
  showDocumentPackageResult
} from "./document-package-modal.js";
import {
  escapePackageHtml,
  formatPackageBytes,
  packageIssueMessage,
  packageScopeLabel,
  packageText,
  renderReturnedPackageRows,
  selectedScopeFromUrl,
  setPackageBusy,
  setPackageReady,
  setPackageStatus,
  syncPackageScopeLinks
} from "./document-package-view.js";

const RETURNED_APPLY_CONTROLS = Object.freeze({
  summary_apply: {
    actionId: "apply-returned-summaries",
    controlId: "documentPackageReturnedSummaryApply"
  },
  hierarchy_apply: {
    actionId: "apply-returned-hierarchy",
    controlId: "documentPackageReturnedHierarchyApply"
  }
});

function returnedState(root) {
  return {
    root,
    status: document.getElementById("documentPackageReturnedStatus"),
    inspectButton: document.getElementById("documentPackageReturnedInspect"),
    reviewActions: document.getElementById("documentPackageReturnedReviewActions"),
    applyActions: document.getElementById("documentPackageReturnedApplyActions"),
    scopeValue: document.getElementById("documentPackageReturnedScopeValue"),
    fileSelect: document.getElementById("documentPackageReturnedFile"),
    context: document.getElementById("documentPackageReturnedContext"),
    profileValue: document.getElementById("documentPackageReturnedProfile"),
    exportValue: document.getElementById("documentPackageReturnedExport"),
    formatValue: document.getElementById("documentPackageReturnedFormat"),
    summary: document.getElementById("documentPackageReturnedSummary"),
    documentsNode: document.getElementById("documentPackageReturnedDocuments"),
    blocked: document.getElementById("documentPackageReturnedBlocked"),
    blockedList: document.getElementById("documentPackageReturnedBlockedList"),
    unassigned: document.getElementById("documentPackageReturnedUnassigned"),
    unassignedList: document.getElementById("documentPackageReturnedUnassignedList"),
    modalHost: document.getElementById("documentPackageReturnedModalHost"),
    scopes: [],
    scope: "",
    reviewActionRecords: [],
    applyActionRecords: [],
    files: [],
    blockedFiles: [],
    unassignedFiles: [],
    inspected: false,
    workspaceAvailable: false,
    busy: false,
    requestVersion: 0
  };
}

function selectedReturnedFile(state) {
  const filename = packageText(state.fileSelect.value);
  return state.files.find((file) => packageText(file && file.filename) === filename) || null;
}

function selectedRequest(state) {
  const file = selectedReturnedFile(state);
  return {
    scope: packageText(state.scope),
    staged_filename: packageText(file && file.filename)
  };
}

function syncReturnedContext(state) {
  const file = selectedReturnedFile(state);
  state.context.hidden = !file;
  state.profileValue.textContent = packageText(file && file.profile_id) || "unresolved";
  state.exportValue.textContent = packageText(file && file.export_id) || "unresolved";
  state.formatValue.textContent = packageText(file && (file.target_format || file.format)) || "unresolved";
}

function syncReturnedControls(state) {
  const file = selectedReturnedFile(state);
  const fileReady = Boolean(file && file.metadata_ok !== false);
  state.fileSelect.disabled = state.busy || !state.scope || !state.files.length;
  state.inspectButton.disabled = state.busy || !file;
  state.reviewActions.querySelectorAll("button").forEach((button) => {
    button.disabled = state.busy || !fileReady || !state.inspected;
  });
  state.applyActions.querySelectorAll("button").forEach((button) => {
    button.disabled = state.busy || !fileReady || !state.inspected;
  });
}

function renderActionButtons(state) {
  state.reviewActions.innerHTML = state.reviewActionRecords.map((action) => `
    <button class="docsPackageButton" type="button" data-package-review-action="${escapePackageHtml(action.id)}" disabled>${escapePackageHtml(action.label || action.id)}</button>
  `).join("");
  state.applyActions.innerHTML = state.applyActionRecords.map((action) => {
    const control = RETURNED_APPLY_CONTROLS[action.id] || {};
    const idAttribute = control.controlId ? ` id="${escapePackageHtml(control.controlId)}"` : "";
    return `
      <button class="docsPackageButton"${idAttribute} type="button" data-package-apply-action="${escapePackageHtml(action.id)}" disabled>${escapePackageHtml(action.label || action.id)}</button>
    `;
  }).join("");
}

function returnedApplyActivityContext(request, actionId) {
  const control = RETURNED_APPLY_CONTROLS[actionId];
  if (!control) return null;
  return {
    page_id: "docs-package-returned",
    action_id: control.actionId,
    route: `/docs/packages/returned/?scope=${encodeURIComponent(request.scope)}`,
    control_id: control.controlId,
    control_selector: `#${control.controlId}`,
    correlation_id: `document-package-apply:${actionId}:${request.staged_filename}:${Date.now()}`,
    staged_filename: request.staged_filename
  };
}

function blockedReason(file) {
  const reason = packageText(file && (file.blocked_reason || file.metadata_error));
  if (reason === "export_only_profile") return "export-only profile";
  if (reason === "unsupported_import_profile") return "unsupported return profile";
  return reason.replace(/_/g, " ") || "not actionable";
}

function renderBlockedFiles(state) {
  state.blocked.hidden = !state.blockedFiles.length;
  state.blockedList.innerHTML = state.blockedFiles.map((file) => `
    <li><strong>${escapePackageHtml(packageText(file.filename) || "unnamed package")}</strong> — ${escapePackageHtml(blockedReason(file))}</li>
  `).join("");
}

function renderUnassignedFiles(state) {
  state.unassigned.hidden = !state.unassignedFiles.length;
  state.unassignedList.innerHTML = state.unassignedFiles.map((file) => {
    const reason = packageText(file && file.metadata_error) || "trusted scope metadata is missing";
    return `<li><strong>${escapePackageHtml(packageText(file && file.filename) || "unnamed package")}</strong> — ${escapePackageHtml(reason)}</li>`;
  }).join("");
}

function renderReturnedFileOptions(state) {
  state.fileSelect.innerHTML = state.files.map((file) => {
    const filename = packageText(file.filename);
    const details = [packageText(file.profile_id), formatPackageBytes(file.size_bytes)].filter(Boolean).join(" · ");
    return `<option value="${escapePackageHtml(filename)}">${escapePackageHtml(filename)}${details ? ` — ${escapePackageHtml(details)}` : ""}</option>`;
  }).join("");
  state.fileSelect.selectedIndex = -1;
  state.inspected = false;
  syncReturnedContext(state);
  renderBlockedFiles(state);
  renderUnassignedFiles(state);
  syncReturnedControls(state);
}

function resetInspection(state, message = "Select a staged package to inspect its complete document set.") {
  state.inspected = false;
  state.summary.textContent = message;
  state.documentsNode.innerHTML = '<p class="docsPackageEmpty">No returned package inspected.</p>';
  syncReturnedControls(state);
}

async function loadReturnedFiles(state) {
  const scope = packageText(state.scope);
  const version = ++state.requestVersion;
  state.files = [];
  state.blockedFiles = [];
  state.unassignedFiles = [];
  resetInspection(state, scope ? "Loading staged packages…" : "A valid Docs Viewer scope is required.");
  if (!scope) {
    state.fileSelect.innerHTML = "";
    renderReturnedFileOptions(state);
    setPackageStatus(state.status, "error", "Open this route from Docs Viewer Actions for a scope.");
    return;
  }
  state.busy = true;
  setPackageBusy(state.root, true);
  setPackageStatus(state.status, "", "Loading staged document packages…");
  syncReturnedControls(state);
  try {
    const payload = await getReturnedDocumentPackages(scope);
    if (version !== state.requestVersion) return;
    state.files = Array.isArray(payload.files) ? payload.files : [];
    state.blockedFiles = Array.isArray(payload.blocked_files) ? payload.blocked_files : [];
    state.unassignedFiles = Array.isArray(payload.unassigned_files) ? payload.unassigned_files : [];
    renderReturnedFileOptions(state);
    const count = state.files.length;
    const unassignedCount = state.unassignedFiles.length;
    state.summary.textContent = count
      ? "Select a staged package to inspect its complete document set."
      : `No staged packages for ${packageScopeLabel(state.scopes, state.scope)}.`;
    const loadedMessage = count === 1 ? "Loaded 1 staged package." : `Loaded ${count} staged packages.`;
    const unassignedMessage = unassignedCount
      ? `${unassignedCount === 1 ? "1 unassigned staging file is" : `${unassignedCount} unassigned staging files are`} reported separately.`
      : "";
    setPackageStatus(
      state.status,
      unassignedCount ? "warn" : (count ? "success" : ""),
      [loadedMessage, unassignedMessage].filter(Boolean).join(" ")
    );
  } catch (error) {
    if (version !== state.requestVersion) return;
    state.fileSelect.innerHTML = "";
    setPackageStatus(state.status, "error", error.message || "Staged packages could not be loaded.");
  } finally {
    if (version === state.requestVersion) {
      state.busy = false;
      setPackageBusy(state.root, false);
      syncReturnedControls(state);
    }
  }
}

async function inspectSelectedPackage(state) {
  const request = selectedRequest(state);
  if (!request.scope || !request.staged_filename || state.busy) return;
  state.busy = true;
  state.inspected = false;
  setPackageBusy(state.root, true);
  setPackageStatus(state.status, "", "Inspecting the complete returned package…");
  syncReturnedControls(state);
  try {
    const payload = await inspectReturnedDocumentPackage(request);
    state.inspected = true;
    const rows = Array.isArray(payload.review_rows) ? payload.review_rows : [];
    renderReturnedPackageRows(state.documentsNode, rows);
    state.summary.textContent = rows.length === 1 ? "1 returned document. The package is the actionable unit." : `${rows.length} returned documents. The package is the actionable unit.`;
    setPackageStatus(state.status, "success", payload.summary_text || "Returned package is complete and valid.");
  } catch (error) {
    const payload = error && error.payload ? error.payload : {};
    renderReturnedPackageRows(state.documentsNode, payload.review_rows || []);
    const issues = Array.isArray(payload.issues) ? payload.issues.map(packageIssueMessage).filter(Boolean) : [];
    state.summary.textContent = issues.length ? issues.join(" · ") : "The returned package is not actionable.";
    setPackageStatus(state.status, "error", error.message || "Returned package validation failed.");
  } finally {
    state.busy = false;
    setPackageBusy(state.root, false);
    syncReturnedControls(state);
  }
}

async function runReturnedReview(state, actionId, button) {
  const request = selectedRequest(state);
  if (!state.inspected || !request.staged_filename || state.busy) return;
  state.busy = true;
  setPackageBusy(state.root, true);
  setPackageStatus(state.status, "", "Producing document-package review…");
  syncReturnedControls(state);
  try {
    const payload = await reviewReturnedDocumentPackage({
      ...request,
      review_action: actionId,
      dry_run: false
    });
    setPackageStatus(state.status, "success", payload.summary_text || "Document-package review completed.");
    await showDocumentPackageResult({
      host: state.modalHost,
      restoreFocus: button,
      title: "Returned package review",
      meta: request.staged_filename,
      payload
    });
  } catch (error) {
    const payload = error && error.payload ? error.payload : { ok: false, summary_text: error.message };
    setPackageStatus(state.status, "error", error.message || "Document-package review failed.");
    await showDocumentPackageResult({
      host: state.modalHost,
      restoreFocus: button,
      title: "Returned package review failed",
      meta: request.staged_filename,
      payload
    });
  } finally {
    state.busy = false;
    setPackageBusy(state.root, false);
    syncReturnedControls(state);
  }
}

async function runReturnedApply(state, actionId, button) {
  const request = selectedRequest(state);
  if (!state.inspected || !request.staged_filename || state.busy) return;
  state.busy = true;
  setPackageBusy(state.root, true);
  setPackageStatus(state.status, "", "Checking the complete returned package…");
  syncReturnedControls(state);
  try {
    const preflight = await applyReturnedDocumentPackage({
      ...request,
      apply_action: actionId,
      confirm: false,
      dry_run: true
    });
    const confirmation = await confirmDocumentPackageApply({
      host: state.modalHost,
      restoreFocus: button,
      title: "Apply complete returned package?",
      meta: request.staged_filename,
      payload: preflight
    });
    if (!confirmation.confirmed) {
      setPackageStatus(state.status, "", "Apply cancelled.");
      return;
    }
    setPackageStatus(state.status, "", "Applying the complete returned package…");
    const applied = await applyReturnedDocumentPackage({
      ...request,
      apply_action: actionId,
      confirm: true,
      dry_run: false,
      activity_context: returnedApplyActivityContext(request, actionId)
    });
    setPackageStatus(state.status, "success", applied.summary_text || "Returned package applied.");
    await showDocumentPackageResult({
      host: state.modalHost,
      restoreFocus: button,
      title: "Returned package applied",
      meta: request.staged_filename,
      payload: applied
    });
    state.busy = false;
    setPackageBusy(state.root, false);
    syncReturnedControls(state);
    await inspectSelectedPackage(state);
  } catch (error) {
    const payload = error && error.payload ? error.payload : { ok: false, summary_text: error.message };
    setPackageStatus(state.status, "error", error.message || "Returned package apply failed.");
    await showDocumentPackageResult({
      host: state.modalHost,
      restoreFocus: button,
      title: "Returned package was not applied",
      meta: request.staged_filename,
      payload
    });
  } finally {
    state.busy = false;
    setPackageBusy(state.root, false);
    syncReturnedControls(state);
  }
}

function bindReturnedEvents(state) {
  state.fileSelect.addEventListener("change", () => {
    syncReturnedContext(state);
    resetInspection(state);
    inspectSelectedPackage(state);
  });
  state.inspectButton.addEventListener("click", () => inspectSelectedPackage(state));
  state.reviewActions.addEventListener("click", (event) => {
    const button = event.target.closest("[data-package-review-action]");
    if (button) runReturnedReview(state, packageText(button.dataset.packageReviewAction), button);
  });
  state.applyActions.addEventListener("click", (event) => {
    const button = event.target.closest("[data-package-apply-action]");
    if (button) runReturnedApply(state, packageText(button.dataset.packageApplyAction), button);
  });
}

async function initDocumentPackageReturned() {
  const root = document.getElementById("documentPackageReturnedRoot");
  if (!root) return;
  const state = returnedState(root);
  bindReturnedEvents(state);
  try {
    const payload = await getDocumentPackageConfig();
    state.scopes = Array.isArray(payload.scopes) ? payload.scopes : [];
    state.scope = selectedScopeFromUrl(state.scopes);
    state.reviewActionRecords = Array.isArray(payload.review_actions) ? payload.review_actions : [];
    state.applyActionRecords = Array.isArray(payload.apply_actions) ? payload.apply_actions : [];
    state.workspaceAvailable = payload.workspace && payload.workspace.available === true;
    state.scopeValue.textContent = state.scope ? packageScopeLabel(state.scopes, state.scope) : "Scope required";
    if (state.scope) delete state.scopeValue.dataset.state;
    else state.scopeValue.dataset.state = "error";
    syncPackageScopeLinks(state.scope);
    renderActionButtons(state);
    if (!state.scope) {
      setPackageStatus(state.status, "error", "Open this route from Docs Viewer Actions for a scope.");
    } else if (!state.workspaceAvailable) {
      setPackageStatus(state.status, "warn", packageText(payload.workspace && payload.workspace.message) || "The document-package workspace is unavailable.");
    } else {
      await loadReturnedFiles(state);
    }
  } catch (error) {
    setPackageStatus(state.status, "error", error.message || "Document-package configuration could not be loaded.");
  } finally {
    setPackageReady(root, true);
    syncReturnedControls(state);
  }
}

initDocumentPackageReturned();
