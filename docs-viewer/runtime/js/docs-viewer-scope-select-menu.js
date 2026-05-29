import {
  escapeHtml
} from "./docs-viewer-render.js";

function scopeSelectMenuRefs(scopeSelect) {
  if (!scopeSelect || typeof scopeSelect.closest !== "function") return null;
  var field = scopeSelect.closest(".docsViewer__scopeField");
  if (!field) return null;
  var menu = field.querySelector("[data-docs-viewer-scope-select-menu]");
  if (!menu) return null;
  return {
    menu: menu,
    button: menu.querySelector("#docsViewerScopeSelectButton"),
    list: menu.querySelector("#docsViewerScopeSelectList"),
    emoji: menu.querySelector(".docsViewer__scopeSelectEmoji"),
    label: menu.querySelector(".docsViewer__scopeSelectText")
  };
}

function visibleScopeMenuItems(list) {
  return Array.from(list.querySelectorAll("[data-docs-viewer-scope-option]")).filter(function (item) {
    return !item.hidden && !item.disabled;
  });
}

function optionAriaLabel(record) {
  return "Docs scope: " + record.label + (record.meta ? ", " + record.meta : "");
}

function renderOption(record) {
  var label = optionAriaLabel(record);
  return (
    '<button class="docsViewer__scopeSelectOption" type="button" role="option" data-docs-viewer-scope-option data-value="' + escapeHtml(record.value) + '" aria-selected="false" aria-label="' + escapeHtml(label) + '" title="' + escapeHtml(label) + '">' +
      '<span class="docsViewer__scopeSelectEmoji" aria-hidden="true">' + escapeHtml(record.emoji) + "</span>" +
      '<span class="docsViewer__scopeSelectOptionLabel">' + escapeHtml(record.label) + "</span>" +
      '<span class="docsViewer__scopeSelectMeta">' + escapeHtml(record.meta) + "</span>" +
    "</button>"
  );
}

export function createDocsViewerScopeSelectMenu(options) {
  var settings = options || {};
  var scopeSelect = settings.scopeSelect || null;
  var windowRef = settings.window || window;
  var documentRef = settings.document || document;
  var records = [];

  function refs() {
    return scopeSelectMenuRefs(scopeSelect);
  }

  function close(options) {
    var closeSettings = options || {};
    var currentRefs = refs();
    if (!currentRefs || !currentRefs.list || !currentRefs.button) return;
    currentRefs.list.hidden = true;
    currentRefs.button.setAttribute("aria-expanded", "false");
    if (closeSettings.restoreFocus && typeof currentRefs.button.focus === "function") {
      currentRefs.button.focus({ preventScroll: true });
    }
  }

  function open(focusTarget) {
    var currentRefs = refs();
    if (!currentRefs || !currentRefs.list || !currentRefs.button || currentRefs.button.disabled) return;
    currentRefs.list.hidden = false;
    currentRefs.button.setAttribute("aria-expanded", "true");
    var items = visibleScopeMenuItems(currentRefs.list);
    var target = items.find(function (item) {
      return item.getAttribute("aria-selected") === "true";
    });
    if (focusTarget === "first") target = items[0];
    if (focusTarget === "last") target = items[items.length - 1];
    if (target && typeof target.focus === "function") target.focus();
  }

  function project() {
    var currentRefs = refs();
    if (!currentRefs || !currentRefs.button || !currentRefs.list) return;
    var selectedValue = String(scopeSelect && scopeSelect.value || "").trim().toLowerCase();
    var selected = records.find(function (record) {
      return record.value === selectedValue;
    }) || records[0] || null;
    if (currentRefs.emoji) currentRefs.emoji.textContent = selected ? selected.emoji : "";
    if (currentRefs.label) currentRefs.label.textContent = selected ? selected.label : "";
    var buttonLabel = selected ? optionAriaLabel(selected) : "Docs scope";
    currentRefs.button.setAttribute("aria-label", buttonLabel);
    currentRefs.button.title = buttonLabel;
    currentRefs.list.querySelectorAll("[data-docs-viewer-scope-option]").forEach(function (item) {
      item.setAttribute("aria-selected", item.dataset.value === selectedValue ? "true" : "false");
    });
  }

  function selectOption(option) {
    if (!scopeSelect || !option || option.disabled) return;
    var value = String(option.dataset.value || "").trim().toLowerCase();
    if (!value) return;
    scopeSelect.value = value;
    project();
    close({ restoreFocus: true });
    scopeSelect.dispatchEvent(new windowRef.Event("change", { bubbles: true }));
  }

  function bind() {
    var currentRefs = refs();
    if (!currentRefs || !currentRefs.menu || !currentRefs.button || !currentRefs.list || currentRefs.menu.dataset.docsViewerScopeSelectBound === "true") return;
    currentRefs.menu.dataset.docsViewerScopeSelectBound = "true";

    currentRefs.button.addEventListener("click", function () {
      if (currentRefs.list.hidden) {
        open();
      } else {
        close();
      }
    });
    currentRefs.button.addEventListener("keydown", function (event) {
      if (event.key === "ArrowDown") {
        event.preventDefault();
        open("first");
      }
      if (event.key === "ArrowUp") {
        event.preventDefault();
        open("last");
      }
      if (event.key === "Escape") {
        close();
      }
    });
    currentRefs.list.addEventListener("click", function (event) {
      var option = event.target instanceof windowRef.Element ? event.target.closest("[data-docs-viewer-scope-option]") : null;
      selectOption(option);
    });
    currentRefs.list.addEventListener("keydown", function (event) {
      var items = visibleScopeMenuItems(currentRefs.list);
      var index = items.indexOf(documentRef.activeElement);
      if (event.key === "Escape") {
        event.preventDefault();
        close({ restoreFocus: true });
        return;
      }
      if (event.key === "ArrowDown" || event.key === "ArrowUp") {
        event.preventDefault();
        if (!items.length) return;
        var direction = event.key === "ArrowDown" ? 1 : -1;
        var nextIndex = index < 0 ? 0 : (index + direction + items.length) % items.length;
        if (items[nextIndex] && typeof items[nextIndex].focus === "function") items[nextIndex].focus();
        return;
      }
      if (event.key === "Home" || event.key === "End") {
        event.preventDefault();
        if (!items.length) return;
        var target = event.key === "Home" ? items[0] : items[items.length - 1];
        if (target && typeof target.focus === "function") target.focus();
        return;
      }
      if (event.key === "Enter" || event.key === " ") {
        var active = documentRef.activeElement;
        if (active && active.matches("[data-docs-viewer-scope-option]")) {
          event.preventDefault();
          selectOption(active);
        }
      }
    });
    documentRef.addEventListener("click", function (event) {
      if (currentRefs.list.hidden || currentRefs.menu.contains(event.target)) return;
      close();
    });
    documentRef.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && !currentRefs.list.hidden) close({ restoreFocus: true });
    });
    windowRef.addEventListener("scroll", function () {
      close();
    }, { passive: true });
    windowRef.addEventListener("resize", function () {
      close();
    });
  }

  function render(nextRecords) {
    records = Array.isArray(nextRecords) ? nextRecords.slice() : [];
    bind();
    var currentRefs = refs();
    if (!currentRefs || !currentRefs.list) return;
    currentRefs.list.innerHTML = records.map(renderOption).join("");
    project();
  }

  return {
    close: close,
    project: project,
    render: render
  };
}
