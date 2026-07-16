import {
  renderDocsViewerManagementShell
} from "./docs-viewer-management-shell-renderer.js";

export function createDocsViewerManagementShellRenderers() {
  return {
    renderShell: renderDocsViewerManagementShell
  };
}
