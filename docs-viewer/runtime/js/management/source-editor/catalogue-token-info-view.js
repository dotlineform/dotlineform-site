import {
  catalogueTokenAtSelection,
  parseCatalogueTokens
} from "./catalogue-token-parser.js";
import {
  loadSemanticTokenRegistry
} from "./semantic-token-registry.js";
import { readCatalogueTokenPresentation } from "./catalogue-media-support.js";
import {
  resolveSemanticTokenTargetHref
} from "./semantic-token-targets.js";
import {
  bindImagePresentation,
  hydrateImagePresentation,
  imagePresentationHtml,
  readImagePresentation
} from "./source-editor-image-presentation.js";

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
  return { token: token, capture: capture };
}

function renderToken(context, state, active) {
  var mount = context.mount;
  var token = active.token;
  var capture = active.capture;
  var draft = state.adapter.getTokenDraft(token, capture, state.registry);
  var values = draft.values;
  var target = state.targetsByKey.get(targetKey(token)) || null;
  var occurrenceHref = target && target.href || "";
  var destinationHref = occurrenceHref
    ? resolveSemanticTokenTargetHref(occurrenceHref, state.publicPreviewBase)
    : "";
  mount.replaceChildren();

  var article = document.createElement("article");
  article.className = "docsViewer__metadataInfo docsViewerCatalogueTokenInfo";
  var heading = document.createElement("h3");
  heading.className = "docsViewer__metadataInfoTitle";
  heading.textContent = token.presentation === "image" ? "Catalogue image" : "Media View link";

  var list = document.createElement("dl");
  list.className = "docsViewer__metadataInfoList";
  appendReadOnlyRow(list, "Family", "Catalogue");
  appendReadOnlyRow(list, "Target type", token.targetType);
  appendReadOnlyRow(list, "Target ID", token.targetId);
  if (token.detailId) appendReadOnlyRow(list, "Detail UID", token.targetId + "-" + token.detailId);
  appendReadOnlyRow(list, "Catalogue title", target ? target.title : "Target not resolved");
  appendReadOnlyRow(
    list,
    "Destination",
    occurrenceHref || (token.targetType === "series" ? "Series gallery in Media View" : "No resolved destination"),
    destinationHref
  );

  var detailField = null;
  var detailInput = null;
  if (token.presentation === "image") {
    detailField = document.createElement("label");
    detailField.className = "docsViewer__field";
    var detailLabel = document.createElement("span");
    detailLabel.className = "docsViewer__fieldLabel";
    detailLabel.textContent = "Work Detail ID";
    detailInput = document.createElement("input");
    detailInput.className = "docsViewer__fieldInput";
    detailInput.type = "text";
    detailInput.dataset.role = "catalogue-work-detail-id";
    detailInput.inputMode = "numeric";
    detailInput.pattern = "[0-9]*";
    detailInput.value = values.detailId;
    detailInput.disabled = token.targetType !== "work";
    detailField.append(detailLabel, detailInput);
  }

  var occurrenceField = document.createElement("label");
  occurrenceField.className = "docsViewer__field";
  var occurrenceLabel = document.createElement("span");
  occurrenceLabel.className = "docsViewer__fieldLabel";
  occurrenceLabel.textContent = token.presentation === "image" ? "Alt text" : "Link text";
  var occurrenceInput = document.createElement("input");
  occurrenceInput.className = "docsViewer__fieldInput";
  occurrenceInput.type = "text";
  occurrenceInput.required = true;
  occurrenceInput.value = values.text;
  occurrenceField.append(occurrenceLabel, occurrenceInput);

  var imagePresentation = null;
  if (token.presentation === "image") {
    imagePresentation = document.createElement("div");
    imagePresentation.innerHTML = imagePresentationHtml({
      idPrefix: "docsViewerCatalogueImageInfo"
    });
    hydrateImagePresentation(imagePresentation, values);
    // Keep raw pending input; normalization belongs to the session's Save validation.
    imagePresentation.querySelector('[data-role="staged-media-caption-text"]').value = values.caption;
    imagePresentation.querySelector('[data-role="staged-media-summary"]').value = values.summary;
    bindImagePresentation(imagePresentation);
  }

  var status = document.createElement("p");
  status.className = "docsViewer__metadataInfoEmpty muted small";
  status.hidden = true;

  var actions = document.createElement("div");
  actions.className = "docsViewerCatalogueTokenInfo__actions";
  var removeButton = document.createElement("button");
  removeButton.className = "docsViewer__button";
  removeButton.type = "button";
  removeButton.textContent = token.presentation === "image" ? "Remove image" : "Remove token";

  function setStatus(message, isError) {
    status.textContent = message || "";
    status.hidden = !message;
    status.classList.toggle("is-error", Boolean(isError));
  }

  var fields = document.createElement("fieldset");
  fields.className = "docsViewerSourceEditor__metadataFields";
  fields.disabled = state.adapter.getSessionState().busy;
  function captureInput() {
    var presentation = imagePresentation ? Object.assign(readImagePresentation(imagePresentation), {
      caption: imagePresentation.querySelector('[data-role="staged-media-caption-text"]').value,
      summary: imagePresentation.querySelector('[data-role="staged-media-summary"]').value
    }) : {};
    state.adapter.updateTokenDraft(draft, Object.assign({}, values, {
      text: occurrenceInput.value,
      detailId: detailInput ? detailInput.value : token.detailId
    }, presentation));
  }
  fields.addEventListener("input", captureInput);
  fields.addEventListener("change", captureInput);
  state.projectBusy = function () { fields.disabled = state.adapter.getSessionState().busy; };

  removeButton.addEventListener("click", function () {
    if (
      !state.adapter
      || typeof state.adapter.replaceCapturedRange !== "function"
      || !state.adapter.replaceCapturedRange(capture, "", "end")
    ) {
      setStatus("Markdown source changed. Select the token again.", true);
      return;
    } else {
      state.adapter.removeTokenDraft(draft);
    }
  });

  actions.append(removeButton);
  article.append(heading, list);
  if (detailField) fields.appendChild(detailField);
  fields.appendChild(occurrenceField);
  if (imagePresentation) fields.appendChild(imagePresentation);
  fields.appendChild(actions);
  article.append(fields, status);
  mount.appendChild(article);
}

