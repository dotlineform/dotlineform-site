let recordListId = 0;

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function valueText(value) {
  const text = normalizeText(value);
  return text || "\u2014";
}

function safeUrl(value) {
  const href = normalizeText(value);
  if (!href) return "";
  if (/^(javascript|data):/i.test(href)) return "";
  return href;
}

function safeSrcset(value) {
  return normalizeText(value)
    .split(",")
    .map((entry) => {
      const parts = entry.trim().split(/\s+/);
      const url = safeUrl(parts[0]);
      if (!url) return "";
      return [url, ...parts.slice(1)].join(" ");
    })
    .filter(Boolean)
    .join(", ");
}

function positiveInteger(value) {
  const number = Number(value);
  if (!Number.isFinite(number) || number <= 0) return "";
  return String(Math.floor(number));
}

function columnValue(column, record, index) {
  if (typeof column.value === "function") return column.value(record, { index, column });
  return record && column.key ? record[column.key] : "";
}

function columnRecordValue(column, record, index, optionKey) {
  const option = column && column[optionKey];
  if (typeof option === "function") return option(record, { index, column });
  return record && option ? record[option] : "";
}

function recordId(options, record, index) {
  if (typeof options.getRecordId === "function") return normalizeText(options.getRecordId(record, index));
  if (record && record.id != null) return normalizeText(record.id);
  return String(index);
}

function isSelectable(options = {}) {
  return options.selectionMode === "single" || options.selectionMode === "multiple";
}

function initialSelectedIds(options, records) {
  const initial = options.initialSelection;
  if (initial == null) return [];
  if (Number.isInteger(initial) && initial >= 0 && initial < records.length) {
    return [recordId(options, records[initial], initial)];
  }
  const ids = new Set((Array.isArray(initial) ? initial : [initial]).map(normalizeText));
  return records.map((record, index) => recordId(options, record, index)).filter(id => ids.has(id));
}

