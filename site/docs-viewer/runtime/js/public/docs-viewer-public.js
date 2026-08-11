import {
  appendAssetVersion
} from "../shared/docs-viewer-asset-url.js";
import {
  docsViewerDiagramDetailAdapter
} from "../shared/docs-viewer-diagram-detail.js";
import {
  CONTENT_DETAIL_BACK_CONTROL_ID,
  withDocsViewerContentDetailDefinitions
} from "../shared/docs-viewer-content-detail-view.js";
import {
  docsViewerTableDetailAdapter
} from "../shared/docs-viewer-table-detail.js";
import {
  createDocsViewerReportPresentationAdapter
} from "../shared/docs-viewer-report-presentation.js";
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
var reportPresentationAdapter = createDocsViewerReportPresentationAdapter();
connectDocsViewerPublicThemeOwner({
  adapter: themedDiagramAdapter,
  document: document
});

import(appendAssetVersion("../shared/docs-viewer-app-boot.js"))
  .then(function (module) {
    module.startDocsViewerPublicApp({
      contentDetailBackControlId: CONTENT_DETAIL_BACK_CONTROL_ID,
      diagramDetailAdapter: docsViewerDiagramDetailAdapter,
      mountDocumentExtras: mountDocsViewerPublicDocumentExtras,
      reportPresentationAdapter: reportPresentationAdapter,
      tableDetailAdapter: docsViewerTableDetailAdapter,
      viewRegistryContributions: withDocsViewerContentDetailDefinitions(null, {
        diagramDetailAdapter: docsViewerDiagramDetailAdapter,
        reportPresentationAdapter: reportPresentationAdapter,
        tableDetailAdapter: docsViewerTableDetailAdapter
      }),
      themedDiagramAdapter: themedDiagramAdapter
    });
  });
