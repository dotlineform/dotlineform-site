import {
  openDocsViewerManagementModal
} from "../docs-viewer-management-modal-shell.js";
import {
  managedDocumentTargetsEqual,
  normalizeManagedDocumentTarget
} from "../docs-viewer-management-document-target.js";
import { localFolderPasteReplacement } from "./local-folder-links.js";
import { createSourceEditorTokenDrafts } from "./source-editor-token-drafts.js";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function normalizeBody(value) {
  return String(value == null ? "" : value).replace(/\r\n/g, "\n").replace(/\r/g, "\n");
}

function setHidden(node, hidden) {
  if (node) node.hidden = Boolean(hidden);
}

function openLeavePrompt(root) {
  return openDocsViewerManagementModal({
    root: root,
    title: "Return to doc?",
    size: "compact",
    bodyHtml: '<p class="docsViewer__modalNote muted small">Unsaved document changes will be discarded if you leave without saving.</p>',
    actions: [
      { role: "modal-primary", label: "Return to doc" },
      { role: "modal-cancel", label: "Cancel" }
    ]
  }).then(function (result) {
    return Boolean(result && result.confirmed);
  });
}

function renderEditorShell(context, state) {
  var mount = context.mount;
  if (!mount) return;

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
  return normalizeBody(state.textarea ? state.textarea.value : "") !== state.lastCleanBody
    || state.tokenDrafts.isDirty()
    || ["title", "summary"].some(function (field) {
      return state.metadataDraft[field] !== state.lastCleanMetadata[field];
    });
}

function projectDirty(state) {
  state.dirtyValue = dirtyNow(state);
  setHidden(state.dirty, !state.dirtyValue);
  if (typeof state.projectMainViewControlState === "function") {
    state.projectMainViewControlState("save-markdown-source", {
      busy: state.busy,
      disabled: state.busy || !state.loaded
    });
    state.projectMainViewControlState("return-to-doc", {
      busy: state.busy,
      disabled: state.busy
    });
    ["source-add-image", "source-add-file"].concat(state.sourceActionControlIds || []).forEach(function (controlId) {
      state.projectMainViewControlState(controlId, {
        busy: state.busy,
        disabled: state.busy || !state.loaded
      });
    });
  }
}