function clearNode(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function setText(node, value) {
  node.textContent = valueText(value);
}

function appendImageCellContent(cell, column, record, index, rawValue) {
  cell.classList.add("sharedRecordList__cell--image");
  const frame = document.createElement("span");
  frame.className = "sharedRecordList__imageFrame";
  const src = safeUrl(column.srcKey ? columnRecordValue(column, record, index, "srcKey") : rawValue);
  const srcset = safeSrcset(columnRecordValue(column, record, index, "srcsetKey"));
  const sizes = normalizeText(columnRecordValue(column, record, index, "sizesKey") || column.sizes);
  const width = positiveInteger(columnRecordValue(column, record, index, "widthKey") || column.widthPx || column.imageWidth);
  const height = positiveInteger(columnRecordValue(column, record, index, "heightKey") || column.heightPx || column.imageHeight);
  const alt = normalizeText(columnRecordValue(column, record, index, "altKey") || column.alt);
  const fallbackText = normalizeText(columnRecordValue(column, record, index, "fallbackTextKey") || column.fallbackText);
  frame.dataset.recordListImageState = src ? "loading" : "missing";
  if (width) frame.style.setProperty("--shared-record-list-image-width", `${width}px`);
  if (height) frame.style.setProperty("--shared-record-list-image-height", `${height}px`);

  if (src) {
    const image = document.createElement("img");
    image.className = "sharedRecordList__image";
    image.src = src;
    if (srcset) image.srcset = srcset;
    if (sizes) image.sizes = sizes;
    if (width) image.width = Number(width);
    if (height) image.height = Number(height);
    image.alt = alt;
    image.loading = normalizeText(column.loading) || "lazy";
    image.decoding = normalizeText(column.decoding) || "async";
    const setReady = () => {
      frame.dataset.recordListImageState = "ready";
    };
    const setMissing = () => {
      frame.dataset.recordListImageState = "missing";
    };
    image.addEventListener("load", setReady, { once: true });
    image.addEventListener("error", setMissing, { once: true });
    if (image.complete) {
      if (image.naturalWidth > 0) setReady();
      else setMissing();
    }
    frame.appendChild(image);
  }

  const placeholder = document.createElement("span");
  placeholder.className = "sharedRecordList__imagePlaceholder";
  placeholder.textContent = fallbackText;
  frame.appendChild(placeholder);
  cell.appendChild(frame);
}

function appendCell(rowNode, column, record, index, role) {
  const cell = document.createElement("div");
  cell.className = ["sharedRecordList__cell", column.className].filter(Boolean).join(" ");
  cell.setAttribute("role", role);
  cell.dataset.recordListCell = column.key || String(index);

  const rawValue = columnValue(column, record, index);
  const text = valueText(rawValue);
  if (column.type === "image") {
    appendImageCellContent(cell, column, record, index, rawValue);
    rowNode.appendChild(cell);
    return;
  }

  if (column.truncate !== false) {
    cell.classList.add("sharedRecordList__cell--truncate");
    cell.title = text;
  }

  if (column.type === "link") {
    const href = safeUrl(column.hrefKey ? record && record[column.hrefKey] : rawValue);
    if (href) {
      const link = document.createElement("a");
      link.className = "sharedRecordList__link";
      link.href = href;
      link.textContent = text;
      link.title = text;
      if (column.external !== false) {
        link.target = "_blank";
        link.rel = "noopener noreferrer";
      }
      cell.appendChild(link);
    } else {
      setText(cell, text);
    }
  } else {
    setText(cell, text);
  }

  rowNode.appendChild(cell);
}

function columnTemplate(columns) {
  if (!columns.length) return "minmax(0, 1fr)";
  return columns.map((column) => normalizeText(column.width) || "minmax(0, 1fr)").join(" ");
}

function hasImageColumn(columns) {
  return columns.some((column) => column && column.type === "image");
}

function renderHeader(rootNode, columns, options) {
  if (options.showHeader === false) return;
  const header = document.createElement("div");
  header.className = "sharedRecordList__header";
  header.setAttribute("role", "row");
  header.style.gridTemplateColumns = `var(--shared-record-list-columns, ${columnTemplate(columns)})`;
  columns.forEach((column) => {
    const cell = document.createElement("div");
    cell.className = "sharedRecordList__headerCell";
    cell.setAttribute("role", "columnheader");
    cell.dataset.recordListHeader = column.key || "";
    cell.textContent = normalizeText(column.label || column.key);
    header.appendChild(cell);
  });
  rootNode.appendChild(header);
}

function renderEmpty(rootNode, options) {
  const empty = document.createElement("p");
  empty.className = "sharedRecordList__empty";
  empty.dataset.recordListEmpty = "true";
  empty.textContent = options.emptyText === "" ? "" : normalizeText(options.emptyText) || "No records.";
  rootNode.appendChild(empty);
}

function selectionsFor(controller) {
  const records = Array.isArray(controller.options.records) ? controller.options.records : [];
  return records.map((record, index) => ({ id: recordId(controller.options, record, index), index, record }))
    .filter(item => controller.selectedIds.has(item.id));
}

function selectionFor(controller) {
  const selections = selectionsFor(controller);
  return selections.length === 1 ? selections[0] : null;
}

function selectedRowIndex(controller) {
  return controller.options.records.findIndex((record, index) => recordId(controller.options, record, index) === controller.focusedId);
}

function setRovingTabIndex(controller) {
  const rows = [...controller.rootNode.querySelectorAll("[data-record-list-row='true']")];
  if (!isSelectable(controller.options)) {
    rows.forEach((row) => row.removeAttribute("tabindex"));
    return;
  }
  const selectedIndex = selectedRowIndex(controller);
  const focusIndex = selectedIndex >= 0 ? selectedIndex : 0;
  rows.forEach((row, index) => {
    row.tabIndex = index === focusIndex ? 0 : -1;
  });
}

function syncSelectionState(controller) {
  const rows = [...controller.rootNode.querySelectorAll("[data-record-list-row='true']")];
  const availableIds = new Set(rows.map(row => row.dataset.recordListRecordId));
  controller.selectedIds = new Set([...controller.selectedIds].filter(id => availableIds.has(id)));
  if (!availableIds.has(controller.focusedId)) controller.focusedId = [...controller.selectedIds][0] || "";
  if (!availableIds.has(controller.anchorId)) controller.anchorId = controller.focusedId;
  rows.forEach((row) => {
    const selected = controller.selectedIds.has(row.dataset.recordListRecordId);
    row.classList.toggle("sharedRecordList__row--selected", selected);
    row.setAttribute("aria-selected", selected ? "true" : "false");
  });
  controller.rootNode.dataset.recordListSelectedId = selectionFor(controller)?.id || "";
  setRovingTabIndex(controller);
}

function emitSelectionChange(controller) {
  const records = Array.isArray(controller.options.records) ? controller.options.records : [];
  const payload = {
    selection: selectionFor(controller),
    selections: selectionsFor(controller),
    records
  };
  if (typeof controller.options.onSelectionChange === "function") {
    controller.options.onSelectionChange(payload);
  }
  controller.selectionListeners.forEach((listener) => listener(payload));
}

function selectRow(controller, row, { focus = false, emit = true, shiftKey = false, metaKey = false, ctrlKey = false } = {}) {
  if (!row || !isSelectable(controller.options)) return;
  const id = row.dataset.recordListRecordId;
  const previous = [...controller.selectedIds].sort().join(",");
  const multiple = controller.options.selectionMode === "multiple";
  const ids = controller.options.records.map((record, index) => recordId(controller.options, record, index));
  const anchor = ids.indexOf(controller.anchorId);
  if (multiple && shiftKey && anchor >= 0) {
    const end = ids.indexOf(id);
    const range = ids.slice(Math.min(anchor, end), Math.max(anchor, end) + 1);
    controller.selectedIds = new Set(metaKey || ctrlKey ? [...controller.selectedIds, ...range] : range);
  } else if (multiple && (metaKey || ctrlKey)) {
    if (controller.selectedIds.has(id)) controller.selectedIds.delete(id);
    else controller.selectedIds.add(id);
    controller.anchorId = id;
  } else {
    controller.selectedIds = new Set([id]);
    controller.anchorId = id;
  }
  controller.focusedId = id;
  syncSelectionState(controller);
  if (focus) row.focus();
  if (emit && (!multiple || previous !== [...controller.selectedIds].sort().join(","))) emitSelectionChange(controller);
}

function clearSelection(controller, { emit = true } = {}) {
  if (!controller.selectedIds.size) return;
  controller.selectedIds.clear();
  controller.focusedId = "";
  controller.anchorId = "";
  syncSelectionState(controller);
  if (emit) emitSelectionChange(controller);
}

function nodeContainsTarget(node, target) {
  return Boolean(node && target && typeof node.contains === "function" && node.contains(target));
}

function isInsideListBoundary(controller, target) {
  if (nodeContainsTarget(controller.rootNode, target)) return true;
  return [...controller.focusBoundaryNodes].some((node) => nodeContainsTarget(node, target));
}

function maybeClearSelectionFromOutsideTarget(controller, target) {
  if (!controller.options.clearSelectionOnBlur) return;
  if (isInsideListBoundary(controller, target)) return;
  clearSelection(controller);
}

function focusRelativeRow(controller, row, offset, modifiers) {
  if (!row || !isSelectable(controller.options)) return;
  const rows = [...controller.rootNode.querySelectorAll("[data-record-list-row='true']")];
  const currentIndex = rows.indexOf(row);
  if (currentIndex < 0) return;
  const nextIndex = Math.max(0, Math.min(rows.length - 1, currentIndex + offset));
  selectRow(controller, rows[nextIndex], { ...modifiers, focus: true });
}

function renderRows(controller, options) {
  const rootNode = controller.rootNode;
  const records = Array.isArray(options.records) ? options.records : [];
  const columns = Array.isArray(options.columns) ? options.columns : [];
  clearNode(rootNode);
  rootNode.classList.add("sharedRecordList");
  rootNode.dataset.recordListId = controller.id;
  rootNode.setAttribute("role", isSelectable(options) ? "grid" : "table");
  if (isSelectable(options)) rootNode.setAttribute("aria-multiselectable", String(options.selectionMode === "multiple"));
  else rootNode.removeAttribute("aria-multiselectable");
  const selectedBackground = normalizeText(options.selectedBackground);
  if (selectedBackground) rootNode.style.setProperty("--shared-record-list-selected-bg", selectedBackground);
  else rootNode.style.removeProperty("--shared-record-list-selected-bg");

  if (!columns.length) {
    controller.selectedIds.clear();
    rootNode.dataset.recordListSelectedId = "";
    renderEmpty(rootNode, { ...options, emptyText: options.emptyText || "No columns." });
    return;
  }

  renderHeader(rootNode, columns, options);

  if (!records.length) {
    controller.selectedIds.clear();
    rootNode.dataset.recordListSelectedId = "";
    renderEmpty(rootNode, options);
    return;
  }

  const rowsNode = document.createElement("div");
  rowsNode.className = "sharedRecordList__rows";
  rowsNode.setAttribute("role", "rowgroup");
  rootNode.appendChild(rowsNode);

  records.forEach((record, index) => {
    const row = document.createElement("div");
    row.className = "sharedRecordList__row";
    if (hasImageColumn(columns)) row.classList.add("sharedRecordList__row--withImage");
    row.setAttribute("role", "row");
    row.style.gridTemplateColumns = `var(--shared-record-list-columns, ${columnTemplate(columns)})`;
    row.dataset.recordListRow = "true";
    row.dataset.recordListIndex = String(index);
    row.dataset.recordListRecordId = recordId(options, record, index);
    if (isSelectable(options)) {
      row.classList.add("sharedRecordList__row--selectable");
      row.setAttribute("aria-selected", "false");
    }
    columns.forEach((column) => appendCell(row, column, record, index, "cell"));
    rowsNode.appendChild(row);
  });
  syncSelectionState(controller);
}

function actionRecords(list) {
  return list && list.options && Array.isArray(list.options.records) ? list.options.records : [];
}

function actionSelection(list) {
  return list && typeof list.selection === "function" ? list.selection() : null;
}

function actionDisabled(action, selection, records) {
  if (typeof action.disabled === "function" && action.disabled(selection, records)) return true;
  if (action.requiresSelection === false) return false;
  return !selection;
}

function actionTitle(action, selection, records) {
  if (typeof action.title === "function") return normalizeText(action.title(selection, records));
  return normalizeText(action.title);
}

function actionAriaLabel(action, selection, records) {
  if (typeof action.ariaLabel === "function") return normalizeText(action.ariaLabel(selection, records));
  return normalizeText(action.ariaLabel);
}

function renderActions(controller) {
  const { rootNode, options } = controller;
  const actions = Array.isArray(options.actions) ? options.actions : [];
  const records = actionRecords(options.list);
  const selection = actionSelection(options.list);
  clearNode(rootNode);
  rootNode.classList.add("sharedRecordListActions");
  rootNode.dataset.recordListActionsId = controller.id;

  actions.forEach((action) => {
    const key = normalizeText(action && action.key);
    if (!key) return;
    const button = document.createElement("button");
    button.type = "button";
    button.className = ["sharedRecordListActions__button", action.className].filter(Boolean).join(" ");
    button.dataset.recordListAction = key;
    button.disabled = actionDisabled(action, selection, records);
    if (action.appearance) button.dataset.appearance = normalizeText(action.appearance);
    if (action.tone) button.dataset.tone = normalizeText(action.tone);
    const title = actionTitle(action, selection, records);
    if (title) button.title = title;
    const ariaLabel = actionAriaLabel(action, selection, records);
    if (ariaLabel) button.setAttribute("aria-label", ariaLabel);
    button.textContent = normalizeText(action.label || key);
    rootNode.appendChild(button);
  });
}

/** Render a record list. Multiple selection is opt-in; selection() returns one item only.
 * selections() and selection-change payloads expose all selected items in row order.
 */
export function createRecordList(rootNode, options = {}) {
  if (!rootNode) {
    throw new Error("createRecordList requires a root node");
  }

  const controller = {
    id: normalizeText(options.id) || `sharedRecordList-${++recordListId}`,
    rootNode,
    options: { ...options },
    selectedIds: new Set(initialSelectedIds(options, options.records || [])),
    focusedId: "",
    anchorId: "",
    focusBoundaryNodes: new Set(),
    selectionListeners: new Set(),
    selection() {
      return selectionFor(controller);
    },
    selections() {
      return selectionsFor(controller);
    },
    /** Synchronize exact selection IDs without emitting a user selection event. */
    setSelection(ids) {
      const next = new Set(ids);
      if ([...next].sort().join(",") === [...controller.selectedIds].sort().join(",")) return;
      controller.selectedIds = next;
      controller.focusedId = ids[0] || "";
      controller.anchorId = controller.focusedId;
      syncSelectionState(controller);
    },
    /** Keep the first visible row at its current offset through a height change. */
    preserveScrollAnchor(change) {
      const top = rootNode.getBoundingClientRect().top;
      const anchor = [...rootNode.querySelectorAll("[data-record-list-row]")]
        .find(row => row.getBoundingClientRect().bottom > top);
      const before = anchor?.getBoundingClientRect().top;
      change();
      if (anchor?.isConnected) rootNode.scrollTop += anchor.getBoundingClientRect().top - before;
    },
    /** Patch named text cells by exact record ID, preserving rows, images and selection. */
    updateCells(updates) {
      const records = controller.options.records.slice();
      controller.preserveScrollAnchor(() => {
        for (const { id, values } of updates) {
          const index = records.findIndex((record, i) => recordId(controller.options, record, i) === id);
          if (index < 0) throw new Error(`Unknown record list ID: ${id}`);
          const row = rootNode.querySelector(`[data-record-list-index="${index}"]`);
          const record = { ...records[index], ...values };
          for (const key of Object.keys(values)) {
            const column = controller.options.columns.find(item => item.key === key);
            if (!column || (column.type && column.type !== "text")) throw new Error(`Not a text column: ${key}`);
            const cell = [...row.children].find(node => node.dataset.recordListCell === key);
            const text = valueText(columnValue(column, record, index));
            cell.textContent = text;
            if (column.truncate !== false) cell.title = text;
          }
          records[index] = record;
        }
        controller.options.records = records;
      });
    },
    subscribeSelectionChange(listener) {
      if (typeof listener !== "function") return () => {};
      controller.selectionListeners.add(listener);
      return () => controller.selectionListeners.delete(listener);
    },
    addFocusBoundary(node) {
      if (!node || typeof node.contains !== "function") return () => {};
      controller.focusBoundaryNodes.add(node);
      return () => controller.focusBoundaryNodes.delete(node);
    },
    update(nextOptions = {}) {
      controller.options = { ...controller.options, ...nextOptions };
      renderRows(controller, controller.options);
    },
    destroy() {
      rootNode.removeEventListener("click", onClick);
      rootNode.removeEventListener("keydown", onKeyDown);
      document.removeEventListener("pointerdown", onDocumentPointerDown, true);
      document.removeEventListener("focusin", onDocumentFocusIn, true);
      clearNode(rootNode);
      rootNode.classList.remove("sharedRecordList");
      delete rootNode.dataset.recordListId;
      delete rootNode.dataset.recordListSelectedId;
      rootNode.removeAttribute("role");
      rootNode.removeAttribute("aria-multiselectable");
      controller.focusBoundaryNodes.clear();
      controller.selectionListeners.clear();
    }
  };

  function onClick(event) {
    const row = event.target && event.target.closest ? event.target.closest("[data-record-list-row='true']") : null;
    if (!row || !rootNode.contains(row)) return;
    selectRow(controller, row, { focus: true, shiftKey: event.shiftKey, metaKey: event.metaKey, ctrlKey: event.ctrlKey });
  }

  function onKeyDown(event) {
    const row = event.target && event.target.closest ? event.target.closest("[data-record-list-row='true']") : null;
    if (!row || !rootNode.contains(row) || !isSelectable(controller.options)) return;
    const modifiers = { shiftKey: event.shiftKey, metaKey: event.metaKey, ctrlKey: event.ctrlKey };
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      selectRow(controller, row, modifiers);
      return;
    }
    if (event.key === "ArrowDown") {
      event.preventDefault();
      focusRelativeRow(controller, row, 1, modifiers);
      return;
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      focusRelativeRow(controller, row, -1, modifiers);
    }
  }

  function onDocumentPointerDown(event) {
    maybeClearSelectionFromOutsideTarget(controller, event.target);
  }

  function onDocumentFocusIn(event) {
    maybeClearSelectionFromOutsideTarget(controller, event.target);
  }

  rootNode.addEventListener("click", onClick);
  rootNode.addEventListener("keydown", onKeyDown);
  document.addEventListener("pointerdown", onDocumentPointerDown, true);
  document.addEventListener("focusin", onDocumentFocusIn, true);
  controller.update(options);
  return controller;
}

