import { createDocsViewerToolbarIcon } from "../../shared/docs-viewer-toolbar-icon.js";

import {
  DOCS_VIEWER_ACTION_IDS
} from "../docs-viewer-action-definitions.js";
import {
  openCatalogueMediaModal
} from "./catalogue-media-modal.js";

export const CATALOGUE_IMAGE_CONTROL_ID = "source-add-catalogue-image";

export function catalogueImageControlDefinition() {
  return {
    id: CATALOGUE_IMAGE_CONTROL_ID,
    actionId: DOCS_VIEWER_ACTION_IDS.SOURCE_ADD_CATALOGUE_IMAGE,
    label: "Add Catalogue image",
    ownerType: "view",
    ownerViewId: "rendered-document",
    modeIds: ["markdown-source"],
    surfaceId: "main-view",
    appKinds: ["manage"],
    features: ["source-editing"],
    renderer: "source-add-catalogue-image"
  };
}

export function catalogueImageControlRenderer(context) {
  var button = context.existingRoot;
  if (!button || button.tagName !== "BUTTON") {
    button = context.document.createElement("button");
    button.className = "docsViewer__toolbarIconButton";
    button.id = "docsViewerManageSourceAddCatalogueImageButton";
    button.type = "button";
  }
  button.replaceChildren(createDocsViewerToolbarIcon(context.document, "docsViewer__icon--book-image"));
  return button;
}

export function createCatalogueImageMainViewControlHandlers() {
  return {
    [CATALOGUE_IMAGE_CONTROL_ID]: function (context) {
      var services = context.sourceEditorServices || {};
      var adapter = typeof services.getActiveSourceEditorContextAdapter === "function"
        ? services.getActiveSourceEditorContextAdapter()
        : null;
      if (!adapter || typeof adapter.captureSelection !== "function") {
        if (typeof services.setStatus === "function") {
          services.setStatus("Catalogue images are available while editing Markdown source.", true);
        }
        return Promise.resolve(null);
      }
      return openCatalogueMediaModal({
        presentation: "image",
        adapter: adapter,
        capture: adapter.captureSelection(),
        root: context.root
      });
    }
  };
}
