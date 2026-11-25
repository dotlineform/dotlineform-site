import {
  startDocsViewerManageApp
} from "../shared/docs-viewer-app-boot.js";
import { createDocsViewerBookPane } from "./docs-viewer-book-pane.js";
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
  createDocsViewerTableDetailAdapter
} from "../shared/docs-viewer-table-detail.js";
import {
  createDocsViewerReportPresentationAdapter
} from "../reports/docs-viewer-report-presentation.js";
import { createDocsViewerManagedImageDetailAdapter } from "./docs-viewer-managed-image-detail.js";
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
  mountManagedConfiguredSiteLinks
} from "./docs-viewer-management-configured-site-links.js";
import {
  mountManagedDocsViewerDocumentLinks
} from "./docs-viewer-management-document-links.js";
import {
  DIRECTIVE_ACTIONS_CONTROL_ID,
  createDirectiveActionsMainViewControlHandlers,
  directiveActionsControlRenderer
} from "./source-editor/directive-actions.js";
import { handleSourceBoldControl, SOURCE_BOLD_CONTROL_ID } from "./source-editor/source-editor-bold.js";
import { handleSourceAddDateControl } from "./source-editor/source-editor-date.js";
import { openSavedResults, renderSavedResultsButton } from "./docs-viewer-saved-searches.js";
import {
  mountLocalFolderLinkActivation
} from "./source-editor/local-folder-links.js";

function mountDocsViewerManageExtras(context) {
  var settings = context || {};
  var routeContext = settings.routeContext || {};
  var workspaceConfigState = settings.workspaceConfigState || {};
  mountManagedConfiguredSiteLinks(settings.content, [
    {
      pathPrefix: "/studio/",
      baseUrl: routeContext.studioBaseUrl
    }
  ]);
  mountManagedDocsViewerDocumentLinks(settings.content, {
    currentHref: window.location.href,
    publicViewerBaseUrl: workspaceConfigState.publicViewerBaseUrl,
    viewerUrlForDocument: settings.viewerUrlForDocument
  });
  return Promise.resolve(mountDocsViewerManageDocumentExtras(settings)).then(function (result) {
    mountLocalFolderLinkActivation(settings);
    return result;
  });
}

const managedTableTools = createDocsViewerManagedTableTools();
const managedImageDetailAdapter = createDocsViewerManagedImageDetailAdapter(docsViewerImageDetailAdapter);
const managedTableDetailAdapter = createDocsViewerTableDetailAdapter({
  presentationExtension: managedTableTools.presentationExtension
});
const reportPresentationAdapter = createDocsViewerReportPresentationAdapter({
  presentationExtension: managedTableTools.reportPresentationExtension
});

startDocsViewerManageApp({
  contentDetailBackControlId: CONTENT_DETAIL_BACK_CONTROL_ID,
  controlRendererContributions: Object.assign(
    {},
    createDocsViewerManagementAppControlRenderers(),
    createDocsViewerManagementControlRenderers(),
    createDocsViewerManagedTableToolControlRenderers(),
    {
      "saved-results-button": renderSavedResultsButton,
      [DIRECTIVE_ACTIONS_CONTROL_ID]: directiveActionsControlRenderer
    }
  ),
  createSourceAdapter: createDocsViewerManagementSourceAdapter,
  createDocumentSidePane: createDocsViewerBookPane,
  imageDetailAdapter: docsViewerImageDetailAdapter,
  mediaDetailAdapter: docsViewerMediaDetailAdapter,
  viewRegistryContributions: withDocsViewerManagedTableToolDefinitions(
    withDocsViewerContentDetailDefinitions(
      createDocsViewerManagementViewDefinitions(),
      {
        imageDetailAdapter: managedImageDetailAdapter,
        mediaDetailAdapter: docsViewerMediaDetailAdapter,
        reportPresentationAdapter: reportPresentationAdapter,
        tableDetailAdapter: managedTableDetailAdapter
      }
    )
  ),
  mainViewControlHandlerContributions: Object.assign(
    {},
    createDirectiveActionsMainViewControlHandlers(),
    { [SOURCE_BOLD_CONTROL_ID]: handleSourceBoldControl, "source-add-date": handleSourceAddDateControl },
    managedTableTools.controlHandlers()
  ),
  managementShellRenderers: createDocsViewerManagementShellRenderers(),
  openSavedResults: openSavedResults,
  mountDocumentExtras: mountDocsViewerManageExtras,
  reportPresentationAdapter: reportPresentationAdapter,
  sourceEditorActionControlIds: [DIRECTIVE_ACTIONS_CONTROL_ID, "source-add-date"],
  tableDetailAdapter: managedTableDetailAdapter
});
