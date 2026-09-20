import {
  renderDocsViewerViewerToolbar
} from "./docs-viewer-viewer-toolbar-renderer.js";
import {
  renderDocsViewerThemeToggle
} from "./docs-viewer-theme.js";
import { createDocsViewerToolbarIcon } from "./docs-viewer-toolbar-icon.js";

function appendReaderTopRow(documentRef, mount, topBar, routeContext) {
  var row = documentRef.createElement("div");
  row.className = "docsViewer__topRow";
  var homeLink = documentRef.createElement("a");
  homeLink.className = "docsViewer__homeLink";
  homeLink.setAttribute("aria-label", "dotlineform home");
  homeLink.title = "dotlineform home";
  homeLink.appendChild(createDocsViewerToolbarIcon(documentRef, "docsViewer__icon--dlf-home"));
  var homeUrl = new URL(routeContext.routeViewerBaseUrl, documentRef.baseURI);
  if (routeContext.appContext.kind === "manage") {
    homeUrl.searchParams.set("stage", routeContext.viewerStage);
  }
  homeLink.href = homeUrl.pathname + homeUrl.search;
  row.append(homeLink, topBar, renderDocsViewerThemeToggle(documentRef));
  mount.appendChild(row);
}

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
  mount.className = "docsViewer__manageToolbarMount docsViewer__manageRow";
  mount.id = "docsViewerManageRow";
  mount.hidden = true;
  mount.setAttribute("data-docs-viewer-management-actions-mount", "");
  mount.setAttribute("data-docs-viewer-control-surface-mount", "app-management");
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

/** Compose shared Public/Manage reader chrome around route-owned toolbar mounts. */
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

  var appKind = routeContext && routeContext.appContext && routeContext.appContext.kind;
  if (appKind === "public" || appKind === "manage") {
    appendReaderTopRow(documentRef, mount, topBar, routeContext);
  } else {
    mount.appendChild(topBar);
  }
  return {
    topBar: topBar,
    viewerToolbar: viewerToolbar,
    mainViewToolbarMount: mainViewToolbarMount,
    manageToolbarMount: manageToolbarMount
  };
}