function setBusy(state, busy) {
  state.busy = Boolean(busy);
  if (state.textarea) state.textarea.readOnly = state.busy;
  projectDirty(state);
  state.sessionListeners.forEach(function (listener) { listener(); });
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

function capturedRangeIsCurrent(state, capture) {
  if (!state.textarea || !capture || typeof capture !== "object") return false;
  var start = Number(capture.start);
  var end = Number(capture.end);
  if (
    !Number.isInteger(start)
    || !Number.isInteger(end)
    || start < 0
    || end < start
    || end > state.textarea.value.length
    || Number(capture.revision) !== state.bufferRevision
    || state.textarea.value.slice(start, end) !== String(capture.text || "")
  ) {
    return false;
  }
  return { start: start, end: end };
}

function replaceCapturedRange(state, capture, value, selectionMode) {
  if (state.saving || !state.loaded) return false;
  var range = capturedRangeIsCurrent(state, capture);
  if (!range) return false;
  var mode = ["select", "start", "end", "preserve"].includes(selectionMode)
    ? selectionMode
    : "end";
  state.textarea.setRangeText(String(value || ""), range.start, range.end, mode);
  state.textarea.dispatchEvent(new Event("input", { bubbles: true }));
  state.textarea.focus();
  return true;
}

function createSourceEditorContextAdapter(state) {
  return {
    captureSelection: function () {
      return Object.assign(sourceSelection(state), { revision: state.bufferRevision });
    },
    focus: function () {
      if (state.textarea) state.textarea.focus();
    },
    getBufferSnapshot: function () {
      return {
        revision: state.bufferRevision,
        value: state.textarea ? state.textarea.value : ""
      };
    },
    getDocumentTarget: function () {
      return state.target ? Object.assign({}, state.target) : null;
    },
    getDocumentSubject: function () {
      return state.subject ? Object.assign({}, state.subject) : null;
    },
    /** Views write each input event into the session, independently of their mounts. */
    getMetadataDraft: function () {
      return Object.assign({}, state.metadataDraft);
    },
    selectMetadataContext: function () { state.metadataContext = true; emitSelectionChange(state); },
    isMetadataContext: function () { return Boolean(state.metadataContext); },
    getSessionState: function () { return { loaded: state.loaded, busy: state.busy }; },
    onSessionChange: function (listener) {
      state.sessionListeners.add(listener);
      return function () { state.sessionListeners.delete(listener); };
    },
    getTokenDraft: function (token, capture, registry) {
      return state.tokenDrafts.get(token, capture, registry);
    },
    updateTokenDraft: function (draft, values) {
      if (state.busy || !state.loaded) return false;
      draft.values = values;
      projectDirty(state);
      return true;
    },
    removeTokenDraft: function (draft) { state.tokenDrafts.remove(draft); projectDirty(state); },
    setMetadataField: function (field, value) {
      if (!state.loaded || state.busy || !["title", "summary"].includes(field)) return false;
      state.metadataDraft[field] = String(value == null ? "" : value);
      projectDirty(state);
      return true;
    },
    readCatalogueMediaTargets: function () {
      return state.collectionProvider.readCatalogueMediaTargets();
    },
    readDocumentLinkTargets: function () {
      var target = { stage: state.target.stage };
      if (state.target.stage) target.stage = state.target.stage;
      return state.collectionProvider.readDocumentLinkTargets(target);
    },
    readCatalogueWork: function (workId) {
      return state.collectionProvider.readCatalogueWork(workId);
    },
    readCatalogueSeriesPresentation: function (seriesId) {
      return state.collectionProvider.readCatalogueSeriesPresentation(seriesId);
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
      if (!state.textarea || !state.loaded || state.saving) return false;
      var selection = sourceSelection(state);
      state.textarea.setRangeText(String(value || ""), selection.start, selection.end, "end");
      state.textarea.dispatchEvent(new Event("input", { bubbles: true }));
      state.textarea.focus();
      return true;
    },
    replaceCapturedSelection: function (capture, value) {
      return replaceCapturedRange(state, capture, value, "end");
    },
    replaceCapturedRange: function (capture, value, selectionMode) {
      return replaceCapturedRange(state, capture, value, selectionMode);
    },
    selectCapturedRange: function (capture) {
      var range = capturedRangeIsCurrent(state, capture);
      if (!range) return false;
      state.textarea.setSelectionRange(range.start, range.end);
      state.textarea.focus();
      emitSelectionChange(state);
      return true;
    },
    setStatus: function (message, isError) {
      setStatus(state, message, isError);
    }
  };
}

function loadSource(context, state) {
  var provider = context.collectionProvider || {};
  if (typeof provider.readSource !== "function") {
    setStatus(state, "Markdown source editing is unavailable on this route.", true);
    return Promise.resolve(null);
  }

  setBusy(state, true);
  setStatus(state, "Loading source...", false);
  return provider.readSource(state.target)
    .then(function (payload) {
      var responseTarget = {
        ...(payload && payload.stage ? { stage: payload.stage } : {}),
        doc_id: cleanString(payload && payload.doc_id)
      };
      if (payload && Object.prototype.hasOwnProperty.call(payload, "collection")) {
        responseTarget.collection = cleanString(payload.collection);
      }
      if (!managedDocumentTargetsEqual(responseTarget, state.target)) {
        throw new Error("Source service returned a different managed document target.");
      }
      if (!payload.metadata || typeof payload.metadata !== "object" || Array.isArray(payload.metadata)
        || payload.metadata.doc_id !== state.target.doc_id
        || typeof payload.source_front_matter !== "string" || typeof payload.source_body !== "string") {
        throw new Error("Source service did not return the complete document.");
      }
      state.frontMatterSource = payload.source_front_matter;
      state.metadataDraft = Object.assign({}, payload.metadata, {
        title: String(payload.metadata.title == null ? "" : payload.metadata.title),
        summary: String(payload.metadata.summary == null ? "" : payload.metadata.summary)
      });
      state.lastCleanMetadata = Object.assign({}, state.metadataDraft);
      state.lastCleanBody = normalizeBody(payload.source_body);
      state.previousBody = state.lastCleanBody;
      state.subject = payload.subject;
      state.loaded = true;
      if (state.textarea) {
        state.textarea.value = state.lastCleanBody;
        state.textarea.setSelectionRange(0, 0);
        state.textarea.focus();
      }
      state.bufferRevision = 0;
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

function saveSource(context, state) {
  var provider = context.collectionProvider || {};
  var services = context.sourceEditorServices || {};
  if (!state.loaded || state.busy || typeof provider.writeSource !== "function") return Promise.resolve(false);
  if (!cleanString(state.metadataDraft.title)) {
    setStatus(state, "Enter a title.", true);
    return Promise.resolve(false);
  }

  setBusy(state, true);
  state.saving = true;
  setStatus(state, "Saving doc...", false);
  var snapshot = state.sourceEditorAdapter.getBufferSnapshot();
  return state.tokenDrafts.prepare(snapshot, state.sourceEditorAdapter).then(function (body) {
    return provider.writeSource(state.target, {
      source_front_matter: state.frontMatterSource,
      source_body: normalizeBody(body),
      metadata: { title: state.metadataDraft.title, summary: state.metadataDraft.summary }
    });
  })
    .then(function (payload) {
      state.frontMatterSource = payload.source_front_matter;
      state.metadataDraft = Object.assign({}, payload.metadata, {
        title: String(payload.metadata.title == null ? "" : payload.metadata.title),
        summary: String(payload.metadata.summary == null ? "" : payload.metadata.summary)
      });
      state.lastCleanMetadata = Object.assign({}, state.metadataDraft);
      state.lastCleanBody = normalizeBody(payload.source_body);
      state.previousBody = state.lastCleanBody;
      state.tokenDrafts.clear();
      if (state.textarea) state.textarea.value = state.lastCleanBody;
      state.saving = false;
      setBusy(state, false);
      setStatus(state, payload.summary_text || "Doc saved.", false);
      // Rendering is independent of a successful source write and cannot fail Save.
      Promise.resolve().then(function () {
        return context.documentView.requestMode("rendered-document", { force: true, warn: false });
      }).catch(function (error) {
        if (typeof services.setStatus === "function") {
          services.setStatus("Doc saved. Could not return to rendered view: " + error.message, true);
        }
      });
      return true;
    })
    .catch(function (error) {
      var message = error && error.message ? error.message : "Save failed.";
      setStatus(state, message, true);
      return false;
    })
    .finally(function () {
      state.saving = false;
      setBusy(state, false);
    });
}

function returnToRendered(context) {
  context.documentView.requestMode("rendered-document", { force: true, warn: false });
  return Promise.resolve(true);
}

function leaveSource(context, state) {
  return confirmNavigation(context, state).then(function (confirmed) {
    return confirmed ? returnToRendered(context) : false;
  });
}

async function confirmNavigation(context, state) {
  if (state.busy) return false;
  if (!dirtyNow(state)) return true;
  var confirmed = await openLeavePrompt(context.root || document.body);
  if (!confirmed) return false;
  state.lastCleanBody = normalizeBody(state.textarea.value);
  state.lastCleanMetadata = Object.assign({}, state.metadataDraft);
  state.tokenDrafts.clear();
  projectDirty(state);
  return true;
}

function addStagedMedia(context, state, mediaKind) {
  if (state.busy || !state.loaded) return Promise.resolve(null);
  var provider = context.collectionProvider || {};
  setBusy(state, true);
  setStatus(state, mediaKind === "file" ? "Loading files..." : "Loading images...", false);
  return import("./source-editor-media.js")
    .then(function (module) {
      return module.publishAndInsertStagedMedia({
        adapter: state.sourceEditorAdapter,
        mediaKind: mediaKind,
        provider: provider,
        target: Object.assign({}, state.target),
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
  state.sourceActionControlIds = Array.isArray(services.sourceEditorActionControlIds)
    ? services.sourceEditorActionControlIds.map(cleanString).filter(Boolean)
    : [];
  state.onInput = function () {
    state.bufferRevision += 1;
    state.tokenDrafts.reconcile(state.previousBody, state.textarea.value, state.bufferRevision);
    state.previousBody = state.textarea.value;
    projectDirty(state);
    emitSelectionChange(state);
  };
  state.onSelectionChange = function () {
    state.metadataContext = false;
    emitSelectionChange(state);
  };
  state.onPaste = function (event) {
    var capability = typeof services.localFolderLinksCapability === "function" ? services.localFolderLinksCapability() : null;
    if (!state.loaded || state.busy || !capability || capability.authoring !== true || !capability.base_path) return;
    var selection = sourceSelection(state);
    var replacement = localFolderPasteReplacement({
      text: event.clipboardData ? event.clipboardData.getData("text/plain") : "",
      basePath: capability.base_path,
      markdown: state.textarea.value,
      start: selection.start,
      end: selection.end
    });
    if (!replacement) return;
    event.preventDefault();
    state.textarea.setRangeText(replacement, selection.start, selection.end, "end");
    state.textarea.dispatchEvent(new Event("input", { bubbles: true }));
  };
  state.onClick = function (event) {
    var action = event.target.closest("[data-source-editor-action]");
    if (!action || action.disabled) return;
    if (action.dataset.sourceEditorAction === "back") {
      leaveSource(context, state);
    }
  };
  state.onToolbarSave = function () {
    saveSource(context, state);
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
    state.textarea.addEventListener("paste", state.onPaste);
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
  if (state.textarea && state.onPaste) state.textarea.removeEventListener("paste", state.onPaste);
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
  state.sourceActionControlIds = [];
}

function restoreRenderedContent(context, state) {
  if (!context.mount || !state.root) return;
  state.root.remove();
  context.mount.scrollTop = state.renderedScrollTop;
  state.root = null;
}

export function createDocsViewerSourceEditorMode() {
  var state = {
    busy: false,
    saving: false,
    bufferRevision: 0,
    dirtyValue: false,
    lastCleanBody: "",
    lastCleanMetadata: {},
    previousBody: "",
    tokenDrafts: createSourceEditorTokenDrafts(),
    sessionListeners: new Set(),
    metadataDraft: {},
    frontMatterSource: "",
    loaded: false,
    collectionProvider: null,
    root: null,
    renderedScrollTop: 0,
    selectionListeners: new Set(),
    sourceActionControlIds: [],
    status: null,
    subject: null,
    target: null,
    textarea: null,
    projectMainViewControlState: null
  };

  return {
    mount: function (context) {
      state.target = normalizeManagedDocumentTarget(context.sourceTarget);
      state.busy = false;
      state.saving = false;
      state.bufferRevision = 0;
      state.dirtyValue = false;
      state.lastCleanBody = "";
      state.lastCleanMetadata = {};
      state.previousBody = "";
      state.tokenDrafts.clear();
      state.metadataDraft = {};
      state.metadataContext = false;
      state.frontMatterSource = "";
      state.subject = null;
      state.loaded = false;
      state.collectionProvider = context.collectionProvider || null;
      state.renderedScrollTop = context.mount.scrollTop;
      // Keep the rendered report mounted so its collection target survives Source.
      // Source-mode CSS hides it until this editor is removed on return.
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
      state.sourceEditorAdapter = createSourceEditorContextAdapter(state);
      var services = context.sourceEditorServices || {};
      if (typeof services.setActiveSourceEditorContextAdapter === "function") {
        services.setActiveSourceEditorContextAdapter(state.sourceEditorAdapter);
      }
      return loadSource(context, state);
    },
    beforeLeave: function (context) {
      if (state.busy) return false;
      if (cleanString(context.requestedModeId) === "markdown-source") return true;
      if (!dirtyNow(state)) return true;
      leaveSource(context, state);
      return false;
    },
    confirmNavigation: function (context) { return confirmNavigation(context, state); },
    update: function (_context) {
      return Promise.resolve(null);
    },
    unmount: function (context) {
      var services = context.sourceEditorServices || {};
      if (typeof services.clearActiveSourceEditorContextAdapter === "function") {
        services.clearActiveSourceEditorContextAdapter(state.sourceEditorAdapter);
      }
      state.selectionListeners.clear();
      state.sessionListeners.clear();
      unbindEvents(context, state);
      restoreRenderedContent(context, state);
    },
    dispose: function (context) {
      var services = context.sourceEditorServices || {};
      if (typeof services.clearActiveSourceEditorContextAdapter === "function") {
        services.clearActiveSourceEditorContextAdapter(state.sourceEditorAdapter);
      }
      state.selectionListeners.clear();
      state.sessionListeners.clear();
      unbindEvents(context, state);
      restoreRenderedContent(context, state);
    }
  };
}
