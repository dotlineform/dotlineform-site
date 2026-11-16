import { fetchManagementJson } from "./docs-viewer-management-client.js";
import { escapeHtml, openDocsViewerManagementModal } from "./docs-viewer-management-modal-shell.js";
import { openDocsViewerPositionModal } from "./docs-viewer-position-modal.js";
import { collectionSequenceForLink, registerCollectionNavigationLink } from "../shared/docs-viewer-collection-navigation.js";
import { createDocsViewerToolbarIcon } from "../shared/docs-viewer-toolbar-icon.js";
import { bookHeadings, isBookMatter } from "./docs-viewer-book-manifest.js";

const editionLabels = { both: "Both", web: "Web only", export: "Export only" };

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

function createBookRowSelection(options, { projectPosition, clearHeading }) {
  let selectedId = "";
  let selectedRow = null;
  const visibleRows = new Map();
  let run;
  let enabled = false;
  let checkedIds = null;

  function positionIds() {
    if (!enabled) return [];
    return checkedIds ?? (selectedId ? [selectedId] : []);
  }

  function project() {
    if (selectedRow) {
      if (checkedIds) selectedRow.link.removeAttribute("aria-current");
      else selectedRow.link.setAttribute("aria-current", "true");
    }
    projectPosition(positionIds().length > 0);
  }

  function select(id) {
    const row = visibleRows.get(id);
    if (selectedId === id && selectedRow === row) return;
    selectedRow?.link.removeAttribute("aria-current");
    selectedId = id;
    selectedRow = row;
    project();
  }

  function open(row, action) {
    row.link.focus({ preventScroll: true });
    const target = { doc_id: row.record.doc_id };
    if (target.doc_id !== options.collectionConfig.reportHostDocId) {
      target.collection = options.collectionConfig.collection;
    }
    return action(target, {
      collectionSequence: collectionSequenceForLink(row.link)
    });
  }

  return {
    prepare(runAction) {
      visibleRows.clear();
      selectedRow = null;
      run = runAction;
    },
    bindRow(link, record, toggleChecked) {
      const row = { link, record };
      visibleRows.set(record.doc_id, row);
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
        clearHeading();
        if (event.altKey) {
          // Let the shared reader handle a source link on the title itself.
          if (link.contains(event.target)) return;
          open(row, options.openSourceFromLink);
          return;
        }
        event.preventDefault();
        if (checkedIds && toggleChecked && event.detail !== 0) {
          link.focus({ preventScroll: true });
          toggleChecked();
          return;
        }
        run(() => open(row, options.openDocument));
      });
      link.addEventListener("keydown", event => {
        if (event.key !== " " || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
        event.preventDefault();
        if (!enabled) return;
        clearHeading();
        if (checkedIds && toggleChecked) toggleChecked();
        else run(() => open(row, options.openDocument));
      });
    },
    capture: () => selectedId,
    restore(id) { select(id || ""); },
    positionIds,
    project(canInteract, checked) {
      enabled = canInteract;
      checkedIds = checked;
      project();
    }
  };
}

export async function openBookLibrarySources({ book, chapter, clientOptions, root, button, readBookManifest, startBusyOperation, commitDocumentChange }) {
  const client = { ...clientOptions, cache: "no-store" };
  const manifest = await readBookManifest(book);
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
          collection: book.collection, doc_id: chapter.doc_id, library_sources: librarySources
        }, client);
      } finally {
        stop();
      }
    }
  });
  if (!result.ok) return;
  const failures = commitDocumentChange({
    target: { collection: book.collection, doc_id: chapter.doc_id },
    record: { ...chapter, library_sources: result.library_sources }
  });
  if (failures?.length) {
    throw new Error("Library sources saved. Could not update retained views. " + failures.map(error => error.message).join(" "));
  }
}

