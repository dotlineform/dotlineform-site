import {
  catalogueTokenAtSelection,
  normalizeCatalogueDetailId,
  parseCatalogueTokens,
  serializeCatalogueImageToken,
  serializeCatalogueToken
} from "./catalogue-token-parser.js";
import {
  loadSemanticTokenRegistry
} from "./semantic-token-registry.js";
import {
  loadSemanticTokenTargets,
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

function occurrenceDestination(token, target) {
  if (!target) return "";
  if (
    token.presentation === "image"
    && token.targetType === "work"
    && token.detailId
  ) {
    var detailUid = token.targetId + "-" + token.detailId;
    return (
      "/work-details/?detail=" + encodeURIComponent(detailUid)
      + "&from_work=" + encodeURIComponent(token.targetId)
    );
  }
  return target.href || "";
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
  var occurrenceHref = occurrenceDestination(token, target);
  var destinationHref = occurrenceHref
    ? resolveSemanticTokenTargetHref(occurrenceHref, state.publicPreviewBase)
    : "";
  mount.replaceChildren();

  var article = document.createElement("article");
  article.className = "docsViewer__metadataInfo docsViewerCatalogueTokenInfo";
  var heading = document.createElement("h3");
  heading.className = "docsViewer__metadataInfoTitle";
  heading.textContent = token.presentation === "image" ? "Catalogue image" : "Catalogue token";

  var list = document.createElement("dl");
  list.className = "docsViewer__metadataInfoList";
  appendReadOnlyRow(list, "Family", "Catalogue");
  appendReadOnlyRow(list, "Target type", token.targetType);
  appendReadOnlyRow(list, "Target ID", token.targetId);
  appendReadOnlyRow(list, "Catalogue title", target ? target.title : "Target not resolved");
  appendReadOnlyRow(
    list,
    "Destination",
    occurrenceHref || "No resolved destination",
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
    detailInput.value = token.detailId;
    detailInput.disabled = (
      token.targetType !== "work"
      || !target
      || target.hasDetails !== true
    );
    detailField.append(detailLabel, detailInput);
  }

  var occurrenceField = document.createElement("label");
  occurrenceField.className = "docsViewer__field";
  var occurrenceLabel = document.createElement("span");
  occurrenceLabel.className = "docsViewer__fieldLabel";
  occurrenceLabel.textContent = token.presentation === "image" ? "Alt text" : "Title";
  var occurrenceInput = document.createElement("input");
  occurrenceInput.className = "docsViewer__fieldInput";
  occurrenceInput.type = "text";
  occurrenceInput.required = true;
  occurrenceInput.value = token.presentation === "image" ? token.alt : token.title;
  occurrenceField.append(occurrenceLabel, occurrenceInput);

  var imagePresentation = null;
  if (token.presentation === "image") {
    imagePresentation = document.createElement("div");
    imagePresentation.innerHTML = imagePresentationHtml({
      idPrefix: "docsViewerCatalogueImageInfo"
    });
    hydrateImagePresentation(imagePresentation, {
      addCaption: Boolean(token.caption),
      caption: token.caption,
      summary: token.summary,
      placement: token.placement || "full",
      fillWidth: typeof token.fillWidth === "boolean" ? token.fillWidth : true
    });
    bindImagePresentation(imagePresentation);
  }

  var status = document.createElement("p");
  status.className = "docsViewer__metadataInfoEmpty muted small";
  status.hidden = true;

  var actions = document.createElement("div");
  actions.className = "docsViewerCatalogueTokenInfo__actions";
  var updateButton = document.createElement("button");
  updateButton.className = "docsViewer__button";
  updateButton.type = "button";
  updateButton.textContent = token.presentation === "image" ? "Update image" : "Update token";
  var removeButton = document.createElement("button");
  removeButton.className = "docsViewer__button";
  removeButton.type = "button";
  removeButton.textContent = token.presentation === "image" ? "Remove image" : "Remove token";

  function setStatus(message, isError) {
    status.textContent = message || "";
    status.hidden = !message;
    status.classList.toggle("is-error", Boolean(isError));
  }

  updateButton.addEventListener("click", function () {
    var value = cleanString(occurrenceInput.value);
    var serialized;
    if (token.presentation === "image") {
      var detailId = normalizeCatalogueDetailId(detailInput ? detailInput.value : "");
      if (detailId === null) {
        setStatus("Enter a positive Work Detail ID using digits only, or leave it blank.", true);
        detailInput.focus();
        return;
      }
      var presentation = readImagePresentation(imagePresentation);
      var serialization = {
        registry: state.registry,
        targetType: token.targetType,
        targetId: token.targetId,
        detailId: detailId,
        alt: value
      };
      if (presentation.addCaption) {
        Object.assign(serialization, {
          caption: presentation.caption,
          summary: presentation.summary,
          placement: presentation.placement,
          fillWidth: presentation.fillWidth
        });
      }
      serialized = serializeCatalogueImageToken(serialization);
    } else {
      serialized = serializeCatalogueToken({
        registry: state.registry,
        targetType: token.targetType,
        targetId: token.targetId,
        title: value
      });
    }
    if (!serialized) {
      setStatus(
        token.presentation === "image"
          ? "Enter alt text and complete the enabled caption presentation."
          : "Enter a single-line Title.",
        true
      );
      occurrenceInput.focus();
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
  article.append(heading, list);
  if (detailField) article.appendChild(detailField);
  article.appendChild(occurrenceField);
  if (imagePresentation) article.appendChild(imagePresentation);
  article.append(status, actions);
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
