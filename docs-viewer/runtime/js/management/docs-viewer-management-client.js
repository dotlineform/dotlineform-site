import {
  normalizeManagedDocumentTarget
} from "./docs-viewer-management-document-target.js";

function defaultFetch(url, options) {
  return window.fetch(url, options);
}

export var DOCS_MANAGEMENT_UNAVAILABLE_MESSAGE = "Docs management service unavailable.";

function scopedPayload(payload, options) {
  var settings = options || {};
  return Object.assign({ scope: settings.scope || "" }, payload || {});
}

export function fetchManagementJson(path, method, payload, options) {
  var settings = options || {};
  var baseUrl = String(settings.baseUrl || "").trim().replace(/\/+$/, "");
  if (!baseUrl) {
    return Promise.reject(new Error(DOCS_MANAGEMENT_UNAVAILABLE_MESSAGE));
  }

  var requestOptions = {
    method: method || "GET",
    headers: {
      Accept: "application/json"
    }
  };
  if (payload !== undefined) {
    requestOptions.headers["Content-Type"] = "application/json";
    requestOptions.body = JSON.stringify(payload);
  }

  var fetchImpl = settings.fetch || defaultFetch;
  return fetchImpl(baseUrl + path, requestOptions).then(function (response) {
    return response.json().catch(function () {
      var error = new Error("HTTP " + response.status);
      error.status = response.status;
      throw error;
    }).then(function (responsePayload) {
      if (
        !response.ok
        || !responsePayload
        || (responsePayload.ok === false && settings.acceptNotOk !== true)
      ) {
        var error = new Error(responsePayload && responsePayload.error ? responsePayload.error : "HTTP " + response.status);
        error.status = response.status;
        error.payload = responsePayload;
        throw error;
      }
      return responsePayload;
    });
  });
}

export function readManagementCapabilities(options) {
  return fetchManagementJson("/capabilities", "GET", undefined, options);
}

export function createManagedDoc(payload, options) {
  return fetchManagementJson("/docs/create", "POST", scopedPayload(payload, options), options);
}

export function rebuildManagedDocs(options) {
  return fetchManagementJson("/docs/rebuild", "POST", scopedPayload({}, options), options);
}

export function confirmManagedDocsPublish(options) {
  return fetchManagementJson("/docs/publish/confirm", "POST", scopedPayload({}, options), options);
}

export function applyManagedDocsPublish(options) {
  return fetchManagementJson("/docs/publish/apply", "POST", scopedPayload({
    confirm: true
  }, options), options);
}

export function applyManagedDocsStaticHtmlExport(options) {
  return fetchManagementJson("/docs/export/static-html/apply", "POST", scopedPayload({
    action: "export"
  }, options), options);
}

function targetQuery(target) {
  var normalized = normalizeManagedDocumentTarget(target);
  var query = ["scope=" + encodeURIComponent(normalized.scope)];
  if (normalized.sub_scope) {
    query.push("sub_scope=" + encodeURIComponent(normalized.sub_scope));
  }
  query.push("doc_id=" + encodeURIComponent(normalized.doc_id));
  return query.join("&");
}

function targetPayload(target, payload) {
  var fields = payload || {};
  if (typeof fields !== "object" || Array.isArray(fields)) {
    throw new Error("Managed document request payload must be an object.");
  }
  ["scope", "sub_scope", "doc_id"].forEach(function (key) {
    if (Object.prototype.hasOwnProperty.call(fields, key)) {
      throw new Error("Managed document request payload must not replace target field " + key + ".");
    }
  });
  return Object.assign({}, normalizeManagedDocumentTarget(target), fields);
}

export function readManagedDocSource(target, options) {
  return fetchManagementJson("/docs/source?" + targetQuery(target), "GET", undefined, options);
}

export function readManagedDocMetadata(target, options) {
  return fetchManagementJson("/docs/metadata?" + targetQuery(target), "GET", undefined, options);
}

export function updateManagedDocMetadata(target, payload, options) {
  return fetchManagementJson(
    "/docs/update-metadata",
    "POST",
    targetPayload(target, payload),
    options
  );
}

export function rebuildManagedDocSource(target, payload, options) {
  return fetchManagementJson("/docs/source/rebuild", "POST", targetPayload(target, payload), options);
}

export function readManagedDiagramSources(target, options) {
  return fetchManagementJson("/docs/diagram-sources?" + targetQuery(target), "GET", undefined, options);
}

export function openManagedDiagramSource(target, payload, options) {
  return fetchManagementJson("/docs/open-diagram-source", "POST", targetPayload(target, Object.assign({
    editor: "vscode"
  }, payload || {})), options);
}

export function listStagedMedia(mediaKind, options) {
  var kind = encodeURIComponent(String(mediaKind || "").trim());
  return fetchManagementJson("/docs/staged-media-files?media_kind=" + kind, "GET", undefined, options);
}

export function previewStagedMedia(payload, options) {
  return fetchManagementJson("/docs/staged-media-preview", "POST", scopedPayload(payload, options), options);
}

