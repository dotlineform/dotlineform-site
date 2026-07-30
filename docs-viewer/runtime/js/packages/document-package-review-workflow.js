import {
  getDocumentPackageConfig,
  getReturnedDocumentPackages,
  reviewReturnedDocumentPackage
} from "./document-package-client.js";
import {
  packageIssueMessage,
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
    supportsDocsReview: file && file.supports_docs_review === true,
    scopeLabel: packageText(file && file.scope_label),
    subScopeLabel: packageText(file && file.sub_scope_label)
  })).filter((file) => (
    file.filename
    && file.supportsDocsReview
    && validDocumentCount(file.documentCount)
  )).map((file) => ({
    filename: file.filename,
    documentCount: file.documentCount,
    collectionLabel: [file.scopeLabel, file.subScopeLabel].filter(Boolean).join(" / ")
  }));
}

export function documentPackageReviewTableHtml(files) {
  const rows = (Array.isArray(files) ? files : []).map((file, index) => [
    '<tr>',
    '  <td><label class="docsViewerReviewPackage__choice">',
    '    <input type="radio" name="docsViewerReviewPackage" value="' + escapeHtml(file.filename) + '"' + (index === 0 ? " checked" : "") + '>',
    '    <span>' + escapeHtml(file.filename) + '</span>',
    '  </label></td>',
    '  <td>' + escapeHtml(file.collectionLabel) + '</td>',
    '  <td class="docsViewerReviewPackage__count">' + escapeHtml(String(file.documentCount)) + '</td>',
    '</tr>'
  ].join("")).join("");
  const body = rows || [
    '<tr>',
    '  <td class="docsViewerReviewPackage__empty" colspan="3">No reviewable packages are available for this scope.</td>',
    '</tr>'
  ].join("");
  return [
    '<div class="docsViewerReviewPackage">',
    '  <div class="docsViewerReviewPackage__tableWrap">',
    '    <table class="docsViewerReviewPackage__table" aria-label="Reviewable packages">',
    '      <colgroup>',
    '        <col class="docsViewerReviewPackage__fileColumn">',
    '        <col class="docsViewerReviewPackage__collectionColumn">',
    '        <col class="docsViewerReviewPackage__documentsColumn">',
    '      </colgroup>',
    '      <thead><tr><th scope="col">File</th><th scope="col">Collection</th><th scope="col">Documents</th></tr></thead>',
    '      <tbody>' + body + '</tbody>',
    '    </table>',
    '  </div>',
    '</div>'
  ].join("");
}

export function documentPackageReviewResult(payload) {
  if (!payload || payload.ok !== true) {
    throw new Error("Docs Review package was not prepared.");
  }
  const packageId = packageText(payload && payload.review_package_id);
  if (!/^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(packageId)) {
    throw new Error("Docs Review package identity is invalid.");
  }
  const reviewUrl = `/docs-review/?package=${encodeURIComponent(packageId)}`;
  if (packageText(payload && payload.review_url) !== reviewUrl) {
    throw new Error("Docs Review package URL is invalid.");
  }
  const existing = payload && payload.review_existing === true;
  return {
    packageId,
    reviewUrl,
    existing,
    linkLabel: existing ? "Open existing review" : "Open in Docs Review"
  };
}

function closeReviewWindow(reviewWindow) {
  if (!reviewWindow || typeof reviewWindow.close !== "function") return;
  try {
    reviewWindow.close();
  } catch (_error) {
    // A failed preparation must not leave an owned blank tab behind.
  }
}

export async function openReturnedDocumentPackageInDocsReview(options = {}) {
  const scope = packageText(options.scope).toLowerCase();
  const stagedFilename = packageText(options.stagedFilename);
  if (!scope || !stagedFilename) {
    throw new Error("An exact returned-package identity is required for Docs Review.");
  }
  const review = typeof options.review === "function"
    ? options.review
    : reviewReturnedDocumentPackage;
  const openWindow = typeof options.openWindow === "function"
    ? options.openWindow
    : (url, target) => window.open(url, target);
  const reviewWindow = openWindow("about:blank", "_blank");
  if (!reviewWindow) {
    throw new Error("The Docs Review tab was blocked. Allow popups and retry.");
  }
  try {
    reviewWindow.opener = null;
    const payload = await review({
      scope,
      staged_filename: stagedFilename,
      dry_run: false
    });
    const result = documentPackageReviewResult(payload);
    if (reviewWindow.closed) {
      throw new Error("The Docs Review tab was closed before preparation completed.");
    }
    if (
      reviewWindow.location
      && typeof reviewWindow.location.replace === "function"
    ) {
      reviewWindow.location.replace(result.reviewUrl);
    } else {
      reviewWindow.location = result.reviewUrl;
    }
    return {
      ...result,
      payload
    };
  } catch (error) {
    closeReviewWindow(reviewWindow);
    throw error;
  }
}

