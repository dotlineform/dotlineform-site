import {
  getDocumentPackageConfig,
  getReturnedDocumentPackages
} from "./document-package-client.js";
import {
  packageText
} from "./document-package-view.js";
import {
  escapeHtml,
  openDocsViewerManagementModal
} from "../management/docs-viewer-management-modal-shell.js";

function validDocumentCount(value) {
  return Number.isInteger(value) && value > 0;
}

export function reviewableDocumentPackages(payload) {
  const files = Array.isArray(payload && payload.files) ? payload.files : [];
  return files.map((file) => ({
    filename: packageText(file && file.filename),
    documentCount: file && file.document_count,
    supportsReturnImport: file && file.supports_return_import === true
  })).filter((file) => (
    file.filename
    && file.supportsReturnImport
    && validDocumentCount(file.documentCount)
  )).map((file) => ({
    filename: file.filename,
    documentCount: file.documentCount
  }));
}

export function documentPackageReviewTableHtml(files) {
  const rows = (Array.isArray(files) ? files : []).map((file, index) => [
    '<tr>',
    '  <td><label class="docsViewerReviewPackage__choice">',
    '    <input type="radio" name="docsViewerReviewPackage" value="' + escapeHtml(file.filename) + '"' + (index === 0 ? " checked" : "") + '>',
    '    <span>' + escapeHtml(file.filename) + '</span>',
    '  </label></td>',
    '  <td class="docsViewerReviewPackage__count">' + escapeHtml(String(file.documentCount)) + '</td>',
    '</tr>'
  ].join("")).join("");
  const body = rows || [
    '<tr>',
    '  <td class="docsViewerReviewPackage__empty" colspan="2">No reviewable packages are available for this scope.</td>',
    '</tr>'
  ].join("");
  return [
    '<div class="docsViewerReviewPackage">',
    '  <div class="docsViewerReviewPackage__tableWrap">',
    '    <table class="docsViewerReviewPackage__table" aria-label="Reviewable packages">',
    '      <thead><tr><th scope="col">File name</th><th scope="col">Documents</th></tr></thead>',
    '      <tbody>' + body + '</tbody>',
    '    </table>',
    '  </div>',
    '</div>'
  ].join("");
}

function showReviewPackageList(options) {
  return openDocsViewerManagementModal({
    root: options.root,
    restoreFocus: options.restoreFocus,
    title: "Review package",
    size: "compact",
    bodyHtml: documentPackageReviewTableHtml(options.files),
    focusSelector: options.files.length ? 'input[name="docsViewerReviewPackage"]' : "",
    actions: [{ role: "modal-primary", label: "Close" }],
    onSubmit: function (api) {
      const selected = api.host.querySelector('input[name="docsViewerReviewPackage"]:checked');
      return {
        confirmed: false,
        selectedFilename: packageText(selected && selected.value)
      };
    }
  });
}

function showReviewPackageError(options) {
  const message = packageText(options.message) || "Reviewable packages could not be loaded.";
  return openDocsViewerManagementModal({
    root: options.root,
    restoreFocus: options.restoreFocus,
    title: "Review packages unavailable",
    size: "compact",
    bodyHtml: '<p class="docsViewer__modalNote muted small">' + escapeHtml(message) + '</p>',
    actions: [{ role: "modal-primary", label: "Close" }]
  });
}

export async function openDocumentPackageReviewWorkflow(options = {}) {
  const root = options.root || document.body;
  const scope = packageText(options.scope).toLowerCase();
  const callbacks = options.callbacks || {};
  const client = {
    getConfig: getDocumentPackageConfig,
    getReturned: getReturnedDocumentPackages,
    ...(options.client || {})
  };
  const setBusy = (busy) => {
    if (typeof callbacks.setBusy === "function") callbacks.setBusy(Boolean(busy));
  };
  const setMessage = (message, isError) => {
    if (typeof callbacks.setMessage === "function") callbacks.setMessage(message, Boolean(isError));
  };

  if (typeof callbacks.hideManageActionsMenu === "function") callbacks.hideManageActionsMenu();
  if (!scope) {
    const error = new Error("A Docs Viewer scope is required.");
    setMessage(error.message, true);
    await showReviewPackageError({ root, restoreFocus: options.restoreFocus, message: error.message });
    return { confirmed: false, error };
  }

  let configPayload;
  let returnedPayload;
  try {
    setBusy(true);
    setMessage("Loading reviewable packages...", false);
    [configPayload, returnedPayload] = await Promise.all([
      client.getConfig(),
      client.getReturned(scope)
    ]);
    const workspace = configPayload && configPayload.workspace;
    if (!workspace || workspace.available !== true) {
      throw new Error(packageText(workspace && workspace.message) || "The document-package workspace is unavailable.");
    }
    const scopes = Array.isArray(configPayload.scopes) ? configPayload.scopes : [];
    if (!scopes.some((record) => packageText(record && record.scope).toLowerCase() === scope)) {
      throw new Error("The active Docs Viewer scope is unavailable for package review.");
    }
    if (packageText(returnedPayload && returnedPayload.scope).toLowerCase() !== scope) {
      throw new Error("The returned-package list did not match the active Docs Viewer scope.");
    }
  } catch (error) {
    setMessage(error && error.message ? error.message : "Reviewable packages could not be loaded.", true);
    await showReviewPackageError({
      root,
      restoreFocus: options.restoreFocus,
      message: error && error.message
    });
    return { confirmed: false, error };
  } finally {
    setBusy(false);
  }

  const files = reviewableDocumentPackages(returnedPayload);
  setMessage(files.length ? "" : "No reviewable packages are available for this scope.", false);
  const result = await showReviewPackageList({
    root,
    restoreFocus: options.restoreFocus,
    files
  });
  return {
    confirmed: false,
    files,
    selectedFilename: packageText(result && result.selectedFilename)
  };
}
