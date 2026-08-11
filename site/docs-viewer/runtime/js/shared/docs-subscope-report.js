import {
  appendAssetVersion
} from "./docs-viewer-asset-url.js";
import {
  normalizeDocsSubscopeFilterValue,
  projectDocsSubscopeDocuments
} from "./docs-subscope-report-filter.js";
import {
  resolvePublicDocsSubscopeCustomisation
} from "./docs-subscope-customisation-registry.js";

/**
 * Optional caller-owned composition for one shared sub-scope report.
 *
 * Render callbacks receive detached hosts that enter the document only when
 * populated. `notify` receives explicit collection-scoped mount, state,
 * complete-manifest refresh, visible-row projection, and unmount events.
 *
 * @typedef {Object} DocsSubscopeReportContribution
 * @property {function(Object): void} [notify]
 * @property {function(Object): Array<Object>} [createFilters]
 * @property {function(Object): number} [compareListDocuments]
 * @property {function(Object): (Object|void)} [renderRow]
 * @property {function(Object): void} [renderListHead]
 * @property {function(Object): void} [renderListToolbar]
 * @property {function(Object): void} [renderDetailToolbar]
 * @property {function(Object): (Object|null)} [projectDetailInfo]
 */

var filterIdSequence = 0;

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function cleanId(value) {
  return cleanString(value).toLowerCase();
}