async function saveBookChanges(payload, options, applyOrder) {
  const stop = options.startBusyOperation();
  let result;
  let failure;
  try {
    try {
      result = await fetchManagementJson("/docs/book/tree", "POST", payload, options.clientOptions);
    } catch (error) {
      if (!error.payload?.book_order && !error.payload?.records?.length) throw error;
      result = error.payload;
      failure = error;
    }
    if (result.book_order) applyOrder?.(result.book_order, !result.records?.length);
    const errors = options.commitBookToc(result.book_toc);
    for (const record of result.records || []) {
      errors.push(...options.commitDocumentChange({ target: { collection: payload.collection, doc_id: record.doc_id }, record }));
    }
    if (errors.length) {
      throw new Error((failure?.message || "Book changes saved.") + " Could not update the open Book. "
        + errors.map(error => error.message).join(" "));
    }
    if (failure) throw failure;
  } finally {
    stop();
  }
}

export function openBookEdition({ target, manifest, ...options }) {
  const saved = manifest.docs.find(row => row.doc_id === target.doc_id).book_edition || "both";
  return openDocsViewerManagementModal({
    root: options.root,
    title: "Edition",
    restoreFocus: () => options.root.querySelector("#docsViewerManageEditButton"),
    bodyHtml: field("Include in", '<select class="docsViewer__fieldInput" data-book-edition>'
      + Object.entries(editionLabels).map(([value, label]) => option(value, label)).join("") + "</select>"),
    focusSelector: "[data-book-edition]",
    actions: [{ role: "modal-primary", label: "Save" }, { role: "modal-cancel", label: "Cancel" }],
    onOpen({ host }) { host.querySelector("[data-book-edition]").value = saved; },
    onSubmit({ host }) {
      const edition = host.querySelector("[data-book-edition]").value;
      if (edition !== saved) return saveBookChanges({ ...target, book_edition: edition }, options);
    }
  });
}

