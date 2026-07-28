function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function statusRecord(statuses, value) {
  var statusValue = cleanString(value);
  if (!statusValue || !(statuses instanceof Map)) return null;
  return statuses.get(statusValue) || null;
}

function appendIcon(host, className, text) {
  var iconText = cleanString(text);
  if (!host || !iconText) return false;
  var icon = host.ownerDocument.createElement("span");
  icon.className = className;
  icon.setAttribute("aria-hidden", "true");
  icon.textContent = iconText;
  host.appendChild(icon);
  return true;
}

/**
 * Creates the manage-only contribution for the shared sub-scope report.
 *
 * The shared report owns collection identity and navigation. This contribution
 * only projects compact-inventory row state and receives explicit lifecycle
 * events; it does not infer targets or load workflows.
 *
 * @param {Object} options
 * @returns {Object}
 */
export function createDocsViewerManagementSubscopeContribution(options = {}) {
  var statuses = options.uiStatusByValue instanceof Map
    ? options.uiStatusByValue
    : new Map();
  var nonViewableEmoji = cleanString(options.nonViewableEmoji) || "\uD83D\uDEAB";
  var onLifecycleEvent = typeof options.onLifecycleEvent === "function"
    ? options.onLifecycleEvent
    : null;

  function notify(event) {
    if (onLifecycleEvent) onLifecycleEvent(event);
  }

  function renderRow(context) {
    var settings = context || {};
    var doc = settings.document || {};
    var host = settings.titlePrefixHost;
    var accessibleLabels = [];
    var uiStatus = statusRecord(statuses, doc.ui_status);
    if (uiStatus && appendIcon(host, "docsViewer__navStatus", uiStatus.emoji)) {
      accessibleLabels.push(cleanString(uiStatus.label) || cleanString(doc.ui_status));
    }
    if (doc.viewable === false && appendIcon(host, "docsViewer__draftPrefix", nonViewableEmoji)) {
      accessibleLabels.push("non-viewable");
    }
    return { accessibleLabels: accessibleLabels };
  }

  return {
    notify: notify,
    renderRow: renderRow
  };
}