function humanize(value) {
  var text = cleanString(value).replace(/[-_]+/g, " ").replace(/\s+/g, " ").trim();
  if (!text) return "";
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function clearNode(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function fetchJson(url, failureMessage, options) {
  var settings = options || {};
  return fetch(appendAssetVersion(url), {
    headers: { Accept: "application/json" },
    cache: settings.cache || "default"
  }).then(function (response) {
    if (!response.ok) throw new Error(failureMessage + " (" + response.status + ")");
    return response.json();
  });
}

function normalizeDocIds(value) {
  return cleanString(value)
    .split(",")
    .map(cleanString)
    .filter(Boolean);
}

function manifestDocs(payload) {
  if (!payload || typeof payload !== "object") return [];
  if (Array.isArray(payload.docs)) {
    return normalizeDocuments(payload.docs);
  }
  return normalizeDocIds(payload.doc_ids).map(function (docId) {
    return normalizeDocument({ doc_id: docId, title: "" });
  });
}

function manifestCustomisation(payload) {
  var value = payload && payload.customisation;
  if (value == null) return null;
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error("Docs sub-scope manifest customisation must be an object.");
  }
  var keys = Object.keys(value).sort();
  var customisationId = cleanId(value.id);
  var data = value.data;
  if (
    keys.length !== 2
    || keys[0] !== "data"
    || keys[1] !== "id"
    || !customisationId
    || !data
    || typeof data !== "object"
    || Array.isArray(data)
  ) {
    throw new Error("Docs sub-scope manifest customisation is invalid.");
  }
  return { id: customisationId, data: Object.assign({}, data) };
}

function manifestPayload(payload) {
  return {
    documents: manifestDocs(payload),
    customisation: manifestCustomisation(payload)
  };
}

function normalizeDocument(record) {
  var docId = cleanString(record && record.doc_id);
  var title = cleanString(record && record.title);
  var normalizedRecord = Object.assign({}, record || {}, {
    doc_id: docId,
    title: title
  });
  if (
    normalizedRecord.customisation
    && typeof normalizedRecord.customisation === "object"
    && !Array.isArray(normalizedRecord.customisation)
  ) {
    normalizedRecord.customisation = Object.freeze(
      Object.assign({}, normalizedRecord.customisation)
    );
  }
  return {
    docId: docId,
    title: title,
    record: Object.freeze(normalizedRecord)
  };
}

function normalizeDocuments(records) {
  return (Array.isArray(records) ? records : []).map(normalizeDocument).filter(function (record) {
    return record.docId;
  });
}

function resolveReportContribution(context) {
  var hasSuppliedContribution = context && Object.prototype.hasOwnProperty.call(
    context,
    "subscopeReportContributionPromise"
  );
  var contribution = hasSuppliedContribution
    ? context.subscopeReportContributionPromise
    : context && context.subscopeReportContribution;
  if (!hasSuppliedContribution && contribution == null) {
    var reportMeta = context && context.reportMeta ? context.reportMeta : {};
    var subScopeIdValue = cleanId(reportMeta.subScope);
    var subScope = findSubScope(context, subScopeIdValue);
    contribution = resolvePublicDocsSubscopeCustomisation(
      subScope && subScope.subScopeCustomisation,
      {
        collection: collectionTarget(
          context && context.viewerScope,
          subScopeIdValue
        )
      }
    );
  }
  return Promise.resolve(contribution).then(function (resolved) {
    if (resolved == null) return null;
    if (typeof resolved !== "object" || Array.isArray(resolved)) {
      throw new Error("Docs sub-scope report contribution is invalid.");
    }
    return resolved;
  });
}

function contributionCallback(contribution, name) {
  return contribution && typeof contribution[name] === "function"
    ? contribution[name]
    : null;
}

function subScopesFromRoute(context) {
  var routeContext = context && context.routeContext ? context.routeContext : {};
  return Array.isArray(routeContext.subScopes) ? routeContext.subScopes : [];
}

function subScopesFromConfigs(context) {
  var viewerScope = cleanId(context && context.viewerScope);
  var configs = Array.isArray(context && context.scopeConfigs) ? context.scopeConfigs : [];
  var scopeConfig = configs.find(function (config) {
    return cleanId(config && (config.scope_id || config.scopeId)) === viewerScope;
  });
  return scopeConfig && Array.isArray(scopeConfig.subScopes) ? scopeConfig.subScopes : [];
}

function subScopeId(record) {
  return cleanId(record && (record.subScope || record.sub_scope));
}

function findSubScope(context, subScopeIdValue) {
  var target = cleanId(subScopeIdValue);
  if (!target) return null;
  var candidates = subScopesFromRoute(context).concat(subScopesFromConfigs(context));
  return candidates.find(function (record) {
    return subScopeId(record) === target;
  }) || null;
}

function subScopeTitle(record, fallback) {
  return cleanString(record && record.title) || humanize(fallback);
}

function manifestUrl(record) {
  return cleanString(record && (record.manifestUrl || record.manifest_url));
}

function byIdUrlBase(record) {
  return cleanString(record && (record.byIdUrlBase || record.by_id_url_base)).replace(/\/+$/, "");
}

function currentSubdocId() {
  if (typeof window === "undefined" || !window.location) return "";
  return cleanString(new URLSearchParams(window.location.search).get("subdoc"));
}

function byIdPayloadUrl(state, docId) {
  if (!state.byIdUrlBase) return "";
  return state.byIdUrlBase + "/" + encodeURIComponent(docId) + ".json";
}

function collectionTarget(scope, subScope) {
  return {
    scope: cleanId(scope),
    sub_scope: cleanId(subScope)
  };
}

function detailTarget(state, docId) {
  return {
    scope: state.viewerScope,
    sub_scope: state.subScopeId,
    doc_id: cleanString(docId)
  };
}

function documentRecord(doc) {
  return doc && doc.record ? doc.record : Object.freeze({});
}

function detailMetadataRecord(state, docId, payload) {
  var doc = state.docs.find(function (record) { return record.docId === docId; });
  var manifestRecord = documentRecord(doc);
  var payloadRecord = payload && typeof payload === "object" ? payload : {};
  var record = { doc_id: docId };
  [
    "title",
    "summary",
    "date",
    "date_display",
    "added_date",
    "last_updated",
    "ui_status",
    "publishable"
  ].forEach(function (fieldName) {
    if (Object.prototype.hasOwnProperty.call(payloadRecord, fieldName)) {
      record[fieldName] = payloadRecord[fieldName];
    } else if (Object.prototype.hasOwnProperty.call(manifestRecord, fieldName)) {
      record[fieldName] = manifestRecord[fieldName];
    }
  });
  return Object.freeze(record);
}

function projectDetailInfo(state, docId, payload, metadata) {
  var project = contributionCallback(state.contribution, "projectDetailInfo");
  if (!project) return null;
  var doc = state.docs.find(function (record) { return record.docId === docId; });
  var projected = project({
    collection: collectionTarget(state.viewerScope, state.subScopeId),
    data: state.customisationData,
    document: documentRecord(doc),
    metadata: metadata,
    payload: payload,
    target: detailTarget(state, docId)
  });
  if (projected == null) return null;
  if (typeof projected !== "object" || Array.isArray(projected)) {
    throw new Error("Docs sub-scope detail information projection is invalid.");
  }
  return projected;
}

function contributionEvent(context, subScopeIdValue, detail) {
  var contribution = context && context.resolvedSubscopeReportContribution;
  var notify = contributionCallback(contribution, "notify");
  if (!notify) return;
  notify(Object.assign({
    access: context && context.managementContext ? "manage" : "public",
    collection: collectionTarget(context && context.viewerScope, subScopeIdValue)
  }, detail || {}));
}

function notifyContribution(state, detail) {
  var notify = contributionCallback(state.contribution, "notify");
  if (!notify) return;
  notify(Object.assign({
    access: state.managementContext ? "manage" : "public",
    collection: collectionTarget(state.viewerScope, state.subScopeId)
  }, detail || {}));
}

function filterValuesPayload(state) {
  var payload = {};
  state.filterValues.forEach(function (value, filterId) {
    payload[filterId] = cleanString(value);
  });
  return Object.freeze(payload);
}

function writeSubdocUrl(state, docId, mode) {
  if (typeof window === "undefined" || !window.history || !window.location) return;
  var url = new URL(window.location.href);
  if (state.parentDocId) url.searchParams.set("doc", state.parentDocId);
  if (docId) {
    url.searchParams.set("subdoc", docId);
  } else {
    url.searchParams.delete("subdoc");
  }
  var nextState = Object.assign({}, window.history.state || {}, {
    docId: state.parentDocId || url.searchParams.get("doc") || "",
    hash: url.hash ? url.hash.slice(1) : "",
    reportParams: docId ? { subdoc: docId } : {}
  });
  if (mode === "replace") {
    window.history.replaceState(nextState, "", url.pathname + url.search + url.hash);
    return;
  }
  window.history.pushState(nextState, "", url.pathname + url.search + url.hash);
}

function collectionTitle(state) {
  return subScopeTitle(state.subScope, state.subScopeId);
}

function renderStatus(state, visibleCount) {
  var totalCount = state.docs.length;
  var scopeTitle = subScopeTitle(state.subScope, state.subScopeId);
  if (visibleCount === totalCount) {
    state.statusNode.textContent = totalCount + " " + scopeTitle + " "
      + (totalCount === 1 ? "document" : "documents");
    return;
  }
  state.statusNode.textContent = visibleCount + " of " + totalCount + " "
    + scopeTitle + " " + (totalCount === 1 ? "document" : "documents");
}

function appendDocRow(state, doc) {
  var docId = doc.docId;
  var row = document.createElement("li");
  row.className = "docsViewerReport__row";
  row.dataset.reportSubdocId = docId;

  var leadingHost = document.createElement("span");
  leadingHost.className = "docsViewerReport__rowContribution docsViewerReport__rowContribution--leading";
  leadingHost.dataset.reportContributionHost = "row-leading";

  var title = document.createElement("button");
  title.className = "docsViewerReport__cellLink docsViewerReport__subscopeButton";
  title.type = "button";

  var titlePrefixHost = document.createElement("span");
  titlePrefixHost.className = "docsViewerReport__rowContribution docsViewerReport__rowContribution--titlePrefix";
  titlePrefixHost.dataset.reportContributionHost = "title-prefix";

  var titleText = document.createElement("span");
  titleText.className = "docsViewerReport__title";
  titleText.textContent = doc.title || humanize(docId) || docId;

  var trailingHost = document.createElement("span");
  trailingHost.className = "docsViewerReport__rowContribution docsViewerReport__rowContribution--trailing";
  trailingHost.dataset.reportContributionHost = "row-trailing";

  var renderRow = contributionCallback(state.contribution, "renderRow");
  var rowResult = renderRow ? renderRow({
    collection: collectionTarget(state.viewerScope, state.subScopeId),
    document: documentRecord(doc),
    leadingHost: leadingHost,
    titlePrefixHost: titlePrefixHost,
    trailingHost: trailingHost
  }) : null;
  if (titlePrefixHost.childNodes.length) title.appendChild(titlePrefixHost);
  title.appendChild(titleText);
  var accessibleLabels = rowResult && Array.isArray(rowResult.accessibleLabels)
    ? rowResult.accessibleLabels.map(cleanString).filter(Boolean)
    : [];
  if (accessibleLabels.length) {
    title.setAttribute("aria-label", [titleText.textContent].concat(accessibleLabels).join(", "));
  }
  title.addEventListener("click", function () {
    writeSubdocUrl(state, docId, "push");
    renderDetailById(state, docId);
  });
  if (leadingHost.childNodes.length) row.appendChild(leadingHost);
  row.appendChild(title);
  if (trailingHost.childNodes.length) row.appendChild(trailingHost);
  state.rowsNode.appendChild(row);
  return {
    hasLeadingContent: leadingHost.childNodes.length > 0,
    leadingHost: leadingHost,
    row: row
  };
}

function renderFilterShell(context, subScope) {
  var toolbar = document.createElement("div");
  toolbar.className = "docsViewerReport__toolbar docsViewerReport__subscopeFilterToolbar";
  toolbar.dataset.docsSubscopeFilters = "true";

  filterIdSequence += 1;
  var searchId = "docs-subscope-title-filter-" + cleanId(
    context && context.viewerScope
  ) + "-" + subScopeId(subScope) + "-" + filterIdSequence;
  var searchLabel = document.createElement("label");
  searchLabel.className = "docsViewerReport__selectLabel visually-hidden";
  searchLabel.htmlFor = searchId;
  searchLabel.textContent = "Filter " + subScopeTitle(
    subScope,
    subScopeId(subScope)
  ) + " by title";

  var search = document.createElement("span");
  search.className = "docsViewerReport__search";
  var input = document.createElement("input");
  input.className = "docsViewerReport__searchInput";
  input.id = searchId;
  input.type = "search";
  input.autocomplete = "off";
  input.spellcheck = false;
  input.placeholder = "search";

  var clear = document.createElement("button");
  clear.className = "docsViewerReport__searchClear";
  clear.type = "button";
  clear.textContent = "\u00D7";
  clear.hidden = true;
  search.appendChild(input);
  search.appendChild(clear);

  var extensions = document.createElement("div");
  extensions.className = "docsViewerReport__filters";
  extensions.hidden = true;

  toolbar.appendChild(searchLabel);
  toolbar.appendChild(extensions);
  toolbar.appendChild(search);
  return {
    clearNode: clear,
    extensionsNode: extensions,
    inputNode: input,
    toolbarNode: toolbar
  };
}

function renderShell(context, subScope) {
  var root = context.reportRoot;
  clearNode(root);
  root.dataset.reportColumns = "1";
  root.dataset.reportSubscope = subScopeId(subScope);

  var filters = renderFilterShell(context, subScope);
  var status = document.createElement("p");
  status.className = "docsViewerReport__status visually-hidden";
  status.setAttribute("aria-live", "polite");
  status.setAttribute("role", "status");

  var table = document.createElement("div");
  table.className = "docsViewerReport__table";

  var head = document.createElement("div");
  head.className = "docsViewerReport__head";
  head.hidden = true;

  var rows = document.createElement("ul");
  rows.className = "docsViewerReport__rows";
  rows.setAttribute("aria-label", subScopeTitle(subScope, subScopeId(subScope)));

  table.appendChild(head);
  table.appendChild(rows);
  root.appendChild(filters.toolbarNode);
  root.appendChild(status);
  root.appendChild(table);

  return {
    filterClearNode: filters.clearNode,
    filterExtensionsNode: filters.extensionsNode,
    filterInputNode: filters.inputNode,
    filterToolbarNode: filters.toolbarNode,
    headNode: head,
    rowsNode: rows,
    statusNode: status,
    tableNode: table
  };
}

function configureContributionFilters(state) {
  state.filters = [];
  state.filterValues = new Map();
  var createFilters = contributionCallback(state.contribution, "createFilters");
  if (!createFilters) return;
  var created = createFilters({
    access: state.managementContext ? "manage" : "public",
    collection: collectionTarget(state.viewerScope, state.subScopeId),
    data: state.customisationData,
    documents: Object.freeze(state.docs.map(documentRecord))
  });
  if (!Array.isArray(created)) {
    throw new Error("Docs sub-scope customisation filters must be an array.");
  }
  var seen = new Set();
  state.filters = created.map(function (filter) {
    var filterId = cleanId(filter && filter.id);
    if (
      !filterId
      || seen.has(filterId)
      || typeof filter.matches !== "function"
      || typeof filter.render !== "function"
    ) {
      throw new Error("Docs sub-scope customisation filter is invalid.");
    }
    seen.add(filterId);
    state.filterValues.set(filterId, cleanString(filter.initialValue));
    return filter;
  });
}

function renderContributionFilters(state) {
  clearNode(state.filterExtensionsNode);
  state.filterExtensionsNode.hidden = state.filters.length === 0;
  state.filters.forEach(function (filter) {
    var filterId = cleanId(filter.id);
    var host = document.createElement("div");
    host.dataset.docsSubscopeCustomFilter = filterId;
    filter.render({
      collection: collectionTarget(state.viewerScope, state.subScopeId),
      host: host,
      value: state.filterValues.get(filterId) || "",
      setValue: function (value) {
        state.filterValues.set(filterId, cleanString(value));
        renderListProjectionContained(state, "custom-filter");
      }
    });
    if (host.childNodes.length) state.filterExtensionsNode.appendChild(host);
  });
  state.filterExtensionsNode.hidden = !state.filterExtensionsNode.childNodes.length;
}

function updateFilterControls(state) {
  var normalizedQuery = normalizeDocsSubscopeFilterValue(state.query);
  if (state.filterInputNode.value !== state.query) {
    state.filterInputNode.value = state.query;
  }
  state.filterClearNode.hidden = !normalizedQuery;
  state.filterClearNode.setAttribute(
    "aria-label",
    "Clear " + collectionTitle(state) + " title filter"
  );
  state.filterClearNode.title = state.filterClearNode.getAttribute("aria-label");
  renderContributionFilters(state);
}

function compareText(left, right) {
  var leftValue = cleanString(left).normalize("NFKC").toLowerCase();
  var rightValue = cleanString(right).normalize("NFKC").toLowerCase();
  if (leftValue < rightValue) return -1;
  if (leftValue > rightValue) return 1;
  var leftRaw = cleanString(left);
  var rightRaw = cleanString(right);
  if (leftRaw < rightRaw) return -1;
  if (leftRaw > rightRaw) return 1;
  return 0;
}

function compareTitleAscending(left, right) {
  return compareText(left.title, right.title) || compareText(left.docId, right.docId);
}

function lastUpdatedTimestamp(doc) {
  var value = cleanString(doc && doc.record && doc.record.last_updated);
  var match = /^(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2}):(\d{2})(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)?$/.exec(value);
  if (!match) return NaN;
  if (/Z$|[+-]\d{2}:\d{2}$/.test(value)) {
    return Date.parse(value.replace(" ", "T"));
  }
  var parts = match.slice(1, 7).map(function (part, index) {
    if (part == null) return index < 3 ? NaN : 0;
    return Number(part);
  });
  var timestamp = Date.UTC(
    parts[0],
    parts[1] - 1,
    parts[2],
    parts[3],
    parts[4],
    parts[5]
  );
  var date = new Date(timestamp);
  if (
    date.getUTCFullYear() !== parts[0]
    || date.getUTCMonth() !== parts[1] - 1
    || date.getUTCDate() !== parts[2]
    || date.getUTCHours() !== parts[3]
    || date.getUTCMinutes() !== parts[4]
    || date.getUTCSeconds() !== parts[5]
  ) return NaN;
  return timestamp;
}

