function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function positiveInteger(value) {
  var number = Number(value);
  return Number.isInteger(number) && number > 0 ? number : 0;
}

function defaultWarning(message, error) {
  if (typeof console !== "undefined" && typeof console.warn === "function") {
    console.warn(message, error);
  }
}

function sameDocumentTarget(left, right) {
  var first = left || {};
  var second = right || {};
  return cleanString(first.scope) === cleanString(second.scope)
    && cleanString(first.docId) === cleanString(second.docId);
}

function sameReportTarget(left, right) {
  var first = left || {};
  var second = right || {};
  return cleanString(first.reportId) === cleanString(second.reportId)
    && cleanString(first.scope) === cleanString(second.scope)
    && cleanString(first.preset) === cleanString(second.preset)
    && cleanString(first.subScope) === cleanString(second.subScope);
}

function immutableTargetContext(state) {
  return Object.freeze({
    documentMountGeneration: state.documentMountGeneration,
    documentTarget: Object.freeze(Object.assign({}, state.documentTarget)),
    kind: "report",
    reportTarget: Object.freeze(Object.assign({}, state.reportTarget))
  });
}

function explicitPresentationResult(mountResult) {
  if (!mountResult || (typeof mountResult !== "object" && typeof mountResult !== "function")) {
    return { explicit: false, value: null };
  }
  return {
    explicit: Object.prototype.hasOwnProperty.call(mountResult, "expandedPresentation"),
    value: mountResult.expandedPresentation
  };
}

function normalizedColumns(rawColumns) {
  if (!Array.isArray(rawColumns) || !rawColumns.length) {
    throw new Error("Semantic-table presentation requires a non-empty column model.");
  }
  var ids = new Set();
  var columns = rawColumns.map(function (rawColumn) {
    var id = cleanString(rawColumn && rawColumn.id);
    var label = cleanString(rawColumn && rawColumn.label);
    if (!id || !label || ids.has(id)) {
      throw new Error("Semantic-table presentation columns require unique ids and labels.");
    }
    ids.add(id);
    return Object.freeze({ id: id, label: label });
  });
  return Object.freeze(columns);
}

function normalizePresentation(rawPresentation, reportRoot) {
  if (!rawPresentation || typeof rawPresentation !== "object") {
    throw new Error("Expanded report presentation must be an object.");
  }
  var kind = cleanString(rawPresentation.kind);
  var label = cleanString(rawPresentation.label);
  if (kind !== "flow" && kind !== "semantic-table") {
    throw new Error("Expanded report presentation kind must be flow or semantic-table.");
  }
  if (!label) throw new Error("Expanded report presentation requires a label.");

  if (kind === "flow") {
    ["table", "columns", "subscribe"].forEach(function (key) {
      if (Object.prototype.hasOwnProperty.call(rawPresentation, key)) {
        throw new Error("Flow presentation must omit semantic-table fields.");
      }
    });
    return Object.freeze({ kind: kind, label: label });
  }

  var table = rawPresentation.table;
  if (
    !table
    || cleanString(table.tagName).toLowerCase() !== "table"
    || typeof reportRoot.contains !== "function"
    || !reportRoot.contains(table)
  ) {
    throw new Error("Semantic-table presentation requires the exact report table.");
  }
  if (typeof rawPresentation.subscribe !== "function") {
    throw new Error("Semantic-table presentation requires a refresh subscription.");
  }
  return Object.freeze({
    columns: normalizedColumns(rawPresentation.columns),
    kind: kind,
    label: label,
    subscribe: function (listener) { return rawPresentation.subscribe(listener); },
    table: table
  });
}

function createOpenControl(documentRef, label) {
  var row = documentRef.createElement("div");
  row.className = "docsViewerReport__detailControlRow";
  row.setAttribute("data-docs-content-detail-control", "report");

  var button = documentRef.createElement("button");
  var controlLabel = "Open " + label + " in expanded view";
  button.className = "docsViewerReport__detailOpen";
  button.type = "button";
  button.setAttribute("aria-label", controlLabel);
  button.title = controlLabel;
  button.innerHTML = [
    '<svg class="docsViewerReport__detailIcon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">',
    '  <path d="M14 5h5v5M19 5l-8 8M19 13v6H5V5h6"></path>',
    "</svg>"
  ].join("");
  row.appendChild(button);
  return { button: button, row: row };
}

