import { buildViewerUrl } from "../shared/docs-viewer-router.js";
import { normalizeDocsViewerAuthoringSubject } from "./docs-viewer-management-document-subject.js";

const DOC_ID_PATTERN = /^d-[0-9]{8}-[0-9]{6}-[0-9a-f]{6}$/;

/** Derive exact Work links from private rows; ambiguous identities fail visibly. */
function catalogueDocumentLinks(payload, route) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)
    || Object.prototype.hasOwnProperty.call(payload, "stage")
    || Object.prototype.hasOwnProperty.call(payload, "scope")
    || typeof payload.subject_generation !== "string"
    || !/^sha256:[0-9a-f]{64}$/.test(payload.subject_generation)
    || !Array.isArray(payload.docs)) {
    throw new Error("Working Catalogue management manifest is invalid.");
  }
  const links = new Map();
  const docIds = new Set();
  payload.docs.forEach((row) => {
    if (!row || typeof row.doc_id !== "string" || !DOC_ID_PATTERN.test(row.doc_id)
      || docIds.has(row.doc_id) || typeof row.title !== "string") {
      throw new Error("Catalogue management manifest has an invalid or duplicate document.");
    }
    docIds.add(row.doc_id);
    const subject = normalizeDocsViewerAuthoringSubject(row.authoring_subject);
    if (subject.state !== "valid" || subject.kind !== "work") return;
    if (typeof subject.key !== "string" || !/^[0-9]{5}$/.test(subject.key)
      || links.has(subject.key)) {
      throw new Error("Catalogue Work mapping requires one exact document.");
    }
    links.set(subject.key, buildViewerUrl({ ...route, reportParams: { subdoc: row.doc_id } }));
  });
  return links;
}

/** Read Catalogue's management manifest and compose links with its configured host.
 * Missing Work entries remain absent; configuration, read and ambiguous identity errors propagate.
 */
export async function loadWorkingCatalogueDocumentLinks(options) {
  const working = options.workspaceConfig;
  const catalogue = working && working.collections.find((collection) => collection.collection === "catalogue");
  if (!catalogue || !catalogue.manifestUrl || !DOC_ID_PATTERN.test(catalogue.reportHostDocId)
    || !working.viewerBaseUrl) {
    throw new Error("Working Catalogue is not configured.");
  }
  const url = new URL(catalogue.manifestUrl, options.document.baseURI);
  const fetchJson = options.fetch || fetch;
  const response = await fetchJson(url.toString(), { headers: { Accept: "application/json" } });
  if (!response.ok) throw new Error("Failed to load Catalogue management manifest.");
  return catalogueDocumentLinks(await response.json(), {
    viewerBaseUrl: working.viewerBaseUrl,
    origin: new URL(options.document.baseURI).origin,
    docId: catalogue.reportHostDocId
  });
}
