const THEME_STORAGE_KEY = "theme";
const LIGHT_THEME = "light";
const DARK_THEME = "dark";

function normalizeTheme(value) {
  return value === DARK_THEME ? DARK_THEME : LIGHT_THEME;
}

function readStoredTheme(storage) {
  if (!storage) return "";
  try {
    return normalizeTheme(storage.getItem(THEME_STORAGE_KEY));
  } catch (_error) {
    return "";
  }
}

function writeStoredTheme(storage, theme) {
  if (!storage) return;
  try {
    storage.setItem(THEME_STORAGE_KEY, theme);
  } catch (_error) {}
}

function currentTheme(documentElement, storage) {
  const attributeTheme = documentElement ? documentElement.getAttribute("data-theme") : "";
  if (attributeTheme === LIGHT_THEME || attributeTheme === DARK_THEME) {
    return attributeTheme;
  }
  return readStoredTheme(storage) || LIGHT_THEME;
}

function renderToggle(button, theme) {
  const activeTheme = normalizeTheme(theme);
  const isDark = activeTheme === DARK_THEME;
  const nextLabel = isDark ? "Switch to light mode" : "Switch to dark mode";
  button.setAttribute("aria-label", nextLabel);
  button.setAttribute("aria-pressed", isDark ? "true" : "false");
  button.title = nextLabel;
  button.querySelectorAll("[data-studio-theme-icon]").forEach((icon) => {
    if (icon.dataset.studioThemeIcon === activeTheme) {
      icon.removeAttribute("hidden");
    } else {
      icon.setAttribute("hidden", "");
    }
  });
}

export function initStudioThemeToggle(options = {}) {
  const root = options.root || document;
  const documentRef = options.document || document;
  const storage = options.storage || window.localStorage;
  const documentElement = documentRef.documentElement;
  if (!root || !documentElement) return null;

  const buttons = Array.from(root.querySelectorAll("[data-studio-theme-toggle]"));
  if (!buttons.length) return null;

  function setTheme(theme) {
    const nextTheme = normalizeTheme(theme);
    documentElement.setAttribute("data-theme", nextTheme);
    writeStoredTheme(storage, nextTheme);
    buttons.forEach((button) => {
      renderToggle(button, nextTheme);
    });
  }

  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      const nextTheme = currentTheme(documentElement, storage) === DARK_THEME ? LIGHT_THEME : DARK_THEME;
      setTheme(nextTheme);
    });
  });

  setTheme(currentTheme(documentElement, storage));
  return { setTheme };
}
