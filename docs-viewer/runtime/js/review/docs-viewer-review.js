import {
  startDocsViewerReviewApp
} from "../shared/docs-viewer-app-boot.js";
import {
  createDocsViewerReturnedPackageProvider
} from "./docs-viewer-returned-package-provider.js";
import {
  createDocsViewerReviewController
} from "./docs-viewer-review-controller.js";

var controller = createDocsViewerReviewController({ document: document, window: window });

startDocsViewerReviewApp({
  createCollectionProvider: function (context) {
    var provider = createDocsViewerReturnedPackageProvider(context);
    controller.setProvider(provider);
    return provider;
  },
  mountDocumentExtras: function (context) {
    controller.mountDocumentExtras(context);
  }
}).then(function () {
  return controller.start();
});