function compareLastUpdatedDescending(left, right) {
  var leftTimestamp = lastUpdatedTimestamp(left);
  var rightTimestamp = lastUpdatedTimestamp(right);
  var leftValid = Number.isFinite(leftTimestamp);
  var rightValid = Number.isFinite(rightTimestamp);
  if (leftValid && !rightValid) return -1;
  if (!leftValid && rightValid) return 1;
  if (leftValid && rightValid && leftTimestamp !== rightTimestamp) {
    return rightTimestamp - leftTimestamp;
  }
  return compareTitleAscending(left, right);
}

function visibleDocuments(state) {
  var visible = projectDocsSubscopeDocuments(state.docs, {
    query: state.query
  }).filter(function (doc) {
    return state.filters.every(function (filter) {
      var filterId = cleanId(filter.id);
      var matches = filter.matches({
        collection: collectionTarget(state.viewerScope, state.subScopeId),
        document: documentRecord(doc),
        value: state.filterValues.get(filterId) || ""
      });
      if (typeof matches !== "boolean") {
        throw new Error(
          "Docs sub-scope customisation filter must return a boolean: " + filterId
        );
      }
      return matches;
    });
  });
  var compareCustom = contributionCallback(state.contribution, "compareListDocuments");
  return visible.slice().sort(function (left, right) {
    if (!compareCustom) {
      return state.sortMode === "last-updated-desc"
        ? compareLastUpdatedDescending(left, right)
        : compareTitleAscending(left, right);
    }
    var comparison = compareCustom({
      collection: collectionTarget(state.viewerScope, state.subScopeId),
      left: documentRecord(left),
      right: documentRecord(right),
      sortMode: state.sortMode
    });
    if (!Number.isFinite(comparison)) {
      throw new Error("Docs sub-scope custom list comparator must return a finite number.");
    }
    return comparison;
  });
}

