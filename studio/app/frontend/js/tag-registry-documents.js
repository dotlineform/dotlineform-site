// Studio Tag document presentation over the private TDL-1 association product.

const ASSOCIATION_SCHEMA_VERSION = "docs_tag_associations_v1";
const TARGET_KEYS = Object.freeze(["scope", "sub_scope", "doc_id"]);

export function normalizeTagDocumentTarget(raw) {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) return null;
  const keys = Object.keys(raw).sort();
  if (keys.join("\u0000") !== TARGET_KEYS.slice().sort().join("\u0000")) {
    return null;
  }
  const scope = String(raw.scope || "").trim();
  const subScope = String(raw.sub_scope || "").trim();
  const docId = String(raw.doc_id || "").trim();
  if (
    scope !== "analysis"
    || subScope !== "tags"
    || !/^d-\d{8}-\d{6}-[a-f0-9]{6}$/.test(docId)
  ) {
    return null;
  }
  return { scope, sub_scope: subScope, doc_id: docId };
}

export function tagDocumentTargetKey(target) {
  const normalized = normalizeTagDocumentTarget(target);
  return normalized
    ? `${normalized.scope}\u0000${normalized.sub_scope}\u0000${normalized.doc_id}`
    : "";
}

export function sameTagDocumentTarget(left, right) {
  const leftKey = tagDocumentTargetKey(left);
  return Boolean(leftKey && leftKey === tagDocumentTargetKey(right));
}

export function tagRegistryDocumentHref(config, url) {
  const documentUrl = String(url == null ? "" : url).trim();
  const docsViewerBase = String(
    config
      && config.app
      && config.app.runtime
      && config.app.runtime.sites
      && config.app.runtime.sites.docs_viewer
      && config.app.runtime.sites.docs_viewer.base
      || ""
  ).trim();
  if (!docsViewerBase || !documentUrl) return documentUrl;
  try {
    return new URL(documentUrl, `${docsViewerBase.replace(/\/+$/, "")}/`).href;
  } catch (_error) {
    return documentUrl;
  }
}

export function normalizeTagDocumentAssociations(payload) {
  if (
    !payload
    || payload.schema_version !== ASSOCIATION_SCHEMA_VERSION
    || payload.scope !== "analysis"
    || payload.sub_scope !== "tags"
    || !Array.isArray(payload.associations)
  ) {
    throw new Error("Tag document associations are invalid.");
  }
  const byTagId = new Map();
  for (const association of payload.associations) {
    const tagId = String(association && association.tag_id || "").trim().toLowerCase();
    if (!tagId || byTagId.has(tagId) || !Array.isArray(association.documents)) {
      throw new Error("Tag document associations are not canonical.");
    }
    const documents = association.documents.map((document) => {
      const target = normalizeTagDocumentTarget(document && document.target);
      if (!target) throw new Error("Tag association document target is invalid.");
      const locations = Array.isArray(document.locations) ? document.locations : [];
      const manageLocation = locations.find((location) => (
        location && location.access === "manage" && String(location.url || "").trim()
      ));
      return {
        target,
        title: String(document.title || target.doc_id).trim() || target.doc_id,
        url: String(manageLocation && manageLocation.url || "").trim()
      };
    });
    byTagId.set(tagId, documents);
  }
  return byTagId;
}

export function attachTagRegistryDocuments(tags, associationsByTagId) {
  const associations = associationsByTagId instanceof Map
    ? associationsByTagId
    : new Map();
  return (Array.isArray(tags) ? tags : []).map((tag) => {
    const documents = (associations.get(tag && tag.tagId) || []).map((document) => ({
      ...document,
      target: { ...document.target }
    }));
    const primaryAvailable = documents.some((document) => (
      sameTagDocumentTarget(document.target, tag && tag.primaryDocument)
    ));
    return {
      ...tag,
      documents,
      unavailablePrimary: tag && tag.primaryDocument && !primaryAvailable
        ? { target: { ...tag.primaryDocument } }
        : null
    };
  });
}
