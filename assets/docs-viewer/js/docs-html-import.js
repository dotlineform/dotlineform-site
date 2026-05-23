import {
  fetchManagementJson
} from "./docs-viewer-management-client.js";
import {
  clearDocsHtmlImportResult,
  resetDocsHtmlImportWarning
} from "./docs-html-import-render.js";
import {
  docsHtmlImportManagementOptions,
  docsHtmlImportSourceFormatForRecord,
  runDocsHtmlImportWorkflow
} from "./docs-html-import-workflow.js";

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

function formatText(template, tokens = {}) {
  let text = String(template || "");
  Object.keys(tokens).forEach((key) => {
    text = text.replace(new RegExp(`\\{${key}\\}`, "g"), tokens[key]);
  });
  return text;
}

function configText(config, path, fallback, tokens = {}) {
  let current = config;
  String(path || "").split(".").filter(Boolean).forEach((key) => {
    if (current && Object.prototype.hasOwnProperty.call(current, key)) {
      current = current[key];
    } else {
      current = undefined;
    }
  });
  return formatText(String(current == null ? fallback == null ? "" : fallback : current), tokens);
}

async function loadDocsViewerText(textUrl = "/assets/docs-viewer/data/ui-text.json") {
  const response = await fetch(textUrl, {
    headers: { Accept: "application/json" },
    cache: "default"
  });
  if (!response.ok) {
    throw new Error(`Failed to load Docs Viewer UI text (${response.status})`);
  }
  const payload = await response.json();
  return payload && typeof payload === "object" && !Array.isArray(payload) ? payload : {};
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

async function loadDocsViewerScopeOptions(configUrl = "/assets/docs-viewer/data/docs-viewer-config.json") {
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

const ALL_STAGED_FILES_VALUE = "__all_staged_import_files__";

function managementOptionsForState(state) {
  return docsHtmlImportManagementOptions({
    managementBaseUrl: state.managementBaseUrl,
    config: state.config
  });
}

async function fetchImportFiles(state) {
  const payload = await fetchManagementJson("/docs/import-source-files", "GET", undefined, managementOptionsForState(state));
  return Array.isArray(payload.files) ? payload.files : [];
}

function isAllFilesSelected(state) {
  return normalizeText(state.fileSelect.value) === ALL_STAGED_FILES_VALUE;
}

function selectedFileRecord(state) {
  const filename = normalizeText(state.fileSelect.value);
  return state.files.find((file) => normalizeText(file && file.filename) === filename) || null;
}

function selectedImportFiles(state) {
  if (isAllFilesSelected(state)) return state.files.slice();
  const record = selectedFileRecord(state);
  return record ? [record] : [];
}

function syncSourceFormatControls(state) {
  const selectedFiles = selectedImportFiles(state);
  const supportsPromptMeta = selectedFiles.some((file) => docsHtmlImportSourceFormatForRecord(file) === "html");
  state.includePromptMeta.checked = supportsPromptMeta ? state.includePromptMeta.checked : false;
  state.includePromptMeta.disabled = !supportsPromptMeta || !state.serviceAvailable;
  state.includePromptMetaWrap.hidden = !supportsPromptMeta;
  state.includePromptMetaHintNode.hidden = !supportsPromptMeta || !normalizeText(state.includePromptMetaHintNode.textContent);
}

function resetImportView(state, statusMessage) {
  resetDocsHtmlImportWarning(state);
  clearDocsHtmlImportResult(state);
  setStatus(state.statusNode, "", statusMessage);
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
    console.warn("docs_html_import: open source failed", error);
    setStatus(
      state.statusNode,
      "error",
      normalizeText(error && error.message)
        || configText(state.config, "docs_html_import.result_open_source_failed", "Failed to open source doc.")
    );
  }
}

function importScope(state) {
  const selectedScope = normalizeText(state.scopeSelect.value).toLowerCase();
  return state.docsScopeIds.includes(selectedScope) ? selectedScope : state.docsScopeIds[0];
}

async function runImport(state) {
  const files = selectedImportFiles(state);
  if (!files.length) {
    setStatus(
      state.statusNode,
      "error",
      configText(state.config, "docs_html_import.file_required", "Select a staged file first.")
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
    config: state.config,
    onRunningChange: () => syncRouteBusyState(state)
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
    introNode: document.getElementById("docsHtmlImportIntro"),
    fileLabelNode: document.getElementById("docsHtmlImportFileLabel"),
    fileSelect: document.getElementById("docsHtmlImportFileSelect"),
    scopeLabelNode: document.getElementById("docsHtmlImportScopeLabel"),
    scopeSelect: document.getElementById("docsHtmlImportScopeSelect"),
    includePromptMeta: document.getElementById("docsHtmlImportIncludePromptMeta"),
    includePromptMetaWrap: document.getElementById("docsHtmlImportIncludePromptMetaWrap"),
    includePromptMetaLabelNode: document.getElementById("docsHtmlImportIncludePromptMetaLabel"),
    includePromptMetaHintNode: document.getElementById("docsHtmlImportIncludePromptMetaHint"),
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
    pendingOverwriteDocId: "",
    pendingOverwriteResolver: null,
    replaceAllOverwrites: false,
    persistScope: options.persistScope !== false,
    routePath: normalizeText(options.routePath) || "/docs/",
    managementBaseUrl: normalizeText(options.managementBaseUrl),
    serviceAvailable: false,
    isRunning: false,
    files: [],
    config: null,
    docsScopeIds: []
  };

  const requiredNodes = [
    state.introNode,
    state.fileLabelNode,
    state.fileSelect,
    state.scopeLabelNode,
    state.scopeSelect,
    state.includePromptMeta,
    state.includePromptMetaWrap,
    state.includePromptMetaLabelNode,
    state.includePromptMetaHintNode,
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
    state.warningsList
  ];
  if (requiredNodes.some((node) => !node)) return;

  try {
    state.config = await loadDocsViewerText(options.uiTextUrl || root.dataset.uiTextUrl || "/assets/docs-viewer/data/ui-text.json");
    state.docsScopeIds = await loadDocsViewerScopeOptions(options.docsViewerConfigUrl);
    state.managementBaseUrl = normalizeText(options.managementBaseUrl);
    const serviceAvailable = await fetchManagementJson("/health", "GET", undefined, managementOptionsForState(state))
      .then(() => true)
      .catch(() => false);
    state.serviceAvailable = Boolean(serviceAvailable);

    if (options.hideIntro) {
      setText(state.introNode, "");
      state.introNode.hidden = true;
    } else {
      setText(
        state.introNode,
        configText(
          state.config,
          "docs_html_import.intro",
          "Import staged source files into the Studio, Analysis, or Library docs source."
        )
      );
      state.introNode.hidden = false;
    }
    setText(state.fileLabelNode, configText(state.config, "docs_html_import.file_label", "staged file"));
    setText(state.scopeLabelNode, configText(state.config, "docs_html_import.scope_label", "publish into"));
    setText(
      state.includePromptMetaLabelNode,
      configText(
        state.config,
        "docs_html_import.include_prompt_meta_label",
        "Include obvious prompt/meta blocks"
      )
    );
    setText(state.includePromptMetaHintNode, configText(state.config, "docs_html_import.include_prompt_meta_hint", ""));
    setText(state.runButton, configText(state.config, "docs_html_import.import_button", "Import"));
    setText(
      state.confirmButton,
      configText(state.config, "docs_html_import.confirm_overwrite_button", "Confirm overwrite")
    );
    setText(
      state.cancelButton,
      configText(state.config, "docs_html_import.cancel_overwrite_button", "Cancel")
    );
    state.scopeSelect.innerHTML = state.docsScopeIds
      .map((scope) => `<option value="${escapeHtml(scope)}">${escapeHtml(scope)}</option>`)
      .join("");
    const initialScope = normalizeText(options.initialScope).toLowerCase();
    const fallbackScope = state.docsScopeIds[0] || "";
    state.scopeSelect.value = state.docsScopeIds.includes(initialScope)
      ? initialScope
      : selectedScopeFromUrl(state.docsScopeIds, fallbackScope);
    state.scopeSelect.addEventListener("change", () => persistSelectedScope(state, state.scopeSelect.value));
    state.includePromptMeta.checked = false;

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
        configText(
          state.config,
          "docs_html_import.service_unavailable",
          "Docs management service unavailable. Start bin/local-studio to run imports."
        )
      );
      markRouteReady(state, true);
      return;
    }

    const files = await fetchImportFiles(state);
    state.files = files;
    if (!files.length) {
      state.runButton.disabled = true;
      state.fileSelect.disabled = true;
      setStatus(
        state.statusNode,
        "warn",
        configText(
          state.config,
          "docs_html_import.no_files",
          "No supported staged import files found under var/docs/import-staging/."
        )
      );
      markRouteReady(state, true);
      return;
    }

    state.fileSelect.innerHTML = [
      `<option value="${escapeHtml(ALL_STAGED_FILES_VALUE)}">${escapeHtml(configText(state.config, "docs_html_import.all_files_option", "< all >"))}</option>`
    ].concat(files.map((file) => {
      const filename = normalizeText(file.filename);
      const sourceFormat = docsHtmlImportSourceFormatForRecord(file).replace(/_/g, " ");
      return `<option value="${escapeHtml(filename)}">${escapeHtml(`${filename} (${sourceFormat})`)}</option>`;
    })).join("");
    state.fileSelect.value = normalizeText(files[0] && files[0].filename);
    syncSourceFormatControls(state);

    setStatus(
      state.statusNode,
      "",
      configText(
        state.config,
        "docs_html_import.idle_status",
        "Select a staged source file and import it into Studio, Analysis, or Library docs."
      )
    );
    markRouteReady(state, true);

    state.fileSelect.addEventListener("change", () => {
      syncSourceFormatControls(state);
      resetImportView(
        state,
        configText(
          state.config,
          "docs_html_import.idle_status",
          "Select a staged source file and import it into Studio, Analysis, or Library docs."
        )
      );
    });

    state.runButton.addEventListener("click", () => {
      runImport(state).catch((error) => console.warn("docs_html_import: unexpected import failure", error));
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
      openResultSource(state, link).catch((error) => console.warn("docs_html_import: unexpected open source failure", error));
    });
    state.confirmButton.addEventListener("click", () => {
      if (state.pendingOverwriteResolver) {
        state.pendingOverwriteResolver("confirm");
        return;
      }
      runImport(state).catch((error) => console.warn("docs_html_import: unexpected overwrite failure", error));
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
        configText(state.config, "docs_html_import.overwrite_cancelled", "Overwrite cancelled.")
      );
    });
  } catch (error) {
    console.warn("docs_html_import: init failed", error);
    bootStatus.hidden = false;
    setStatus(
      bootStatus,
      "error",
      configText(state.config || {}, "docs_html_import.load_files_failed", "Failed to load staged import files.")
    );
    root.hidden = false;
    state.serviceAvailable = false;
    markRouteReady(state, true);
  }
}
