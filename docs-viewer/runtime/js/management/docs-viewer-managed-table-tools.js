export const CONTENT_DETAIL_RESET_WIDTHS_CONTROL_ID = "content-detail-reset-widths";
export const CONTENT_DETAIL_COPY_TABLE_CONTROL_ID = "content-detail-copy-table";

const RESET_WIDTHS_RENDERER_ID = "content-detail-reset-widths";
const COPY_TABLE_RENDERER_ID = "content-detail-copy-table";
const MIN_COLUMN_WIDTH = 72;
const MAX_COLUMN_WIDTH = 4096;
const KEYBOARD_RESIZE_STEP = 16;

function cleanText(value) {
  return String(value == null ? "" : value).replace(/\s+/g, " ").trim();
}

function positiveSpan(value) {
  var span = Number(value);
  return Number.isInteger(span) && span > 0 ? span : 1;
}

function clampWidth(value) {
  return Math.min(MAX_COLUMN_WIDTH, Math.max(MIN_COLUMN_WIDTH, Math.round(Number(value) || 0)));
}

/** Serialize the accepted semantic table as plain-text TSV for spreadsheet paste. */
export function serializeDocsViewerTableToTsv(table) {
  if (!table || !table.rows) throw new Error("Copy table requires a semantic table.");
  var rows = Array.from(table.rows);
  if (!rows.length) return "";
  var grid = rows.map(function () { return []; });

  rows.forEach(function (row, rowIndex) {
    var columnIndex = 0;
    Array.from(row.cells || []).forEach(function (cell) {
      while (grid[rowIndex][columnIndex] !== undefined) columnIndex += 1;
      var columnSpan = positiveSpan(cell.colSpan);
      var rowSpan = positiveSpan(cell.rowSpan);
      for (var rowOffset = 0; rowOffset < rowSpan && rowIndex + rowOffset < rows.length; rowOffset += 1) {
        for (var columnOffset = 0; columnOffset < columnSpan; columnOffset += 1) {
          grid[rowIndex + rowOffset][columnIndex + columnOffset] = rowOffset === 0 && columnOffset === 0
            ? cleanText(cell.textContent)
            : "";
        }
      }
      columnIndex += columnSpan;
    });
  });

  var columnCount = grid.reduce(function (maximum, row) {
    return Math.max(maximum, row.length);
  }, 0);
  return grid.map(function (row) {
    return Array.from({ length: columnCount }, function (_, index) {
      return row[index] === undefined ? "" : row[index];
    }).join("\t");
  }).join("\n");
}

function resetWidthsControlRenderer(context) {
  var button = context.existingRoot;
  if (!button || button.tagName !== "BUTTON") {
    button = context.document.createElement("button");
    button.className = "docsViewer__actionButton docsViewer__tableResetWidths";
    button.type = "button";
  }
  button.textContent = "Reset widths";
  return button;
}

function copyTableControlRenderer(context) {
  var button = context.existingRoot;
  if (!button || button.tagName !== "BUTTON") {
    button = context.document.createElement("button");
    button.className = "docsViewer__actionButton docsViewer__actionButton--iconOnly docsViewer__tableCopy";
    button.type = "button";
    button.innerHTML = [
      '<svg class="docsViewer__tableToolIcon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">',
      '  <rect x="9" y="9" width="10" height="10" rx="2"></rect>',
      '  <path d="M15 9V7a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2"></path>',
      "</svg>"
    ].join("");
  }
  return button;
}

export function createDocsViewerManagedTableToolControlRenderers() {
  return {
    [RESET_WIDTHS_RENDERER_ID]: resetWidthsControlRenderer,
    [COPY_TABLE_RENDERER_ID]: copyTableControlRenderer
  };
}

export function withDocsViewerManagedTableToolDefinitions(definitions) {
  var source = definitions || {};
  return Object.assign({}, source, {
    views: (source.views || []).slice(),
    modes: (source.modes || []).slice(),
    controls: (source.controls || []).concat([
      {
        id: CONTENT_DETAIL_RESET_WIDTHS_CONTROL_ID,
        label: "Reset widths",
        ownerType: "view",
        ownerViewId: "content-detail",
        surfaceId: "main-view",
        appKinds: ["manage"],
        features: ["management"],
        renderer: RESET_WIDTHS_RENDERER_ID
      },
      {
        id: CONTENT_DETAIL_COPY_TABLE_CONTROL_ID,
        label: "Copy table",
        ownerType: "view",
        ownerViewId: "content-detail",
        surfaceId: "main-view",
        appKinds: ["manage"],
        features: ["management"],
        renderer: COPY_TABLE_RENDERER_ID
      }
    ])
  });
}

