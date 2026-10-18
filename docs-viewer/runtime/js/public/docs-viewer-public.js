import {
  appendAssetVersion
} from "../shared/docs-viewer-asset-url.js";
import {
  docsViewerImageDetailAdapter
} from "../shared/docs-viewer-image-detail.js";
import {
  CONTENT_DETAIL_BACK_CONTROL_ID,
  withDocsViewerContentDetailDefinitions
} from "../shared/docs-viewer-content-detail-view.js";
import {
  docsViewerMediaDetailAdapter
} from "../shared/docs-viewer-media-detail.js";
import {
  docsViewerTableDetailAdapter
} from "../shared/docs-viewer-table-detail.js";
import {
  mountDocsViewerPublicDocumentExtras
} from "./docs-viewer-public-document-reports.js";
import(appendAssetVersion("../shared/docs-viewer-app-boot.js"))
  .then(function (module) {
    module.startDocsViewerPublicApp({
      contentDetailBackControlId: CONTENT_DETAIL_BACK_CONTROL_ID,
      imageDetailAdapter: docsViewerImageDetailAdapter,
      mediaDetailAdapter: docsViewerMediaDetailAdapter,
      mountDocumentExtras: mountDocsViewerPublicDocumentExtras,
      tableDetailAdapter: docsViewerTableDetailAdapter,
      viewRegistryContributions: withDocsViewerContentDetailDefinitions(null, {
        imageDetailAdapter: docsViewerImageDetailAdapter,
        mediaDetailAdapter: docsViewerMediaDetailAdapter,
        tableDetailAdapter: docsViewerTableDetailAdapter
      })
    });
  });
