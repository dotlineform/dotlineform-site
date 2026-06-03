import {
  openDocsViewerManagementModal
} from "../../docs-viewer-management-modal-shell.js";

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

function lineCount(body) {
  return normalizeBody(body).split("\n").length;
}

function renderLineNumbers(gutter, body) {
  if (!gutter) return;
  var count = Math.max(1, lineCount(body));
  var lines = [];
  for (var index = 1; index <= count; index += 1) {
    lines.push(String(index));
  }
  gutter.textContent = lines.join("\n");
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

function selectedDocLabel(context) {
  var doc = context.selectedDoc || {};
  return cleanString(doc.title) || cleanString(doc.doc_id) || "Selected document";
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

  var header = document.createElement("div");
  header.className = "docsViewerSourceEditor__header";

  var headingGroup = document.createElement("div");
  headingGroup.className = "docsViewerSourceEditor__headingGroup";

  var heading = document.createElement("h2");
  heading.className = "docsViewerSourceEditor__title";
  heading.textContent = "Markdown source";

  var meta = document.createElement("p");
  meta.className = "docsViewerSourceEditor__meta muted small";
  meta.textContent = selectedDocLabel(context);

  headingGroup.append(heading, meta);

  var actions = document.createElement("div");
  actions.className = "docsViewerSourceEditor__actions";

  var dirty = document.createElement("span");
  dirty.className = "docsViewerSourceEditor__dirty muted small";
  dirty.textContent = "Unsaved changes";
  dirty.hidden = true;

  var back = document.createElement("button");
  back.className = "docsViewer__actionButton";
  back.type = "button";
  back.textContent = "Back";
  back.dataset.sourceEditorAction = "back";

  var rebuild = document.createElement("button");
  rebuild.className = "docsViewer__actionButton";
  rebuild.type = "button";
  rebuild.textContent = "Rebuild doc";
  rebuild.dataset.sourceEditorAction = "rebuild";

  actions.append(dirty, back, rebuild);
  header.append(headingGroup, actions);

  var status = document.createElement("p");
  status.className = "docsViewerSourceEditor__status muted small";
  status.hidden = true;

  var editor = document.createElement("div");
  editor.className = "docsViewerSourceEditor__editor";

  var gutter = document.createElement("pre");
  gutter.className = "docsViewerSourceEditor__gutter";
  gutter.setAttribute("aria-hidden", "true");
  gutter.tabIndex = -1;

  var textarea = document.createElement("textarea");
  textarea.className = "docsViewerSourceEditor__textarea";
  textarea.spellcheck = false;
  textarea.wrap = "off";
  textarea.setAttribute("aria-label", "Markdown source body");

  editor.append(gutter, textarea);
  root.append(header, status, editor);
  mount.appendChild(root);

  state.root = root;
  state.status = status;
  state.dirty = dirty;
  state.back = back;
  state.rebuild = rebuild;
  state.gutter = gutter;
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
  if (state.rebuild) state.rebuild.disabled = state.busy || !state.loaded;
  if (state.back) state.back.disabled = state.busy;
}

function setBusy(state, busy) {
  state.busy = Boolean(busy);
  projectDirty(state);
}

function loadSource(context, state) {
  var services = context.sourceEditorServices || {};
  var doc = context.selectedDoc || null;
  if (!doc || !doc.doc_id) {
    setStatus(state, "Select a document before opening Markdown source.", true);
    return Promise.resolve(null);
  }
  if (typeof services.readSource !== "function") {
    setStatus(state, "Markdown source editing is unavailable on this route.", true);
    return Promise.resolve(null);
  }

  setBusy(state, true);
  setStatus(state, "Loading source...", false);
  return services.readSource(doc.doc_id)
    .then(function (payload) {
      state.docId = cleanString(payload.doc_id || doc.doc_id);
      state.revision = cleanString(payload.source_revision);
      state.lastCleanBody = normalizeBody(payload.source_body);
      state.loaded = true;
      if (state.textarea) {
        state.textarea.value = state.lastCleanBody;
        state.textarea.focus();
      }
      renderLineNumbers(state.gutter, state.lastCleanBody);
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
  var services = context.sourceEditorServices || {};
  if (!state.loaded || typeof services.rebuildSource !== "function") return Promise.resolve(false);

  setBusy(state, true);
  setStatus(state, "Rebuilding doc...", false);
  var nextBody = normalizeBody(state.textarea ? state.textarea.value : "");
  return services.rebuildSource({
    doc_id: state.docId,
    source_revision: state.revision,
    source_body: nextBody
  })
    .then(function (payload) {
      state.revision = cleanString(payload.source_revision);
      state.lastCleanBody = nextBody;
      projectDirty(state);
      setStatus(state, diagnosticsText(payload) || "Doc rebuilt.", false);
      if (typeof services.reloadRenderedDoc === "function") {
        return services.reloadRenderedDoc(state.docId).then(function () {
          context.mainView.requestView("rendered-document", { force: true, warn: false });
          return true;
        });
      }
      context.mainView.requestView("rendered-document", { force: true, warn: false });
      return true;
    })
    .catch(function (error) {
      setStatus(state, error && error.message ? error.message : "Rebuild failed.", true);
      return false;
    })
    .finally(function () {
      setBusy(state, false);
    });
}

function returnToRendered(context, state) {
  var services = context.sourceEditorServices || {};
  if (typeof services.reloadRenderedDoc !== "function") {
    context.mainView.requestView("rendered-document", { force: true, warn: false });
    return Promise.resolve(true);
  }

  setBusy(state, true);
  return services.reloadRenderedDoc(state.docId)
    .then(function () {
      context.mainView.requestView("rendered-document", { force: true, warn: false });
      return true;
    })
    .catch(function (error) {
      setStatus(state, error && error.message ? error.message : "Failed to return to rendered view.", true);
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

function bindEvents(context, state) {
  state.onInput = function () {
    renderLineNumbers(state.gutter, state.textarea ? state.textarea.value : "");
    projectDirty(state);
  };
  state.onScroll = function () {
    if (state.gutter && state.textarea) state.gutter.scrollTop = state.textarea.scrollTop;
  };
  state.onClick = function (event) {
    var action = event.target.closest("[data-source-editor-action]");
    if (!action || action.disabled) return;
    if (action.dataset.sourceEditorAction === "rebuild") {
      rebuildSource(context, state);
    } else if (action.dataset.sourceEditorAction === "back") {
      leaveSource(context, state);
    }
  };
  state.onBeforeUnload = function (event) {
    if (!dirtyNow(state)) return;
    event.preventDefault();
    event.returnValue = "";
  };

  if (state.textarea) {
    state.textarea.addEventListener("input", state.onInput);
    state.textarea.addEventListener("scroll", state.onScroll);
  }
  if (state.root) state.root.addEventListener("click", state.onClick);
  window.addEventListener("beforeunload", state.onBeforeUnload);
}

function unbindEvents(state) {
  if (state.textarea && state.onInput) state.textarea.removeEventListener("input", state.onInput);
  if (state.textarea && state.onScroll) state.textarea.removeEventListener("scroll", state.onScroll);
  if (state.root && state.onClick) state.root.removeEventListener("click", state.onClick);
  if (state.onBeforeUnload) window.removeEventListener("beforeunload", state.onBeforeUnload);
}

export function createDocsViewerSourceEditorView() {
  var state = {
    busy: false,
    dirtyValue: false,
    docId: "",
    gutter: null,
    lastCleanBody: "",
    loaded: false,
    rebuild: null,
    revision: "",
    root: null,
    status: null,
    textarea: null
  };

  return {
    mount: function (context) {
      context.mainView.projectToolbar({
        toolbarHidden: false,
        metaHidden: true,
        contentHidden: false,
        resultsHidden: true,
        moreHidden: true,
        clearMore: true
      });
      renderEditorShell(context, state);
      bindEvents(context, state);
      return loadSource(context, state);
    },
    beforeLeave: function (context) {
      if (!dirtyNow(state) || cleanString(context.requestedViewId) === "markdown-source") return true;
      leaveSource(context, state);
      return false;
    },
    update: function (context) {
      if (state.docId === cleanString(context.selectedDoc && context.selectedDoc.doc_id)) return Promise.resolve(null);
      return loadSource(context, state);
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