function render(context, state) {
  if (!context.mount) return;
  if (!state.loaded) {
    state.renderKey = "";
    emptyMessage(context.mount, "Catalogue token info is loading.");
    return;
  }
  var active = currentToken(state);
  if (!active) {
    state.renderKey = "";
    emptyMessage(context.mount, "Place the caret inside a Catalogue token to inspect it.");
    return;
  }
  var key = targetKey(active.token) + ":" + active.token.detailId;
  if (state.targetKey !== key) {
    state.renderKey = "";
    emptyMessage(context.mount, "Catalogue target info is loading.");
    if (state.loadingKey === key) return;
    state.loadingKey = key;
    var adapter = state.adapter;
    var load = readCatalogueTokenPresentation(adapter, active.token, active.token.detailId).then(function (presentation) {
          return [{ family: "catalogue", targetType: active.token.targetType, targetId: active.token.targetId,
            title: presentation.label, href: presentation.newTabTarget }];
        });
    load.catch(function () { return []; }).then(function (targets) {
      if (state.adapter !== adapter || state.loadingKey !== key) return;
      state.targetsByKey = new Map(targets.map(function (target) { return [targetKey(target), target]; }));
      state.targetKey = key;
      state.loadingKey = "";
      render(context, state);
    });
    return;
  }
  state.loadingKey = "";
  var renderKey = [active.capture.revision, active.capture.start, active.capture.end, active.capture.text].join(":");
  if (state.renderKey === renderKey) return;
  state.renderKey = renderKey;
  renderToken(context, state, active);
}

function loadSupport(state) {
  return loadSemanticTokenRegistry({ fetch: state.fetch })
    .then(function (registry) {
      state.registry = registry;
      state.loaded = true;
    });
}

export function createCatalogueTokenInfoView(options = {}) {
  var state = {
    adapter: null,
    fetch: options.fetch,
    generation: 0,
    loaded: false,
    targetKey: "",
    loadingKey: "",
    publicPreviewBase: "",
    registry: null,
    targetsByKey: new Map(),
    unsubscribe: null,
    sessionUnsubscribe: null,
    projectBusy: null,
    renderKey: ""
  };

  function bind(context) {
    var services = context.sourceEditorServices || {};
    state.adapter = typeof services.getActiveSourceEditorContextAdapter === "function"
      ? services.getActiveSourceEditorContextAdapter()
      : null;
    state.publicPreviewBase = cleanString(services.publicPreviewBase);
    if (state.adapter) state.sessionUnsubscribe = state.adapter.onSessionChange(function () {
      if (state.projectBusy) state.projectBusy();
    });
    if (state.adapter && typeof state.adapter.onSelectionChange === "function") {
      state.unsubscribe = state.adapter.onSelectionChange(function () {
        render(context, state);
      });
    }
  }

  function unbind() {
    state.generation += 1;
    if (typeof state.unsubscribe === "function") state.unsubscribe();
    state.unsubscribe = null;
    if (state.sessionUnsubscribe) state.sessionUnsubscribe();
    state.sessionUnsubscribe = null;
    state.projectBusy = null;
    state.renderKey = "";
    state.adapter = null;
    state.targetKey = "";
    state.loadingKey = "";
  }

  return {
    mount: function (context) {
      var generation = state.generation;
      bind(context);
      render(context, state);
      return loadSupport(state)
        .then(function () {
          if (state.generation === generation) render(context, state);
        })
        .catch(function () {
          if (state.generation !== generation) return;
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
