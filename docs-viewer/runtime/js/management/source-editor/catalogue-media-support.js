import { loadSemanticTokenRegistry } from "./semantic-token-registry.js";
import { normalizeSemanticTokenTargets } from "./semantic-token-targets.js";

/** Map the source document's Catalogue subject to the existing picker identity. */
export function catalogueDocumentSubjectTarget(subject) {
  if (!subject || subject.kind !== "work") return null;
  return { targetType: "work", targetId: subject.key };
}

/** Preserve authored labels while allowing an untouched default to follow selection. */
export function catalogueMediaLinkLabel(target, current, previous, preserveLabel = false) {
  if (preserveLabel && current) return current;
  return !current || (previous && current === previous.title) ? target.title : current;
}

/** Read exact generated Work and Gallery search identities, independently of documents. */
export async function loadCatalogueMediaSupport(adapter, options = {}) {
  var [registry, payload] = await Promise.all([
    loadSemanticTokenRegistry(options), adapter.readCatalogueMediaTargets()
  ]);
  if (!payload || payload.schema_version !== "docs_semantic_token_target_lookup_v2" || !Array.isArray(payload.targets)) {
    throw new Error("Generated Catalogue targets are unavailable.");
  }
  var targets = normalizeSemanticTokenTargets(payload, registry);
  return { registry: registry, targets: targets };
}
