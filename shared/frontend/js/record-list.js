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

function columnValue(column, record, index) {
  if (typeof column.value === "function") return column.value(record, { index, column });
  return record && column.key ? record[column.key] : "";
}

function recordId(options, record, index) {
  if (typeof options.getRecordId === "function") return normalizeText(options.getRecordId(record, index));
  if (record && record.id != null) return normalizeText(record.id);
  return String(index);
}

function isSelectable(options = {}) {
  return options.selectionMode === "single";
}

function initialSelectedId(options, records) {
  const initial = options.initialSelection;
  if (initial == null) return "";
  if (Number.isInteger(initial) && initial >= 0 && initial < records.length) {
    return recordId(options, records[initial], initial);
  }
  const initialId = normalizeText(initial);
  const match = records.find((record, index) => recordId(options, record, index) === initialId);
  return match ? initialId : "";
}

function clearNode(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function setText(node, value) {
  node.textContent = valueText(value);
}

function appendCell(rowNode, column, record, index, role) {
  const cell = document.createElement("div");
  cell.className = ["sharedRecordList__cell", column.className].filter(Boolean).join(" ");
  cell.setAttribute("role", role);
  cell.dataset.recordListCell = column.key || String(index);

  const rawValue = columnValue(column, record, index);
  const text = valueText(rawValue);
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
  const count = Math.max(1, columns.length);
  return `repeat(${count}, minmax(0, 1fr))`;
}

function renderHeader(rootNode, columns, options) {
  if (options.showHeader === false) return;
  const header = document.createElement("div");
  header.className = "sharedRecordList__header";
  header.setAttribute("role", "row");
  header.style.gridTemplateColumns = columnTemplate(columns);
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

function selectionFor(controller) {
  const records = Array.isArray(controller.options.records) ? controller.options.records : [];
  const selectedId = normalizeText(controller.selectedId);
  if (!selectedId) return null;
  const index = records.findIndex((record, recordIndex) => recordId(controller.options, record, recordIndex) === selectedId);
  if (index < 0) return null;
  return {
    id: selectedId,
    index,
    record: records[index]
  };
}

function selectedRowIndex(controller) {
  const selection = selectionFor(controller);
  return selection ? selection.index : -1;
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
  const selectedId = normalizeText(controller.selectedId);
  let selectedStillExists = !selectedId;
  rows.forEach((row) => {
    const selected = Boolean(selectedId && row.dataset.recordListRecordId === selectedId);
    if (selected) selectedStillExists = true;
    row.classList.toggle("sharedRecordList__row--selected", selected);
    row.setAttribute("aria-selected", selected ? "true" : "false");
  });
  if (!selectedStillExists) controller.selectedId = "";
  controller.rootNode.dataset.recordListSelectedId = controller.selectedId || "";
  setRovingTabIndex(controller);
}

function emitSelectionChange(controller) {
  const records = Array.isArray(controller.options.records) ? controller.options.records : [];
  const payload = {
    selection: selectionFor(controller),
    records
  };
  if (typeof controller.options.onSelectionChange === "function") {
    controller.options.onSelectionChange(payload);
  }
  controller.selectionListeners.forEach((listener) => listener(payload));
}

function selectRow(controller, row, { focus = false, emit = true } = {}) {
  if (!row || !isSelectable(controller.options)) return;
  controller.selectedId = normalizeText(row.dataset.recordListRecordId);
  syncSelectionState(controller);
  if (focus) row.focus();
  if (emit) emitSelectionChange(controller);
}

function clearSelection(controller, { emit = true } = {}) {
  if (!controller.selectedId) return;
  controller.selectedId = "";
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

function focusRelativeRow(controller, row, offset) {
  if (!row || !isSelectable(controller.options)) return;
  const rows = [...controller.rootNode.querySelectorAll("[data-record-list-row='true']")];
  const currentIndex = rows.indexOf(row);
  if (currentIndex < 0) return;
  const nextIndex = Math.max(0, Math.min(rows.length - 1, currentIndex + offset));
  selectRow(controller, rows[nextIndex], { focus: true });
}

function renderRows(controller, options) {
  const rootNode = controller.rootNode;
  const records = Array.isArray(options.records) ? options.records : [];
  const columns = Array.isArray(options.columns) ? options.columns : [];
  clearNode(rootNode);
  rootNode.classList.add("sharedRecordList");
  rootNode.dataset.recordListId = controller.id;
  rootNode.setAttribute("role", isSelectable(options) ? "grid" : "table");
  if (isSelectable(options)) rootNode.setAttribute("aria-multiselectable", "false");
  else rootNode.removeAttribute("aria-multiselectable");
  const selectedBackground = normalizeText(options.selectedBackground);
  if (selectedBackground) rootNode.style.setProperty("--shared-record-list-selected-bg", selectedBackground);
  else rootNode.style.removeProperty("--shared-record-list-selected-bg");

  if (!columns.length) {
    controller.selectedId = "";
    rootNode.dataset.recordListSelectedId = "";
    renderEmpty(rootNode, { ...options, emptyText: options.emptyText || "No columns." });
    return;
  }

  renderHeader(rootNode, columns, options);

  if (!records.length) {
    controller.selectedId = "";
    rootNode.dataset.recordListSelectedId = "";
    renderEmpty(rootNode, options);
    return;
  }

  if (!controller.selectedId) controller.selectedId = initialSelectedId(options, records);

  const rowsNode = document.createElement("div");
  rowsNode.className = "sharedRecordList__rows";
  rowsNode.setAttribute("role", "rowgroup");
  rootNode.appendChild(rowsNode);

  records.forEach((record, index) => {
    const row = document.createElement("div");
    row.className = "sharedRecordList__row";
    row.setAttribute("role", "row");
    row.style.gridTemplateColumns = columnTemplate(columns);
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

export function createRecordList(rootNode, options = {}) {
  if (!rootNode) {
    throw new Error("createRecordList requires a root node");
  }

  const controller = {
    id: normalizeText(options.id) || `sharedRecordList-${++recordListId}`,
    rootNode,
    options: { ...options },
    selectedId: "",
    focusBoundaryNodes: new Set(),
    selectionListeners: new Set(),
    selection() {
      return selectionFor(controller);
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
    selectRow(controller, row, { focus: true });
  }

  function onKeyDown(event) {
    const row = event.target && event.target.closest ? event.target.closest("[data-record-list-row='true']") : null;
    if (!row || !rootNode.contains(row) || !isSelectable(controller.options)) return;
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      selectRow(controller, row);
      return;
    }
    if (event.key === "ArrowDown") {
      event.preventDefault();
      focusRelativeRow(controller, row, 1);
      return;
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      focusRelativeRow(controller, row, -1);
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
