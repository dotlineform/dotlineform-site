import {
  fetchManagementJson
} from "./docs-viewer-management-client.js";

export var REVIEW_SESSIONS_PATH = "/docs/review-sessions";
export var REVIEW_SESSION_BUILD_PATH = "/docs/review-sessions/build";
export var REVIEW_SESSION_DELETE_PATH = "/docs/review-sessions/delete";
export var REVIEW_SESSION_INDEX_TREE_PATH = "/docs/review-sessions/index-tree";
export var REVIEW_SESSION_PAYLOAD_PATH = "/docs/review-sessions/payload";

function cleanString(value) {
  return String(value || "").trim();
}

function queryPath(path, params) {
  var query = [];
  Object.keys(params || {}).forEach(function (key) {
    var value = cleanString(params[key]);
    if (value) query.push(encodeURIComponent(key) + "=" + encodeURIComponent(value));
  });
  return path + (query.length ? "?" + query.join("&") : "");
}

export function listReviewSessions(options) {
  return fetchManagementJson(REVIEW_SESSIONS_PATH, "GET", undefined, options);
}

export function buildReviewSession(sessionId, options) {
  return fetchManagementJson(REVIEW_SESSION_BUILD_PATH, "POST", {
    session_id: cleanString(sessionId)
  }, options);
}

export function deleteReviewSession(sessionId, options) {
  return fetchManagementJson(REVIEW_SESSION_DELETE_PATH, "POST", {
    session_id: cleanString(sessionId)
  }, options);
}

export function readReviewSessionIndexTree(sessionId, options) {
  return fetchManagementJson(
    queryPath(REVIEW_SESSION_INDEX_TREE_PATH, { session_id: sessionId }),
    "GET",
    undefined,
    options
  );
}

export function readReviewSessionPayload(sessionId, docId, options) {
  return fetchManagementJson(
    queryPath(REVIEW_SESSION_PAYLOAD_PATH, {
      session_id: sessionId,
      doc_id: docId
    }),
    "GET",
    undefined,
    options
  );
}
