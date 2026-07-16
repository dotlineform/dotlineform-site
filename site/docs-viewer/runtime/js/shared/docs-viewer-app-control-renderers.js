function appViewerConfigMount(root) {
  return root && typeof root.closest === "function"
    ? root.closest("[data-docs-viewer-header-controls-mount]")
    : null;
}

function renderRecentButton(context) {
  var control = context.control;
  var button = context.existingRoot;
  if (!button || button.tagName !== "BUTTON") {
    button = context.document.createElement("button");
    button.className = "docsViewer__actionButton docsViewer__recentButton";
    button.type = "button";
    button.id = "docsViewerRecentButton";
    button.setAttribute("aria-pressed", "false");
  }
  button.textContent = control.state && control.state.label || control.label;
  return button;
}

function renderSearchInput(context) {
  var control = context.control;
  var wrap = context.existingRoot;
  var input = wrap ? wrap.querySelector("#docsViewerSearchInput") : null;
  if (!wrap || !input) {
    var configMount = appViewerConfigMount(context.mount);
    var ariaLabel = String(configMount && configMount.dataset.searchAriaLabel || control.label || "Search docs");
    var placeholder = String(configMount && configMount.dataset.searchPlaceholder || "search docs");

    wrap = context.document.createElement("div");
    wrap.className = "docsViewer__search";

    var label = context.document.createElement("label");
    label.className = "visually-hidden";
    label.setAttribute("for", "docsViewerSearchInput");
    label.textContent = ariaLabel;

    input = context.document.createElement("input");
    input.className = "docsViewer__searchInput";
    input.id = "docsViewerSearchInput";
    input.type = "search";
    input.autocomplete = "off";
    input.spellcheck = false;
    input.placeholder = placeholder;
    input.setAttribute("aria-label", ariaLabel);

    wrap.append(label, input);
  }
  return { root: wrap, interactive: input };
}

function renderIndexViewToggle(context) {
  var control = context.control;
  var group = context.existingRoot;
  var button = group ? group.querySelector("#docsViewerIndexViewToggle") : null;
  if (!group || !button) {
    group = context.document.createElement("div");
    group.className = "docsViewer__panelControls";
    group.id = "docsViewerPanelControls";
    group.setAttribute("role", "group");
    group.setAttribute("aria-label", "Panel controls");

    button = context.document.createElement("button");
    button.className = "docsViewer__indexViewToggle";
    button.type = "button";
    button.id = "docsViewerIndexViewToggle";
    group.appendChild(button);
  }
  var label = control.state && control.state.label || control.label;
  button.textContent = label === "Graph index view" ? "🕸️" : "📁";
  return { root: group, interactive: button };
}

function renderBookmarkToggle(context) {
  var control = context.control;
  var button = context.existingRoot;
  if (!button || button.tagName !== "BUTTON") {
    button = context.document.createElement("button");
    button.className = "docsViewer__bookmarkToggle";
    button.id = "docsViewerBookmarkToggle";
    button.type = "button";
    button.setAttribute("aria-pressed", "false");
  }
  var active = Boolean(control.state && control.state.pressed);
  button.classList.toggle("is-active", active);
  button.textContent = active ? "★" : "☆";
  return button;
}

function renderInfoToggle(context) {
  var control = context.control;
  var button = context.existingRoot;
  if (!button || button.tagName !== "BUTTON") {
    button = context.document.createElement("button");
    button.className = "docsViewer__infoToggle";
    button.id = "docsViewerInfoToggle";
    button.type = "button";
    button.textContent = "i";
    button.setAttribute("aria-expanded", "false");
  }
  button.classList.toggle("is-active", Boolean(control.state && control.state.expanded));
  return button;
}

export function createDocsViewerSharedControlRenderers() {
  return {
    "recent-button": renderRecentButton,
    "search-input": renderSearchInput,
    "index-view-toggle": renderIndexViewToggle,
    "bookmark-toggle": renderBookmarkToggle,
    "info-toggle": renderInfoToggle
  };
}
