import {
  appendAssetVersion
} from "../shared/docs-viewer-asset-url.js";
import {
  docsViewerDiagramDetailAdapter
} from "../shared/docs-viewer-diagram-detail.js";
import {
  mountDocsViewerPublicDocumentExtras
} from "./docs-viewer-public-document-reports.js";
import {
  connectDocsViewerPublicThemeOwner,
  createDocsViewerPublicThemedDiagramAdapter
} from "./docs-viewer-public-themed-diagrams.js";

var themedDiagramAdapter = createDocsViewerPublicThemedDiagramAdapter({
  diagramDetailAdapter: docsViewerDiagramDetailAdapter
});
connectDocsViewerPublicThemeOwner({
  adapter: themedDiagramAdapter,
  document: document
});

import(appendAssetVersion("../shared/docs-viewer-app-boot.js"))
  .then(function (module) {
    module.startDocsViewerPublicApp({
      diagramDetailAdapter: docsViewerDiagramDetailAdapter,
      mountDocumentExtras: mountDocsViewerPublicDocumentExtras,
      themedDiagramAdapter: themedDiagramAdapter
    });
  });