function defaultWriteClipboardText(text, context) {
  var windowRef = context && context.window;
  if (
    !windowRef
    || !windowRef.navigator
    || !windowRef.navigator.clipboard
    || typeof windowRef.navigator.clipboard.writeText !== "function"
  ) {
    return Promise.reject(new Error("Clipboard access is unavailable."));
  }
  return windowRef.navigator.clipboard.writeText(text);
}

function directionMultiplier(state) {
  var windowRef = state.document && state.document.defaultView;
  if (!windowRef || typeof windowRef.getComputedStyle !== "function") return 1;
  return windowRef.getComputedStyle(state.table).direction === "rtl" ? -1 : 1;
}

function measureColumnWidths(state) {
  return state.headers.map(function (header) {
    return clampWidth(header.getBoundingClientRect().width);
  });
}

function updateHandleValues(state, widths) {
  state.handles.forEach(function (handle, index) {
    var width = clampWidth(widths[index]);
    handle.setAttribute("aria-valuenow", String(width));
    handle.setAttribute("aria-valuetext", width + " pixels");
  });
}

function projectControl(state, controlId, controlState) {
  if (typeof state.projectControlState === "function") {
    state.projectControlState(controlId, controlState);
  }
}

function projectActiveControls(state) {
  projectControl(state, CONTENT_DETAIL_RESET_WIDTHS_CONTROL_ID, {
    disabled: !state.widths,
    hidden: !state.resizable
  });
  projectControl(state, CONTENT_DETAIL_COPY_TABLE_CONTROL_ID, {
    disabled: !state.copyEnabled,
    hidden: !state.copyEnabled
  });
}

function hideControls(state) {
  projectControl(state, CONTENT_DETAIL_RESET_WIDTHS_CONTROL_ID, { disabled: true, hidden: true });
  projectControl(state, CONTENT_DETAIL_COPY_TABLE_CONTROL_ID, { disabled: true, hidden: true });
}

function ensureManagedColgroup(state) {
  if (state.colgroup) return state.colgroup;
  var colgroup = state.document.createElement("colgroup");
  colgroup.setAttribute("data-docs-viewer-managed-table-widths", "");
  state.headers.forEach(function () {
    colgroup.appendChild(state.document.createElement("col"));
  });
  var reference = state.table.tHead || state.table.tBodies[0] || state.table.tFoot || state.table.firstChild;
  state.table.insertBefore(colgroup, reference || null);
  state.colgroup = colgroup;
  return colgroup;
}

function applyColumnWidths(state, values) {
  var widths = values.map(clampWidth);
  var colgroup = ensureManagedColgroup(state);
  Array.from(colgroup.children).forEach(function (column, index) {
    column.style.width = widths[index] + "px";
  });
  state.widths = widths;
  state.table.classList.add("docsViewer__tableDetailTable--managedWidths");
  state.table.style.width = widths.reduce(function (total, width) { return total + width; }, 0) + "px";
  updateHandleValues(state, widths);
  projectActiveControls(state);
}

function clearColumnWidths(state) {
  if (state.colgroup) state.colgroup.remove();
  state.colgroup = null;
  state.widths = null;
  state.table.classList.remove("docsViewer__tableDetailTable--managedWidths");
  if (state.originalTableWidth) {
    state.table.style.width = state.originalTableWidth;
  } else {
    state.table.style.removeProperty("width");
  }
  if (state.active) {
    updateHandleValues(state, measureColumnWidths(state));
    projectActiveControls(state);
  }
}

function cleanupActivePointer(state) {
  var pointer = state.activePointer;
  if (!pointer) return;
  state.activePointer = null;
  pointer.handle.removeEventListener("pointermove", pointer.move);
  pointer.handle.removeEventListener("pointerup", pointer.finish);
  pointer.handle.removeEventListener("pointercancel", pointer.finish);
  pointer.handle.removeEventListener("lostpointercapture", pointer.finish);
  if (
    typeof pointer.handle.hasPointerCapture === "function"
    && pointer.handle.hasPointerCapture(pointer.pointerId)
    && typeof pointer.handle.releasePointerCapture === "function"
  ) {
    pointer.handle.releasePointerCapture(pointer.pointerId);
  }
}

