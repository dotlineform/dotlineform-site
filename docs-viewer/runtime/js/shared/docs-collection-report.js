import { mountSearchField } from "/shared/frontend/js/search-field.js";
import { createDocsViewerToolbarIcon } from "./docs-viewer-toolbar-icon.js";
import { registerCollectionNavigationLink } from "./docs-viewer-collection-navigation.js";
import { createDocsCollectionReportState } from "./docs-collection-report-state.js";
import { fetchDocsCollectionManifest, fetchSelectedDocumentRows } from "./docs-viewer-data.js";
import { normalizeDocsCollectionFilterValue } from "./docs-collection-report-filter.js";
import {
  CATALOGUE_DISCOVERY_SIZE,
  COLLECTION_PAGE_SIZE,
  COLLECTION_SEARCH_DELAY_MS,
  appendCollectionThumbnail,
  catalogueDiscoveryRows,
  catalogueRandomIndex,
  catalogueShuffleFileOrder,
  createCatalogueGallerySearch,
  createCollectionBrowsingData,
  createCollectionPager,
  loadCatalogueCollectionThumbnailSettings,
  savedCatalogueDiscovery,
  shuffleCatalogueWorks
} from "./docs-collection-browsing.js";
import { catalogueDiscoveryMediaPresentation } from "./docs-viewer-catalogue-media.js";

const CATALOGUE_DEFAULT_SORT = "last-updated-desc";
const CATALOGUE_LIST_SIZE = 64;
const CATALOGUE_DISCOVERY_COLUMNS = 8;
const CATALOGUE_GALLERY_WIDTH = CATALOGUE_DISCOVERY_COLUMNS * 64 + (CATALOGUE_DISCOVERY_COLUMNS - 1) * 8;

/**
 * Optional caller-owned composition for one shared collection report.
 *
 * Render callbacks receive detached hosts that enter the document only when
 * populated. `notify` receives explicit collection-scoped mount, state,
 * complete-inventory IDs and unmount events.
 * Manage supplies its local list controller; public browsing has no edit or
 * selection bookkeeping. Document navigation belongs to the shared reader.
 *
 * @typedef {Object} DocsCollectionReportContribution
 * @property {function(Object): void} [notify]
 * @property {function(Object): (Object|void)} [renderRow]
 * @property {function(Object): void} [renderListToolbar]
 * @property {function(): *} [captureListState] Optional JSON-safe list restoration state.
 * @property {function(*): void} [restoreListState] Restore a previously captured caller state.
 * @property {function(Object): Object} createListManagement Manage-owned data, updates and refresh.
 * @property {boolean} [paginationDefault] Caller-owned initial pagination choice.
 * @property {function(Object): Object} [mountPaginationControl] Local control over shared pagination state.
 * @property {function(Object): Object} [mountCatalogueSearchCopy] Manage-only copy control for the Catalogue query.
 */

