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
      if (!response.ok || !responsePayload || !responsePayload.ok) {
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

export function updateManagedDocMetadata(payload, options) {
  return fetchManagementJson("/docs/update-metadata", "POST", scopedPayload(payload, options), options);
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

export function readManagedDocSource(docId, options) {
  var settings = options || {};
  var scope = encodeURIComponent(String(settings.scope || "").trim());
  var targetDocId = encodeURIComponent(String(docId || "").trim());
  var query = [];
  if (scope) query.push("scope=" + scope);
  if (targetDocId) query.push("doc_id=" + targetDocId);
  return fetchManagementJson("/docs/source" + (query.length ? "?" + query.join("&") : ""), "GET", undefined, options);
}

export function rebuildManagedDocSource(payload, options) {
  return fetchManagementJson("/docs/source/rebuild", "POST", scopedPayload(payload, options), options);
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

export function previewManagedDocDelete(docId, options) {
  return fetchManagementJson("/docs/delete-preview", "POST", scopedPayload({ doc_id: docId }, options), options);
}

export function applyManagedDocDelete(docId, options) {
  return fetchManagementJson("/docs/delete-apply", "POST", scopedPayload({
    doc_id: docId,
    confirm: true
  }, options), options);
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

export function updateManagedDocsViewability(docIds, viewable, options) {
  return fetchManagementJson("/docs/update-viewability-bulk", "POST", scopedPayload({
    doc_ids: docIds,
    viewable: Boolean(viewable)
  }, options), options);
}

export function moveManagedDoc(docId, parentId, options) {
  return fetchManagementJson("/docs/move", "POST", scopedPayload({
    doc_id: docId,
    parent_id: parentId
  }, options), options);
}

export function openManagedDocSource(docId, editor, options) {
  return fetchManagementJson("/docs/open-source", "POST", scopedPayload({
    doc_id: docId,
    editor: editor === "vscode" ? "vscode" : "default"
  }, options), options);
}
