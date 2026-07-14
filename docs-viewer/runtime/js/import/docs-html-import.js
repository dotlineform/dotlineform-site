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

export const DOCS_IMPORT_MODE_FILES = "files";
export const DOCS_IMPORT_MODE_DATA_SHARING = "data_sharing_packages";

function normalizeImportMode(value) {
  return normalizeText(value) === DOCS_IMPORT_MODE_DATA_SHARING
    ? DOCS_IMPORT_MODE_DATA_SHARING
    : DOCS_IMPORT_MODE_FILES;
}

export function docsImportFilesForMode(files, mode) {
  const records = Array.isArray(files) ? files : [];
  const wantsCollections = normalizeImportMode(mode) === DOCS_IMPORT_MODE_DATA_SHARING;
  return records.filter((record) => isDocsImportCollectionRecord(record) === wantsCollections);
}

function selectedFilenames(state) {
  return Array.from(state.fileSelect.selectedOptions || [])
    .map((option) => normalizeText(option.value))
    .filter(Boolean);
}

function rememberSelectedFilenames(state) {
  state.selectedFilenamesByMode[state.importMode] = selectedFilenames(state);
}

function selectedRecordsForMode(state, mode) {
  const selected = new Set(
    mode === state.importMode
      ? selectedFilenames(state)
      : state.selectedFilenamesByMode[mode] || []
  );
  return docsImportFilesForMode(state.files, mode).filter((record) => (
    selected.has(normalizeText(record && record.filename))
  ));
}

