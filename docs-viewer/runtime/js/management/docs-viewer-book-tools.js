import { fetchManagementJson } from "./docs-viewer-management-client.js";
import { escapeHtml, openDocsViewerManagementModal } from "./docs-viewer-management-modal-shell.js";
import { openDocsViewerPositionModal } from "./docs-viewer-position-modal.js";
import { collectionSequenceForLink } from "../shared/docs-viewer-collection-navigation.js";
import { createDocsViewerToolbarIcon } from "../shared/docs-viewer-toolbar-icon.js";

const bookManifest = "/docs/generated/external/book/manage-manifest.json";
const bookTree = "/docs/generated/external/book/index-tree.json";

function button(document, label, action) {
  const control = document.createElement("button");
  control.type = "button";
  control.className = "docsViewerReport__collectionSelectionButton docsViewerBook__control";
  control.textContent = label;
  control.addEventListener("click", action);
  return control;
}

function field(label, control) {
  return '<label class="docsViewer__field"><span class="docsViewer__fieldLabel">'
    + escapeHtml(label) + "</span>" + control + "</label>";
}

function option(value, label) {
  return '<option value="' + escapeHtml(value) + '">' + escapeHtml(label) + "</option>";
}

function bookHeadings(tree) {
  return tree.flatMap(node => [node, ...(node.sections || [])]);
}

function headingOptions(tree) {
  return tree.map(node => option(node.id, node.title)
    + (node.sections || []).map(section => option(section.id, "\u00a0\u00a0" + section.title)).join("")).join("");
}

function sectionOptions(tree) {
  return tree.map(node => {
    if (!node.sections) return option(node.id, node.title);
    if (!node.sections.length) return "";
    return '<optgroup label="' + escapeHtml(node.title) + '">'
      + node.sections.map(section => option(section.id, section.title)).join("") + "</optgroup>";
  }).join("");
}

function chapterCopyCheckbox(attribute, label) {
  return '<label class="docsViewer__field docsViewer__field--checkbox">'
    + '<input class="docsViewer__checkboxInput" type="checkbox" ' + attribute + '>'
    + '<span class="docsViewer__fieldLabel">' + escapeHtml(label) + "</span></label>";
}

function createBookRowSelection(options) {
  let selectedId = "";
  let selectedRow = null;
  let run;
  let enabled = false;
  let checkboxMode = false;

  function project() {
    if (selectedRow) {
      if (checkboxMode) selectedRow.link.removeAttribute("aria-current");
      else selectedRow.link.setAttribute("aria-current", "true");
    }
  }

  function select(row) {
    selectedRow?.link.removeAttribute("aria-current");
    selectedRow = row;
    selectedId = row.record.doc_id;
    project();
  }

  function open(row, action) {
    row.link.focus({ preventScroll: true });
    return action({ collection: "book", doc_id: row.record.doc_id }, {
      collectionSequence: collectionSequenceForLink(row.link)
    });
  }

  return {
    prepare(docIds, runAction) {
      if (!docIds.includes(selectedId)) selectedId = "";
      selectedRow = null;
      run = runAction;
    },
    bindRow(link, record, toggleChecked) {
      const row = { link, record };
      if (record.doc_id === selectedId) selectedRow = row;
      const element = link.parentElement;
      element.classList.add("docsViewerBook__selectableRow");
      element.addEventListener("click", event => {
        if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey
          || event.target.closest("input, button")) return;
        if (!enabled) {
          event.preventDefault();
          return;
        }
        if (event.altKey) {
          if (!checkboxMode) select(row);
          // Let the shared reader handle the title link after projecting Book selection.
          if (link.contains(event.target)) return;
          open(row, options.openSourceFromLink);
          return;
        }
        event.preventDefault();
        if (checkboxMode && event.detail !== 0) {
          link.focus({ preventScroll: true });
          toggleChecked();
          return;
        }
        if (!checkboxMode) select(row);
        run(() => open(row, options.openDocument));
      });
      link.addEventListener("keydown", event => {
        if (event.key !== " " || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
        event.preventDefault();
        if (!enabled) return;
        if (checkboxMode) toggleChecked();
        else select(row);
      });
    },
    capture: () => selectedId,
    restore(id) { selectedId = typeof id === "string" ? id : ""; },
    project(canInteract, bulk) {
      enabled = canInteract;
      checkboxMode = bulk;
      project();
    }
  };
}

