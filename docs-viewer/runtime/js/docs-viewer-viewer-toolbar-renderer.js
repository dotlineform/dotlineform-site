function routeAllowsScopeQuery(routeContext) {
  if (routeContext && routeContext.access) return Boolean(routeContext.access.allowScopeQuery);
  return false;
}

function routeEnablesSearch(mount) {
  return !mount || mount.dataset.enableSearch !== "false";
}

function appendScopeSelect(documentRef, toolbar) {
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
  toolbar.appendChild(label);
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

function appendInfoToggle(documentRef, toolbar) {
  var button = documentRef.createElement("button");
  button.className = "docsViewer__infoToggle";
  button.id = "docsViewerInfoToggle";
  button.type = "button";
  button.hidden = true;
  button.setAttribute("aria-label", "Show document info");
  button.setAttribute("aria-expanded", "false");
  button.title = "Show document info";
  button.textContent = "i";
  toolbar.appendChild(button);
}

export function renderDocsViewerViewerToolbar(options) {
  var settings = options || {};
  var documentRef = settings.document || document;
  var mount = settings.mount || null;
  var controlMount = settings.controlMount || mount;
  var routeContext = settings.routeContext || null;
  if (!mount) return null;

  var toolbar = documentRef.createElement("div");
  toolbar.className = "docsViewer__viewerToolbar";
  toolbar.id = "docsViewerViewerToolbar";
  toolbar.setAttribute("role", "toolbar");
  toolbar.setAttribute("aria-label", "Viewer controls");

  var enableSearch = routeEnablesSearch(controlMount);
  var allowScopeQuery = routeAllowsScopeQuery(routeContext);
  if (allowScopeQuery) {
    appendScopeSelect(documentRef, toolbar);
  }
  if (enableSearch) {
    appendRecentButton(documentRef, toolbar);
    appendSearchInput(documentRef, toolbar, controlMount);
  }
  appendIndexViewToggle(documentRef, toolbar);
  appendInfoToggle(documentRef, toolbar);

  mount.appendChild(toolbar);
  return toolbar;
}

export function applyDocsViewerViewerToolbarProjection(options) {
  var refs = options && options.refs ? options.refs : {};
  var projection = options && options.projection ? options.projection : {};
  var infoToggle = refs.infoToggle || null;
  if (!infoToggle) return;

  if (Object.prototype.hasOwnProperty.call(projection, "infoToggleHidden")) {
    infoToggle.hidden = Boolean(projection.infoToggleHidden);
  }
  if (Object.prototype.hasOwnProperty.call(projection, "infoTogglePressed")) {
    infoToggle.classList.toggle("is-active", Boolean(projection.infoTogglePressed));
    infoToggle.setAttribute("aria-expanded", projection.infoTogglePressed ? "true" : "false");
  }
  if (Object.prototype.hasOwnProperty.call(projection, "infoToggleLabel")) {
    infoToggle.setAttribute("aria-label", projection.infoToggleLabel || "Show document info");
    infoToggle.title = projection.infoToggleLabel || "Show document info";
  }
}
