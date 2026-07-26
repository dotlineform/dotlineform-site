import {
  catalogueTokenAtSelection,
  parseCatalogueTokens,
  serializeCatalogueToken
} from "./catalogue-token-parser.js";
import {
  loadSemanticTokenRegistry
} from "./semantic-token-registry.js";
import {
  loadSemanticTokenTargets,
  resolveSemanticTokenTargetHref
} from "./semantic-token-targets.js";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function appendReadOnlyRow(list, label, value, href) {
  var row = document.createElement("div");
  row.className = "docsViewer__metadataInfoRow";
  var term = document.createElement("dt");
  term.className = "docsViewer__metadataInfoTerm";
  term.textContent = label;
  var definition = document.createElement("dd");
  definition.className = "docsViewer__metadataInfoValue";
  if (href) {
    var link = document.createElement("a");
    link.href = href;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = value;
    definition.appendChild(link);
  } else {
    definition.textContent = value;
  }
  row.append(term, definition);
  list.appendChild(row);
}

function targetKey(token) {
  return [token.family, token.targetType, token.targetId].join(":");
}

function emptyMessage(mount, message) {
  mount.replaceChildren();
  var empty = document.createElement("p");
  empty.className = "docsViewer__metadataInfoEmpty muted small";
  empty.textContent = message;
  mount.appendChild(empty);
}

function currentToken(state) {
  var adapter = state.adapter;
  if (
    !adapter
    || typeof adapter.getBufferSnapshot !== "function"
    || typeof adapter.getSelection !== "function"
  ) return null;
  var snapshot = adapter.getBufferSnapshot();
  var selection = adapter.getSelection();
  var tokens = parseCatalogueTokens(snapshot.value, { registry: state.registry });
  var token = catalogueTokenAtSelection(tokens, selection);
  if (!token) return null;
  var capture = {
    start: token.start,
    end: token.end,
    text: token.raw,
    revision: snapshot.revision
  };
  if (
    selection.start === selection.end
    && typeof adapter.selectCapturedRange === "function"
  ) {
    adapter.selectCapturedRange(capture);
  }
  return { token: token, capture: capture };
}

function renderToken(context, state, active) {
  var mount = context.mount;
  var token = active.token;
  var capture = active.capture;
  var target = state.targetsByKey.get(targetKey(token)) || null;
  var destinationHref = target && target.href
    ? resolveSemanticTokenTargetHref(target.href, state.publicPreviewBase)
    : "";
  mount.replaceChildren();

  var article = document.createElement("article");
  article.className = "docsViewer__metadataInfo docsViewerCatalogueTokenInfo";
  var heading = document.createElement("h3");
  heading.className = "docsViewer__metadataInfoTitle";
  heading.textContent = "Catalogue token";

  var list = document.createElement("dl");
  list.className = "docsViewer__metadataInfoList";
  appendReadOnlyRow(list, "Family", "Catalogue");
  appendReadOnlyRow(list, "Target type", token.targetType);
  appendReadOnlyRow(list, "Target ID", token.targetId);
  appendReadOnlyRow(list, "Catalogue title", target ? target.title : "Target not resolved");
  appendReadOnlyRow(
    list,
    "Destination",
    target && target.href ? target.href : "No resolved destination",
    destinationHref
  );

  var titleField = document.createElement("label");
  titleField.className = "docsViewer__field";
  var titleLabel = document.createElement("span");
  titleLabel.className = "docsViewer__fieldLabel";
  titleLabel.textContent = "Title";
  var titleInput = document.createElement("input");
  titleInput.className = "docsViewer__fieldInput";
  titleInput.type = "text";
  titleInput.required = true;
  titleInput.value = token.title;
  titleField.append(titleLabel, titleInput);

  var status = document.createElement("p");
  status.className = "docsViewer__metadataInfoEmpty muted small";
  status.hidden = true;

  var actions = document.createElement("div");
  actions.className = "docsViewerCatalogueTokenInfo__actions";
  var updateButton = document.createElement("button");
  updateButton.className = "docsViewer__button";
  updateButton.type = "button";
  updateButton.textContent = "Update token";
  var removeButton = document.createElement("button");
  removeButton.className = "docsViewer__button";
  removeButton.type = "button";
  removeButton.textContent = "Remove token";

  function setStatus(message, isError) {
    status.textContent = message || "";
    status.hidden = !message;
    status.classList.toggle("is-error", Boolean(isError));
  }

  updateButton.addEventListener("click", function () {
    var title = cleanString(titleInput.value);
    var serialized = serializeCatalogueToken({
      registry: state.registry,
      targetType: token.targetType,
      targetId: token.targetId,
      title: title
    });
    if (!serialized) {
      setStatus("Enter a single-line Title.", true);
      titleInput.focus();
      return;
    }
    if (
      !state.adapter
      || typeof state.adapter.replaceCapturedRange !== "function"
      || !state.adapter.replaceCapturedRange(capture, serialized, "select")
    ) {
      setStatus("Markdown source changed. Select the token again.", true);
      return;
    }
  });

  removeButton.addEventListener("click", function () {
    if (
      !state.adapter
      || typeof state.adapter.replaceCapturedRange !== "function"
      || !state.adapter.replaceCapturedRange(capture, "", "end")
    ) {
      setStatus("Markdown source changed. Select the token again.", true);
      return;
    }
  });

  actions.append(updateButton, removeButton);
  article.append(heading, list, titleField, status, actions);
  mount.appendChild(article);
}

function render(context, state) {
  if (!context.mount) return;
  if (!state.loaded) {
    emptyMessage(context.mount, "Catalogue token info is loading.");
    return;
  }
  var active = currentToken(state);
  if (!active) {
    emptyMessage(context.mount, "Place the caret inside a Catalogue token to inspect it.");
    return;
  }
  renderToken(context, state, active);
}

function loadSupport(state) {
  return loadSemanticTokenRegistry({ fetch: state.fetch })
    .then(function (registry) {
      state.registry = registry;
      return loadSemanticTokenTargets(registry, { fetch: state.fetch });
    })
    .then(function (targets) {
      state.targetsByKey = new Map(targets.map(function (target) {
        return [[target.family, target.targetType, target.targetId].join(":"), target];
      }));
      state.loaded = true;
    });
}

export function createCatalogueTokenInfoView(options = {}) {
  var state = {
    adapter: null,
    fetch: options.fetch,
    loaded: false,
    publicPreviewBase: "",
    registry: null,
    targetsByKey: new Map(),
    unsubscribe: null
  };

  function bind(context) {
    var services = context.sourceEditorServices || {};
    state.adapter = typeof services.getActiveSourceEditorContextAdapter === "function"
      ? services.getActiveSourceEditorContextAdapter()
      : null;
    state.publicPreviewBase = cleanString(services.publicPreviewBase);
    if (state.adapter && typeof state.adapter.onSelectionChange === "function") {
      state.unsubscribe = state.adapter.onSelectionChange(function () {
        render(context, state);
      });
    }
  }

  function unbind() {
    if (typeof state.unsubscribe === "function") state.unsubscribe();
    state.unsubscribe = null;
    state.adapter = null;
  }

  return {
    mount: function (context) {
      bind(context);
      render(context, state);
      return loadSupport(state)
        .then(function () {
          render(context, state);
        })
        .catch(function () {
          state.loaded = true;
          render(context, state);
        });
    },
    update: function (context) {
      render(context, state);
    },
    unmount: function (context) {
      unbind();
      if (context && context.mount) context.mount.replaceChildren();
    },
    dispose: function (context) {
      unbind();
      if (context && context.mount) context.mount.replaceChildren();
    }
  };
}
