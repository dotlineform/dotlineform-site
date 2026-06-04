import {
  startDocsViewerManageApp
} from "./docs-viewer-app-boot.js";
import {
  mountDocsViewerManageDocumentExtras
} from "./docs-viewer-management-document-reports.js";

startDocsViewerManageApp({
  mountDocumentExtras: mountDocsViewerManageDocumentExtras
});
