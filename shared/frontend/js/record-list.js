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
  empty.textContent = normalizeText(options.emptyText) || "No records.";
  rootNode.appendChild(empty);
}

function renderRows(controller, options) {
  const rootNode = controller.rootNode;
  const records = Array.isArray(options.records) ? options.records : [];
  const columns = Array.isArray(options.columns) ? options.columns : [];
  clearNode(rootNode);
  rootNode.classList.add("sharedRecordList");
  rootNode.dataset.recordListId = controller.id;
  rootNode.setAttribute("role", "table");

  if (!columns.length) {
    renderEmpty(rootNode, { ...options, emptyText: options.emptyText || "No columns." });
    return;
  }

  renderHeader(rootNode, columns, options);

  if (!records.length) {
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
    row.setAttribute("role", "row");
    row.style.gridTemplateColumns = columnTemplate(columns);
    row.dataset.recordListRow = "true";
    row.dataset.recordListIndex = String(index);
    row.dataset.recordListRecordId = recordId(options, record, index);
    columns.forEach((column) => appendCell(row, column, record, index, "cell"));
    rowsNode.appendChild(row);
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
    update(nextOptions = {}) {
      controller.options = { ...controller.options, ...nextOptions };
      renderRows(controller, controller.options);
    },
    destroy() {
      clearNode(rootNode);
      rootNode.classList.remove("sharedRecordList");
      delete rootNode.dataset.recordListId;
      rootNode.removeAttribute("role");
    }
  };

  controller.update(options);
  return controller;
}
