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

function targetLabel(target) {
  const kind = cleanString(target && target.target_kind);
  const id = cleanString(target && target.target_id);
  return kind && id ? `${kind}:${id}` : kind || id;
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

function appendTargetCell(row, target) {
  const cell = document.createElement("span");
  cell.className = "docsViewerReport__cellMeta docsViewerReport__referenceTarget";

  const label = targetLabel(target);
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

  const status = document.createElement("span");
  status.className = "docsViewerReport__subtext";
  status.textContent = targetStatus(target);
  cell.appendChild(status);
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

    const label = document.createElement("span");
    label.className = "docsViewerReport__subtext";
    label.textContent = cleanString(ref.label);

    const item = document.createElement("span");
    item.className = "docsViewerReport__referenceSource";
    item.appendChild(link);
    if (label.textContent) item.appendChild(label);
    cell.appendChild(item);
  });

  row.appendChild(cell);
}

function renderShell(root) {
  clearNode(root);
  root.dataset.reportColumns = "3";

  const status = document.createElement("p");
  status.className = "docsViewerReport__status";

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
  root.appendChild(status);
  root.appendChild(table);

  return { statusNode: status, rowsNode: rows };
}

function renderRows(state) {
  clearNode(state.rowsNode);
  const targets = state.targets.slice().sort((left, right) => {
    return targetLabel(left).localeCompare(targetLabel(right), undefined, { numeric: true, sensitivity: "base" });
  });
  state.statusNode.textContent = targets.length === 1 ? "1 target" : `${targets.length} targets`;

  targets.forEach((target) => {
    const row = document.createElement("li");
    row.className = "docsViewerReport__row";
    row.dataset.reportTargetKey = cleanString(target.target_key);
    appendTargetCell(row, target);
    appendTextCell(row, "docsViewerReport__cellMeta", String(targetCount(target)));
    appendSourcesCell(row, state, state.buckets.get(cleanString(target.target_key)));
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

export function mountSemanticReferencesReport(context) {
  const sourceScope = context.reportMeta.scope || context.viewerScope;
  const nodes = renderShell(context.reportRoot);
  nodes.statusNode.textContent = "Loading semantic references...";

  const state = Object.assign({
    context,
    sourceScope,
    targets: [],
    buckets: new Map()
  }, nodes);

  return context.fetchDocsReferencesIndex(sourceScope)
    .then((payload) => {
      state.targets = Array.isArray(payload && payload.targets) ? payload.targets : [];
      return loadBuckets(context, sourceScope, state.targets);
    })
    .then((buckets) => {
      state.buckets = buckets;
      renderRows(state);
    })
    .catch((error) => {
      clearNode(context.reportRoot);
      const status = document.createElement("p");
      status.className = "docsViewerReport__status";
      status.textContent = error && error.status === 404 ? "No semantic references generated." : "Failed to load semantic references.";
      context.reportRoot.appendChild(status);
    });
}
