let selectableListId = 0;

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function clearNode(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function itemId(options, item, index) {
  if (typeof options.getId === "function") return normalizeText(options.getId(item, index));
  if (item && item.id != null) return normalizeText(item.id);
  return String(index);
}

function itemLabel(options, item, index) {
  if (typeof options.getLabel === "function") return normalizeText(options.getLabel(item, index));
  return normalizeText(item && item.label);
}

function itemMeta(options, item, index) {
  const meta = typeof options.getMeta === "function" ? options.getMeta(item, index) : item && item.meta;
  if (Array.isArray(meta)) return meta.map(normalizeText).filter(Boolean);
  const text = normalizeText(meta);
  return text ? [text] : [];
}

function itemDisabled(options, item, index) {
  if (typeof options.isDisabled === "function") return Boolean(options.isDisabled(item, index));
  return Boolean(item && item.disabled);
}

function itemParentId(options, item, index) {
  if (typeof options.getParentId === "function") return normalizeText(options.getParentId(item, index));
  return normalizeText(item && item.parentId);
}

function itemIndent(options, item, index) {
  if (typeof options.getIndent === "function") return normalizeText(options.getIndent(item, index));
  return normalizeText(item && item.indent);
}

function itemSelectedIds(options) {
  const selectedIds = options.selectedIds;
  if (selectedIds instanceof Set) return new Set([...selectedIds].map(normalizeText).filter(Boolean));
  if (Array.isArray(selectedIds)) return new Set(selectedIds.map(normalizeText).filter(Boolean));
  return new Set();
}

function items(controller) {
  return Array.isArray(controller.options.items) ? controller.options.items : [];
}

function treeEnabled(options) {
  return Boolean(options.tree || typeof options.getParentId === "function");
}

function buildTreeState(controller) {
  const options = controller.options;
  const entries = items(controller)
    .map((item, index) => ({ item, index, id: itemId(options, item, index), parentId: itemParentId(options, item, index) }))
    .filter((entry) => entry.id);
  const idSet = new Set(entries.map((entry) => entry.id));
  const byId = new Map(entries.map((entry) => [entry.id, entry]));
  const childrenByParent = new Map();
  entries.forEach((entry) => {
    entry.effectiveParentId = entry.parentId && idSet.has(entry.parentId) ? entry.parentId : "";
    if (!childrenByParent.has(entry.effectiveParentId)) childrenByParent.set(entry.effectiveParentId, []);
    childrenByParent.get(entry.effectiveParentId).push(entry);
  });

  const depthById = new Map();
  const orderedEntries = [];
  const visit = (parentId, depth) => {
    (childrenByParent.get(parentId) || []).forEach((entry) => {
      if (depthById.has(entry.id)) return;
      depthById.set(entry.id, depth);
      orderedEntries.push(entry);
      visit(entry.id, depth + 1);
    });
  };
  visit("", 0);
  entries.forEach((entry) => {
    if (!depthById.has(entry.id)) {
      depthById.set(entry.id, 0);
      orderedEntries.push(entry);
    }
    entry.depth = depthById.get(entry.id) || 0;
    entry.hasChildren = (childrenByParent.get(entry.id) || []).length > 0;
  });

  const hiddenByCollapse = (entry) => {
    const seen = new Set();
    let parentId = entry.effectiveParentId;
    while (parentId) {
      if (seen.has(parentId)) return false;
      seen.add(parentId);
      if (controller.collapsedIds.has(parentId)) return true;
      const parent = byId.get(parentId);
      parentId = parent ? parent.effectiveParentId : "";
    }
    return false;
  };
  const visibleEntries = treeEnabled(options)
    ? orderedEntries.filter((entry) => !hiddenByCollapse(entry))
    : entries;

  return { entries, visibleEntries, byId, childrenByParent };
}

function descendantsForTree(treeState, id) {
  const ids = [];
  const visit = (parentId) => {
    (treeState.childrenByParent.get(parentId) || []).forEach((entry) => {
      ids.push(entry.id);
      visit(entry.id);
    });
  };
  visit(id);
  return ids;
}

function selectedItems(controller) {
  const selectedIds = controller.selectedIds;
  return items(controller).filter((item, index) => selectedIds.has(itemId(controller.options, item, index)));
}

function enabledVisibleIds(controller) {
  if (typeof controller.options.getSelectAllIds === "function") {
    const ids = controller.options.getSelectAllIds({ items: items(controller) });
    if (ids instanceof Set || Array.isArray(ids)) return [...ids].map(normalizeText).filter(Boolean);
  }
  return buildTreeState(controller).entries
    .filter(({ item, index, id }) => id && !itemDisabled(controller.options, item, index))
    .map(({ id }) => id);
}

function emitSelectionChange(controller) {
  const payload = {
    selectedIds: Array.from(controller.selectedIds),
    selectedItems: selectedItems(controller)
  };
  if (typeof controller.options.onSelectionChange === "function") {
    controller.options.onSelectionChange(payload);
  }
  controller.selectionListeners.forEach((listener) => listener(payload));
}

function syncSummary(controller) {
  const node = controller.options.summaryNode;
  if (!node) return;
  const count = controller.selectedIds.size;
  if (typeof controller.options.renderSummary === "function") {
    node.textContent = normalizeText(controller.options.renderSummary({ count, selectedIds: Array.from(controller.selectedIds) }));
    return;
  }
  node.textContent = count ? `${count} selected.` : "";
}

function syncButtons(controller) {
  const disabled = Boolean(controller.options.disabled);
  const hasItems = enabledVisibleIds(controller).length > 0;
  if (controller.options.selectAllButton) {
    controller.options.selectAllButton.disabled = disabled || !hasItems;
  }
  if (controller.options.clearButton) {
    controller.options.clearButton.disabled = disabled || controller.selectedIds.size === 0;
  }
}

function syncRows(controller) {
  const rows = [...controller.rootNode.querySelectorAll("[data-selectable-list-row='true']")];
  const treeState = buildTreeState(controller);
  rows.forEach((row) => {
    const id = normalizeText(row.dataset.selectableListItemId);
    const selected = Boolean(id && controller.selectedIds.has(id));
    const selectedDescendantCount = descendantsForTree(treeState, id)
      .filter((descendantId) => controller.selectedIds.has(descendantId)).length;
    row.dataset.selected = selected ? "true" : "false";
    if (controller.options.readOnly) {
      row.removeAttribute("aria-selected");
    } else {
      row.setAttribute("aria-selected", selected ? "true" : "false");
    }
    const checkbox = row.querySelector("[data-selectable-list-checkbox='true']");
    if (checkbox instanceof HTMLInputElement) {
      checkbox.checked = selected;
      checkbox.indeterminate = !selected && selectedDescendantCount > 0;
    }
  });
  syncSummary(controller);
  syncButtons(controller);
}

function setSelection(controller, selectedIds, { emit = true } = {}) {
  controller.selectedIds = new Set([...selectedIds].map(normalizeText).filter(Boolean));
  syncRows(controller);
  if (emit) emitSelectionChange(controller);
}

function applyItemSelection(controller, item, index, checked) {
  const id = itemId(controller.options, item, index);
  if (!id || itemDisabled(controller.options, item, index)) return;
  const nextSelectedIds = new Set(controller.selectedIds);
  const treeState = buildTreeState(controller);
  const affectedIds = controller.options.cascadeSelection && controller.options.selectionMode !== "single"
    ? [
        id,
        ...descendantsForTree(treeState, id).filter((descendantId) => {
          const entry = treeState.byId.get(descendantId);
          return entry && !itemDisabled(controller.options, entry.item, entry.index);
        })
      ]
    : [id];
  if (controller.options.selectionMode === "single") {
    nextSelectedIds.clear();
    if (checked) nextSelectedIds.add(id);
  } else if (checked) {
    affectedIds.forEach((affectedId) => nextSelectedIds.add(affectedId));
  } else {
    affectedIds.forEach((affectedId) => nextSelectedIds.delete(affectedId));
  }
  if (typeof controller.options.resolveSelectionChange === "function") {
    const resolved = controller.options.resolveSelectionChange({
      item,
      index,
      id,
      checked,
      selectedIds: nextSelectedIds,
      previousSelectedIds: new Set(controller.selectedIds),
      items: items(controller)
    });
    if (resolved instanceof Set || Array.isArray(resolved)) {
      setSelection(controller, resolved);
      return;
    }
  }
  setSelection(controller, nextSelectedIds);
}

function renderStatus(rootNode, className, text, state) {
  const status = document.createElement("p");
  status.className = className;
  status.dataset.state = state;
  status.textContent = normalizeText(text);
  rootNode.appendChild(status);
}

function renderRows(controller) {
  const { rootNode, options } = controller;
  const currentItems = items(controller);
  const currentTreeState = buildTreeState(controller);
  controller.collapsedIds.forEach((id) => {
    const entry = currentTreeState.byId.get(id);
    if (!entry || !entry.hasChildren) controller.collapsedIds.delete(id);
  });
  clearNode(rootNode);
  rootNode.classList.add("sharedSelectableList");
  rootNode.dataset.selectableListId = controller.id;
  rootNode.dataset.selectionMode = normalizeText(options.selectionMode) || "multiple";
  rootNode.dataset.state = options.constructing ? "constructing" : (currentItems.length ? "ready" : "empty");
  rootNode.dataset.readOnly = options.readOnly ? "true" : "false";
  rootNode.setAttribute("role", "listbox");
  rootNode.setAttribute("aria-multiselectable", options.selectionMode === "single" ? "false" : "true");
  if (options.readOnly) {
    rootNode.setAttribute("role", "list");
    rootNode.removeAttribute("aria-multiselectable");
  }

  if (options.constructing) {
    renderStatus(rootNode, "sharedSelectableList__status", options.constructingMessage || "Building list...", "constructing");
    syncSummary(controller);
    syncButtons(controller);
    return;
  }

  if (!currentItems.length) {
    renderStatus(rootNode, "sharedSelectableList__empty", options.emptyMessage || "", "empty");
    syncSummary(controller);
    syncButtons(controller);
    return;
  }

  const rowsNode = document.createElement("ul");
  rowsNode.className = "sharedSelectableList__rows";
  rowsNode.setAttribute("role", "presentation");
  rootNode.appendChild(rowsNode);

  currentTreeState.visibleEntries.forEach((entry) => {
    const { item, index, id } = entry;
    const disabled = itemDisabled(options, item, index);
    const row = document.createElement("li");
    row.className = "sharedSelectableList__row";
    row.dataset.selectableListRow = "true";
    row.dataset.selectableListItemId = id;
    row.dataset.disabled = disabled ? "true" : "false";
    row.setAttribute("role", "option");
    row.setAttribute("aria-disabled", disabled ? "true" : "false");
    row.setAttribute("aria-selected", "false");
    if (options.readOnly) {
      row.setAttribute("role", "listitem");
      row.removeAttribute("aria-selected");
    }
    const indent = treeEnabled(options)
      ? `${((entry.depth || 0) * Number(options.treeIndentRem || 1.35)).toFixed(2)}rem`
      : itemIndent(options, item, index);
    if (indent) {
      row.style.setProperty("--shared-selectable-list-indent", indent);
      row.style.marginInlineStart = indent;
    }

    if (treeEnabled(options) && typeof options.renderLeading !== "function") {
      const toggle = document.createElement(entry.hasChildren ? "button" : "span");
      toggle.className = entry.hasChildren ? "sharedSelectableList__toggle" : "sharedSelectableList__toggleSpacer";
      if (entry.hasChildren) {
        const expanded = !controller.collapsedIds.has(id);
        toggle.type = "button";
        toggle.dataset.selectableListToggle = id;
        toggle.setAttribute("aria-expanded", expanded ? "true" : "false");
        toggle.setAttribute("aria-label", expanded
          ? (normalizeText(options.collapseLabel) || "Collapse section")
          : (normalizeText(options.expandLabel) || "Expand section"));
        toggle.textContent = expanded ? "▼" : "▶";
      } else {
        toggle.setAttribute("aria-hidden", "true");
      }
      row.appendChild(toggle);
    } else if (typeof options.renderLeading === "function") {
      const leading = options.renderLeading({ item, index, id });
      if (leading instanceof Node) {
        if (leading.classList && typeof leading.classList.add === "function") {
          leading.classList.add("sharedSelectableList__leading");
        }
        row.appendChild(leading);
      }
    }

    const label = document.createElement(options.readOnly ? "div" : "label");
    label.className = "sharedSelectableList__label";
    if (!options.readOnly) {
      const checkbox = document.createElement("input");
      checkbox.className = "sharedSelectableList__checkbox";
      checkbox.type = "checkbox";
      checkbox.value = id;
      checkbox.disabled = disabled;
      checkbox.dataset.selectableListCheckbox = "true";
      label.appendChild(checkbox);
    }

    const text = document.createElement("span");
    text.className = "sharedSelectableList__title";
    text.textContent = itemLabel(options, item, index);
    label.appendChild(text);

    const meta = itemMeta(options, item, index);
    if (meta.length) {
      const metaNode = document.createElement("span");
      metaNode.className = "sharedSelectableList__meta";
      metaNode.textContent = meta.join(" ");
      label.appendChild(metaNode);
    }

    row.appendChild(label);
    rowsNode.appendChild(row);
  });
  syncRows(controller);
}

export function createSelectableList(rootNode, options = {}) {
  if (!rootNode) {
    throw new Error("createSelectableList requires a root node");
  }

  const controller = {
    id: normalizeText(options.id) || `sharedSelectableList-${++selectableListId}`,
    rootNode,
    options: { selectionMode: "multiple", ...options },
    selectedIds: itemSelectedIds(options),
    collapsedIds: new Set(),
    selectionListeners: new Set(),
    selection() {
      return {
        selectedIds: Array.from(controller.selectedIds),
        selectedItems: selectedItems(controller)
      };
    },
    subscribeSelectionChange(listener) {
      if (typeof listener !== "function") return () => {};
      controller.selectionListeners.add(listener);
      return () => controller.selectionListeners.delete(listener);
    },
    update(nextOptions = {}) {
      controller.options = { ...controller.options, ...nextOptions };
      if (Object.prototype.hasOwnProperty.call(nextOptions, "selectedIds")) {
        controller.selectedIds = itemSelectedIds(controller.options);
      }
      renderRows(controller);
    },
    setSelectedIds(selectedIds, options = {}) {
      setSelection(controller, selectedIds, { emit: options.emit !== false });
    },
    selectAll() {
      setSelection(controller, enabledVisibleIds(controller));
    },
    clearSelection() {
      setSelection(controller, []);
    },
    destroy() {
      rootNode.removeEventListener("change", onChange);
      rootNode.removeEventListener("click", onClick);
      if (controller.options.selectAllButton) controller.options.selectAllButton.removeEventListener("click", onSelectAll);
      if (controller.options.clearButton) controller.options.clearButton.removeEventListener("click", onClear);
      clearNode(rootNode);
      rootNode.classList.remove("sharedSelectableList");
      delete rootNode.dataset.selectableListId;
      delete rootNode.dataset.selectionMode;
      delete rootNode.dataset.state;
      delete rootNode.dataset.readOnly;
      rootNode.removeAttribute("role");
      rootNode.removeAttribute("aria-multiselectable");
      controller.selectionListeners.clear();
    }
  };

  function onChange(event) {
    const target = event.target;
    if (!(target instanceof HTMLInputElement) || target.dataset.selectableListCheckbox !== "true") return;
    const row = target.closest("[data-selectable-list-row='true']");
    if (!row || !rootNode.contains(row)) return;
    const id = normalizeText(row.dataset.selectableListItemId);
    const index = items(controller).findIndex((item, itemIndex) => itemId(controller.options, item, itemIndex) === id);
    if (index < 0) return;
    applyItemSelection(controller, items(controller)[index], index, target.checked);
  }

  function onClick(event) {
    const target = event.target;
    const button = target instanceof Element ? target.closest("[data-selectable-list-toggle]") : null;
    if (!(button instanceof HTMLButtonElement) || !rootNode.contains(button)) return;
    event.preventDefault();
    event.stopPropagation();
    const id = normalizeText(button.dataset.selectableListToggle);
    if (!id) return;
    if (controller.collapsedIds.has(id)) controller.collapsedIds.delete(id);
    else controller.collapsedIds.add(id);
    renderRows(controller);
  }

  function onSelectAll() {
    controller.selectAll();
  }

  function onClear() {
    controller.clearSelection();
  }

  rootNode.addEventListener("change", onChange);
  rootNode.addEventListener("click", onClick);
  if (options.selectAllButton) options.selectAllButton.addEventListener("click", onSelectAll);
  if (options.clearButton) options.clearButton.addEventListener("click", onClear);
  controller.update(options);
  return controller;
}
