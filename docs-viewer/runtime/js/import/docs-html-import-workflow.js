import {
  fetchManagementJson
} from "../management/docs-viewer-management-client.js";
import {
  clearDocsHtmlImportResult,
  renderDocsHtmlImportInteractiveOverwriteWarning,
  renderDocsHtmlImportResult,
  renderDocsHtmlImportWarnings,
  resetDocsHtmlImportWarning
} from "./docs-html-import-render.js";
import {
  importText
} from "./docs-html-import-text.js";

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

export function buildDocsImportActivityContext({
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

export function docsHtmlImportManagementOptions({
  managementBaseUrl = ""
} = {}) {
  return {
    baseUrl: managementBaseUrl,
    fetch: (url, options) => window.fetch(url, options)
  };
}

export function docsHtmlImportSourceFormatForRecord(record) {
  return normalizeText(record && record.source_format).toLowerCase() || "html";
}

function resetImportView(state, statusMessage) {
  resetDocsHtmlImportWarning(state);
  clearDocsHtmlImportResult(state);
  setStatus(state.statusNode, "", statusMessage);
}

function awaitInteractiveHtmlConfirmation(state, payload) {
  renderDocsHtmlImportInteractiveOverwriteWarning(state, payload);
  renderDocsHtmlImportWarnings(state, payload.import_preview && payload.import_preview.warnings);
  setStatus(
    state.statusNode,
    "warn",
    payload.summary_text || importText("interactiveAssetCollisionHeading")
  );
  state.confirmButton.disabled = false;
  state.cancelButton.disabled = false;
  return new Promise((resolve) => {
    state.pendingInteractiveOverwriteResolver = (action) => {
      state.pendingInteractiveOverwriteResolver = null;
      resetDocsHtmlImportWarning(state);
      resolve(action);
    };
  });
}

async function requestImport(
  file,
  context,
  {
    confirmInteractiveHtmlOverwrite = false
  } = {}
) {
  const stagedFilename = normalizeText(file && file.filename);
  return fetchManagementJson("/docs/import-source", "POST", {
    scope: context.scope,
    staged_filename: stagedFilename,
    include_prompt_meta: docsHtmlImportSourceFormatForRecord(file) === "html" ? Boolean(context.includePromptMeta) : false,
    confirm_interactive_html_overwrite: confirmInteractiveHtmlOverwrite,
    preview_only: false,
    activity_context: buildDocsImportActivityContext({
      pageId: "docs-import",
      actionId: "import-docs-source",
      route: context.routePath || "/docs/",
      controlId: "docsHtmlImportRun",
      controlSelector: "#docsHtmlImportRun",
      recordIdField: "staged_filename",
      recordId: stagedFilename
    })
  }, docsHtmlImportManagementOptions(context));
}

async function importFileWithPrompts(state, file, context = {}) {
  let nextOptions = {};
  const total = Number(context.total || 1);
  while (true) {
    const stagedFilename = normalizeText(file && file.filename);
    if (total > 1) {
      setStatus(
        state.statusNode,
        "",
        importText("runningStatusAll", {
          index: Number(context.index || 0) + 1,
          total,
          filename: stagedFilename
        })
      );
    }
    const payload = await requestImport(file, {
      scope: context.scope,
      includePromptMeta: context.includePromptMeta,
      routePath: context.routePath,
      managementBaseUrl: context.managementBaseUrl
    }, nextOptions);

    if (payload.preview_only && payload.requires_interactive_html_confirmation) {
      const action = await awaitInteractiveHtmlConfirmation(state, payload);
      if (action !== "confirm") return { cancelled: true };
      nextOptions = {
        confirmInteractiveHtmlOverwrite: true
      };
      continue;
    }

    return { payload };
  }
}

export async function runDocsHtmlImportWorkflow(
  state,
  {
    files = [],
    scope = "",
    includePromptMeta = false,
    routePath = "/docs/",
    managementBaseUrl = "",
    onRunningChange = () => {},
    onTerminalResult = () => {}
  } = {}
) {
  const workflowContext = {
    scope: normalizeText(scope),
    includePromptMeta: Boolean(includePromptMeta),
    routePath: normalizeText(routePath) || "/docs/",
    managementBaseUrl: normalizeText(managementBaseUrl)
  };
  state.runButton.disabled = true;
  state.confirmButton.disabled = true;
  state.cancelButton.disabled = true;
  resetImportView(
    state,
    importText("runningStatus")
  );
  state.isRunning = true;
  onRunningChange(true);

  const results = [];
  try {
    for (let index = 0; index < files.length; index += 1) {
      const result = await importFileWithPrompts(state, files[index], {
        index,
        total: files.length,
        ...workflowContext
      });
      if (result.cancelled) {
        if (results.length) renderDocsHtmlImportResult(state, results);
        setStatus(
          state.statusNode,
          "",
          files.length > 1
            ? importText("importCancelledPartial", { count: results.length, total: files.length })
            : importText("overwriteCancelled")
        );
        return;
      }
      if (result.payload) results.push(result.payload);
    }

    renderDocsHtmlImportResult(state, results);
    setStatus(
      state.statusNode,
      "success",
      results.length > 1
        ? importText("importAllSuccess", { count: results.length })
        : normalizeText(results[0] && results[0].summary_text)
    );
    const displayedResult = results.slice().reverse().find((result) => normalizeText(result && result.doc_id)) || null;
    try {
      await onTerminalResult({
        scope: workflowContext.scope,
        docId: normalizeText(displayedResult && displayedResult.doc_id),
        results: results.slice()
      });
    } catch (error) {
      console.warn("docs_import_source: terminal result projection failed", error);
    }
  } catch (error) {
    console.warn("docs_import_source: import failed", error);
    if (results.length) renderDocsHtmlImportResult(state, results);
    setStatus(
      state.statusNode,
      "error",
      normalizeText(error && error.message) || importText("importFailed")
    );
  } finally {
    state.isRunning = false;
    state.runButton.disabled = false;
    state.confirmButton.disabled = false;
    state.cancelButton.disabled = false;
    state.pendingInteractiveOverwriteResolver = null;
    onRunningChange(false);
  }
}
