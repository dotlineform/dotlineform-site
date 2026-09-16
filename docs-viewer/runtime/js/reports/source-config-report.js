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

function selectedStageFromRoute(stages) {
  const params = new URLSearchParams(window.location.search);
  const selected = cleanString(params.get("report_stage")).toLowerCase();
  if (!selected) return "";
  return stages.some((stage) => stage.stage === selected) ? selected : "";
}

function persistSelectedStage(stage) {
  const url = new URL(window.location.href);
  if (stage) {
    url.searchParams.set("report_stage", stage);
  } else {
    url.searchParams.delete("report_stage");
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

function sourceRows(stage) {
  const config = stage.source_config || {};
  return [
    ["stage", config.stage],
    ["viewer_base_url", config.viewer_base_url],
    ["default_doc_id", config.default_doc_id],
    ["allow_unresolved_parent_ids", config.allow_unresolved_parent_ids],
    ["non_loadable_doc_ids", config.non_loadable_doc_ids],
    ["manage_only_tree_root_ids", config.manage_only_tree_root_ids]
  ];
}

function roleRows(stage) {
  const roles = stage.roles || {};
  return [
    ["source", roles.source],
    ["published documents", roles.published_documents],
    ["published search", roles.published_search],
    ["published media", roles.media]
  ];
}

function browserRows(stage) {
  const config = stage.browser_config || {};
  return [
    ["viewer_base_url", config.viewer_base_url],
    ["default_doc_id", config.default_doc_id],
    ["media", config.media],
    ["index_tree_url", config.index_tree_url],
    ["recent_url", config.recent_url],
    ["search_index_url", config.search_index_url],
    ["search", config.search]
  ];
}

function artifactRows(stage) {
  const artifacts = stage.artifacts || {};
  return [
    ["generated documents available", artifacts.generated_documents_available],
    ["generated search available", artifacts.generated_search_available],
    ["viewer_options", stage.viewer_options || {}]
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

function appendStage(parent, stage) {
  const section = document.createElement("section");
  section.className = "docsViewerReport__configStage";
  const heading = document.createElement("h2");
  heading.className = "docsViewerReport__configTitle";
  heading.textContent = cleanString(stage.title) || cleanString(stage.stage);
  const meta = document.createElement("p");
  meta.className = "docsViewerReport__subtext";
  meta.textContent = cleanString(stage.stage);
  section.appendChild(heading);
  section.appendChild(meta);
  appendGroup(section, "Source config", sourceRows(stage));
  appendGroup(section, "Roles and locations", roleRows(stage));
  appendGroup(section, "Browser projection", browserRows(stage));
  appendGroup(section, "Published artifacts", artifactRows(stage));
  appendWarnings(section, stage.warnings);
  parent.appendChild(section);
}

function renderToolbar(root, state) {
  const toolbar = document.createElement("div");
  toolbar.className = "docsViewerReport__toolbar";
  const label = document.createElement("label");
  label.className = "docsViewerReport__selectLabel";
  label.setAttribute("for", "docsViewerSourceConfigStage");
  label.textContent = "Stage";
  const select = document.createElement("select");
  select.id = "docsViewerSourceConfigStage";
  select.className = "docsViewerReport__select";
  const all = document.createElement("option");
  all.value = "";
  all.textContent = "All stages";
  select.appendChild(all);
  state.stages.forEach((stage) => {
    const option = document.createElement("option");
    option.value = stage.stage;
    option.textContent = cleanString(stage.title) || stage.stage;
    select.appendChild(option);
  });
  select.value = state.selectedStage;
  const status = document.createElement("p");
  status.className = "docsViewerReport__status";
  toolbar.appendChild(label);
  toolbar.appendChild(select);
  toolbar.appendChild(status);
  select.addEventListener("change", () => {
    state.selectedStage = cleanString(select.value);
    persistSelectedStage(state.selectedStage);
    renderStages(state);
  });
  state.statusNode = status;
  root.appendChild(toolbar);
}

function renderStages(state) {
  clearNode(state.stagesNode);
  const visible = state.selectedStage
    ? state.stages.filter((stage) => stage.stage === state.selectedStage)
    : state.stages;
  state.statusNode.textContent = visible.length === 1 ? "1 stage" : `${visible.length} stages`;
  visible.forEach((stage) => appendStage(state.stagesNode, stage));
}

export function mountSourceConfigReport(context) {
  const root = context.reportRoot;
  clearNode(root);
  root.dataset.reportId = "source_config";
  root.innerHTML = '<p class="docsViewerReport__status">Loading source config...</p>';
  return fetchSourceConfig(context).then((payload) => {
    const stages = Array.isArray(payload.stages)
      ? payload.stages.map((stage) => Object.assign({}, stage, { stage: cleanString(stage.stage).toLowerCase() })).filter((stage) => stage.stage)
      : [];
    clearNode(root);
    const state = {
      stages,
      selectedStage: selectedStageFromRoute(stages),
      statusNode: null,
      stagesNode: document.createElement("div")
    };
    state.stagesNode.className = "docsViewerReport__configStages";
    renderToolbar(root, state);
    appendGroup(root, "Shared viewer config", [
      ["source", payload.docs_viewer_source || {}],
      ["browser projection", payload.docs_viewer_browser || {}]
    ]);
    root.appendChild(state.stagesNode);
    renderStages(state);
  }).catch((error) => {
    clearNode(root);
    const status = document.createElement("p");
    status.className = "docsViewerReport__status";
    status.textContent = error && error.message ? error.message : "Failed to load source config.";
    root.appendChild(status);
  });
}