var filterIdSequence = 0;

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function clearNode(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function contributionCallback(contribution, name) {
  return contribution && typeof contribution[name] === "function"
    ? contribution[name]
    : null;
}

function collectionId(record) {
  return record.collection;
}

function collectionTitle(record) {
  return record.title;
}

/** Select shared capabilities independently of the current page-display choice. */
function collectionBrowsingFeatures(collection) {
  var boundedBrowsing = ["catalogue", "works"].includes(collection.collection)
    || collection.collectionType === "book-collection";
  return { pagination: boundedBrowsing, delayedSearch: boundedBrowsing, filterToolbarSort: boundedBrowsing };
}

function collectionItemsLabel(collection) {
  return collectionId(collection) === "works" ? "documents" : collectionTitle(collection);
}

function collectionTarget(collection) {
  return {
    collection: collection
  };
}

function contributionEvent(context, collectionIdValue, detail) {
  var contribution = context && context.resolvedCollectionReportContribution;
  var notify = contributionCallback(contribution, "notify");
  if (!notify) return;
  notify(Object.assign({
    access: context && context.managementContext ? "manage" : "public",
    collection: collectionTarget(collectionIdValue)
  }, detail || {}));
}

function notifyContribution(state, detail) {
  var notify = contributionCallback(state.contribution, "notify");
  if (!notify) return;
  notify(Object.assign({
    access: state.managementContext ? "manage" : "public",
    collection: collectionTarget(state.collectionId)
  }, detail || {}));
}

function collectionSequenceForRow(state, docId) {
  if (!state.readingRows) {
    var rows = state.sectionNavigation ? state.sectionNavigation.readingRows()
      : state.pinnedMatches ? state.pinnedMatches.concat(state.matches) : state.documentMatches;
    state.readingRows = rows ? rows.map(({ docId, href, title }) => ({ docId, href, title })) : [];
  }
  if (state.readingRows.length < 2) return;
  var position = state.readingRows.findIndex(row => row.docId === docId);
  if (position >= 0) return { rows: state.readingRows, position: position };
}

function appendDocRow(state, doc, reserveThumbnailSpace, rowsNode, thumbnailLoading) {
  var item = createDocRow(doc, reserveThumbnailSpace, thumbnailLoading);
  registerCollectionNavigationLink(item.link, function () { return collectionSequenceForRow(state, doc.docId); });
  if (catalogueDiscoveryActive(state)) rememberDiscoveryLinkFocus(item.link);
  contributeDocRow(state, item, doc);
  rowsNode.appendChild(item.row);
  return item;
}

function rememberDiscoveryLinkFocus(link) {
  link.addEventListener("click", event => {
    if (event.button === 0 && !event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey) {
      link.focus({ preventScroll: true });
    }
  });
}

function createDocRow(doc, reserveThumbnailSpace, thumbnailLoading) {
  var docId = doc.docId;
  var row = document.createElement("li");
  row.className = "docsViewerReport__row";
  row.dataset.reportSubdocId = docId;

  var leadingHost = document.createElement("span");
  leadingHost.className = "docsViewerReport__rowContribution docsViewerReport__rowContribution--leading";
  leadingHost.dataset.reportContributionHost = "row-leading";

  var title = document.createElement("a");
  title.className = "docsViewerReport__cellLink docsViewerReport__collectionButton";
  title.href = doc.href;
  if (reserveThumbnailSpace) appendCollectionThumbnail(title, doc.workThumbnail?.src || doc.thumbnailSrc || undefined,
    thumbnailLoading);

  var titlePrefixHost = document.createElement("span");
  titlePrefixHost.className = "docsViewerReport__rowContribution docsViewerReport__rowContribution--titlePrefix";
  titlePrefixHost.dataset.reportContributionHost = "title-prefix";

  var titleText = document.createElement("span");
  titleText.className = "docsViewerReport__title";
  titleText.textContent = doc.title;

  var trailingHost = document.createElement("span");
  trailingHost.className = "docsViewerReport__rowContribution docsViewerReport__rowContribution--trailing";
  trailingHost.dataset.reportContributionHost = "row-trailing";

  title.appendChild(titleText);
  row.append(title);
  return { row, link: title, titleText, leadingHost, titlePrefixHost, trailingHost, hasLeadingContent: false };
}

function contributeDocRow(state, item, doc) {
  var { row, link, titleText, leadingHost, titlePrefixHost, trailingHost } = item;
  leadingHost.replaceChildren();
  titlePrefixHost.replaceChildren();
  trailingHost.replaceChildren();
  var renderRow = contributionCallback(state.contribution, "renderRow");
  var rowResult = renderRow ? renderRow({
    collection: collectionTarget(state.collectionId),
    document: doc.record,
    leadingHost: leadingHost,
    titlePrefixHost: titlePrefixHost,
    trailingHost: trailingHost
  }) : null;
  if (titlePrefixHost.childNodes.length) link.insertBefore(titlePrefixHost, titleText);
  var accessibleLabels = rowResult && Array.isArray(rowResult.accessibleLabels)
    ? rowResult.accessibleLabels.map(cleanString).filter(Boolean)
    : [];
  if (accessibleLabels.length) {
    link.setAttribute("aria-label", [titleText.textContent].concat(accessibleLabels).join(", "));
  }
  item.hasLeadingContent = leadingHost.childNodes.length > 0;
  if (item.hasLeadingContent) row.prepend(leadingHost);
  if (trailingHost.childNodes.length) row.appendChild(trailingHost);
}

function appendGalleryRow(state, gallery) {
  var row = document.createElement("li");
  row.className = "docsViewerReport__row docsViewerReport__galleryRow";
  var button = document.createElement("button");
  button.type = "button";
  button.className = "docsViewerReport__collectionButton docsViewerReport__galleryButton";
  var title = document.createElement("strong");
  title.textContent = gallery.title;
  button.append(createDocsViewerToolbarIcon(document, "docsViewerReport__galleryIcon"), title);
  var label = "Open Gallery " + gallery.title;
  if (gallery.marker) {
    var marker = createDocsViewerToolbarIcon(document, "docsViewerReport__galleryMarker");
    marker.dataset.marker = gallery.marker;
    button.appendChild(marker);
  }
  if (gallery.description) {
    var description = document.createElement("span");
    description.className = "docsViewerReport__galleryDescription";
    description.textContent = gallery.description;
    button.appendChild(description);
    label += ", " + gallery.description;
  }
  if (gallery.matchCount) {
    var count = document.createElement("span");
    count.className = "docsViewerReport__galleryMatchCount";
    count.textContent = gallery.matchCount + (gallery.matchCount === 1 ? " matching work" : " matching works");
    button.appendChild(count);
    label += ", " + count.textContent;
  }
  button.setAttribute("aria-label", label);
  button.addEventListener("click", async function () {
    var isCurrent = function () { return state.mounted && state.rowsNode.contains(button); };
    state.statusNode.textContent = "";
    state.statusNode.hidden = true;
    button.disabled = true;
    button.setAttribute("aria-busy", "true");
    try {
      await state.openMediaTarget({
        mediaTarget: { kind: "catalogue-gallery", id: gallery.galleryId },
        invocationControl: button,
        documentTarget: { docId: state.parentDocId },
        isCurrentDocument: isCurrent
      });
    } catch (error) {
      if (isCurrent()) {
        state.statusNode.textContent = error.message || "Gallery could not open.";
        state.statusNode.hidden = false;
      }
    } finally {
      button.disabled = false;
      button.removeAttribute("aria-busy");
    }
  });
  row.appendChild(button);
  state.rowsNode.appendChild(row);
}

function renderFilterShell(context, collection) {
  var toolbar = document.createElement("div");
  toolbar.className = "docsViewerReport__toolbar docsViewerReport__collectionFilterToolbar";
  toolbar.dataset.docsCollectionFilters = "true";
  filterIdSequence += 1;
  var searchId = "docs-collection-title-filter-" + collectionId(collection) + "-" + filterIdSequence;
  var searchLabel = document.createElement("label");
  searchLabel.className = "docsViewerReport__selectLabel visually-hidden";
  searchLabel.htmlFor = searchId;
  searchLabel.textContent = collectionId(collection) === "catalogue"
    ? "Filter Works and Galleries by title or Work ID" : "Filter " + collectionItemsLabel(collection) + " by title";

  var search = document.createElement("span");
  search.className = "docsViewerReport__search";
  var input = document.createElement("input");
  input.className = "docsViewerReport__searchInput";
  input.id = searchId;
  input.type = "search";
  input.autocomplete = "off";
  input.spellcheck = false;
  input.placeholder = ({ catalogue: "work or gallery", concepts: "concept", moments: "moment", works: "title" })[collectionId(collection)] || "search";

  search.appendChild(input);
  var clear = mountSearchField(input).clearButton;

  toolbar.appendChild(searchLabel);
  toolbar.appendChild(search);
  return {
    clearNode: clear,
    inputNode: input,
    toolbarNode: toolbar
  };
}

function renderShell(context, collection, features) {
  var root = context.reportRoot;
  clearNode(root);
  root.dataset.reportColumns = "1";
  root.dataset.reportCollection = collectionId(collection);

  var filters = renderFilterShell(context, collection);
  var status = document.createElement("p");
  status.className = "docsViewerReport__status visually-hidden";
  status.setAttribute("aria-live", "polite");
  status.setAttribute("role", "status");
  status.hidden = Boolean(context.managementContext);

  var table = document.createElement("div");
  table.className = "docsViewerReport__table";

  var pinnedRows = null;
  if (collection.pinStarredDocuments) {
    pinnedRows = document.createElement("ul");
    pinnedRows.className = "docsViewerReport__rows docsViewerReport__pinnedRows";
    pinnedRows.setAttribute("aria-label", "Starred documents");
    table.appendChild(pinnedRows);
  }

  var rows = document.createElement("ul");
  rows.className = "docsViewerReport__rows";
  rows.setAttribute("aria-label", collectionItemsLabel(collection));

  table.appendChild(rows);
  root.appendChild(filters.toolbarNode);
  root.appendChild(status);
  root.appendChild(table);

  var shuffle = null;
  var discoveryMedia = null;
  var resetDiscoveryList = null;
  var discoveryGrid = null;
  var galleryToggle = null;
  if (collectionId(collection) === "catalogue") {
    status.classList.remove("visually-hidden");
    shuffle = document.createElement("button");
    shuffle.type = "button";
    shuffle.className = "docsViewer__toolbarIconButton";
    shuffle.title = "Shuffle";
    shuffle.setAttribute("aria-label", shuffle.title);
    shuffle.appendChild(createDocsViewerToolbarIcon(shuffle.ownerDocument, "docsViewer__icon--dices"));
    filters.toolbarNode.appendChild(shuffle);
    galleryToggle = document.createElement("button");
    galleryToggle.type = "button";
    galleryToggle.className = "docsViewer__toolbarIconButton";
    galleryToggle.title = "Switch to Gallery view";
    galleryToggle.setAttribute("aria-label", galleryToggle.title);
    galleryToggle.appendChild(createDocsViewerToolbarIcon(document, "docsViewer__icon--layout-grid"));
    filters.toolbarNode.appendChild(galleryToggle);
    resetDiscoveryList = document.createElement("button");
    resetDiscoveryList.type = "button";
    resetDiscoveryList.className = "docsViewer__toolbarIconButton";
    resetDiscoveryList.title = "Reset to default order";
    resetDiscoveryList.setAttribute("aria-label", resetDiscoveryList.title);
    resetDiscoveryList.appendChild(createDocsViewerToolbarIcon(document, "docsViewer__icon--clock-3"));
    filters.toolbarNode.appendChild(resetDiscoveryList);
    discoveryGrid = document.createElement("div");
    discoveryGrid.className = "docsViewerReport__discoveryGrid";
    discoveryGrid.setAttribute("role", "group");
    discoveryGrid.hidden = true;
    table.appendChild(discoveryGrid);
    if (typeof context.openMediaPresentation === "function") {
      discoveryMedia = document.createElement("button");
      discoveryMedia.type = "button";
      discoveryMedia.className = "docsViewer__toolbarIconButton";
      discoveryMedia.title = "Open selection in Media View";
      discoveryMedia.setAttribute("aria-label", discoveryMedia.title);
      discoveryMedia.appendChild(createDocsViewerToolbarIcon(document, "docsViewer__icon--images"));
      filters.toolbarNode.appendChild(discoveryMedia);
    }
  }
  var collectionSort = null;
  if (context.managementContext && features.filterToolbarSort) {
    collectionSort = document.createElement("button");
    collectionSort.type = "button";
    collectionSort.className = "docsViewer__toolbarIconButton docsViewerReport__collectionSortButton";
    filters.toolbarNode.appendChild(collectionSort);
  }

  return {
    shuffleNode: shuffle,
    discoveryMediaNode: discoveryMedia,
    resetDiscoveryList,
    discoveryGrid,
    galleryToggle,
    collectionSortNode: collectionSort,
    filterClearNode: filters.clearNode,
    filterInputNode: filters.inputNode,
    filterToolbarNode: filters.toolbarNode,
    pinnedRowsNode: pinnedRows,
    rowsNode: rows,
    statusNode: status,
    tableNode: table
  };
}

function updateFilterControls(state) {
  if (state.filterInputNode.value !== state.query) {
    state.filterInputNode.value = state.query;
  }
  state.filterClearNode.setAttribute(
    "aria-label",
    state.collectionId === "works" ? "Clear document search"
      : "Clear " + collectionItemsLabel(state.collection) + (state.features.delayedSearch ? " search" : " title filter")
  );
  state.filterClearNode.title = state.filterClearNode.getAttribute("aria-label");
  state.searchCopy?.update(state.query);
}

function catalogueDiscoveryActive(state) {
  return state.collectionId === "catalogue" && !normalizeDocsCollectionFilterValue(state.query);
}

function catalogueGalleryActive(state) {
  return state.galleryPreferred && state.galleryFits && !state.selectionActive && catalogueDiscoveryActive(state);
}

function visibleDocuments(state, discoveryActive) {
  if (discoveryActive) {
    if (catalogueGalleryActive(state)) return [];
    return state.listDiscovery.selection ??= state.browsingData.project("", CATALOGUE_DEFAULT_SORT).slice(0, CATALOGUE_LIST_SIZE);
  }
  var rows = state.browsingData.project(state.query, state.sortMode);
  return state.sectionNavigation ? state.sectionNavigation.project(rows) : rows;
}

async function loadCataloguePass(state, discovery, controls) {
  state.shufflePending = controls;
  updateCollectionControls(state);
  try {
    var source = state.browsingData.project("", CATALOGUE_DEFAULT_SORT);
    var rows = await shuffleCatalogueWorks(source, controls.files[controls.fileIndex]);
    if (!state.mounted || state.shufflePending !== controls) return;
    var start = controls.start ?? catalogueRandomIndex(rows.length);
    discovery.pass = { controls: { ...controls, start }, rows };
    discovery.error = "";
    return true;
  } catch (error) {
    if (!state.mounted || state.shufflePending !== controls) return;
    discovery.error = error.message;
    return false;
  } finally {
    if (state.shufflePending === controls) state.shufflePending = null;
  }
}

async function shuffleCatalogueList(state, remembered) {
  if (state.shuffleNode.disabled) return;
  var gallery = catalogueGalleryActive(state);
  var discovery = gallery ? state.galleryDiscovery : state.listDiscovery;
  var pass = discovery.pass;
  var controls = pass?.controls;
  var count = state.browsingData.rows.length;
  var size = gallery ? CATALOGUE_DISCOVERY_SIZE : CATALOGUE_LIST_SIZE;
  var offset = controls ? controls.offset + size : 0;
  var withinPass = controls && (gallery ? offset + size <= count : offset < count);
  var next = withinPass ? { ...controls, offset } : discovery.pendingPass;
  if (!next) {
    next = controls && controls.fileIndex + 1 < controls.files.length
      ? { files: controls.files, fileIndex: controls.fileIndex + 1, offset: 0 }
      : { files: catalogueShuffleFileOrder(), fileIndex: 0, offset: 0 };
  }
  if (withinPass && pass.rows) {
    pass.controls = next;
  } else {
    var loaded = await loadCataloguePass(state, discovery, next);
    if (loaded === undefined) return;
    if (!loaded) {
      if (!withinPass) discovery.pendingPass = next;
      updateReportStatus(state);
      updateCollectionControls(state);
      return;
    }
    discovery.pendingPass = null;
  }
  if (!state.mounted) return;
  var remaining = discovery.pass.rows.length - discovery.pass.controls.offset;
  var selection = catalogueDiscoveryRows(discovery.pass.rows, discovery.pass.controls, Math.min(size, remaining));
  if (gallery) discovery.columns = [selection, ...discovery.columns.slice(0, CATALOGUE_DISCOVERY_COLUMNS - 1)];
  else discovery.selection = selection;
  state.listNeedsRender = true;
  if (catalogueDiscoveryActive(state) && state.root.dataset.reportState === "list") {
    renderListProjectionContained(state, "catalogue-shuffle");
  } else {
    updateCollectionControls(state);
  }
  remembered.save();
}

function discoverySequenceForCell(state, column, cellIndex) {
  var columns = state.galleryDiscovery.columns;
  var rows = [];
  var position = -1;
  for (const current of columns) {
    current.forEach(({ docId, href, title }, index) => {
      if (rows.at(-1)?.docId !== docId) rows.push({ docId, href, title });
      if (current === column && index === cellIndex) position = rows.length - 1;
    });
  }
  if (rows.length > 1 && position >= 0) return { rows, position };
}

function renderDiscoveryColumns(state) {
  var grid = state.discoveryGrid;
  var columns = state.galleryDiscovery.columns;
  var rendered = state.renderedDiscoveryColumns;
  for (const [column, root] of rendered) {
    if (columns.includes(column)) continue;
    root.remove();
    rendered.delete(column);
  }
  var next = grid.firstElementChild;
  for (const column of columns) {
    var root = rendered.get(column);
    if (!root) {
      root = grid.ownerDocument.createElement("ul");
      root.className = "docsViewerReport__discoveryColumn docsViewerReport__rows";
      column.forEach((doc, index) => {
        var item = createDocRow(doc, true);
        item.link.setAttribute("aria-label", doc.title || doc.docId);
        registerCollectionNavigationLink(item.link, () => discoverySequenceForCell(state, column, index));
        rememberDiscoveryLinkFocus(item.link);
        root.appendChild(item.row);
      });
      rendered.set(column, root);
    }
    if (root !== next) grid.insertBefore(root, next);
    next = root.nextElementSibling;
  }
}

function loadGallerySearch(state, search) {
  if (search.pending || search.project || search.error) return;
  search.pending = true;
  function finish() {
    search.pending = false;
    if (state.mounted && !state.selectionActive && state.gallerySearch === search && state.root.dataset.reportState === "list"
      && state.searchTimer === null && normalizeDocsCollectionFilterValue(state.query)) {
      var focused = state.rowsNode.contains(document.activeElement) && document.activeElement;
      var workId = focused && focused.closest("[data-report-subdoc-id]")?.dataset.reportSubdocId;
      if (renderListProjectionContained(state, "gallery-search-loaded") && workId) {
        var row = state.rowsNode.querySelector('[data-report-subdoc-id="' + CSS.escape(workId) + '"]');
        (row?.querySelector(".docsViewerReport__collectionButton") || state.filterInputNode).focus({ preventScroll: true });
      }
    }
  }
  Promise.resolve().then(search.read).then(createCatalogueGallerySearch).then(function (project) {
    search.project = project;
    finish();
  }, function (error) {
    search.error = error.message ? "Gallery search could not load. " + error.message : "Gallery search could not load.";
    finish();
  });
}

function gallerySearchPending(state) {
  return Boolean(state.gallerySearch?.pending && normalizeDocsCollectionFilterValue(state.query));
}

function bindFilterControls(state) {
  state.filterInputNode.addEventListener("input", function () {
    if (!state.mounted || state.selectionActive) return;
    state.query = state.filterInputNode.value;
    state.searchCopy?.update(state.query);
    if (state.features.delayedSearch) {
      cancelCollectionSearch(state);
      state.listNeedsRender = true;
      if (!normalizeDocsCollectionFilterValue(state.query)) {
        state.pageIndex = 0;
        renderListProjectionContained(state, "collection-search-clear");
        return;
      }
      state.searchTimer = setTimeout(function () {
        state.searchTimer = null;
        if (!state.mounted) return;
        state.pageIndex = 0;
        if (state.root.dataset.reportState === "list") {
          renderListProjectionContained(state, "collection-search");
        }
      }, COLLECTION_SEARCH_DELAY_MS);
      updateCollectionControls(state);
      return;
    }
    renderListProjectionContained(state, "title-filter");
  });
}

/** Navigate rendered results without changing management selection. */
function bindCollectionKeyboardNavigation(state) {
  function onKeyDown(event) {
    if (event.defaultPrevented || event.isComposing || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey
      || !state.mounted || !state.manifestLoaded || state.root.dataset.reportState !== "list") return;
    if (!["ArrowDown", "ArrowUp", "Escape"].includes(event.key)) return;

    if (event.target === state.filterInputNode) {
      if (event.key !== "ArrowDown") return;
      event.preventDefault();
      event.stopPropagation();
      if (state.searchTimer !== null) {
        cancelCollectionSearch(state);
        if (!renderListProjectionContained(state, "collection-keyboard-search")) return;
      }
      var rows = state.discoveryGrid && !state.discoveryGrid.hidden ? state.discoveryGrid : state.tableNode;
      rows.querySelector(".docsViewerReport__rows:not([hidden]) .docsViewerReport__collectionButton")?.focus();
      return;
    }

    var link = event.target.closest(".docsViewerReport__collectionButton");
    if (!link || !state.tableNode.contains(link)) return;
    event.preventDefault();
    event.stopPropagation();
    if (event.key === "Escape") {
      state.filterInputNode.focus();
      return;
    }
    var row = link.parentElement;
    var up = event.key === "ArrowUp";
    var adjacent = up ? row.previousElementSibling : row.nextElementSibling;
    if (!adjacent && up && row.parentElement === state.rowsNode) adjacent = state.pinnedRowsNode?.lastElementChild;
    if (!adjacent && !up && row.parentElement === state.pinnedRowsNode) adjacent = state.rowsNode.firstElementChild;
    if (!adjacent && catalogueGalleryActive(state) && state.discoveryGrid.contains(row)) {
      var column = row.parentElement;
      adjacent = up ? column.previousElementSibling?.lastElementChild : column.nextElementSibling?.firstElementChild;
    }
    if (adjacent) {
      adjacent.querySelector(".docsViewerReport__collectionButton")?.focus();
    } else if (up) {
      state.filterInputNode.focus();
    }
  }

  state.root.addEventListener("keydown", onKeyDown);
  return function () { state.root.removeEventListener("keydown", onKeyDown); };
}

function cancelCollectionSearch(state) {
  if (state.searchTimer !== null) {
    clearTimeout(state.searchTimer);
    state.searchTimer = null;
    state.pageIndex = 0;
  }
}

function selectionReady(state) {
  return state.manifestLoaded && state.searchTimer === null && !state.shufflePending && !gallerySearchPending(state)
    && !catalogueGalleryActive(state);
}

function updateCollectionControls(state, pageIndex = state.pageIndex) {
  var pending = state.searchTimer !== null || !state.manifestLoaded;
  var locked = state.selectionActive;
  var discoveryActive = catalogueDiscoveryActive(state);
  var gallery = catalogueGalleryActive(state);
  state.filterInputNode.disabled = !state.manifestLoaded || locked;
  state.filterClearNode.disabled = state.filterInputNode.disabled;
  state.selectionControls?.setReady(selectionReady(state));
  state.paginationControl?.update(state.pagedBrowsing);
  if (state.paginationControl) state.paginationControl.button.disabled = locked;
  state.sectionNavigation?.setBrowsingLocked(locked);
  if (state.shuffleNode) {
    state.shuffleNode.disabled = locked || pending || state.shufflePending || state.browsingData.rows.length < CATALOGUE_DISCOVERY_SIZE
      || Boolean(normalizeDocsCollectionFilterValue(state.query));
    state.shuffleNode.setAttribute("aria-busy", String(Boolean(state.shufflePending)));
    state.shuffleNode.classList.toggle("is-active", gallery);
  }
  if (state.galleryToggle) {
    state.galleryToggle.hidden = !discoveryActive || !state.galleryFits;
    state.galleryToggle.disabled = locked || pending || Boolean(state.shufflePending);
    var toggleLabel = gallery ? "Switch to List view" : "Switch to Gallery view";
    state.galleryToggle.title = toggleLabel;
    state.galleryToggle.setAttribute("aria-label", toggleLabel);
    state.galleryToggle.firstElementChild.classList.toggle("docsViewer__icon--list", gallery);
    state.galleryToggle.firstElementChild.classList.toggle("docsViewer__icon--layout-grid", !gallery);
  }
  if (state.resetDiscoveryList) {
    state.resetDiscoveryList.hidden = !discoveryActive || gallery;
    state.resetDiscoveryList.disabled = locked || pending || Boolean(state.shufflePending)
      || !(state.listDiscovery.pass || state.listDiscovery.pendingPass);
  }
  if (state.discoveryMediaNode) {
    state.discoveryMediaNode.hidden = !discoveryActive || gallery;
    state.discoveryMediaNode.disabled = gallery || pending || state.shufflePending || !state.documentMatches.length;
  }
  var button = state.collectionSortNode;
  if (button) {
    button.hidden = discoveryActive && !gallery;
    button.disabled = discoveryActive || locked || pending || state.shufflePending;
    if (button.dataset.docsCollectionSort !== state.sortMode) {
      var recentMode = state.sortMode === "last-updated-desc";
      button.dataset.docsCollectionSort = state.sortMode;
      button.replaceChildren(createDocsViewerToolbarIcon(button.ownerDocument,
        recentMode ? "docsViewer__icon--clock-3" : "docsViewer__icon--arrow-down-a-z"));
      button.title = recentMode ? "Sorted by recently updated. Switch to title A–Z."
        : "Sorted by title A–Z. Switch to recently updated.";
      button.setAttribute("aria-label", button.title);
    }
  }
  if (state.pager) {
    state.pager.update(state.matches.length, pageIndex, locked || pending || gallerySearchPending(state),
      state.pagedBrowsing && !discoveryActive);
  }
}

function listSortContext(state) {
  return {
    mode: state.sortMode,
    setMode: function (mode) {
      if (!state.mounted || state.selectionActive || state.searchTimer !== null || !state.manifestLoaded) return state.sortMode;
      var nextMode = cleanString(mode);
      if (!["title-asc", "last-updated-desc"].includes(nextMode)) {
        throw new Error("Docs collection sort mode is invalid: " + nextMode);
      }
      state.sortMode = nextMode;
      state.pageIndex = 0;
      renderListProjectionContained(state, "sort-change", { reusePinnedRows: true });
      return nextMode;
    }
  };
}

function renderListToolbar(state, docIds, retainedRows) {
  var renderToolbar = contributionCallback(state.contribution, "renderListToolbar");
  if (!renderToolbar) return;
  state.listActionHost.replaceChildren();
  state.selectionControls = null;
  if (state.listToolbarNode) {
    state.listToolbarNode.remove();
    state.listToolbarNode = null;
  }
  var host = document.createElement("div");
  host.className = "docsViewerReport__contributionToolbar docsViewerReport__contributionToolbar--list";
  host.dataset.reportContributionHost = "list-toolbar";
  state.selectionControls = renderToolbar({
    actionContext: state.actionContext,
    collection: state.actionContext.collectionTarget,
    docIds: docIds,
    selectionReady: selectionReady(state),
    retainedRows: retainedRows,
    host: host,
    actionHost: state.listActionHost,
    refreshAndOpenDocument: function (target) {
      return state.openDocument(target);
    },
    refreshCollection: state.management.refreshCollection,
    completeCatalogueRegenerate: state.collectionId === "catalogue" ? state.completeCatalogueRegenerate : undefined,
    selectionChanged: function (active) {
      if (state.selectionActive === active) return;
      var wasGallery = catalogueGalleryActive(state);
      state.selectionActive = active;
      if (wasGallery !== catalogueGalleryActive(state) && !state.listNeedsRender) {
        renderListProjectionContained(state, "catalogue-gallery-selection");
        if (!active) {
          state.discoveryPositionChanged?.(true);
          state.galleryToggle?.focus({ preventScroll: true });
        }
        return;
      }
      updateCollectionControls(state);
    },
    renderList: function () {
      if (state.mounted) renderListProjectionContained(state, "collection-controls-changed");
    },
    sort: state.features.filterToolbarSort ? null : listSortContext(state)
  });
  if (!host.childNodes.length) return;
  state.filterToolbarNode.appendChild(host);
  state.listToolbarNode = host;
}

function renderPinnedRows(state, matches, retainedRows, reserveThumbnailSpace) {
  var list = state.pinnedRowsNode;
  if (!list) return [];
  if (retainedRows) {
    var next = list.firstElementChild;
    for (const match of matches) {
      var row = retainedRows.get(match.docId).row;
      if (row === next) next = row.nextElementSibling;
      else list.insertBefore(row, next);
    }
  } else {
    clearNode(list);
    state.renderedPinnedRows = matches?.length ? new Map() : null;
    matches?.forEach(function (match) {
      state.renderedPinnedRows.set(match.docId, appendDocRow(state, match, reserveThumbnailSpace, list));
    });
  }
  return state.renderedPinnedRows ? Array.from(state.renderedPinnedRows.values()) : [];
}

function updateReportStatus(state) {
  var searchError = state.gallerySearch?.error && normalizeDocsCollectionFilterValue(state.query)
    ? state.gallerySearch.error : "";
  var discovery = catalogueGalleryActive(state) ? state.galleryDiscovery : state.listDiscovery;
  var shuffleError = catalogueDiscoveryActive(state) ? discovery?.error : "";
  var message = searchError || shuffleError || state.pinLoadError;
  state.statusNode.textContent = message;
  state.statusNode.hidden = !message;
}

function renderRows(state, matches, pinnedMatches, retainedPinnedRows, thumbnailLoading, retainList) {
  var reserveThumbnailSpace = state.browsingData.hasThumbnails;
  var rows = renderPinnedRows(state, pinnedMatches, retainedPinnedRows, reserveThumbnailSpace);
  state.root.removeAttribute("data-report-leading-column");
  if (retainList && state.renderedDiscoveryList?.matches === matches) {
    state.renderedDiscoveryList.items.forEach((item, index) => {
      if (state.contribution) contributeDocRow(state, item, matches[index]);
      rows.push(item);
    });
  } else {
    clearNode(state.rowsNode);
    state.renderedDiscoveryList = null;
    if (!matches.length && !rows.length) {
      var empty = document.createElement("li");
      empty.className = "docsViewerReport__empty";
      empty.textContent = state.browsingData.rows.length
        ? "No " + collectionItemsLabel(state.collection).toLowerCase() + " match the current filters."
        : state.collectionId === "works" ? "No documents are available."
          : "No documents are available in " + collectionItemsLabel(state.collection) + ".";
      state.rowsNode.appendChild(empty);
      return;
    }
    matches.forEach(function (match) {
      if (match.galleryId) appendGalleryRow(state, match);
      else rows.push(appendDocRow(state, match, reserveThumbnailSpace, state.rowsNode, thumbnailLoading));
    });
    if (retainList) state.renderedDiscoveryList = { matches, items: rows };
  }
  if (!rows.some(function (record) { return record.hasLeadingContent; })) return;
  state.root.dataset.reportLeadingColumn = "true";
  rows.forEach(function (record) {
    if (!record.leadingHost.parentNode) {
      record.row.insertBefore(record.leadingHost, record.row.firstChild);
    }
  });
}

function publishState(state, reportState, target, reason) {
  if (reportState === "error" || reportState === "unmounted") cancelCollectionSearch(state);
  var active = !["inactive", "unmounted"].includes(reportState);
  state.actionContext = Object.freeze({
    state: reportState, reason: reason,
    parentTarget: active ? state.parentTarget : null,
    collectionTarget: active ? state.collectionTarget : null,
    collectionLabel: collectionTitle(state.collection),
    documentTarget: reportState === "list" ? state.parentTarget : null,
    documentRecord: reportState === "list" ? state.parentRecord : null,
    actionHost: reportState === "list" ? state.listActionHost : null,
    refreshDocument: state.openDocument,
    ...(state.management ? { refreshCollection: state.management.refreshCollection } : {})
  });
  if (typeof state.onDocumentState === "function") state.onDocumentState(state.actionContext);
  notifyContribution(state, { type: "state", state: reportState, reason: reason });
}

function renderListProjection(state, reusePinnedRows) {
  var retainedPinnedRows = reusePinnedRows && !state.listNeedsRender ? state.renderedPinnedRows : null;
  state.listNeedsRender = true;
  var gallerySearch = state.gallerySearch;
  var query = state.shuffleNode ? normalizeDocsCollectionFilterValue(state.query) : "";
  var documents = visibleDocuments(state, catalogueDiscoveryActive(state));
  if (query && gallerySearch) loadGallerySearch(state, gallerySearch);
  var matches = query && gallerySearch?.project ? gallerySearch.project(query, documents) : documents;
  state.pinnedMatches = null;
  if (state.pinnedDocIds?.size) {
    var pinned = [];
    var regular = [];
    for (const row of matches) {
      (state.pinnedDocIds.has(row.docId) ? pinned : regular).push(row);
    }
    if (pinned.length) {
      state.pinnedMatches = pinned;
      matches = regular;
    }
  }
  state.matches = matches;
  state.documentMatches = documents;
  state.readingRows = null;
  renderListPage(state, retainedPinnedRows);
  state.catalogueSearchRoute?.replaceQuery(state.query);
  state.listNeedsRender = false;
}

/** Page turns reuse the complete matches and pass the rendered IDs to Working selection. */
function renderListPage(state, retainedPinnedRows) {
  var matches = state.matches;
  var discovery = catalogueDiscoveryActive(state);
  var gallery = catalogueGalleryActive(state);
  var paginate = state.pagedBrowsing && !discovery;
  var pageIndex = paginate ? state.pageIndex : 0;
  if (paginate) {
    pageIndex = Math.min(pageIndex, Math.max(0, Math.ceil(matches.length / COLLECTION_PAGE_SIZE) - 1));
    if (!gallerySearchPending(state)) state.pageIndex = pageIndex;
  }
  updateFilterControls(state);
  var pageRows = paginate
    ? matches.slice(pageIndex * COLLECTION_PAGE_SIZE, (pageIndex + 1) * COLLECTION_PAGE_SIZE)
    : matches;
  var pinnedRows = pageIndex === 0 ? state.pinnedMatches : null;
  if (state.contribution) {
    var docIds = pinnedRows ? pinnedRows.map(row => row.docId) : [];
    if (!gallery) {
      for (const row of pageRows) {
        if (row.docId) docIds.push(row.docId);
      }
    }
    renderListToolbar(state, docIds, retainedPinnedRows);
  }
  updateReportStatus(state);
  if (state.discoveryGrid) state.discoveryGrid.hidden = !gallery;
  state.rowsNode.hidden = gallery;
  if (gallery) {
    state.root.removeAttribute("data-report-leading-column");
    renderDiscoveryColumns(state);
  } else {
    renderRows(state, pageRows, pinnedRows, retainedPinnedRows, paginate ? "eager" : "lazy", discovery);
  }
  state.selectionControls?.project();
  updateCollectionControls(state, pageIndex);
}

function renderListProjectionContained(state, reason, { reusePinnedRows = false } = {}) {
  try {
    renderListProjection(state, reusePinnedRows);
    return true;
  } catch (error) {
    return reportFailure(state, error, reason);
  }
}

function reportFailure(state, error, reason) {
  if (!state.mounted) return false;
  try {
    publishState(state, "error", null, reason);
  } catch (_notifyError) {
    // Preserve the original operation failure if contribution notification fails.
  }
  renderError(state.root, error.message || "Failed to render docs collection report.");
  return false;
}

function captureListControls(state) {
  var captureContribution = contributionCallback(state.contribution, "captureListState");
  return { query: state.query, sort: state.sortMode,
    page: state.searchTimer !== null ? 0 : state.pageIndex,
    ...(state.discoveryGrid ? { rollingDiscovery: {
      gallery: state.galleryPreferred,
      list: {
        ids: state.listDiscovery.pass ? state.listDiscovery.selection.map(row => row.docId) : undefined,
        pass: state.listDiscovery.pass?.controls,
        position: state.listDiscovery.position
      },
      grid: {
        columns: state.galleryDiscovery.columns.map(column => column.map(row => row.docId)),
        pass: state.galleryDiscovery.pass?.controls
      }
    } } : {}),
    ...(typeof state.contribution?.paginationDefault === "boolean" ? { pagination: state.pagedBrowsing } : {}),
    ...(state.sectionNavigation ? { section: state.sectionNavigation.selected() } : {}),
    contribution: captureContribution ? captureContribution.call(state.contribution) : null };
}

function restoreDiscoveryRows(byId, ids, size) {
  if (!Array.isArray(ids) || !ids.length || ids.length > size) return null;
  var rows = ids.map(id => byId.get(id));
  return rows.every(Boolean) ? rows : null;
}

function restoreCatalogueColumns(byId, saved) {
  if (!Array.isArray(saved) || saved.length > CATALOGUE_DISCOVERY_COLUMNS) return [];
  var columns = [];
  for (const ids of saved) {
    var column = restoreDiscoveryRows(byId, ids, CATALOGUE_DISCOVERY_SIZE);
    if (column?.length !== CATALOGUE_DISCOVERY_SIZE) return [];
    columns.push(column);
  }
  return columns;
}

function restoreDiscoveryPass(saved, current, count, size, fullColumn) {
  var controls = savedCatalogueDiscovery(saved, size);
  if (!controls || controls.start >= count || controls.offset >= count || (fullColumn && controls.offset + size > count)) return null;
  return JSON.stringify(controls) === JSON.stringify(current?.controls) ? current : { controls };
}

/** Restore controls against the current inventory, never a saved payload. */
function restoreListControls(state, saved) {
  var current = captureListControls(state);
  if (JSON.stringify(current) === JSON.stringify(saved)) return;
  cancelCollectionSearch(state);
  if (typeof saved.query === "string") state.query = saved.query;
  if (["title-asc", "last-updated-desc"].includes(saved.sort)) state.sortMode = saved.sort;
  if (typeof state.contribution?.paginationDefault === "boolean" && typeof saved.pagination === "boolean") {
    state.pagedBrowsing = saved.pagination;
  }
  state.pageIndex = Number.isInteger(saved.page) && saved.page >= 0 ? saved.page : 0;
  state.sectionNavigation?.restore(saved.section);
  var restoreContribution = contributionCallback(state.contribution, "restoreListState");
  if (restoreContribution) restoreContribution.call(state.contribution, saved.contribution);
  state.listNeedsRender = true;
  if (!state.discoveryGrid) return;
  var discovery = saved.rollingDiscovery;
  var previous = current.rollingDiscovery;
  state.galleryPreferred = Boolean(discovery?.grid && discovery.gallery === true);
  var restoreList = JSON.stringify(discovery?.list) !== JSON.stringify(previous.list);
  var restoreGrid = JSON.stringify(discovery?.grid) !== JSON.stringify(previous.grid);
  if (!restoreList && !restoreGrid) return;
  var inventory = state.browsingData.rows;
  var byId = new Map(inventory.map(row => [row.docId, row]));
  if (restoreList) {
    var selection = restoreDiscoveryRows(byId, discovery?.list?.ids, CATALOGUE_LIST_SIZE);
    var listPass = selection && restoreDiscoveryPass(discovery.list.pass, state.listDiscovery.pass, inventory.length, CATALOGUE_LIST_SIZE, false);
    state.listDiscovery = { selection: listPass ? selection : null, pass: listPass,
      position: discovery?.list?.position ?? null };
  }
  if (restoreGrid) {
    var columns = restoreCatalogueColumns(byId, discovery?.grid?.columns);
    var gridPass = columns.length ? restoreDiscoveryPass(discovery.grid.pass, state.galleryDiscovery.pass,
      inventory.length, CATALOGUE_DISCOVERY_SIZE, true) : null;
    state.galleryDiscovery = { columns: gridPass ? columns : [], pass: gridPass };
    if (!state.galleryDiscovery.columns.length) renderDiscoveryColumns(state);
  }
}

/** Reveal the retained list, rebuilding only when its document data changed. */
function renderListView(state) {
  state.root.dataset.reportState = "list";
  state.filterToolbarNode.hidden = false;
  state.tableNode.hidden = false;
  publishState(state, "list", null, "list-view");
  if (state.listNeedsRender && !renderListProjectionContained(state, "list-projection-failed")) return false;
  if (state.listToolbarNode) state.listToolbarNode.hidden = false;
  return true;
}

function renderError(root, message) {
  clearNode(root);
  root.dataset.reportState = "error";
  var note = document.createElement("p");
  note.className = "docsViewerReport__status is-error";
  note.textContent = message;
  root.appendChild(note);
}

function mountResolvedDocsCollectionReport(context, contribution, lifetime) {
  var root = context && context.reportRoot;
  var reportMeta = context && context.reportMeta ? context.reportMeta : {};
  var collectionIdValue = reportMeta.collection;
  if (!root) return Promise.resolve(false);
  if (!collectionIdValue) {
    contributionEvent(context, collectionIdValue, {
      type: "state",
      state: "error",
      reason: "missing-collection",
      target: null
    });
    renderError(root, "This report is missing report collection.");
    return Promise.resolve(true);
  }

  var collection = context.collectionConfig;
  if (!collection || collection.collection !== collectionIdValue) {
    contributionEvent(context, collectionIdValue, {
      type: "state",
      state: "error",
      reason: "unconfigured-collection",
      target: null
    });
    renderError(root, "Docs collection is not configured: " + collectionIdValue);
    return Promise.resolve(true);
  }

  var url = collection.manifestUrl;
  if (!url) {
    contributionEvent(context, collectionIdValue, {
      type: "state",
      state: "error",
      reason: "missing-manifest",
      target: null
    });
    renderError(root, "Docs collection manifest is not configured: " + collectionIdValue);
    return Promise.resolve(true);
  }

  var features = collectionBrowsingFeatures(collection);
  var refs = renderShell(context, collection, features);
  var readGallerySearch = collectionIdValue === "catalogue" && typeof context.openMediaTarget === "function"
    && context.collectionProvider.readCatalogueGalleryReportSearch;
  var readContextManifest = collectionIdValue === "works" && context.collectionProvider.readContextManifest;
  var state = {
    root: root,
    openDocument: context.openDocument,
    openMediaTarget: context.openMediaTarget,
    onDocumentState: context.onCollectionDocumentState,
    parentDocId: cleanString(context && context.doc && context.doc.doc_id),
    parentTarget: Object.freeze({
      doc_id: cleanString(context.doc && context.doc.doc_id)
    }),
    parentRecord: context.doc,
    collectionTarget: Object.freeze(collectionTarget(collectionIdValue)),
    listActionHost: contribution ? root.ownerDocument.createElement("div") : null,
    collection: collection,
    collectionId: collectionIdValue,
    manifestLoaded: false,
    query: "",
    sortMode: collectionIdValue === "catalogue" ? "last-updated-desc" : "title-asc",
    features: features,
    pagedBrowsing: contribution?.paginationDefault ?? features.pagination,
    paginationControl: null,
    thumbnailSettingsRead: null,
    gallerySearch: null,
    catalogueSearchRoute: context.catalogueSearchRoute,
    shuffleNode: refs.shuffleNode,
    discoveryMediaNode: refs.discoveryMediaNode,
    discoveryGrid: refs.discoveryGrid,
    galleryToggle: refs.galleryToggle,
    galleryPreferred: false,
    galleryFits: false,
    listDiscovery: refs.discoveryGrid ? {} : null,
    galleryDiscovery: refs.discoveryGrid ? { columns: [] } : null,
    renderedDiscoveryList: null,
    renderedDiscoveryColumns: refs.discoveryGrid ? new Map() : null,
    shufflePending: null,
    resetDiscoveryList: refs.resetDiscoveryList,
    collectionSortNode: refs.collectionSortNode,
    matches: [],
    documentMatches: [],
    readingRows: null,
    pinnedMatches: null,
    renderedPinnedRows: null,
    pinnedDocIds: null,
    pinLoadError: "",
    pageIndex: 0,
    searchTimer: null,
    selectionActive: false,
    selectionControls: null,
    pager: null,
    contribution: contribution,
    managementContext: Boolean(context && context.managementContext),
    filterClearNode: refs.filterClearNode,
    filterInputNode: refs.filterInputNode,
    filterToolbarNode: refs.filterToolbarNode,
    listToolbarNode: null,
    listNeedsRender: true,
    statusNode: refs.statusNode,
    tableNode: refs.tableNode,
    pinnedRowsNode: refs.pinnedRowsNode,
    rowsNode: refs.rowsNode,
    mounted: true
  };
  var browsingOptions = {
    collectionId: collectionIdValue, mediaRoot: context.mediaRoot,
    documentHref: function (docId) {
      return context.collectionProvider.documentHref({ collection: collectionIdValue, doc_id: docId });
    }
  };
  state.management = contribution ? contribution.createListManagement({
    browsingOptions: browsingOptions,
    collectionId: collectionIdValue,
    collectionProvider: context.collectionProvider,
    isMounted: function () { return state.mounted; },
    isReady: function () { return state.manifestLoaded; },
    notify: function (detail) { notifyContribution(state, detail); },
    render: function (reason) { return renderListProjectionContained(state, reason); },
    reveal: function () { renderListView(state); },
    fail: function (error, reason) { return reportFailure(state, error, reason); },
    loadManifest: function () { return state.loadManifest(); },
    resolveThumbnails: resolvePendingThumbnails
  }) : null;
  state.browsingData = state.management ? state.management.data : createCollectionBrowsingData(browsingOptions);
  state.searchCopy = contributionCallback(contribution, "mountCatalogueSearchCopy")?.({
    host: state.filterToolbarNode, before: state.collectionSortNode
  });
  if (state.listActionHost) state.listActionHost.className = "docsViewer__collectionActions";
  if (features.pagination) {
    state.filterInputNode.disabled = true;
    state.pager = createCollectionPager(root.ownerDocument,
      state.collectionId === "works" ? "document" : collectionItemsLabel(state.collection), function (pageIndex) {
      if (!state.mounted || state.selectionActive || state.searchTimer !== null || gallerySearchPending(state) || pageIndex < 0
        || pageIndex * COLLECTION_PAGE_SIZE >= state.matches.length) return;
      state.pageIndex = pageIndex;
      try {
        renderListPage(state);
      } catch (error) {
        publishState(state, "error", null, "collection-page-failed");
        renderError(root, error.message);
      }
    });
    root.appendChild(state.pager.root);
  }
  if (state.collectionSortNode) {
    state.collectionSortNode.addEventListener("click", function () {
      listSortContext(state).setMode(state.sortMode === "last-updated-desc" ? "title-asc" : "last-updated-desc");
    });
  }
  var mountPaginationControl = contributionCallback(contribution, "mountPaginationControl");
  if (mountPaginationControl) {
    state.paginationControl = mountPaginationControl({
      host: state.filterToolbarNode,
      change: function (enabled) {
        if (state.selectionActive) return;
        cancelCollectionSearch(state);
        state.pagedBrowsing = enabled;
        state.pageIndex = 0;
        renderListProjectionContained(state, "pagination-change");
        remembered.save();
      }
    });
  }
  updateCollectionControls(state);
  bindFilterControls(state);
  var unbindKeyboardNavigation = bindCollectionKeyboardNavigation(state);
  updateFilterControls(state);

  var remembered = createDocsCollectionReportState({
    root: root, collectionId: state.collectionId, hostDocId: state.parentDocId,
    isReady: function () {
      return state.mounted && state.manifestLoaded && root.dataset.reportState === "list";
    },
    captureControls: function () { return captureListControls(state); },
    restoreControls: function (saved) { return restoreListControls(state, saved); }
  });
  var viewer = state.discoveryGrid ? root.closest(".docsViewer") : null;
  var infoPanel = viewer?.querySelector(".docsViewer__infoPanel");
  function updateGalleryFit() {
    if (!viewer || !state.mounted || root.dataset.reportState !== "list") return false;
    var table = state.tableNode.getBoundingClientRect();
    if (!table.width) return false;
    var right = viewer.getBoundingClientRect().right;
    var info = infoPanel?.getBoundingClientRect();
    if (info?.width && info.left > table.left) right = Math.min(right, info.left);
    var fits = right - table.left >= CATALOGUE_GALLERY_WIDTH + 8;
    var changed = fits !== state.galleryFits;
    state.galleryFits = fits;
    return changed;
  }
  var galleryResize = viewer ? new ResizeObserver(function () {
    var wasGallery = catalogueGalleryActive(state);
    if (!updateGalleryFit()) return;
    if (wasGallery !== catalogueGalleryActive(state) && state.searchTimer === null) {
      var active = root.ownerDocument.activeElement;
      var hiddenFocus = active === state.galleryToggle || state.discoveryGrid.contains(active);
      if (!wasGallery) state.listDiscovery.position = remembered.capturePosition();
      if (renderListProjectionContained(state, "catalogue-gallery-fit")) {
        state.discoveryPositionChanged(!wasGallery);
        if (!state.galleryFits && hiddenFocus) state.shuffleNode.focus({ preventScroll: true });
      }
    } else {
      updateCollectionControls(state);
    }
  }) : null;
  if (galleryResize) {
    galleryResize.observe(viewer);
    galleryResize.observe(state.tableNode);
    if (infoPanel) galleryResize.observe(infoPanel);
  }
  state.discoveryPositionChanged = function (gallery) {
    remembered.applyPosition(gallery ? null : state.listDiscovery.position);
    remembered.save();
  };
  state.galleryToggle?.addEventListener("click", function () {
    if (state.galleryToggle.disabled || state.galleryToggle.hidden) return;
    var enterGallery = !catalogueGalleryActive(state);
    if (enterGallery) {
      state.listDiscovery.position = remembered.capturePosition();
    } else {
      state.galleryDiscovery = { columns: [] };
      renderDiscoveryColumns(state);
    }
    state.galleryPreferred = enterGallery;
    if (renderListProjectionContained(state, "catalogue-gallery-toggle")) state.discoveryPositionChanged(enterGallery);
  });
  state.resetDiscoveryList?.addEventListener("click", function () {
    if (state.resetDiscoveryList.disabled || state.resetDiscoveryList.hidden) return;
    state.listDiscovery = {};
    if (renderListProjectionContained(state, "catalogue-list-reset")) {
      remembered.resetPosition();
      state.shuffleNode.focus({ preventScroll: true });
    }
  });
  state.shuffleNode?.addEventListener("click", function () { shuffleCatalogueList(state, remembered); });
  state.discoveryMediaNode?.addEventListener("click", function () {
    if (state.discoveryMediaNode.disabled || !catalogueDiscoveryActive(state)) return;
    try {
      var opened = context.openMediaPresentation({
        presentation: catalogueDiscoveryMediaPresentation(state.documentMatches),
        invocationControl: state.discoveryMediaNode,
        documentTarget: { docId: state.parentDocId }
      });
      if (opened) return;
      state.statusNode.textContent = "The current selection could not open in Media View.";
    } catch (error) {
      state.statusNode.textContent = error.message;
    }
    state.statusNode.hidden = false;
  });
  state.completeCatalogueRegenerate = async function (changed) {
    if (changed && !await state.loadManifest()) return;
    if (!state.mounted) return;
    cancelCollectionSearch(state);
    state.query = "";
    state.sortMode = CATALOGUE_DEFAULT_SORT;
    state.pageIndex = 0;
    state.listDiscovery = {};
    state.galleryDiscovery = { columns: [] };
    renderDiscoveryColumns(state);
    state.galleryPreferred = false;
    state.shufflePending = null;
    lifetime.catalogueSearch = undefined;
    state.listNeedsRender = true;
    if (!renderListView(state)) throw new Error(state.root.textContent);
    remembered.resetPosition();
  };
  state.sectionNavigation = contributionCallback(contribution, "mountSectionNavigation")?.({
    root: root,
    rows: function () { return state.browsingData.rows; },
    rowForId: function (id) { return state.browsingData.rowForId(id); },
    change: function () {
      state.pageIndex = 0;
      if (state.manifestLoaded) {
        renderListProjectionContained(state, "section-change");
        remembered.save();
      }
    }
  });
  function restoreRememberedList() {
    if (!state.manifestLoaded || !state.mounted || root.dataset.reportState === "error") return;
    remembered.restore();
    var wasGallery = catalogueGalleryActive(state);
    if (updateGalleryFit()) {
      if (wasGallery !== catalogueGalleryActive(state)) state.listNeedsRender = true;
      else updateCollectionControls(state);
    }
    revealRememberedList();
  }
  function revealRememberedList() {
    var catalogueSearch = lifetime.catalogueSearch;
    if (catalogueSearch !== undefined) {
      lifetime.catalogueSearch = undefined;
      cancelCollectionSearch(state);
      if (catalogueSearch !== state.query && state.selectionActive) {
        contributionCallback(state.contribution, "restoreListState")?.(null);
      }
      state.query = catalogueSearch;
      state.pageIndex = 0;
      state.listNeedsRender = true;
    }
    renderListView(state);
    state.catalogueSearchRoute?.replaceQuery(state.query);
    if (catalogueSearch === undefined) {
      if (state.galleryPreferred && !state.galleryFits && catalogueDiscoveryActive(state) && state.listDiscovery.position) {
        remembered.restorePosition(state.listDiscovery.position);
      } else {
        remembered.restorePosition();
      }
    }
  }
  function dispose() {
    if (!state.mounted) return;
    remembered.dispose();
    galleryResize?.disconnect();
    unbindKeyboardNavigation();
    state.mounted = false;
    cancelCollectionSearch(state);
    publishState(state, "unmounted", null, "report-unmount");
    notifyContribution(state, { type: "unmount", reason: "report-unmount" });
    state.management?.dispose();
    state.browsingData.clear();
    state.matches = [];
    state.documentMatches = [];
    state.readingRows = null;
    state.pinnedMatches = null;
    state.renderedPinnedRows = null;
    state.pinnedDocIds = null;
    state.thumbnailSettingsRead = null;
    state.gallerySearch = null;
    state.listDiscovery = null;
    state.galleryDiscovery = null;
    state.renderedDiscoveryList = null;
    state.renderedDiscoveryColumns?.clear();
  }
  lifetime.view = {
    dispose: dispose, capture: remembered.save, restore: restoreRememberedList, resume: restoreRememberedList
  };

  async function resolvePendingThumbnails() {
    if (!state.browsingData.needsThumbnailSettings) return false;
    if (!state.thumbnailSettingsRead) state.thumbnailSettingsRead = loadCatalogueCollectionThumbnailSettings(context);
    var settings = await state.thumbnailSettingsRead;
    return state.mounted && state.browsingData.setThumbnailSettings(settings);
  }

  notifyContribution(state, {
    type: "mount",
    root: root
  });
  publishState(state, "loading", null, "report-loading");
  state.loadManifest = function (starsRead) {
    if (!state.mounted) return Promise.resolve(false);
    return (readContextManifest ? readContextManifest() : fetchDocsCollectionManifest(url)).then(async function (payload) {
      if (!state.mounted) return false;
      cancelCollectionSearch(state);
      state.browsingData.replace(payload.docs);
      await resolvePendingThumbnails();
      if (starsRead) await starsRead;
      if (!state.mounted) return false;
      state.gallerySearch = readGallerySearch ? { read: readGallerySearch } : null;
      state.manifestLoaded = true;
      state.listNeedsRender = true;
      state.management?.inventoryChanged("documents-loaded", true);
      return true;
    });
  };
  state.management?.connect();
  var starsRead = collection.pinStarredDocuments ? fetchSelectedDocumentRows(context.selectedUrl).then(function (rows) {
    if (!state.mounted) return;
    var pinnedDocIds = new Set();
    for (const row of rows) {
      if (row.collection === collectionIdValue) pinnedDocIds.add(row.doc_id);
    }
    state.pinnedDocIds = pinnedDocIds;
    context.collectionProvider.subscribeDocumentStars?.(function (change) {
      if (change.target.collection !== collectionIdValue) return;
      if (change.selected) pinnedDocIds.add(change.target.doc_id);
      else pinnedDocIds.delete(change.target.doc_id);
      state.listNeedsRender = true;
    });
  }).catch(function () {
    if (!state.mounted) return;
    state.pinLoadError = "Could not load starred documents.";
    state.statusNode.classList.remove("visually-hidden");
  }) : null;
  return state.loadManifest(starsRead).then(async function (loaded) {
      if (loaded) {
        // The document inventory must exist before restoring saved controls.
        root.dataset.reportState = "list";
        await restoreRememberedList();
      }
      return true;
    })
    .catch(function (error) {
      reportFailure(state, error, "report-load-failed");
      return true;
    });
}

export function mountDocsCollectionReport(context) {
  var root = context && context.reportRoot;
  if (!root) return Promise.resolve(false);
  var lifetime = { active: true, view: null, catalogueSearch: context.catalogueSearchRoute?.query };
  context.registerRetainedView?.({
    id: "collection:" + context.reportMeta.collection,
    dispose: function () { lifetime.active = false; lifetime.view?.dispose(); lifetime.view = null; },
    capture: function () { return lifetime.view?.capture() || null; },
    restore: function () { lifetime.view?.restore(); },
    resume: function (catalogueSearch) {
      if (catalogueSearch !== undefined) lifetime.catalogueSearch = catalogueSearch;
      lifetime.view?.resume();
    }
  });
  return Promise.resolve(context.collectionReportContributionPromise)
    .then(function (contribution) {
      if (!lifetime.active) return false;
      return mountResolvedDocsCollectionReport(
        Object.assign({}, context, {
          resolvedCollectionReportContribution: contribution
        }),
        contribution,
        lifetime
      );
    })
    .catch(function (error) {
      if (!lifetime.active) return false;
      renderError(
        root,
        error && error.message
          ? error.message
          : "Failed to resolve docs collection controls."
      );
      if (typeof context.onCollectionDocumentState === "function") {
        context.onCollectionDocumentState({
          state: "error",
          parentTarget: {  doc_id: context.doc.doc_id },
          documentTarget: null
        });
      }
      return true;
    });
}
