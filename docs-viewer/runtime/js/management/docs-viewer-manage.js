import {
  startDocsViewerManageApp
} from "../shared/docs-viewer-app-boot.js";
import {
  docsViewerDiagramDetailAdapter
} from "../shared/docs-viewer-diagram-detail.js";
import {
  CONTENT_DETAIL_BACK_CONTROL_ID,
  withDocsViewerContentDetailDefinitions
} from "../shared/docs-viewer-content-detail-view.js";
import {
  createDocsViewerTableDetailAdapter
} from "../shared/docs-viewer-table-detail.js";
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
  createDocsViewerManagedTableToolControlRenderers,
  createDocsViewerManagedTableTools,
  withDocsViewerManagedTableToolDefinitions
} from "./docs-viewer-managed-table-tools.js";
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
  createCatalogueTokenInfoViewResolver,
  createCatalogueTokenMainViewControlHandlers
} from "./source-editor/catalogue-token-contribution.js";
import {
  DIRECTIVE_ACTIONS_CONTROL_ID,
  createDirectiveActionsMainViewControlHandlers,
  directiveActionsControlRenderer
} from "./source-editor/directive-actions.js";
import {
  mountSemanticTokenTargetLinks
} from "./source-editor/semantic-token-targets.js";
import {
  mountLocalFolderLinkActivation
} from "./source-editor/local-folder-links.js";
import {
  SUBJECT_LINK_CONTROL_ID,
  createSubjectLinkMainViewControlHandlers,
  subjectLinkControlRenderer
} from "./source-editor/subject-link-contribution.js";

function mountDocsViewerManageExtras(context) {
  var settings = context || {};
  var routeContext = settings.routeContext || {};
  return Promise.resolve(mountDocsViewerManageDocumentExtras(settings)).then(function (result) {
    mountSemanticTokenTargetLinks(
      settings.content,
      routeContext.publicPreviewBase
    );
    mountLocalFolderLinkActivation(settings);
    return result;
  });
}

const managedTableTools = createDocsViewerManagedTableTools();
const managedTableDetailAdapter = createDocsViewerTableDetailAdapter({
  presentationExtension: managedTableTools.presentationExtension
});

startDocsViewerManageApp({
  contentDetailBackControlId: CONTENT_DETAIL_BACK_CONTROL_ID,
  controlRendererContributions: Object.assign(
    {},
    createDocsViewerManagementAppControlRenderers(),
    createDocsViewerManagementControlRenderers(),
    createDocsViewerManagedTableToolControlRenderers(),
    {
      [CATALOGUE_TOKEN_CONTROL_ID]: catalogueTokenControlRenderer,
      [SUBJECT_LINK_CONTROL_ID]: subjectLinkControlRenderer,
      [DIRECTIVE_ACTIONS_CONTROL_ID]: directiveActionsControlRenderer
    }
  ),
  createSourceAdapter: createDocsViewerManagementSourceAdapter,
  diagramDetailAdapter: docsViewerDiagramDetailAdapter,
  viewRegistryContributions: withDocsViewerManagedTableToolDefinitions(
    withDocsViewerContentDetailDefinitions(
      createDocsViewerManagementViewDefinitions(),
      {
        diagramDetailAdapter: docsViewerDiagramDetailAdapter,
        tableDetailAdapter: managedTableDetailAdapter
      }
    )
  ),
  infoPanelAutoOpenDocumentModes: ["markdown-source"],
  infoPanelDefaultViewByDocumentMode: {
    "markdown-source": "metadata-info",
    "rendered-document": "metadata-info"
  },
  inlineMermaidAdapter: docsViewerInlineMermaidAdapter,
  mainViewControlHandlerContributions: Object.assign(
    {},
    createCatalogueTokenMainViewControlHandlers(),
    createSubjectLinkMainViewControlHandlers(),
    createDirectiveActionsMainViewControlHandlers(),
    managedTableTools.controlHandlers()
  ),
  managementShellRenderers: createDocsViewerManagementShellRenderers(),
  mountDocumentExtras: mountDocsViewerManageExtras,
  sourceEditorActionControlIds: [
    CATALOGUE_TOKEN_CONTROL_ID,
    SUBJECT_LINK_CONTROL_ID,
    DIRECTIVE_ACTIONS_CONTROL_ID
  ],
  sourceEditorInfoViewResolver: createCatalogueTokenInfoViewResolver(),
  tableDetailAdapter: managedTableDetailAdapter
});
