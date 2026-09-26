import {
  normalizeManagedDocumentCollectionTarget,
  normalizeManagedDocumentTarget
} from "./docs-viewer-management-document-target.js";

function defaultFetch(url, options) {
  return window.fetch(url, options);
}

export var DOCS_MANAGEMENT_UNAVAILABLE_MESSAGE = "Docs management service unavailable.";

function stagedPayload(payload, options) {
  var settings = options || {};
  return Object.assign({ stage: settings.stage }, settings.collection ? { collection: settings.collection } : {}, payload || {});
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

/** Read authoring targets in one exact stage; the response supplies ordinary hrefs. */
export function readDocumentLinkTargets(target, options) {
  var collection = normalizeManagedDocumentCollectionTarget(target);
  var query = "?stage=" + encodeURIComponent(collection.stage);
  if (collection.collection) query += "&collection=" + encodeURIComponent(collection.collection);
  return fetchManagementJson("/docs/document-link-targets" + query, "GET", undefined,
    Object.assign({}, options, { cache: "no-store" }));
}

function catalogueStageQuery(stage) {
  if (!["working", "preview"].includes(stage)) throw new Error("Catalogue stage is required.");
  return "stage=" + encodeURIComponent(stage);
}

/** Read generated Catalogue targets independently of document scope and association. */
export function readCatalogueMediaTargets(stage, options) {
  return fetchManagementJson("/docs/catalogue-media-targets?" + catalogueStageQuery(stage), "GET", undefined, options);
}

/** Read the generated rendition policy shared by all Catalogue records. */
export function readCatalogueMediaConfig(stage, options) {
  return fetchManagementJson("/docs/catalogue-media-config?" + catalogueStageQuery(stage), "GET", undefined,
    Object.assign({}, options, { cache: "no-store" }));
}

/** Read the current generated Work consumer record independently of Document Build. */
export function readCatalogueWork(workId, stage, options) {
  return fetchManagementJson("/docs/catalogue-work?work_id=" + encodeURIComponent(workId) + "&" + catalogueStageQuery(stage), "GET", undefined,
    Object.assign({}, options, { cache: "no-store" }));
}

/** Preview an exact Working Catalogue selection without source writes. */
export function previewCatalogueRegeneration(payload, options) {
  return fetchManagementJson("/docs/catalogue/regenerate-preview", "POST", payload, options);
}

/** Apply the server preview receipt and await source, document and Links outcomes. */
export function applyCatalogueRegeneration(payload, options) {
  return fetchManagementJson("/docs/catalogue/regenerate-apply", "POST", payload, options);
}

/** Read current Series membership without resolving any member Work records. */
export function readCatalogueSeries(seriesId, stage, options) {
  return fetchManagementJson("/docs/catalogue-series?series_id=" + encodeURIComponent(seriesId) + "&" + catalogueStageQuery(stage), "GET", undefined,
    Object.assign({}, options, { cache: "no-store" }));
}

/** Read exact Gallery membership from current Studio-generated output. */
export function readCatalogueGallery(galleryId, stage, options) {
  return fetchManagementJson("/docs/catalogue-gallery?gallery_id=" + encodeURIComponent(galleryId) + "&" + catalogueStageQuery(stage), "GET", undefined,
    Object.assign({}, options, { cache: "no-store" }));
}

export function readManagedDocsIndex(options) {
  var stage = options && options.stage;
  if (!["working", "preview"].includes(stage)) return Promise.reject(new Error("Docs stage is required."));
  return fetchManagementJson("/docs/index-tree?stage=" + encodeURIComponent(stage), "GET", undefined, options);
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
  return fetchManagementJson("/docs/create", "POST", stagedPayload(payload, options), options);
}

export function rebuildManagedDocs(options) {
  return fetchManagementJson("/docs/rebuild", "POST", stagedPayload({}, options), options);
}

export function planManagedDocsPreview(options) {
  return fetchManagementJson("/docs/prepare-preview/plan", "POST", stagedPayload({}, options), options);
}

export function prepareManagedDocsPreview(preview, options) {
  return fetchManagementJson("/docs/prepare-preview/apply", "POST", stagedPayload({
    confirm: true,
    plan_revision: String(preview && preview.plan_revision || "")
  }, options), options);
}

export function previewManagedDocsDeployRepo(options) {
  return fetchManagementJson(
    "/docs/deploy-repo/preview",
    "POST",
    { stage: "preview" },
    options
  );
}

export function applyManagedDocsDeployRepo(preview, options) {
  var plan = preview && typeof preview === "object" ? preview : {};
  return fetchManagementJson("/docs/deploy-repo/apply", "POST", {
    stage: "preview",
    confirm: true,
    preview_revision: String(plan.preview_revision || "").trim(),
    deployment_timestamp: String(plan.deployment_timestamp || "").trim(),
    plan_revision: String(plan.plan_revision || "").trim()
  }, options);
}

export function previewManagedDocsStaticHtmlExport(docIds, options) {
  return fetchManagementJson("/docs/export/static-html/preview", "POST", stagedPayload({
    doc_ids: Array.isArray(docIds) ? docIds.slice() : []
  }, options), options);
}

export function applyManagedDocsStaticHtmlExport(preview, options) {
  var plan = preview && typeof preview === "object" ? preview : {};
  var settings = options || {};
  if (!plan.stage || plan.stage !== settings.stage || Object.prototype.hasOwnProperty.call(plan, "scope")) {
    return Promise.reject(new Error("Snapshot preview stage no longer matches the active stage."));
  }
  var replaceExisting = plan.target_state === "recognized" || plan.target_state === "unrecognized";
  return fetchManagementJson("/docs/export/static-html/apply", "POST", {
    ...(plan.stage ? { stage: plan.stage } : {}),
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
  var query = ["stage=" + encodeURIComponent(normalized.stage)];
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

export function readManagedDocMetadata(target, options) {
  return fetchManagementJson("/docs/metadata?" + targetQuery(target), "GET", undefined, options);
}

/** Write readiness using the exact document identity and source revision. */
export function setManagedDocDraft(target, payload, options) {
  return fetchManagementJson("/docs/set-draft", "POST", targetPayload(target, payload), options);
}

export function assignManagedDocFieldGroup(target, payload, options) {
  return fetchManagementJson(
    "/docs/assign-field-group",
    "POST",
    targetPayload(target, payload),
    options
  );
}

/** Persist one loaded source session; generated output is owned by the watcher. */
export function saveManagedDocSource(target, payload, options) {
  return fetchManagementJson("/docs/source/save", "POST", targetPayload(target, payload), options);
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
  var settings = options || {};
  var kind = encodeURIComponent(String(mediaKind || "").trim());
  var query = ["stage=" + encodeURIComponent(settings.stage), "media_kind=" + kind];
  if (settings.collection) query.push("collection=" + encodeURIComponent(settings.collection));
  var sourceDirectory = String(settings.sourceDirectory || "").trim();
  if (sourceDirectory) {
    query.push("source_directory=" + encodeURIComponent(sourceDirectory));
  }
  return fetchManagementJson(
    "/docs/staged-media-files?" + query.join("&"),
    "GET",
    undefined,
    options
  );
}

export function previewStagedMedia(payload, options) {
  return fetchManagementJson("/docs/staged-media-preview", "POST", stagedPayload(payload, options), options);
}

export function applyStagedMedia(payload, options) {
  return fetchManagementJson("/docs/staged-media-apply", "POST", stagedPayload(payload, options), options);
}

export function readSourceConfigSettings(options) {
  var settings = options || {};
  var path = "/docs/source-config-settings";
  if (settings.stage) path += "?stage=" + encodeURIComponent(settings.stage);
  return fetchManagementJson(path, "GET", undefined, options);
}

export function updateSourceConfigSettings(changes, options) {
  return fetchManagementJson("/docs/source-config-settings", "POST", stagedPayload({
    changes: changes || {}
  }, options), options);
}

export function previewManagedDocDelete(docIds, options) {
  return fetchManagementJson("/docs/delete-preview", "POST", stagedPayload({ doc_ids: docIds }, options), options);
}

export function applyManagedDocDelete(docIds, options) {
  return fetchManagementJson("/docs/delete-apply", "POST", stagedPayload({
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

export function previewManagedCollectionDocDelete(target, options) {
  return fetchManagementJson(
    "/docs/delete-preview",
    "POST",
    collectionDeleteTargetPayload(target, {}),
    options
  );
}

export function applyManagedCollectionDocDelete(target, sourceRevision, options) {
  var revision = String(sourceRevision || "").trim();
  if (!/^sha256:[0-9a-f]{64}$/.test(revision)) {
    throw new Error("Collection document delete requires a sha256 source revision.");
  }
  return fetchManagementJson(
    "/docs/delete-apply",
    "POST",
    collectionDeleteTargetPayload(target, {
      source_revision: revision,
      confirm: true
    }),
    options
  );
}

export function previewCollectionCreate(payload, options) {
  return fetchManagementJson("/docs/collections/create-preview", "POST", Object.assign({ stage: options && options.stage }, payload || {}), options);
}

export function applyCollectionCreate(payload, options) {
  return fetchManagementJson("/docs/collections/create-apply", "POST", Object.assign({ stage: options && options.stage }, payload || {}, {
    confirm: true
  }), options);
}

export function previewCollectionDelete(collection, options) {
  return fetchManagementJson("/docs/collections/delete-preview", "POST", {
    stage: options && options.stage,
    collection: collection
  }, options);
}

export function applyCollectionDelete(collection, options) {
  return fetchManagementJson("/docs/collections/delete-apply", "POST", {
    stage: options && options.stage,
    collection: collection,
    confirm: true
  }, options);
}

export function moveManagedDoc(docId, targetDocId, placement, options) {
  return fetchManagementJson("/docs/move", "POST", stagedPayload({
    doc_id: docId,
    target_doc_id: targetDocId,
    placement: placement
  }, options), options);
}

export function openManagedDocSource(target, editor, options) {
  return fetchManagementJson("/docs/open-source", "POST", targetPayload(target, {
    editor: editor === "vscode" ? "vscode" : "default"
  }), options);
}
