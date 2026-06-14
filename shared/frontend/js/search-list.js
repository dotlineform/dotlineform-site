let searchListId = 0;

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function escapeHtml(value) {
  return String(value == null ? "" : value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function defaultValueForOption(option) {
  if (option && typeof option === "object" && "value" in option) return normalizeText(option.value);
  return normalizeText(option);
}

// Default matching is only a convenience. Consumers with domain-specific
// semantics, such as prefix-only folder lookup, should pass filterOptions.
function defaultFilterOptions(options, query) {
  const q = normalizeText(query).toLowerCase();
  if (!q) return options.slice();
  return options.filter((option) => defaultValueForOption(option).toLowerCase().includes(q));
}

// Row markup belongs to the consumer. Use renderOption for one-column,
// two-column, or richer rows instead of changing this shared fallback.
function defaultRenderOption(option) {
  return `<span class="sharedSearchList__optionText">${escapeHtml(defaultValueForOption(option))}</span>`;
}

function optionClassNames(classNames = {}) {
  return [
    "sharedSearchList__option",
    normalizeText(classNames.option)
  ].filter(Boolean).join(" ");
}

function noResultsHtml(options = {}) {
  if (typeof options.renderNoResults === "function") return options.renderNoResults();
  return `<p class="sharedSearchList__empty">${escapeHtml(options.noResultsText || "No matching results.")}</p>`;
}

function optionValue(options, option) {
  if (typeof options.getOptionValue === "function") return normalizeText(options.getOptionValue(option));
  return defaultValueForOption(option);
}

function visibleOptions(controller, options) {
  const loaded = Array.isArray(controller.loadedOptions) ? controller.loadedOptions : [];
  const filterOptions = typeof options.filterOptions === "function" ? options.filterOptions : defaultFilterOptions;
  const filtered = filterOptions(loaded, controller.inputNode.value);
  const records = Array.isArray(filtered) ? filtered : [];
  const limit = Number.isFinite(options.maxOptions) ? Math.max(0, options.maxOptions) : 12;
  return records.slice(0, limit);
}

function scrollActiveOption(controller) {
  if (!controller || !controller.popupNode || controller.activeIndex < 0) return;
  const activeOption = controller.popupNode.querySelector(`#${controller.optionId(controller.activeIndex)}`);
  if (!activeOption) return;
  const popupStyle = window.getComputedStyle(controller.popupNode);
  const topPadding = parseFloat(popupStyle.paddingTop) || 0;
  const bottomPadding = parseFloat(popupStyle.paddingBottom) || 0;
  const popupRect = controller.popupNode.getBoundingClientRect();
  const optionRect = activeOption.getBoundingClientRect();
  const visibleTop = popupRect.top + topPadding;
  const visibleBottom = popupRect.bottom - bottomPadding;
  if (optionRect.bottom > visibleBottom) {
    controller.popupNode.scrollTop += optionRect.bottom - visibleBottom;
  } else if (optionRect.top < visibleTop) {
    controller.popupNode.scrollTop -= visibleTop - optionRect.top;
  }
}

function renderOptions(controller, options = {}) {
  const inputNode = controller.inputNode;
  const popupNode = controller.popupNode;
  controller.matches = visibleOptions(controller, options);
  if (controller.activeIndex >= controller.matches.length) controller.activeIndex = controller.matches.length - 1;
  if (!controller.matches.length) {
    controller.activeIndex = -1;
    inputNode.removeAttribute("aria-activedescendant");
    popupNode.innerHTML = noResultsHtml(options);
    popupNode.hidden = false;
    return;
  }

  const renderOption = typeof options.renderOption === "function" ? options.renderOption : defaultRenderOption;
  popupNode.innerHTML = controller.matches.map((option, index) => {
    const active = index === controller.activeIndex;
    const value = optionValue(options, option);
    return `
      <button type="button" id="${controller.optionId(index)}" class="${escapeHtml(optionClassNames(options.classNames))}" data-search-list-index="${index}" data-search-list-value="${escapeHtml(value)}" tabindex="-1" role="option" aria-selected="${active ? "true" : "false"}">
        ${renderOption(option, { index, active, value })}
      </button>
    `;
  }).join("");

  if (controller.activeIndex >= 0) {
    inputNode.setAttribute("aria-activedescendant", controller.optionId(controller.activeIndex));
  } else {
    inputNode.removeAttribute("aria-activedescendant");
  }
  popupNode.hidden = false;
  scrollActiveOption(controller);
}

function setActiveIndex(controller, index, options = {}) {
  if (!controller.matches.length) {
    controller.activeIndex = -1;
  } else {
    controller.activeIndex = Math.max(-1, Math.min(index, controller.matches.length - 1));
  }
  renderOptions(controller, options);
}

async function refreshOptions(controller, options = {}) {
  try {
    const loaded = typeof options.loadOptions === "function" ? await options.loadOptions(controller.inputNode.value) : [];
    controller.loadedOptions = Array.isArray(loaded) ? loaded : [];
    renderOptions(controller, options);
  } catch (error) {
    controller.activeIndex = -1;
    controller.inputNode.removeAttribute("aria-activedescendant");
    if (typeof options.renderError === "function") {
      controller.popupNode.innerHTML = options.renderError(error);
    } else {
      controller.popupNode.innerHTML = `<p class="sharedSearchList__empty">${escapeHtml(normalizeText(error && error.message) || "Results could not be loaded.")}</p>`;
    }
    controller.popupNode.hidden = false;
  }
}

function closeSearchList(controller, { reset = false } = {}, options = {}) {
  controller.activeIndex = -1;
  if (reset) {
    controller.inputNode.value = controller.startValue || "";
    if (typeof options.onCancel === "function") options.onCancel({ value: controller.inputNode.value });
  }
  controller.inputNode.removeAttribute("aria-activedescendant");
  controller.popupNode.hidden = true;
}

async function commitOption(controller, option, options = {}) {
  if (option == null) return;
  const value = optionValue(options, option);
  controller.inputNode.value = value;
  controller.startValue = value;
  controller.activeIndex = -1;
  controller.inputNode.removeAttribute("aria-activedescendant");
  controller.popupNode.hidden = true;
  if (typeof options.onCommit === "function") {
    await options.onCommit(option, { value });
  }
}

function commitSelectedOption(controller, option, options = {}) {
  commitOption(controller, option, options).catch((error) => {
    if (typeof options.onCommitError === "function") {
      options.onCommitError(error);
    } else {
      console.warn("search_list: failed to commit option", error);
    }
  });
}

export function bindSearchList(inputNode, popupNode, options = {}) {
  if (!inputNode || !popupNode) {
    throw new Error("bindSearchList requires input and popup nodes");
  }

  const id = normalizeText(options.id) || `sharedSearchList-${++searchListId}`;
  const controller = {
    activeIndex: -1,
    inputNode,
    loadedOptions: [],
    matches: [],
    popupNode,
    startValue: "",
    optionId(index) {
      return `${id}-option-${index}`;
    },
    close(closeOptions = {}) {
      closeSearchList(controller, closeOptions, options);
    },
    refresh() {
      return refreshOptions(controller, options);
    }
  };

  inputNode.setAttribute("aria-autocomplete", "list");
  inputNode.setAttribute("aria-controls", id);
  popupNode.id = id;
  popupNode.setAttribute("role", "listbox");
  popupNode.classList.add("sharedSearchList__popup");
  popupNode.hidden = true;

  function onFocus() {
    controller.startValue = inputNode.value;
    controller.activeIndex = -1;
    inputNode.select();
    refreshOptions(controller, options);
  }

  function onMouseUp(event) {
    if (document.activeElement === inputNode && inputNode.selectionStart === 0 && inputNode.selectionEnd === inputNode.value.length) {
      event.preventDefault();
    }
  }

  function onInput() {
    controller.activeIndex = -1;
    // Typing is not a committed selection. Dirty state and durable form writes
    // should usually happen in onCommit, not onTransientInput.
    if (typeof options.onTransientInput === "function") {
      options.onTransientInput({ value: inputNode.value });
    }
    refreshOptions(controller, options);
  }

  function onKeyDown(event) {
    const matches = controller.matches || [];
    if (event.key === "Escape") {
      event.preventDefault();
      closeSearchList(controller, { reset: true }, options);
      return;
    }
    if (event.key === "ArrowDown") {
      if (!matches.length) return;
      event.preventDefault();
      popupNode.dataset.navigation = "keyboard";
      setActiveIndex(controller, controller.activeIndex < 0 ? 0 : controller.activeIndex + 1, options);
      return;
    }
    if (event.key === "ArrowUp") {
      if (!matches.length) return;
      event.preventDefault();
      popupNode.dataset.navigation = "keyboard";
      setActiveIndex(controller, controller.activeIndex <= 0 ? -1 : controller.activeIndex - 1, options);
      return;
    }
    if (event.key === "Enter") {
      if (!matches.length) return;
      event.preventDefault();
      popupNode.dataset.navigation = "keyboard";
      const index = controller.activeIndex >= 0 ? controller.activeIndex : 0;
      commitSelectedOption(controller, matches[index], options);
    }
  }

  function onPointerMove() {
    popupNode.dataset.navigation = "pointer";
  }

  function onPopupClick(event) {
    const button = event.target && event.target.closest ? event.target.closest("[data-search-list-index]") : null;
    if (!button || !popupNode.contains(button)) return;
    const index = Number(button.getAttribute("data-search-list-index"));
    if (!Number.isInteger(index) || index < 0 || index >= controller.matches.length) return;
    popupNode.dataset.navigation = "pointer";
    commitSelectedOption(controller, controller.matches[index], options);
  }

  function onDocumentClick(event) {
    if (event.target === inputNode || popupNode.contains(event.target)) return;
    closeSearchList(controller, {}, options);
  }

  inputNode.addEventListener("focus", onFocus);
  inputNode.addEventListener("mouseup", onMouseUp);
  inputNode.addEventListener("input", onInput);
  inputNode.addEventListener("keydown", onKeyDown);
  popupNode.addEventListener("mousemove", onPointerMove);
  popupNode.addEventListener("click", onPopupClick);
  document.addEventListener("click", onDocumentClick);

  controller.destroy = function destroy() {
    inputNode.removeEventListener("focus", onFocus);
    inputNode.removeEventListener("mouseup", onMouseUp);
    inputNode.removeEventListener("input", onInput);
    inputNode.removeEventListener("keydown", onKeyDown);
    popupNode.removeEventListener("mousemove", onPointerMove);
    popupNode.removeEventListener("click", onPopupClick);
    document.removeEventListener("click", onDocumentClick);
  };

  return controller;
}
