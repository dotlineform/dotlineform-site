function defaultFetch(url, options) {
  return window.fetch(url, options);
}

function scopedPayload(payload, options) {
  var settings = options || {};
  return Object.assign({ scope: settings.scope || "" }, payload || {});
}

export function fetchManagementJson(path, method, payload, options) {
  var settings = options || {};
  var baseUrl = String(settings.baseUrl || "").trim().replace(/\/+$/, "");
  if (!baseUrl) {
    return Promise.reject(new Error(settings.serverNotConfiguredError || "Local docs-management server is not configured."));
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
      throw new Error("HTTP " + response.status);
    }).then(function (responsePayload) {
      if (!response.ok || !responsePayload || !responsePayload.ok) {
        throw new Error(responsePayload && responsePayload.error ? responsePayload.error : "HTTP " + response.status);
      }
      return responsePayload;
    });
  });
}

export function scopeSupportsGeneratedDataReads(capabilities, scope) {
  var scopeCaps = capabilities && capabilities.scopes ? capabilities.scopes[scope] : null;
  return Boolean(
    capabilities &&
    capabilities.generated_data_reads &&
    scopeCaps &&
    scopeCaps.available &&
    scopeCaps.generated_data_reads
  );
}

export function scopeSupportsGeneratedSearchReads(capabilities, scope) {
  var scopeCaps = capabilities && capabilities.scopes ? capabilities.scopes[scope] : null;
  return Boolean(
    capabilities &&
    capabilities.generated_data_reads &&
    scopeCaps &&
    scopeCaps.available &&
    scopeCaps.generated_search_reads
  );
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

export function archiveManagedDoc(docId, options) {
  return fetchManagementJson("/docs/archive", "POST", scopedPayload({ doc_id: docId }, options), options);
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

export function updateManagedDocsViewability(docIds, hidden, options) {
  return fetchManagementJson("/docs/update-viewability-bulk", "POST", scopedPayload({
    doc_ids: docIds,
    hidden: Boolean(hidden)
  }, options), options);
}

export function moveManagedDoc(docId, targetDocId, position, options) {
  return fetchManagementJson("/docs/move", "POST", scopedPayload({
    doc_id: docId,
    target_doc_id: targetDocId,
    position: position
  }, options), options);
}

export function restoreManagedDocMove(focusDocId, records, options) {
  return fetchManagementJson("/docs/restore-move", "POST", scopedPayload({
    focus_doc_id: focusDocId,
    records: records
  }, options), options);
}

export function openManagedDocSource(docId, editor, options) {
  return fetchManagementJson("/docs/open-source", "POST", scopedPayload({
    doc_id: docId,
    editor: editor === "vscode" ? "vscode" : "default"
  }, options), options);
}