export async function createBookReportTools(options) {
  const collection = options.collectionConfig.collection;
  const isBook = options.collectionConfig.collectionType === "curated-book";
  const client = { ...options.clientOptions, cache: "no-store" };
  const get = path => fetchManagementJson(path, "GET", undefined, client);
  const post = async (path, payload) => {
    const stop = options.startBusyOperation?.();
    try {
      return await fetchManagementJson(path, "POST", payload, client);
    } finally {
      stop?.();
    }
  };
  const manifest = options.bookManifest;
  const bookOrder = manifest?.book_order;
  const hostId = options.collectionConfig.reportHostDocId;
  const tocRow = { docId: hostId, title: "Table of contents", href: "?doc=" + encodeURIComponent(hostId) };
  const copied = new Set(isBook ? [] : (await get("/docs/book/copied")).doc_ids);
  let navigation;
  let headingId = "";
  let mode = "tree";
  let positionButton;
  let toolbarActions;
  const rowSelection = isBook ? createBookRowSelection(options, {
    projectPosition(canPosition) {
      if (positionButton) positionButton.disabled = !canPosition;
    },
    clearHeading() {
      if (headingId) navigation.choose("");
    }
  }) : null;

  function modal(title, bodyHtml, onSubmit, onOpen, primaryLabel = "Save") {
    return openDocsViewerManagementModal({
      root: options.root, title, bodyHtml, onSubmit, onOpen,
      focusSelector: "select, input",
      actions: [{ role: "modal-primary", label: primaryLabel }, { role: "modal-cancel", label: "Cancel" }]
    });
  }

  function commit(destination, record, sectionId) {
    return options.commitDocumentChange?.({
      target: { collection: destination, doc_id: record.doc_id }, record, book_heading_id: sectionId
    }) || [];
  }

  async function copySelection(docIds, renderList) {
    const books = options.books;
    const loadedBooks = new Map();
    async function loadBook(book) {
      const { book_order, docs } = await options.readBookManifest(book);
      const data = {
        tree: book_order.tree,
        sections: new Map(bookHeadings(book_order.tree).filter(node => !node.sections).map(node => [node.id, node])),
        chapters: docs.filter(row => !row.copied_from_library).sort((a, b) => a.title.localeCompare(b.title))
      };
      loadedBooks.set(book.collection, data);
      return data;
    }
    if (books.length === 1) await loadBook(books[0]);

    const bookField = field("Book", '<select class="docsViewer__fieldInput" data-book-destination>'
      + (books.length === 1 ? "" : option("", "Choose a book"))
      + books.map(book => option(book.collection, book.title)).join("") + "</select>");
    const sectionField = field("Placement", '<select class="docsViewer__fieldInput" data-book-section>'
      + option("", "Choose a book first") + "</select>");
    const newChapter = '<div class="docsViewer__fieldGroup">'
      + chapterCopyCheckbox("data-book-new", "Add to a new chapter")
      + field("Chapter title", '<input class="docsViewer__fieldInput" data-book-title type="text" autocomplete="off" disabled>')
      + "</div>";
    const existingChapter = '<div class="docsViewer__fieldGroup">'
      + chapterCopyCheckbox("data-book-existing", "Add to an existing chapter")
      + field("Chapter", '<select class="docsViewer__fieldInput" data-book-chapter disabled></select>')
      + "</div>";
    let controls;
    let destination;
    let sections;
    async function selectBook({ setBusy, setStatus }, book) {
      destination = undefined;
      setStatus("");
      let data = book && loadedBooks.get(book.collection);
      if (book && !data) {
        setBusy(true);
        try {
          data = await loadBook(book);
        } catch (error) {
          setStatus(error.message);
        } finally {
          setBusy(false);
        }
      }
      if (data) {
        destination = book;
        sections = data.sections;
        controls.section.innerHTML = option("", "Root") + sectionOptions(data.tree);
        controls.chapter.innerHTML = option("", data.chapters.length ? "Choose a chapter" : "No chapters in this book")
          + data.chapters.map(row => option(row.doc_id, row.title)).join("");
      } else {
        controls.section.innerHTML = option("", "Choose a book first");
        controls.chapter.innerHTML = option("", "Choose a book first");
      }
      controls.section.disabled = !destination;
      controls.chapter.disabled = !destination || !controls.addExisting.checked;
      controls.copy.disabled = !destination;
    }
    const result = await modal("Copy to Book", bookField + sectionField + newChapter + existingChapter, () => {
      const sectionId = controls.section.value;
      const payload = { collection: destination.collection, doc_ids: docIds, section_id: sectionId };
      if (controls.addNew.checked) {
        payload.new_chapter_title = controls.title.value.trim();
        if (!payload.new_chapter_title) throw new Error("Enter a chapter title.");
      }
      if (controls.addExisting.checked) {
        payload.existing_chapter_id = controls.chapter.value;
        if (!payload.existing_chapter_id) throw new Error("Choose a chapter in the selected book.");
      }
      return post("/docs/book/copy", payload);
    }, api => {
      const { host } = api;
      const picker = host.querySelector("[data-book-destination]");
      controls = {
        section: host.querySelector("[data-book-section]"),
        addNew: host.querySelector("[data-book-new]"),
        addExisting: host.querySelector("[data-book-existing]"),
        title: host.querySelector("[data-book-title]"),
        chapter: host.querySelector("[data-book-chapter]"),
        copy: host.querySelector('[data-role="modal-primary"]')
      };
      const updateDestination = () => selectBook(api, books.find(book => book.collection === picker.value));
      picker.addEventListener("change", updateDestination);
      controls.addNew.addEventListener("change", () => {
        controls.title.disabled = !controls.addNew.checked;
      });
      controls.addExisting.addEventListener("change", () => {
        controls.chapter.disabled = !destination || !controls.addExisting.checked;
      });
      updateDestination();
    }, "Copy");
    if (!result.ok) return;
    result.copied_doc_ids.forEach(id => copied.add(id));
    const placements = new Set(result.placed_doc_ids);
    const failures = result.records.flatMap(record =>
      commit(destination.collection, record, placements.has(record.doc_id) ? result.section_id : undefined));
    renderList();
    const placement = result.section_id ? sections.get(result.section_id).title : "Root";
    const message = result.copied_doc_ids.length + " copied to " + destination.title + " / " + placement + ".";
    options.setStatus?.(failures.length
      ? message + " Could not update the retained Book list. " + failures.map(error => error.message).join(" ")
      : message, Boolean(failures.length));
  }

  async function clearCopyFlags(docIds, renderList) {
    await post("/docs/book/copied/clear", { doc_ids: docIds });
    docIds.forEach(id => copied.delete(id));
    renderList();
  }

  async function saveOrder(next, selected = headingId) {
    await saveBookChanges({ collection, book_order: next }, { ...options, clientOptions: client }, (order, redraw) => {
      Object.assign(bookOrder, order);
      if (redraw) navigation.redraw(selected);
      else navigation.choose(selected);
    });
  }

  async function addHeading(part) {
    const tree = bookOrder.tree;
    const body = field(part ? "Part title" : "Section title", '<input class="docsViewer__fieldInput" data-book-heading type="text" autocomplete="off">')
      + (!part && tree.some(node => node.sections)
        ? field("Part", '<select class="docsViewer__fieldInput" data-book-parent>' + option("", "Top level")
          + tree.filter(node => node.sections).map(node => option(node.id, node.title)).join("") + "</select>") : "");
    await modal(part ? "New part" : "New section", body, async ({ host }) => {
      const title = host.querySelector("[data-book-heading]").value.trim();
      if (!title) throw new Error("Enter a title.");
      const parentId = host.querySelector("[data-book-parent]")?.value;
      const next = structuredClone(bookOrder);
      const group = parentId ? next.tree.find(node => node.id === parentId).sections : next.tree;
      const node = { id: crypto.randomUUID(), title, doc_ids: [] };
      if (part) node.sections = [];
      group.push(node);
      await saveOrder(next, node.id);
    });
  }

  async function editHeading() {
    const tree = bookOrder.tree;
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
      const next = structuredClone(bookOrder);
      const from = oldPart ? next.tree.find(node => node.id === oldPart.id).sections : next.tree;
      const index = from.findIndex(node => node.id === selected.id);
      from[index].title = title;
      if (partId !== (oldPart?.id || "")) {
        const to = partId ? next.tree.find(node => node.id === partId).sections : next.tree;
        to.push(from.splice(index, 1)[0]);
      }
      await saveOrder(next);
    }, ({ host }) => {
      const picker = host.querySelector("[data-book-parent]");
      if (picker) picker.value = oldPart?.id || "";
    });
  }

  async function positionSelection(docIds) {
    const titles = new Map(manifest.docs.map(row => [row.doc_id, row.title]));
    titles.set(hostId, tocRow.title);
    const selected = new Set(docIds);
    const movingToc = selected.has(hostId);
    const resetsEdition = manifest.docs.some(row => selected.has(row.doc_id)
      && isBookMatter(bookOrder, row.doc_id) && editionLabels[row.book_edition] && row.book_edition !== "both");
    const inside = [
      { id: "@front", title: "Opening pages", depth: 0, headingId: "@front" },
      { id: "", title: "Root chapters", depth: 0, headingId: "" }
    ];
    const beside = [];
    function addDocuments(ids, depth, headingId) {
      for (const docId of ids) {
        if (selected.has(docId)) continue;
        beside.push({ id: "document:" + docId, title: titles.get(docId), depth, headingId, docId });
      }
    }
    function addDestinations(heading, depth) {
      const row = { id: "heading:" + heading.id, title: heading.title, depth, headingId: heading.id };
      inside.push(row);
      beside.push({ ...row, disabled: true });
      addDocuments(heading.doc_ids, depth + 1, heading.id);
    }
    addDocuments(bookOrder.front, 0, "@front");
    addDocuments(bookOrder.root, 0, "");
    for (const node of bookOrder.tree) {
      addDestinations(node, 0);
      for (const section of node.sections || []) addDestinations(section, 1);
    }
    inside.push({ id: "@back", title: "Back matter", depth: 0, headingId: "@back" });
    addDocuments(bookOrder.back, 0, "@back");
    const destinations = new Map([...beside, ...inside].map(row => [row.id, row]));
    await openDocsViewerPositionModal({
      root: options.root,
      title: "Book Position",
      note: docIds.length === 1 ? titles.get(docIds[0]) : docIds.length + " documents",
      insideLabel: "Inside (at end)",
      initialPlacement: "inside",
      getDestinations: placement => {
        const targets = placement === "inside" ? inside : beside;
        return movingToc ? targets.filter(target => target.headingId === "@front") : targets;
      },
      destinationNote: resetsEdition ? id => {
        const destination = destinations.get(id);
        return destination.headingId === "@front" || destination.headingId === "@back"
          ? "" : "Saving this move will set the edition to Both for pages that are Web only or Export only.";
      } : null,
      onSave: async (targetId, placement) => {
        const target = destinations.get(targetId);
        const next = structuredClone(bookOrder);
        let changed = false;
        const placements = [["@front", next.front], ["", next.root],
          ...bookHeadings(next.tree).map(node => [node.id, node.doc_ids]), ["@back", next.back]];
        for (const [id, previous] of placements) {
          const ordered = previous.filter(id => !selected.has(id));
          if (id === target.headingId) {
            if (placement === "inside") ordered.push(...docIds);
            else ordered.splice(ordered.indexOf(target.docId) + Number(placement === "after"), 0, ...docIds);
          }
          if (ordered.length !== previous.length || ordered.some((id, index) => id !== previous[index])) {
            previous.splice(0, previous.length, ...ordered);
            changed = true;
          }
        }
        if (changed) await saveOrder(next, target.headingId);
        else if (target.headingId !== headingId) navigation.choose(target.headingId);
      }
    });
  }

  return {
    rowSelection,
    newDocumentHeading: isBook ? () => mode === "tree" ? headingId : "" : null,
    readManifest: isBook ? () => Promise.resolve(manifest) : null,
    editionSuffix({ doc_id: docId, book_edition: edition }) {
      return isBook && edition && edition !== "both" && isBookMatter(bookOrder, docId) ? editionLabels[edition] : "";
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
      if (isBook) return null;
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
      if (options.books.length) add("copy", "Copy to Book…", () => copySelection(controls.ids, renderList), "docsViewer__icon--dlf-doc");
      add("clearCopied", "Clear Copied to Book", () => clearCopyFlags(controls.flaggedIds, renderList), "docsViewer__icon--dlf-doc");
      controls.clearCopied.classList.add("docsViewerBook__clearCopyFlag");
      return controls;
    },
    projectSelection(controls, ids) {
      controls.ids = ids;
      if (controls.copy) controls.copy.hidden = !ids.length;
      controls.flaggedIds = ids.filter(id => copied.has(id));
      controls.clearCopied.hidden = !controls.flaggedIds.length;
    },
    ...(isBook ? { mountListActions(selectButton, selectionControl, actionsHost) {
      toolbarActions.prepend(selectButton, selectionControl, actionsHost);
    }, mountSectionNavigation({ root, rowForId, change }) {
      const document = root.ownerDocument;
      const toolbar = document.createElement("div");
      toolbar.className = "docsViewerBook__viewControls";
      const viewControls = document.createElement("div");
      viewControls.className = "docsViewerBook__modes";
      viewControls.setAttribute("role", "group");
      viewControls.setAttribute("aria-label", "Book view");
      const viewToggle = button(document, "", toggleMode);
      viewToggle.className = "docsViewer__toolbarIconButton";
      const viewIcon = createDocsViewerToolbarIcon(document, "docsViewerBook__icon--list-tree");
      viewToggle.append(viewIcon);
      viewControls.append(viewToggle);

      const headingActions = document.createElement("div");
      headingActions.className = "docsViewerReport__toolbar";
      headingActions.setAttribute("role", "group");
      headingActions.setAttribute("aria-label", "Book heading actions");
      function actionIcon(label, artwork, run) {
        const control = button(document, label, () => run().catch(error => options.setStatus(error.message, true)));
        control.className = "docsViewer__toolbarIconButton";
        control.title = label;
        control.setAttribute("aria-label", label);
        control.replaceChildren(createDocsViewerToolbarIcon(document, artwork));
        return control;
      }
      positionButton = actionIcon("Position…", "docsViewer__icon--arrow-up-down",
        () => positionSelection(rowSelection.positionIds()));
      positionButton.disabled = !rowSelection.positionIds().length;
      viewControls.append(positionButton);
      const edit = actionIcon("Edit heading…", "docsViewer__icon--pen", editHeading);
      headingActions.append(
        actionIcon("New section…", "docsViewer__icon--file-plus-corner", () => addHeading(false)),
        actionIcon("New part…", "docsViewerBook__icon--folder-plus", () => addHeading(true)),
        edit
      );
      toolbarActions = document.createElement("div");
      toolbarActions.className = "docsViewerBook__toolbarActions";
      if (options.expandControl) toolbarActions.append(options.expandControl);
      toolbar.append(viewControls, headingActions, toolbarActions);
      root.prepend(toolbar);

      let browsingLocked = false;
      let headingControls = new Map();
      let matchesById;
      function projectControls() {
        root.dataset.bookMode = mode;
        const tree = mode === "tree";
        viewIcon.classList.toggle("docsViewer__icon--list", tree);
        viewIcon.classList.toggle("docsViewerBook__icon--list-tree", !tree);
        const label = tree ? "Show List view" : "Show Tree view";
        viewToggle.title = label;
        viewToggle.setAttribute("aria-label", label);
        viewToggle.disabled = browsingLocked;
        headingActions.hidden = !tree || browsingLocked;
        edit.disabled = browsingLocked || !headingId || headingId.startsWith("@");
      }
      function toggleMode() {
        mode = mode === "tree" ? "list" : "tree";
        projectControls();
        change();
      }
      function choose(id) {
        headingControls.get(headingId)?.setAttribute("aria-pressed", "false");
        headingId = id;
        headingControls.get(headingId)?.setAttribute("aria-pressed", "true");
        projectControls();
      }
      function readingIds() {
        return [...bookOrder.front, ...bookOrder.root, ...bookHeadings(bookOrder.tree).flatMap(node => node.doc_ids), ...bookOrder.back];
      }
      function readingRows() {
        return readingIds().map(id => id === hostId ? tocRow : rowForId(id)).filter(Boolean);
      }
      function renderTree(host, filtering, appendRow) {
        headingControls = new Map();
        function renderBranch(parent, id, title, docIds, sections) {
          const item = document.createElement("li");
          item.className = "docsViewerBook__branch";
          const body = document.createElement("ul");
          body.className = "docsViewerReport__rows docsViewerBook__branchRows";
          for (const docId of docIds) {
            const row = matchesById.get(docId);
            if (row) appendRow(row, body);
            else if (docId === hostId && !filtering) {
              const item = document.createElement("li");
              item.className = "docsViewerReport__row";
              const link = document.createElement("a");
              link.className = "docsViewerReport__cellLink docsViewerReport__collectionButton";
              link.href = tocRow.href;
              link.textContent = tocRow.title;
              registerCollectionNavigationLink(link, () => {
                const rows = readingRows();
                return { rows, position: rows.indexOf(tocRow) };
              });
              item.append(link);
              rowSelection.bindRow(link, { doc_id: hostId });
              body.append(item);
            }
          }
          for (const section of sections ?? []) renderBranch(body, section.id, section.title, section.doc_ids);
          if (filtering && !body.childElementCount) return;
          if (title !== null) {
            const control = button(document, title, () => choose(id));
            control.className = "docsViewerBook__heading";
            if (sections) control.classList.add("docsViewerBook__heading--part");
            control.disabled = browsingLocked;
            control.setAttribute("aria-pressed", String(id === headingId));
            headingControls.set(id, control);
            item.append(control);
          }
          item.append(body);
          parent.appendChild(item);
        }
        renderBranch(host, "@front", "Opening pages", bookOrder.front);
        if (bookOrder.root.length) renderBranch(host, "", null, bookOrder.root);
        for (const node of bookOrder.tree) renderBranch(host, node.id, node.title, node.doc_ids, node.sections);
        renderBranch(host, "@back", "Back matter", bookOrder.back);
        return Boolean(host.childElementCount);
      }

      navigation = { choose, redraw(id) {
        choose(id);
        change();
      } };
      projectControls();
      return {
        selected: () => ({ mode, headingId }),
        restore(saved) {
          if (!saved) return;
          mode = saved.mode;
          choose(saved.headingId);
        },
        setBrowsingLocked(locked) {
          if (browsingLocked === locked) return;
          browsingLocked = locked;
          projectControls();
          for (const control of headingControls.values()) control.disabled = locked;
        },
        readingRows,
        project(matches) {
          if (mode === "list") return matches;
          matchesById = new Map(matches.map(row => [row.docId, row]));
          return readingIds().map(id => matchesById.get(id)).filter(Boolean);
        },
        renderTree(host, filtering, appendRow) {
          return mode === "tree" && renderTree(host, filtering, appendRow);
        },
        usesTreeRows: () => mode === "tree"
      };
    } } : {})
  };
}