export async function openBookLibrarySources({ chapter, clientOptions, root, button, startBusyOperation, commitDocumentChange }) {
  const client = { ...clientOptions, cache: "no-store" };
  const manifest = await fetchManagementJson(bookManifest, "GET", undefined, client);
  if (!button.isConnected || button.closest("[hidden]")) return;
  const saved = chapter.library_sources || [];
  const records = new Map(saved.map(record => [record.doc_id, record]));
  for (const { copied_from_library: origin } of manifest.docs) {
    if (origin && !records.has(origin.doc_id)) records.set(origin.doc_id, origin);
  }
  const checked = new Set(saved.map(record => record.doc_id));
  const body = Array.from(records.values()).map(record =>
    '<label class="docsViewer__field docsViewer__field--checkbox"><input type="checkbox" data-book-source value="'
    + escapeHtml(record.doc_id) + '"' + (checked.has(record.doc_id) ? " checked" : "") + ">"
    + '<span class="docsViewer__fieldLabel" title="' + escapeHtml(record.doc_id) + '">'
    + escapeHtml(record.title) + "</span></label>").join("");
  const result = await openDocsViewerManagementModal({
    root, title: "Library sources",
    bodyHtml: body || "<p>No Library sources are available.</p>",
    restoreFocus: () => root.querySelector("[data-book-library-sources]"),
    focusSelector: "input",
    actions: [{ role: "modal-primary", label: "Save" }, { role: "modal-cancel", label: "Cancel" }],
    async onSubmit({ host }) {
      const librarySources = Array.from(host.querySelectorAll("[data-book-source]:checked"), input => records.get(input.value));
      const stop = startBusyOperation();
      try {
        return await fetchManagementJson("/docs/book/sources", "POST", {
          doc_id: chapter.doc_id, library_sources: librarySources
        }, client);
      } finally {
        stop();
      }
    }
  });
  if (!result.ok) return;
  const failures = commitDocumentChange({
    target: { collection: "book", doc_id: chapter.doc_id },
    record: { ...chapter, library_sources: result.library_sources }
  });
  if (failures?.length) {
    throw new Error("Library sources saved. Could not update retained views. " + failures.map(error => error.message).join(" "));
  }
}

