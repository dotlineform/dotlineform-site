function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function clearNode(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function appendTextCell(row, className, text) {
  const cell = document.createElement("span");
  cell.className = className;
  cell.textContent = text;
  row.appendChild(cell);
  return cell;
}

function appendHeaderCell(row, text) {
  appendTextCell(row, "docsViewerReport__headLabel", text);
}

function targetTitle(target, bucket) {
  const refs = sourceReferences(bucket);
  return cleanString(target && target.target_title)
    || cleanString(bucket && bucket.target_title)
    || cleanString(refs[0] && refs[0].label);
}

function targetLabel(target, bucket) {
  const id = cleanString(target && target.target_id);
  const title = targetTitle(target, bucket);
  return id && title ? `${id}: ${title}` : id || title || cleanString(target && target.target_key);
}

function targetStatus(target) {
  return cleanString(target && target.target_status) || "unknown";
}

function targetCount(target) {
  const count = Number(target && target.count);
  return Number.isFinite(count) ? count : 0;
}

function sourceReferences(payload) {
  return Array.isArray(payload && payload.references) ? payload.references : [];
}

function configuredScopes(context) {
  const scopes = Array.isArray(context && context.scopeConfigs) ? context.scopeConfigs : [];
  return scopes.map((scope) => ({
    scopeId: cleanString(scope && (scope.scope_id || scope.scopeId)).toLowerCase(),
    title: cleanString(scope && scope.title) || cleanString(scope && (scope.scope_id || scope.scopeId))
  })).filter((scope) => scope.scopeId);
}

function selectedScopeFromRoute(scopes, fallbackScope) {
  const params = new URLSearchParams(window.location.search);
  const selected = cleanString(params.get("report_scope")).toLowerCase();
  if (selected === "all") return "";
  if (scopes.some((scope) => scope.scopeId === selected)) return selected;
  return cleanString(fallbackScope).toLowerCase();
}

function persistSelectedScope(scopeId) {
  const url = new URL(window.location.href);
  if (scopeId) {
    url.searchParams.set("report_scope", scopeId);
  } else {
    url.searchParams.set("report_scope", "all");
  }
  window.history.replaceState({}, "", url.pathname + url.search + url.hash);
}

function selectedScopes(state) {
  if (state.selectedScope) return [state.selectedScope];
  const scopes = state.scopes.map((scope) => scope.scopeId).filter(Boolean);
  return scopes.length ? scopes : [cleanString(state.context.viewerScope).toLowerCase()].filter(Boolean);
}

function appendTargetCell(row, target, bucket) {
  const cell = document.createElement("span");
  cell.className = "docsViewerReport__cellMeta docsViewerReport__referenceTarget";

  const label = targetLabel(target, bucket);
  const href = cleanString(target && target.target_href);
  if (href) {
    const link = document.createElement("a");
    link.className = "docsViewerReport__cellLink docsViewerReport__title";
    link.href = href;
    link.textContent = label;
    cell.appendChild(link);
  } else {
    const title = document.createElement("span");
    title.className = "docsViewerReport__title";
    title.textContent = label;
    cell.appendChild(title);
  }
  row.appendChild(cell);
}

function appendSourcesCell(row, state, bucket) {
  const refs = sourceReferences(bucket);
  const cell = document.createElement("span");
  cell.className = "docsViewerReport__cellMeta docsViewerReport__referenceSources";

  if (!refs.length) {
    cell.textContent = "No source docs";
    row.appendChild(cell);
    return;
  }

  refs.forEach((ref) => {
    const link = document.createElement("a");
    link.className = "docsViewerReport__cellLink";
    link.href = state.context.viewerUrlForScope(
      cleanString(ref.source_scope) || state.sourceScope,
      cleanString(ref.source_doc_id),
      { manage: state.context.managementMode }
    );
    link.textContent = cleanString(ref.source_title) || cleanString(ref.source_doc_id);

    const item = document.createElement("span");
    item.className = "docsViewerReport__referenceSource";
    item.appendChild(link);
    cell.appendChild(item);
  });

  row.appendChild(cell);
}

function renderScopeSelect(state) {
  clearNode(state.scopeSelectNode);
  const all = document.createElement("option");
  all.value = "";
  all.textContent = "All scopes";
  state.scopeSelectNode.appendChild(all);
  state.scopes.forEach((scope) => {
    const option = document.createElement("option");
    option.value = scope.scopeId;
    option.textContent = scope.title || scope.scopeId;
    state.scopeSelectNode.appendChild(option);
  });
  state.scopeSelectNode.value = state.selectedScope;
}

function renderShell(root) {
  clearNode(root);
  root.dataset.reportColumns = "3";

  const toolbar = document.createElement("div");
  toolbar.className = "docsViewerReport__toolbar";

  const label = document.createElement("label");
  label.className = "docsViewerReport__selectLabel";
  label.textContent = "scope ";

  const select = document.createElement("select");
  select.className = "docsViewerReport__select";
  label.appendChild(select);

  const status = document.createElement("p");
  status.className = "docsViewerReport__status";
  toolbar.appendChild(label);
  toolbar.appendChild(status);

  const table = document.createElement("div");
  table.className = "docsViewerReport__table";

  const head = document.createElement("div");
  head.className = "docsViewerReport__head";
  appendHeaderCell(head, "target");
  appendHeaderCell(head, "count");
  appendHeaderCell(head, "source docs");

  const rows = document.createElement("ul");
  rows.className = "docsViewerReport__rows";

  table.appendChild(head);
  table.appendChild(rows);
  root.appendChild(toolbar);
  root.appendChild(table);

  return { scopeSelectNode: select, statusNode: status, rowsNode: rows };
}

function renderRows(state) {
  clearNode(state.rowsNode);
  const targets = state.targets.slice().sort((left, right) => {
    return targetLabel(left, state.buckets.get(cleanString(left.target_key))).localeCompare(
      targetLabel(right, state.buckets.get(cleanString(right.target_key))),
      undefined,
      { numeric: true, sensitivity: "base" }
    );
  });
  const scopeLabel = state.selectedScope || "all scopes";
  state.statusNode.textContent = targets.length === 1 ? `1 target [${scopeLabel}]` : `${targets.length} targets [${scopeLabel}]`;

  targets.forEach((target) => {
    const row = document.createElement("li");
    row.className = "docsViewerReport__row";
    row.dataset.reportTargetKey = cleanString(target.target_key);
    const bucket = state.buckets.get(cleanString(target.target_key));
    appendTargetCell(row, target, bucket);
    appendTextCell(row, "docsViewerReport__cellMeta", String(targetCount(target)));
    appendSourcesCell(row, state, bucket);
    state.rowsNode.appendChild(row);
  });
}

function loadBuckets(context, sourceScope, targets) {
  return Promise.all(targets.map((target) => {
    return context.fetchDocsReferenceTarget(sourceScope, target)
      .then((payload) => [cleanString(target.target_key), payload])
      .catch(() => [cleanString(target.target_key), { references: [] }]);
  })).then((pairs) => new Map(pairs));
}

function mergeIndexes(scopePayloads) {
  const targetsByKey = new Map();
  scopePayloads.forEach(([scope, payload]) => {
    const targets = Array.isArray(payload && payload.targets) ? payload.targets : [];
    targets.forEach((target) => {
      const key = cleanString(target && target.target_key);
      if (!key) return;
      const existing = targetsByKey.get(key) || Object.assign({}, target, { count: 0, source_scopes: [] });
      existing.count = Number(existing.count || 0) + targetCount(target);
      if (!cleanString(existing.target_href)) existing.target_href = cleanString(target && target.target_href);
      if (targetStatus(existing) !== "published" && targetStatus(target) === "published") existing.target_status = "published";
      if (!existing.source_scopes.includes(scope)) existing.source_scopes.push(scope);
      targetsByKey.set(key, existing);
    });
  });
  return Array.from(targetsByKey.values());
}

function mergeBuckets(scopeBuckets) {
  const buckets = new Map();
  scopeBuckets.forEach((bucket) => {
    const key = cleanString(bucket && bucket.target_key);
    if (!key) return;
    const existing = buckets.get(key) || Object.assign({}, bucket, { references: [] });
    existing.references = existing.references.concat(sourceReferences(bucket));
    buckets.set(key, existing);
  });
  return buckets;
}

function loadReportData(state) {
  state.statusNode.textContent = "Loading semantic references...";
  clearNode(state.rowsNode);
  const scopes = selectedScopes(state);

  return Promise.all(scopes.map((scope) => {
    return state.context.fetchDocsReferencesIndex(scope)
      .then((payload) => [scope, payload])
      .catch(() => [scope, { targets: [] }]);
  }))
    .then((scopePayloads) => {
      state.targets = mergeIndexes(scopePayloads);
      return Promise.all(scopePayloads.flatMap(([scope, payload]) => {
        const targets = Array.isArray(payload && payload.targets) ? payload.targets : [];
        return targets.map((target) => state.context.fetchDocsReferenceTarget(scope, target)
          .catch(() => Object.assign({}, target, { references: [] })));
      }));
    })
    .then((scopeBuckets) => {
      state.buckets = mergeBuckets(scopeBuckets);
      renderRows(state);
    })
    .catch((error) => {
      state.statusNode.textContent = error && error.status === 404 ? "No semantic references generated." : "Failed to load semantic references.";
    });
}

export function mountSemanticReferencesReport(context) {
  const scopes = configuredScopes(context);
  const fallbackScope = context.reportMeta.scope || "";
  const selectedScope = selectedScopeFromRoute(scopes, fallbackScope);
  const nodes = renderShell(context.reportRoot);

  const state = Object.assign({
    context,
    sourceScope: selectedScope,
    selectedScope,
    scopes,
    targets: [],
    buckets: new Map()
  }, nodes);

  renderScopeSelect(state);
  state.scopeSelectNode.addEventListener("change", () => {
    state.selectedScope = cleanString(state.scopeSelectNode.value).toLowerCase();
    state.sourceScope = state.selectedScope;
    persistSelectedScope(state.selectedScope);
    loadReportData(state);
  });

  return loadReportData(state);
}
