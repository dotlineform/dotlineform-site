function cleanString(value) {
  return String(value || "").trim();
}

function clearNode(node) {
  if (node) node.replaceChildren();
}

function sessionTitle(session) {
  var manifest = session && session.manifest && typeof session.manifest === "object" ? session.manifest : {};
  return cleanString(manifest.title) || cleanString(session && session.session_id) || "review session";
}

function sessionMeta(session) {
  var manifest = session && session.manifest && typeof session.manifest === "object" ? session.manifest : {};
  var parts = [
    cleanString(manifest.source_scope),
    cleanString(manifest.profile_id),
    cleanString(manifest.content_format),
    session && session.built ? "built" : "not built"
  ].filter(Boolean);
  return parts.join(" - ");
}

function appendSessionRow(state, session) {
  var documentRef = state.document;
  var row = documentRef.createElement("button");
  row.type = "button";
  row.className = "docsViewer__reviewSessionRow";
  row.dataset.sessionId = cleanString(session && session.session_id);
  if (row.dataset.sessionId === state.selectedSessionId) {
    row.setAttribute("aria-current", "true");
  }

  var title = documentRef.createElement("span");
  title.className = "docsViewer__reviewSessionTitle";
  title.textContent = sessionTitle(session);

  var meta = documentRef.createElement("span");
  meta.className = "docsViewer__reviewSessionMeta muted small";
  meta.textContent = sessionMeta(session);

  row.appendChild(title);
  row.appendChild(meta);
  row.addEventListener("click", function () {
    if (state.callbacks.onSelect) state.callbacks.onSelect(row.dataset.sessionId);
  });
  state.listNode.appendChild(row);
}

function selectedSession(state) {
  return state.sessions.find(function (session) {
    return cleanString(session && session.session_id) === state.selectedSessionId;
  }) || null;
}

function updateActions(state) {
  var session = selectedSession(state);
  var hasSession = Boolean(session);
  state.openButton.disabled = !hasSession || !session.built;
  state.buildButton.disabled = !hasSession;
  state.deleteButton.disabled = !hasSession;
}

function renderList(state) {
  clearNode(state.listNode);
  if (!state.sessions.length) {
    var empty = state.document.createElement("p");
    empty.className = "docsViewer__panelStatus muted small";
    empty.textContent = "No review sessions found.";
    state.listNode.appendChild(empty);
    return;
  }
  state.sessions.forEach(function (session) {
    appendSessionRow(state, session);
  });
}

export function createDocsViewerReviewSessionsModal(options) {
  var settings = options || {};
  var documentRef = settings.document || document;
  var mount = settings.mount;
  var callbacks = settings.callbacks || {};
  if (!mount) return null;

  var state = {
    callbacks: callbacks,
    document: documentRef,
    sessions: [],
    selectedSessionId: ""
  };

  var modal = documentRef.createElement("div");
  modal.className = "docsViewer__modal";
  modal.hidden = true;
  modal.innerHTML = [
    '<div class="docsViewer__modalBackdrop" data-review-sessions-close="true"></div>',
    '<div class="docsViewer__modalCard docsViewer__modalCard--document" role="dialog" aria-modal="true" aria-labelledby="docsViewerReviewSessionsHeading">',
    '  <div class="docsViewer__modalHeader">',
    '    <div class="docsViewer__modalHeaderCopy">',
    '      <h2 class="docsViewer__modalTitle" id="docsViewerReviewSessionsHeading">Review sessions</h2>',
    '      <p class="docsViewer__modalMeta muted small" data-review-sessions-status></p>',
    '    </div>',
    '  </div>',
    '  <div class="docsViewer__modalForm">',
    '    <div class="docsViewer__reviewSessionsList" data-review-sessions-list></div>',
    '    <div class="docsViewer__modalActions">',
    '      <button class="docsViewer__actionButton docsViewer__actionButton--defaultWidth" type="button" data-review-sessions-open>Open</button>',
    '      <button class="docsViewer__actionButton docsViewer__actionButton--defaultWidth" type="button" data-review-sessions-build>Build</button>',
    '      <button class="docsViewer__actionButton docsViewer__actionButton--defaultWidth" type="button" data-review-sessions-delete>Delete</button>',
    '      <button class="docsViewer__actionButton docsViewer__actionButton--defaultWidth" type="button" data-review-sessions-close>Cancel</button>',
    '    </div>',
    '  </div>',
    '</div>'
  ].join("");
  mount.replaceChildren(modal);

  state.modal = modal;
  state.listNode = modal.querySelector("[data-review-sessions-list]");
  state.statusNode = modal.querySelector("[data-review-sessions-status]");
  state.openButton = modal.querySelector("[data-review-sessions-open]");
  state.buildButton = modal.querySelector("[data-review-sessions-build]");
  state.deleteButton = modal.querySelector("[data-review-sessions-delete]");

  modal.querySelectorAll("[data-review-sessions-close]").forEach(function (node) {
    node.addEventListener("click", function () {
      if (callbacks.onClose) callbacks.onClose();
    });
  });
  state.openButton.addEventListener("click", function () {
    var session = selectedSession(state);
    if (session && callbacks.onOpen) callbacks.onOpen(session);
  });
  state.buildButton.addEventListener("click", function () {
    var session = selectedSession(state);
    if (session && callbacks.onBuild) callbacks.onBuild(session);
  });
  state.deleteButton.addEventListener("click", function () {
    var session = selectedSession(state);
    if (session && callbacks.onDelete) callbacks.onDelete(session);
  });

  function setSessions(sessions, selectedSessionId) {
    state.sessions = Array.isArray(sessions) ? sessions : [];
    state.selectedSessionId = cleanString(selectedSessionId);
    renderList(state);
    updateActions(state);
  }

  function selectSession(sessionId) {
    state.selectedSessionId = cleanString(sessionId);
    renderList(state);
    updateActions(state);
  }

  function setStatus(message, isError) {
    state.statusNode.textContent = cleanString(message);
    state.statusNode.dataset.error = isError ? "true" : "false";
  }

  function open() {
    modal.hidden = false;
  }

  function close() {
    modal.hidden = true;
  }

  setSessions([], "");
  return {
    close: close,
    open: open,
    selectSession: selectSession,
    setSessions: setSessions,
    setStatus: setStatus
  };
}