function showReviewPackageList(options) {
  return openDocsViewerManagementModal({
    root: options.root,
    restoreFocus: options.restoreFocus,
    title: "Review package",
    size: "review-package",
    bodyHtml: documentPackageReviewTableHtml(options.files),
    focusSelector: options.files.length ? 'input[name="docsViewerReviewPackage"]' : "",
    actions: [
      { role: "modal-primary", label: "Review package", disabled: !options.files.length },
      { role: "modal-cancel", label: "Cancel" }
    ],
    onSubmit: function (api) {
      const selected = api.host.querySelector('input[name="docsViewerReviewPackage"]:checked');
      const selectedFilename = packageText(selected && selected.value);
      if (!selectedFilename) {
        api.setStatus("Choose one package to review.");
        return false;
      }
      return {
        confirmed: true,
        selectedFilename
      };
    }
  });
}

function showReviewPackageError(options) {
  const message = packageText(options.message) || "Reviewable packages could not be loaded.";
  const issues = (Array.isArray(options.issues) ? options.issues : [])
    .map(packageIssueMessage)
    .filter(Boolean);
  return openDocsViewerManagementModal({
    root: options.root,
    restoreFocus: options.restoreFocus,
    title: options.title || "Review packages unavailable",
    size: "compact",
    bodyHtml: [
      '<p class="docsViewer__modalNote muted small">' + escapeHtml(message) + '</p>',
      issues.length ? '<ul class="docsViewerReviewPackage__issues">' + issues.map((issue) => (
        '<li>' + escapeHtml(issue) + '</li>'
      )).join("") + '</ul>' : ""
    ].join(""),
    actions: [{ role: "modal-primary", label: "Close" }]
  });
}

function showReviewPackageResult(options) {
  const result = documentPackageReviewResult(options.payload);
  const summary = packageText(options.payload && options.payload.summary_text);
  return openDocsViewerManagementModal({
    root: options.root,
    restoreFocus: options.restoreFocus,
    title: result.existing ? "Review package already prepared" : "Review package prepared",
    size: "compact",
    bodyHtml: [
      summary ? '<p class="docsViewer__modalNote muted small">' + escapeHtml(summary) + '</p>' : "",
      '<p class="docsViewerReviewPackage__resultLink">',
      '  <a href="' + escapeHtml(result.reviewUrl) + '" target="_blank" rel="noopener noreferrer">' + escapeHtml(result.linkLabel) + '</a>',
      '</p>'
    ].join(""),
    focusSelector: ".docsViewerReviewPackage__resultLink a",
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
    review: reviewReturnedDocumentPackage,
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
  const selectedFilename = packageText(result && result.selectedFilename);
  if (!result || !result.confirmed || !selectedFilename) {
    return { confirmed: false, files, selectedFilename };
  }

  let reviewPayload;
  try {
    setBusy(true);
    setMessage("Preparing the complete package for Docs Review...", false);
    reviewPayload = await client.review({
      scope,
      staged_filename: selectedFilename,
      dry_run: false
    });
    documentPackageReviewResult(reviewPayload);
    setMessage(packageText(reviewPayload.summary_text) || "Review package prepared.", false);
  } catch (error) {
    const payload = error && error.payload && typeof error.payload === "object"
      ? error.payload
      : {};
    const message = packageText(error && error.message) || "Review package could not be prepared.";
    setMessage(message, true);
    await showReviewPackageError({
      root,
      restoreFocus: options.restoreFocus,
      title: "Review package was not prepared",
      message,
      issues: payload.issues
    });
    return { confirmed: true, ok: false, error, files, selectedFilename, payload };
  } finally {
    setBusy(false);
  }

  await showReviewPackageResult({
    root,
    restoreFocus: options.restoreFocus,
    payload: reviewPayload
  });
  return {
    confirmed: true,
    ok: true,
    files,
    selectedFilename,
    payload: reviewPayload
  };
}
