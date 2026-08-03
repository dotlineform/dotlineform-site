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

function listing(payload, requested) {
  if (!payload || text(payload.current_directory) !== requested) {
    throw new Error("Folder listing did not match the requested directory.");
  }
  if (payload.current_selectable !== true && payload.current_selectable !== false) {
    throw new Error("Folder listing has an invalid selection state.");
  }
  const parent = payload.parent_directory == null ? null : text(payload.parent_directory);
  if (payload.parent_directory != null && !parent) {
    throw new Error("Folder listing has an invalid parent directory.");
  }
  const directories = (Array.isArray(payload.directories) ? payload.directories : []).map((item) => {
    const directory = text(item && item.source_directory);
    const label = text(item && item.label);
    if (!directory || !label) throw new Error("Folder listing contains an invalid directory.");
    return { directory, label };
  });
  return { directory: requested, selectable: payload.current_selectable === true, parent, directories };
}

export function createFolderPicker(root, options = {}) {
  const initialDirectory = text(options.initialDirectory);
  if (!root || !initialDirectory || typeof options.loadDirectory !== "function" || typeof options.onSubmit !== "function") {
    throw new Error("Folder picker configuration is incomplete.");
  }
  const id = `sharedFolderPicker-${++pickerSequence}`;
  root.innerHTML = [
    '<div class="sharedFolderPicker" data-folder-picker tabindex="-1">',
    '  <nav class="sharedFolderPicker__breadcrumbs" data-breadcrumbs aria-label="Current folder"></nav>',
    '  <div class="sharedFolderPicker__toolbar">',
    '    <button class="sharedFolderPicker__parent" type="button" data-parent>Parent folder</button>',
    '  </div>',
    '  <p class="sharedFolderPicker__status" data-status role="status" aria-live="polite"></p>',
    `  <div class="sharedFolderPicker__list" id="${id}-list" data-list role="listbox" tabindex="0" aria-label="Folders"></div>`,
    '</div>'
  ].join("");
  const picker = root.querySelector("[data-folder-picker]");
  const breadcrumbs = root.querySelector("[data-breadcrumbs]");
  const parentButton = root.querySelector("[data-parent]");
  const statusNode = root.querySelector("[data-status]");
  const list = root.querySelector("[data-list]");
  let current = null;
  let activeIndex = -1;
  let requestId = 0;
  let destroyed = false;

  function status(message, state = "") {
    statusNode.textContent = message;
    if (state) statusNode.dataset.state = state;
    else delete statusNode.dataset.state;
  }

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
    parentButton.disabled = !record.parent;
    breadcrumbs.innerHTML = record.directory === "."
      ? '<span class="sharedFolderPicker__breadcrumb" aria-current="page">Projects</span>'
      : `<button class="sharedFolderPicker__breadcrumb" type="button" data-nav=".">Projects</button><span class="sharedFolderPicker__separator">/</span><span class="sharedFolderPicker__breadcrumb" aria-current="page">${escapeHtml(record.directory)}</span>`;
    list.innerHTML = record.directories.length
      ? record.directories.map((item, index) => (
        `<div class="sharedFolderPicker__option" id="${id}-option-${index + 1}" role="option" aria-selected="false" data-directory="${escapeHtml(item.directory)}">${escapeHtml(item.label)}</div>`
      )).join("")
      : '<p class="sharedFolderPicker__empty">No folders in this location.</p>';
    activeIndex = -1;
    list.removeAttribute("aria-activedescendant");
    if (record.directories.length) activate(0);
    status(record.selectable
      ? "This folder can be selected."
      : "Choose a folder below the Projects root.");
  }

  async function load(directory, focus = false) {
    const requested = text(directory);
    const activeRequest = ++requestId;
    list.setAttribute("aria-busy", "true");
    parentButton.disabled = true;
    status("Loading folders…", "busy");
    try {
      const record = listing(await options.loadDirectory({ directory: requested }), requested);
      if (destroyed || activeRequest !== requestId) return null;
      render(record);
      if (focus) focusPreferred();
      return record;
    } catch (error) {
      if (!destroyed && activeRequest === requestId) {
        status(text(error && error.message) || "Folder could not be loaded.", "error");
      }
      throw error;
    } finally {
      if (!destroyed && activeRequest === requestId) list.setAttribute("aria-busy", "false");
    }
  }

  function navigate(directory) {
    load(directory, true).catch(() => {});
  }

  function focusPreferred() {
    const target = current && current.directories.length
      ? list
      : current && current.parent ? parentButton : picker;
    target.focus({ preventScroll: true });
    return true;
  }

  picker.addEventListener("click", (event) => {
    const target = event.target.closest("[data-nav], [data-directory]");
    if (target) navigate(target.dataset.nav || target.dataset.directory);
  });
  parentButton.addEventListener("click", () => {
    if (current && current.parent) navigate(current.parent);
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
      status("Choose a selectable folder before continuing.", "error");
      throw new Error("Choose a selectable folder before continuing.");
    }
    status("Selecting folder…", "busy");
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
