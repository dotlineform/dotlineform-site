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
  return article;
}

function renderDiagramSources(context, article, state, requestId) {
  var provider = context.collectionProvider || null;
  var doc = context.selectedDoc || null;
  if (
    !doc
    || !context.appContext
    || context.appContext.kind !== "manage"
    || !provider
    || typeof provider.readDiagramSources !== "function"
    || typeof provider.openDiagramSource !== "function"
  ) return;

  provider.readDiagramSources(doc.doc_id).then(function (payload) {
    if (state.requestId !== requestId || !article.parentNode) return;
    var sources = payload && Array.isArray(payload.sources) ? payload.sources : [];
    if (!sources.length) return;

    var section = document.createElement("section");
    section.className = "docsViewer__diagramSources";

    var heading = document.createElement("h4");
    heading.className = "docsViewer__diagramSourcesTitle";
    heading.textContent = "Diagram sources";

    var list = document.createElement("ul");
    list.className = "docsViewer__diagramSourcesList";
    sources.forEach(function (source) {
      var item = document.createElement("li");
      item.className = "docsViewer__diagramSourcesItem";

      var label = document.createElement("span");
      label.textContent = cleanString(source.label) || cleanString(source.source_identity) || "Diagram";

      var link = document.createElement("a");
      link.href = "#";
      link.textContent = cleanString(source.open_label) || "Open in VS Code";
      link.addEventListener("click", function (event) {
        event.preventDefault();
        provider.openDiagramSource({
          doc_id: doc.doc_id,
          media_identity: cleanString(source.media_identity),
          editor: "vscode"
        }).catch(function (error) {
          link.title = error && error.message ? error.message : "Could not open diagram source.";
        });
      });

      item.append(label, link);
      list.appendChild(item);
    });

    section.append(heading, list);
    article.appendChild(section);
  }).catch(function () {
    // Document Info remains useful when the local source service is unavailable.
  });
}

function renderMetadata(context, state) {
  var mount = context.mount;
  if (!mount) return;
  state.requestId += 1;
  var requestId = state.requestId;
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
  var article = renderMetadataDetails(context, metadata);
  renderDiagramSources(context, article, state, requestId);
}

export function createDocsViewerMetadataInfoView() {
  var state = { requestId: 0 };
  return {
    mount: function (context) { renderMetadata(context, state); },
    update: function (context) { renderMetadata(context, state); },
    unmount: function (context) {
      state.requestId += 1;
      if (context && context.mount) context.mount.replaceChildren();
    },
    dispose: function (context) {
      state.requestId += 1;
      if (context && context.mount) context.mount.replaceChildren();
    }
  };
}
