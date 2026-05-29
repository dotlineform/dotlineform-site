function routeAllowsScopeQuery(routeContext) {
  if (routeContext && routeContext.access) return Boolean(routeContext.access.allowScopeQuery);
  return false;
}

function routeAllowsManagement(routeContext) {
  if (routeContext && routeContext.access) return Boolean(routeContext.access.canLoadManagementUi);
  return false;
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
  select.className = "docsViewer__scopeSelectNative visually-hidden";
  select.id = "docsViewerScopeSelect";
  select.tabIndex = -1;
  select.setAttribute("aria-hidden", "true");

  var menu = documentRef.createElement("div");
  menu.className = "docsViewer__scopeSelectMenu";
  menu.setAttribute("data-docs-viewer-scope-select-menu", "");

  var button = documentRef.createElement("button");
  button.className = "docsViewer__scopeSelectButton";
  button.type = "button";
  button.id = "docsViewerScopeSelectButton";
  button.setAttribute("aria-haspopup", "listbox");
  button.setAttribute("aria-expanded", "false");
  button.setAttribute("aria-controls", "docsViewerScopeSelectList");
  button.setAttribute("aria-label", "Docs scope");

  var emoji = documentRef.createElement("span");
  emoji.className = "docsViewer__scopeSelectEmoji";
  emoji.setAttribute("aria-hidden", "true");

  var text = documentRef.createElement("span");
  text.className = "docsViewer__scopeSelectText";
  text.setAttribute("data-docs-viewer-scope-select-label", "");

  var list = documentRef.createElement("div");
  list.className = "docsViewer__scopeSelectSurface";
  list.id = "docsViewerScopeSelectList";
  list.setAttribute("role", "listbox");
  list.hidden = true;

  button.append(emoji, text);
  menu.append(button, list);
  label.append(select, menu);
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
  var mount = settings.mount;
  var routeContext = settings.routeContext || null;
  if (!mount) return null;

  mount.replaceChildren();

  var enableSearch = routeEnablesSearch(mount);
  var allowScopeQuery = routeAllowsScopeQuery(routeContext);
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
  if (routeAllowsManagement(routeContext)) {
    appendManagementMount(documentRef, row);
  }

  mount.appendChild(row);
  return row;
}
