import {
  appendAssetVersion
} from "../shared/docs-viewer-asset-url.js";
import {
  mountDocsViewerPublicDocumentExtras
} from "./docs-viewer-public-document-reports.js";

import(appendAssetVersion("../shared/docs-viewer-app-boot.js"))
  .then(function (module) {
    module.startDocsViewerPublicApp({
      mountDocumentExtras: mountDocsViewerPublicDocumentExtras
    });
  });