/** Create one report-presentation adapter with no management or service authority. */
export function createDocsViewerReportPresentationAdapter(options) {
  var settings = options || {};
  var presentationExtension = settings.presentationExtension || null;
  var warn = typeof settings.warn === "function" ? settings.warn : defaultWarning;
  var stateByRoot = new WeakMap();

  function resolveState(root, targetContext) {
    var target = targetContext || {};
    var state = root ? stateByRoot.get(root) : null;
    if (
      !state
      || cleanString(target.kind) !== "report"
      || positiveInteger(target.documentMountGeneration) !== state.documentMountGeneration
      || !sameDocumentTarget(target.documentTarget, state.documentTarget)
      || !sameReportTarget(target.reportTarget, state.reportTarget)
      || !root.contains(state.reportRoot)
    ) {
      return null;
    }
    return state;
  }

  function releasePresentation(state, releaseContext) {
    var presentation = state && state.presentation;
    if (!presentation) return;
    presentation.release(releaseContext || {});
  }

  function releaseState(root, state) {
    if (!state) return { released: 0 };
    releasePresentation(state, {
      requestReason: "document-navigation",
      restoreDocumentContext: false
    });
    state.button.removeEventListener("click", state.handleClick);
    state.controlRow.remove();
    stateByRoot.delete(root);
    return { released: 1 };
  }

  function releaseDocument(releaseContext) {
    var context = releaseContext || {};
    var root = context.content;
    if (!root || typeof root !== "object") return { released: 0 };
    return releaseState(root, stateByRoot.get(root));
  }

  function registerMountedReport(registrationContext) {
    var context = registrationContext || {};
    var root = context.content;
    var reportRoot = context.reportRoot;
    if (
      !root
      || !reportRoot
      || typeof root.contains !== "function"
      || !root.contains(reportRoot)
    ) {
      return { registered: false, reason: "stale" };
    }

    var result = explicitPresentationResult(context.mountResult);
    releaseState(root, stateByRoot.get(root));
    if (!result.explicit) return { registered: false, reason: "absent" };

    var presentation;
    try {
      presentation = normalizePresentation(result.value, reportRoot);
    } catch (error) {
      warn("docs_viewer: expanded report presentation unavailable", error);
      return { registered: false, reason: "invalid" };
    }

    var documentRef = context.document || root.ownerDocument;
    var doc = context.doc || {};
    var reportMeta = context.reportMeta || {};
    var state = {
      button: null,
      content: root,
      controlRow: null,
      documentMountGeneration: positiveInteger(context.documentMountGeneration),
      documentTarget: {
        docId: cleanString(doc.doc_id),
        scope: cleanString(context.viewerScope)
      },
      handleClick: null,
      presentation: null,
      presentationHandle: presentation,
      reportRoot: reportRoot,
      reportTarget: {
        preset: cleanString(reportMeta.preset),
        reportId: cleanString(reportMeta.reportId),
        scope: cleanString(reportMeta.scope),
        subScope: cleanString(reportMeta.subScope)
      },
      requestContentDetail: typeof context.requestContentDetail === "function"
        ? context.requestContentDetail
        : function () { return false; }
    };
    if (
      !documentRef
      || !state.documentMountGeneration
      || !state.documentTarget.scope
      || !state.documentTarget.docId
      || !state.reportTarget.reportId
    ) {
      warn(
        "docs_viewer: expanded report presentation unavailable",
        new Error("Expanded report presentation requires exact document and report identity.")
      );
      return { registered: false, reason: "invalid" };
    }

    var control = createOpenControl(documentRef, presentation.label);
    state.button = control.button;
    state.controlRow = control.row;
    state.handleClick = function () {
      if (!resolveState(root, immutableTargetContext(state))) return;
      state.requestContentDetail(immutableTargetContext(state));
    };
    state.button.addEventListener("click", state.handleClick);
    reportRoot.before(state.controlRow);
    stateByRoot.set(root, state);
    return { registered: true, targetContext: immutableTargetContext(state) };
  }

  function mountPresentation(presentationContext) {
    var context = presentationContext || {};
    var root = context.content;
    var state = resolveState(root, context.targetContext);
    if (!state) throw new Error("Expanded report target is stale or unavailable.");
    if (state.presentation) throw new Error("Expanded report target is already active.");

    var documentRef = context.document || root.ownerDocument;
    var placeholder = documentRef.createComment("docs-viewer-report-restoration");
    state.reportRoot.before(placeholder);

    var section = documentRef.createElement("section");
    section.className = "docsViewer__contentDetail docsViewer__contentDetail--report";
    section.setAttribute("data-docs-content-detail-view", "report");

    var viewport = documentRef.createElement("div");
    viewport.className = "docsViewerReport__expandedViewport";
    viewport.tabIndex = 0;
    viewport.setAttribute("role", "region");
    viewport.setAttribute("aria-label", state.presentationHandle.label);
    viewport.appendChild(state.reportRoot);
    section.appendChild(viewport);

    var extension = null;
    try {
      extension = presentationExtension && typeof presentationExtension.mount === "function"
        ? presentationExtension.mount({
            columns: state.presentationHandle.columns || null,
            document: documentRef,
            kind: state.presentationHandle.kind,
            label: state.presentationHandle.label,
            root: section,
            reportRoot: state.reportRoot,
            subscribe: state.presentationHandle.subscribe || null,
            table: state.presentationHandle.table || null,
            targetContext: context.targetContext,
            viewport: viewport
          })
        : null;
    } catch (error) {
      placeholder.before(state.reportRoot);
      placeholder.remove();
      section.remove();
      throw error;
    }

    var released = false;
    var presentation = {
      activate: function (activationContext) {
        if (extension && typeof extension.activate === "function") {
          extension.activate(activationContext || {});
        }
      },
      focusTarget: viewport,
      invocationControl: state.button,
      label: state.presentationHandle.label,
      root: section,
      release: function (releaseContext) {
        if (released) return;
        released = true;
        var releaseSettings = releaseContext || {};
        var restore = Boolean(releaseSettings.restoreDocumentContext)
          || cleanString(releaseSettings.requestReason) === "view-failure";
        try {
          if (extension && typeof extension.release === "function") extension.release();
        } finally {
          if (restore && placeholder.isConnected) placeholder.before(state.reportRoot);
          placeholder.remove();
          section.remove();
          if (state.presentation === presentation) state.presentation = null;
        }
      }
    };
    state.presentation = presentation;
    return presentation;
  }

  return {
    mountPresentation: mountPresentation,
    registerMountedReport: registerMountedReport,
    releaseDocument: releaseDocument
  };
}
