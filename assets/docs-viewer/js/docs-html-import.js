import {
  fetchManagementJson
} from "./docs-viewer-management-client.js";
import {
  openReplacementDocIdModal
} from "./docs-html-import-modals.js";

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

function setHtml(node, value) {
  if (!node) return;
  node.innerHTML = String(value == null ? "" : value);
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
  return formatText(String(current || fallback || ""), tokens);
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

function buildActivityContext({
  pageId,
  actionId,
  route,
  controlId,
  controlSelector,
  recordIdField,
  recordId
}) {
  const normalizedActionId = normalizeText(actionId);
  const normalizedRecordId = normalizeText(recordId);
  const fallback = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  const randomId = window.crypto && typeof window.crypto.randomUUID === "function"
    ? window.crypto.randomUUID()
    : fallback;
  return {
    page_id: pageId,
    action_id: normalizedActionId,
    route,
    control_id: controlId,
    control_selector: controlSelector,
    correlation_id: `${normalizedActionId}:${normalizedRecordId}:${randomId}`,
    [recordIdField]: normalizedRecordId
  };
}

function managementOptions(state) {
  return {
    baseUrl: state.managementBaseUrl,
    serverNotConfiguredError: configText(
      state.config || {},
      "docs_html_import.server_not_configured",
      "Local docs-management server is not configured."
    ),
    fetch: (url, options) => window.fetch(url, options)
  };
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

function viewerLinkHtml(config, href, fallbackLabel) {
  const label = configText(config, "docs_html_import.result_open_viewer", fallbackLabel || "Open viewer");
  if (!normalizeText(href)) return "";
  return `<a href="${escapeHtml(href)}" target="_blank" rel="noopener noreferrer">${escapeHtml(label)}</a>`;
}

function sourceDocLinkHtml(scope, docId) {
  const normalizedScope = normalizeText(scope);
  const normalizedDocId = normalizeText(docId);
  if (!normalizedScope || !normalizedDocId) return "";
  return [
    `<a href="#" data-doc-source-link="true"`,
    ` data-scope="${escapeHtml(normalizedScope)}"`,
    ` data-doc-id="${escapeHtml(normalizedDocId)}">`,
    `${escapeHtml(normalizedDocId)}</a>`
  ].join("");
}

function mediaPlansFromPreview(preview) {
  if (Array.isArray(preview.media_plans)) {
    return preview.media_plans.filter((plan) => plan && typeof plan === "object");
  }
  return preview.media_plan && typeof preview.media_plan === "object" ? [preview.media_plan] : [];
}

function mediaPlanListHtml(plans, key) {
  return plans
    .map((plan) => normalizeText(plan[key]))
    .filter(Boolean)
    .map((value) => escapeHtml(value))
    .join("<br>");
}

async function fetchImportFiles(state) {
  const payload = await fetchManagementJson("/docs/import-source-files", "GET", undefined, managementOptions(state));
  return Array.isArray(payload.files) ? payload.files : [];
}

function selectedFileRecord(state) {
  const filename = normalizeText(state.fileSelect.value);
  return state.files.find((file) => normalizeText(file && file.filename) === filename) || null;
}

function selectedSourceFormat(state) {
  const record = selectedFileRecord(state);
  return normalizeText(record && record.source_format).toLowerCase() || "html";
}

function syncSourceFormatControls(state) {
  const supportsPromptMeta = selectedSourceFormat(state) === "html";
  state.includePromptMeta.checked = supportsPromptMeta ? state.includePromptMeta.checked : false;
  state.includePromptMeta.disabled = !supportsPromptMeta || !state.serviceAvailable;
  state.includePromptMetaWrap.hidden = !supportsPromptMeta;
  state.includePromptMetaHintNode.hidden = !supportsPromptMeta;
}

function resetWarning(state) {
  state.pendingOverwriteDocId = "";
  state.warningNode.hidden = true;
  setText(state.collisionMetaNode, "");
  state.confirmButton.hidden = true;
  state.cancelButton.hidden = true;
}

function clearImportResult(state) {
  state.resultNode.hidden = true;
  state.warningsWrap.hidden = true;
  state.warningsList.innerHTML = "";
}

function resetImportView(state, statusMessage) {
  resetWarning(state);
  clearImportResult(state);
  setStatus(state.statusNode, "", statusMessage);
}

function renderWarnings(state, warnings) {
  const items = Array.isArray(warnings) ? warnings.filter((item) => normalizeText(item)) : [];
  if (!items.length) {
    state.warningsWrap.hidden = true;
    state.warningsList.innerHTML = "";
    return;
  }
  setText(
    state.warningsHeading,
    configText(state.config, "docs_html_import.warnings_heading", "Warnings")
  );
  state.warningsList.innerHTML = items.map((warning) => `<li>${escapeHtml(warning)}</li>`).join("");
  state.warningsWrap.hidden = false;
}

function renderResult(state, payload) {
  const preview = payload && payload.import_preview && typeof payload.import_preview === "object"
    ? payload.import_preview
    : {};
  setText(
    state.resultTitleNode,
    payload.operation === "overwrite"
      ? configText(state.config, "docs_html_import.result_operation_overwrite", "Overwrote existing doc")
      : configText(state.config, "docs_html_import.result_operation_create", "Created new doc")
  );
  setText(state.resultScopeLabelNode, configText(state.config, "docs_html_import.result_scope", "scope"));
  setText(state.resultDocIdLabelNode, configText(state.config, "docs_html_import.result_doc_id", "doc_id"));
  setText(state.resultTitleLabelNode, configText(state.config, "docs_html_import.result_title_label", "title"));
  setText(state.resultSourceLabelNode, configText(state.config, "docs_html_import.result_source", "source"));
  setText(state.resultViewerLabelNode, configText(state.config, "docs_html_import.result_viewer", "viewer"));
  setText(state.resultBackupLabelNode, configText(state.config, "docs_html_import.result_backup", "backup"));
  setText(state.resultMediaSourceLabelNode, configText(state.config, "docs_html_import.result_media_source", "staged media"));
  setText(state.resultMediaKeyLabelNode, configText(state.config, "docs_html_import.result_media_key", "media path"));
  setText(state.resultMediaTokenLabelNode, configText(state.config, "docs_html_import.result_media_token", "media link"));
  setText(state.resultScopeNode, payload.scope);
  setHtml(state.resultDocIdNode, sourceDocLinkHtml(payload.scope, payload.doc_id));
  setText(state.resultDocTitleNode, payload.title || preview.title || "");
  setText(state.resultSourceNode, preview.source_path || preview.source_html || payload.staged_filename || "");
  setHtml(
    state.resultViewerNode,
    payload.viewer_url ? viewerLinkHtml(state.config, payload.viewer_url, "Open viewer") : ""
  );
  setText(state.resultBackupNode, payload.backup_dir || "");
  const mediaPlans = mediaPlansFromPreview(preview);
  const mediaSourceHtml = mediaPlanListHtml(mediaPlans, "staging_path") || mediaPlanListHtml(mediaPlans, "source_path");
  if (mediaSourceHtml) {
    setHtml(state.resultMediaSourceNode, mediaSourceHtml);
    state.resultMediaSourceRow.hidden = false;
  } else {
    setHtml(state.resultMediaSourceNode, "");
    state.resultMediaSourceRow.hidden = true;
  }
  const mediaKeyHtml = mediaPlanListHtml(mediaPlans, "media_path");
  if (mediaKeyHtml) {
    setHtml(state.resultMediaKeyNode, mediaKeyHtml);
    state.resultMediaKeyRow.hidden = false;
  } else {
    setHtml(state.resultMediaKeyNode, "");
    state.resultMediaKeyRow.hidden = true;
  }
  const mediaTokenHtml = mediaPlanListHtml(mediaPlans, "media_token");
  if (mediaTokenHtml) {
    setHtml(state.resultMediaTokenNode, mediaTokenHtml);
    state.resultMediaTokenRow.hidden = false;
  } else {
    setHtml(state.resultMediaTokenNode, "");
    state.resultMediaTokenRow.hidden = true;
  }

  const stats = preview.source_stats && typeof preview.source_stats === "object" ? preview.source_stats : {};
  if (preview.source_format === "markdown") {
    setText(
      state.resultCountsNode,
      configText(
        state.config,
        "docs_html_import.result_markdown_counts",
        "{chars} chars, {links} links, {images} images",
        {
          chars: Number(stats.chars || 0),
          links: Number(stats.links || 0),
          images: Number(stats.images || 0)
        }
      )
    );
  } else {
    setText(
      state.resultCountsNode,
      configText(
        state.config,
        "docs_html_import.result_summary_counts",
        "{links} links, {images} images, {svg} SVG, {details} details blocks",
        {
          links: Number(stats.links || 0),
          images: Number(stats.images || 0),
          svg: Number(stats.svg || 0),
          details: Number(stats.details || 0)
        }
      )
    );
  }
  renderWarnings(state, preview.warnings);
  state.resultNode.hidden = false;
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
    }, managementOptions(state));
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

function renderOverwriteWarning(state, payload) {
  const collision = payload && payload.collision && typeof payload.collision === "object" ? payload.collision : {};
  const preview = payload && payload.import_preview && typeof payload.import_preview === "object"
    ? payload.import_preview
    : {};
  state.pendingOverwriteDocId = normalizeText(collision.doc_id);
  setText(
    state.collisionHeadingNode,
    configText(state.config, "docs_html_import.collision_heading", "Overwrite warning")
  );
  setText(
    state.collisionBodyNode,
    configText(
      state.config,
      "docs_html_import.collision_body",
      "This import matches an existing doc target. Confirm overwrite to replace the current source while keeping the same doc identity and filename."
    )
  );
  setText(
    state.collisionMetaNode,
    configText(
      state.config,
      "docs_html_import.overwrite_required",
      "Overwrite required: {doc_id} ({title}). Review the warning and confirm if you want to replace it.",
      {
        doc_id: collision.doc_id || preview.proposed_doc_id || "",
        title: collision.title || preview.title || ""
      }
    )
  );
  state.warningNode.hidden = false;
  state.confirmButton.hidden = false;
  state.cancelButton.hidden = false;
}

async function handleReplacementDocIdModal(state, payload) {
  const result = await openReplacementDocIdModal({
    root: state.root,
    config: state.config,
    payload
  });
  if (!result || result.action === "cancel") {
    setStatus(
      state.statusNode,
      "",
      configText(state.config, "docs_html_import.filename_conflict_cancelled", "Import cancelled.")
    );
    return;
  }
  if (result.action === "replace" && result.overwriteDocId) {
    await runImport(state, { overwriteDocId: result.overwriteDocId, confirmOverwrite: true });
    return;
  }
  if (result.action === "rename" && result.replacementDocId) {
    await runImport(state, { replacementDocId: result.replacementDocId });
  }
}

async function runImport(state, { overwriteDocId = "", confirmOverwrite = false, replacementDocId = "" } = {}) {
  const stagedFilename = normalizeText(state.fileSelect.value);
  if (!stagedFilename) {
    setStatus(
      state.statusNode,
      "error",
      configText(state.config, "docs_html_import.file_required", "Select a staged file first.")
    );
    return;
  }

  const selectedScope = normalizeText(state.scopeSelect.value).toLowerCase();
  const scope = state.docsScopeIds.includes(selectedScope) ? selectedScope : state.docsScopeIds[0];
  if (!scope) {
    setStatus(state.statusNode, "error", "Docs Viewer config does not define any import scopes.");
    return;
  }
  const normalizedReplacementDocId = normalizeText(replacementDocId);
  persistSelectedScope(state, scope);
  state.runButton.disabled = true;
  state.confirmButton.disabled = true;
  state.cancelButton.disabled = true;
  resetImportView(
    state,
    configText(state.config, "docs_html_import.running_status", "Converting and validating staged source…")
  );
  state.isRunning = true;
  syncRouteBusyState(state);

  try {
    const payload = await fetchManagementJson("/docs/import-source", "POST", {
      scope,
      staged_filename: stagedFilename,
      include_prompt_meta: selectedSourceFormat(state) === "html" ? Boolean(state.includePromptMeta.checked) : false,
      overwrite_doc_id: overwriteDocId,
      confirm_overwrite: confirmOverwrite,
      replacement_doc_id: normalizedReplacementDocId,
      preview_only: false,
      activity_context: buildActivityContext({
        pageId: "docs-import",
        actionId: "import-docs-source",
        route: state.routePath || "/docs/",
        controlId: "docsHtmlImportRun",
        controlSelector: "#docsHtmlImportRun",
        recordIdField: "staged_filename",
        recordId: stagedFilename
      })
    }, managementOptions(state));

    if (payload.preview_only && (payload.replacement_doc_id_required || payload.replacement_title_required)) {
      renderWarnings(state, payload.import_preview && payload.import_preview.warnings);
      setStatus(
        state.statusNode,
        "warn",
        payload.summary_text || configText(state.config, "docs_html_import.replacement_doc_id_required", "Enter a doc_id first.")
      );
      await handleReplacementDocIdModal(state, payload);
      return;
    }

    if (payload.preview_only && payload.requires_overwrite_confirmation) {
      renderOverwriteWarning(state, payload);
      renderWarnings(state, payload.import_preview && payload.import_preview.warnings);
      setStatus(
        state.statusNode,
        "warn",
        payload.summary_text || configText(state.config, "docs_html_import.overwrite_required", "Overwrite required.")
      );
      return;
    }

    renderResult(state, payload);
    setStatus(state.statusNode, "success", payload.summary_text || "");
  } catch (error) {
    console.warn("docs_html_import: import failed", error);
    setStatus(
      state.statusNode,
      "error",
      normalizeText(error && error.message) || configText(state.config, "docs_html_import.import_failed", "Import failed.")
    );
  } finally {
    state.isRunning = false;
    state.runButton.disabled = false;
    state.confirmButton.disabled = false;
    state.cancelButton.disabled = false;
    syncRouteBusyState(state);
  }
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
    resultScopeLabelNode: document.getElementById("docsHtmlImportResultScopeLabel"),
    resultScopeNode: document.getElementById("docsHtmlImportResultScope"),
    resultDocIdLabelNode: document.getElementById("docsHtmlImportResultDocIdLabel"),
    resultDocIdNode: document.getElementById("docsHtmlImportResultDocId"),
    resultTitleLabelNode: document.getElementById("docsHtmlImportResultTitleLabel"),
    resultDocTitleNode: document.getElementById("docsHtmlImportResultDocTitle"),
    resultSourceLabelNode: document.getElementById("docsHtmlImportResultSourceLabel"),
    resultSourceNode: document.getElementById("docsHtmlImportResultSource"),
    resultViewerLabelNode: document.getElementById("docsHtmlImportResultViewerLabel"),
    resultViewerNode: document.getElementById("docsHtmlImportResultViewer"),
    resultBackupLabelNode: document.getElementById("docsHtmlImportResultBackupLabel"),
    resultBackupNode: document.getElementById("docsHtmlImportResultBackup"),
    resultMediaSourceRow: document.getElementById("docsHtmlImportResultMediaSourceRow"),
    resultMediaSourceLabelNode: document.getElementById("docsHtmlImportResultMediaSourceLabel"),
    resultMediaSourceNode: document.getElementById("docsHtmlImportResultMediaSource"),
    resultMediaKeyRow: document.getElementById("docsHtmlImportResultMediaKeyRow"),
    resultMediaKeyLabelNode: document.getElementById("docsHtmlImportResultMediaKeyLabel"),
    resultMediaKeyNode: document.getElementById("docsHtmlImportResultMediaKey"),
    resultMediaTokenRow: document.getElementById("docsHtmlImportResultMediaTokenRow"),
    resultMediaTokenLabelNode: document.getElementById("docsHtmlImportResultMediaTokenLabel"),
    resultMediaTokenNode: document.getElementById("docsHtmlImportResultMediaToken"),
    resultCountsNode: document.getElementById("docsHtmlImportResultCounts"),
    warningsWrap: document.getElementById("docsHtmlImportWarnings"),
    warningsHeading: document.getElementById("docsHtmlImportWarningsHeading"),
    warningsList: document.getElementById("docsHtmlImportWarningsList"),
    pendingOverwriteDocId: "",
    persistScope: options.persistScope !== false,
    routePath: normalizeText(options.routePath) || "/docs/",
    managementBaseUrl: normalizeText(options.managementBaseUrl) || "http://127.0.0.1:8789",
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
    state.resultScopeLabelNode,
    state.resultScopeNode,
    state.resultDocIdLabelNode,
    state.resultDocIdNode,
    state.resultTitleLabelNode,
    state.resultDocTitleNode,
    state.resultSourceLabelNode,
    state.resultSourceNode,
    state.resultViewerLabelNode,
    state.resultViewerNode,
    state.resultBackupLabelNode,
    state.resultBackupNode,
    state.resultMediaSourceRow,
    state.resultMediaSourceLabelNode,
    state.resultMediaSourceNode,
    state.resultMediaKeyRow,
    state.resultMediaKeyLabelNode,
    state.resultMediaKeyNode,
    state.resultMediaTokenRow,
    state.resultMediaTokenLabelNode,
    state.resultMediaTokenNode,
    state.resultCountsNode,
    state.warningsWrap,
    state.warningsHeading,
    state.warningsList
  ];
  if (requiredNodes.some((node) => !node)) return;

  try {
    state.config = await loadDocsViewerText(options.uiTextUrl || root.dataset.uiTextUrl || "/assets/docs-viewer/data/ui-text.json");
    state.docsScopeIds = await loadDocsViewerScopeOptions(options.docsViewerConfigUrl);
    state.managementBaseUrl = normalizeText(options.managementBaseUrl) || "http://127.0.0.1:8789";
    const serviceAvailable = await fetchManagementJson("/health", "GET", undefined, managementOptions(state))
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
    setText(
      state.includePromptMetaHintNode,
      configText(
        state.config,
        "docs_html_import.include_prompt_meta_hint",
        "When enabled, clearly identifiable prompt/meta sections are kept in simple fenced code blocks."
      )
    );
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
          "Docs management service unavailable. Start bin/dev-studio to run imports."
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

    state.fileSelect.innerHTML = files.map((file) => {
      const filename = normalizeText(file.filename);
      return `<option value="${escapeHtml(filename)}">${escapeHtml(filename)}</option>`;
    }).join("");
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
    state.resultDocIdNode.addEventListener("click", (event) => {
      const target = event.target && event.target.closest
        ? event.target
        : event.target && event.target.parentElement
          ? event.target.parentElement
          : null;
      const link = target && target.closest
        ? target.closest("[data-doc-source-link]")
        : null;
      if (!link || !state.resultDocIdNode.contains(link)) return;
      event.preventDefault();
      openResultSource(state, link).catch((error) => console.warn("docs_html_import: unexpected open source failure", error));
    });
    state.confirmButton.addEventListener("click", () => {
      runImport(state, {
        overwriteDocId: state.pendingOverwriteDocId,
        confirmOverwrite: true
      }).catch((error) => console.warn("docs_html_import: unexpected overwrite failure", error));
    });
    state.cancelButton.addEventListener("click", () => {
      resetWarning(state);
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