export function applyStagedMedia(payload, options) {
  return fetchManagementJson("/docs/staged-media-apply", "POST", scopedPayload(payload, options), options);
}

export function readSourceConfigSettings(options) {
  var settings = options || {};
  var scope = encodeURIComponent(String(settings.scope || "").trim());
  var path = "/docs/source-config-settings" + (scope ? "?scope=" + scope : "");
  return fetchManagementJson(path, "GET", undefined, options);
}

export function updateSourceConfigSettings(changes, options) {
  return fetchManagementJson("/docs/source-config-settings", "POST", scopedPayload({
    changes: changes || {}
  }, options), options);
}

export function previewManagedDocDelete(docIds, options) {
  return fetchManagementJson("/docs/delete-preview", "POST", scopedPayload({ doc_ids: docIds }, options), options);
}

export function applyManagedDocDelete(docIds, options) {
  return fetchManagementJson("/docs/delete-apply", "POST", scopedPayload({
    doc_ids: docIds,
    confirm: true
  }, options), options);
}

function subScopeDeleteTargetPayload(target, payload) {
  var normalized = normalizeManagedDocumentTarget(target);
  if (!normalized.sub_scope) {
    throw new Error("Sub-scope document delete requires a sub-scope target.");
  }
  return targetPayload(normalized, payload);
}

export function previewManagedSubScopeDocDelete(target, options) {
  return fetchManagementJson(
    "/docs/delete-preview",
    "POST",
    subScopeDeleteTargetPayload(target, {}),
    options
  );
}

export function applyManagedSubScopeDocDelete(target, sourceRevision, options) {
  var revision = String(sourceRevision || "").trim();
  if (!/^sha256:[0-9a-f]{64}$/.test(revision)) {
    throw new Error("Sub-scope document delete requires a sha256 source revision.");
  }
  return fetchManagementJson(
    "/docs/delete-apply",
    "POST",
    subScopeDeleteTargetPayload(target, {
      source_revision: revision,
      confirm: true
    }),
    options
  );
}

export function previewScopeCreate(payload, options) {
  return fetchManagementJson("/docs/scopes/create-preview", "POST", payload || {}, options);
}

export function applyScopeCreate(payload, options) {
  return fetchManagementJson("/docs/scopes/create-apply", "POST", Object.assign({}, payload || {}, {
    confirm: true
  }), options);
}

export function previewScopeRename(scopeId, newScopeId, options) {
  return fetchManagementJson("/docs/scopes/rename-preview", "POST", {
    scope_id: scopeId,
    new_scope_id: newScopeId
  }, options);
}

export function applyScopeRename(scopeId, newScopeId, options) {
  return fetchManagementJson("/docs/scopes/rename-apply", "POST", {
    scope_id: scopeId,
    new_scope_id: newScopeId,
    confirm: true
  }, options);
}

export function previewScopeDelete(scopeId, options) {
  return fetchManagementJson("/docs/scopes/delete-preview", "POST", {
    scope_id: scopeId
  }, options);
}

export function applyScopeDelete(scopeId, options) {
  return fetchManagementJson("/docs/scopes/delete-apply", "POST", {
    scope_id: scopeId,
    confirm: true
  }, options);
}

export function previewSubScopeCreate(payload, options) {
  return fetchManagementJson("/docs/scopes/sub-scopes/create-preview", "POST", payload || {}, options);
}

export function applySubScopeCreate(payload, options) {
  return fetchManagementJson("/docs/scopes/sub-scopes/create-apply", "POST", Object.assign({}, payload || {}, {
    confirm: true
  }), options);
}

export function previewSubScopeDelete(parentScope, subScope, options) {
  return fetchManagementJson("/docs/scopes/sub-scopes/delete-preview", "POST", {
    parent_scope: parentScope,
    sub_scope: subScope
  }, options);
}

export function applySubScopeDelete(parentScope, subScope, options) {
  return fetchManagementJson("/docs/scopes/sub-scopes/delete-apply", "POST", {
    parent_scope: parentScope,
    sub_scope: subScope,
    confirm: true
  }, options);
}

export function moveManagedDoc(docId, parentId, options) {
  return fetchManagementJson("/docs/move", "POST", scopedPayload({
    doc_id: docId,
    parent_id: parentId
  }, options), options);
}

export function previewManagedDocumentTransfer(docIds, targetScope, transferMode, includeDescendants, options) {
  var settings = Object.assign({}, options || {}, { acceptNotOk: true });
  return fetchManagementJson("/docs/document-transfer-preview", "POST", scopedPayload({
    doc_ids: docIds,
    target_scope: targetScope,
    transfer_mode: transferMode,
    include_descendants: includeDescendants === true
  }, settings), settings);
}

export function applyManagedDocumentTransfer(applyPlan, options) {
  return fetchManagementJson("/docs/document-transfer-apply", "POST", scopedPayload({
    apply_plan: applyPlan,
    confirm: true
  }, options), options);
}

export function openManagedDocSource(target, editor, options) {
  return fetchManagementJson("/docs/open-source", "POST", targetPayload(target, {
    editor: editor === "vscode" ? "vscode" : "default"
  }), options);
}
