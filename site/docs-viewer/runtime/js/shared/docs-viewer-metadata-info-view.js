function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function valueOrFallback(value, fallback) {
  var text = cleanString(value);
  return text || fallback || "Not set";
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

var METADATA_FIELDS = {
  added: function (metadata) {
    return {
      label: "Added",
      value: valueOrFallback(metadata.added_date, "Not set")
    };
  },
  date: function (metadata) {
    return {
      label: "Date",
      value: valueOrFallback(metadata.date_display || metadata.date, "Not set")
    };
  },
  doc_id: function (metadata) {
    return {
      label: "Doc ID",
      value: valueOrFallback(metadata.doc_id, "Not set")
    };
  },
  summary: function (metadata) {
    return {
      label: "Summary",
      value: valueOrFallback(metadata.summary, "No summary")
    };
  },
  updated: function (metadata) {
    return {
      label: "Updated",
      value: valueOrFallback(metadata.last_updated, "Not set")
    };
  }
};

var MANAGE_METADATA_FIELD_ORDER = ["doc_id", "summary", "date", "added", "updated"];
var PUBLIC_METADATA_FIELD_ORDER = ["summary", "updated"];

function metadataFieldOrder(context) {
  return context.appContext && context.appContext.kind === "public"
    ? PUBLIC_METADATA_FIELD_ORDER
    : MANAGE_METADATA_FIELD_ORDER;
}

function renderLoading(mount) {
  var empty = document.createElement("p");
  empty.className = "docsViewer__metadataInfoEmpty muted small";
  empty.textContent = "Document info is loading.";
  mount.appendChild(empty);
}

function renderMetadataDetails(context, metadata) {
  var mount = context.mount;
  var article = document.createElement("article");
  article.className = "docsViewer__metadataInfo";

  var title = document.createElement("h3");
  title.className = "docsViewer__metadataInfoTitle";
  title.textContent = valueOrFallback(metadata.title, metadata.doc_id || "Untitled document");

  var list = document.createElement("dl");
  list.className = "docsViewer__metadataInfoList";
  metadataFieldOrder(context).forEach(function (fieldName) {
    var field = METADATA_FIELDS[fieldName];
    if (!field) return;
    var definition = field(metadata);
    appendDefinition(list, definition.label, definition.value);
  });

  article.append(title, list);
  mount.appendChild(article);
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

  var metadata = context.selectedMetadata || null;
  if (!metadata) {
    renderLoading(mount);
    return;
  }
  renderMetadataDetails(context, metadata);
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
