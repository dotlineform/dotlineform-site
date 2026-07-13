import {
  applyScopeCreate,
  applyScopeDelete,
  applyScopeRename,
  applySubScopeCreate,
  applySubScopeDelete,
  previewScopeCreate,
  previewScopeDelete,
  previewScopeRename,
  previewSubScopeCreate,
  previewSubScopeDelete
} from "./docs-viewer-management-client.js";
import {
  openDocsViewerManagementModal
} from "./docs-viewer-management-modals.js";
import {
  scopeCreateSupported,
  scopeDeleteSupported,
  scopeLifecycleDeleteTargets,
  scopeLifecycleRenameTargets,
  scopeRenameSupported,
  subScopeCreateSupported,
  subScopeDeleteSupported,
  subScopeLifecycleDeleteTargets
} from "./docs-viewer-management-capabilities.js";
import {
  escapeHtml
} from "../shared/docs-viewer-render.js";

export {
  scopeCreateSupported,
  scopeDeleteSupported,
  scopeLifecycleDeleteTargets,
  scopeLifecycleRenameTargets,
  scopeRenameSupported,
  subScopeCreateSupported,
  subScopeDeleteSupported,
  subScopeLifecycleDeleteTargets
};

var DEFAULT_PUBLISHING_MODES = [
  "local_external",
  "local_committed"
];
var PUBLISHING_MODE_ORDER = [
  "local_external",
  "local_committed",
  "public_readonly"
];

var SCOPE_LIFECYCLE_TEXT = {
  cancelButton: "Cancel",
  scopeCreateTitle: "New scope",
  scopeIdLabel: "scope id",
  scopeTitleLabel: "title",
  scopePublishingModeLabel: "scope type",
  scopePublicReadonlyMode: "public",
  scopeLocalCommittedMode: "local tracked",
  scopeLocalExternalMode: "external local",
  scopeSourceRootLabel: "source root",
  scopeDefaultDocIdLabel: "default doc id",
  scopePublicRoutePathLabel: "public route path",
  scopePreviewButton: "Preview",
  scopeSaveButton: "Save",
  scopeRenameButton: "Rename",
  scopeDeleteButton: "Delete",
  scopeResultOkButton: "OK",
  scopeCreateRequiredMessage: "Enter the required scope fields.",
  scopeCreateRouteRequiredMessage: "Enter a public route path for public scopes.",
  scopeCreatePreviewing: "Previewing new scope...",
  scopeCreatePreviewTitle: "Preview new scope",
  scopeCreateSaving: "Saving new scope...",
  scopeCreateFailed: "New scope failed.",
  scopeCreateResultTitle: "Scope created",
  scopeRenameTitle: "Rename scope",
  scopeRenameIntro: "Rename a user-created external-local scope.",
  scopeRenameTargetLabel: "scope",
  scopeRenameNewIdLabel: "new scope id",
  scopeRenameWarning: "Links containing the old scope id are not rewritten.",
  scopeRenameRequiredMessage: "Select a scope and enter its new id.",
  scopeRenameSameIdMessage: "Enter a different scope id.",
  scopeRenameNoTargets: "No user-created external-local scopes are eligible for renaming.",
  scopeRenameSaving: "Renaming scope...",
  scopeRenameFailed: "Rename scope failed.",
  scopeRenameBlocked: "Rename scope is blocked.",
  scopeDeleteTitle: "Delete scope",
  scopeDeleteIntro: "Select the user-created scope to delete.",
  scopeDeleteTargetLabel: "scope",
  scopeDeleteRequiredMessage: "Select a scope to delete.",
  scopeDeleteNoTargets: "No user-created scopes are eligible for deletion.",
  scopeDeletePreviewing: "Previewing scope deletion...",
  scopeDeletePreviewTitle: "Preview delete scope",
  scopeDeleteDeleting: "Deleting scope...",
  scopeDeleteFailed: "Delete scope failed.",
  scopeDeleteBlocked: "Delete scope is blocked.",
  scopeDeleteBlockedTitle: "Delete blocked",
  scopeDeleteResultTitle: "Scope deleted",
  subScopeCreateTitle: "New sub-scope",
  subScopeIdLabel: "sub-scope id",
  subScopeTitleLabel: "title",
  subScopeCreateRequiredMessage: "Enter the required sub-scope fields.",
  subScopeCreatePreviewing: "Previewing new sub-scope...",
  subScopeCreatePreviewTitle: "Preview new sub-scope",
  subScopeCreateSaving: "Saving new sub-scope...",
  subScopeCreateFailed: "New sub-scope failed.",
  subScopeCreateResultTitle: "Sub-scope created",
  subScopeDeleteTitle: "Delete sub-scope",
  subScopeDeleteIntro: "Select the sub-scope to delete from the active parent scope.",
  subScopeDeleteTargetLabel: "sub-scope",
  subScopeDeleteRequiredMessage: "Select a sub-scope to delete.",
  subScopeDeleteNoParent: "Select a parent scope before deleting a sub-scope.",
  subScopeDeleteNoTargets: "No sub-scopes are configured for the active scope.",
  subScopeDeletePreviewing: "Previewing sub-scope deletion...",
  subScopeDeletePreviewTitle: "Preview delete sub-scope",
  subScopeDeleteDeleting: "Deleting sub-scope...",
  subScopeDeleteFailed: "Delete sub-scope failed.",
  subScopeDeleteBlocked: "Delete sub-scope is blocked.",
  subScopeDeleteResultTitle: "Sub-scope deleted"
};

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function publishingModes(capabilities) {
  var lifecycle = capabilities && capabilities.scope_lifecycle && typeof capabilities.scope_lifecycle === "object"
    ? capabilities.scope_lifecycle
    : null;
  var rawModes = lifecycle && Array.isArray(lifecycle.publishing_modes)
    ? lifecycle.publishing_modes
    : DEFAULT_PUBLISHING_MODES;
  var seen = new Set();
  var modes = rawModes.map(normalizeText).filter(function (mode) {
    if (!mode || seen.has(mode)) return false;
    seen.add(mode);
    return true;
  });
  var ordered = PUBLISHING_MODE_ORDER.filter(function (mode) {
    return modes.includes(mode);
  });
  return ordered.length ? ordered : DEFAULT_PUBLISHING_MODES.slice();
}

