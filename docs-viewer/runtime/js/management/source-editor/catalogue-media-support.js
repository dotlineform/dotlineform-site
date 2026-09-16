import { loadSemanticTokenRegistry } from "./semantic-token-registry.js";
import { normalizeSemanticTokenTargets } from "./semantic-token-targets.js";
import { normalizeDocsViewerMediaPresentation } from "../../shared/docs-viewer-media-presentation.js";
import { catalogueWorkMediaPresentation } from "../../shared/docs-viewer-catalogue-media.js";
import { parseDocsViewerDetailUid } from "../docs-viewer-management-document-subject.js";

/** Map the source document's Catalogue subject to the existing picker identity. */
export function catalogueDocumentSubjectTarget(subject) {
  if (!subject) return null;
  if (subject.kind === "detail") {
    var detail = parseDocsViewerDetailUid(subject.key);
    return { targetType: "work", targetId: detail.workId, detailId: detail.detailId };
  }
  return { targetType: subject.kind, targetId: subject.key, detailId: "" };
}

/** Preserve authored labels while allowing an untouched default to follow selection. */
export function catalogueMediaLinkLabel(target, current, previous, preserveLabel = false) {
  if (preserveLabel && current) return current;
  return !current || (previous && current === previous.title) ? target.title : current;
}

/** Read exact generated Work and Series search identities, independently of documents. */
export async function loadCatalogueMediaSupport(adapter, options = {}) {
  var [registry, payload] = await Promise.all([
    loadSemanticTokenRegistry(options), adapter.readCatalogueMediaTargets()
  ]);
  if (!payload || payload.schema_version !== "docs_semantic_token_target_lookup_v2" || !Array.isArray(payload.targets)) {
    throw new Error("Generated Catalogue targets are unavailable.");
  }
  var targets = normalizeSemanticTokenTargets(payload, registry);
  var identities = new Set();
  if (targets.length !== payload.targets.length || targets.some(function (target) {
    var valid = target.targetType === "work" ? /^\d{5}$/.test(target.targetId)
      : target.targetType === "series" && /^\d{3}$/.test(target.targetId);
    var key = target.targetType + ":" + target.targetId;
    if (target.family !== "catalogue" || !valid || identities.has(key)) return true;
    identities.add(key);
    return false;
  })) throw new Error("Generated Catalogue identities are invalid.");
  return { registry: registry, targets: targets };
}

/** Validate the exact generated Work or Detail before insertion or token inspection. */
export async function readCatalogueMediaPresentation(adapter, workId, detailId = "") {
  var response = await adapter.readCatalogueWork(workId);
  return normalizeDocsViewerMediaPresentation(catalogueWorkMediaPresentation(response, workId, detailId));
}

/** Resolve a token target through its existing provider, with no document or image fallback. */
export async function readCatalogueTokenPresentation(adapter, target, detailId = "") {
  if (target.targetType === "work") return readCatalogueMediaPresentation(adapter, target.targetId, detailId);
  if (target.targetType !== "series" || detailId) throw new Error("Unsupported Catalogue target.");
  var presentation = normalizeDocsViewerMediaPresentation(await adapter.readCatalogueSeriesPresentation(target.targetId));
  if (!presentation || !presentation.gallery || presentation.target.kind !== "catalogue-series"
    || presentation.target.id !== target.targetId) throw new Error("Generated Series identity is mismatched.");
  return presentation;
}
