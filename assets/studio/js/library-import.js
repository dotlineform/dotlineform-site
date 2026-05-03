import { getStudioText, loadStudioConfig } from "./studio-config.js";
import {
  DOCS_MANAGEMENT_ENDPOINTS,
  getJson,
  postJson,
  probeDocsManagementHealth
} from "./studio-transport.js";
import {
  initializeStudioRouteState,
  setStudioRouteBusy,
  setStudioRouteReady
} from "./studio-route-state.js";

const SCOPE = "library";

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

function routeModeForState(state) {
  if (state.resultNode && !state.resultNode.hidden) return "result";
  return "selection";
}

function routeStateDetail(state) {
  return {
    route: "library-import",
    mode: routeModeForState(state),
    service: state.serviceAvailable ? "available" : "unavailable",
    recordLoaded: Boolean(state.files && state.files.length)
  };
}

function syncRouteBusyState(state) {
  setStudioRouteBusy(state.root, Boolean(state.isRunning), routeStateDetail(state));
}

function markRouteReady(state, ready) {
  setStudioRouteReady(state.root, ready, routeStateDetail(state));
}

function selectedFile(state) {
  const filename = normalizeText(state.fileSelect.value);
  return state.files.find((file) => normalizeText(file.filename) === filename) || null;
}