export function docsImportReviewHandoff(files, packageId) {
  const normalizedPackageId = normalizeText(packageId);
  const file = normalizedPackageId ? files.find((record) => (
    isDocsImportCollectionRecord(record)
    && Array.isArray(record && record.review_package_ids)
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
  if (state.importMode !== DOCS_IMPORT_MODE_FILES) return [];
  return selectedRecordsForMode(state, DOCS_IMPORT_MODE_FILES);
}

function selectedCollectionFile(state) {
  if (state.importMode !== DOCS_IMPORT_MODE_DATA_SHARING) return null;
  return selectedRecordsForMode(state, DOCS_IMPORT_MODE_DATA_SHARING)[0] || null;
}

function renderImportModeOptions(state) {
  const filesCount = docsImportFilesForMode(state.files, DOCS_IMPORT_MODE_FILES).length;
  const packagesCount = docsImportFilesForMode(state.files, DOCS_IMPORT_MODE_DATA_SHARING).length;
  state.typeSelect.innerHTML = [
    `<option value="${DOCS_IMPORT_MODE_FILES}">${escapeHtml(importText("filesOption", { count: filesCount }))}</option>`,
    `<option value="${DOCS_IMPORT_MODE_DATA_SHARING}">${escapeHtml(importText("dataSharingPackagesOption", { count: packagesCount }))}</option>`
  ].join("");
  state.typeSelect.value = state.importMode;
}

function syncSourceFormatControls(state) {
  const selectedFiles = selectedImportFiles(state);
  const collectionFile = selectedCollectionFile(state);
  const availableFiles = docsImportFilesForMode(state.files, DOCS_IMPORT_MODE_FILES);
  const supportsPromptMeta = selectedFiles.some((file) => docsHtmlImportSourceFormatForRecord(file) === "html");
  state.includePromptMeta.checked = supportsPromptMeta ? state.includePromptMeta.checked : false;
  state.includePromptMeta.disabled = !supportsPromptMeta || !state.serviceAvailable;
  state.includePromptMetaWrap.hidden = !supportsPromptMeta;
  state.selectionBar.hidden = state.importMode !== DOCS_IMPORT_MODE_FILES;
  state.selectionCountNode.textContent = importText("selectedCount", {
    count: state.importMode === DOCS_IMPORT_MODE_FILES ? selectedFiles.length : collectionFile ? 1 : 0
  });
  const allFilesSelected = Boolean(availableFiles.length && selectedFiles.length === availableFiles.length);
  state.selectAllButton.textContent = importText(
    allFilesSelected ? "clearSelectionButton" : "selectAllButton"
  );
  state.selectAllButton.disabled = state.isRunning || !state.serviceAvailable || !availableFiles.length;
  state.runButton.textContent = collectionFile
    ? importText("collectionPreviewButton")
    : importText("importSelectedButton");
  state.runButton.disabled = state.isRunning || !state.serviceAvailable || (!collectionFile && !selectedFiles.length);
  state.collectionController.setActive(Boolean(collectionFile));
}

function syncImportInputControls(state) {
  const records = docsImportFilesForMode(state.files, state.importMode);
  const handoff = docsImportReviewHandoff(state.files, state.reviewPackageId);
  const handoffUnavailable = state.importMode === DOCS_IMPORT_MODE_DATA_SHARING
    && handoff.requested
    && !handoff.available;
  state.typeSelect.disabled = state.isRunning || !state.serviceAvailable;
  state.scopeSelect.disabled = state.isRunning || !state.serviceAvailable;
  state.fileSelect.disabled = state.isRunning || !state.serviceAvailable || !records.length || handoffUnavailable;
  syncSourceFormatControls(state);
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

function selectFileOptions(state, filenames) {
  const selected = new Set((filenames || []).map(normalizeText).filter(Boolean));
  Array.from(state.fileSelect.options).forEach((option) => {
    option.selected = selected.has(normalizeText(option.value));
  });
}

function renderStagedFileList(state, handoff) {
  const records = docsImportFilesForMode(state.files, state.importMode);
  const availableValues = new Set(records.map((file) => normalizeText(file && file.filename)));
  const previousSelection = (state.selectedFilenamesByMode[state.importMode] || [])
    .filter((filename) => availableValues.has(filename));
  const packageMode = state.importMode === DOCS_IMPORT_MODE_DATA_SHARING;
  state.fileSelect.multiple = !packageMode;
  setText(state.fileLabelNode, importText(packageMode ? "packageLabel" : "fileLabel"));
  state.fileSelect.innerHTML = records.map(stagedFileOption).join("");

  if (packageMode && handoff.requested && !handoff.available) {
    state.fileSelect.insertAdjacentHTML(
      "afterbegin",
      `<option value="" disabled>${escapeHtml(importText("collectionHandoffUnavailableStatus"))}</option>`
    );
    state.fileSelect.value = "";
  } else if (packageMode && handoff.file) {
    state.fileSelect.value = normalizeText(handoff.file.filename);
  } else if (previousSelection.length) {
    selectFileOptions(state, packageMode ? previousSelection.slice(0, 1) : previousSelection);
  } else if (records.length) {
    selectFileOptions(state, [normalizeText(records[0] && records[0].filename)]);
  } else {
    state.fileSelect.value = "";
  }

  state.fileSelect.disabled = !records.length || Boolean(packageMode && handoff.requested && !handoff.available);
  rememberSelectedFilenames(state);
  state.collectionController.reset({
    active: Boolean(selectedCollectionFile(state))
  });
  syncImportInputControls(state);

  let statusState = "";
  let statusMessage = "";
  if (packageMode && handoff.requested && !handoff.available) {
    statusState = "error";
    statusMessage = importText("collectionHandoffUnavailableStatus");
  } else if (packageMode && handoff.file) {
    statusMessage = importText("collectionHandoffReadyStatus");
  } else if (!records.length) {
    statusState = "warn";
    statusMessage = importText(packageMode ? "noPackagesInMode" : "noFilesInMode");
  }
  setStatus(
    state.statusNode,
    statusState,
    statusMessage
  );
}

function renderStagedFiles(state, files) {
  rememberSelectedFilenames(state);
  state.files = files;
  resetImportView(state, "");
  state.collectionController.reset({ active: false });

  const handoff = docsImportReviewHandoff(files, state.reviewPackageId);
  if (handoff.requested) {
    state.importMode = DOCS_IMPORT_MODE_DATA_SHARING;
  } else if (!docsImportFilesForMode(files, state.importMode).length) {
    state.importMode = docsImportFilesForMode(files, DOCS_IMPORT_MODE_DATA_SHARING).length
      ? DOCS_IMPORT_MODE_DATA_SHARING
      : DOCS_IMPORT_MODE_FILES;
  }
  renderImportModeOptions(state);
  renderStagedFileList(state, handoff);

  if (!files.length && !handoff.requested) {
    setStatus(state.statusNode, "warn", importText("noFiles"));
  }
  markRouteReady(state, true);
}

function refreshStagedFiles(state) {
  if (!state.serviceAvailable || state.isRunning) return Promise.resolve(state.files);
  if (state.refreshPromise) return state.refreshPromise;

  state.fileSelect.disabled = true;
  state.typeSelect.disabled = true;
  state.selectAllButton.disabled = true;
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
      state.typeSelect.disabled = true;
      state.selectAllButton.disabled = true;
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
  state.typeSelect.addEventListener("change", () => {
    rememberSelectedFilenames(state);
    state.importMode = normalizeImportMode(state.typeSelect.value);
    resetImportView(state, "");
    state.collectionController.reset({ active: false });
    renderStagedFileList(state, docsImportReviewHandoff(state.files, state.reviewPackageId));
    markRouteReady(state, true);
  });
  state.scopeSelect.addEventListener("change", () => {
    persistSelectedScope(state, state.scopeSelect.value);
    if (!selectedCollectionFile(state)) return;
    state.collectionController.reset({ active: true });
    setStatus(state.statusNode, "", "");
    markRouteReady(state, true);
  });
  state.fileSelect.addEventListener("change", () => {
    rememberSelectedFilenames(state);
    resetImportView(state, "");
    state.collectionController.reset({
      active: Boolean(selectedCollectionFile(state))
    });
    syncImportInputControls(state);
    markRouteReady(state, true);
  });
  state.selectAllButton.addEventListener("click", () => {
    if (state.importMode !== DOCS_IMPORT_MODE_FILES) return;
    const availableFiles = docsImportFilesForMode(state.files, DOCS_IMPORT_MODE_FILES);
    const clearSelection = Boolean(availableFiles.length && selectedImportFiles(state).length === availableFiles.length);
    Array.from(state.fileSelect.options).forEach((option) => {
      option.selected = !clearSelection;
    });
    rememberSelectedFilenames(state);
    resetImportView(state, "");
    state.collectionController.reset({ active: false });
    syncImportInputControls(state);
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
      syncImportInputControls(state);
      syncRouteBusyState(state);
      state.onBusyChange(busy);
    },
    onTerminalResult: state.onTerminalResult
  });
  syncImportInputControls(state);
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
    typeLabelNode: document.getElementById("docsHtmlImportTypeLabel"),
    typeSelect: document.getElementById("docsHtmlImportTypeSelect"),
    fileLabelNode: document.getElementById("docsHtmlImportFileLabel"),
    fileSelect: document.getElementById("docsHtmlImportFileSelect"),
    selectionBar: document.getElementById("docsHtmlImportSelectionBar"),
    selectAllButton: document.getElementById("docsHtmlImportSelectAll"),
    selectionCountNode: document.getElementById("docsHtmlImportSelectionCount"),
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
    importMode: DOCS_IMPORT_MODE_FILES,
    selectedFilenamesByMode: {
      [DOCS_IMPORT_MODE_FILES]: [],
      [DOCS_IMPORT_MODE_DATA_SHARING]: []
    },
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
      syncImportInputControls(state);
      syncRouteBusyState(state);
      state.onBusyChange(busy);
    }
  });

  const requiredNodes = [
    state.typeLabelNode,
    state.typeSelect,
    state.fileLabelNode,
    state.fileSelect,
    state.selectionBar,
    state.selectAllButton,
    state.selectionCountNode,
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

    setText(state.typeLabelNode, importText("typeLabel"));
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
      state.typeSelect.disabled = true;
      state.selectAllButton.disabled = true;
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
