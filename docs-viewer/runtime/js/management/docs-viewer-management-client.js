import { normalizeManagedDocumentTarget } from "./docs-viewer-management-document-target.js";

function defaultFetch(url, options) {
  return window.fetch(url, options);
}

export var DOCS_MANAGEMENT_UNAVAILABLE_MESSAGE = "Docs management service unavailable.";

function collectionPayload(payload, options) {
  var settings = options || {};
  return Object.assign({  }, settings.collection ? { collection: settings.collection } : {}, payload || {});
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
    if (payload instanceof FormData) {
      requestOptions.body = payload;
    } else {
      requestOptions.headers["Content-Type"] = "application/json";
      requestOptions.body = JSON.stringify(payload);
    }
  }
  if (settings.cache) requestOptions.cache = settings.cache;

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
        var error = new Error(responsePayload && (responsePayload.error || responsePayload.summary_text) ? (responsePayload.error || responsePayload.summary_text) : "HTTP " + response.status);
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

export function readSelectedDocuments(options) {
  return fetchManagementJson("/docs/selected", "GET", undefined,
    Object.assign({}, options, { cache: "no-store" }));
}

export function setManagedDocSelected(target, selected, options) {
  return fetchManagementJson("/docs/set-selected", "POST", targetPayload(target, { selected: selected }), options);
}

/** Read authoring targets in the authoring workspace; the response supplies ordinary hrefs. */
export function readDocumentLinkTargets(options) {
  return fetchManagementJson("/docs/document-link-targets", "GET", undefined,
    Object.assign({}, options, { cache: "no-store" }));
}

/** Read generated Catalogue targets independently of document scope and association. */
export function readCatalogueMediaTargets( options) {
  return fetchManagementJson("/docs/catalogue-media-targets", "GET", undefined,
    Object.assign({}, options, { cache: "no-cache" }));
}

/** Read the generated rendition policy shared by all Catalogue records. */
export function readCatalogueMediaConfig( options) {
  return fetchManagementJson("/docs/catalogue-media-config", "GET", undefined,
    Object.assign({}, options, { cache: "no-cache" }));
}

/** Read the current generated Work consumer record independently of Document Build. */
export function readCatalogueWork(workId,  options) {
  return fetchManagementJson("/docs/catalogue-work?work_id=" + encodeURIComponent(workId), "GET", undefined,
    Object.assign({}, options, { cache: "no-cache" }));
}

/** Await one Working Catalogue reconciliation and its required document Build. */
export function runCatalogueRegeneration(payload, options) {
  return fetchManagementJson("/docs/catalogue/regenerate", "POST", payload, options);
}

/** Read exact Gallery membership from current Studio-generated output. */
export function readCatalogueGallery(galleryId,  options) {
  return fetchManagementJson("/docs/catalogue-gallery?gallery_id=" + encodeURIComponent(galleryId), "GET", undefined,
    Object.assign({}, options, { cache: "no-cache" }));
}

/** Read the current generated Series relevance map independently of Work membership. */
export function readCatalogueSeriesGalleries(options) {
  return fetchManagementJson("/docs/catalogue-series-galleries", "GET", undefined,
    Object.assign({}, options, { cache: "no-cache" }));
}

export function readManagedDocsIndex(options) {
  return fetchManagementJson("/docs/index-tree", "GET", undefined, options);
}

export function encodeDecodedLocalTarget(target) {
  if (
    typeof target !== "string"
    || !target
    || target !== target.trim()
    || target.startsWith("/")
    || target.includes("\\")
    || Array.from(target).some(function (character) {
      return character.charCodeAt(0) < 32 || character.charCodeAt(0) === 127;
    })
    || /^[A-Za-z][A-Za-z0-9+.-]*:/.test(target)
  ) {
    return "";
  }
  var parts = target.split("/");
  if (parts.some(function (part) { return !part || part === "." || part === ".."; })) {
    return "";
  }
  try {
    return parts.map(function (part) {
      return encodeURIComponent(part).replace(/[!'()*]/g, function (character) {
        return "%" + character.charCodeAt(0).toString(16).toUpperCase();
      });
    }).join("/");
  } catch (_error) {
    return "";
  }
}

export function openLocalTarget(target, options) {
  return fetchManagementJson("/docs/open-local-target", "POST", { target: String(target || "") }, options);
}

export function createManagedDoc(payload, options) {
  return fetchManagementJson("/docs/create", "POST", collectionPayload(payload, options), options);
}

export function refreshManagedDiscovery(options) {
  return fetchManagementJson("/docs/refresh-discovery", "POST", {}, options);
}

/** Rebuild one exact ordinary or collection document from its saved inputs. */
export function rebuildManagedDocument(target, options) {
  return fetchManagementJson("/docs/rebuild-document", "POST", targetPayload(target), options);
}

export function previewManagedDocsStaticHtmlExport(docIds, options) {
  return fetchManagementJson("/docs/export/static-html/preview", "POST", collectionPayload({
    doc_ids: Array.isArray(docIds) ? docIds.slice() : []
  }, options), options);
}

export function applyManagedDocsStaticHtmlExport(preview, options) {
  var plan = preview && typeof preview === "object" ? preview : {};
  var replaceExisting = plan.target_state === "recognized" || plan.target_state === "unrecognized";
  return fetchManagementJson("/docs/export/static-html/apply", "POST", {
    doc_ids: Array.isArray(plan.doc_ids) ? plan.doc_ids.slice() : [],
    export_date: String(plan.export_date || "").trim(),
    plan_revision: String(plan.plan_revision || "").trim(),
    target_revision: String(plan.target_revision || "").trim(),
    confirm: true,
    replace_existing: replaceExisting
  }, options);
}

