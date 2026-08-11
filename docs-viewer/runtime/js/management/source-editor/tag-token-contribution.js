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
  openTagTokenModal
} from "./tag-token-modal.js";
import {
  parseTagTokens,
  tagTokenAtSelection
} from "./tag-token-parser.js";

export const TAG_TOKEN_CONTROL_ID = "source-add-tag-token";

export function tagTokenControlDefinition() {
  return {
    id: TAG_TOKEN_CONTROL_ID,
    actionId: DOCS_VIEWER_ACTION_IDS.SOURCE_ADD_TAG_TOKEN,
    label: "Add tag token",
    ownerType: "view",
    ownerViewId: "rendered-document",
    modeIds: ["markdown-source"],
    surfaceId: "main-view",
    appKinds: ["manage"],
    features: ["source-editing"],
    renderer: "source-add-tag-token"
  };
}

export function tagTokenControlRenderer(context) {
  var button = context.existingRoot;
  if (!button || button.tagName !== "BUTTON") {
    button = context.document.createElement("button");
    button.className = "docsViewer__documentActionButton";
    button.id = "docsViewerManageSourceAddTagTokenButton";
    button.type = "button";
  }
  button.textContent = "🏷️";
  return button;
}

export function createTagTokenMainViewControlHandlers() {
  return {
    [TAG_TOKEN_CONTROL_ID]: function (context) {
      var services = context.sourceEditorServices || {};
      var adapter = typeof services.getActiveSourceEditorContextAdapter === "function"
        ? services.getActiveSourceEditorContextAdapter()
        : null;
      if (!adapter || typeof adapter.captureSelection !== "function") {
        if (typeof services.setStatus === "function") {
          services.setStatus("Tag tokens are available while editing Markdown source.", true);
        }
        return Promise.resolve(null);
      }
      return openTagTokenModal({
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
      if (tagTokenAtSelection(parseTagTokens(snapshot.value, { registry: registry }), selection)) {
        return "tag-token-info";
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
