import {
  openDocsViewerManagementModal
} from "../docs-viewer-management-modal-shell.js";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function normalizeBody(value) {
  return String(value == null ? "" : value).replace(/\r\n/g, "\n").replace(/\r/g, "\n");
}

function setHidden(node, hidden) {
  if (node) node.hidden = Boolean(hidden);
}

function clearNode(node) {
  if (node) node.replaceChildren();
}

function diagnosticsText(payload) {
  var messages = [];
  var rebuild = payload && payload.rebuild ? payload.rebuild : null;
  var docs = rebuild && rebuild.docs ? rebuild.docs : null;
  var search = rebuild && rebuild.search ? rebuild.search : null;
  if (payload && payload.summary_text) messages.push(payload.summary_text);
  if (docs && docs.mode) messages.push("Docs payload rebuild: " + docs.mode + ".");
  if (search && search.mode && search.mode !== "none") messages.push("Search rebuild: " + search.mode + ".");
  return messages.join(" ");
}

function openLeavePrompt(root) {
  return openDocsViewerManagementModal({
    root: root,
    title: "Do you want to save changes?",
    size: "compact",
    bodyHtml: '<p class="docsViewer__modalNote muted small">Unsaved Markdown source changes will be discarded if you leave without rebuilding.</p>',
    actions: [
      { role: "modal-primary", label: "Yes" },
      { role: "modal-cancel", label: "No" }
    ]
  }).then(function (result) {
    return Boolean(result && result.confirmed);
  });
}

function renderEditorShell(context, state) {
  var mount = context.mount;
  if (!mount) return;
  clearNode(mount);

  var root = document.createElement("section");
  root.className = "docsViewerSourceEditor";
  root.setAttribute("data-docs-viewer-source-editor", "");

  var dirty = document.createElement("span");
  dirty.className = "docsViewerSourceEditor__dirty muted small";
  dirty.textContent = "Unsaved changes";
  dirty.hidden = true;

  var status = document.createElement("p");
  status.className = "docsViewerSourceEditor__status muted small";
  status.hidden = true;

  var editor = document.createElement("div");
  editor.className = "docsViewerSourceEditor__editor";

  var textarea = document.createElement("textarea");
  textarea.className = "docsViewerSourceEditor__textarea";
  textarea.spellcheck = false;
  textarea.wrap = "soft";
  textarea.setAttribute("aria-label", "Markdown source body");

  editor.append(textarea);
  root.append(dirty, status, editor);
  mount.appendChild(root);

  state.root = root;
  state.status = status;
  state.dirty = dirty;
  state.textarea = textarea;
}

function setStatus(state, message, isError) {
  if (!state.status) return;
  state.status.textContent = message || "";
  state.status.hidden = !message;
  state.status.classList.toggle("is-error", Boolean(isError));
}

function dirtyNow(state) {
  return normalizeBody(state.textarea ? state.textarea.value : "") !== state.lastCleanBody;
}

function projectDirty(state) {
  state.dirtyValue = dirtyNow(state);
  setHidden(state.dirty, !state.dirtyValue);
  if (typeof state.projectMainViewControlState === "function") {
    state.projectMainViewControlState("save-markdown-source", {
      busy: state.busy,
      disabled: state.busy || !state.loaded
    });
    ["source-add-image", "source-add-file"].forEach(function (controlId) {
      state.projectMainViewControlState(controlId, {
        busy: state.busy,
        disabled: state.busy || !state.loaded
      });
    });
  }
}

function setBusy(state, busy) {
  state.busy = Boolean(busy);
  projectDirty(state);
}

function emitSelectionChange(state) {
  if (!state.selectionListeners) return;
  state.selectionListeners.forEach(function (listener) {
    listener();
  });
}

function sourceSelection(state) {
  if (!state.textarea) return { start: 0, end: 0, text: "" };
  var start = state.textarea.selectionStart || 0;
  var end = state.textarea.selectionEnd || 0;
  return {
    start: start,
    end: end,
    text: state.textarea.value.slice(start, end)
  };
}

function createSemanticTokenAdapter(state) {
  return {
    focus: function () {
      if (state.textarea) state.textarea.focus();
    },
    getSelection: function () {
      return sourceSelection(state);
    },
    onSelectionChange: function (listener) {
      if (typeof listener !== "function") return function () {};
      state.selectionListeners.add(listener);
      return function () {
        state.selectionListeners.delete(listener);
      };
    },
    replaceSelection: function (value) {
      if (!state.textarea) return false;
      var selection = sourceSelection(state);
      state.textarea.setRangeText(String(value || ""), selection.start, selection.end, "end");
      state.textarea.dispatchEvent(new Event("input", { bubbles: true }));
      state.textarea.focus();
      return true;
    },
    setStatus: function (message, isError) {
      setStatus(state, message, isError);
    }
  };
}

