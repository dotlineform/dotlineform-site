import {
  DOCS_MANAGEMENT_UNAVAILABLE_MESSAGE,
  fetchManagementJson,
  openManagedDocSource
} from "../management/docs-viewer-management-client.js";
import {
  normalizeManagedDocumentCollectionTarget
} from "../management/docs-viewer-management-document-target.js";
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
  DOCS_IMPORT_COLLECTION_SOURCE_FORMAT,
  DOCS_IMPORT_EDITED_REVIEW_SOURCE_FORMAT,
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
  if (
    state
    && (
      state.persistScope === false
      || state.importDestination && state.importDestination.sub_scope
    )
  ) return;
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

function returnedPackagePath(destination) {
  return [
    "/docs/packages/returned?scope=",
    encodeURIComponent(normalizeText(destination && destination.scope).toLowerCase()),
    "&sub_scope=",
    encodeURIComponent(normalizeText(destination && destination.sub_scope).toLowerCase())
  ].join("");
}

export function docsReturnedPackageFilesForDestination(payload, destination) {
  const target = normalizeManagedDocumentCollectionTarget(destination);
  if (!target.sub_scope) {
    throw new Error("Returned-package discovery requires an exact child collection.");
  }
  if (
    normalizeText(payload && payload.scope).toLowerCase() !== target.scope
    || normalizeText(payload && payload.sub_scope).toLowerCase() !== target.sub_scope
  ) {
    throw new Error("Returned-package discovery did not match the requested child collection.");
  }
  return (Array.isArray(payload && payload.files) ? payload.files : []).filter((record) => (
    normalizeText(record && record.scope).toLowerCase() === target.scope
    && normalizeText(record && record.sub_scope).toLowerCase() === target.sub_scope
    && record.supports_return_import === true
  )).map((record) => ({
    ...record,
    source_format: DOCS_IMPORT_COLLECTION_SOURCE_FORMAT
  }));
}

async function fetchReturnedPackageFiles(state) {
  if (!fixedSubscopeDestination(state)) return [];
  const destination = state.importDestination;
  const payload = await fetchManagementJson(
    returnedPackagePath(destination),
    "GET",
    undefined,
    managementOptionsForState(state)
  );
  return docsReturnedPackageFilesForDestination(payload, destination);
}

async function fetchAvailableImportFiles(state) {
  if (!fixedSubscopeDestination(state)) return fetchImportFiles(state);
  const [ordinaryFiles, returnedPackages] = await Promise.all([
    fetchImportFiles(state),
    fetchReturnedPackageFiles(state).catch((error) => {
      state.returnedPackageLoadError = error;
      console.warn("docs_import_source: returned package refresh failed", error);
      return [];
    })
  ]);
  const target = normalizeManagedDocumentCollectionTarget(state.importDestination);
  return ordinaryFiles
    .filter((record) => (
      !isDocsImportCollectionRecord(record)
      || (
        normalizeText(record && record.source_format)
          === DOCS_IMPORT_EDITED_REVIEW_SOURCE_FORMAT
        && normalizeText(record && record.scope).toLowerCase() === target.scope
        && normalizeText(record && record.sub_scope).toLowerCase() === target.sub_scope
        && record.supports_return_import === true
      )
    ))
    .concat(returnedPackages);
}

export const DOCS_IMPORT_MODE_FILES = "files";
export const DOCS_IMPORT_MODE_DATA_SHARING = "data_sharing_packages";

function normalizeImportMode(value) {
  return normalizeText(value) === DOCS_IMPORT_MODE_DATA_SHARING
    ? DOCS_IMPORT_MODE_DATA_SHARING
    : DOCS_IMPORT_MODE_FILES;
}

function fixedSubscopeDestination(state) {
  return Boolean(
    state
    && state.importDestination
    && state.importDestination.sub_scope
  );
}

function importDestinationLabel(destination, configuredLabel = "") {
  const label = normalizeText(configuredLabel);
  if (label) return label;
  const scope = normalizeText(destination && destination.scope);
  const subScope = normalizeText(destination && destination.sub_scope);
  return subScope ? `${scope} / ${subScope}` : scope;
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
  const options = [
    `<option value="${DOCS_IMPORT_MODE_FILES}">${escapeHtml(importText("filesOption", { count: filesCount }))}</option>`,
    `<option value="${DOCS_IMPORT_MODE_DATA_SHARING}">${escapeHtml(importText("dataSharingPackagesOption", { count: packagesCount }))}</option>`
  ];
  state.typeSelect.innerHTML = options.join("");
  state.typeSelect.value = state.importMode;
}