function bindFilterControls(state) {
  state.filterInputNode.addEventListener("input", function () {
    state.query = state.filterInputNode.value;
    renderListProjectionContained(state, "title-filter");
  });
  state.filterClearNode.addEventListener("click", function () {
    state.query = "";
    state.filterInputNode.value = "";
    renderListProjectionContained(state, "title-filter-clear");
    state.filterInputNode.focus();
  });
}

function listSortContext(state) {
  return {
    mode: state.sortMode,
    setMode: function (mode) {
      var nextMode = cleanString(mode);
      var compareCustom = contributionCallback(state.contribution, "compareListDocuments");
      if (
        !nextMode
        || (
          !["title-asc", "last-updated-desc"].includes(nextMode)
          && !compareCustom
        )
      ) {
        throw new Error("Docs sub-scope sort mode is invalid: " + nextMode);
      }
      state.sortMode = nextMode;
      renderListProjectionContained(state, "sort-change");
      return nextMode;
    }
  };
}

function renderListHead(state, documents) {
  clearNode(state.headNode);
  state.headNode.hidden = true;
  var renderHead = contributionCallback(state.contribution, "renderListHead");
  if (!renderHead) return;
  renderHead({
    collection: collectionTarget(state.viewerScope, state.subScopeId),
    documents: Object.freeze(documents.map(documentRecord)),
    host: state.headNode,
    sort: listSortContext(state)
  });
  state.headNode.hidden = !state.headNode.childNodes.length;
}

