import { createDocsViewerToolbarIcon } from "./docs-viewer-toolbar-icon.js";

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
    button.className = "docsViewer__toolbarIconButton docsViewer__recentButton";
    button.type = "button";
    button.id = "docsViewerRecentButton";
    button.setAttribute("aria-pressed", "false");
  }
  button.replaceChildren(createDocsViewerToolbarIcon(context.document, "docsViewer__icon--clock-9"));
  button.classList.toggle("is-active", Boolean(control.state && control.state.pressed));
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

function renderBookmarkToggle(context) {
  var control = context.control;
  var button = context.existingRoot;
  if (!button || button.tagName !== "BUTTON") {
    button = context.document.createElement("button");
    button.className = "docsViewer__toolbarIconButton";
    button.id = "docsViewerBookmarkToggle";
    button.type = "button";
    button.setAttribute("aria-pressed", "false");
  }
  var active = Boolean(control.state && control.state.pressed);
  button.classList.toggle("is-active", active);
  button.replaceChildren(createDocsViewerToolbarIcon(context.document,
    active ? "docsViewer__icon--bookmark-filled" : "docsViewer__icon--bookmark"));
  return button;
}

function renderInfoToggle(context) {
  var button = context.existingRoot;
  if (!button || button.tagName !== "BUTTON") {
    button = context.document.createElement("button");
    button.className = "docsViewer__toolbarIconButton";
    button.id = "docsViewerInfoToggle";
    button.type = "button";
    button.appendChild(createDocsViewerToolbarIcon(context.document, "docsViewer__icon--info"));
    button.setAttribute("aria-expanded", "false");
  }
  return button;
}

function renderContentDetailBack(context) {
  var button = context.existingRoot;
  if (!button || button.tagName !== "BUTTON") {
    button = context.document.createElement("button");
    button.className = "docsViewer__toolbarIconButton docsViewer__contentDetailBack";
    button.type = "button";
  }
  button.replaceChildren(createDocsViewerToolbarIcon(context.document, "docsViewer__icon--arrow-left"));
  return button;
}

function renderDocumentLinks(context) {
  var button = context.existingRoot || context.document.createElement("button");
  button.className = "docsViewer__toolbarIconButton";
  button.type = "button";
  button.replaceChildren(createDocsViewerToolbarIcon(context.document, "docsViewer__icon--waypoints"));
  return button;
}

function renderContentDetailLabel(context) {
  var label = context.existingRoot;
  if (!label || label.tagName !== "SPAN") {
    label = context.document.createElement("span");
    label.className = "docsViewer__contentDetailLabel";
  }
  label.textContent = context.control.state && context.control.state.label || context.control.label;
  return label;
}

function renderContentDetailOpenNewTab(context) {
  var link = context.existingRoot;
  if (!link || link.tagName !== "A") {
    link = context.document.createElement("a");
    link.className = "docsViewer__toolbarIconButton docsViewer__contentDetailOpenNewTab";
    link.target = "_blank";
    link.rel = "noopener";
    link.appendChild(createDocsViewerToolbarIcon(context.document, "docsViewer__icon--external-link"));
  }
  var label = context.control.state && context.control.state.label || context.control.label;
  link.setAttribute("aria-label", label);
  link.title = label;
  link.href = context.control.state && context.control.state.href || "";
  return link;
}

export function createDocsViewerSharedControlRenderers() {
  return {
    "recent-button": renderRecentButton,
    "search-input": renderSearchInput,
    "bookmark-toggle": renderBookmarkToggle,
    "info-toggle": renderInfoToggle,
    "document-links": renderDocumentLinks,
    "content-detail-back": renderContentDetailBack,
    "content-detail-label": renderContentDetailLabel,
    "content-detail-open-new-tab": renderContentDetailOpenNewTab
  };
}
