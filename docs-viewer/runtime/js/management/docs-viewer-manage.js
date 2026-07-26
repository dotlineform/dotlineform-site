import {
  startDocsViewerManageApp
} from "../shared/docs-viewer-app-boot.js";
import {
  docsViewerDiagramDetailAdapter
} from "../shared/docs-viewer-diagram-detail.js";
import {
  docsViewerInlineMermaidAdapter
} from "./docs-viewer-inline-mermaid.js";
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
import {
  CATALOGUE_TOKEN_CONTROL_ID,
  catalogueTokenControlRenderer,
  createCatalogueTokenMainViewControlHandlers
} from "./source-editor/catalogue-token-contribution.js";

startDocsViewerManageApp({
  controlRendererContributions: Object.assign(
    {},
    createDocsViewerManagementAppControlRenderers(),
    createDocsViewerManagementControlRenderers(),
    { [CATALOGUE_TOKEN_CONTROL_ID]: catalogueTokenControlRenderer }
  ),
  createSourceAdapter: createDocsViewerManagementSourceAdapter,
  diagramDetailAdapter: docsViewerDiagramDetailAdapter,
  viewRegistryContributions: createDocsViewerManagementViewDefinitions(),
  infoPanelDefaultViewByDocumentMode: {
    "markdown-source": "metadata-info",
    "rendered-document": "metadata-info"
  },
  inlineMermaidAdapter: docsViewerInlineMermaidAdapter,
  mainViewControlHandlerContributions: createCatalogueTokenMainViewControlHandlers(),
  managementShellRenderers: createDocsViewerManagementShellRenderers(),
  mountDocumentExtras: mountDocsViewerManageDocumentExtras,
  sourceEditorActionControlIds: [CATALOGUE_TOKEN_CONTROL_ID]
});
