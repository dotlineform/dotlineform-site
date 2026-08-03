const TABLE_DETAIL_SELECTOR = 'table[data-docs-content-detail="table"]';
const TABLE_DETAIL_MARKER = "data-docs-content-detail";
const REFERENCE_ATTRIBUTES = ["headers", "aria-labelledby", "aria-describedby", "aria-controls", "aria-owns"];

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function positiveInteger(value) {
  var number = Number(value);
  return Number.isInteger(number) && number > 0 ? number : 0;
}

function sameDocumentTarget(left, right) {
  var first = left || {};
  var second = right || {};
  return cleanString(first.scope) === cleanString(second.scope)
    && cleanString(first.subScope) === cleanString(second.subScope)
    && cleanString(first.docId) === cleanString(second.docId);
}

function immutableTargetContext(state, record) {
  return Object.freeze({
    documentTarget: Object.freeze(Object.assign({}, state.documentTarget)),
    documentMountGeneration: state.documentMountGeneration,
    kind: "table",
    adapterTargetId: record.id,
    occurrence: record.occurrence
  });
}

function createOpenControl(documentRef, label) {
  var row = documentRef.createElement("div");
  row.className = "docsViewer__tableDetailControlRow";
  row.setAttribute("data-docs-content-detail-control", "table");

  var button = documentRef.createElement("button");
  button.className = "docsViewer__tableDetailOpen";
  button.type = "button";
  button.innerHTML = [
    '<svg class="docsViewer__diagramDetailIcon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">',
    '  <path d="M14 5h5v5M19 5l-8 8M19 13v6H5V5h6"></path>',
    "</svg>"
  ].join("");
  button.setAttribute("aria-label", "Open " + label.toLowerCase());
  button.title = "Open " + label.toLowerCase();
  row.appendChild(button);
  return { button: button, row: row };
}

function remapCloneIds(table, prefix) {
  var identified = Array.from(table.querySelectorAll("[id]"));
  if (table.id) identified.unshift(table);
  var counts = identified.reduce(function (values, element) {
    var id = cleanString(element.id);
    if (id) values.set(id, (values.get(id) || 0) + 1);
    return values;
  }, new Map());
  var remapped = new Map();
  var sequence = 0;

  identified.forEach(function (element) {
    var currentId = cleanString(element.id);
    if (!currentId || counts.get(currentId) !== 1) {
      element.removeAttribute("id");
      return;
    }
    sequence += 1;
    var nextId = prefix + "-" + sequence;
    remapped.set(currentId, nextId);
    element.id = nextId;
  });

  REFERENCE_ATTRIBUTES.forEach(function (attribute) {
    var referenced = Array.from(table.querySelectorAll("[" + attribute + "]"));
    if (table.hasAttribute(attribute)) referenced.unshift(table);
    referenced.forEach(function (element) {
      var references = cleanString(element.getAttribute(attribute)).split(/\s+/).filter(Boolean);
      var mapped = references.map(function (reference) {
        return remapped.get(reference) || "";
      }).filter(Boolean);
      if (mapped.length) {
        element.setAttribute(attribute, mapped.join(" "));
      } else {
        element.removeAttribute(attribute);
      }
    });
  });
}

/** Clone one accepted semantic table while keeping its internal relationships document-unique. */
export function cloneDocsViewerTableDetailTable(table, targetContext) {
  if (!table || typeof table.cloneNode !== "function") {
    throw new Error("Table detail requires an accepted semantic table.");
  }
  var clone = table.cloneNode(true);
  clone.removeAttribute(TABLE_DETAIL_MARKER);
  clone.querySelectorAll("[data-docs-content-detail-control]").forEach(function (control) {
    control.remove();
  });
  clone.classList.add("docsViewer__tableDetailTable");
  var target = targetContext || {};
  var prefix = [
    "docs-table-detail",
    positiveInteger(target.documentMountGeneration),
    cleanString(target.adapterTargetId).replace(/[^a-zA-Z0-9_-]+/g, "-") || "table"
  ].join("-");
  remapCloneIds(clone, prefix);
  return clone;
}

