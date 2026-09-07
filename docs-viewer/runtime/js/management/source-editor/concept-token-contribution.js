import {
  DOCS_VIEWER_ACTION_IDS
} from "../docs-viewer-action-definitions.js";
import {
  catalogueTokenAtSelection,
  parseCatalogueTokens
} from "./catalogue-token-parser.js";
import {
  loadSemanticTokenRegistry
} from "./semantic-token-registry.js";
import {
  openConceptTokenModal
} from "./concept-token-modal.js";
import {
  parseConceptTokens,
  conceptTokenAtSelection
} from "./concept-token-parser.js";

export const CONCEPT_TOKEN_CONTROL_ID = "source-add-concept-token";

export function conceptTokenControlDefinition() {
  return {
    id: CONCEPT_TOKEN_CONTROL_ID,
    actionId: DOCS_VIEWER_ACTION_IDS.SOURCE_ADD_CONCEPT_TOKEN,
    label: "Add concept token",
    ownerType: "view",
    ownerViewId: "rendered-document",
    modeIds: ["markdown-source"],
    surfaceId: "main-view",
    appKinds: ["manage"],
    features: ["source-editing"],
    renderer: "source-add-concept-token"
  };
}

export function conceptTokenControlRenderer(context) {
  var button = context.existingRoot;
  if (!button || button.tagName !== "BUTTON") {
    button = context.document.createElement("button");
    button.className = "docsViewer__documentActionButton";
    button.id = "docsViewerManageSourceAddConceptTokenButton";
    button.type = "button";
  }
  button.textContent = "🏷️";
  return button;
}

export function createConceptTokenMainViewControlHandlers() {
  return {
    [CONCEPT_TOKEN_CONTROL_ID]: function (context) {
      var services = context.sourceEditorServices || {};
      var adapter = typeof services.getActiveSourceEditorContextAdapter === "function"
        ? services.getActiveSourceEditorContextAdapter()
        : null;
      if (!adapter || typeof adapter.captureSelection !== "function") {
        if (typeof services.setStatus === "function") {
          services.setStatus("Concept tokens are available while editing Markdown source.", true);
        }
        return Promise.resolve(null);
      }
      return openConceptTokenModal({
        adapter: adapter,
        capture: adapter.captureSelection(),
        root: context.root
      });
    }
  };
}

export function createSemanticTokenInfoViewResolver(options = {}) {
  var registryPromise = null;
  function loadRegistry() {
    if (!registryPromise) {
      registryPromise = loadSemanticTokenRegistry({ fetch: options.fetch });
    }
    return registryPromise;
  }
  return function (adapter) {
    if (
      !adapter
      || typeof adapter.getBufferSnapshot !== "function"
      || typeof adapter.getSelection !== "function"
    ) return Promise.resolve("metadata-info");
    return loadRegistry().then(function (registry) {
      var snapshot = adapter.getBufferSnapshot();
      var selection = adapter.getSelection();
      if (conceptTokenAtSelection(parseConceptTokens(snapshot.value, { registry: registry }), selection)) {
        return "concept-token-info";
      }
      if (
        catalogueTokenAtSelection(
          parseCatalogueTokens(snapshot.value, { registry: registry }),
          selection
        )
      ) return "catalogue-token-info";
      return "metadata-info";
    }).catch(function () {
      return "metadata-info";
    });
  };
}
