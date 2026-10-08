import {
  openDocsViewerManagementModal
} from "../docs-viewer-management-modal-shell.js";
import {
  managedDocumentTargetsEqual,
  normalizeManagedDocumentTarget
} from "../docs-viewer-management-document-target.js";
import { localFolderPasteReplacement } from "./local-folder-links.js";
import { sourceBodyStart, sourceWithThumbnail } from "./source-buffer.js";
import { classifyDocsDocumentSubject } from "../../shared/docs-document-subject.js";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function normalizeSource(value) {
  return String(value == null ? "" : value).replace(/\r\n/g, "\n").replace(/\r/g, "\n");
}

function responseMatchesTarget(payload, target) {
  var returned = { doc_id: payload && payload.doc_id };
  if (payload && Object.prototype.hasOwnProperty.call(payload, "collection")) returned.collection = payload.collection;
  return managedDocumentTargetsEqual(returned, target);
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
  textarea.setAttribute("aria-label", "Complete Markdown source");

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
  return normalizeSource(state.textarea ? state.textarea.value : "") !== state.lastCleanSource;
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
    (state.sourceActionControlIds || []).forEach(function (controlId) {
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

function createSourceEditorContextAdapter(context, state) {
  function isCurrent() { return state.sourceEditorAdapter === adapter && state.loaded && Boolean(state.textarea); }
  var adapter = {
    isCurrent: isCurrent,
    captureSelection: function () {
      return Object.assign(sourceSelection(state), { revision: state.bufferRevision });
    },
    addSourceMedia: function (mediaKind, capture) {
      if (!isCurrent() || !capturedRangeIsCurrent(state, capture)) return Promise.resolve(null);
      return addSourceMedia(context, state, mediaKind, capture);
    },
    focus: function () {
      if (isCurrent()) state.textarea.focus();
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
    readDocumentSubject: async function (snapshot) {
      if (!isCurrent()) throw new Error("The Source editor was replaced.");
      var target = adapter.getDocumentTarget();
      var payload = await state.collectionProvider.readSourceContext(target, { source_text: snapshot.value });
      if (!isCurrent() || snapshot.revision !== state.bufferRevision
        || !responseMatchesTarget(payload, target)) throw new Error("The Source context changed.");
      return classifyDocsDocumentSubject(payload);
    },
    readCatalogueMediaTargets: function () {
      return state.collectionProvider.readCatalogueMediaTargets();
    },
    readDocumentLinkTargets: function () {
      var target = {  };
      return state.collectionProvider.readDocumentLinkTargets(target);
    },
    readCatalogueWork: function (workId) {
      return state.collectionProvider.readCatalogueWork(workId);
    },
    readCatalogueSeriesGalleries: function () {
      return state.collectionProvider.readCatalogueSeriesGalleries();
    },
    readCatalogueMediaConfig: function () {
      return state.collectionProvider.readCatalogueMediaConfig();
    },
    readCatalogueGalleryPresentation: function (galleryId) {
      return state.collectionProvider.readCatalogueGalleryPresentation(galleryId);
    },
    getSelection: function () {
      return sourceSelection(state);
    },
    replaceCapturedSelection: function (capture, value) {
      return isCurrent() && replaceCapturedRange(state, capture, value, "end");
    },
    insertSourceMedia: function (capture, payload) {
      if (!isCurrent() || !replaceCapturedRange(state, capture, payload.markdown, "end")) return false;
      if (payload.thumbnail) {
        var start = state.textarea.selectionStart;
        var end = state.textarea.selectionEnd;
        var previous = state.textarea.value;
        var next = sourceWithThumbnail(previous);
        var offset = next.length - previous.length;
        state.textarea.value = next;
        state.textarea.setSelectionRange(start + offset, end + offset);
        state.textarea.dispatchEvent(new Event("input", { bubbles: true }));
      }
      return true;
    },
    replaceCapturedRange: function (capture, value, selectionMode) {
      return isCurrent() && replaceCapturedRange(state, capture, value, selectionMode);
    },
    selectCapturedRange: function (capture) {
      var range = isCurrent() && capturedRangeIsCurrent(state, capture);
      if (!range) return false;
      state.textarea.setSelectionRange(range.start, range.end);
      state.textarea.focus();
      return true;
    },
    setStatus: function (message, isError) {
      setStatus(state, message, isError);
    }
  };
  return adapter;
}

function loadSource(context, state) {
  var adapter = state.sourceEditorAdapter;
  var provider = context.collectionProvider || {};
  if (typeof provider.readSource !== "function") {
    setStatus(state, "Markdown source editing is unavailable on this route.", true);
    return Promise.resolve(null);
  }

  setBusy(state, true);
  setStatus(state, "Loading source...", false);
  return provider.readSource(state.target)
    .then(function (payload) {
      if (state.sourceEditorAdapter !== adapter) return null;
      var responseTarget = {
        doc_id: cleanString(payload && payload.doc_id)
      };
      if (payload && Object.prototype.hasOwnProperty.call(payload, "collection")) {
        responseTarget.collection = cleanString(payload.collection);
      }
      if (!managedDocumentTargetsEqual(responseTarget, state.target)) {
        throw new Error("Source service returned a different managed document target.");
      }
      if (typeof payload.source_text !== "string") {
        throw new Error("Source service did not return the complete document.");
      }
      state.lastCleanSource = normalizeSource(payload.source_text);
      state.loaded = true;
      if (state.textarea) {
        state.textarea.value = state.lastCleanSource;
        state.textarea.setSelectionRange(0, 0);
        state.textarea.focus();
      }
      state.bufferRevision = 0;
      setStatus(state, "", false);
      projectDirty(state);
      return payload;
    })
    .catch(function (error) {
      if (state.sourceEditorAdapter !== adapter) return;
      setStatus(state, error && error.message ? error.message : "Failed to load source.", true);
    })
    .finally(function () {
      if (state.sourceEditorAdapter === adapter) setBusy(state, false);
    });
}

function saveSource(context, state) {
  var provider = context.collectionProvider || {};
  var services = context.sourceEditorServices || {};
  if (!state.loaded || state.busy || typeof provider.writeSource !== "function") return Promise.resolve(false);
  setBusy(state, true);
  state.saving = true;
  var stopBusy = typeof services.startBusy === "function" ? services.startBusy() : null;
  setStatus(state, "Saving doc...", false);
  var adapter = state.sourceEditorAdapter;
  var saved = false;
  var generated = false;
  function acceptSavedSource(payload) {
    if (!responseMatchesTarget(payload, state.target) || typeof payload.source_text !== "string") {
      throw new Error("Source service did not return the saved document.");
    }
    state.lastCleanSource = normalizeSource(payload.source_text);
    if (state.textarea) state.textarea.value = state.lastCleanSource;
    saved = true;
    projectDirty(state);
  }
  return provider.writeSource(state.target, { source_text: normalizeSource(state.textarea.value) })
    .then(async function (payload) {
      if (state.sourceEditorAdapter !== adapter) return true;
      if (payload.source_saved !== true) throw new Error("Source service did not confirm persistence.");
      acceptSavedSource(payload);
      if (payload.generation_complete !== true) throw new Error("Source saved, but document generation did not complete.");
      generated = true;
      if (typeof services.refreshSavedDocument !== "function") throw new Error("Fresh document display is unavailable.");
      await services.refreshSavedDocument(state.target);
      if (services.setStatus) {
        var projectionErrors = payload.projection_errors || [];
        services.setStatus(projectionErrors.length
          ? "Source saved. A retained list could not be updated: " + projectionErrors.join("; ")
          : "", projectionErrors.length > 0);
      }
      return true;
    })
    .catch(function (error) {
      if (state.sourceEditorAdapter === adapter && error.payload && error.payload.source_saved === true) {
        try { acceptSavedSource(error.payload); }
        catch (validationError) { error = validationError; }
      }
      var message = error && error.message ? error.message : "Save failed.";
      if (saved && generated) message = "Source saved and document rebuilt, but display failed: " + message;
      setStatus(state, message, true);
      if (services.setStatus) services.setStatus(message, true);
      return false;
    })
    .finally(function () {
      if (stopBusy) stopBusy();
      if (state.sourceEditorAdapter === adapter) {
        state.saving = false;
        setBusy(state, false);
      }
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
  state.lastCleanSource = normalizeSource(state.textarea.value);
  projectDirty(state);
  return true;
}

function addSourceMedia(context, state, mediaKind, capture) {
  if (state.busy || !state.loaded) return Promise.resolve(null);
  var provider = context.collectionProvider || {};
  setBusy(state, true);
  setStatus(state, mediaKind === "file" ? "Loading files..." : "Loading images...", false);
  return import("./source-editor-media.js")
    .then(function (module) {
      return module.publishAndInsertSourceMedia({
        adapter: state.sourceEditorAdapter,
        capture: capture,
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
    projectDirty(state);
  };
  state.onPaste = function (event) {
    var capability = typeof services.localFolderLinksCapability === "function" ? services.localFolderLinksCapability() : null;
    if (!state.loaded || state.busy || !capability || capability.authoring !== true) return;
    var selection = sourceSelection(state);
    if (selection.start < sourceBodyStart(state.textarea.value)) return;
    var replacement = localFolderPasteReplacement({
      text: event.clipboardData ? event.clipboardData.getData("text/plain") : "",
      basePath: capability.base_path,
      docsBasePath: capability.docs_base_path,
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
  state.onBeforeUnload = function (event) {
    if (!dirtyNow(state)) return;
    event.preventDefault();
    event.returnValue = "";
  };

  if (state.textarea) {
    state.textarea.addEventListener("input", state.onInput);
    state.textarea.addEventListener("paste", state.onPaste);
  }
  if (state.root) state.root.addEventListener("click", state.onClick);
  if (root && state.onToolbarSave) root.addEventListener("docs-viewer-source-editor-save", state.onToolbarSave);
  window.addEventListener("beforeunload", state.onBeforeUnload);
  projectDirty(state);
}

function unbindEvents(context, state) {
  var root = context && context.root ? context.root : document;
  if (state.textarea && state.onInput) state.textarea.removeEventListener("input", state.onInput);
  if (state.textarea && state.onPaste) state.textarea.removeEventListener("paste", state.onPaste);
  if (state.root && state.onClick) state.root.removeEventListener("click", state.onClick);
  if (root && state.onToolbarSave) root.removeEventListener("docs-viewer-source-editor-save", state.onToolbarSave);
  if (state.onBeforeUnload) window.removeEventListener("beforeunload", state.onBeforeUnload);
  state.projectMainViewControlState = null;
  state.sourceActionControlIds = [];
}

function restoreRenderedContent(context, state) {
  if (!context.mount || !state.root) return;
  state.root.remove();
  context.mount.scrollTop = state.renderedScrollTop;
  state.root = null;
  state.textarea = null;
  state.loaded = false;
  state.sourceEditorAdapter = null;
}

export function createDocsViewerSourceEditorMode() {
  var state = {
    busy: false,
    saving: false,
    bufferRevision: 0,
    dirtyValue: false,
    lastCleanSource: "",
    loaded: false,
    collectionProvider: null,
    root: null,
    renderedScrollTop: 0,
    sourceActionControlIds: [],
    status: null,
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
      state.lastCleanSource = "";
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
      state.sourceEditorAdapter = createSourceEditorContextAdapter(context, state);
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
      unbindEvents(context, state);
      restoreRenderedContent(context, state);
    },
    dispose: function (context) {
      var services = context.sourceEditorServices || {};
      if (typeof services.clearActiveSourceEditorContextAdapter === "function") {
        services.clearActiveSourceEditorContextAdapter(state.sourceEditorAdapter);
      }
      unbindEvents(context, state);
      restoreRenderedContent(context, state);
    }
  };
}
