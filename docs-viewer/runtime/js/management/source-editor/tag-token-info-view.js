import {
  parseTagTokens,
  serializeTagToken,
  tagTokenAtSelection
} from "./tag-token-parser.js";
import {
  loadSemanticTokenRegistry
} from "./semantic-token-registry.js";
import {
  loadSemanticTokenTargets
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
  var token = tagTokenAtSelection(
    parseTagTokens(snapshot.value, { registry: state.registry }),
    selection
  );
  if (!token) return null;
  var capture = {
    start: token.start,
    end: token.end,
    text: token.raw,
    revision: snapshot.revision
  };
  if (selection.start === selection.end && adapter.selectCapturedRange) {
    adapter.selectCapturedRange(capture);
  }
  return { token: token, capture: capture };
}

function renderToken(context, state, active) {
  var token = active.token;
  var target = state.targetsByKey.get(token.targetId) || null;
  var destination = target ? target.href : "";
  context.mount.replaceChildren();
  var article = document.createElement("article");
  article.className = "docsViewer__metadataInfo docsViewerCatalogueTokenInfo";
  var heading = document.createElement("h3");
  heading.className = "docsViewer__metadataInfoTitle";
  heading.textContent = "Tag token";
  var list = document.createElement("dl");
  list.className = "docsViewer__metadataInfoList";
  appendReadOnlyRow(list, "Family", "Tag");
  appendReadOnlyRow(list, "Target ID", token.targetId);
  appendReadOnlyRow(list, "Aliases", target && target.aliases.length ? target.aliases.join(", ") : "None");
  appendReadOnlyRow(list, "Group", target && target.meta[0] ? target.meta[0] : "Target not resolved");
  appendReadOnlyRow(list, "Resolved document", target && target.meta[1] ? target.meta[1] : "Target not resolved");
  appendReadOnlyRow(list, "Destination", target ? target.href : "No resolved destination", destination);

  var field = document.createElement("label");
  field.className = "docsViewer__field";
  var label = document.createElement("span");
  label.className = "docsViewer__fieldLabel";
  label.textContent = "Title";
  var input = document.createElement("input");
  input.className = "docsViewer__fieldInput";
  input.type = "text";
  input.required = true;
  input.value = token.title;
  field.append(label, input);

  var status = document.createElement("p");
  status.className = "docsViewer__metadataInfoEmpty muted small";
  status.hidden = true;
  function setError(message) {
    status.textContent = message;
    status.hidden = false;
    status.classList.add("is-error");
  }

  var actions = document.createElement("div");
  actions.className = "docsViewerCatalogueTokenInfo__actions";
  var updateButton = document.createElement("button");
  updateButton.className = "docsViewer__button";
  updateButton.type = "button";
  updateButton.textContent = "Update token";
  updateButton.addEventListener("click", function () {
    var serialized = serializeTagToken({
      registry: state.registry,
      targetId: token.targetId,
      title: cleanString(input.value)
    });
    if (!serialized) {
      setError("Enter a single-line Title.");
      input.focus();
      return;
    }
    if (
      !state.adapter
      || typeof state.adapter.replaceCapturedRange !== "function"
      || !state.adapter.replaceCapturedRange(active.capture, serialized, "select")
    ) {
      setError("Markdown source changed. Select the token again.");
    }
  });
  var removeButton = document.createElement("button");
  removeButton.className = "docsViewer__button";
  removeButton.type = "button";
  removeButton.textContent = "Remove token";
  removeButton.addEventListener("click", function () {
    if (
      !state.adapter
      || typeof state.adapter.replaceCapturedRange !== "function"
      || !state.adapter.replaceCapturedRange(active.capture, "", "end")
    ) {
      setError("Markdown source changed. Select the token again.");
    }
  });
  actions.append(updateButton, removeButton);
  article.append(heading, list, field, status, actions);
  context.mount.appendChild(article);
}

function render(context, state) {
  if (!context.mount) return;
  if (!state.loaded) {
    emptyMessage(context.mount, "Tag token info is loading.");
    return;
  }
  var active = currentToken(state);
  if (!active) {
    emptyMessage(context.mount, "Place the caret inside a Tag token to inspect it.");
    return;
  }
  renderToken(context, state, active);
}

function loadSupport(state) {
  return loadSemanticTokenRegistry({ fetch: state.fetch }).then(function (registry) {
    state.registry = registry;
    return loadSemanticTokenTargets(registry, { fetch: state.fetch });
  }).then(function (targets) {
    state.targetsByKey = new Map(targets.filter(function (target) {
      return target.family === "tag" && target.targetType === "tag";
    }).map(function (target) {
      return [target.targetId, target];
    }));
    state.loaded = true;
  });
}

export function createTagTokenInfoView(options = {}) {
  var state = {
    adapter: null,
    fetch: options.fetch,
    loaded: false,
    registry: null,
    targetsByKey: new Map(),
    unsubscribe: null
  };
  function unbind() {
    if (typeof state.unsubscribe === "function") state.unsubscribe();
    state.unsubscribe = null;
    state.adapter = null;
  }
  return {
    mount: function (context) {
      var services = context.sourceEditorServices || {};
      state.adapter = typeof services.getActiveSourceEditorContextAdapter === "function"
        ? services.getActiveSourceEditorContextAdapter()
        : null;
      if (state.adapter && state.adapter.onSelectionChange) {
        state.unsubscribe = state.adapter.onSelectionChange(function () {
          render(context, state);
        });
      }
      render(context, state);
      return loadSupport(state).then(function () {
        render(context, state);
      }).catch(function () {
        state.loaded = true;
        render(context, state);
      });
    },
    update: function (context) { render(context, state); },
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
