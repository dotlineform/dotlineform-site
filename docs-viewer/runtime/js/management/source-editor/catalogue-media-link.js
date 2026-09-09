import { DOCS_VIEWER_ACTION_IDS } from "../docs-viewer-action-definitions.js";
import { openSemanticTextTokenModal } from "./catalogue-token-modal.js";
import { selectedTextForCatalogueTitle } from "./catalogue-token-contract.js";
import { parseCatalogueToken, serializeCatalogueToken } from "./catalogue-token-parser.js";
import { loadSemanticTokenRegistry } from "./semantic-token-registry.js";
import { collectSemanticTokenTargetMatches, normalizeSemanticTokenTargets } from "./semantic-token-targets.js";
import { normalizeDocsViewerMediaPresentation } from "../../shared/docs-viewer-media-presentation.js";
import { catalogueWorkMediaPresentation } from "../../shared/docs-viewer-catalogue-media.js";

export const CATALOGUE_MEDIA_LINK_CONTROL_ID = "source-add-media-view-link";

/** Preserve authored labels while allowing an untouched Work-title default to follow selection. */
export function catalogueMediaLinkLabel(target, current, previous, preserveLabel = false) {
  if (preserveLabel && current) return current;
  return !current || (previous && current === previous.title) ? target.title : current;
}

/** Load the generated Catalogue through the active local source provider. */
export async function loadCatalogueMediaSupport(adapter, options = {}) {
  var [registry, payload] = await Promise.all([
    loadSemanticTokenRegistry(options), adapter.readCatalogueMediaTargets()
  ]);
  if (!payload || payload.schema_version !== "docs_semantic_token_target_lookup_v2" || !Array.isArray(payload.targets)) {
    throw new Error("Generated Catalogue targets are unavailable.");
  }
  var targets = normalizeSemanticTokenTargets(payload, registry);
  if (targets.length !== payload.targets.length || targets.some(function (target) {
    return target.family !== "catalogue" || target.targetType !== "work" || !/^\d{5}$/.test(target.targetId);
  })) throw new Error("Generated Catalogue Work identities are invalid.");
  return { registry: registry, targets: targets };
}

/** Validate the exact generated Work response before insertion or token inspection. */
export async function readCatalogueMediaPresentation(adapter, workId, detailId = "") {
  var response = await adapter.readCatalogueWork(workId);
  return normalizeDocsViewerMediaPresentation(catalogueWorkMediaPresentation(response, workId, detailId));
}

/** Author one Work link; the modal awaits media validation before replacing captured source. */
export function openCatalogueMediaLinkModal(options = {}) {
  var adapter = options.adapter;
  return openSemanticTextTokenModal({
    buildToken: function (value) { return serializeCatalogueToken(Object.assign({}, value, { presentation: "media" })); },
    collectMatches: function (support, query, limit) {
      return collectSemanticTokenTargetMatches(support.targets, query, support.registry, limit);
    },
    familyLabel: "Catalogue Work",
    findByIdentity: function (support, token) {
      return support.targets.find(function (target) { return target.targetId === token.targetId; }) || null;
    },
    loadingMessage: "Loading Catalogue…",
    loadSupport: function (settings) { return loadCatalogueMediaSupport(adapter, settings); },
    modalId: "catalogue-media-link-modal",
    modalTitle: "Add Media View link",
    noMatchesMessage: "No matching Catalogue Works.",
    parseToken: function (raw) {
      var token = parseCatalogueToken(raw);
      return token && token.presentation === "media" ? token : null;
    },
    resultsId: "docsViewerMediaLinkResults",
    resultsLabel: "Catalogue Works",
    searchInputId: "docsViewerMediaLinkSearch",
    searchLabel: "Search Catalogue",
    selectedText: selectedTextForCatalogueTitle,
    targetMeta: function (target) { return target.meta; },
    titleOnSelect: function (target, current, previous) {
      return catalogueMediaLinkLabel(target, current, previous, Boolean(options.capture && options.capture.text.trim()));
    },
    titleInputId: "docsViewerMediaLinkLabel",
    titleLabel: "Link text",
    unavailableMessage: "Generated Catalogue Works are unavailable.",
    validateTarget: function (target) { return readCatalogueMediaPresentation(adapter, target.targetId); }
  }, options);
}

export function catalogueMediaLinkControlDefinition() {
  return {
    id: CATALOGUE_MEDIA_LINK_CONTROL_ID,
    actionId: DOCS_VIEWER_ACTION_IDS.SOURCE_ADD_MEDIA_VIEW_LINK,
    label: "Add Media View link",
    ownerType: "view", ownerViewId: "rendered-document", modeIds: ["markdown-source"],
    surfaceId: "main-view", appKinds: ["manage"], features: ["source-editing"],
    renderer: CATALOGUE_MEDIA_LINK_CONTROL_ID
  };
}

export function catalogueMediaLinkControlRenderer(context) {
  var button = context.existingRoot || context.document.createElement("button");
  button.className = "docsViewer__documentActionButton";
  button.type = "button";
  button.textContent = "Add Media View link";
  return button;
}

export function createCatalogueMediaLinkControlHandlers() {
  return {
    [CATALOGUE_MEDIA_LINK_CONTROL_ID]: function (context) {
      var services = context.sourceEditorServices;
      var adapter = services.getActiveSourceEditorContextAdapter();
      return openCatalogueMediaLinkModal({ adapter: adapter, capture: adapter.captureSelection(), root: context.root });
    }
  };
}
