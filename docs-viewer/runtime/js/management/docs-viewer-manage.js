import {
  startDocsViewerManageApp
} from "../shared/docs-viewer-app-boot.js";
import {
  docsViewerInlineMermaidAdapter
} from "../shared/docs-viewer-inline-mermaid.js";
import {
  mountDocsViewerManageDocumentExtras
} from "./docs-viewer-management-document-reports.js";
import {
  createDocsViewerManagementViewDefinitions
} from "./docs-viewer-management-hosted-views.js";
import {
  createDocsViewerManagementShellRenderers
} from "./docs-viewer-management-shell-composition.js";
import {
  createDocsViewerManagementControlRenderers
} from "./docs-viewer-management-control-renderers.js";
import {
  createDocsViewerManagementAppControlRenderers
} from "./docs-viewer-management-actions-renderer.js";
import {
  createDocsViewerManagementSourceAdapter
} from "./docs-viewer-management-source-adapter.js";

startDocsViewerManageApp({
  controlRendererContributions: Object.assign(
    {},
    createDocsViewerManagementAppControlRenderers(),
    createDocsViewerManagementControlRenderers()
  ),
  createSourceAdapter: createDocsViewerManagementSourceAdapter,
  viewRegistryContributions: createDocsViewerManagementViewDefinitions(),
  infoPanelDefaultViewByDocumentMode: {
    "markdown-source": "semantic-token-picker",
    "rendered-document": "metadata-info"
  },
  inlineMermaidAdapter: docsViewerInlineMermaidAdapter,
  managementShellRenderers: createDocsViewerManagementShellRenderers(),
  mountDocumentExtras: mountDocsViewerManageDocumentExtras
});