function targetQuery(target) {
  var normalized = normalizeManagedDocumentTarget(target);
  var query = [];
  if (normalized.collection) {
    query.push("collection=" + encodeURIComponent(normalized.collection));
  }
  query.push("doc_id=" + encodeURIComponent(normalized.doc_id));
  return query.join("&");
}

function targetPayload(target, payload) {
  var fields = payload || {};
  if (typeof fields !== "object" || Array.isArray(fields)) {
    throw new Error("Managed document request payload must be an object.");
  }
  ["scope", "stage", "collection", "doc_id"].forEach(function (key) {
    if (Object.prototype.hasOwnProperty.call(fields, key)) {
      throw new Error("Managed document request payload must not replace target field " + key + ".");
    }
  });
  return Object.assign({}, normalizeManagedDocumentTarget(target), fields);
}

export function readManagedDocSource(target, options) {
  return fetchManagementJson("/docs/source?" + targetQuery(target), "GET", undefined, options);
}

export function readManagedDocSourceContext(target, payload, options) {
  return fetchManagementJson("/docs/source/context", "POST", targetPayload(target, payload), options);
}

export function readManagedDocMetadata(target, options) {
  return fetchManagementJson("/docs/metadata?" + targetQuery(target), "GET", undefined, options);
}

/** Write readiness using the exact document identity and source revision. */
export function setManagedDocDraft(target, payload, options) {
  return fetchManagementJson("/docs/set-draft", "POST", targetPayload(target, payload), options);
}

/** Submit one bounded source/media operation; no upload occurs before this Save. */
export async function saveManagedDocSource(target, payload, options) {
  var selections = payload.media;
  var limits = options.mediaLimits;
  if (selections.some(function (entry) { return entry.file.size > limits.max_file_bytes; })) {
    throw new Error("Selected media exceeds the 64 MiB file limit.");
  }
  if (selections.reduce(function (total, entry) { return total + entry.file.size; }, 0) > limits.max_total_file_bytes) {
    throw new Error("Selected pending media exceeds the combined 64 MiB limit. Reduce the pending media before Save.");
  }
  var metadata = JSON.stringify(targetPayload(target, {
    source_text: payload.source_text,
    media: selections.map(function (entry) {
      return { media_kind: entry.media_kind, body: entry.body, thumbnail: entry.thumbnail,
        replace: entry.replace, preserve_resolution: entry.preserve_resolution };
    })
  }));
  if (new Blob([metadata]).size > limits.max_metadata_bytes) {
    throw new Error("Source Save metadata exceeds the 1 MiB limit.");
  }
  var data = new FormData();
  data.append("metadata", metadata);
  selections.forEach(function (entry, index) { data.append("file_" + index, entry.file, entry.file.name); });
  return fetchManagementJson("/docs/source/save", "POST", data, options);
}

/** Resolve a basename into this document's identity without uploading or storing bytes. */
export function prepareSourceMedia(payload, options) {
  return fetchManagementJson("/docs/source/media", "POST", collectionPayload(payload, options), options);
}

export function deleteManagedDoc(docIds, options) {
  return fetchManagementJson("/docs/delete", "POST", collectionPayload({
    doc_ids: docIds,
    confirm: true
  }, options), options);
}

function collectionDeleteTargetPayload(target, payload) {
  var normalized = normalizeManagedDocumentTarget(target);
  if (!normalized.collection) {
    throw new Error("Collection document delete requires a collection target.");
  }
  return targetPayload(normalized, payload);
}

export function deleteManagedCollectionDoc(target, options) {
  return fetchManagementJson(
    "/docs/delete",
    "POST",
    collectionDeleteTargetPayload(target, {
      confirm: true
    }),
    options
  );
}

export function moveManagedDoc(docId, targetDocId, placement, options) {
  return fetchManagementJson("/docs/move", "POST", collectionPayload({
    doc_id: docId,
    target_doc_id: targetDocId,
    placement: placement
  }, options), options);
}

/** Persist the browser's complete ordered IDs for one ordinary parent's children. */
export function orderManagedDocChildren(parentDocId, childDocIds, options) {
  return fetchManagementJson("/docs/order-children", "POST", {
    parent_doc_id: parentDocId,
    child_doc_ids: childDocIds
  }, options);
}

/** Send one confirmed native document; original filenames remain UTF-8 metadata. */
export function importNativeDoc(file, destination, afterDocId, includePromptMeta, options) {
  var form = new FormData();
  form.append("metadata", JSON.stringify(Object.assign({}, destination, {
    filename: file.name, include_prompt_meta: includePromptMeta,
    ...(afterDocId ? { after_doc_id: afterDocId } : {})
  })));
  form.append("document", file.slice(0, file.size, "application/octet-stream"), "document");
  return fetchManagementJson("/docs/import-doc", "POST", form, options);
}

export function openManagedDocSource(target, editor, options) {
  return fetchManagementJson("/docs/open-source", "POST", targetPayload(target, {
    editor: editor === "vscode" ? "vscode" : "default"
  }), options);
}

export function publishManagedDocs(options) {
  return fetchManagementJson("/docs/publish", "POST", {}, options);
}

export function openRecentExclusions(options) {
  return fetchManagementJson("/docs/open-recent-exclusions", "POST", {}, options);
}
