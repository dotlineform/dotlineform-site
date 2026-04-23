import { getStudioText, loadStudioConfig } from "./studio-config.js";
import {
  DOCS_MANAGEMENT_ENDPOINTS,
  postJson,
  probeDocsManagementHealth
} from "./studio-transport.js";

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

function selectedScopeFromUrl() {
  try {
    const url = new URL(window.location.href);
    const scope = normalizeText(url.searchParams.get("scope")).toLowerCase();
    return scope === "studio" ? "studio" : "library";
  } catch (_error) {
    return "library";
  }
}

function persistSelectedScope(scope) {
  try {
    const url = new URL(window.location.href);
    url.searchParams.set("scope", scope);
    window.history.replaceState({}, "", url.toString());
  } catch (_error) {
    // Ignore URL sync failures in constrained runtimes.
  }
}

function viewerLinkHtml(config, href, fallbackLabel) {
  const label = getStudioText(config, "docs_html_import.result_open_viewer", fallbackLabel || "Open viewer");
  if (!normalizeText(href)) return "";
  return `<a href="${escapeHtml(href)}">${escapeHtml(label)}</a>`;
}

async function fetchImportFiles() {
  const response = await fetch(DOCS_MANAGEMENT_ENDPOINTS.importHtmlFiles, { cache: "no-store" });
  const payload = await response.json().catch(() => null);
  if (!response.ok || !payload || !payload.ok) {
    throw new Error(payload && payload.error ? payload.error : `HTTP ${response.status}`);
  }
  return Array.isArray(payload.files) ? payload.files : [];
}

