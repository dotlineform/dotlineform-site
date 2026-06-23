import {
  loadSemanticReferenceRegistry
} from "./semantic-reference-registry.js";
import {
  collectSemanticTargetMatches,
  loadSemanticTargets
} from "./semantic-targets.js";
import {
  createSemanticTargetPickerList
} from "./semantic-target-picker.js";
import {
  buildSemanticReferenceToken,
  selectedTextForToken
} from "./semantic-token-editor.js";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function clearNode(node) {
  if (node) node.replaceChildren();
}

function setStatus(state, message, isError) {
  if (!state.status) return;
  state.status.textContent = message || "";
  state.status.hidden = !message;
  state.status.classList.toggle("is-error", Boolean(isError));
}

function currentSelectionText(adapter) {
  var selection = adapter && typeof adapter.getSelection === "function" ? adapter.getSelection() : null;
  return selectedTextForToken(selection && selection.text);
}

function renderShell(context, state) {
  var documentRef = context.mount && context.mount.ownerDocument ? context.mount.ownerDocument : document;
  var root = documentRef.createElement("section");
  root.className = "docsViewerSemanticPicker";

  var form = documentRef.createElement("div");
  form.className = "docsViewerSemanticPicker__search";

  var input = documentRef.createElement("input");
  input.className = "docsViewerSemanticPicker__input";
  input.type = "search";
  input.autocomplete = "off";
  input.placeholder = "Search targets";
  input.setAttribute("aria-label", "Search semantic reference targets");

  var status = documentRef.createElement("p");
  status.className = "docsViewerSemanticPicker__status muted small";
  status.hidden = true;

  var results = documentRef.createElement("div");
  results.className = "docsViewerSemanticPicker__results";
  results.setAttribute("role", "listbox");
  results.setAttribute("aria-label", "Semantic reference targets");

  form.appendChild(input);
  root.append(form, status, results);
  clearNode(context.mount);
  context.mount.appendChild(root);

  state.root = root;
  state.input = input;
  state.results = results;
  state.status = status;
}

function updateMatches(state) {
  if (!state.list) return;
  var query = cleanString(state.input && state.input.value);
  var matches = collectSemanticTargetMatches(state.targets, query, state.registry, 20);
  state.list.setTargets(matches);
  if (!query) {
    setStatus(state, "", false);
    return;
  }
  if (!matches.length) {
    setStatus(state, "No matching targets.", false);
    return;
  }
  setStatus(state, "", false);
}

function syncQueryFromSelection(state) {
  var text = currentSelectionText(state.adapter);
  if (!state.input) return;
  if (!text) {
    if (state.querySource === "selection" && state.input.value === state.selectionQuery) {
      state.input.value = "";
      state.selectionQuery = "";
      state.querySource = null;
      updateMatches(state);
    }
    return;
  }
  state.selectionQuery = text;
  state.querySource = "selection";
  if (state.input.value === text) return;
  state.input.value = text;
  updateMatches(state);
}

function insertTarget(state, target) {
  if (!target || !state.adapter) return;
  var token = buildSemanticReferenceToken(target);
  if (!token) {
    setStatus(state, "Target title cannot be used as a token label.", true);
    if (typeof state.adapter.focus === "function") state.adapter.focus();
    return;
  }
  if (typeof state.adapter.replaceSelection === "function") {
    state.adapter.replaceSelection(token);
    setStatus(state, "Inserted " + target.kind + ":" + target.id + ".", false);
  }
}

function bindEvents(state) {
  state.onInput = function () {
    state.selectionQuery = "";
    state.querySource = cleanString(state.input && state.input.value) ? "manual" : null;
    updateMatches(state);
  };
  state.onKeydown = function (event) {
    if (event.key === "Escape") {
      if (state.adapter && typeof state.adapter.focus === "function") state.adapter.focus();
      return;
    }
    if (state.list && state.list.handleKeydown(event)) return;
  };
  if (state.input) {
    state.input.addEventListener("input", state.onInput);
    state.input.addEventListener("keydown", state.onKeydown);
  }
  if (state.adapter && typeof state.adapter.onSelectionChange === "function") {
    state.unsubscribeSelection = state.adapter.onSelectionChange(function () {
      syncQueryFromSelection(state);
    });
  }
}

function unbindEvents(state) {
  if (state.input && state.onInput) state.input.removeEventListener("input", state.onInput);
  if (state.input && state.onKeydown) state.input.removeEventListener("keydown", state.onKeydown);
  if (typeof state.unsubscribeSelection === "function") state.unsubscribeSelection();
  if (state.list) state.list.destroy();
  state.unsubscribeSelection = null;
  state.list = null;
}

function loadSupport(context, state) {
  return loadSemanticReferenceRegistry({ fetch: context.fetch })
    .then(function (registry) {
      state.registry = registry;
      return loadSemanticTargets(registry, { fetch: context.fetch });
    })
    .then(function (targets) {
      state.targets = targets;
      state.list = createSemanticTargetPickerList(state.results, {
        onSelect: function (target) {
          insertTarget(state, target);
        }
      });
      syncQueryFromSelection(state);
      updateMatches(state);
      if (state.input) state.input.focus();
    })
    .catch(function (error) {
      setStatus(state, error && error.message ? error.message : "Semantic reference support is unavailable.", true);
    });
}

export function createSemanticTokenPickerView() {
  var state = {
    adapter: null,
    input: null,
    list: null,
    registry: null,
    results: null,
    root: null,
    querySource: null,
    selectionQuery: "",
    status: null,
    targets: [],
    unsubscribeSelection: null
  };

  return {
    mount: function (context) {
      renderShell(context, state);
      var services = context.sourceEditorServices || {};
      state.adapter = typeof services.getActiveSourceEditorContextAdapter === "function"
        ? services.getActiveSourceEditorContextAdapter()
        : null;
      if (!state.adapter) {
        setStatus(state, "Semantic reference insertion is available while editing Markdown source.", true);
        return Promise.resolve(false);
      }
      bindEvents(state);
      return loadSupport(context, state);
    },
    update: function (context) {
      var services = context.sourceEditorServices || {};
      state.adapter = typeof services.getActiveSourceEditorContextAdapter === "function"
        ? services.getActiveSourceEditorContextAdapter()
        : state.adapter;
      syncQueryFromSelection(state);
      return Promise.resolve(true);
    },
    unmount: function (context) {
      unbindEvents(state);
      if (context && context.mount) context.mount.replaceChildren();
    },
    dispose: function (context) {
      unbindEvents(state);
      if (context && context.mount) context.mount.replaceChildren();
    }
  };
}
