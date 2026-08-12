let pickerSequence = 0;

function text(value) {
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

function directoryMarker(value) {
  const marker = text(value);
  if (marker === ".") return marker;
  if (!marker || marker.startsWith("/") || marker.endsWith("/") || marker.includes("\\")) {
    throw new Error("Folder marker is not canonical.");
  }
  const parts = marker.split("/");
  if (parts.some((part) => !part || part === "." || part === "..")) {
    throw new Error("Folder marker is not canonical.");
  }
  return parts.join("/");
}

function isWithin(directory, rootDirectory) {
  return rootDirectory === "."
    || directory === rootDirectory
    || directory.startsWith(`${rootDirectory}/`);
}

function parentMarker(directory) {
  if (directory === ".") return null;
  const parts = directory.split("/");
  return parts.length === 1 ? "." : parts.slice(0, -1).join("/");
}

function listing(payload, requested, rootDirectory) {
  if (!payload || directoryMarker(payload.current_directory) !== requested) {
    throw new Error("Folder listing did not match the requested directory.");
  }
  if (!isWithin(requested, rootDirectory)) {
    throw new Error("Folder listing escaped its configured root.");
  }
  if (payload.current_selectable !== true && payload.current_selectable !== false) {
    throw new Error("Folder listing has an invalid selection state.");
  }
  const parent = payload.parent_directory == null ? null : directoryMarker(payload.parent_directory);
  const expectedParent = requested === rootDirectory ? null : parentMarker(requested);
  if (parent !== expectedParent || (parent !== null && !isWithin(parent, rootDirectory))) {
    throw new Error("Folder listing has an invalid parent directory.");
  }
  const directories = (Array.isArray(payload.directories) ? payload.directories : []).map((item) => {
    const directory = directoryMarker(item && item.source_directory);
    const label = text(item && item.label);
    if (
      !label
      || !isWithin(directory, rootDirectory)
      || parentMarker(directory) !== requested
    ) {
      throw new Error("Folder listing contains an invalid directory.");
    }
    return { directory, label };
  });
  return { directory: requested, selectable: payload.current_selectable === true, parent, directories };
}

function breadcrumbMarkup(directory, rootDirectory, rootLabel) {
  const rootSegments = rootDirectory === "." ? [] : rootDirectory.split("/");
  const segments = directory === rootDirectory
    ? []
    : directory.split("/").slice(rootSegments.length);
  const locations = [{ directory: rootDirectory, label: rootLabel }];
  segments.forEach((label, index) => {
    const relative = segments.slice(0, index + 1);
    locations.push({
      directory: rootDirectory === "."
        ? relative.join("/")
        : rootSegments.concat(relative).join("/"),
      label
    });
  });
  return locations.map((location, index) => {
    const separator = index
      ? '<span class="sharedFolderPicker__separator" aria-hidden="true">/</span>'
      : "";
    if (index === locations.length - 1) {
      return `${separator}<span class="sharedFolderPicker__current" aria-current="location">${escapeHtml(location.label)}</span>`;
    }
    return `${separator}<button class="sharedFolderPicker__breadcrumb" type="button" data-nav="${escapeHtml(location.directory)}">${escapeHtml(location.label)}</button>`;
  }).join("");
}

export function createFolderPicker(root, options = {}) {
  const rootDirectory = directoryMarker(options.rootDirectory || ".");
  const initialDirectory = directoryMarker(options.initialDirectory);
  const rootLabel = text(options.rootLabel)
    || (rootDirectory === "." ? "Projects" : rootDirectory.split("/").slice(-1)[0]);
  if (!root || !initialDirectory || typeof options.loadDirectory !== "function" || typeof options.onSubmit !== "function") {
    throw new Error("Folder picker configuration is incomplete.");
  }
  if (!isWithin(initialDirectory, rootDirectory)) {
    throw new Error("Initial folder is outside the configured root.");
  }
  const id = `sharedFolderPicker-${++pickerSequence}`;
  root.innerHTML = [
    '<div class="sharedFolderPicker" data-folder-picker tabindex="-1">',
    '  <nav class="sharedFolderPicker__breadcrumbs" data-breadcrumbs aria-label="Current folder"></nav>',
    `  <div class="sharedFolderPicker__list" id="${id}-list" data-list role="listbox" tabindex="0" aria-label="Folders"></div>`,
    '</div>'
  ].join("");
  const picker = root.querySelector("[data-folder-picker]");
  const breadcrumbs = root.querySelector("[data-breadcrumbs]");
  const list = root.querySelector("[data-list]");
  let current = null;
  let activeIndex = -1;
  let requestId = 0;
  let destroyed = false;

  function activate(index) {
    const rows = Array.from(list.querySelectorAll("[data-directory]"));
    if (!rows.length) return false;
    activeIndex = Math.max(0, Math.min(rows.length - 1, index));
    rows.forEach((row, rowIndex) => {
      const active = rowIndex === activeIndex;
      row.dataset.active = active ? "true" : "false";
      row.setAttribute("aria-selected", active ? "true" : "false");
    });
    list.setAttribute("aria-activedescendant", rows[activeIndex].id);
    rows[activeIndex].scrollIntoView({ block: "nearest" });
    return true;
  }

  function render(record) {
    current = record;
    breadcrumbs.innerHTML = breadcrumbMarkup(record.directory, rootDirectory, rootLabel);
    list.innerHTML = record.directories.length
      ? record.directories.map((item, index) => (
        `<div class="sharedFolderPicker__option" id="${id}-option-${index + 1}" role="option" aria-selected="false" data-directory="${escapeHtml(item.directory)}">${escapeHtml(item.label)}</div>`
      )).join("")
      : '<p class="sharedFolderPicker__empty">No folders in this location.</p>';
    activeIndex = -1;
    list.removeAttribute("aria-activedescendant");
    if (record.directories.length) activate(0);
  }

  async function load(directory, focus = false) {
    const requested = directoryMarker(directory);
    if (!isWithin(requested, rootDirectory)) {
      throw new Error("Folder navigation escaped its configured root.");
    }
    const activeRequest = ++requestId;
    list.setAttribute("aria-busy", "true");
    try {
      const record = listing(
        await options.loadDirectory({ directory: requested }),
        requested,
        rootDirectory
      );
      if (destroyed || activeRequest !== requestId) return null;
      render(record);
      if (focus) focusPreferred();
      return record;
    } finally {
      if (!destroyed && activeRequest === requestId) list.setAttribute("aria-busy", "false");
    }
  }

  function navigate(directory) {
    load(directory, true).catch((error) => {
      if (!destroyed && typeof options.onError === "function") options.onError(error);
    });
  }

  function focusPreferred() {
    const parentLinks = Array.from(breadcrumbs.querySelectorAll("[data-nav]"));
    const target = current && current.directories.length
      ? list
      : parentLinks[parentLinks.length - 1] || picker;
    target.focus({ preventScroll: true });
    return true;
  }

  picker.addEventListener("click", (event) => {
    const target = event.target.closest("[data-nav], [data-directory]");
    if (target) navigate(target.dataset.nav || target.dataset.directory);
  });
  list.addEventListener("keydown", (event) => {
    if (!current || !current.directories.length) return;
    const keys = { ArrowDown: 1, ArrowUp: -1, Home: -Infinity, End: Infinity };
    if (Object.prototype.hasOwnProperty.call(keys, event.key)) {
      event.preventDefault();
      const movement = keys[event.key];
      activate(Number.isFinite(movement) ? activeIndex + movement : movement < 0 ? 0 : current.directories.length - 1);
    } else if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      const item = current.directories[activeIndex];
      if (item) navigate(item.directory);
    }
  });

  async function submit() {
    if (!current || !current.selectable) {
      throw new Error(
        rootDirectory === "."
          ? "Choose a folder below the Projects root."
          : "Choose an available folder."
      );
    }
    return options.onSubmit({ directory: current.directory });
  }

  return Object.freeze({
    ready: load(initialDirectory),
    focusPreferred,
    getDirectory: () => current ? current.directory : "",
    submit,
    destroy: () => {
      if (destroyed) return false;
      destroyed = true;
      requestId += 1;
      root.replaceChildren();
      return true;
    }
  });
}