export async function createBookReportTools(options) {
  const isBook = options.collection === "book";
  const client = { ...options.clientOptions, cache: "no-store" };
  const get = path => fetchManagementJson(path, "GET", undefined, client);
  const post = async (path, payload, { alreadyBusy = false } = {}) => {
    const stop = alreadyBusy ? null : options.startBusyOperation?.();
    try {
      return await fetchManagementJson(path, "POST", payload, client);
    } finally {
      stop?.();
    }
  };
  let tree = isBook ? (await get(bookTree)).tree : null;
  const copied = new Set(isBook ? [] : (await get("/docs/book/copied")).doc_ids);
  let navigation;
  let headingId = "";

  function modal(title, bodyHtml, onSubmit, onOpen, primaryLabel = "Save") {
    return openDocsViewerManagementModal({
      root: options.root, title, bodyHtml, onSubmit, onOpen,
      focusSelector: "select, input",
      actions: [{ role: "modal-primary", label: primaryLabel }, { role: "modal-cancel", label: "Cancel" }]
    });
  }

  function commit(record, sectionId) {
    return options.commitDocumentChange?.({
      target: { collection: "book", doc_id: record.doc_id }, record, bookSectionId: sectionId
    }) || [];
  }

  async function copySelection(docIds, renderList) {
    const [bookIndex, manifest] = await Promise.all([get(bookTree), get(bookManifest)]);
    const sections = new Map(bookHeadings(bookIndex.tree).filter(node => !node.sections).map(node => [node.id, node]));
    const chapters = new Map(manifest.docs.filter(row => !row.copied_from_library).map(row => [row.doc_id, row]));
    const sectionField = field("Copy to section", '<select class="docsViewer__fieldInput" data-book-section>'
      + option("", sections.size ? "Choose a section" : "No sections yet") + sectionOptions(bookIndex.tree) + "</select>");
    const newChapter = '<div class="docsViewer__fieldGroup">'
      + chapterCopyCheckbox("data-book-new", "Add to a new chapter")
      + field("Chapter title", '<input class="docsViewer__fieldInput" data-book-title type="text" autocomplete="off" disabled>')
      + "</div>";
    const existingChapter = '<div class="docsViewer__fieldGroup">'
      + chapterCopyCheckbox("data-book-existing", "Add to an existing chapter")
      + field("Chapter", '<select class="docsViewer__fieldInput" data-book-chapter disabled></select>')
      + "</div>";
    let controls;
    function updateChapterPicker() {
      const section = sections.get(controls.section.value);
      const choices = section ? section.doc_ids.map(id => chapters.get(id)).filter(Boolean) : [];
      const placeholder = !section ? "Choose a section first"
        : choices.length ? "Choose a chapter" : "No chapters in this section";
      controls.chapter.innerHTML = option("", placeholder) + choices.map(row => option(row.doc_id, row.title)).join("");
    }
    const result = await modal("Copy to Book", sectionField + newChapter + existingChapter, () => {
      const sectionId = controls.section.value;
      if (!sectionId) throw new Error("Choose a Book section.");
      const payload = { doc_ids: docIds, section_id: sectionId };
      if (controls.addNew.checked) {
        payload.new_chapter_title = controls.title.value.trim();
        if (!payload.new_chapter_title) throw new Error("Enter a chapter title.");
      }
      if (controls.addExisting.checked) {
        payload.existing_chapter_id = controls.chapter.value;
        if (!payload.existing_chapter_id) throw new Error("Choose a chapter in the selected section.");
      }
      return post("/docs/book/copy", payload);
    }, ({ host }) => {
      controls = {
        section: host.querySelector("[data-book-section]"),
        addNew: host.querySelector("[data-book-new]"),
        addExisting: host.querySelector("[data-book-existing]"),
        title: host.querySelector("[data-book-title]"),
        chapter: host.querySelector("[data-book-chapter]")
      };
      host.querySelector('[data-role="modal-primary"]').disabled = !sections.size;
      controls.section.addEventListener("change", updateChapterPicker);
      controls.addNew.addEventListener("change", () => {
        controls.title.disabled = !controls.addNew.checked;
      });
      controls.addExisting.addEventListener("change", () => {
        controls.chapter.disabled = !controls.addExisting.checked;
      });
      updateChapterPicker();
    }, "Copy");
    if (!result.ok) return;
    result.copied_doc_ids.forEach(id => copied.add(id));
    const placements = new Set(result.placed_doc_ids);
    const failures = result.records.flatMap(record =>
      commit(record, placements.has(record.doc_id) ? result.section_id : undefined));
    renderList();
    const message = result.copied_doc_ids.length + " copied to " + sections.get(result.section_id).title + ".";
    options.setStatus?.(failures.length
      ? message + " Could not update the retained Book list. " + failures.map(error => error.message).join(" ")
      : message, Boolean(failures.length));
  }

  async function clearCopyFlags(docIds, renderList) {
    await post("/docs/book/copied/clear", { doc_ids: docIds });
    docIds.forEach(id => copied.delete(id));
    renderList();
  }

  async function saveTree(next, selected = headingId, requestOptions) {
    const result = await post("/docs/book/tree", { tree: next }, requestOptions);
    tree = result.tree;
    navigation.redraw(selected);
  }

  async function addHeading(part) {
    const body = field(part ? "Part title" : "Section title", '<input class="docsViewer__fieldInput" data-book-heading type="text" autocomplete="off">')
      + (!part && tree.some(node => node.sections)
        ? field("Part", '<select class="docsViewer__fieldInput" data-book-parent>' + option("", "Top level")
          + tree.filter(node => node.sections).map(node => option(node.id, node.title)).join("") + "</select>") : "");
    await modal(part ? "New part" : "New section", body, async ({ host }) => {
      const title = host.querySelector("[data-book-heading]").value.trim();
      if (!title) throw new Error("Enter a title.");
      const parentId = host.querySelector("[data-book-parent]")?.value;
      const next = structuredClone(tree);
      const group = parentId ? next.find(node => node.id === parentId).sections : next;
      const node = { id: crypto.randomUUID(), title, doc_ids: [] };
      if (part) node.sections = [];
      group.push(node);
      await saveTree(next, node.id);
    });
  }

  async function editHeading() {
    const selected = bookHeadings(tree).find(node => node.id === headingId);
    if (!selected) return;
    const kind = selected.sections ? "part" : "section";
    const oldPart = tree.find(node => node.sections?.includes(selected));
    const parts = selected.sections ? [] : tree.filter(node => node.sections);
    const body = field(selected.sections ? "Part title" : "Section title", '<input class="docsViewer__fieldInput" data-book-heading type="text" autocomplete="off" value="'
      + escapeHtml(selected.title) + '">') + (parts.length
      ? field("Part", '<select class="docsViewer__fieldInput" data-book-parent>' + option("", "Top level")
        + parts.map(part => option(part.id, part.title)).join("") + "</select>") : "");
    await modal("Edit " + kind, body, async ({ host }) => {
      const title = host.querySelector("[data-book-heading]").value.trim();
      if (!title) throw new Error("Enter a title.");
      const partId = host.querySelector("[data-book-parent]")?.value || "";
      const next = structuredClone(tree);
      const from = oldPart ? next.find(node => node.id === oldPart.id).sections : next;
      const index = from.findIndex(node => node.id === selected.id);
      from[index].title = title;
      if (partId !== (oldPart?.id || "")) {
        const to = partId ? next.find(node => node.id === partId).sections : next;
        to.push(from.splice(index, 1)[0]);
      }
      await saveTree(next);
    }, ({ host }) => {
      const picker = host.querySelector("[data-book-parent]");
      if (picker) picker.value = oldPart?.id || "";
    });
  }

  async function positionSelection(docIds) {
    const titles = new Map(navigation.rows().map(row => [row.docId, row.title]));
    const selected = new Set(docIds);
    const inside = [{ id: "", title: "Unfiled", depth: 0, headingId: "" }];
    const beside = [];
    function addDestinations(heading, depth) {
      const row = { id: "heading:" + heading.id, title: heading.title, depth, headingId: heading.id };
      inside.push(row);
      beside.push({ ...row, disabled: true });
      for (const docId of heading.doc_ids) {
        if (selected.has(docId)) continue;
        beside.push({ id: "document:" + docId, title: titles.get(docId), depth: depth + 1, headingId: heading.id, docId });
      }
    }
    for (const node of tree) {
      addDestinations(node, 0);
      for (const section of node.sections || []) addDestinations(section, 1);
    }
    const destinations = new Map([...beside, ...inside].map(row => [row.id, row]));
    await openDocsViewerPositionModal({
      root: options.root,
      title: "Position " + (docIds.length === 1 ? titles.get(docIds[0]) : docIds.length + " documents"),
      insideLabel: "Inside (at end)",
      initialPlacement: "inside",
      getDestinations: placement => placement === "inside" ? inside : beside,
      onSave: async (targetId, placement) => {
        const target = destinations.get(targetId);
        const next = structuredClone(tree);
        let changed = false;
        for (const heading of bookHeadings(next)) {
          const previous = heading.doc_ids;
          const ordered = previous.filter(id => !selected.has(id));
          if (heading.id === target.headingId) {
            if (placement === "inside") ordered.push(...docIds);
            else ordered.splice(ordered.indexOf(target.docId) + Number(placement === "after"), 0, ...docIds);
          }
          if (ordered.length !== previous.length || ordered.some((id, index) => id !== previous[index])) {
            heading.doc_ids = ordered;
            changed = true;
          }
        }
        if (changed) await saveTree(next, target.headingId || headingId);
        else if (target.headingId && target.headingId !== headingId) navigation.choose(target.headingId);
      }
    });
  }

  return {
    rowSelection: isBook ? createBookRowSelection(options) : null,
    withNewDocumentPlacement(openDocument) {
      const destinationId = headingId;
      if (!destinationId) return openDocument;
      return async (target, response) => {
        if (response.ok !== false) {
          const next = structuredClone(tree);
          const destination = bookHeadings(next).find(node => node.id === destinationId);
          destination.doc_ids.push(target.doc_id);
          try {
            await saveTree(next, destinationId, { alreadyBusy: true });
          } catch (error) {
            throw new Error("Could not finish placing the new document in " + destination.title + ". " + error.message, { cause: error });
          }
        }
        return openDocument(target, response);
      };
    },
    renderIndicator(host, { doc_id: docId, copied_from_library: origin }) {
      if (isBook ? !origin : !copied.has(docId)) return;
      const label = isBook ? "Working copy from Library" : "Copied to Book";
      const icon = host.ownerDocument.createElement("span");
      icon.className = "docsViewer__listIcon " + (isBook
        ? "docsViewer__icon--copy docsViewerBook__workingCopyIndicator" : "docsViewer__icon--dlf-doc");
      icon.title = label;
      icon.setAttribute("aria-hidden", "true");
      host.append(icon);
      return label;
    },
    mountSelectionControls(host, renderList) {
      const document = host.ownerDocument;
      const controls = { ids: [] };
      const add = (key, label, run, artwork) => {
        const control = button(document, label, () => run().catch(error => options.setStatus?.(error.message, true)));
        control.className = "docsViewer__toolbarIconButton docsViewerBook__control";
        control.title = label;
        control.setAttribute("aria-label", label);
        control.replaceChildren(createDocsViewerToolbarIcon(document, artwork));
        control.hidden = true;
        controls[key] = control;
        host.append(control);
      };
      if (isBook) {
        add("position", "Position…", () => positionSelection(controls.ids), "docsViewer__icon--arrow-up-down");
      } else {
        add("copy", "Copy to Book…", () => copySelection(controls.ids, renderList), "docsViewer__icon--dlf-doc");
        add("clearCopied", "Clear Copied to Book", () => clearCopyFlags(controls.flaggedIds, renderList), "docsViewer__icon--dlf-doc");
        controls.clearCopied.classList.add("docsViewerBook__clearCopyFlag");
      }
      return controls;
    },
    projectSelection(controls, ids) {
      controls.ids = ids;
      if (!isBook) {
        controls.copy.hidden = !ids.length;
        controls.flaggedIds = ids.filter(id => copied.has(id));
        controls.clearCopied.hidden = !controls.flaggedIds.length;
        return;
      }
      controls.position.hidden = !ids.length || !tree.length;
    },
    updateInventory(ids) {
      if (!isBook) return;
      const present = new Set(ids);
      for (const heading of bookHeadings(tree)) {
        heading.doc_ids = heading.doc_ids.filter(id => present.has(id));
      }
    },
    applyPlacement(sectionId, docId) {
      bookHeadings(tree).find(node => node.id === sectionId).doc_ids.push(docId);
    },
    ...(isBook ? { mountSectionNavigation({ root, rows, rowForId, change }) {
      const document = root.ownerDocument;
      const list = document.createElement("nav");
      list.className = "docsViewerBook__sectionList";
      list.setAttribute("aria-label", "Book contents");
      const picker = document.createElement("select");
      picker.className = "docsViewerBook__sectionPicker";
      picker.setAttribute("aria-label", "Book contents");
      const sidebar = document.createElement("div");
      sidebar.className = "docsViewerBook__sidebar";
      const actions = document.createElement("div");
      actions.className = "docsViewerReport__toolbar";
      actions.setAttribute("role", "group");
      actions.setAttribute("aria-label", "Book heading actions");
      function actionIcon(label, artwork, run) {
        const control = button(document, label, run);
        control.className = "docsViewer__toolbarIconButton";
        control.title = label;
        control.setAttribute("aria-label", label);
        control.replaceChildren(createDocsViewerToolbarIcon(document, artwork));
        return control;
      }
      const reportError = error => options.setStatus?.(error.message, true);
      const unfiled = actionIcon("Unfiled", "docsViewerBook__icon--file-question-mark", () => choose(""));
      const edit = actionIcon("Edit section…", "docsViewer__icon--pen", () => editHeading().catch(reportError));
      actions.append(
        unfiled,
        actionIcon("New section…", "docsViewer__icon--file-plus-corner", () => addHeading(false).catch(reportError)),
        actionIcon("New part…", "docsViewerBook__icon--folder-plus", () => addHeading(true).catch(reportError)),
        edit
      );
      sidebar.append(actions, list, picker);
      const body = document.createElement("div");
      body.className = "docsViewerBook__documents";
      body.append(...root.childNodes);
      root.replaceChildren(sidebar, body);
      root.classList.add("docsViewerBook__layout");

      const closedParts = new Set();
      const headingControls = new Map();
      let browsingLocked = false;
      function selected(id) {
        const previous = headingControls.get(headingId)?.control;
        previous?.classList.remove("is-active");
        previous?.removeAttribute("aria-current");
        const current = headingControls.get(id);
        headingId = current ? id : "";
        if (current) {
          current.control.classList.add("is-active");
          current.control.setAttribute("aria-current", "true");
          current.reveal?.();
        }
        unfiled.classList.toggle("is-active", !current);
        unfiled.setAttribute("aria-pressed", String(!current));
        edit.disabled = browsingLocked || !current;
        edit.title = current?.node.sections ? "Edit part…" : "Edit section…";
        edit.setAttribute("aria-label", edit.title);
        root.dataset.bookHeadingActive = String(Boolean(current));
        picker.value = headingId;
      }
      function choose(id) {
        selected(id);
        change();
      }
      function treeList(child = false) {
        const headings = document.createElement("ul");
        headings.className = child ? "docsViewer__navList docsViewer__navList--child" : "docsViewer__navList";
        return headings;
      }
      function heading(node, reveal) {
        const item = document.createElement("li");
        item.className = "docsViewer__navItem";
        const row = document.createElement("div");
        row.className = "docsViewer__navRow";
        const control = button(document, node.title, () => choose(node.id));
        control.className = "docsViewer__navLink";
        control.disabled = browsingLocked;
        headingControls.set(node.id, { control, node, reveal });
        item.append(row);
        if (node.sections?.length) {
          const children = treeList(true);
          const toggle = button(document, "", () => setExpanded(children.hidden));
          toggle.className = "docsViewer__toggle";
          function setExpanded(expanded) {
            children.hidden = !expanded;
            toggle.textContent = expanded ? "▼" : "►";
            toggle.setAttribute("aria-expanded", String(expanded));
            toggle.setAttribute("aria-label", (expanded ? "Collapse " : "Expand ") + node.title);
            if (expanded) closedParts.delete(node.id);
            else closedParts.add(node.id);
          }
          children.append(...node.sections.map(section => heading(section, () => setExpanded(true))));
          setExpanded(!closedParts.has(node.id));
          row.append(toggle);
          item.append(children);
        } else {
          const spacer = document.createElement("span");
          spacer.className = "docsViewer__toggleSpacer";
          spacer.setAttribute("aria-hidden", "true");
          row.append(spacer);
        }
        row.append(control);
        return item;
      }
      function renderHeadings() {
        headingControls.clear();
        const headings = treeList();
        for (const node of tree) headings.append(heading(node));
        list.replaceChildren(headings);
        picker.innerHTML = option("", "Unfiled") + headingOptions(tree);
      }
      picker.addEventListener("change", () => choose(picker.value));
      navigation = { rows, choose, redraw(id) {
        renderHeadings();
        choose(id);
      } };
      renderHeadings();
      selected(headingId);
      return {
        selected: () => headingId,
        restore: selected,
        setBrowsingLocked(locked) {
          if (browsingLocked === locked) return;
          browsingLocked = locked;
          picker.disabled = locked;
          for (const control of actions.children) control.disabled = locked;
          edit.disabled = locked || !headingId;
          for (const { control } of headingControls.values()) control.disabled = locked;
        },
        readingRows() {
          return headingControls.get(headingId)?.node.doc_ids.map(rowForId).filter(Boolean);
        },
        project(matches) {
          const current = headingControls.get(headingId)?.node;
          if (!current) {
            const placed = new Set(bookHeadings(tree).flatMap(node => node.doc_ids));
            return matches.filter(row => !placed.has(row.docId));
          }
          const byId = new Map(matches.map(row => [row.docId, row]));
          return current.doc_ids.map(id => byId.get(id)).filter(Boolean);
        }
      };
    } } : {})
  };
}
