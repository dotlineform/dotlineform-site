function routeAllowsScopeQuery(root, routeContext) {
  if (routeContext && routeContext.access) return Boolean(routeContext.access.allowScopeQuery);
  return Boolean(root && root.dataset.allowScopeQuery === "true");
}

function routeAllowsManagement(root, routeContext) {
  if (routeContext && routeContext.access) return Boolean(routeContext.access.canLoadManagementUi);
  return Boolean(root && root.dataset.allowManagement === "true");
}

function routeEnablesSearch(mount) {
  return !mount || mount.dataset.enableSearch !== "false";
}

function appendScopeSelect(documentRef, row) {
  var label = documentRef.createElement("label");
  label.className = "docsViewer__scopeField";
  label.setAttribute("for", "docsViewerScopeSelect");
  label.setAttribute("aria-label", "Docs scope");

  var select = documentRef.createElement("select");
  select.className = "docsViewer__scopeSelect";
  select.id = "docsViewerScopeSelect";

  label.appendChild(select);
  row.appendChild(label);
}

function appendRecentButton(documentRef, row) {
  var button = documentRef.createElement("button");
  button.className = "docsViewer__actionButton docsViewer__recentButton";
  button.type = "button";
  button.id = "docsViewerRecentButton";
  button.setAttribute("aria-pressed", "false");
  button.textContent = "recently added";
  row.appendChild(button);
}

function appendSearchInput(documentRef, row, mount) {
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
  row.appendChild(wrap);
}

function appendManagementMount(documentRef, row) {
  var mount = documentRef.createElement("div");
  mount.id = "docsViewerManageActionsMount";
  mount.setAttribute("data-docs-viewer-management-actions-mount", "");
  row.appendChild(mount);
}

export function renderDocsViewerHeaderControls(options) {
  var settings = options || {};
  var documentRef = settings.document || document;
  var root = settings.root;
  var mount = settings.mount;
  var routeContext = settings.routeContext || null;
  if (!mount) return null;

  mount.replaceChildren();

  var enableSearch = routeEnablesSearch(mount);
  var allowScopeQuery = routeAllowsScopeQuery(root, routeContext);
  if (!enableSearch && !allowScopeQuery) return null;

  var row = documentRef.createElement("div");
  row.className = "docsViewer__searchRow";

  if (allowScopeQuery) {
    appendScopeSelect(documentRef, row);
  }
  if (enableSearch) {
    appendRecentButton(documentRef, row);
    appendSearchInput(documentRef, row, mount);
  }
  if (routeAllowsManagement(root, routeContext)) {
    appendManagementMount(documentRef, row);
  }

  mount.appendChild(row);
  return row;
}
