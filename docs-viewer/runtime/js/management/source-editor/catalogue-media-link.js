import { createDocsViewerToolbarIcon } from "../../shared/docs-viewer-toolbar-icon.js";

import { DOCS_VIEWER_ACTION_IDS } from "../docs-viewer-action-definitions.js";
import { openCatalogueMediaModal } from "./catalogue-media-modal.js";

export const CATALOGUE_MEDIA_LINK_CONTROL_ID = "source-add-media-view-link";

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
  button.className = "docsViewer__toolbarIconButton";
  button.type = "button";
  button.replaceChildren(createDocsViewerToolbarIcon(context.document, "docsViewer__icon--image-plus"));
  return button;
}

export function createCatalogueMediaLinkControlHandlers() {
  return {
    [CATALOGUE_MEDIA_LINK_CONTROL_ID]: function (context) {
      var services = context.sourceEditorServices;
      var adapter = services.getActiveSourceEditorContextAdapter();
      return openCatalogueMediaModal({ presentation: "media", adapter: adapter, capture: adapter.captureSelection(), root: context.root });
    }
  };
}