/** Own exact marked-table registration for one rendered-document mount. */
export function createDocsViewerTableDetailAdapter() {
  var stateByRoot = new WeakMap();

  function releaseState(root, state) {
    if (!state) return { released: 0 };
    state.presentations.forEach(function (presentation) {
      presentation.release();
    });
    state.presentations.clear();
    state.records.forEach(function (record) {
      record.button.removeEventListener("click", record.handleClick);
      record.controlRow.remove();
    });
    stateByRoot.delete(root);
    return { released: state.records.size };
  }

  function releaseDocument(releaseContext) {
    var context = releaseContext || {};
    var root = context.content;
    if (!root || typeof root !== "object") return { released: 0 };
    return releaseState(root, stateByRoot.get(root));
  }

  function resolveRecord(root, targetContext) {
    var target = targetContext || {};
    var state = root ? stateByRoot.get(root) : null;
    if (
      !state
      || cleanString(target.kind) !== "table"
      || positiveInteger(target.documentMountGeneration) !== state.documentMountGeneration
      || !sameDocumentTarget(target.documentTarget, state.documentTarget)
    ) {
      return null;
    }
    var record = state.records.get(cleanString(target.adapterTargetId)) || null;
    return record && root.contains(record.table) ? { record: record, state: state } : null;
  }

  function mountDocument(mountContext) {
    var context = mountContext || {};
    var root = context.content;
    if (!root || typeof root.querySelectorAll !== "function") {
      return { found: 0, decorated: 0, skipped: 0 };
    }
    releaseState(root, stateByRoot.get(root));

    var documentRef = context.document || root.ownerDocument;
    var doc = context.doc || {};
    var documentMountGeneration = positiveInteger(context.documentMountGeneration);
    var documentTarget = {
      scope: cleanString(context.viewerScope),
      subScope: "",
      docId: cleanString(doc.doc_id)
    };
    var tables = Array.from(root.querySelectorAll(TABLE_DETAIL_SELECTOR));
    if (!documentRef || !documentMountGeneration || !documentTarget.scope || !documentTarget.docId) {
      return { found: tables.length, decorated: 0, skipped: tables.length };
    }

    var state = {
      documentMountGeneration: documentMountGeneration,
      documentTarget: documentTarget,
      presentations: new Set(),
      records: new Map(),
      requestContentDetail: typeof context.requestContentDetail === "function"
        ? context.requestContentDetail
        : function () { return false; }
    };
    tables.forEach(function (table, index) {
      var occurrence = index + 1;
      var id = "table-" + index;
      var label = "Table " + occurrence;
      var control = createOpenControl(documentRef, label);
      var record = {
        button: control.button,
        controlRow: control.row,
        handleClick: null,
        id: id,
        label: label,
        occurrence: occurrence,
        table: table
      };
      record.handleClick = function () {
        var current = resolveRecord(root, immutableTargetContext(state, record));
        if (!current) return;
        state.requestContentDetail(immutableTargetContext(state, record));
      };
      record.button.addEventListener("click", record.handleClick);
      table.before(record.controlRow);
      state.records.set(id, record);
    });
    stateByRoot.set(root, state);
    return { found: tables.length, decorated: tables.length, skipped: 0 };
  }

  function mountPresentation(presentationContext) {
    var context = presentationContext || {};
    var root = context.content;
    var resolved = resolveRecord(root, context.targetContext);
    if (!resolved) throw new Error("Table detail target is stale or unavailable.");

    var record = resolved.record;
    var state = resolved.state;
    var documentRef = context.document || root.ownerDocument;
    var section = documentRef.createElement("section");
    section.className = "docsViewer__contentDetail docsViewer__contentDetail--table";
    section.setAttribute("data-docs-content-detail-view", "table");

    var viewport = documentRef.createElement("div");
    viewport.className = "docsViewer__tableDetailViewport";
    viewport.tabIndex = 0;
    viewport.setAttribute("role", "region");
    viewport.setAttribute("aria-label", record.label);
    viewport.appendChild(cloneDocsViewerTableDetailTable(record.table, context.targetContext));
    section.appendChild(viewport);

    var released = false;
    var presentation = {
      focusTarget: viewport,
      invocationControl: record.button,
      label: record.label,
      root: section,
      release: function () {
        if (released) return;
        released = true;
        section.remove();
        state.presentations.delete(presentation);
      }
    };
    state.presentations.add(presentation);
    return presentation;
  }

  return {
    mountDocument: mountDocument,
    mountPresentation: mountPresentation,
    releaseDocument: releaseDocument
  };
}

export const docsViewerTableDetailAdapter = createDocsViewerTableDetailAdapter();
