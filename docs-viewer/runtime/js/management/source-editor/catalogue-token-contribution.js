import {
  DOCS_VIEWER_ACTION_IDS
} from "../docs-viewer-action-definitions.js";
import {
  openCatalogueTokenModal
} from "./catalogue-token-modal.js";
import {
  catalogueTokenAtSelection,
  parseCatalogueTokens
} from "./catalogue-token-parser.js";
import {
  loadSemanticTokenRegistry
} from "./semantic-token-registry.js";

export const CATALOGUE_TOKEN_CONTROL_ID = "source-add-catalogue-token";

export function catalogueTokenControlDefinition() {
  return {
    id: CATALOGUE_TOKEN_CONTROL_ID,
    actionId: DOCS_VIEWER_ACTION_IDS.SOURCE_ADD_CATALOGUE_TOKEN,
    label: "Add catalogue token",
    ownerType: "view",
    ownerViewId: "rendered-document",
    modeIds: ["markdown-source"],
    surfaceId: "main-view",
    appKinds: ["manage"],
    features: ["source-editing"],
    renderer: "source-add-catalogue-token"
  };
}

export function catalogueTokenControlRenderer(context) {
  var button = context.existingRoot;
  if (!button || button.tagName !== "BUTTON") {
    button = context.document.createElement("button");
    button.className = "docsViewer__documentActionButton";
    button.id = "docsViewerManageSourceAddCatalogueTokenButton";
    button.type = "button";
  }
  button.textContent = "📍";
  return button;
}

export function createCatalogueTokenMainViewControlHandlers() {
  return {
    [CATALOGUE_TOKEN_CONTROL_ID]: function (context) {
      var services = context.sourceEditorServices || {};
      var adapter = typeof services.getActiveSourceEditorContextAdapter === "function"
        ? services.getActiveSourceEditorContextAdapter()
        : null;
      if (!adapter || typeof adapter.captureSelection !== "function") {
        if (typeof services.setStatus === "function") {
          services.setStatus("Catalogue tokens are available while editing Markdown source.", true);
        }
        return Promise.resolve(null);
      }
      return openCatalogueTokenModal({
        adapter: adapter,
        capture: adapter.captureSelection(),
        root: context.root
      });
    }
  };
}

export function createCatalogueTokenInfoViewResolver(options = {}) {
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
    return loadRegistry()
      .then(function (registry) {
        var snapshot = adapter.getBufferSnapshot();
        var selection = adapter.getSelection();
        var tokens = parseCatalogueTokens(snapshot.value, { registry: registry });
        return catalogueTokenAtSelection(tokens, selection)
          ? "catalogue-token-info"
          : "metadata-info";
      })
      .catch(function () {
        return "metadata-info";
      });
  };
}
