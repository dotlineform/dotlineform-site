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
  var activeDeleteWorkflow = null;
  var deleteWorkflowRequest = 0;

  function clearDeleteWorkflow() {
    deleteWorkflowRequest += 1;
    if (activeDeleteWorkflow && typeof activeDeleteWorkflow.destroy === "function") {
      activeDeleteWorkflow.destroy();
    }
    activeDeleteWorkflow = null;
  }

  function notify(event) {
    if (
      event
      && (
        event.type === "unmount"
        || (event.type === "state" && cleanString(event.state) !== "detail")
      )
    ) {
      clearDeleteWorkflow();
    }
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

  function renderDetailToolbar(context) {
    var settings = context || {};
    var host = settings.host;
    var target = settings.target;
    if (!host || !target || typeof settings.commitDeletedDocument !== "function") return;

    clearDeleteWorkflow();
    var request = deleteWorkflowRequest;
    var button = host.ownerDocument.createElement("button");
    button.className = "docsViewerReport__button";
    button.type = "button";
    button.disabled = true;
    button.dataset.docsSubscopeDelete = "true";
    button.textContent = "Delete";
    button.title = "Checking Delete availability.";
    host.appendChild(button);

    import("./docs-viewer-management-subscope-delete-workflow.js")
      .then(function (module) {
        if (request !== deleteWorkflowRequest || !button.isConnected) return;
        activeDeleteWorkflow = module.createDocsViewerManagementSubscopeDeleteWorkflow({
          button: button,
          clientOptions: options.clientOptions || {},
          commitDeletedDocument: settings.commitDeletedDocument,
          root: options.root,
          setStatus: options.setStatus,
          target: target,
          title: cleanString(settings.document && settings.document.title) || cleanString(target.doc_id)
        });
        return activeDeleteWorkflow.initialize();
      })
      .catch(function (error) {
        if (request !== deleteWorkflowRequest || !button.isConnected) return;
        button.disabled = true;
        button.title = "Sub-scope detail Delete is unavailable.";
        if (typeof options.setStatus === "function") {
          options.setStatus(
            error && error.message ? error.message : "Sub-scope detail Delete is unavailable.",
            true
          );
        }
      });
  }

  return {
    notify: notify,
    renderDetailToolbar: renderDetailToolbar,
    renderRow: renderRow
  };
}