function beginPointerResize(state, columnIndex, handle, event) {
  if (state.released || (Number.isFinite(event.button) && event.button !== 0)) return;
  cleanupActivePointer(state);
  var startWidths = state.widths ? state.widths.slice() : measureColumnWidths(state);
  var startX = Number(event.clientX) || 0;
  var multiplier = directionMultiplier(state);
  var pointerId = Number(event.pointerId) || 0;

  function move(moveEvent) {
    if (Number(moveEvent.pointerId) !== pointerId) return;
    var widths = startWidths.slice();
    widths[columnIndex] = clampWidth(startWidths[columnIndex] + ((Number(moveEvent.clientX) || 0) - startX) * multiplier);
    applyColumnWidths(state, widths);
    moveEvent.preventDefault();
  }

  function finish(finishEvent) {
    if (finishEvent && Number(finishEvent.pointerId) !== pointerId) return;
    cleanupActivePointer(state);
  }

  state.activePointer = { finish: finish, handle: handle, move: move, pointerId: pointerId };
  handle.addEventListener("pointermove", move);
  handle.addEventListener("pointerup", finish);
  handle.addEventListener("pointercancel", finish);
  handle.addEventListener("lostpointercapture", finish);
  if (typeof handle.setPointerCapture === "function") {
    try {
      handle.setPointerCapture(pointerId);
    } catch (_error) {
      // Synthetic pointer events may not establish native capture; local listeners remain authoritative.
    }
  }
  event.preventDefault();
}

function handleKeyboardResize(state, columnIndex, event) {
  if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
  var widths = state.widths ? state.widths.slice() : measureColumnWidths(state);
  var physicalDirection = event.key === "ArrowRight" ? 1 : -1;
  widths[columnIndex] = clampWidth(
    widths[columnIndex] + physicalDirection * directionMultiplier(state) * KEYBOARD_RESIZE_STEP
  );
  applyColumnWidths(state, widths);
  event.preventDefault();
}

function directColgroup(table) {
  return Array.from(table.children || []).find(function (child) {
    return child.tagName === "COLGROUP";
  }) || null;
}

function headerCells(table) {
  var headerRow = table.tHead && table.tHead.rows.length
    ? table.tHead.rows[table.tHead.rows.length - 1]
    : null;
  return headerRow ? Array.from(headerRow.cells) : [];
}

function simpleHeadersMatch(state, headers) {
  var existingColgroup = directColgroup(state.table);
  return Boolean(
    headers.length
    && (!existingColgroup || existingColgroup === state.colgroup)
    && headers.every(function (header) {
      return positiveSpan(header.colSpan) === 1 && positiveSpan(header.rowSpan) === 1;
    })
  );
}

function cellMatchesColumn(cell, column) {
  return cleanText(cell && cell.getAttribute("data-report-column-id")) === column.id
    && cleanText(cell && cell.getAttribute("data-report-column-visibility")) === column.visibility
    && positiveSpan(cell && cell.colSpan) === 1
    && positiveSpan(cell && cell.rowSpan) === 1;
}

function exactReportColumnsMatch(state, headers) {
  var columns = state.columns;
  if (!columns || !state.table.tHead || state.table.tHead.rows.length !== 1 || headers.length !== columns.length) {
    return false;
  }
  if (!headers.every(function (header, index) { return cellMatchesColumn(header, columns[index]); })) {
    return false;
  }
  return Array.from(state.table.tBodies || []).every(function (body) {
    return Array.from(body.rows || []).every(function (row) {
      var cells = Array.from(row.cells || []);
      return cells.length === columns.length
        && cells.every(function (cell, index) { return cellMatchesColumn(cell, columns[index]); });
    });
  });
}

function refreshEligibility(state) {
  state.headers = headerCells(state.table);
  state.resizable = simpleHeadersMatch(state, state.headers)
    && (!state.columns || exactReportColumnsMatch(state, state.headers));
}

function createPresentationState(context, options) {
  var table = context && context.table;
  var documentRef = context && context.document;
  var settings = options || {};
  if (!table || !documentRef) throw new Error("Managed table tools require the active table presentation.");
  var state = {
    active: false,
    activePointer: null,
    cleanup: [],
    colgroup: null,
    columns: settings.columns || null,
    copyEnabled: settings.copyEnabled !== false,
    document: documentRef,
    handleCleanup: [],
    handles: [],
    headers: [],
    originalTableWidth: table.style.width,
    projectControlState: null,
    released: false,
    resizable: false,
    table: table,
    viewport: context.viewport,
    widths: null
  };
  refreshEligibility(state);
  return state;
}

function mountResizeHandles(state) {
  if (!state.resizable) return;
  state.headers.forEach(function (header, index) {
    var declaredColumn = state.columns && state.columns[index];
    var columnLabel = cleanText(declaredColumn && declaredColumn.label)
      || cleanText(header.textContent)
      || "Column " + (index + 1);
    var handle = state.document.createElement("span");
    handle.className = "docsViewer__tableResizeHandle";
    handle.tabIndex = 0;
    handle.setAttribute("role", "separator");
    handle.setAttribute("aria-orientation", "vertical");
    handle.setAttribute("aria-label", "Resize " + columnLabel);
    handle.setAttribute("aria-valuemin", String(MIN_COLUMN_WIDTH));
    handle.setAttribute("aria-valuemax", String(MAX_COLUMN_WIDTH));
    handle.title = "Resize " + columnLabel;
    var onPointerDown = function (event) { beginPointerResize(state, index, handle, event); };
    var onKeyDown = function (event) { handleKeyboardResize(state, index, event); };
    handle.addEventListener("pointerdown", onPointerDown);
    handle.addEventListener("keydown", onKeyDown);
    state.handleCleanup.push(function () {
      handle.removeEventListener("pointerdown", onPointerDown);
      handle.removeEventListener("keydown", onKeyDown);
    });
    header.classList.add("docsViewer__tableResizeHeader");
    header.appendChild(handle);
    state.handles.push(handle);
  });
}

