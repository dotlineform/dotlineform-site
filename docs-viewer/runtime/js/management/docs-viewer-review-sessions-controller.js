import {
  buildReviewSession,
  deleteReviewSession,
  listReviewSessions
} from "./docs-viewer-review-sessions-client.js";
import {
  createDocsViewerReviewSessionsModal
} from "./docs-viewer-review-sessions-modal.js";

function cleanString(value) {
  return String(value || "").trim();
}

export function createDocsViewerReviewSessionsController(options) {
  var settings = options || {};
  var callbacks = settings.callbacks || {};
  var clientOptions = settings.clientOptions || function () { return {}; };
  var modal = createDocsViewerReviewSessionsModal({
    document: settings.document,
    mount: settings.mount,
    callbacks: {
      onBuild: function (session) {
        return buildSession(session);
      },
      onClose: function () {
        close();
      },
      onDelete: function (session) {
        return deleteSession(session);
      },
      onOpen: function (session) {
        if (callbacks.onOpenSession) callbacks.onOpenSession(session);
      },
      onSelect: function (sessionId) {
        if (modal) modal.selectSession(sessionId);
      }
    }
  });
  var sessions = [];

  function setStatus(message, isError) {
    if (modal) modal.setStatus(message, isError);
  }

  function refresh(selectedSessionId) {
    setStatus("Loading review sessions...", false);
    return listReviewSessions(clientOptions()).then(function (payload) {
      sessions = Array.isArray(payload.sessions) ? payload.sessions : [];
      if (modal) {
        modal.setSessions(sessions, selectedSessionId || cleanString(sessions[0] && sessions[0].session_id));
        modal.setStatus(sessions.length ? sessions.length + " review session" + (sessions.length === 1 ? "" : "s") : "No review sessions found.", false);
      }
      return sessions;
    }).catch(function (error) {
      setStatus(error && error.message ? error.message : "Review sessions unavailable.", true);
      throw error;
    });
  }

  function open() {
    if (!modal) return Promise.resolve([]);
    modal.open();
    return refresh("");
  }

  function close() {
    if (modal) modal.close();
  }

  function buildSession(session) {
    var sessionId = cleanString(session && session.session_id);
    if (!sessionId) return Promise.resolve(null);
    setStatus("Building review session...", false);
    return buildReviewSession(sessionId, clientOptions()).then(function (payload) {
      setStatus(cleanString(payload.summary_text) || "Review session build requested.", false);
      return refresh(sessionId).then(function () {
        return payload;
      });
    }).catch(function (error) {
      setStatus(error && error.message ? error.message : "Review session build failed.", true);
      throw error;
    });
  }

  function deleteSession(session) {
    var sessionId = cleanString(session && session.session_id);
    if (!sessionId) return Promise.resolve(null);
    setStatus("Deleting review session...", false);
    return deleteReviewSession(sessionId, clientOptions()).then(function (payload) {
      setStatus(cleanString(payload.summary_text) || "Review session deleted.", false);
      return refresh("").then(function () {
        return payload;
      });
    }).catch(function (error) {
      setStatus(error && error.message ? error.message : "Review session delete failed.", true);
      throw error;
    });
  }

  return {
    buildSession: buildSession,
    close: close,
    deleteSession: deleteSession,
    open: open,
    refresh: refresh
  };
}