function resetWarning(state) {
  state.pendingOverwriteDocId = "";
  state.warningNode.hidden = true;
  setText(state.collisionMetaNode, "");
  state.confirmButton.hidden = true;
  state.cancelButton.hidden = true;
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
    getStudioText(state.config, "docs_html_import.warnings_heading", "Warnings")
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
      ? getStudioText(state.config, "docs_html_import.result_operation_overwrite", "Overwrote existing doc")
      : getStudioText(state.config, "docs_html_import.result_operation_create", "Created new doc")
  );
  setText(state.resultScopeLabelNode, getStudioText(state.config, "docs_html_import.result_scope", "scope"));
  setText(state.resultDocIdLabelNode, getStudioText(state.config, "docs_html_import.result_doc_id", "doc_id"));
  setText(state.resultTitleLabelNode, getStudioText(state.config, "docs_html_import.result_title_label", "title"));
  setText(state.resultSourceLabelNode, getStudioText(state.config, "docs_html_import.result_source", "source"));
  setText(state.resultViewerLabelNode, getStudioText(state.config, "docs_html_import.result_viewer", "viewer"));
  setText(state.resultBackupLabelNode, getStudioText(state.config, "docs_html_import.result_backup", "backup"));
  setText(state.resultScopeNode, payload.scope);
  setText(state.resultDocIdNode, payload.doc_id);
  setText(state.resultDocTitleNode, payload.title || preview.title || "");
  setText(state.resultSourceNode, preview.source_html || payload.staged_filename || "");
  setHtml(
    state.resultViewerNode,
    payload.viewer_url ? viewerLinkHtml(state.config, payload.viewer_url, "Open viewer") : ""
  );
  setText(state.resultBackupNode, payload.backup_dir || "");

  const stats = preview.source_stats && typeof preview.source_stats === "object" ? preview.source_stats : {};
  setText(
    state.resultCountsNode,
    getStudioText(
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
  renderWarnings(state, preview.warnings);
  state.resultNode.hidden = false;
}

function renderOverwriteWarning(state, payload) {
  const collision = payload && payload.collision && typeof payload.collision === "object" ? payload.collision : {};
  const preview = payload && payload.import_preview && typeof payload.import_preview === "object"
    ? payload.import_preview
    : {};
  state.pendingOverwriteDocId = normalizeText(collision.doc_id);
  setText(
    state.collisionHeadingNode,
    getStudioText(state.config, "docs_html_import.collision_heading", "Overwrite warning")
  );
  setText(
    state.collisionBodyNode,
    getStudioText(
      state.config,
      "docs_html_import.collision_body",
      "This import matches an existing doc target. Confirm overwrite to replace the current source while keeping the same doc identity and filename."
    )
  );
  setText(
    state.collisionMetaNode,
    getStudioText(
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

async function runImport(state, { overwriteDocId = "", confirmOverwrite = false } = {}) {
  const stagedFilename = normalizeText(state.fileSelect.value);
  if (!stagedFilename) {
    setStatus(
      state.statusNode,
      "error",
      getStudioText(state.config, "docs_html_import.file_required", "Select a staged HTML file first.")
    );
    return;
  }

  const scope = normalizeText(state.scopeSelect.value).toLowerCase() === "studio" ? "studio" : "library";
  persistSelectedScope(scope);
  state.runButton.disabled = true;
  state.confirmButton.disabled = true;
  state.cancelButton.disabled = true;
  state.resultNode.hidden = true;
  resetWarning(state);
  setStatus(
    state.statusNode,
    "",
    getStudioText(state.config, "docs_html_import.running_status", "Converting and validating staged HTML…")
  );

  try {
    const payload = await postJson(DOCS_MANAGEMENT_ENDPOINTS.importHtml, {
      scope,
      staged_filename: stagedFilename,
      include_prompt_meta: Boolean(state.includePromptMeta.checked),
      overwrite_doc_id: overwriteDocId,
      confirm_overwrite: confirmOverwrite,
      preview_only: false
    });

    if (payload.preview_only && payload.requires_overwrite_confirmation) {
      renderOverwriteWarning(state, payload);
      renderWarnings(state, payload.import_preview && payload.import_preview.warnings);
      setStatus(
        state.statusNode,
        "warn",
        payload.summary_text || getStudioText(state.config, "docs_html_import.overwrite_required", "Overwrite required.")
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
      normalizeText(error && error.message) || getStudioText(state.config, "docs_html_import.import_failed", "Import failed.")
    );
  } finally {
    state.runButton.disabled = false;
    state.confirmButton.disabled = false;
    state.cancelButton.disabled = false;
  }
}

async function init() {
  const bootStatus = document.getElementById("docsHtmlImportBootStatus");
  const root = document.getElementById("docsHtmlImportRoot");
  if (!bootStatus || !root) return;

  const state = {
    bootStatus,
    root,
    introNode: document.getElementById("docsHtmlImportIntro"),
    fileLabelNode: document.getElementById("docsHtmlImportFileLabel"),
    fileSelect: document.getElementById("docsHtmlImportFileSelect"),
    scopeLabelNode: document.getElementById("docsHtmlImportScopeLabel"),
    scopeSelect: document.getElementById("docsHtmlImportScopeSelect"),
    includePromptMeta: document.getElementById("docsHtmlImportIncludePromptMeta"),
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
    resultCountsNode: document.getElementById("docsHtmlImportResultCounts"),
    warningsWrap: document.getElementById("docsHtmlImportWarnings"),
    warningsHeading: document.getElementById("docsHtmlImportWarningsHeading"),
    warningsList: document.getElementById("docsHtmlImportWarningsList"),
    pendingOverwriteDocId: "",
    config: null
  };

  const requiredNodes = [
    state.introNode,
    state.fileLabelNode,
    state.fileSelect,
    state.scopeLabelNode,
    state.scopeSelect,
    state.includePromptMeta,
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
    state.resultCountsNode,
    state.warningsWrap,
    state.warningsHeading,
    state.warningsList
  ];
  if (requiredNodes.some((node) => !node)) return;

  try {
    state.config = await loadStudioConfig();
    const serviceAvailable = await probeDocsManagementHealth();

    setText(
      state.introNode,
      getStudioText(
        state.config,
        "docs_html_import.intro",
        "Import a staged self-contained HTML file into the Studio or Library docs source as a best-attempt Markdown doc."
      )
    );
    setText(state.fileLabelNode, getStudioText(state.config, "docs_html_import.file_label", "staged file"));
    setText(state.scopeLabelNode, getStudioText(state.config, "docs_html_import.scope_label", "publish into"));
    setText(
      state.includePromptMetaLabelNode,
      getStudioText(
        state.config,
        "docs_html_import.include_prompt_meta_label",
        "Include obvious prompt/meta blocks"
      )
    );
    setText(
      state.includePromptMetaHintNode,
      getStudioText(
        state.config,
        "docs_html_import.include_prompt_meta_hint",
        "When enabled, clearly identifiable prompt/meta sections are kept in simple fenced code blocks."
      )
    );
    setText(state.runButton, getStudioText(state.config, "docs_html_import.import_button", "Import"));
    setText(
      state.confirmButton,
      getStudioText(state.config, "docs_html_import.confirm_overwrite_button", "Confirm overwrite")
    );
    setText(
      state.cancelButton,
      getStudioText(state.config, "docs_html_import.cancel_overwrite_button", "Cancel")
    );
    state.scopeSelect.innerHTML = `
      <option value="library">${escapeHtml(getStudioText(state.config, "docs_html_import.scope_option_library", "library"))}</option>
      <option value="studio">${escapeHtml(getStudioText(state.config, "docs_html_import.scope_option_studio", "studio"))}</option>
    `;
    state.scopeSelect.value = selectedScopeFromUrl();
    state.scopeSelect.addEventListener("change", () => persistSelectedScope(state.scopeSelect.value));
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
        getStudioText(
          state.config,
          "docs_html_import.service_unavailable",
          "Docs management service unavailable. Start bin/dev-studio to run imports."
        )
      );
      return;
    }

    const files = await fetchImportFiles();
    if (!files.length) {
      state.runButton.disabled = true;
      state.fileSelect.disabled = true;
      setStatus(
        state.statusNode,
        "warn",
        getStudioText(
          state.config,
          "docs_html_import.no_files",
          "No staged HTML files found under var/docs/import-staging/."
        )
      );
      return;
    }

    state.fileSelect.innerHTML = files.map((file) => {
      const filename = normalizeText(file.filename);
      return `<option value="${escapeHtml(filename)}">${escapeHtml(filename)}</option>`;
    }).join("");

    setStatus(
      state.statusNode,
      "",
      getStudioText(
        state.config,
        "docs_html_import.idle_status",
        "Select a staged HTML file and import it into Studio or Library docs."
      )
    );

    state.runButton.addEventListener("click", () => {
      runImport(state).catch((error) => console.warn("docs_html_import: unexpected import failure", error));
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
        getStudioText(state.config, "docs_html_import.overwrite_cancelled", "Overwrite cancelled.")
      );
    });
  } catch (error) {
    console.warn("docs_html_import: init failed", error);
    bootStatus.hidden = false;
    setStatus(
      bootStatus,
      "error",
      getStudioText(state.config || {}, "docs_html_import.load_files_failed", "Failed to load staged HTML files.")
    );
  }
}

init();
