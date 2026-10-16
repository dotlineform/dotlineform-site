import { createDocsViewerToolbarIcon } from "./docs-viewer-toolbar-icon.js";

var THEME_STORAGE_KEY = "theme";
var LIGHT_THEME = "light";
var DARK_THEME = "dark";

/** Render the shared reader theme control; initialization owns its state and events. */
export function renderDocsViewerThemeToggle(documentRef) {
  var button = documentRef.createElement("button");
  button.className = "docsViewer__toolbarIconButton";
  button.type = "button";
  button.setAttribute("data-docs-viewer-theme-toggle", "");
  renderToggle(button, currentTheme(documentRef.documentElement, null));
  return button;
}

function normalizeTheme(value) {
  return value === DARK_THEME ? DARK_THEME : LIGHT_THEME;
}

function readStoredTheme(storage) {
  if (!storage) return "";
  try {
    return normalizeTheme(storage.getItem(THEME_STORAGE_KEY));
  } catch (error) {
    return "";
  }
}

function writeStoredTheme(storage, theme) {
  if (!storage) return;
  try {
    storage.setItem(THEME_STORAGE_KEY, theme);
  } catch (error) {}
}

function currentTheme(documentElement, storage) {
  var attributeTheme = documentElement ? documentElement.getAttribute("data-theme") : "";
  if (attributeTheme === LIGHT_THEME || attributeTheme === DARK_THEME) {
    return attributeTheme;
  }
  return readStoredTheme(storage) || LIGHT_THEME;
}

function applyTheme(documentElement, theme) {
  if (!documentElement) return;
  documentElement.setAttribute("data-theme", normalizeTheme(theme));
}

function renderToggle(button, theme) {
  var activeTheme = normalizeTheme(theme);
  var isDark = activeTheme === DARK_THEME;
  var nextLabel = isDark ? "Switch to light mode" : "Switch to dark mode";
  button.setAttribute("aria-label", nextLabel);
  button.setAttribute("aria-pressed", isDark ? "true" : "false");
  button.title = nextLabel;
  button.replaceChildren(createDocsViewerToolbarIcon(button.ownerDocument,
    isDark ? "docsViewer__icon--moon" : "docsViewer__icon--sun"));
}

/** Bind reader theme changes and publish the applied theme event. */
export function initDocsViewerThemeToggle(options) {
  var settings = options || {};
  var root = settings.root;
  var documentRef = settings.document || document;
  var storage = settings.storage;
  if (storage === undefined) {
    try {
      storage = documentRef.defaultView.localStorage;
    } catch (error) {
      storage = null;
    }
  }
  var documentElement = documentRef.documentElement;
  if (!root || !documentElement) return null;

  var buttons = Array.prototype.slice.call(root.querySelectorAll("[data-docs-viewer-theme-toggle]"));
  if (!buttons.length) return null;

  function setTheme(theme) {
    var nextTheme = normalizeTheme(theme);
    applyTheme(documentElement, nextTheme);
    writeStoredTheme(storage, nextTheme);
    buttons.forEach(function (button) {
      renderToggle(button, nextTheme);
    });
    var windowRef = documentRef.defaultView;
    if (windowRef && typeof windowRef.CustomEvent === "function") {
      documentRef.dispatchEvent(new windowRef.CustomEvent("dlf:theme-applied", {
        detail: { theme: nextTheme }
      }));
    }
  }

  buttons.forEach(function (button) {
    button.addEventListener("click", function () {
      var nextTheme = currentTheme(documentElement, storage) === DARK_THEME ? LIGHT_THEME : DARK_THEME;
      setTheme(nextTheme);
    });
  });

  setTheme(currentTheme(documentElement, storage));
  return { setTheme: setTheme };
}