export function createRecordListActions(rootNode, options = {}) {
  if (!rootNode) {
    throw new Error("createRecordListActions requires a root node");
  }

  let unsubscribeSelectionChange = null;
  let unregisterFocusBoundary = null;
  const controller = {
    id: normalizeText(options.id) || `sharedRecordListActions-${++recordListId}`,
    rootNode,
    options: { ...options },
    update(nextOptions = {}) {
      controller.options = { ...controller.options, ...nextOptions };
      if (unsubscribeSelectionChange) {
        unsubscribeSelectionChange();
        unsubscribeSelectionChange = null;
      }
      const list = controller.options.list;
      if (list && typeof list.subscribeSelectionChange === "function") {
        unsubscribeSelectionChange = list.subscribeSelectionChange(() => renderActions(controller));
      }
      if (unregisterFocusBoundary) {
        unregisterFocusBoundary();
        unregisterFocusBoundary = null;
      }
      if (list && typeof list.addFocusBoundary === "function") {
        unregisterFocusBoundary = list.addFocusBoundary(rootNode);
      }
      renderActions(controller);
    },
    destroy() {
      rootNode.removeEventListener("click", onClick);
      if (unsubscribeSelectionChange) {
        unsubscribeSelectionChange();
        unsubscribeSelectionChange = null;
      }
      if (unregisterFocusBoundary) {
        unregisterFocusBoundary();
        unregisterFocusBoundary = null;
      }
      clearNode(rootNode);
      rootNode.classList.remove("sharedRecordListActions");
      delete rootNode.dataset.recordListActionsId;
    }
  };

  function onClick(event) {
    const button = event.target && event.target.closest ? event.target.closest("[data-record-list-action]") : null;
    if (!button || !rootNode.contains(button) || button.disabled) return;
    const actionKey = normalizeText(button.dataset.recordListAction);
    const action = (Array.isArray(controller.options.actions) ? controller.options.actions : [])
      .find((candidate) => normalizeText(candidate && candidate.key) === actionKey);
    if (!action || typeof controller.options.onAction !== "function") return;
    button.focus();
    const records = actionRecords(controller.options.list);
    controller.options.onAction({
      action,
      actionKey,
      selection: actionSelection(controller.options.list),
      records
    });
  }

  rootNode.addEventListener("click", onClick);
  controller.update(options);
  return controller;
}
