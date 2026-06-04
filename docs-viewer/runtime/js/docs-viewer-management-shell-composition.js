import {
  renderDocsViewerManagementActions
} from "./docs-viewer-management-actions-renderer.js";
import {
  renderDocsViewerManagementDocumentActions
} from "./docs-viewer-management-document-actions-renderer.js";
import {
  renderDocsViewerManagementShell
} from "./docs-viewer-management-shell-renderer.js";

export function createDocsViewerManagementShellRenderers() {
  return {
    renderActions: renderDocsViewerManagementActions,
    renderDocumentActions: renderDocsViewerManagementDocumentActions,
    renderShell: renderDocsViewerManagementShell
  };
}
