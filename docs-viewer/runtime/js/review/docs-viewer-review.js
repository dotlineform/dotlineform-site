import {
  startDocsViewerReviewApp
} from "../shared/docs-viewer-app-boot.js";
import {
  createDocsViewerReturnedPackageProvider
} from "./docs-viewer-returned-package-provider.js";
import {
  createDocsViewerReviewController
} from "./docs-viewer-review-controller.js";
import {
  createDocsViewerReviewDocumentControls
} from "./docs-viewer-review-document-controls.js";
import {
  createDocsViewerReviewViewDefinitions
} from "./docs-viewer-review-hosted-views.js";

var controller = createDocsViewerReviewController({ document: document, window: window });
var documentControls = createDocsViewerReviewDocumentControls();

startDocsViewerReviewApp({
  createCollectionProvider: function (context) {
    var provider = createDocsViewerReturnedPackageProvider(context);
    controller.setProvider(provider);
    return provider;
  },
  mountDocumentExtras: function (context) {
    controller.mountDocumentExtras(context);
    documentControls.applyRequestedMode();
  },
  renderDocumentControls: documentControls.render,
  viewRegistryContributions: createDocsViewerReviewViewDefinitions()
}).then(function () {
  return controller.start();
});