function renderImportScopeOptions(state, fallbackScope = "") {
  if (fixedSubscopeDestination(state)) {
    state.scopeSelect.innerHTML = (
      `<option value="${escapeHtml(state.importDestination.scope)}">`
      + `${escapeHtml(state.importDestinationLabel)}</option>`
    );
    state.scopeSelect.value = state.importDestination.scope;
    return;
  }
  state.scopeSelect.innerHTML = state.docsScopeIds
    .map((scope) => `<option value="${escapeHtml(scope)}">${escapeHtml(scope)}</option>`)
    .join("");
  const normalizedFallback = normalizeText(fallbackScope).toLowerCase();
  const selectedScope = state.docsScopeIds.includes(normalizedFallback)
    ? normalizedFallback
    : selectedScopeFromUrl(state.docsScopeIds, state.docsScopeIds[0] || "");
  state.scopeSelect.value = selectedScope;
}

function setImportDestination(state, destination, options = {}) {
  state.importDestination = destination
    ? normalizeManagedDocumentCollectionTarget(destination)
    : null;
  state.importDestinationLabel = state.importDestination
    ? importDestinationLabel(state.importDestination, options.label)
    : "";
  if (fixedSubscopeDestination(state)) {
    state.importMode = DOCS_IMPORT_MODE_FILES;
    state.selectedFilenamesByMode[DOCS_IMPORT_MODE_DATA_SHARING] = [];
  }
  renderImportScopeOptions(state, options.fallbackScope);
  if (!state.files.length) {
    renderImportModeOptions(state);
    syncImportInputControls(state);
    return;
  }
  renderImportModeOptions(state);
  renderStagedFileList(state);
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
  state.typeSelect.disabled = (
    state.isRunning
    || !state.serviceAvailable
  );
  state.scopeSelect.disabled = (
    state.isRunning
    || !state.serviceAvailable
    || fixedSubscopeDestination(state)
  );
  state.fileSelect.disabled = state.isRunning || !state.serviceAvailable || !records.length;
  syncSourceFormatControls(state);
}

function resetImportView(state, statusMessage) {
  resetDocsHtmlImportWarning(state);
  clearDocsHtmlImportResult(state);
  setStatus(state.statusNode, "", statusMessage);
}

function collectionFileLabel(state, file) {
  const displayName = normalizeText(file && file.display_name);
  if (displayName) return displayName;
  const count = Number(file && file.document_count);
  const collectionLabel = normalizeText(state.importDestinationLabel)
    || [
      normalizeText(file && file.scope_label),
      normalizeText(file && file.sub_scope_label)
    ].filter(Boolean).join(" / ");
  return [
    normalizeText(file && file.filename),
    collectionLabel,
    Number.isInteger(count) && count >= 0
      ? importText("packageDocumentCount", { count })
      : ""
  ].filter(Boolean).join(" — ");
}

function stagedFileOption(state, file) {
  const filename = normalizeText(file && file.filename);
  if (isDocsImportCollectionRecord(file)) {
    return `<option value="${escapeHtml(filename)}">${escapeHtml(collectionFileLabel(state, file))}</option>`;
  }
  const displayName = normalizeText(file && file.display_name);
  if (displayName) {
    return `<option value="${escapeHtml(filename)}">${escapeHtml(displayName)}</option>`;
  }
  const sourceFormat = docsHtmlImportSourceFormatForRecord(file).replace(/_/g, " ");
  return `<option value="${escapeHtml(filename)}">${escapeHtml(`${filename} (${sourceFormat})`)}</option>`;
}

function selectFileOptions(state, filenames) {
  const selected = new Set((filenames || []).map(normalizeText).filter(Boolean));
  Array.from(state.fileSelect.options).forEach((option) => {
    option.selected = selected.has(normalizeText(option.value));
  });
}

