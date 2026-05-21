import {
  fetchManagementJson
} from "./docs-viewer-management-client.js";
import {
  openReplacementDocIdModal
} from "./docs-html-import-modals.js";
import {
  clearDocsHtmlImportResult,
  renderDocsHtmlImportOverwriteWarning,
  renderDocsHtmlImportResult,
  renderDocsHtmlImportWarnings,
  resetDocsHtmlImportWarning
} from "./docs-html-import-render.js";

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
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

function setStatus(node, state, message) {
  if (!node) return;
  node.textContent = normalizeText(message);
  if (state) {
    node.setAttribute("data-state", state);
  } else {
    node.removeAttribute("data-state");
  }
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

function collisionDocId(payload) {
  const collision = payload && payload.collision && typeof payload.collision === "object" ? payload.collision : {};
  return normalizeText(collision.doc_id);
}

export function docsHtmlImportManagementOptions(state) {
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

export function docsHtmlImportSourceFormatForRecord(record) {
  return normalizeText(record && record.source_format).toLowerCase() || "html";
}

function resetImportView(state, statusMessage) {
  resetDocsHtmlImportWarning(state);
  clearDocsHtmlImportResult(state);
  setStatus(state.statusNode, "", statusMessage);
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
    return { action: "cancel" };
  }
  if ((result.action === "replace" || result.action === "replaceAll") && result.overwriteDocId) {
    if (result.action === "replaceAll") {
      state.replaceAllOverwrites = true;
    }
    return {
      action: "replace",
      overwriteDocId: result.overwriteDocId,
      confirmOverwrite: true
    };
  }
  if (result.action === "rename" && result.replacementDocId) {
    return { action: "rename", replacementDocId: result.replacementDocId };
  }
  return { action: "cancel" };
}

function awaitOverwriteConfirmation(state, payload) {
  renderDocsHtmlImportOverwriteWarning(state, payload);
  renderDocsHtmlImportWarnings(state, payload.import_preview && payload.import_preview.warnings);
  setStatus(
    state.statusNode,
    "warn",
    payload.summary_text || configText(state.config, "docs_html_import.overwrite_required", "Overwrite required.")
  );
  state.confirmButton.disabled = false;
  state.cancelButton.disabled = false;
  return new Promise((resolve) => {
    state.pendingOverwriteResolver = (action) => {
      state.pendingOverwriteResolver = null;
      resetDocsHtmlImportWarning(state);
      resolve(action);
    };
  });
}

async function requestImport(
  state,
  file,
  {
    scope,
    includePromptMeta,
    overwriteDocId = "",
    confirmOverwrite = false,
    replacementDocId = ""
  } = {}
) {
  const stagedFilename = normalizeText(file && file.filename);
  const normalizedReplacementDocId = normalizeText(replacementDocId);
  return fetchManagementJson("/docs/import-source", "POST", {
    scope,
    staged_filename: stagedFilename,
    include_prompt_meta: docsHtmlImportSourceFormatForRecord(file) === "html" ? Boolean(includePromptMeta) : false,
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
  }, docsHtmlImportManagementOptions(state));
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
        configText(
          state.config,
          "docs_html_import.running_status_all",
          "Importing {index} of {total}: {filename}",
          {
            index: Number(context.index || 0) + 1,
            total,
            filename: stagedFilename
          }
        )
      );
    }
    const payload = await requestImport(state, file, {
      scope: context.scope,
      includePromptMeta: context.includePromptMeta,
      ...nextOptions
    });

    if (payload.preview_only && (payload.replacement_doc_id_required || payload.replacement_title_required)) {
      renderDocsHtmlImportWarnings(state, payload.import_preview && payload.import_preview.warnings);
      setStatus(
        state.statusNode,
        "warn",
        payload.summary_text || configText(state.config, "docs_html_import.replacement_doc_id_required", "Enter a doc_id first.")
      );
      if (state.replaceAllOverwrites) {
        const overwriteDocId = collisionDocId(payload);
        if (!overwriteDocId) {
          throw new Error(configText(state.config, "docs_html_import.overwrite_required", "Overwrite required."));
        }
        nextOptions = { overwriteDocId, confirmOverwrite: true };
        continue;
      }
      const choice = await handleReplacementDocIdModal(state, payload);
      if (!choice || choice.action === "cancel") return { cancelled: true };
      if (choice.action === "replace") {
        nextOptions = {
          overwriteDocId: choice.overwriteDocId,
          confirmOverwrite: true
        };
        continue;
      }
      if (choice.action === "rename") {
        nextOptions = { replacementDocId: choice.replacementDocId };
        continue;
      }
    }

    if (payload.preview_only && payload.requires_overwrite_confirmation) {
      if (state.replaceAllOverwrites) {
        nextOptions = {
          overwriteDocId: collisionDocId(payload),
          confirmOverwrite: true
        };
        continue;
      }
      const action = await awaitOverwriteConfirmation(state, payload);
      if (action !== "confirm") return { cancelled: true };
      nextOptions = {
        overwriteDocId: collisionDocId(payload),
        confirmOverwrite: true
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
    onRunningChange = () => {}
  } = {}
) {
  state.replaceAllOverwrites = false;
  state.runButton.disabled = true;
  state.confirmButton.disabled = true;
  state.cancelButton.disabled = true;
  resetImportView(
    state,
    configText(state.config, "docs_html_import.running_status", "Converting and validating staged source...")
  );
  state.isRunning = true;
  onRunningChange(true);

  const results = [];
  try {
    for (let index = 0; index < files.length; index += 1) {
      const result = await importFileWithPrompts(state, files[index], {
        index,
        total: files.length,
        scope,
        includePromptMeta
      });
      if (result.cancelled) {
        if (results.length) renderDocsHtmlImportResult(state, results);
        setStatus(
          state.statusNode,
          "",
          files.length > 1
            ? configText(
              state.config,
              "docs_html_import.import_cancelled_partial",
              "Import cancelled after {count} of {total} files.",
              { count: results.length, total: files.length }
            )
            : configText(state.config, "docs_html_import.filename_conflict_cancelled", "Import cancelled.")
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
        ? configText(state.config, "docs_html_import.import_all_success", "Imported {count} staged files.", { count: results.length })
        : normalizeText(results[0] && results[0].summary_text)
    );
  } catch (error) {
    console.warn("docs_html_import: import failed", error);
    if (results.length) renderDocsHtmlImportResult(state, results);
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
    state.pendingOverwriteResolver = null;
    onRunningChange(false);
  }
}
