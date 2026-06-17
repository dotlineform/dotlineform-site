import {
  appendAssetVersion
} from "../shared/docs-viewer-asset-url.js";

import(appendAssetVersion("../shared/docs-viewer-app-boot.js"))
  .then(function (module) {
    module.startDocsViewerPublicApp();
  });