function renderListToolbar(state, documents) {
  if (state.listToolbarNode) {
    state.listToolbarNode.remove();
    state.listToolbarNode = null;
  }
  var renderToolbar = contributionCallback(state.contribution, "renderListToolbar");
  if (!renderToolbar) return;
  var host = document.createElement("div");
  host.className = "docsViewerReport__contributionToolbar docsViewerReport__contributionToolbar--list";
  host.dataset.reportContributionHost = "list-toolbar";
  renderToolbar({
    collection: collectionTarget(state.viewerScope, state.subScopeId),
    documents: Object.freeze(documents.map(documentRecord)),
    handleContributionError: function (error, reason) {
      try {
        publishState(state, "error", null, cleanString(reason));
      } catch (_notifyError) {
        // The contained report error below remains authoritative.
      }
      renderError(
        state.root,
        error && error.message
          ? error.message
          : "Failed to render docs sub-scope customisation."
      );
    },
    host: host,
    refreshAndOpenDocument: function (target) {
      return refreshAndOpenDocument(state, target);
    },
    refreshCollection: function (target) {
      return refreshCollection(state, target);
    },
    sort: listSortContext(state)
  });
  if (!host.childNodes.length) return;
  state.filterToolbarNode.appendChild(host);
  state.listToolbarNode = host;
}

function renderRows(state, docs) {
  clearNode(state.rowsNode);
  state.root.removeAttribute("data-report-leading-column");
  renderStatus(state, docs.length);
  if (!docs.length) {
    var empty = document.createElement("li");
    empty.className = "docsViewerReport__empty";
    empty.textContent = state.docs.length
      ? "No " + collectionTitle(state).toLowerCase() + " match the current filters."
      : "No documents are available in " + collectionTitle(state) + ".";
    state.rowsNode.appendChild(empty);
    return;
  }
  var rows = docs.map(function (doc) {
    return appendDocRow(state, doc);
  });
  if (!rows.some(function (record) { return record.hasLeadingContent; })) return;
  state.root.dataset.reportLeadingColumn = "true";
  rows.forEach(function (record) {
    if (!record.leadingHost.parentNode) {
      record.row.insertBefore(record.leadingHost, record.row.firstChild);
    }
  });
}

function publishState(state, reportState, target, reason, detail) {
  notifyContribution(state, Object.assign({
    type: "state",
    state: cleanString(reportState),
    reason: cleanString(reason),
    target: target || null,
    refreshDocument: function (documentTarget) {
      return refreshAndOpenDocument(state, documentTarget);
    },
    refreshCollection: function (collection) {
      return refreshCollection(state, collection);
    }
  }, detail || {}));
}

function invalidateDetailRequest(state) {
  state.detailRequestVersion += 1;
  return state.detailRequestVersion;
}

function renderListProjection(state) {
  var documents = visibleDocuments(state);
  updateFilterControls(state);
  renderListToolbar(state, documents);
  renderListHead(state, documents);
  renderRows(state, documents);
  notifyContribution(state, {
    type: "projection",
    documents: Object.freeze(documents.map(documentRecord)),
    filterValues: filterValuesPayload(state),
    sort: state.sortMode,
    reason: "filters-projected"
  });
}

function renderListProjectionContained(state, reason) {
  try {
    renderListProjection(state);
    return true;
  } catch (error) {
    try {
      publishState(state, "error", null, cleanString(reason) || "contribution-failed");
    } catch (_notifyError) {
      // The contained report error below remains authoritative.
    }
    renderError(
      state.root,
      error && error.message
        ? error.message
        : "Failed to render docs sub-scope customisation."
    );
    return false;
  }
}

function renderListView(state) {
  invalidateDetailRequest(state);
  state.validDetailId = "";
  state.root.dataset.reportState = "list";
  state.filterToolbarNode.hidden = false;
  state.tableNode.hidden = false;
  state.statusNode.hidden = false;
  if (state.detailNode) state.detailNode.hidden = true;
  if (!renderListProjectionContained(state, "list-projection-failed")) return;
  if (state.listToolbarNode) state.listToolbarNode.hidden = false;
  publishState(state, "list", null, "list-view");
}