function loadSource(context, state) {
  var provider = context.collectionProvider || {};
  var doc = context.selectedDoc || null;
  if (!doc || !doc.doc_id) {
    setStatus(state, "Select a document before opening Markdown source.", true);
    return Promise.resolve(null);
  }
  if (typeof provider.readSource !== "function") {
    setStatus(state, "Markdown source editing is unavailable on this route.", true);
    return Promise.resolve(null);
  }

  setBusy(state, true);
  setStatus(state, "Loading source...", false);
  return provider.readSource(doc.doc_id)
    .then(function (payload) {
      state.docId = cleanString(payload.doc_id || doc.doc_id);
      state.revision = cleanString(payload.source_revision);
      state.lastCleanBody = normalizeBody(payload.source_body);
      state.loaded = true;
      if (state.textarea) {
        state.textarea.value = state.lastCleanBody;
        state.textarea.setSelectionRange(0, 0);
        state.textarea.focus();
      }
      setStatus(state, "", false);
      projectDirty(state);
      return payload;
    })
    .catch(function (error) {
      setStatus(state, error && error.message ? error.message : "Failed to load source.", true);
    })
    .finally(function () {
      setBusy(state, false);
    });
}

function rebuildSource(context, state) {
  var provider = context.collectionProvider || {};
  var services = context.sourceEditorServices || {};
  if (!state.loaded || typeof provider.writeSource !== "function") return Promise.resolve(false);

  setBusy(state, true);
  setStatus(state, "Rebuilding doc...", false);
  var nextBody = normalizeBody(state.textarea ? state.textarea.value : "");
  var switchedToRendered = false;
  return provider.writeSource({
    doc_id: state.docId,
    source_revision: state.revision,
    source_body: nextBody
  })
    .then(function (payload) {
      state.revision = cleanString(payload.source_revision);
      state.lastCleanBody = nextBody;
      projectDirty(state);
      setStatus(state, diagnosticsText(payload) || "Doc rebuilt.", false);
      context.documentView.requestMode("rendered-document", { force: true, warn: false });
      switchedToRendered = true;
      if (typeof services.reloadRenderedDoc === "function") {
        return services.reloadRenderedDoc(state.docId).then(function () { return true; });
      }
      return true;
    })
    .catch(function (error) {
      var message = error && error.message ? error.message : "Rebuild failed.";
      if (switchedToRendered) {
        context.documentView.requestMode("markdown-source", { force: true, warn: false });
        if (typeof services.setStatus === "function") services.setStatus(message, true);
      }
      setStatus(state, message, true);
      return false;
    })
    .finally(function () {
      setBusy(state, false);
    });
}

function returnToRendered(context, state) {
  var services = context.sourceEditorServices || {};
  context.documentView.requestMode("rendered-document", { force: true, warn: false });
  if (typeof services.reloadRenderedDoc !== "function") {
    return Promise.resolve(true);
  }

  setBusy(state, true);
  return services.reloadRenderedDoc(state.docId)
    .then(function () {
      return true;
    })
    .catch(function (error) {
      setStatus(state, error && error.message ? error.message : "Failed to return to rendered view.", true);
      context.documentView.requestMode("markdown-source", { force: true, warn: false });
      return false;
    })
    .finally(function () {
      setBusy(state, false);
    });
}

function leaveSource(context, state) {
  if (!dirtyNow(state)) {
    returnToRendered(context, state);
    return;
  }
  openLeavePrompt(context.mount ? context.mount.ownerDocument.body : document.body).then(function (saveFirst) {
    if (saveFirst) {
      rebuildSource(context, state);
      return;
    }
    state.lastCleanBody = normalizeBody(state.textarea ? state.textarea.value : "");
    projectDirty(state);
    returnToRendered(context, state);
  });
}

function addStagedMedia(context, state, mediaKind) {
  if (state.busy || !state.loaded) return Promise.resolve(null);
  var provider = context.collectionProvider || {};
  setBusy(state, true);
  setStatus(state, mediaKind === "file" ? "Loading staged files..." : "Loading staged images...", false);
  return import("./source-editor-media.js")
    .then(function (module) {
      return module.publishAndInsertStagedMedia({
        adapter: state.semanticTokenAdapter,
        mediaKind: mediaKind,
        provider: provider,
        root: context.root || document.body
      });
    })
    .then(function (payload) {
      setStatus(state, payload ? payload.summary_text || "Media reference inserted." : "", false);
      return payload;
    })
    .catch(function (error) {
      setStatus(state, error && error.message ? error.message : "Failed to add media.", true);
      return null;
    })
    .finally(function () {
      setBusy(state, false);
    });
}

