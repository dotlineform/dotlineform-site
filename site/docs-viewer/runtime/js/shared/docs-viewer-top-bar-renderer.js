import {
  renderDocsViewerViewerToolbar
} from "./docs-viewer-viewer-toolbar-renderer.js";

function routeAllowsManagement(routeContext) {
  return Boolean(
    routeContext
    && routeContext.appContext
    && routeContext.appContext.routeAccess
    && routeContext.appContext.routeAccess.managementUi
  );
}

function appendManageToolbarMount(documentRef, topBar) {
  var mount = documentRef.createElement("div");
  mount.className = "docsViewer__manageToolbarMount";
  mount.id = "docsViewerManageActionsMount";
  mount.setAttribute("data-docs-viewer-management-actions-mount", "");
  topBar.appendChild(mount);
  return mount;
}

function appendMainViewToolbarMount(documentRef, topBar) {
  var mount = documentRef.createElement("div");
  mount.className = "docsViewer__mainViewToolbarMount";
  mount.id = "docsViewerMainViewToolbarMount";
  mount.setAttribute("data-docs-viewer-main-view-toolbar-mount", "");
  topBar.appendChild(mount);
  return mount;
}

export function renderDocsViewerTopBar(options) {
  var settings = options || {};
  var documentRef = settings.document || document;
  var mount = settings.mount || null;
  var routeContext = settings.routeContext || null;
  if (!mount) return null;

  mount.replaceChildren();

  var topBar = documentRef.createElement("div");
  topBar.className = "docsViewer__topBar";
  topBar.id = "docsViewerTopBar";

  var viewerToolbar = renderDocsViewerViewerToolbar({
    document: documentRef,
    mount: topBar,
    controlMount: mount,
    routeContext: routeContext
  });
  var mainViewToolbarMount = appendMainViewToolbarMount(documentRef, topBar);
  var manageToolbarMount = routeAllowsManagement(routeContext)
    ? appendManageToolbarMount(documentRef, topBar)
    : null;

  mount.appendChild(topBar);
  return {
    topBar: topBar,
    viewerToolbar: viewerToolbar,
    mainViewToolbarMount: mainViewToolbarMount,
    manageToolbarMount: manageToolbarMount
  };
}