function detailTitle(payload, fallback) {
  return cleanString(payload && payload.title) || humanize(fallback) || fallback;
}

function renderDetailShell(state, docId) {
  if (state.detailNode) state.detailNode.remove();
  state.validDetailId = "";

  var section = document.createElement("section");
  section.className = "docsReportDetail";
  section.setAttribute("aria-label", "Loading " + (humanize(docId) || docId));

  var header = document.createElement("div");
  header.className = "docsReportDetail__header";

  var back = document.createElement("button");
  back.className = "docsViewerReport__button docsReportDetail__iconButton docsReportDetail__back";
  back.type = "button";
  back.textContent = "\u2190";
  var backLabel = "Back to all "
    + subScopeTitle(state.subScope, state.subScopeId).toLowerCase();
  back.setAttribute("aria-label", backLabel);
  back.title = backLabel;
  back.addEventListener("click", function () {
    writeSubdocUrl(state, "", "push");
    renderListView(state);
  });

  var body = document.createElement("article");
  body.className = "docsReportDetail__body docsViewer__content content";

  header.appendChild(back);
  section.appendChild(header);
  section.appendChild(body);
  state.root.appendChild(section);
  state.detailNode = section;
  state.detailHeaderNode = header;
  state.detailBodyNode = body;
}

function renderDetailToolbar(state, docId) {
  var renderToolbar = contributionCallback(state.contribution, "renderDetailToolbar");
  if (!renderToolbar || !state.detailHeaderNode) return;
  var host = document.createElement("div");
  host.className = "docsViewerReport__contributionToolbar docsViewerReport__contributionToolbar--detail";
  host.dataset.reportContributionHost = "detail-toolbar";
  var doc = state.docs.find(function (record) { return record.docId === docId; });
  renderToolbar({
    collection: collectionTarget(state.viewerScope, state.subScopeId),
    commitDeletedDocument: function (target) {
      return reconcileCommittedDeletion(state, target);
    },
    document: documentRecord(doc),
    host: host,
    refreshAndOpenDocument: function (target) {
      return refreshAndOpenDocument(state, target);
    },
    refreshCollection: function (target) {
      return refreshCollection(state, target);
    },
    target: detailTarget(state, docId)
  });
  if (host.childNodes.length) {
    state.detailHeaderNode.appendChild(host);
  }
}

function renderDetailPayload(state, docId, payload) {
  var payloadDocId = cleanString(payload && payload.doc_id);
  if (payloadDocId !== docId) {
    throw new Error("Docs sub-scope detail payload did not match the requested document.");
  }
  state.detailPayloads[docId] = payload;
  state.detailNode.dataset.reportSubdocId = docId;
  state.detailNode.dataset.reportSubdocTitle = detailTitle(payload, docId);
  state.detailNode.dataset.reportSubdocUpdated = cleanString(payload && payload.last_updated);
  state.detailNode.setAttribute("aria-label", detailTitle(payload, docId));
  state.detailBodyNode.innerHTML = payload && payload.content_html ? payload.content_html : "";
  state.validDetailId = docId;
  renderDetailToolbar(state, docId);
  var metadata = detailMetadataRecord(state, docId, payload);
  publishState(state, "detail", {
    scope: state.viewerScope,
    sub_scope: state.subScopeId,
    doc_id: docId
  }, "detail-loaded", {
    info: projectDetailInfo(state, docId, payload, metadata),
    record: metadata
  });
}

function renderDetailById(state, docId, options) {
  var requestVersion = invalidateDetailRequest(state);
  publishState(state, "loading", null, "detail-navigation");
  state.root.dataset.reportState = "detail";
  state.filterToolbarNode.hidden = true;
  state.tableNode.hidden = true;
  state.statusNode.hidden = true;
  if (state.listToolbarNode) state.listToolbarNode.hidden = true;
  renderDetailShell(state, docId);

  var url = byIdPayloadUrl(state, docId);
  if (!url) {
    publishState(state, "error", null, "missing-detail-path");
    renderError(state.root, "Docs sub-scope by-id payload path is not configured: " + state.subScopeId);
    return Promise.resolve(true);
  }

  return fetchJson(url, "Failed to load docs sub-scope detail payload", options)
    .then(function (payload) {
      if (requestVersion !== state.detailRequestVersion) return true;
      renderDetailPayload(state, docId, payload);
      return true;
    })
    .catch(function (error) {
      if (requestVersion !== state.detailRequestVersion) return true;
      publishState(state, "error", null, "detail-load-failed");
      renderError(state.root, error && error.message ? error.message : "Failed to render docs sub-scope detail.");
      return true;
    });
}

function renderError(root, message) {
  clearNode(root);
  root.dataset.reportState = "error";
  var note = document.createElement("p");
  note.className = "docsViewerReport__status is-error";
  note.textContent = message;
  root.appendChild(note);
}

function assertCollectionTarget(state, target) {
  var targetScope = cleanId(target && target.scope);
  var targetSubScope = cleanId(target && target.sub_scope);
  var targetDocId = cleanString(target && target.doc_id);
  if (
    !targetDocId
    || targetScope !== state.viewerScope
    || targetSubScope !== state.subScopeId
  ) {
    throw new Error("Deleted sub-scope document target did not match the mounted collection.");
  }
  return targetDocId;
}

function assertCreatedCollectionTarget(state, target) {
  var targetScope = cleanId(target && target.scope);
  var targetSubScope = cleanId(target && target.sub_scope);
  var targetDocId = cleanString(target && target.doc_id);
  if (
    !targetDocId
    || targetScope !== state.viewerScope
    || targetSubScope !== state.subScopeId
  ) {
    throw new Error("Created sub-scope document target did not match the mounted collection.");
  }
  return targetDocId;
}