function bindEvents(context, state) {
  var root = context.root || document;
  var services = context.sourceEditorServices || {};
  state.projectMainViewControlState = services.projectMainViewControlState;
  state.onInput = function () {
    projectDirty(state);
    emitSelectionChange(state);
  };
  state.onSelectionChange = function () {
    emitSelectionChange(state);
  };
  state.onClick = function (event) {
    var action = event.target.closest("[data-source-editor-action]");
    if (!action || action.disabled) return;
    if (action.dataset.sourceEditorAction === "back") {
      leaveSource(context, state);
    }
  };
  state.onToolbarSave = function () {
    rebuildSource(context, state);
  };
  state.onToolbarAddImage = function () {
    addStagedMedia(context, state, "image");
  };
  state.onToolbarAddFile = function () {
    addStagedMedia(context, state, "file");
  };
  state.onBeforeUnload = function (event) {
    if (!dirtyNow(state)) return;
    event.preventDefault();
    event.returnValue = "";
  };

  if (state.textarea) {
    state.textarea.addEventListener("input", state.onInput);
    state.textarea.addEventListener("keyup", state.onSelectionChange);
    state.textarea.addEventListener("mouseup", state.onSelectionChange);
    state.textarea.addEventListener("select", state.onSelectionChange);
  }
  if (state.root) state.root.addEventListener("click", state.onClick);
  if (root && state.onToolbarSave) root.addEventListener("docs-viewer-source-editor-save", state.onToolbarSave);
  if (root && state.onToolbarAddImage) root.addEventListener("docs-viewer-source-editor-add-image", state.onToolbarAddImage);
  if (root && state.onToolbarAddFile) root.addEventListener("docs-viewer-source-editor-add-file", state.onToolbarAddFile);
  window.addEventListener("beforeunload", state.onBeforeUnload);
  projectDirty(state);
}

function unbindEvents(context, state) {
  var root = context && context.root ? context.root : document;
  if (state.textarea && state.onInput) state.textarea.removeEventListener("input", state.onInput);
  if (state.textarea && state.onSelectionChange) {
    state.textarea.removeEventListener("keyup", state.onSelectionChange);
    state.textarea.removeEventListener("mouseup", state.onSelectionChange);
    state.textarea.removeEventListener("select", state.onSelectionChange);
  }
  if (state.root && state.onClick) state.root.removeEventListener("click", state.onClick);
  if (root && state.onToolbarSave) root.removeEventListener("docs-viewer-source-editor-save", state.onToolbarSave);
  if (root && state.onToolbarAddImage) root.removeEventListener("docs-viewer-source-editor-add-image", state.onToolbarAddImage);
  if (root && state.onToolbarAddFile) root.removeEventListener("docs-viewer-source-editor-add-file", state.onToolbarAddFile);
  if (state.onBeforeUnload) window.removeEventListener("beforeunload", state.onBeforeUnload);
  state.projectMainViewControlState = null;
}

export function createDocsViewerSourceEditorMode() {
  var state = {
    busy: false,
    dirtyValue: false,
    docId: "",
    lastCleanBody: "",
    loaded: false,
    revision: "",
    root: null,
    selectionListeners: new Set(),
    status: null,
    textarea: null,
    projectMainViewControlState: null
  };

  return {
    mount: function (context) {
      context.documentView.projectToolbar({
        toolbarHidden: false,
        metaHidden: true,
        contentHidden: false,
        resultsHidden: true,
        moreHidden: true,
        clearMore: true
      });
      renderEditorShell(context, state);
      bindEvents(context, state);
      state.semanticTokenAdapter = createSemanticTokenAdapter(state);
      var services = context.sourceEditorServices || {};
      if (typeof services.setActiveSourceEditorContextAdapter === "function") {
        services.setActiveSourceEditorContextAdapter(state.semanticTokenAdapter);
      }
      return loadSource(context, state);
    },
    beforeLeave: function (context) {
      if (cleanString(context.requestedModeId) === "markdown-source") return true;
      leaveSource(context, state);
      return false;
    },
    update: function (context) {
      if (state.docId === cleanString(context.selectedDoc && context.selectedDoc.doc_id)) return Promise.resolve(null);
      return loadSource(context, state);
    },
    unmount: function (context) {
      var services = context.sourceEditorServices || {};
      if (typeof services.clearActiveSourceEditorContextAdapter === "function") {
        services.clearActiveSourceEditorContextAdapter(state.semanticTokenAdapter);
      }
      state.selectionListeners.clear();
      unbindEvents(context, state);
      if (context && context.mount) context.mount.replaceChildren();
    },
    dispose: function (context) {
      var services = context.sourceEditorServices || {};
      if (typeof services.clearActiveSourceEditorContextAdapter === "function") {
        services.clearActiveSourceEditorContextAdapter(state.semanticTokenAdapter);
      }
      state.selectionListeners.clear();
      unbindEvents(context, state);
      if (context && context.mount) context.mount.replaceChildren();
    }
  };
}
