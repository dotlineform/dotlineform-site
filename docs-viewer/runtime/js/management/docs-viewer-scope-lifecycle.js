import {
  applyScopeCreate,
  applyScopeDelete,
  applySubScopeCreate,
  applySubScopeDelete,
  previewScopeCreate,
  previewScopeDelete,
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

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function managementText(state, key) {
  if (state && state.managementText && Object.prototype.hasOwnProperty.call(state.managementText, key)) {
    var value = state.managementText[key];
    return normalizeText(value);
  }
  return "";
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

function modeLabel(state, mode) {
  var labels = {
    public_readonly: managementText(state, "scopePublicReadonlyMode"),
    local_committed: managementText(state, "scopeLocalCommittedMode"),
    local_external: managementText(state, "scopeLocalExternalMode")
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

function renderModeOptions(state, modes) {
  return modes.map(function (mode) {
    return '<option value="' + escapeHtml(mode) + '">' + escapeHtml(modeLabel(state, mode)) + '</option>';
  }).join("");
}

function renderCreateFormHtml(state, capabilities) {
  var modes = publishingModes(capabilities);
  return (
    '<div class="docsViewerScopeLifecycle">' +
      '<label class="docsViewer__field">' +
        '<span class="docsViewer__fieldLabel">' + escapeHtml(managementText(state, "scopeIdLabel")) + '</span>' +
        '<input class="docsViewer__fieldInput" data-role="scope-id" type="text" autocomplete="off" spellcheck="false" required>' +
      '</label>' +
      '<label class="docsViewer__field">' +
        '<span class="docsViewer__fieldLabel">' + escapeHtml(managementText(state, "scopeTitleLabel")) + '</span>' +
        '<input class="docsViewer__fieldInput" data-role="scope-title" type="text" autocomplete="off" spellcheck="false" required>' +
      '</label>' +
      '<label class="docsViewer__field">' +
        '<span class="docsViewer__fieldLabel">' + escapeHtml(managementText(state, "scopePublishingModeLabel")) + '</span>' +
        '<select class="docsViewer__fieldInput" data-role="scope-publishing-mode">' + renderModeOptions(state, modes) + '</select>' +
      '</label>' +
      '<label class="docsViewer__field" data-role="scope-source-root-field">' +
        '<span class="docsViewer__fieldLabel">' + escapeHtml(managementText(state, "scopeSourceRootLabel")) + '</span>' +
        '<input class="docsViewer__fieldInput" data-role="scope-source-root" type="text" autocomplete="off" spellcheck="false" required>' +
      '</label>' +
      '<label class="docsViewer__field">' +
        '<span class="docsViewer__fieldLabel">' + escapeHtml(managementText(state, "scopeDefaultDocIdLabel")) + '</span>' +
        '<input class="docsViewer__fieldInput" data-role="scope-default-doc-id" type="text" autocomplete="off" spellcheck="false" required>' +
      '</label>' +
      '<label class="docsViewer__field" data-role="scope-route-field">' +
        '<span class="docsViewer__fieldLabel">' + escapeHtml(managementText(state, "scopePublicRoutePathLabel")) + '</span>' +
        '<input class="docsViewer__fieldInput" data-role="scope-public-route-path" type="text" autocomplete="off" spellcheck="false">' +
      '</label>' +
    '</div>'
  );
}

function wireCreateForm(api, state) {
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
    return humanTitleFromSlug(scopeInput && scopeInput.value);
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

function collectCreatePayload(api, state) {
  var host = api.host;
  var scopeId = normalizeText(host.querySelector('[data-role="scope-id"]')?.value).toLowerCase();
  var title = normalizeText(host.querySelector('[data-role="scope-title"]')?.value);
  var publishingMode = normalizeText(host.querySelector('[data-role="scope-publishing-mode"]')?.value) || "local_external";
  var sourceRoot = normalizeText(host.querySelector('[data-role="scope-source-root"]')?.value);
  var defaultDocId = normalizeText(host.querySelector('[data-role="scope-default-doc-id"]')?.value);
  var publicRoutePath = normalizeText(host.querySelector('[data-role="scope-public-route-path"]')?.value);

  if (!scopeId || !title || !defaultDocId || (publishingMode !== "local_external" && !sourceRoot)) {
    api.setStatus(managementText(state, "scopeCreateRequiredMessage"));
    return null;
  }
  if (publishingMode === "public_readonly" && !publicRoutePath) {
    api.setStatus(managementText(state, "scopeCreateRouteRequiredMessage"));
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

function renderCreateSubScopeFormHtml(state, parentScope) {
  return (
    '<div class="docsViewerScopeLifecycle">' +
      '<label class="docsViewer__field">' +
        '<span class="docsViewer__fieldLabel">' + escapeHtml(managementText(state, "subScopeIdLabel")) + '</span>' +
        '<input class="docsViewer__fieldInput" data-role="sub-scope-id" type="text" autocomplete="off" spellcheck="false" required>' +
      '</label>' +
      '<label class="docsViewer__field">' +
        '<span class="docsViewer__fieldLabel">' + escapeHtml(managementText(state, "subScopeTitleLabel")) + '</span>' +
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

function collectCreateSubScopePayload(api, state, parentScope) {
  var host = api.host;
  var subScope = slugFromScopeInput(host.querySelector('[data-role="sub-scope-id"]')?.value);
  var title = normalizeText(host.querySelector('[data-role="sub-scope-title"]')?.value);
  if (!parentScope || !subScope || !title) {
    api.setStatus(managementText(state, "subScopeCreateRequiredMessage"));
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
      '<ul class="docsViewerScopeLifecycle__list">' + records.map(function (record) {
        var command = normalizeText(record && record.command);
        var status = normalizeText(record && record.status);
        return '<li>' + escapeHtml([command, status].filter(Boolean).join(" - ")) + '</li>';
      }).join("") + '</ul>' +
    '</section>'
  );
}

function renderUrls(urls) {
  var entries = [];
  if (urls && urls.management) entries.push(["management", urls.management]);
  if (urls && urls.public) entries.push(["public", urls.public]);
  if (!entries.length) return "";
  return (
    '<section class="docsViewerScopeLifecycle__section">' +
      '<h3>' + escapeHtml("URLs") + '</h3>' +
      '<dl class="docsViewerScopeLifecycle__summaryGrid">' + entries.map(function (entry) {
        return '<div><dt>' + escapeHtml(entry[0]) + '</dt><dd>' + escapeHtml(entry[1]) + '</dd></div>';
      }).join("") + '</dl>' +
    '</section>'
  );
}

function renderStorageContract(contract) {
  if (!contract || typeof contract !== "object") return "";
  var rows = [];
  var summary = normalizeText(contract.summary);
  var sourceRoot = normalizeText(contract.source_root);
  var docsOutput = normalizeText(contract.docs_output);
  var searchOutput = normalizeText(contract.search_output);
  var publicAssets = contract.public_static_assets === true ? "yes" : "no";
  rows.push(["public static assets", publicAssets]);
  if (sourceRoot) rows.push(["source root", sourceRoot]);
  if (docsOutput) rows.push(["docs output", docsOutput]);
  if (searchOutput) rows.push(["search output", searchOutput]);
  return (
    '<section class="docsViewerScopeLifecycle__section">' +
      '<h3>' + escapeHtml("Storage") + '</h3>' +
      (summary ? '<p class="docsViewer__modalNote muted small">' + escapeHtml(summary) + '</p>' : "") +
      '<dl class="docsViewerScopeLifecycle__summaryGrid">' + rows.map(function (entry) {
        return '<div><dt>' + escapeHtml(entry[0]) + '</dt><dd>' + escapeHtml(entry[1]) + '</dd></div>';
      }).join("") + '</dl>' +
    '</section>'
  );
}

function renderPreviewHtml(payload, options) {
  var settings = options || {};
  var title = normalizeText(payload && payload.title) || normalizeText(payload && payload.scope_id);
  var summary = normalizeText(payload && payload.summary_text);
  var blockers = Array.isArray(payload && payload.blockers) ? payload.blockers : [];
  var summaryRows = [];
  if (payload && payload.parent_scope) summaryRows.push(["parent scope", payload.parent_scope]);
  if (payload && payload.sub_scope) summaryRows.push(["sub-scope", payload.sub_scope]);
  if (payload && !payload.parent_scope && payload.scope_id) summaryRows.push(["scope", payload.scope_id]);
  if (title) summaryRows.push(["title", title]);
  return (
    '<div class="docsViewerScopeLifecycle docsViewerScopeLifecycle--preview">' +
      (summary ? '<p class="docsViewer__modalNote muted small">' + escapeHtml(summary) + '</p>' : "") +
      (summaryRows.length ? '<dl class="docsViewerScopeLifecycle__summaryGrid">' + summaryRows.map(function (entry) {
        return '<div><dt>' + escapeHtml(entry[0]) + '</dt><dd>' + escapeHtml(entry[1]) + '</dd></div>';
      }).join("") + '</dl>' : "") +
      renderStorageContract(payload && payload.storage_contract) +
      (blockers.length ? '<section class="docsViewerScopeLifecycle__section"><h3>Blockers</h3>' + renderList(blockers, "") + '</section>' : "") +
      (Array.isArray(payload && payload.warnings) && payload.warnings.length ? '<section class="docsViewerScopeLifecycle__section"><h3>Warnings</h3>' + renderList(payload.warnings, "") + '</section>' : "") +
      (Array.isArray(payload && payload.created_files) ? '<section class="docsViewerScopeLifecycle__section"><h3>' + escapeHtml(settings.createdHeading || "Created files") + '</h3>' + renderList(payload && payload.created_files, "No files will be created.") + '</section>' : "") +
      '<section class="docsViewerScopeLifecycle__section"><h3>' + escapeHtml(settings.changedHeading || "Changed files") + '</h3>' + renderList(payload && payload.changed_files, "No files will be changed.") + '</section>' +
      (Array.isArray(payload && payload.deleted_files) && payload.deleted_files.length ? '<section class="docsViewerScopeLifecycle__section"><h3>Deleted files</h3>' + renderList(payload.deleted_files, "") + '</section>' : "") +
      (Array.isArray(payload && payload.delete_files) && payload.delete_files.length ? '<section class="docsViewerScopeLifecycle__section"><h3>Deleted files</h3>' + renderList(payload.delete_files, "") + '</section>' : "") +
      (Array.isArray(payload && payload.missing_files) && payload.missing_files.length ? '<section class="docsViewerScopeLifecycle__section"><h3>Missing files</h3>' + renderList(payload.missing_files, "") + '</section>' : "") +
      renderCommands(payload && payload.build_commands) +
      renderUrls(payload && payload.urls) +
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
    bodyHtml: renderPreviewHtml(options.payload, options),
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
    bodyHtml: renderPreviewHtml(options.payload, options),
    actions: [
      { role: "modal-primary", label: options.primaryLabel }
    ]
  });
}

export async function openCreateScopeFlow(options = {}) {
  var state = options.state || {};
  var callbacks = options.callbacks || {};
  var result = await openDocsViewerManagementModal({
    root: options.root,
    title: managementText(state, "scopeCreateTitle"),
    bodyHtml: renderCreateFormHtml(state, options.capabilities),
    focusSelector: '[data-role="scope-id"]',
    actions: [
      { role: "modal-primary", label: managementText(state, "scopePreviewButton") },
      { role: "modal-cancel", label: managementText(state, "cancelButton") }
    ],
    onOpen: function (api) {
      wireCreateForm(api, state);
    },
    onSubmit: function (api) {
      var payload = collectCreatePayload(api, state);
      return payload ? { confirmed: true, payload: payload } : false;
    }
  });
  if (!result || !result.confirmed || !result.payload) return null;

  var preview;
  try {
    setBusy(callbacks, true);
    setMessage(callbacks, managementText(state, "scopeCreatePreviewing"), false);
    render(callbacks);
    preview = await previewScopeCreate(result.payload, options.clientOptions);
  } catch (error) {
    setMessage(callbacks, error && error.message ? error.message : managementText(state, "scopeCreateFailed"), true);
    return null;
  } finally {
    setBusy(callbacks, false);
    render(callbacks);
  }

  var confirmed = await openPreviewModal({
    root: options.root,
    title: managementText(state, "scopeCreatePreviewTitle"),
    payload: preview,
    primaryLabel: managementText(state, "scopeSaveButton"),
    cancelLabel: managementText(state, "cancelButton")
  });
  if (!confirmed) {
    setMessage(callbacks, "", false);
    return null;
  }

  var appliedPayload;
  try {
    setBusy(callbacks, true);
    setMessage(callbacks, managementText(state, "scopeCreateSaving"), false);
    render(callbacks);
    appliedPayload = await applyScopeCreate(result.payload, options.clientOptions);
    setMessage(callbacks, normalizeText(appliedPayload.summary_text), false);
    applied(callbacks, appliedPayload);
  } catch (error) {
    setMessage(callbacks, error && error.message ? error.message : managementText(state, "scopeCreateFailed"), true);
    return null;
  } finally {
    setBusy(callbacks, false);
    render(callbacks);
  }

  await openResultModal({
    root: options.root,
    title: managementText(state, "scopeCreateResultTitle"),
    payload: appliedPayload,
    primaryLabel: managementText(state, "scopeResultOkButton")
  });
  return appliedPayload;
}

export async function openCreateSubScopeFlow(options = {}) {
  var state = options.state || {};
  var callbacks = options.callbacks || {};
  var parentScope = normalizeText(options.parentScope);
  if (!parentScope) {
    return null;
  }
  var result = await openDocsViewerManagementModal({
    root: options.root,
    title: managementText(state, "subScopeCreateTitle"),
    size: "compact",
    bodyHtml: renderCreateSubScopeFormHtml(state, parentScope),
    focusSelector: '[data-role="sub-scope-id"]',
    actions: [
      { role: "modal-primary", label: managementText(state, "scopePreviewButton") },
      { role: "modal-cancel", label: managementText(state, "cancelButton") }
    ],
    onOpen: function (api) {
      wireCreateSubScopeForm(api);
    },
    onSubmit: function (api) {
      var payload = collectCreateSubScopePayload(api, state, parentScope);
      return payload ? { confirmed: true, payload: payload } : false;
    }
  });
  if (!result || !result.confirmed || !result.payload) return null;

  var preview;
  try {
    setBusy(callbacks, true);
    setMessage(callbacks, managementText(state, "subScopeCreatePreviewing"), false);
    render(callbacks);
    preview = await previewSubScopeCreate(result.payload, options.clientOptions);
  } catch (error) {
    setMessage(callbacks, error && error.message ? error.message : managementText(state, "subScopeCreateFailed"), true);
    return null;
  } finally {
    setBusy(callbacks, false);
    render(callbacks);
  }

  var confirmed = await openPreviewModal({
    root: options.root,
    title: managementText(state, "subScopeCreatePreviewTitle"),
    payload: preview,
    primaryLabel: managementText(state, "scopeSaveButton"),
    cancelLabel: managementText(state, "cancelButton")
  });
  if (!confirmed) {
    setMessage(callbacks, "", false);
    return null;
  }

  var appliedPayload;
  try {
    setBusy(callbacks, true);
    setMessage(callbacks, managementText(state, "subScopeCreateSaving"), false);
    render(callbacks);
    appliedPayload = await applySubScopeCreate(result.payload, options.clientOptions);
    setMessage(callbacks, normalizeText(appliedPayload.summary_text), false);
    applied(callbacks, appliedPayload);
  } catch (error) {
    setMessage(callbacks, error && error.message ? error.message : managementText(state, "subScopeCreateFailed"), true);
    return null;
  } finally {
    setBusy(callbacks, false);
    render(callbacks);
  }

  await openResultModal({
    root: options.root,
    title: managementText(state, "subScopeCreateResultTitle"),
    payload: appliedPayload,
    primaryLabel: managementText(state, "scopeResultOkButton")
  });
  return appliedPayload;
}

function renderDeleteSelectHtml(state, targets) {
  return (
    '<div class="docsViewerScopeLifecycle">' +
      '<p class="docsViewer__modalNote muted small">' + escapeHtml(managementText(state, "scopeDeleteIntro")) + '</p>' +
      '<label class="docsViewer__field">' +
        '<span class="docsViewer__fieldLabel">' + escapeHtml(managementText(state, "scopeDeleteTargetLabel")) + '</span>' +
        '<select class="docsViewer__fieldInput" data-role="scope-delete-target">' + targets.map(function (target) {
          var label = target.scopeId + (target.root ? " - " + target.root : "");
          return '<option value="' + escapeHtml(target.scopeId) + '">' + escapeHtml(label) + '</option>';
        }).join("") + '</select>' +
      '</label>' +
    '</div>'
  );
}

function renderDeleteSubScopeSelectHtml(state, parentScope, targets) {
  return (
    '<div class="docsViewerScopeLifecycle">' +
      '<p class="docsViewer__modalNote muted small">' + escapeHtml(managementText(state, "subScopeDeleteIntro")) + '</p>' +
      '<label class="docsViewer__field">' +
        '<span class="docsViewer__fieldLabel">' + escapeHtml(managementText(state, "subScopeDeleteTargetLabel")) + '</span>' +
        '<select class="docsViewer__fieldInput" data-role="sub-scope-delete-target">' + targets.map(function (target) {
          var label = target.subScope + (target.title ? " - " + target.title : "");
          return '<option value="' + escapeHtml(target.subScope) + '">' + escapeHtml(label) + '</option>';
        }).join("") + '</select>' +
      '</label>' +
    '</div>'
  );
}

export async function openDeleteScopeFlow(options = {}) {
  var state = options.state || {};
  var callbacks = options.callbacks || {};
  var targets = scopeLifecycleDeleteTargets(options.capabilities);
  if (!targets.length) {
    setMessage(callbacks, managementText(state, "scopeDeleteNoTargets"), true);
    return null;
  }

  var selection = await openDocsViewerManagementModal({
    root: options.root,
    title: managementText(state, "scopeDeleteTitle"),
    size: "compact",
    bodyHtml: renderDeleteSelectHtml(state, targets),
    focusSelector: '[data-role="scope-delete-target"]',
    actions: [
      { role: "modal-primary", label: managementText(state, "scopePreviewButton") },
      { role: "modal-cancel", label: managementText(state, "cancelButton") }
    ],
    onSubmit: function (api) {
      var scopeId = normalizeText(api.host.querySelector('[data-role="scope-delete-target"]')?.value);
      if (!scopeId) {
        api.setStatus(managementText(state, "scopeDeleteRequiredMessage"));
        return false;
      }
      return { confirmed: true, scopeId: scopeId };
    }
  });
  if (!selection || !selection.confirmed || !selection.scopeId) return null;

  var preview;
  try {
    setBusy(callbacks, true);
    setMessage(callbacks, managementText(state, "scopeDeletePreviewing"), false);
    render(callbacks);
    preview = await previewScopeDelete(selection.scopeId, options.clientOptions);
  } catch (error) {
    setMessage(callbacks, error && error.message ? error.message : managementText(state, "scopeDeleteFailed"), true);
    return null;
  } finally {
    setBusy(callbacks, false);
    render(callbacks);
  }

  if (!preview.allowed) {
    setMessage(callbacks, (preview.blockers || []).join("; ") || managementText(state, "scopeDeleteBlocked"), true);
    await openResultModal({
      root: options.root,
      title: managementText(state, "scopeDeleteBlockedTitle"),
      payload: preview,
      primaryLabel: managementText(state, "scopeResultOkButton")
    });
    return null;
  }

  var confirmed = await openPreviewModal({
    root: options.root,
    title: managementText(state, "scopeDeletePreviewTitle"),
    payload: preview,
    createdHeading: "Created files",
    changedHeading: "Changed files",
    primaryLabel: managementText(state, "scopeDeleteButton"),
    cancelLabel: managementText(state, "cancelButton")
  });
  if (!confirmed) {
    setMessage(callbacks, "", false);
    return null;
  }

  var appliedPayload;
  try {
    setBusy(callbacks, true);
    setMessage(callbacks, managementText(state, "scopeDeleteDeleting"), false);
    render(callbacks);
    appliedPayload = await applyScopeDelete(selection.scopeId, options.clientOptions);
    setMessage(callbacks, normalizeText(appliedPayload.summary_text), false);
    applied(callbacks, appliedPayload);
  } catch (error) {
    setMessage(callbacks, error && error.message ? error.message : managementText(state, "scopeDeleteFailed"), true);
    return null;
  } finally {
    setBusy(callbacks, false);
    render(callbacks);
  }

  await openResultModal({
    root: options.root,
    title: managementText(state, "scopeDeleteResultTitle"),
    payload: appliedPayload,
    primaryLabel: managementText(state, "scopeResultOkButton")
  });
  return appliedPayload;
}

export async function openDeleteSubScopeFlow(options = {}) {
  var state = options.state || {};
  var callbacks = options.callbacks || {};
  var parentScope = normalizeText(options.parentScope);
  var targets = subScopeLifecycleDeleteTargets(options.capabilities, parentScope);
  if (!parentScope) {
    setMessage(callbacks, managementText(state, "subScopeDeleteNoParent"), true);
    return null;
  }
  if (!targets.length) {
    setMessage(callbacks, managementText(state, "subScopeDeleteNoTargets"), true);
    return null;
  }

  var selection = await openDocsViewerManagementModal({
    root: options.root,
    title: managementText(state, "subScopeDeleteTitle"),
    size: "compact",
    bodyHtml: renderDeleteSubScopeSelectHtml(state, parentScope, targets),
    focusSelector: '[data-role="sub-scope-delete-target"]',
    actions: [
      { role: "modal-primary", label: managementText(state, "scopePreviewButton") },
      { role: "modal-cancel", label: managementText(state, "cancelButton") }
    ],
    onSubmit: function (api) {
      var subScope = normalizeText(api.host.querySelector('[data-role="sub-scope-delete-target"]')?.value);
      if (!subScope) {
        api.setStatus(managementText(state, "subScopeDeleteRequiredMessage"));
        return false;
      }
      return { confirmed: true, subScope: subScope };
    }
  });
  if (!selection || !selection.confirmed || !selection.subScope) return null;

  var preview;
  try {
    setBusy(callbacks, true);
    setMessage(callbacks, managementText(state, "subScopeDeletePreviewing"), false);
    render(callbacks);
    preview = await previewSubScopeDelete(parentScope, selection.subScope, options.clientOptions);
  } catch (error) {
    setMessage(callbacks, error && error.message ? error.message : managementText(state, "subScopeDeleteFailed"), true);
    return null;
  } finally {
    setBusy(callbacks, false);
    render(callbacks);
  }

  if (!preview.allowed) {
    setMessage(callbacks, (preview.blockers || []).join("; ") || managementText(state, "subScopeDeleteBlocked"), true);
    await openResultModal({
      root: options.root,
      title: managementText(state, "scopeDeleteBlockedTitle"),
      payload: preview,
      primaryLabel: managementText(state, "scopeResultOkButton")
    });
    return null;
  }

  var confirmed = await openPreviewModal({
    root: options.root,
    title: managementText(state, "subScopeDeletePreviewTitle"),
    payload: preview,
    changedHeading: "Changed files",
    primaryLabel: managementText(state, "scopeDeleteButton"),
    cancelLabel: managementText(state, "cancelButton")
  });
  if (!confirmed) {
    setMessage(callbacks, "", false);
    return null;
  }

  var appliedPayload;
  try {
    setBusy(callbacks, true);
    setMessage(callbacks, managementText(state, "subScopeDeleteDeleting"), false);
    render(callbacks);
    appliedPayload = await applySubScopeDelete(parentScope, selection.subScope, options.clientOptions);
    setMessage(callbacks, normalizeText(appliedPayload.summary_text), false);
    applied(callbacks, appliedPayload);
  } catch (error) {
    setMessage(callbacks, error && error.message ? error.message : managementText(state, "subScopeDeleteFailed"), true);
    return null;
  } finally {
    setBusy(callbacks, false);
    render(callbacks);
  }

  await openResultModal({
    root: options.root,
    title: managementText(state, "subScopeDeleteResultTitle"),
    payload: appliedPayload,
    primaryLabel: managementText(state, "scopeResultOkButton")
  });
  return appliedPayload;
}