function assertExactCollectionTarget(state, target) {
  var keys = Object.keys(target || {}).sort();
  var targetScope = cleanId(target && target.scope);
  var targetSubScope = cleanId(target && target.sub_scope);
  if (
    keys.length !== 2
    || keys[0] !== "scope"
    || keys[1] !== "sub_scope"
    || targetScope !== state.viewerScope
    || targetSubScope !== state.subScopeId
  ) {
    throw new Error("Imported package target did not match the mounted collection.");
  }
  return collectionTarget(targetScope, targetSubScope);
}

function focusFirstListRow(state) {
  var first = state.rowsNode && state.rowsNode.querySelector(".docsViewerReport__subscopeButton");
  if (!first || typeof first.focus !== "function") return;
  try {
    first.focus({ preventScroll: true });
  } catch (_error) {
    first.focus();
  }
}

function publishDocumentsRefresh(state, reason) {
  notifyContribution(state, {
    type: "refresh",
    data: state.customisationData,
    documents: Object.freeze(state.docs.map(documentRecord)),
    reason: cleanString(reason)
  });
}

function applyManifest(state, manifest) {
  var descriptorId = cleanId(
    state.subScope
    && state.subScope.subScopeCustomisation
    && state.subScope.subScopeCustomisation.id
  );
  var manifestCustomisation = manifest.customisation;
  var manifestId = cleanId(manifestCustomisation && manifestCustomisation.id);
  if (descriptorId !== manifestId) {
    throw new Error(
      "Docs sub-scope customisation identity did not match its manifest projection."
    );
  }
  state.docs = manifest.documents;
  state.customisationData = manifestCustomisation
    ? Object.freeze(Object.assign({}, manifestCustomisation.data))
    : Object.freeze({});
  configureContributionFilters(state);
  state.docIds = state.docs.map(function (doc) { return doc.docId; });
}

function refreshAndOpenDocument(state, target) {
  var docId = assertCreatedCollectionTarget(state, target);
  if (!state.mounted) {
    return Promise.reject(new Error(
      "Document was created, but the mounted sub-scope report is no longer available."
    ));
  }
  return fetchJson(
    state.manifestUrl,
    "Failed to refresh docs sub-scope manifest",
    { cache: "no-store" }
  )
    .then(manifestPayload)
    .then(function (manifest) {
      if (!state.mounted) {
        throw new Error(
          "Document was created, but the mounted sub-scope report is no longer available."
        );
      }
      applyManifest(state, manifest);
      var matches = state.docs.filter(function (doc) { return doc.docId === docId; });
      if (matches.length !== 1) {
        throw new Error(
          "Document was created, but the refreshed report did not contain one exact target."
        );
      }
      publishDocumentsRefresh(state, "document-created-refresh");
      writeSubdocUrl(state, docId, "replace");
      return renderDetailById(state, docId, { cache: "no-store" });
    })
    .then(function () {
      if (state.validDetailId !== docId) {
        throw new Error(
          "Document was created, but its report detail could not be opened."
        );
      }
      return target;
    });
}

function refreshCollection(state, target) {
  var collection = assertExactCollectionTarget(state, target);
  var activeDetailId = state.root.dataset.reportState === "detail"
    ? cleanString(state.validDetailId)
    : "";
  if (!state.mounted) {
    return Promise.reject(new Error(
      "Package import completed, but the mounted sub-scope report is no longer available."
    ));
  }
  return fetchJson(
    state.manifestUrl,
    "Failed to refresh docs sub-scope manifest",
    { cache: "no-store" }
  )
    .then(manifestPayload)
    .then(function (manifest) {
      if (!state.mounted) {
        throw new Error(
          "Package import completed, but the mounted sub-scope report is no longer available."
        );
      }
      applyManifest(state, manifest);
      publishDocumentsRefresh(state, "package-import-refresh");
      if (!activeDetailId) {
        renderListView(state);
        return collection;
      }
      var matches = state.docs.filter(function (doc) {
        return doc.docId === activeDetailId;
      });
      if (matches.length !== 1) {
        throw new Error(
          "Package import completed, but the current report detail is no longer available."
        );
      }
      return renderDetailById(state, activeDetailId, { cache: "no-store" })
        .then(function () {
          if (state.validDetailId !== activeDetailId) {
            throw new Error(
              "Package import completed, but the current report detail could not be refreshed."
            );
          }
          return collection;
        });
    });
}

function returnFromDeletedDetail(state, docId) {
  if (state.validDetailId === docId) {
    if (state.detailNode) state.detailNode.remove();
    state.detailNode = null;
    state.detailHeaderNode = null;
    state.detailBodyNode = null;
    writeSubdocUrl(state, "", "replace");
    renderListView(state);
    focusFirstListRow(state);
    return;
  }
  if (state.root.dataset.reportState === "list") {
    renderListView(state);
  }
}

function reconcileCommittedDeletion(state, target) {
  var docId = assertCollectionTarget(state, target);
  if (!state.mounted) {
    return Promise.resolve({ reconciled: false, mode: "unmounted" });
  }
  if (!Array.isArray(state.docs)) {
    return Promise.reject(new Error(
      "Document was deleted, but the report manifest could not be reconciled."
    ));
  }
  var matchingIndexes = [];
  state.docs.forEach(function (doc, index) {
    if (doc.docId === docId) matchingIndexes.push(index);
  });
  if (matchingIndexes.length !== 1) {
    return Promise.reject(new Error(
      "Document was deleted, but the report manifest did not contain one exact target."
    ));
  }
  state.docs = state.docs.filter(function (_doc, index) {
    return index !== matchingIndexes[0];
  });
  state.docIds = state.docs.map(function (doc) { return doc.docId; });
  delete state.detailPayloads[docId];
  publishDocumentsRefresh(state, "document-deleted-local");
  returnFromDeletedDetail(state, docId);
  return Promise.resolve({ reconciled: true, mode: "local" });
}

