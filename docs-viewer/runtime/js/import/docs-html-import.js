import {
  DOCS_MANAGEMENT_UNAVAILABLE_MESSAGE,
  fetchManagementJson
} from "../management/docs-viewer-management-client.js";
import {
  clearDocsHtmlImportResult,
  resetDocsHtmlImportWarning
} from "./docs-html-import-render.js";
import {
  docsHtmlImportManagementOptions,
  docsHtmlImportSourceFormatForRecord,
  runDocsHtmlImportWorkflow
} from "./docs-html-import-workflow.js";
import {
  importText
} from "./docs-html-import-text.js";
import {
  createDocsImportCollectionController,
  isDocsImportCollectionRecord
} from "./docs-import-collection-controller.js";

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

function setText(node, value) {
  if (!node) return;
  node.textContent = normalizeText(value);
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

function applyRouteDetail(root, detail = {}) {
  if (!root) return;
  if (Object.prototype.hasOwnProperty.call(detail, "route")) {
    root.dataset.studioRoute = normalizeText(detail.route);
  }
  if (Object.prototype.hasOwnProperty.call(detail, "mode")) {
    root.dataset.studioMode = normalizeText(detail.mode);
  }
  if (Object.prototype.hasOwnProperty.call(detail, "service")) {
    root.dataset.studioService = normalizeText(detail.service);
  }
  if (Object.prototype.hasOwnProperty.call(detail, "recordLoaded")) {
    root.dataset.studioRecordLoaded = detail.recordLoaded ? "true" : "false";
  }
}

function initializeRouteState(root, detail = {}) {
  if (!root) return;
  applyRouteDetail(root, detail);
  root.dataset.studioReady = "false";
  root.dataset.studioBusy = "false";
}

function setRouteBusy(root, busy, detail = {}) {
  if (!root) return;
  applyRouteDetail(root, detail);
  root.dataset.studioBusy = busy ? "true" : "false";
}

function setRouteReady(root, ready, detail = {}) {
  if (!root) return;
  const nextReady = Boolean(ready);
  applyRouteDetail(root, detail);
  root.dataset.studioReady = nextReady ? "true" : "false";
  root.dispatchEvent(new CustomEvent("studio:ready", {
    bubbles: true,
    detail: {
      ready: nextReady,
      busy: root.dataset.studioBusy === "true",
      route: root.dataset.studioRoute || "",
      mode: root.dataset.studioMode || "",
      service: root.dataset.studioService || "",
      recordLoaded: root.dataset.studioRecordLoaded === "true"
    }
  }));
}

function routeModeForState(state) {
  const collectionMode = state.collectionController && state.collectionController.mode();
  if (collectionMode && collectionMode !== "idle") return collectionMode;
  if (state.resultNode && !state.resultNode.hidden) return "result";
  if (state.warningNode && !state.warningNode.hidden) return "confirm";
  return "idle";
}

function routeStateDetail(state) {
  return {
    route: "docs-import",
    mode: routeModeForState(state),
    service: state.serviceAvailable ? "available" : "unavailable",
    recordLoaded: Boolean(state.files && state.files.length)
  };
}

function syncRouteBusyState(state) {
  setRouteBusy(state.root, Boolean(state.isRunning), routeStateDetail(state));
}

function markRouteReady(state, ready) {
  setRouteReady(state.root, ready, routeStateDetail(state));
}

async function loadDocsViewerScopeOptions(configUrl = "/docs-viewer/config/defaults/docs-viewer-config.json") {
  const response = await fetch(configUrl, {
    headers: { Accept: "application/json" },
    cache: "default"
  });
  if (!response.ok) {
    throw new Error(`Failed to load Docs Viewer config (${response.status})`);
  }
  const payload = await response.json();
  if (!payload || payload.schema_version !== "docs_viewer_config_v1" || !Array.isArray(payload.scopes)) {
    throw new Error("Docs Viewer config has an unsupported schema.");
  }
  const scopes = payload.scopes
    .map((scope) => normalizeText(scope && scope.scope_id).toLowerCase())
    .filter(Boolean);
  const uniqueScopes = Array.from(new Set(scopes));
  if (!uniqueScopes.length) {
    throw new Error("Docs Viewer config does not define any scopes.");
  }
  return uniqueScopes;
}

function selectedScopeFromUrl(validScopes, fallbackScope = "") {
  try {
    const url = new URL(window.location.href);
    const scope = normalizeText(url.searchParams.get("scope")).toLowerCase();
    return validScopes.includes(scope) ? scope : fallbackScope;
  } catch (_error) {
    return fallbackScope;
  }
}

function persistSelectedScope(state, scope) {
  if (state && state.persistScope === false) return;
  try {
    const url = new URL(window.location.href);
    url.searchParams.set("scope", scope);
    window.history.replaceState({}, "", url.toString());
  } catch (_error) {
    // Ignore URL sync failures in constrained runtimes.
  }
}

function managementOptionsForState(state) {
  return docsHtmlImportManagementOptions({
    managementBaseUrl: state.managementBaseUrl
  });
}

async function fetchImportFiles(state) {
  const payload = await fetchManagementJson("/docs/import-source-files", "GET", undefined, managementOptionsForState(state));
  return Array.isArray(payload.files) ? payload.files : [];
}

function selectedFileRecord(state) {
  const filename = normalizeText(state.fileSelect.value);
  return state.files.find((file) => normalizeText(file && file.filename) === filename) || null;
}

export function docsImportReviewHandoff(files, packageId) {
  const normalizedPackageId = normalizeText(packageId);
  const file = normalizedPackageId ? files.find((record) => (
    Array.isArray(record && record.review_package_ids)
    && record.review_package_ids.some((value) => normalizeText(value) === normalizedPackageId)
  )) || null : null;
  return {
    requested: Boolean(normalizedPackageId),
    packageId: normalizedPackageId,
    file,
    available: Boolean(file)
  };
}

function selectedImportFiles(state) {
  const record = selectedFileRecord(state);
  return record && !isDocsImportCollectionRecord(record) ? [record] : [];
}

function selectedCollectionFile(state) {
  const record = selectedFileRecord(state);
  return isDocsImportCollectionRecord(record) ? record : null;
}

function syncSourceFormatControls(state) {
  const selectedFiles = selectedImportFiles(state);
  const collectionFile = selectedCollectionFile(state);
  const supportsPromptMeta = selectedFiles.some((file) => docsHtmlImportSourceFormatForRecord(file) === "html");
  state.includePromptMeta.checked = supportsPromptMeta ? state.includePromptMeta.checked : false;
  state.includePromptMeta.disabled = !supportsPromptMeta || !state.serviceAvailable;
  state.includePromptMetaWrap.hidden = !supportsPromptMeta;
  state.runButton.textContent = collectionFile
    ? importText("collectionPreviewButton")
    : importText("importButton");
  state.collectionController.setActive(Boolean(collectionFile));
}

function resetImportView(state, statusMessage) {
  resetDocsHtmlImportWarning(state);
  clearDocsHtmlImportResult(state);
  setStatus(state.statusNode, "", statusMessage);
}

function stagedFileOption(file) {
  const filename = normalizeText(file && file.filename);
  const sourceFormat = docsHtmlImportSourceFormatForRecord(file).replace(/_/g, " ");
  return `<option value="${escapeHtml(filename)}">${escapeHtml(`${filename} (${sourceFormat})`)}</option>`;
}

function renderStagedFiles(state, files) {
  const previousValue = normalizeText(state.fileSelect.value);
  state.files = files;
  resetImportView(state, "");
  state.collectionController.reset({ active: false });

  if (!files.length) {
    state.fileSelect.innerHTML = "";
    state.fileSelect.disabled = true;
    state.runButton.disabled = true;
    syncSourceFormatControls(state);
    setStatus(
      state.statusNode,
      state.reviewPackageId ? "error" : "warn",
      state.reviewPackageId
        ? importText("collectionHandoffUnavailableStatus")
        : importText("noFiles")
    );
    markRouteReady(state, true);
    return;
  }

  state.fileSelect.innerHTML = files.map(stagedFileOption).join("");

  const handoff = docsImportReviewHandoff(files, state.reviewPackageId);
  const availableValues = new Set(files.map((file) => normalizeText(file && file.filename)));
  if (handoff.requested && !handoff.available) {
    state.fileSelect.insertAdjacentHTML(
      "afterbegin",
      `<option value="" disabled>${escapeHtml(importText("collectionHandoffUnavailableStatus"))}</option>`
    );
    state.fileSelect.value = "";
  } else if (previousValue && availableValues.has(previousValue)) {
    state.fileSelect.value = previousValue;
  } else {
    state.fileSelect.value = normalizeText(handoff.file && handoff.file.filename || files[0] && files[0].filename);
  }

  state.fileSelect.disabled = false;
  state.runButton.disabled = Boolean(handoff.requested && !handoff.available);
  state.collectionController.reset({
    active: Boolean(selectedCollectionFile(state))
  });
  syncSourceFormatControls(state);
  setStatus(
    state.statusNode,
    handoff.requested && !handoff.available ? "error" : "",
    handoff.requested && !handoff.available
      ? importText("collectionHandoffUnavailableStatus")
      : ""
  );
  markRouteReady(state, true);
}

function refreshStagedFiles(state) {
  if (!state.serviceAvailable || state.isRunning) return Promise.resolve(state.files);
  if (state.refreshPromise) return state.refreshPromise;

  state.fileSelect.disabled = true;
  state.runButton.disabled = true;
  state.refreshPromise = fetchImportFiles(state)
    .then((files) => {
      renderStagedFiles(state, files);
      return files;
    })
    .catch((error) => {
      console.warn("docs_import_source: staged file refresh failed", error);
      state.files = [];
      state.fileSelect.innerHTML = "";
      state.fileSelect.disabled = true;
      state.runButton.disabled = true;
      state.collectionController.reset({ active: false });
      syncSourceFormatControls(state);
      resetImportView(state, "");
      setStatus(state.statusNode, "error", importText("loadFilesFailed"));
      markRouteReady(state, true);
      return [];
    })
    .finally(() => {
      state.refreshPromise = null;
    });
  return state.refreshPromise;
}

function bindImportEvents(state) {
  state.scopeSelect.addEventListener("change", () => {
    persistSelectedScope(state, state.scopeSelect.value);
    if (!selectedCollectionFile(state)) return;
    state.collectionController.reset({ active: true });
    setStatus(state.statusNode, "", "");
    markRouteReady(state, true);
  });
  state.fileSelect.addEventListener("change", () => {
    state.runButton.disabled = false;
    resetImportView(state, "");
    state.collectionController.reset({
      active: Boolean(selectedCollectionFile(state))
    });
    syncSourceFormatControls(state);
    markRouteReady(state, true);
  });
  state.runButton.addEventListener("click", () => {
    runImport(state).catch((error) => console.warn("docs_import_source: unexpected import failure", error));
  });
  state.resultGridNode.addEventListener("click", (event) => {
    const target = event.target && event.target.closest
      ? event.target
      : event.target && event.target.parentElement
        ? event.target.parentElement
        : null;
    const link = target && target.closest
      ? target.closest("[data-doc-source-link]")
      : null;
    if (!link || !state.resultGridNode.contains(link)) return;
    event.preventDefault();
    openResultSource(state, link).catch((error) => console.warn("docs_import_source: unexpected open source failure", error));
  });
  state.confirmButton.addEventListener("click", () => {
    if (state.pendingOverwriteResolver) {
      state.pendingOverwriteResolver("confirm");
      return;
    }
    runImport(state).catch((error) => console.warn("docs_import_source: unexpected overwrite failure", error));
  });
  state.cancelButton.addEventListener("click", () => {
    if (state.pendingOverwriteResolver) {
      state.pendingOverwriteResolver("cancel");
      return;
    }
    resetDocsHtmlImportWarning(state);
    setStatus(
      state.statusNode,
      "",
      importText("overwriteCancelled")
    );
  });
}

async function openResultSource(state, link) {
  const scope = normalizeText(link && link.dataset ? link.dataset.scope : "");
  const docId = normalizeText(link && link.dataset ? link.dataset.docId : "");
  if (!scope || !docId) return;
  try {
    await fetchManagementJson("/docs/open-source", "POST", {
      scope,
      doc_id: docId,
      editor: "vscode"
    }, managementOptionsForState(state));
  } catch (error) {
    console.warn("docs_import_source: open source failed", error);
    setStatus(
      state.statusNode,
      "error",
      normalizeText(error && error.message)
        || importText("resultOpenSourceFailed")
    );
  }
}

function importScope(state) {
  const selectedScope = normalizeText(state.scopeSelect.value).toLowerCase();
  return state.docsScopeIds.includes(selectedScope) ? selectedScope : state.docsScopeIds[0];
}

async function runImport(state) {
  const collectionFile = selectedCollectionFile(state);
  if (collectionFile) {
    const scope = importScope(state);
    if (!scope) {
      setStatus(state.statusNode, "error", "Docs Viewer config does not define any import scopes.");
      return;
    }
    persistSelectedScope(state, scope);
    await state.collectionController.preview({
      file: collectionFile,
      scope,
      managementBaseUrl: state.managementBaseUrl
    });
    return;
  }
  const files = selectedImportFiles(state);
  if (!files.length) {
    setStatus(
      state.statusNode,
      "error",
      importText("fileRequired")
    );
    return;
  }

  const scope = importScope(state);
  if (!scope) {
    setStatus(state.statusNode, "error", "Docs Viewer config does not define any import scopes.");
    return;
  }
  persistSelectedScope(state, scope);
  await runDocsHtmlImportWorkflow(state, {
    files,
    scope,
    includePromptMeta: Boolean(state.includePromptMeta.checked),
    routePath: state.routePath,
    managementBaseUrl: state.managementBaseUrl,
    onRunningChange: (busy) => {
      syncRouteBusyState(state);
      state.onBusyChange(busy);
    },
    onTerminalResult: state.onTerminalResult
  });
}

export async function initDocsHtmlImport(options = {}) {
  const bootStatus = options.bootStatus || document.getElementById("docsHtmlImportBootStatus");
  const root = options.root || document.getElementById("docsHtmlImportRoot");
  if (!bootStatus || !root) return;
  if (root.dataset.docsImportInitialized === "true") return;
  root.dataset.docsImportInitialized = "true";
  initializeRouteState(root, { route: "docs-import" });

  const state = {
    bootStatus,
    root,
    fileLabelNode: document.getElementById("docsHtmlImportFileLabel"),
    fileSelect: document.getElementById("docsHtmlImportFileSelect"),
    scopeLabelNode: document.getElementById("docsHtmlImportScopeLabel"),
    scopeSelect: document.getElementById("docsHtmlImportScopeSelect"),
    includePromptMeta: document.getElementById("docsHtmlImportIncludePromptMeta"),
    includePromptMetaWrap: document.getElementById("docsHtmlImportIncludePromptMetaWrap"),
    includePromptMetaLabelNode: document.getElementById("docsHtmlImportIncludePromptMetaLabel"),
    runButton: document.getElementById("docsHtmlImportRun"),
    confirmButton: document.getElementById("docsHtmlImportConfirm"),
    cancelButton: document.getElementById("docsHtmlImportCancel"),
    statusNode: document.getElementById("docsHtmlImportStatus"),
    warningNode: document.getElementById("docsHtmlImportWarning"),
    collisionHeadingNode: document.getElementById("docsHtmlImportCollisionHeading"),
    collisionBodyNode: document.getElementById("docsHtmlImportCollisionBody"),
    collisionMetaNode: document.getElementById("docsHtmlImportCollisionMeta"),
    resultNode: document.getElementById("docsHtmlImportResult"),
    resultTitleNode: document.getElementById("docsHtmlImportResultTitle"),
    resultGridNode: document.getElementById("docsHtmlImportResultGrid"),
    resultDocIdNode: document.getElementById("docsHtmlImportResultDocId"),
    resultCountsNode: document.getElementById("docsHtmlImportResultCounts"),
    warningsWrap: document.getElementById("docsHtmlImportWarnings"),
    warningsHeading: document.getElementById("docsHtmlImportWarningsHeading"),
    warningsList: document.getElementById("docsHtmlImportWarningsList"),
    collectionView: document.getElementById("docsImportCollectionView"),
    pendingOverwriteDocId: "",
    pendingOverwriteResolver: null,
    persistScope: options.persistScope !== false,
    routePath: normalizeText(options.routePath) || "/docs/",
    managementBaseUrl: normalizeText(options.managementBaseUrl),
    serviceAvailable: false,
    isRunning: false,
    refreshPromise: null,
    files: [],
    docsScopeIds: [],
    reviewPackageId: normalizeText(options.reviewPackageId),
    onBusyChange: typeof options.onBusyChange === "function" ? options.onBusyChange : () => {},
    onTerminalResult: typeof options.onTerminalResult === "function" ? options.onTerminalResult : () => {}
  };
  state.collectionController = createDocsImportCollectionController({
    host: state.collectionView,
    statusNode: state.statusNode,
    routePath: state.routePath,
    onTerminalResult: state.onTerminalResult,
    onBusyChange: (busy) => {
      state.isRunning = busy;
      state.runButton.disabled = busy;
      syncRouteBusyState(state);
      state.onBusyChange(busy);
    }
  });

  const requiredNodes = [
    state.fileLabelNode,
    state.fileSelect,
    state.scopeLabelNode,
    state.scopeSelect,
    state.includePromptMeta,
    state.includePromptMetaWrap,
    state.includePromptMetaLabelNode,
    state.runButton,
    state.confirmButton,
    state.cancelButton,
    state.statusNode,
    state.warningNode,
    state.collisionHeadingNode,
    state.collisionBodyNode,
    state.collisionMetaNode,
    state.resultNode,
    state.resultTitleNode,
    state.resultGridNode,
    state.resultDocIdNode,
    state.resultCountsNode,
    state.warningsWrap,
    state.warningsHeading,
    state.warningsList,
    state.collectionView
  ];
  if (requiredNodes.some((node) => !node)) return;
  const importApp = {
    refreshStagedFiles: () => refreshStagedFiles(state)
  };

  try {
    state.docsScopeIds = await loadDocsViewerScopeOptions(options.docsViewerConfigUrl);
    state.managementBaseUrl = normalizeText(options.managementBaseUrl);
    const serviceAvailable = await fetchManagementJson("/health", "GET", undefined, managementOptionsForState(state))
      .then(() => true)
      .catch(() => false);
    state.serviceAvailable = Boolean(serviceAvailable);

    setText(state.fileLabelNode, importText("fileLabel"));
    setText(state.scopeLabelNode, importText("scopeLabel"));
    setText(state.includePromptMetaLabelNode, importText("includePromptMetaLabel"));
    setText(state.runButton, importText("importButton"));
    setText(state.confirmButton, importText("confirmOverwriteButton"));
    setText(state.cancelButton, importText("cancelOverwriteButton"));
    state.scopeSelect.innerHTML = state.docsScopeIds
      .map((scope) => `<option value="${escapeHtml(scope)}">${escapeHtml(scope)}</option>`)
      .join("");
    const initialScope = normalizeText(options.initialScope).toLowerCase();
    const fallbackScope = state.docsScopeIds[0] || "";
    state.scopeSelect.value = state.docsScopeIds.includes(initialScope)
      ? initialScope
      : selectedScopeFromUrl(state.docsScopeIds, fallbackScope);
    state.includePromptMeta.checked = false;
    bindImportEvents(state);

    root.hidden = false;
    bootStatus.hidden = true;

    if (!serviceAvailable) {
      state.runButton.disabled = true;
      state.fileSelect.disabled = true;
      state.scopeSelect.disabled = true;
      state.includePromptMeta.disabled = true;
      setStatus(
        state.statusNode,
        "error",
        DOCS_MANAGEMENT_UNAVAILABLE_MESSAGE
      );
      markRouteReady(state, true);
      return importApp;
    }

    await refreshStagedFiles(state);
    return importApp;
  } catch (error) {
    console.warn("docs_import_source: init failed", error);
    bootStatus.hidden = false;
    setStatus(
      bootStatus,
      "error",
      importText("loadFilesFailed")
    );
    root.hidden = false;
    state.serviceAvailable = false;
    markRouteReady(state, true);
    delete root.dataset.docsImportInitialized;
    throw error;
  }
}
