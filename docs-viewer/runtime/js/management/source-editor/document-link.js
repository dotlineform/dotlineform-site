const DOC_ID = /^d-\d{8}-\d{6}-[a-f0-9]{6}$/;

/** Validate a supplied document location against its exact identity, without reconstructing it. */
function validLocation(record) {
  var target = record.target;
  var href = record.href;
  if (typeof href !== "string" || !href.startsWith("/") || href.startsWith("//")
    || /[\\<>\s]/.test(href)) return false;
  var url = new URL(href, "https://docs.invalid");
  if (url.origin !== "https://docs.invalid" || url.hash) return false;
  var params = url.searchParams;
  if (Array.from(params.keys()).some(function (key) {
    return !["scope", "doc", "subdoc"].includes(key) || params.getAll(key).length !== 1;
  })) return false;
  if (params.has("scope") && params.get("scope") !== target.scope) return false;
  return target.sub_scope
    ? DOC_ID.test(params.get("doc") || "") && params.get("subdoc") === target.doc_id
    : params.get("doc") === target.doc_id && !params.has("subdoc");
}

/** Accept only the mounted editor's scope/stage response and complete exact targets. */
export function normalizeDocumentLinkTargets(payload, context) {
  if (!payload || payload.schema_version !== "docs_document_link_targets_v1"
    || payload.scope !== context.scope || payload.stage !== (context.stage || "")
    || !Array.isArray(payload.sub_scopes) || !Array.isArray(payload.documents)) {
    throw new Error("Document targets do not match the current authoring scope and stage.");
  }
  var subScopes = payload.sub_scopes;
  if (new Set(subScopes).size !== subScopes.length || subScopes.some(function (name) {
    return typeof name !== "string" || !/^[a-z0-9][a-z0-9_-]*$/.test(name);
  })) throw new Error("Document collections are invalid.");
  var seen = new Set();
  var documents = payload.documents.map(function (record) {
    var target = record && record.target;
    if (!target || Object.keys(target).sort().join(",") !== "doc_id,scope,sub_scope"
      || target.scope !== context.scope || !DOC_ID.test(target.doc_id)
      || (target.sub_scope !== "" && !subScopes.includes(target.sub_scope))
      || typeof record.title !== "string" || !record.title.trim() || !validLocation(record)) {
      throw new Error("A document target or location is invalid.");
    }
    var key = target.sub_scope + ":" + target.doc_id;
    if (seen.has(key)) throw new Error("Duplicate document target.");
    seen.add(key);
    return { target: Object.assign({}, target), title: record.title, href: record.href };
  });
  return { subScopes: subScopes.slice(), documents: documents };
}

/** Keep All (null), scope-level (empty string), and exact child filters distinct. */
export function filterDocumentLinkTargets(documents, query, subScope = null) {
  var search = String(query || "").trim().toLowerCase();
  return documents.filter(function (record) {
    return (subScope === null || record.target.sub_scope === subScope)
      && (!search || record.title.toLowerCase().includes(search) || record.target.doc_id.includes(search));
  }).sort(function (left, right) {
    return left.title.localeCompare(right.title) || left.target.sub_scope.localeCompare(right.target.sub_scope)
      || left.target.doc_id.localeCompare(right.target.doc_id);
  });
}

/** Insert the document title as literal inline text and preserve the supplied ordinary href. */
export function documentLinkMarkdown(record) {
  var title = record.title.replace(/\s+/g, " ").trim()
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/([\\[\]`*_])/g, "\\$1");
  return "[" + title + "](<" + record.href + ">)";
}

/** Use the editor's revision-checked replacement only while its exact mount is still active. */
export function insertDocumentLink(adapter, capture, record, isCurrent) {
  if (!isCurrent()) throw new Error("The source document is no longer active. Cancel and try again.");
  if (!adapter.replaceCapturedSelection(capture, documentLinkMarkdown(record))) {
    throw new Error("Markdown source changed while this modal was open. Cancel and try again.");
  }
}