/**
 * Mounts the manifest-backed sub-scope reader with an optional caller-owned
 * contribution. The report retains collection identity, membership,
 * navigation, and detail validation.
 *
 * @param {Object} context
 * @returns {Promise<boolean>}
 */
function mountResolvedDocsSubscopeReport(context, contribution) {
  var root = context && context.reportRoot;
  var reportMeta = context && context.reportMeta ? context.reportMeta : {};
  var subScopeIdValue = cleanId(reportMeta.subScope);
  if (!root) return Promise.resolve(false);
  if (!subScopeIdValue) {
    contributionEvent(context, subScopeIdValue, {
      type: "state",
      state: "error",
      reason: "missing-sub-scope",
      target: null
    });
    renderError(root, "This report is missing report sub_scope.");
    return Promise.resolve(true);
  }

  var subScope = findSubScope(context, subScopeIdValue);
  if (!subScope) {
    contributionEvent(context, subScopeIdValue, {
      type: "state",
      state: "error",
      reason: "unconfigured-sub-scope",
      target: null
    });
    renderError(root, "Docs sub-scope is not configured: " + subScopeIdValue);
    return Promise.resolve(true);
  }

  var url = manifestUrl(subScope);
  if (!url) {
    contributionEvent(context, subScopeIdValue, {
      type: "state",
      state: "error",
      reason: "missing-manifest",
      target: null
    });
    renderError(root, "Docs sub-scope manifest is not configured: " + subScopeIdValue);
    return Promise.resolve(true);
  }

  var refs = renderShell(context, subScope);
  refs.statusNode.textContent = "Loading " + subScopeTitle(subScope, subScopeIdValue) + "...";
  var state = {
    root: root,
    parentDocId: cleanString(context && context.doc && context.doc.doc_id),
    subScope: subScope,
    subScopeId: subScopeIdValue,
    manifestUrl: url,
    byIdUrlBase: byIdUrlBase(subScope),
    docs: [],
    docIds: [],
    customisationData: {},
    query: "",
    sortMode: "title-asc",
    detailRequestVersion: 0,
    detailPayloads: {},
    contribution: contribution,
    managementContext: Boolean(context && context.managementContext),
    filterClearNode: refs.filterClearNode,
    filterExtensionsNode: refs.filterExtensionsNode,
    filterInputNode: refs.filterInputNode,
    filterToolbarNode: refs.filterToolbarNode,
    filters: [],
    filterValues: new Map(),
    headNode: refs.headNode,
    listToolbarNode: null,
    statusNode: refs.statusNode,
    tableNode: refs.tableNode,
    rowsNode: refs.rowsNode,
    validDetailId: "",
    viewerScope: cleanId(context && context.viewerScope),
    mounted: true
  };
  bindFilterControls(state);
  updateFilterControls(state);

  var parent = root.parentNode;
  var windowRef = root.ownerDocument && root.ownerDocument.defaultView;
  if (state.contribution && parent && windowRef && typeof windowRef.MutationObserver === "function") {
    state.unmountObserver = new windowRef.MutationObserver(function () {
      if (root.parentNode === parent) return;
      state.unmountObserver.disconnect();
      state.unmountObserver = null;
      state.mounted = false;
      invalidateDetailRequest(state);
      publishState(state, "unmounted", null, "report-unmount");
      notifyContribution(state, {
        type: "unmount",
        reason: "report-unmount"
      });
    });
    state.unmountObserver.observe(parent, { childList: true });
  }

  notifyContribution(state, {
    type: "mount",
    root: root
  });
  publishState(state, "loading", null, "report-loading");
  return fetchJson(url, "Failed to load docs sub-scope manifest").then(manifestPayload)
    .then(function (manifest) {
      applyManifest(state, manifest);
      notifyContribution(state, {
        type: "refresh",
        data: state.customisationData,
        documents: Object.freeze(state.docs.map(documentRecord)),
        reason: "documents-loaded"
      });
      var selectedDetailId = currentSubdocId();
      if (selectedDetailId) {
        if (state.docIds.indexOf(selectedDetailId) === -1) {
          publishState(state, "invalid", null, "unlisted-detail");
          renderError(root, "Docs sub-scope detail is not listed: " + selectedDetailId);
          return true;
        }
        return renderDetailById(state, selectedDetailId);
      }
      renderListView(state);
      return true;
    })
    .catch(function (error) {
      try {
        publishState(state, "error", null, "report-load-failed");
      } catch (_notifyError) {
        // The contained report error below remains authoritative.
      }
      renderError(root, error && error.message ? error.message : "Failed to render docs sub-scope report.");
      return true;
    });
}

export function mountDocsSubscopeReport(context) {
  var root = context && context.reportRoot;
  if (!root) return Promise.resolve(false);
  return resolveReportContribution(context)
    .then(function (contribution) {
      return mountResolvedDocsSubscopeReport(
        Object.assign({}, context, {
          resolvedSubscopeReportContribution: contribution
        }),
        contribution
      );
    })
    .catch(function (error) {
      renderError(
        root,
        error && error.message
          ? error.message
          : "Failed to resolve docs sub-scope customisation."
      );
      return true;
    });
}