function modeLabel(mode) {
  var labels = {
    public_readonly: SCOPE_LIFECYCLE_TEXT.scopePublicReadonlyMode,
    local_committed: SCOPE_LIFECYCLE_TEXT.scopeLocalCommittedMode,
    local_external: SCOPE_LIFECYCLE_TEXT.scopeLocalExternalMode
  };
  return labels[mode] || mode;
}

function slugFromScopeInput(value) {
  return normalizeText(value)
    .toLowerCase()
    .replace(/[^a-z0-9_-]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function humanTitleFromSlug(value) {
  return slugFromScopeInput(value).split(/[-_]+/g).filter(Boolean).map(function (part) {
    return part.charAt(0).toUpperCase() + part.slice(1);
  }).join(" ");
}

function renderModeOptions(modes) {
  return modes.map(function (mode) {
    return '<option value="' + escapeHtml(mode) + '">' + escapeHtml(modeLabel(mode)) + '</option>';
  }).join("");
}

function renderCreateFormHtml(capabilities) {
  var modes = publishingModes(capabilities);
  return (
    '<div class="docsViewerScopeLifecycle">' +
      '<label class="docsViewer__field">' +
        '<span class="docsViewer__fieldLabel">' + escapeHtml(SCOPE_LIFECYCLE_TEXT.scopeIdLabel) + '</span>' +
        '<input class="docsViewer__fieldInput" data-role="scope-id" type="text" autocomplete="off" spellcheck="false" required>' +
      '</label>' +
      '<label class="docsViewer__field">' +
        '<span class="docsViewer__fieldLabel">' + escapeHtml(SCOPE_LIFECYCLE_TEXT.scopeTitleLabel) + '</span>' +
        '<input class="docsViewer__fieldInput" data-role="scope-title" type="text" autocomplete="off" spellcheck="false" required>' +
      '</label>' +
      '<label class="docsViewer__field">' +
        '<span class="docsViewer__fieldLabel">' + escapeHtml(SCOPE_LIFECYCLE_TEXT.scopePublishingModeLabel) + '</span>' +
        '<select class="docsViewer__fieldInput" data-role="scope-publishing-mode">' + renderModeOptions(modes) + '</select>' +
      '</label>' +
      '<label class="docsViewer__field" data-role="scope-source-root-field">' +
        '<span class="docsViewer__fieldLabel">' + escapeHtml(SCOPE_LIFECYCLE_TEXT.scopeSourceRootLabel) + '</span>' +
        '<input class="docsViewer__fieldInput" data-role="scope-source-root" type="text" autocomplete="off" spellcheck="false" required>' +
      '</label>' +
      '<label class="docsViewer__field">' +
        '<span class="docsViewer__fieldLabel">' + escapeHtml(SCOPE_LIFECYCLE_TEXT.scopeDefaultDocIdLabel) + '</span>' +
        '<input class="docsViewer__fieldInput" data-role="scope-default-doc-id" type="text" autocomplete="off" spellcheck="false" required>' +
      '</label>' +
      '<label class="docsViewer__field" data-role="scope-route-field">' +
        '<span class="docsViewer__fieldLabel">' + escapeHtml(SCOPE_LIFECYCLE_TEXT.scopePublicRoutePathLabel) + '</span>' +
        '<input class="docsViewer__fieldInput" data-role="scope-public-route-path" type="text" autocomplete="off" spellcheck="false">' +
      '</label>' +
    '</div>'
  );
}

function wireCreateForm(api) {
  var host = api.host;
  var scopeInput = host.querySelector('[data-role="scope-id"]');
  var titleInput = host.querySelector('[data-role="scope-title"]');
  var modeInput = host.querySelector('[data-role="scope-publishing-mode"]');
  var sourceField = host.querySelector('[data-role="scope-source-root-field"]');
  var sourceInput = host.querySelector('[data-role="scope-source-root"]');
  var defaultDocInput = host.querySelector('[data-role="scope-default-doc-id"]');
  var routeField = host.querySelector('[data-role="scope-route-field"]');
  var routeInput = host.querySelector('[data-role="scope-public-route-path"]');

  function expectedTitle() {
    return slugFromScopeInput(scopeInput && scopeInput.value);
  }

  function expectedSourceRoot() {
    var slug = slugFromScopeInput(scopeInput && scopeInput.value);
    return slug ? "docs-viewer/source/" + slug : "";
  }

  function expectedDefaultDocId() {
    return slugFromScopeInput(scopeInput && scopeInput.value);
  }

  function expectedRoutePath() {
    var slug = slugFromScopeInput(scopeInput && scopeInput.value);
    return slug ? "/" + slug + "/" : "";
  }

  function applyScopeDefaults() {
    if (titleInput && (!titleInput.value || titleInput.dataset.auto === "true")) {
      titleInput.value = expectedTitle();
      titleInput.dataset.auto = "true";
    }
    if (sourceInput && (!sourceInput.value || sourceInput.dataset.auto === "true")) {
      sourceInput.value = expectedSourceRoot();
      sourceInput.dataset.auto = "true";
    }
    if (defaultDocInput && (!defaultDocInput.value || defaultDocInput.dataset.auto === "true")) {
      defaultDocInput.value = expectedDefaultDocId();
      defaultDocInput.dataset.auto = "true";
    }
    if (routeInput && (!routeInput.value || routeInput.dataset.auto === "true")) {
      routeInput.value = expectedRoutePath();
      routeInput.dataset.auto = "true";
    }
  }

  function syncMode() {
    var mode = normalizeText(modeInput && modeInput.value) || "local_external";
    if (routeField) routeField.hidden = mode !== "public_readonly";
    if (routeInput) routeInput.required = mode === "public_readonly";
    if (sourceField) sourceField.hidden = mode === "local_external";
    if (sourceInput) {
      sourceInput.readOnly = mode === "local_external";
      sourceInput.required = mode !== "local_external";
      if (mode === "local_external") {
        sourceInput.value = "";
      } else if (!sourceInput.value || sourceInput.dataset.auto === "true") {
        sourceInput.value = expectedSourceRoot();
        sourceInput.dataset.auto = "true";
      }
    }
  }

  if (scopeInput) {
    scopeInput.addEventListener("input", applyScopeDefaults);
  }
  [titleInput, sourceInput, defaultDocInput, routeInput].forEach(function (input) {
    if (!input) return;
    input.dataset.auto = "true";
    input.addEventListener("input", function () {
      input.dataset.auto = "false";
    });
  });
  if (modeInput) {
    modeInput.addEventListener("change", syncMode);
  }
  syncMode();
}

function collectCreatePayload(api) {
  var host = api.host;
  var scopeId = normalizeText(host.querySelector('[data-role="scope-id"]')?.value).toLowerCase();
  var title = normalizeText(host.querySelector('[data-role="scope-title"]')?.value);
  var publishingMode = normalizeText(host.querySelector('[data-role="scope-publishing-mode"]')?.value) || "local_external";
  var sourceRoot = normalizeText(host.querySelector('[data-role="scope-source-root"]')?.value);
  var defaultDocId = normalizeText(host.querySelector('[data-role="scope-default-doc-id"]')?.value);
  var publicRoutePath = normalizeText(host.querySelector('[data-role="scope-public-route-path"]')?.value);

  if (!scopeId || !title || !defaultDocId || (publishingMode !== "local_external" && !sourceRoot)) {
    api.setStatus(SCOPE_LIFECYCLE_TEXT.scopeCreateRequiredMessage);
    return null;
  }
  if (publishingMode === "public_readonly" && !publicRoutePath) {
    api.setStatus(SCOPE_LIFECYCLE_TEXT.scopeCreateRouteRequiredMessage);
    return null;
  }

  return {
    scope_id: scopeId,
    title: title,
    source_root: publishingMode === "local_external" ? "" : sourceRoot,
    default_doc_id: defaultDocId,
    publishing_mode: publishingMode,
    public_route_path: publishingMode === "public_readonly" ? publicRoutePath : ""
  };
}

function renderCreateSubScopeFormHtml() {
  return (
    '<div class="docsViewerScopeLifecycle">' +
      '<label class="docsViewer__field">' +
        '<span class="docsViewer__fieldLabel">' + escapeHtml(SCOPE_LIFECYCLE_TEXT.subScopeIdLabel) + '</span>' +
        '<input class="docsViewer__fieldInput" data-role="sub-scope-id" type="text" autocomplete="off" spellcheck="false" required>' +
      '</label>' +
      '<label class="docsViewer__field">' +
        '<span class="docsViewer__fieldLabel">' + escapeHtml(SCOPE_LIFECYCLE_TEXT.subScopeTitleLabel) + '</span>' +
        '<input class="docsViewer__fieldInput" data-role="sub-scope-title" type="text" autocomplete="off" spellcheck="false" required>' +
      '</label>' +
    '</div>'
  );
}

function wireCreateSubScopeForm(api) {
  var host = api.host;
  var subScopeInput = host.querySelector('[data-role="sub-scope-id"]');
  var titleInput = host.querySelector('[data-role="sub-scope-title"]');

  function applyDefaults() {
    if (titleInput && (!titleInput.value || titleInput.dataset.auto === "true")) {
      titleInput.value = humanTitleFromSlug(subScopeInput && subScopeInput.value);
      titleInput.dataset.auto = "true";
    }
  }

  if (subScopeInput) {
    subScopeInput.addEventListener("input", applyDefaults);
  }
  if (titleInput) {
    titleInput.dataset.auto = "true";
    titleInput.addEventListener("input", function () {
      titleInput.dataset.auto = "false";
    });
  }
}

function collectCreateSubScopePayload(api, parentScope) {
  var host = api.host;
  var subScope = slugFromScopeInput(host.querySelector('[data-role="sub-scope-id"]')?.value);
  var title = normalizeText(host.querySelector('[data-role="sub-scope-title"]')?.value);
  if (!parentScope || !subScope || !title) {
    api.setStatus(SCOPE_LIFECYCLE_TEXT.subScopeCreateRequiredMessage);
    return null;
  }
  return {
    parent_scope: parentScope,
    sub_scope: subScope,
    title: title
  };
}

function fileLabel(record) {
  var kind = normalizeText(record && record.kind);
  var path = normalizeText(record && record.path);
  return [kind, path].filter(Boolean).join(": ");
}

function renderList(items, emptyText) {
  var records = Array.isArray(items) ? items.filter(Boolean) : [];
  if (!records.length) {
    return '<p class="docsViewerScopeLifecycle__empty muted small">' + escapeHtml(emptyText || "None") + '</p>';
  }
  return '<ul class="docsViewerScopeLifecycle__list">' + records.map(function (record) {
    var text = typeof record === "string" ? record : fileLabel(record);
    return '<li>' + escapeHtml(text) + '</li>';
  }).join("") + '</ul>';
}

function renderCommands(commands) {
  var records = Array.isArray(commands) ? commands : [];
  if (!records.length) return "";
  return (
    '<section class="docsViewerScopeLifecycle__section">' +
      '<h3>' + escapeHtml("Build commands") + '</h3>' +
      '<ul class="docsViewerScopeLifecycle__list docsViewerScopeLifecycle__list--plain">' + records.map(function (record) {
        var command = normalizeText(record && record.command);
        var status = normalizeText(record && record.status);
        return '<li>' + escapeHtml([command, status].filter(Boolean).join(" - ")) + '</li>';
      }).join("") + '</ul>' +
    '</section>'
  );
}

function renderDetailRows(rows, emptyText) {
  var entries = Array.isArray(rows) ? rows.filter(function (entry) {
    return Array.isArray(entry) && normalizeText(entry[0]) && normalizeText(entry[1]);
  }) : [];
  if (!entries.length) {
    return '<p class="docsViewerScopeLifecycle__empty muted small">' + escapeHtml(emptyText || "None") + '</p>';
  }
  return '<dl class="docsViewerScopeLifecycle__detailGrid">' + entries.map(function (entry) {
    return '<dt>' + escapeHtml(entry[0]) + ':</dt><dd>' + escapeHtml(entry[1]) + '</dd>';
  }).join("") + '</dl>';
}

function hasDetailRows(rows) {
  return Array.isArray(rows) && rows.some(function (entry) {
    return Array.isArray(entry) && normalizeText(entry[0]) && normalizeText(entry[1]);
  });
}

function lifecyclePathRecords(payload) {
  return [
    payload && payload.created_files,
    payload && payload.publish_files,
    payload && payload.delete_files,
    payload && payload.deleted_files,
    payload && payload.missing_files
  ].flatMap(function (records) {
    return Array.isArray(records) ? records : [];
  });
}

function lifecycleRecord(payload, kinds) {
  var allowedKinds = new Set(Array.isArray(kinds) ? kinds : [kinds]);
  return lifecyclePathRecords(payload).find(function (record) {
    return allowedKinds.has(normalizeText(record && record.kind));
  }) || null;
}

function externalLifecycleRoot(payload) {
  var contract = payload && payload.storage_contract && typeof payload.storage_contract === "object"
    ? payload.storage_contract
    : {};
  var sourceRoot = normalizeText(contract.source_root);
  var sourceRecord = lifecycleRecord(payload, ["source_root", "sub_scope_source_root"]);
  var sourcePath = normalizeText(sourceRecord && sourceRecord.path);
  if (normalizeText(sourceRecord && sourceRecord.location) !== "external" || !sourcePath) return "";
  var sourceAnchor = sourceRoot.indexOf("/source/");
  var relativeSource = sourceAnchor >= 0
    ? sourceRoot.slice(sourceAnchor + 1)
    : [
        "source",
        normalizeText(payload && payload.parent_scope) || normalizeText(payload && payload.scope_id),
        normalizeText(payload && payload.sub_scope)
      ].filter(Boolean).join("/");
  var suffix = "/" + relativeSource;
  return sourcePath.endsWith(suffix) ? sourcePath.slice(0, -suffix.length) : "";
}

function lifecycleRelativePath(value, root) {
  var path = normalizeText(value);
  if (!path) return "";
  if (root && path.startsWith(root + "/")) return path.slice(root.length + 1);
  if (root) {
    var anchors = ["/source/", "/generated/"];
    var anchor = anchors.find(function (candidate) {
      return path.includes(candidate);
    });
    if (anchor) return path.slice(path.indexOf(anchor) + 1);
  }
  return path;
}

function lifecycleFileRows(payload, records) {
  var labels = {
    default_source_doc: "default doc",
    generated_docs_index_tree: "index",
    generated_docs_recently_added: "recently added",
    generated_search_index: "search index",
    published_docs_index_tree: "index",
    published_docs_recently_added: "recently added",
    published_search_index: "search index",
    route_file: "public route",
    scope_config: "scope config",
    scope_manifest: "scope manifest",
    route_config: "route config",
    public_route_config: "public route config"
  };
  var omittedKinds = new Set([
    "source_root",
    "generated_docs_root",
    "generated_docs_payload_root",
    "published_docs_root",
    "published_docs_payload_root",
    "sub_scope_source_root",
    "sub_scope_generated_docs_root",
    "sub_scope_generated_docs_payload_root",
    "sub_scope_published_docs_root",
    "sub_scope_published_docs_payload_root"
  ]);
  var root = externalLifecycleRoot(payload);
  return (Array.isArray(records) ? records : []).filter(function (record) {
    return !omittedKinds.has(normalizeText(record && record.kind));
  }).map(function (record) {
    var kind = normalizeText(record && record.kind);
    var label = labels[kind] || kind.replace(/_/g, " ");
    return [label, lifecycleRelativePath(record && record.path, root)];
  });
}

function lifecycleTypeLabel(payload, root) {
  var publishingMode = normalizeText(payload && payload.publishing_mode);
  if (publishingMode) return modeLabel(publishingMode);
  if (root) return SCOPE_LIFECYCLE_TEXT.scopeLocalExternalMode;
  var scopeType = normalizeText(payload && payload.scope_type);
  if (scopeType === "public") return SCOPE_LIFECYCLE_TEXT.scopePublicReadonlyMode;
  if (scopeType === "local") return SCOPE_LIFECYCLE_TEXT.scopeLocalCommittedMode;
  return scopeType;
}

function lifecycleOverviewRows(payload, root) {
  var subScope = normalizeText(payload && payload.sub_scope);
  var rows = subScope
    ? [
        ["parent scope", payload && payload.parent_scope],
        ["sub-scope", subScope]
      ]
    : [["scope", payload && payload.scope_id]];
  rows.push(["title", payload && payload.title]);
  rows.push(["url", payload && payload.urls && payload.urls.management]);
  if (!subScope) rows.push(["type", lifecycleTypeLabel(payload, root)]);
  return rows;
}

function lifecycleStorageRows(payload, root) {
  var contract = payload && payload.storage_contract && typeof payload.storage_contract === "object"
    ? payload.storage_contract
    : {};
  var sourceRecord = lifecycleRecord(payload, ["source_root", "sub_scope_source_root"]);
  var generatedRecord = lifecycleRecord(payload, ["generated_docs_root", "sub_scope_generated_docs_root"]);
  var searchRecord = lifecycleRecord(payload, "generated_search_index");
  var publishedRecord = lifecycleRecord(payload, ["published_docs_root", "sub_scope_published_docs_root"]);
  var publishedSearchRecord = lifecycleRecord(payload, "published_search_index");
  var docsOutput = normalizeText(contract.docs_output);
  var publishOutput = normalizeText(contract.publish_output);
  var searchOutput = normalizeText(contract.search_output);
  var publishSearchOutput = normalizeText(contract.publish_search_output);
  return [
    ["root", root],
    ["source", lifecycleRelativePath(contract.source_root || (sourceRecord && sourceRecord.path), root)],
    ["generated", lifecycleRelativePath(docsOutput || (generatedRecord && generatedRecord.path), root)],
    ["search", lifecycleRelativePath(searchOutput || (searchRecord && searchRecord.path), root)],
    ["published", publishOutput && publishOutput !== docsOutput
      ? lifecycleRelativePath(publishOutput, root)
      : lifecycleRelativePath(publishedRecord && publishedRecord.path, root)],
    ["public search", publishSearchOutput && publishSearchOutput !== searchOutput
      ? lifecycleRelativePath(publishSearchOutput, root)
      : lifecycleRelativePath(publishedSearchRecord && publishedSearchRecord.path, root)]
  ];
}

function renderLifecycleFileSection(heading, payload, records) {
  var rows = lifecycleFileRows(payload, records);
  if (!rows.length) return "";
  return '<section class="docsViewerScopeLifecycle__section"><h3>' + escapeHtml(heading) + '</h3>' +
    renderDetailRows(rows, "") + '</section>';
}

function renderPreviewHtml(payload) {
  var root = externalLifecycleRoot(payload);
  var storageRows = lifecycleStorageRows(payload, root);
  var blockers = Array.isArray(payload && payload.blockers) ? payload.blockers : [];
  var warnings = Array.isArray(payload && payload.warnings) ? payload.warnings : [];
  var deletedFiles = Array.isArray(payload && payload.deleted_files) && payload.deleted_files.length
    ? payload.deleted_files
    : payload && payload.delete_files;
  return (
    '<div class="docsViewerScopeLifecycle docsViewerScopeLifecycle--preview">' +
      renderDetailRows(lifecycleOverviewRows(payload, root), "") +
      (hasDetailRows(storageRows) ? renderDetailRows(storageRows, "") : "") +
      (blockers.length ? '<section class="docsViewerScopeLifecycle__section"><h3>Blockers</h3>' + renderList(blockers, "") + '</section>' : "") +
      (warnings.length ? '<section class="docsViewerScopeLifecycle__section"><h3>Warnings</h3>' + renderList(warnings, "") + '</section>' : "") +
      renderLifecycleFileSection("Created files", payload, payload && payload.created_files) +
      renderLifecycleFileSection("Published files", payload, payload && payload.publish_files) +
      renderLifecycleFileSection("Changed files (repo)", payload, payload && payload.changed_files) +
      renderLifecycleFileSection("Deleted files", payload, deletedFiles) +
      renderLifecycleFileSection("Missing files", payload, payload && payload.missing_files) +
      renderCommands(payload && payload.build_commands) +
    '</div>'
  );
}

function setBusy(callbacks, busy) {
  if (callbacks && typeof callbacks.setBusy === "function") callbacks.setBusy(Boolean(busy));
}

function setMessage(callbacks, message, isError) {
  if (callbacks && typeof callbacks.setMessage === "function") callbacks.setMessage(message, isError);
}

function render(callbacks) {
  if (callbacks && typeof callbacks.render === "function") callbacks.render();
}

function applied(callbacks, payload) {
  if (callbacks && typeof callbacks.onApplied === "function") callbacks.onApplied(payload);
}

async function openPreviewModal(options) {
  var result = await openDocsViewerManagementModal({
    root: options.root,
    title: options.title,
    size: "wide",
    bodyHtml: renderPreviewHtml(options.payload),
    actions: [
      { role: "modal-primary", label: options.primaryLabel },
      { role: "modal-cancel", label: options.cancelLabel }
    ]
  });
  return Boolean(result && result.confirmed);
}

async function openResultModal(options) {
  await openDocsViewerManagementModal({
    root: options.root,
    title: options.title,
    size: "wide",
    bodyHtml: renderPreviewHtml(options.payload),
    actions: [
      { role: "modal-primary", label: options.primaryLabel }
    ]
  });
}

export async function openCreateScopeFlow(options = {}) {
  var callbacks = options.callbacks || {};
  var result = await openDocsViewerManagementModal({
    root: options.root,
    title: SCOPE_LIFECYCLE_TEXT.scopeCreateTitle,
    bodyHtml: renderCreateFormHtml(options.capabilities),
    focusSelector: '[data-role="scope-id"]',
    actions: [
      { role: "modal-primary", label: SCOPE_LIFECYCLE_TEXT.scopePreviewButton },
      { role: "modal-cancel", label: SCOPE_LIFECYCLE_TEXT.cancelButton }
    ],
    onOpen: function (api) {
      wireCreateForm(api);
    },
    onSubmit: function (api) {
      var payload = collectCreatePayload(api);
      return payload ? { confirmed: true, payload: payload } : false;
    }
  });
  if (!result || !result.confirmed || !result.payload) return null;

  var preview;
  try {
    setBusy(callbacks, true);
    setMessage(callbacks, SCOPE_LIFECYCLE_TEXT.scopeCreatePreviewing, false);
    render(callbacks);
    preview = await previewScopeCreate(result.payload, options.clientOptions);
  } catch (error) {
    setMessage(callbacks, error && error.message ? error.message : SCOPE_LIFECYCLE_TEXT.scopeCreateFailed, true);
    return null;
  } finally {
    setBusy(callbacks, false);
    render(callbacks);
  }

  var confirmed = await openPreviewModal({
    root: options.root,
    title: SCOPE_LIFECYCLE_TEXT.scopeCreatePreviewTitle,
    payload: preview,
    primaryLabel: SCOPE_LIFECYCLE_TEXT.scopeSaveButton,
    cancelLabel: SCOPE_LIFECYCLE_TEXT.cancelButton
  });
  if (!confirmed) {
    setMessage(callbacks, "", false);
    return null;
  }

  var appliedPayload;
  try {
    setBusy(callbacks, true);
    setMessage(callbacks, SCOPE_LIFECYCLE_TEXT.scopeCreateSaving, false);
    render(callbacks);
    appliedPayload = await applyScopeCreate(result.payload, options.clientOptions);
    setMessage(callbacks, normalizeText(appliedPayload.summary_text), false);
    applied(callbacks, appliedPayload);
  } catch (error) {
    setMessage(callbacks, error && error.message ? error.message : SCOPE_LIFECYCLE_TEXT.scopeCreateFailed, true);
    return null;
  } finally {
    setBusy(callbacks, false);
    render(callbacks);
  }

  await openResultModal({
    root: options.root,
    title: SCOPE_LIFECYCLE_TEXT.scopeCreateResultTitle,
    payload: appliedPayload,
    primaryLabel: SCOPE_LIFECYCLE_TEXT.scopeResultOkButton
  });
  return appliedPayload;
}

export async function openCreateSubScopeFlow(options = {}) {
  var callbacks = options.callbacks || {};
  var parentScope = normalizeText(options.parentScope);
  if (!parentScope) {
    return null;
  }
  var result = await openDocsViewerManagementModal({
    root: options.root,
    title: SCOPE_LIFECYCLE_TEXT.subScopeCreateTitle,
    size: "compact",
    bodyHtml: renderCreateSubScopeFormHtml(),
    focusSelector: '[data-role="sub-scope-id"]',
    actions: [
      { role: "modal-primary", label: SCOPE_LIFECYCLE_TEXT.scopePreviewButton },
      { role: "modal-cancel", label: SCOPE_LIFECYCLE_TEXT.cancelButton }
    ],
    onOpen: function (api) {
      wireCreateSubScopeForm(api);
    },
    onSubmit: function (api) {
      var payload = collectCreateSubScopePayload(api, parentScope);
      return payload ? { confirmed: true, payload: payload } : false;
    }
  });
  if (!result || !result.confirmed || !result.payload) return null;

  var preview;
  try {
    setBusy(callbacks, true);
    setMessage(callbacks, SCOPE_LIFECYCLE_TEXT.subScopeCreatePreviewing, false);
    render(callbacks);
    preview = await previewSubScopeCreate(result.payload, options.clientOptions);
  } catch (error) {
    setMessage(callbacks, error && error.message ? error.message : SCOPE_LIFECYCLE_TEXT.subScopeCreateFailed, true);
    return null;
  } finally {
    setBusy(callbacks, false);
    render(callbacks);
  }

  var confirmed = await openPreviewModal({
    root: options.root,
    title: SCOPE_LIFECYCLE_TEXT.subScopeCreatePreviewTitle,
    payload: preview,
    primaryLabel: SCOPE_LIFECYCLE_TEXT.scopeSaveButton,
    cancelLabel: SCOPE_LIFECYCLE_TEXT.cancelButton
  });
  if (!confirmed) {
    setMessage(callbacks, "", false);
    return null;
  }

  var appliedPayload;
  try {
    setBusy(callbacks, true);
    setMessage(callbacks, SCOPE_LIFECYCLE_TEXT.subScopeCreateSaving, false);
    render(callbacks);
    appliedPayload = await applySubScopeCreate(result.payload, options.clientOptions);
    setMessage(callbacks, normalizeText(appliedPayload.summary_text), false);
    applied(callbacks, appliedPayload);
  } catch (error) {
    setMessage(callbacks, error && error.message ? error.message : SCOPE_LIFECYCLE_TEXT.subScopeCreateFailed, true);
    return null;
  } finally {
    setBusy(callbacks, false);
    render(callbacks);
  }

  await openResultModal({
    root: options.root,
    title: SCOPE_LIFECYCLE_TEXT.subScopeCreateResultTitle,
    payload: appliedPayload,
    primaryLabel: SCOPE_LIFECYCLE_TEXT.scopeResultOkButton
  });
  return appliedPayload;
}

function renderDeleteSelectHtml(targets) {
  return (
    '<div class="docsViewerScopeLifecycle">' +
      '<p class="docsViewer__modalNote muted small">' + escapeHtml(SCOPE_LIFECYCLE_TEXT.scopeDeleteIntro) + '</p>' +
      '<label class="docsViewer__field">' +
        '<span class="docsViewer__fieldLabel">' + escapeHtml(SCOPE_LIFECYCLE_TEXT.scopeDeleteTargetLabel) + '</span>' +
        '<select class="docsViewer__fieldInput" data-role="scope-delete-target">' + targets.map(function (target) {
          var label = target.scopeId + (target.root ? " - " + target.root : "");
          return '<option value="' + escapeHtml(target.scopeId) + '">' + escapeHtml(label) + '</option>';
        }).join("") + '</select>' +
      '</label>' +
    '</div>'
  );
}

function renderRenameFormHtml(targets) {
  return (
    '<div class="docsViewerScopeLifecycle">' +
      '<p class="docsViewer__modalNote muted small">' + escapeHtml(SCOPE_LIFECYCLE_TEXT.scopeRenameIntro) + '</p>' +
      '<label class="docsViewer__field">' +
        '<span class="docsViewer__fieldLabel">' + escapeHtml(SCOPE_LIFECYCLE_TEXT.scopeRenameTargetLabel) + '</span>' +
        '<select class="docsViewer__fieldInput" data-role="scope-rename-target">' + targets.map(function (target) {
          return '<option value="' + escapeHtml(target.scopeId) + '">' + escapeHtml(target.scopeId) + '</option>';
        }).join("") + '</select>' +
      '</label>' +
      '<label class="docsViewer__field">' +
        '<span class="docsViewer__fieldLabel">' + escapeHtml(SCOPE_LIFECYCLE_TEXT.scopeRenameNewIdLabel) + '</span>' +
        '<input class="docsViewer__fieldInput" data-role="scope-rename-new-id" type="text" autocomplete="off" spellcheck="false" required>' +
      '</label>' +
      '<p class="docsViewer__modalNote muted small">' + escapeHtml(SCOPE_LIFECYCLE_TEXT.scopeRenameWarning) + '</p>' +
    '</div>'
  );
}

export async function openRenameScopeFlow(options = {}) {
  var callbacks = options.callbacks || {};
  var targets = scopeLifecycleRenameTargets(options.capabilities);
  if (!targets.length) {
    setMessage(callbacks, SCOPE_LIFECYCLE_TEXT.scopeRenameNoTargets, true);
    return null;
  }

  var selection = await openDocsViewerManagementModal({
    root: options.root,
    title: SCOPE_LIFECYCLE_TEXT.scopeRenameTitle,
    size: "compact",
    bodyHtml: renderRenameFormHtml(targets),
    focusSelector: '[data-role="scope-rename-new-id"]',
    actions: [
      { role: "modal-primary", label: SCOPE_LIFECYCLE_TEXT.scopeRenameButton },
      { role: "modal-cancel", label: SCOPE_LIFECYCLE_TEXT.cancelButton }
    ],
    onSubmit: function (api) {
      var scopeId = normalizeText(api.host.querySelector('[data-role="scope-rename-target"]')?.value);
      var newScopeId = normalizeText(api.host.querySelector('[data-role="scope-rename-new-id"]')?.value).toLowerCase();
      if (!scopeId || !newScopeId) {
        api.setStatus(SCOPE_LIFECYCLE_TEXT.scopeRenameRequiredMessage);
        return false;
      }
      if (scopeId === newScopeId) {
        api.setStatus(SCOPE_LIFECYCLE_TEXT.scopeRenameSameIdMessage);
        return false;
      }
      return { confirmed: true, scopeId: scopeId, newScopeId: newScopeId };
    }
  });
  if (!selection || !selection.confirmed) return null;

  var preview;
  try {
    setBusy(callbacks, true);
    setMessage(callbacks, SCOPE_LIFECYCLE_TEXT.scopeRenameSaving, false);
    render(callbacks);
    preview = await previewScopeRename(selection.scopeId, selection.newScopeId, options.clientOptions);
    if (!preview.allowed) {
      setMessage(callbacks, (preview.blockers || []).join("; ") || SCOPE_LIFECYCLE_TEXT.scopeRenameBlocked, true);
      return null;
    }
    var appliedPayload = await applyScopeRename(selection.scopeId, selection.newScopeId, options.clientOptions);
    setMessage(callbacks, normalizeText(appliedPayload.summary_text), false);
    applied(callbacks, appliedPayload);
    if (typeof callbacks.navigateToScope === "function") callbacks.navigateToScope(selection.newScopeId);
    return appliedPayload;
  } catch (error) {
    setMessage(callbacks, error && error.message ? error.message : SCOPE_LIFECYCLE_TEXT.scopeRenameFailed, true);
    return null;
  } finally {
    setBusy(callbacks, false);
    render(callbacks);
  }
}

function renderDeleteSubScopeSelectHtml(targets) {
  return (
    '<div class="docsViewerScopeLifecycle">' +
      '<p class="docsViewer__modalNote muted small">' + escapeHtml(SCOPE_LIFECYCLE_TEXT.subScopeDeleteIntro) + '</p>' +
      '<label class="docsViewer__field">' +
        '<span class="docsViewer__fieldLabel">' + escapeHtml(SCOPE_LIFECYCLE_TEXT.subScopeDeleteTargetLabel) + '</span>' +
        '<select class="docsViewer__fieldInput" data-role="sub-scope-delete-target">' + targets.map(function (target) {
          var label = target.subScope + (target.title ? " - " + target.title : "");
          return '<option value="' + escapeHtml(target.subScope) + '">' + escapeHtml(label) + '</option>';
        }).join("") + '</select>' +
      '</label>' +
    '</div>'
  );
}

export async function openDeleteScopeFlow(options = {}) {
  var callbacks = options.callbacks || {};
  var targets = scopeLifecycleDeleteTargets(options.capabilities);
  if (!targets.length) {
    setMessage(callbacks, SCOPE_LIFECYCLE_TEXT.scopeDeleteNoTargets, true);
    return null;
  }

  var selection = await openDocsViewerManagementModal({
    root: options.root,
    title: SCOPE_LIFECYCLE_TEXT.scopeDeleteTitle,
    size: "compact",
    bodyHtml: renderDeleteSelectHtml(targets),
    focusSelector: '[data-role="scope-delete-target"]',
    actions: [
      { role: "modal-primary", label: SCOPE_LIFECYCLE_TEXT.scopePreviewButton },
      { role: "modal-cancel", label: SCOPE_LIFECYCLE_TEXT.cancelButton }
    ],
    onSubmit: function (api) {
      var scopeId = normalizeText(api.host.querySelector('[data-role="scope-delete-target"]')?.value);
      if (!scopeId) {
        api.setStatus(SCOPE_LIFECYCLE_TEXT.scopeDeleteRequiredMessage);
        return false;
      }
      return { confirmed: true, scopeId: scopeId };
    }
  });
  if (!selection || !selection.confirmed || !selection.scopeId) return null;

  var preview;
  try {
    setBusy(callbacks, true);
    setMessage(callbacks, SCOPE_LIFECYCLE_TEXT.scopeDeletePreviewing, false);
    render(callbacks);
    preview = await previewScopeDelete(selection.scopeId, options.clientOptions);
  } catch (error) {
    setMessage(callbacks, error && error.message ? error.message : SCOPE_LIFECYCLE_TEXT.scopeDeleteFailed, true);
    return null;
  } finally {
    setBusy(callbacks, false);
    render(callbacks);
  }

  if (!preview.allowed) {
    setMessage(callbacks, (preview.blockers || []).join("; ") || SCOPE_LIFECYCLE_TEXT.scopeDeleteBlocked, true);
    await openResultModal({
      root: options.root,
      title: SCOPE_LIFECYCLE_TEXT.scopeDeleteBlockedTitle,
      payload: preview,
      primaryLabel: SCOPE_LIFECYCLE_TEXT.scopeResultOkButton
    });
    return null;
  }

  var confirmed = await openPreviewModal({
    root: options.root,
    title: SCOPE_LIFECYCLE_TEXT.scopeDeletePreviewTitle,
    payload: preview,
    primaryLabel: SCOPE_LIFECYCLE_TEXT.scopeDeleteButton,
    cancelLabel: SCOPE_LIFECYCLE_TEXT.cancelButton
  });
  if (!confirmed) {
    setMessage(callbacks, "", false);
    return null;
  }

  var appliedPayload;
  try {
    setBusy(callbacks, true);
    setMessage(callbacks, SCOPE_LIFECYCLE_TEXT.scopeDeleteDeleting, false);
    render(callbacks);
    appliedPayload = await applyScopeDelete(selection.scopeId, options.clientOptions);
    setMessage(callbacks, normalizeText(appliedPayload.summary_text), false);
    applied(callbacks, appliedPayload);
  } catch (error) {
    setMessage(callbacks, error && error.message ? error.message : SCOPE_LIFECYCLE_TEXT.scopeDeleteFailed, true);
    return null;
  } finally {
    setBusy(callbacks, false);
    render(callbacks);
  }

  await openResultModal({
    root: options.root,
    title: SCOPE_LIFECYCLE_TEXT.scopeDeleteResultTitle,
    payload: appliedPayload,
    primaryLabel: SCOPE_LIFECYCLE_TEXT.scopeResultOkButton
  });
  return appliedPayload;
}

export async function openDeleteSubScopeFlow(options = {}) {
  var callbacks = options.callbacks || {};
  var parentScope = normalizeText(options.parentScope);
  var targets = subScopeLifecycleDeleteTargets(options.capabilities, parentScope);
  if (!parentScope) {
    setMessage(callbacks, SCOPE_LIFECYCLE_TEXT.subScopeDeleteNoParent, true);
    return null;
  }
  if (!targets.length) {
    setMessage(callbacks, SCOPE_LIFECYCLE_TEXT.subScopeDeleteNoTargets, true);
    return null;
  }

  var selection = await openDocsViewerManagementModal({
    root: options.root,
    title: SCOPE_LIFECYCLE_TEXT.subScopeDeleteTitle,
    size: "compact",
    bodyHtml: renderDeleteSubScopeSelectHtml(targets),
    focusSelector: '[data-role="sub-scope-delete-target"]',
    actions: [
      { role: "modal-primary", label: SCOPE_LIFECYCLE_TEXT.scopePreviewButton },
      { role: "modal-cancel", label: SCOPE_LIFECYCLE_TEXT.cancelButton }
    ],
    onSubmit: function (api) {
      var subScope = normalizeText(api.host.querySelector('[data-role="sub-scope-delete-target"]')?.value);
      if (!subScope) {
        api.setStatus(SCOPE_LIFECYCLE_TEXT.subScopeDeleteRequiredMessage);
        return false;
      }
      return { confirmed: true, subScope: subScope };
    }
  });
  if (!selection || !selection.confirmed || !selection.subScope) return null;

  var preview;
  try {
    setBusy(callbacks, true);
    setMessage(callbacks, SCOPE_LIFECYCLE_TEXT.subScopeDeletePreviewing, false);
    render(callbacks);
    preview = await previewSubScopeDelete(parentScope, selection.subScope, options.clientOptions);
  } catch (error) {
    setMessage(callbacks, error && error.message ? error.message : SCOPE_LIFECYCLE_TEXT.subScopeDeleteFailed, true);
    return null;
  } finally {
    setBusy(callbacks, false);
    render(callbacks);
  }

  if (!preview.allowed) {
    setMessage(callbacks, (preview.blockers || []).join("; ") || SCOPE_LIFECYCLE_TEXT.subScopeDeleteBlocked, true);
    await openResultModal({
      root: options.root,
      title: SCOPE_LIFECYCLE_TEXT.scopeDeleteBlockedTitle,
      payload: preview,
      primaryLabel: SCOPE_LIFECYCLE_TEXT.scopeResultOkButton
    });
    return null;
  }

  var confirmed = await openPreviewModal({
    root: options.root,
    title: SCOPE_LIFECYCLE_TEXT.subScopeDeletePreviewTitle,
    payload: preview,
    primaryLabel: SCOPE_LIFECYCLE_TEXT.scopeDeleteButton,
    cancelLabel: SCOPE_LIFECYCLE_TEXT.cancelButton
  });
  if (!confirmed) {
    setMessage(callbacks, "", false);
    return null;
  }

  var appliedPayload;
  try {
    setBusy(callbacks, true);
    setMessage(callbacks, SCOPE_LIFECYCLE_TEXT.subScopeDeleteDeleting, false);
    render(callbacks);
    appliedPayload = await applySubScopeDelete(parentScope, selection.subScope, options.clientOptions);
    setMessage(callbacks, normalizeText(appliedPayload.summary_text), false);
    applied(callbacks, appliedPayload);
  } catch (error) {
    setMessage(callbacks, error && error.message ? error.message : SCOPE_LIFECYCLE_TEXT.subScopeDeleteFailed, true);
    return null;
  } finally {
    setBusy(callbacks, false);
    render(callbacks);
  }

  await openResultModal({
    root: options.root,
    title: SCOPE_LIFECYCLE_TEXT.subScopeDeleteResultTitle,
    payload: appliedPayload,
    primaryLabel: SCOPE_LIFECYCLE_TEXT.scopeResultOkButton
  });
  return appliedPayload;
}