function formatBytes(value) {
  const bytes = Number(value || 0);
  if (!Number.isFinite(bytes) || bytes <= 0) return "0 B";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function resetResult(state) {
  state.resultNode.hidden = true;
  state.issuesWrap.hidden = true;
  state.issuesList.innerHTML = "";
  state.previewsWrap.hidden = true;
  state.previewList.innerHTML = "";
}

function renderFileMeta(state) {
  const file = selectedFile(state);
  if (!file) {
    state.fileMeta.hidden = true;
    return;
  }
  setText(state.filePathNode, file.path || file.filename || "");
  setText(state.fileFormatNode, file.format || "");
  setText(state.fileSizeNode, formatBytes(file.size_bytes));
  setText(state.fileModifiedNode, file.modified_utc || "");
  state.fileMeta.hidden = false;
}

function issueLabel(issue) {
  const code = normalizeText(issue && issue.code);
  const level = normalizeText(issue && issue.level);
  const docId = normalizeText(issue && issue.doc_id);
  const message = normalizeText(issue && issue.message);
  const prefix = [level, code].filter(Boolean).join(" ");
  const suffix = docId ? ` (${docId})` : "";
  return `${prefix ? `${prefix}: ` : ""}${message}${suffix}`;
}

function renderIssues(state, issues) {
  const items = Array.isArray(issues) ? issues.map(issueLabel).filter(Boolean) : [];
  if (!items.length) {
    state.issuesWrap.hidden = true;
    state.issuesList.innerHTML = "";
    return;
  }
  setText(state.issuesHeading, getStudioText(state.config, "library_import.issues_heading", "Issues"));
  state.issuesList.innerHTML = items.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  state.issuesWrap.hidden = false;
}

function renderPreviewFiles(state, previewFiles) {
  const items = Array.isArray(previewFiles) ? previewFiles : [];
  if (!items.length) {
    state.previewsWrap.hidden = true;
    state.previewList.innerHTML = "";
    return;
  }
  setText(state.previewsHeading, getStudioText(state.config, "library_import.previews_heading", "Preview files"));
  state.previewList.innerHTML = items.map((item) => {
    const path = normalizeText(item && item.path);
    const kind = normalizeText(item && item.kind);
    const docId = normalizeText(item && item.doc_id);
    const meta = [docId, kind].filter(Boolean).join(" · ");
    return `<li><span>${escapeHtml(path)}</span>${meta ? ` <small>${escapeHtml(meta)}</small>` : ""}</li>`;
  }).join("");
  state.previewsWrap.hidden = false;
}

function countsText(state, counts) {
  const safeCounts = counts && typeof counts === "object" ? counts : {};
  return getStudioText(
    state.config,
    "library_import.result_counts",
    "{records} records; {parsed} parsed; {malformed} malformed; {warnings} warnings; {errors} errors.",
    {
      records: Number(safeCounts.records || 0),
      parsed: Number(safeCounts.parsed_records || 0),
      malformed: Number(safeCounts.malformed_records || 0),
      warnings: Number(safeCounts.warnings || 0),
      errors: Number(safeCounts.errors || 0)
    }
  );
}

function renderResult(state, payload, failed = false) {
  const sourceMetadata = payload && typeof payload.source_metadata === "object" ? payload.source_metadata : {};
  setText(
    state.resultTitle,
    failed
      ? getStudioText(state.config, "library_import.result_title_failed", "Import preview failed")
      : getStudioText(state.config, "library_import.result_title", "Import preview")
  );
  setText(state.summaryNode, payload.summary_text || "");
  setText(state.resultTypeLabel, getStudioText(state.config, "library_import.result_type", "type"));
  setText(state.resultExportLabel, getStudioText(state.config, "library_import.result_export", "source export"));
  setText(state.resultGeneratedLabel, getStudioText(state.config, "library_import.result_generated", "generated"));
  setText(state.resultCountsLabel, getStudioText(state.config, "library_import.result_counts_label", "counts"));
  setText(state.resultTypeNode, payload.detected_import_type || "");
  setText(state.resultExportNode, payload.source_export_id || sourceMetadata.export_id || sourceMetadata.config_id || "");
  setText(state.resultGeneratedNode, payload.generated_at || sourceMetadata.generated_at || "");
  setText(state.resultCountsNode, countsText(state, payload.counts));
  renderIssues(state, payload.issues);
  renderPreviewFiles(state, payload.preview_files);
  state.resultNode.hidden = false;
}

function setControlsDisabled(state, disabled) {
  state.fileSelect.disabled = disabled || !state.files.length;
  state.previewButton.disabled = disabled || !state.serviceAvailable || !state.files.length;
}

async function loadImportFiles() {
  const url = `${DOCS_MANAGEMENT_ENDPOINTS.libraryImportFiles}?scope=${encodeURIComponent(SCOPE)}`;
  const payload = await getJson(url);
  return Array.isArray(payload.files) ? payload.files : [];
}

async function runPreview(state) {
  if (!state.serviceAvailable || state.isRunning) return;
  const file = selectedFile(state);
  if (!file) {
    setStatus(
      state.statusNode,
      "error",
      getStudioText(state.config, "library_import.file_required", "Select a staged data file first.")
    );
    return;
  }

  resetResult(state);
  state.isRunning = true;
  setControlsDisabled(state, true);
  syncRouteBusyState(state);
  setStatus(
    state.statusNode,
    "",
    getStudioText(state.config, "library_import.running_status", "Generating import previews...")
  );

  try {
    const payload = await postJson(DOCS_MANAGEMENT_ENDPOINTS.libraryImportPreview, {
      scope: SCOPE,
      staged_filename: file.filename
    });
    renderResult(state, payload, false);
    setStatus(
      state.statusNode,
      "success",
      payload.summary_text || getStudioText(state.config, "library_import.status_success", "Import previews generated.")
    );
  } catch (error) {
    const payload = error && error.payload ? error.payload : {};
    renderResult(state, payload, true);
    setStatus(
      state.statusNode,
      "error",
      normalizeText(error && error.message) || getStudioText(state.config, "library_import.status_failed", "Import preview failed.")
    );
  } finally {
    state.isRunning = false;
    setControlsDisabled(state, false);
    syncRouteBusyState(state);
  }
}

async function init() {
  const bootStatus = document.getElementById("libraryImportBootStatus");
  const root = document.getElementById("libraryImportRoot");
  if (!bootStatus || !root) return;
  initializeStudioRouteState(root, { route: "library-import", mode: "selection" });

  const state = {
    bootStatus,
    root,
    introNode: document.getElementById("libraryImportIntro"),
    fileLabelNode: document.getElementById("libraryImportFileLabel"),
    fileSelect: document.getElementById("libraryImportFileSelect"),
    fileMeta: document.getElementById("libraryImportFileMeta"),
    filePathLabel: document.getElementById("libraryImportFilePathLabel"),
    filePathNode: document.getElementById("libraryImportFilePath"),
    fileFormatLabel: document.getElementById("libraryImportFileFormatLabel"),
    fileFormatNode: document.getElementById("libraryImportFileFormat"),
    fileSizeLabel: document.getElementById("libraryImportFileSizeLabel"),
    fileSizeNode: document.getElementById("libraryImportFileSize"),
    fileModifiedLabel: document.getElementById("libraryImportFileModifiedLabel"),
    fileModifiedNode: document.getElementById("libraryImportFileModified"),
    previewButton: document.getElementById("libraryImportPreview"),
    statusNode: document.getElementById("libraryImportStatus"),
    resultNode: document.getElementById("libraryImportResult"),
    resultTitle: document.getElementById("libraryImportResultTitle"),
    summaryNode: document.getElementById("libraryImportSummary"),
    resultTypeLabel: document.getElementById("libraryImportResultTypeLabel"),
    resultTypeNode: document.getElementById("libraryImportResultType"),
    resultExportLabel: document.getElementById("libraryImportResultExportLabel"),
    resultExportNode: document.getElementById("libraryImportResultExport"),
    resultGeneratedLabel: document.getElementById("libraryImportResultGeneratedLabel"),
    resultGeneratedNode: document.getElementById("libraryImportResultGenerated"),
    resultCountsLabel: document.getElementById("libraryImportResultCountsLabel"),
    resultCountsNode: document.getElementById("libraryImportResultCounts"),
    issuesWrap: document.getElementById("libraryImportIssues"),
    issuesHeading: document.getElementById("libraryImportIssuesHeading"),
    issuesList: document.getElementById("libraryImportIssuesList"),
    previewsWrap: document.getElementById("libraryImportPreviews"),
    previewsHeading: document.getElementById("libraryImportPreviewsHeading"),
    previewList: document.getElementById("libraryImportPreviewList"),
    config: null,
    files: [],
    serviceAvailable: false,
    isRunning: false
  };

  const requiredNodes = [
    state.introNode,
    state.fileLabelNode,
    state.fileSelect,
    state.fileMeta,
    state.filePathLabel,
    state.filePathNode,
    state.fileFormatLabel,
    state.fileFormatNode,
    state.fileSizeLabel,
    state.fileSizeNode,
    state.fileModifiedLabel,
    state.fileModifiedNode,
    state.previewButton,
    state.statusNode,
    state.resultNode,
    state.resultTitle,
    state.summaryNode,
    state.resultTypeLabel,
    state.resultTypeNode,
    state.resultExportLabel,
    state.resultExportNode,
    state.resultGeneratedLabel,
    state.resultGeneratedNode,
    state.resultCountsLabel,
    state.resultCountsNode,
    state.issuesWrap,
    state.issuesHeading,
    state.issuesList,
    state.previewsWrap,
    state.previewsHeading,
    state.previewList
  ];
  if (requiredNodes.some((node) => !node)) return;

  try {
    state.config = await loadStudioConfig();
    state.serviceAvailable = Boolean(await probeDocsManagementHealth());

    setText(
      state.introNode,
      getStudioText(
        state.config,
        "library_import.intro",
        "Select a staged Library data file and generate Markdown previews for review."
      )
    );
    setText(state.fileLabelNode, getStudioText(state.config, "library_import.file_label", "staged file"));
    setText(state.filePathLabel, getStudioText(state.config, "library_import.file_path", "path"));
    setText(state.fileFormatLabel, getStudioText(state.config, "library_import.file_format", "format"));
    setText(state.fileSizeLabel, getStudioText(state.config, "library_import.file_size", "size"));
    setText(state.fileModifiedLabel, getStudioText(state.config, "library_import.file_modified", "modified"));
    setText(state.previewButton, getStudioText(state.config, "library_import.preview_button", "Generate preview"));

    root.hidden = false;
    bootStatus.hidden = true;

    if (!state.serviceAvailable) {
      setControlsDisabled(state, true);
      setStatus(
        state.statusNode,
        "error",
        getStudioText(
          state.config,
          "library_import.service_unavailable",
          "Docs management service unavailable. Start bin/dev-studio to run Library imports."
        )
      );
      markRouteReady(state, true);
      return;
    }

    state.files = await loadImportFiles();
    if (!state.files.length) {
      setControlsDisabled(state, true);
      setStatus(
        state.statusNode,
        "warn",
        getStudioText(
          state.config,
          "library_import.no_files",
          "No staged Library data files found under var/docs/import-staging/library/."
        )
      );
      markRouteReady(state, true);
      return;
    }

    state.fileSelect.innerHTML = state.files.map((file) => {
      const filename = normalizeText(file.filename);
      return `<option value="${escapeHtml(filename)}">${escapeHtml(filename)}</option>`;
    }).join("");
    renderFileMeta(state);
    setControlsDisabled(state, false);
    setStatus(
      state.statusNode,
      "",
      getStudioText(
        state.config,
        "library_import.idle_status",
        "Select a staged data file and generate Markdown previews."
      )
    );
    markRouteReady(state, true);

    state.fileSelect.addEventListener("change", () => {
      resetResult(state);
      renderFileMeta(state);
      setStatus(
        state.statusNode,
        "",
        getStudioText(
          state.config,
          "library_import.idle_status",
          "Select a staged data file and generate Markdown previews."
        )
      );
      syncRouteBusyState(state);
    });
    state.previewButton.addEventListener("click", () => {
      runPreview(state).catch((error) => console.warn("library_import: unexpected preview failure", error));
    });
  } catch (error) {
    console.warn("library_import: init failed", error);
    root.hidden = false;
    bootStatus.hidden = true;
    state.serviceAvailable = false;
    setStatus(
      state.statusNode,
      "error",
      getStudioText(state.config || {}, "library_import.load_failed", "Failed to load Library import data.")
    );
    markRouteReady(state, true);
  } finally {
    state.isRunning = false;
    syncRouteBusyState(state);
  }
}

init();
