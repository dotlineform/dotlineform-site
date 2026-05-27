function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function valueOrFallback(value, fallback) {
  var text = cleanString(value);
  return text || fallback || "Not set";
}

function appendText(parent, className, text) {
  var node = document.createElement("span");
  node.className = className;
  node.textContent = text;
  parent.appendChild(node);
  return node;
}

function appendDefinition(list, label, value, options) {
  var settings = options || {};
  var row = document.createElement("div");
  row.className = "docsViewer__metadataInfoRow";

  var term = document.createElement("dt");
  term.className = "docsViewer__metadataInfoTerm";
  term.textContent = label;

  var definition = document.createElement("dd");
  definition.className = "docsViewer__metadataInfoValue";
  if (settings.href) {
    var link = document.createElement("a");
    link.href = settings.href;
    link.textContent = value;
    definition.appendChild(link);
  } else {
    definition.textContent = value;
  }

  row.append(term, definition);
  list.appendChild(row);
}

function parentPathLabel(context) {
  var trail = Array.isArray(context.parentTrail) ? context.parentTrail : [];
  if (trail.length === 0) return "Top level";
  return trail.map(function (entry) {
    return cleanString(entry && entry.title) || cleanString(entry && entry.doc_id);
  }).filter(Boolean).join(" / ") || "Top level";
}

function visibilityLabel(doc) {
  if (!doc) return "Not set";
  if (doc.hidden === true || doc.viewable === false) return "Hidden";
  return "Visible";
}

function renderMetadata(context) {
  var mount = context.mount;
  if (!mount) return;
  mount.replaceChildren();

  var doc = context.selectedDoc || null;
  if (!doc) {
    var empty = document.createElement("p");
    empty.className = "docsViewer__metadataInfoEmpty muted small";
    empty.textContent = "Select a document to see metadata.";
    mount.appendChild(empty);
    return;
  }

  var article = document.createElement("article");
  article.className = "docsViewer__metadataInfo";

  var title = document.createElement("h3");
  title.className = "docsViewer__metadataInfoTitle";
  title.textContent = valueOrFallback(doc.title, doc.doc_id || "Untitled document");

  var idLine = document.createElement("p");
  idLine.className = "docsViewer__metadataInfoId muted small";
  appendText(idLine, "docsViewer__metadataInfoIdLabel", "Doc ID ");
  appendText(idLine, "docsViewer__metadataInfoIdValue", valueOrFallback(doc.doc_id, "Not set"));

  var list = document.createElement("dl");
  list.className = "docsViewer__metadataInfoList";
  appendDefinition(list, "Scope", valueOrFallback(context.viewerScope || doc.scope, "Not set"));
  appendDefinition(list, "Summary", valueOrFallback(doc.summary, "No summary"));
  appendDefinition(list, "Parent path", parentPathLabel(context));
  appendDefinition(list, "Added", valueOrFallback(doc.added_date, "Not set"));
  appendDefinition(list, "Updated", valueOrFallback(doc.last_updated, "Not set"));
  appendDefinition(list, "UI status", valueOrFallback(context.statusLabel || doc.ui_status, "Not set"));
  appendDefinition(list, "Visibility", visibilityLabel(doc));
  if (context.canonicalUrl) {
    appendDefinition(list, "Route", context.canonicalUrl, { href: context.canonicalUrl });
  }

  article.append(title, idLine, list);
  mount.appendChild(article);
}

export function createDocsViewerMetadataInfoView() {
  return {
    mount: renderMetadata,
    update: renderMetadata,
    unmount: function (context) {
      if (context && context.mount) context.mount.replaceChildren();
    },
    dispose: function (context) {
      if (context && context.mount) context.mount.replaceChildren();
    }
  };
}
