function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function clearNode(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function valueText(value) {
  if (value === true) return "true";
  if (value === false) return "false";
  if (value == null) return "";
  if (Array.isArray(value)) return value.length ? value.map(valueText).join(", ") : "[]";
  if (typeof value === "object") return JSON.stringify(value, null, 2);
  return cleanString(value);
}

function selectedScopeFromRoute(scopes) {
  const params = new URLSearchParams(window.location.search);
  const selected = cleanString(params.get("report_scope")).toLowerCase();
  if (!selected) return "";
  return scopes.some((scope) => scope.scope_id === selected) ? selected : "";
}

function persistSelectedScope(scopeId) {
  const url = new URL(window.location.href);
  if (scopeId) {
    url.searchParams.set("report_scope", scopeId);
  } else {
    url.searchParams.delete("report_scope");
  }
  try {
    window.history.replaceState({}, "", url.pathname + url.search + url.hash);
  } catch (_error) {
    // Route persistence is useful in the viewer but should not block report rendering.
  }
}

function reportService(context) {
  return context && context.reportService && typeof context.reportService.readSourceConfig === "function"
    ? context.reportService
    : null;
}

function fetchSourceConfig(context) {
  const service = reportService(context);
  if (!service) {
    return Promise.reject(new Error("Local docs-management server is not configured."));
  }
  return service.readSourceConfig();
}

function appendKeyValue(parent, label, value) {
  const row = document.createElement("div");
  row.className = "docsViewerReport__configRow";
  const key = document.createElement("dt");
  key.className = "docsViewerReport__configKey";
  key.textContent = label;
  const val = document.createElement("dd");
  val.className = "docsViewerReport__configValue";
  const text = valueText(value);
  if (text.includes("\n")) {
    const pre = document.createElement("pre");
    pre.textContent = text;
    val.appendChild(pre);
  } else {
    val.textContent = text || "not set";
  }
  row.appendChild(key);
  row.appendChild(val);
  parent.appendChild(row);
}

function appendGroup(parent, title, rows) {
  const group = document.createElement("section");
  group.className = "docsViewerReport__configGroup";
  const heading = document.createElement("h3");
  heading.className = "docsViewerReport__configHeading";
  heading.textContent = title;
  const list = document.createElement("dl");
  list.className = "docsViewerReport__configList";
  rows.forEach((row) => appendKeyValue(list, row[0], row[1]));
  group.appendChild(heading);
  group.appendChild(list);
  parent.appendChild(group);
}

function sourceRows(scope) {
  const config = scope.source_config || {};
  return [
    ["scope_id", config.scope_id],
    ["scope_type", config.scope_type],
    ["viewer_base_url", config.viewer_base_url],
    ["include_scope_param", config.include_scope_param],
    ["default_doc_id", config.default_doc_id],
    ["allow_unresolved_parent_ids", config.allow_unresolved_parent_ids],
    ["non_loadable_doc_ids", config.non_loadable_doc_ids],
    ["manage_only_tree_root_ids", config.manage_only_tree_root_ids]
  ];
}

function roleRows(scope) {
  const roles = scope.roles || {};
  return [
    ["source", roles.source],
    ["published documents", roles.published_documents],
    ["published search", roles.published_search],
    ["published media", roles.media]
  ];
}

function browserRows(scope) {
  const config = scope.browser_config || {};
  return [
    ["viewer_base_url", config.viewer_base_url],
    ["include_scope_param", config.include_scope_param],
    ["default_doc_id", config.default_doc_id],
    ["media", config.media],
    ["index_tree_url", config.index_tree_url],
    ["recent_url", config.recent_url],
    ["search_index_url", config.search_index_url],
    ["search", config.search]
  ];
}

function artifactRows(scope) {
  const artifacts = scope.artifacts || {};
  return [
    ["published documents available", artifacts.published_documents_available],
    ["published search available", artifacts.published_search_available],
    ["viewer_options", scope.viewer_options || {}]
  ];
}

function appendWarnings(parent, warnings) {
  if (!Array.isArray(warnings) || !warnings.length) return;
  const group = document.createElement("section");
  group.className = "docsViewerReport__configGroup";
  const heading = document.createElement("h3");
  heading.className = "docsViewerReport__configHeading";
  heading.textContent = "Warnings";
  const list = document.createElement("ul");
  list.className = "docsViewerReport__configWarnings";
  warnings.forEach((warning) => {
    const item = document.createElement("li");
    item.textContent = cleanString(warning);
    list.appendChild(item);
  });
  group.appendChild(heading);
  group.appendChild(list);
  parent.appendChild(group);
}

function appendScope(parent, scope) {
  const section = document.createElement("section");
  section.className = "docsViewerReport__configScope";
  const heading = document.createElement("h2");
  heading.className = "docsViewerReport__configTitle";
  heading.textContent = cleanString(scope.title) || cleanString(scope.scope_id);
  const meta = document.createElement("p");
  meta.className = "docsViewerReport__subtext";
  meta.textContent = cleanString(scope.scope_id);
  section.appendChild(heading);
  section.appendChild(meta);
  appendGroup(section, "Source config", sourceRows(scope));
  appendGroup(section, "Roles and locations", roleRows(scope));
  appendGroup(section, "Browser projection", browserRows(scope));
  appendGroup(section, "Published artifacts", artifactRows(scope));
  appendWarnings(section, scope.warnings);
  parent.appendChild(section);
}

function renderToolbar(root, state) {
  const toolbar = document.createElement("div");
  toolbar.className = "docsViewerReport__toolbar";
  const label = document.createElement("label");
  label.className = "docsViewerReport__selectLabel";
  label.setAttribute("for", "docsViewerSourceConfigScope");
  label.textContent = "Scope";
  const select = document.createElement("select");
  select.id = "docsViewerSourceConfigScope";
  select.className = "docsViewerReport__select";
  const all = document.createElement("option");
  all.value = "";
  all.textContent = "All scopes";
  select.appendChild(all);
  state.scopes.forEach((scope) => {
    const option = document.createElement("option");
    option.value = scope.scope_id;
    option.textContent = cleanString(scope.title) || scope.scope_id;
    select.appendChild(option);
  });
  select.value = state.selectedScope;
  const status = document.createElement("p");
  status.className = "docsViewerReport__status";
  toolbar.appendChild(label);
  toolbar.appendChild(select);
  toolbar.appendChild(status);
  select.addEventListener("change", () => {
    state.selectedScope = cleanString(select.value);
    persistSelectedScope(state.selectedScope);
    renderScopes(state);
  });
  state.statusNode = status;
  root.appendChild(toolbar);
}

function renderScopes(state) {
  clearNode(state.scopesNode);
  const visible = state.selectedScope
    ? state.scopes.filter((scope) => scope.scope_id === state.selectedScope)
    : state.scopes;
  state.statusNode.textContent = visible.length === 1 ? "1 scope" : `${visible.length} scopes`;
  visible.forEach((scope) => appendScope(state.scopesNode, scope));
}

export function mountSourceConfigReport(context) {
  const root = context.reportRoot;
  clearNode(root);
  root.dataset.reportId = "source_config";
  root.innerHTML = '<p class="docsViewerReport__status">Loading source config...</p>';
  return fetchSourceConfig(context).then((payload) => {
    const scopes = Array.isArray(payload.scopes)
      ? payload.scopes.map((scope) => Object.assign({}, scope, { scope_id: cleanString(scope.scope_id).toLowerCase() })).filter((scope) => scope.scope_id)
      : [];
    clearNode(root);
    const state = {
      scopes,
      selectedScope: selectedScopeFromRoute(scopes),
      statusNode: null,
      scopesNode: document.createElement("div")
    };
    state.scopesNode.className = "docsViewerReport__configScopes";
    renderToolbar(root, state);
    appendGroup(root, "Shared viewer config", [
      ["source", payload.docs_viewer_source || {}],
      ["browser projection", payload.docs_viewer_browser || {}]
    ]);
    root.appendChild(state.scopesNode);
    renderScopes(state);
  }).catch((error) => {
    clearNode(root);
    const status = document.createElement("p");
    status.className = "docsViewerReport__status";
    status.textContent = error && error.message ? error.message : "Failed to load source config.";
    root.appendChild(status);
  });
}