function clearResizeHandles(state) {
  cleanupActivePointer(state);
  state.handleCleanup.splice(0).forEach(function (cleanup) { cleanup(); });
  state.handles.forEach(function (handle) { handle.remove(); });
  state.headers.forEach(function (header) { header.classList.remove("docsViewer__tableResizeHeader"); });
  state.handles = [];
}

function refreshReportPresentation(state) {
  if (state.released) return;
  var retainedWidths = state.widths ? state.widths.slice() : null;
  clearResizeHandles(state);
  refreshEligibility(state);
  if (!state.resizable) {
    clearColumnWidths(state);
    return;
  }
  mountResizeHandles(state);
  if (retainedWidths && retainedWidths.length === state.headers.length) {
    applyColumnWidths(state, retainedWidths);
  } else if (state.active) {
    updateHandleValues(state, measureColumnWidths(state));
    projectActiveControls(state);
  }
}

export function createDocsViewerManagedTableTools(options) {
  var settings = options || {};
  var writeClipboardText = typeof settings.writeClipboardText === "function"
    ? settings.writeClipboardText
    : defaultWriteClipboardText;
  var activeState = null;

  function releaseState(state) {
    if (!state || state.released) return;
    state.released = true;
    state.cleanup.splice(0).forEach(function (cleanup) { cleanup(); });
    clearResizeHandles(state);
    state.active = false;
    clearColumnWidths(state);
    hideControls(state);
    if (activeState === state) activeState = null;
  }

  function resetWidths() {
    if (!activeState || activeState.released) throw new Error("Reset widths is unavailable.");
    clearColumnWidths(activeState);
  }

  function copyTable() {
    if (!activeState || activeState.released || !activeState.copyEnabled) {
      return Promise.reject(new Error("Copy table is unavailable."));
    }
    var text = serializeDocsViewerTableToTsv(activeState.table);
    return Promise.resolve(writeClipboardText(text, {
      document: activeState.document,
      window: activeState.document.defaultView
    }));
  }

  function reportFailure(context, fallback, error) {
    var message = error && error.message ? error.message : fallback;
    if (context && typeof context.setStatus === "function") context.setStatus(message, true);
  }

  return {
    controlHandlers: function () {
      return {
        [CONTENT_DETAIL_RESET_WIDTHS_CONTROL_ID]: function (context) {
          try {
            resetWidths();
          } catch (error) {
            reportFailure(context, "Reset widths failed.", error);
          }
        },
        [CONTENT_DETAIL_COPY_TABLE_CONTROL_ID]: function (context) {
          copyTable().catch(function (error) {
            reportFailure(context, "Copy table failed.", error);
          });
        }
      };
    },
    presentationExtension: {
      mount: function (context) {
        var state = createPresentationState(context, { copyEnabled: true });
        mountResizeHandles(state);
        return {
          activate: function (activationContext) {
            if (state.released) throw new Error("Managed table presentation is unavailable.");
            activeState = state;
            state.active = true;
            state.projectControlState = activationContext && activationContext.projectControlState;
            if (state.resizable) updateHandleValues(state, measureColumnWidths(state));
            projectActiveControls(state);
          },
          release: function () { releaseState(state); }
        };
      }
    },
    reportPresentationExtension: {
      mount: function (context) {
        if (!context || context.kind !== "semantic-table") return null;
        var state = createPresentationState(context, {
          columns: context.columns,
          copyEnabled: false
        });
        mountResizeHandles(state);
        var subscriptionCleanup;
        try {
          subscriptionCleanup = context.subscribe(function () {
            refreshReportPresentation(state);
          });
          if (typeof subscriptionCleanup !== "function") {
            throw new Error("Managed report table requires refresh-subscription cleanup.");
          }
        } catch (error) {
          clearResizeHandles(state);
          throw error;
        }
        state.cleanup.push(subscriptionCleanup);
        return {
          activate: function (activationContext) {
            if (state.released) throw new Error("Managed report table presentation is unavailable.");
            activeState = state;
            state.active = true;
            state.projectControlState = activationContext && activationContext.projectControlState;
            if (state.resizable) updateHandleValues(state, measureColumnWidths(state));
            projectActiveControls(state);
          },
          release: function () { releaseState(state); }
        };
      }
    }
  };
}
