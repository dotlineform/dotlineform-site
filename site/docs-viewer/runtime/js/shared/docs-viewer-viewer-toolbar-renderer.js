import {
  docsViewerRouteFeatureEnabled
} from "./docs-viewer-route-features.js";

function routeFeatureEnabled(routeContext, featureId) {
  var appContext = routeContext && routeContext.appContext ? routeContext.appContext : {};
  return docsViewerRouteFeatureEnabled(appContext.featurePolicy, featureId);
}

function appendRecentButton(documentRef, toolbar) {
  var button = documentRef.createElement("button");
  button.className = "docsViewer__actionButton docsViewer__recentButton";
  button.type = "button";
  button.id = "docsViewerRecentButton";
  button.setAttribute("aria-pressed", "false");
  button.textContent = "recently added";
  toolbar.appendChild(button);
}

function appendSearchInput(documentRef, toolbar, mount) {
  var ariaLabel = String(mount && mount.dataset.searchAriaLabel || "Search docs");
  var placeholder = String(mount && mount.dataset.searchPlaceholder || "search docs");

  var wrap = documentRef.createElement("div");
  wrap.className = "docsViewer__search";

  var label = documentRef.createElement("label");
  label.className = "visually-hidden";
  label.setAttribute("for", "docsViewerSearchInput");
  label.textContent = ariaLabel;

  var input = documentRef.createElement("input");
  input.className = "docsViewer__searchInput";
  input.id = "docsViewerSearchInput";
  input.type = "search";
  input.autocomplete = "off";
  input.spellcheck = false;
  input.placeholder = placeholder;
  input.setAttribute("aria-label", ariaLabel);

  wrap.append(label, input);
  toolbar.appendChild(wrap);
}

function appendIndexViewToggle(documentRef, toolbar) {
  var button = documentRef.createElement("button");
  button.className = "docsViewer__indexViewToggle";
  button.type = "button";
  button.id = "docsViewerIndexViewToggle";
  button.hidden = true;
  button.setAttribute("aria-label", "Tree index view");
  button.title = "Tree index view";
  button.textContent = "📁";
  toolbar.appendChild(button);
}

function appendPanelControls(documentRef, toolbar) {
  var group = documentRef.createElement("div");
  group.className = "docsViewer__panelControls";
  group.id = "docsViewerPanelControls";
  group.setAttribute("role", "group");
  group.setAttribute("aria-label", "Panel controls");
  appendIndexViewToggle(documentRef, group);
  toolbar.appendChild(group);
}

export function renderDocsViewerViewerToolbar(options) {
  var settings = options || {};
  var documentRef = settings.document || document;
  var mount = settings.mount || null;
  var controlMount = settings.controlMount || mount;
  if (!mount) return null;

  var toolbar = documentRef.createElement("div");
  toolbar.className = "docsViewer__viewerToolbar";
  toolbar.id = "docsViewerViewerToolbar";
  toolbar.setAttribute("role", "toolbar");
  toolbar.setAttribute("aria-label", "Viewer controls");

  if (routeFeatureEnabled(settings.routeContext, "recently-added")) {
    appendRecentButton(documentRef, toolbar);
  }
  if (routeFeatureEnabled(settings.routeContext, "search")) {
    appendSearchInput(documentRef, toolbar, controlMount);
  }
  appendPanelControls(documentRef, toolbar);

  mount.appendChild(toolbar);
  return toolbar;
}