function renderStagedFileList(state) {
  const records = docsImportFilesForMode(state.files, state.importMode);
  const availableValues = new Set(records.map((file) => normalizeText(file && file.filename)));
  const previousSelection = (state.selectedFilenamesByMode[state.importMode] || [])
    .filter((filename) => availableValues.has(filename));
  const packageMode = state.importMode === DOCS_IMPORT_MODE_DATA_SHARING;
  state.fileSelect.multiple = !packageMode;
  setText(state.fileLabelNode, importText(packageMode ? "packageLabel" : "fileLabel"));
  state.fileSelect.innerHTML = records.map((file) => stagedFileOption(state, file)).join("");

  if (previousSelection.length) {
    selectFileOptions(state, packageMode ? previousSelection.slice(0, 1) : previousSelection);
  } else if (records.length && !(packageMode && fixedSubscopeDestination(state))) {
    selectFileOptions(state, [normalizeText(records[0] && records[0].filename)]);
  } else {
    selectFileOptions(state, []);
  }

  state.fileSelect.disabled = !records.length;
  rememberSelectedFilenames(state);
  state.collectionController.reset({
    active: Boolean(selectedCollectionFile(state))
  });
  syncImportInputControls(state);

  const statusState = records.length ? "" : "warn";
  const statusMessage = records.length
    ? ""
    : importText(packageMode ? "noPackagesInMode" : "noFilesInMode");
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

  if (!docsImportFilesForMode(files, state.importMode).length) {
    state.importMode = (
      !fixedSubscopeDestination(state)
      && docsImportFilesForMode(files, DOCS_IMPORT_MODE_DATA_SHARING).length
    )
      ? DOCS_IMPORT_MODE_DATA_SHARING
      : DOCS_IMPORT_MODE_FILES;
  }
  renderImportModeOptions(state);
  renderStagedFileList(state);

  if (state.returnedPackageLoadError) {
    setStatus(state.statusNode, "error", importText("loadPackagesFailed"));
  } else if (!files.length) {
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
  state.returnedPackageLoadError = null;
  state.refreshPromise = fetchAvailableImportFiles(state)
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
    renderStagedFileList(state);
    markRouteReady(state, true);
  });
  state.scopeSelect.addEventListener("change", () => {
    if (fixedSubscopeDestination(state)) {
      state.scopeSelect.value = state.importDestination.scope;
      return;
    }
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
    if (state.pendingInteractiveOverwriteResolver) {
      state.pendingInteractiveOverwriteResolver("confirm");
      return;
    }
    runImport(state).catch((error) => console.warn("docs_import_source: unexpected overwrite failure", error));
  });
  state.cancelButton.addEventListener("click", () => {
    if (state.pendingInteractiveOverwriteResolver) {
      state.pendingInteractiveOverwriteResolver("cancel");
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
  const subScope = normalizeText(
    link && link.dataset ? link.dataset.subScope : ""
  );
  const docId = normalizeText(link && link.dataset ? link.dataset.docId : "");
  if (!scope || !docId) return;
  try {
    const target = {
      scope,
      doc_id: docId
    };
    if (subScope) target.sub_scope = subScope;
    await openManagedDocSource(target, "vscode", managementOptionsForState(state));
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
  if (state.importDestination) return state.importDestination.scope;
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
      subScope: normalizeText(
        state.importDestination && state.importDestination.sub_scope
      ),
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
    subScope: normalizeText(
      state.importDestination && state.importDestination.sub_scope
    ),
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
    collectionStatusNode: document.getElementById("docsImportCollectionStatus"),
    pendingInteractiveOverwriteResolver: null,
    persistScope: options.persistScope !== false,
    routePath: normalizeText(options.routePath) || "/docs/",
    managementBaseUrl: normalizeText(options.managementBaseUrl),
    serviceAvailable: false,
    isRunning: false,
    refreshPromise: null,
    returnedPackageLoadError: null,
    files: [],
    importMode: DOCS_IMPORT_MODE_FILES,
    importDestination: null,
    importDestinationLabel: "",
    selectedFilenamesByMode: {
      [DOCS_IMPORT_MODE_FILES]: [],
      [DOCS_IMPORT_MODE_DATA_SHARING]: []
    },
    docsScopeIds: [],
    onBusyChange: typeof options.onBusyChange === "function" ? options.onBusyChange : () => {},
    onCollectionStateChange: typeof options.onCollectionStateChange === "function"
      ? options.onCollectionStateChange
      : () => {},
    onTerminalResult: typeof options.onTerminalResult === "function" ? options.onTerminalResult : () => {}
  };
  state.collectionController = createDocsImportCollectionController({
    host: state.collectionView,
    statusNode: state.collectionStatusNode,
    previewStatusNode: state.statusNode,
    renderActions: false,
    routePath: state.routePath,
    onTerminalResult: state.onTerminalResult,
    onViewStateChange: state.onCollectionStateChange,
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
    state.collectionView,
    state.collectionStatusNode
  ];
  if (requiredNodes.some((node) => !node)) return;
  const importApp = {
    refreshStagedFiles: () => refreshStagedFiles(state),
    setDestination: (destination, destinationOptions = {}) => {
      setImportDestination(state, destination, destinationOptions);
    }
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
    const initialScope = normalizeText(options.initialScope).toLowerCase();
    const fallbackScope = state.docsScopeIds[0] || "";
    setImportDestination(
      state,
      options.initialDestination || null,
      {
        fallbackScope: state.docsScopeIds.includes(initialScope)
          ? initialScope
          : selectedScopeFromUrl(state.docsScopeIds, fallbackScope),
        label: options.initialDestinationLabel
      }
    );
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
