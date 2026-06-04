import {
  startDocsViewerManageApp
} from "./docs-viewer-app-boot.js";
import {
  mountDocsViewerManageDocumentExtras
} from "./docs-viewer-management-document-reports.js";
import {
  createDocsViewerManagementHostedViews
} from "./docs-viewer-management-hosted-views.js";

startDocsViewerManageApp({
  entrypointHostedViews: createDocsViewerManagementHostedViews(),
  mountDocumentExtras: mountDocsViewerManageDocumentExtras
});
