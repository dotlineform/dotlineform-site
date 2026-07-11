import {
  startDocsViewerManageApp
} from "../shared/docs-viewer-app-boot.js";
import {
  mountDocsViewerManageDocumentExtras
} from "./docs-viewer-management-document-reports.js";
import {
  createDocsViewerManagementDocumentDisplayModes,
  createDocsViewerManagementHostedViews
} from "./docs-viewer-management-hosted-views.js";
import {
  createDocsViewerManagementShellRenderers
} from "./docs-viewer-management-shell-composition.js";
import {
  createDocsViewerManagementSourceAdapter
} from "./docs-viewer-management-source-adapter.js";

startDocsViewerManageApp({
  createSourceAdapter: createDocsViewerManagementSourceAdapter,
  documentDisplayModes: createDocsViewerManagementDocumentDisplayModes(),
  entrypointHostedViews: createDocsViewerManagementHostedViews(),
  infoPanelDefaultViewByDocumentMode: {
    "markdown-source": "semantic-token-picker",
    "rendered-document": "metadata-info"
  },
  managementShellRenderers: createDocsViewerManagementShellRenderers(),
  mountDocumentExtras: mountDocsViewerManageDocumentExtras
});
