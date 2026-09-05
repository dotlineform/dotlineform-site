function searchText(value) {
  return String(value || "").normalize("NFKC").toLocaleLowerCase("en").trim();
}

/** Reject a media response for any other document or Work before opening the host. */
export function readSeriesWorkPresentation(payload, target, workId) {
  var actual = payload && payload.target;
  var presentation = payload && payload.presentation;
  if (!actual || actual.scope !== target.scope || actual.doc_id !== target.doc_id
    || (actual.sub_scope || "") !== (target.sub_scope || "")
    || !presentation || !presentation.target
    || presentation.target.kind !== "catalogue-work" || presentation.target.id !== workId) {
    throw new Error("Work media response does not match the selected Work and document.");
  }
  return presentation;
}

/** Read ordered generated members for the exact document that owns this report. */
export function readSeriesWorksRows(payload, target) {
  var actual = payload && payload.target;
  if (
    !payload || payload.schema !== "docs_series_works_report_v1"
    || !actual || actual.scope !== target.scope || actual.doc_id !== target.doc_id
    || (actual.sub_scope || "") !== (target.sub_scope || "")
    || !Array.isArray(payload.works)
  ) {
    throw new Error("Works in Series response does not match its document.");
  }
  return payload.works;
}

/** Filter only this Series' member rows, preserving its supplied order. */
export function filterSeriesWorks(rows, query) {
  var needle = searchText(query);
  return rows.filter(function (row) {
    return [row.work_id, row.title, row.year_display].some(function (value) {
      return searchText(value).includes(needle);
    });
  });
}

/** Mount a local, subject-driven table; all controls remain inside its document. */
export function mountSeriesWorksReport(context) {
  var root = context.reportRoot;
  var documentRef = root.ownerDocument;
  var target = context.documentTarget || {
    scope: context.viewerScope,
    doc_id: context.doc && context.doc.doc_id
  };
  var service = context.reportService;
  if (!service || typeof service.readSeriesWorks !== "function") {
    throw new Error("Works in Series requires the local report service.");
  }

  root.replaceChildren();
  var toolbar = documentRef.createElement("div");
  toolbar.className = "docsViewerReport__toolbar";
  var label = documentRef.createElement("label");
  label.textContent = "Filter works ";
  var filter = documentRef.createElement("input");
  filter.type = "search";
  filter.className = "docsViewer__fieldInput";
  label.appendChild(filter);
  var refresh = documentRef.createElement("button");
  refresh.type = "button";
  refresh.className = "docsViewerReport__button";
  refresh.textContent = "Refresh";
  toolbar.append(label, refresh);
  var status = documentRef.createElement("p");
  status.className = "docsViewerReport__status";
  status.setAttribute("aria-live", "polite");
  var viewport = documentRef.createElement("div");
  viewport.className = "docsViewerReport__seriesWorksViewport";
  viewport.tabIndex = 0;
  viewport.setAttribute("aria-label", "Series Works table");
  var table = documentRef.createElement("table");
  var head = documentRef.createElement("thead");
  var headings = documentRef.createElement("tr");
  ["Work", "Title", "Year"].forEach(function (title) {
    var cell = documentRef.createElement("th");
    cell.scope = "col";
    cell.textContent = title;
    headings.appendChild(cell);
  });
  head.appendChild(headings);
  var body = documentRef.createElement("tbody");
  table.append(head, body);
  viewport.appendChild(table);
  root.append(toolbar, status, viewport);
  var rows = [];
  var seriesLabel = "";
  var requestVersion = 0;
  var mediaRequestVersion = 0;

  function current(version) {
    return version === requestVersion && root.isConnected !== false
      && (typeof context.isCurrentDocument !== "function" || context.isCurrentDocument());
  }

  function renderRows() {
    mediaRequestVersion += 1;
    var visible = filterSeriesWorks(rows, filter.value);
    body.replaceChildren();
    visible.forEach(function (row) {
      var tr = documentRef.createElement("tr");
      [row.work_id, row.title, row.year_display].forEach(function (value, index) {
        var cell = documentRef.createElement("td");
        if (index === 1) {
          var link = documentRef.createElement("button");
          link.type = "button";
          link.className = "docsViewerReport__workTitleLink";
          link.textContent = value;
          link.addEventListener("click", function () { return openWork(row, link); });
          cell.appendChild(link);
        } else {
          cell.textContent = value;
        }
        tr.appendChild(cell);
      });
      body.appendChild(tr);
    });
    status.textContent = seriesLabel + " · " + visible.length + " of " + rows.length + " works";
  }

  function openWork(row, control) {
    var version = ++mediaRequestVersion;
    var listVersion = requestVersion;
    function isCurrent() {
      return version === mediaRequestVersion && current(listVersion) && root.contains(control);
    }
    status.textContent = "Loading " + row.title + "…";
    return service.readSeriesWorkMedia({ target: target, workId: row.work_id }).then(function (payload) {
      if (!isCurrent()) return;
      var presentation = readSeriesWorkPresentation(payload, target, row.work_id);
      if (typeof context.openMediaPresentation !== "function" || !context.openMediaPresentation({
        presentation: presentation,
        invocationControl: control,
        documentTarget: { scope: target.scope, subScope: target.sub_scope || "", docId: target.doc_id },
        isCurrentDocument: isCurrent
      })) throw new Error("Media View is unavailable for this document.");
      status.textContent = seriesLabel + " · " + filterSeriesWorks(rows, filter.value).length + " of " + rows.length + " works";
    }).catch(function (error) {
      if (isCurrent()) status.textContent = error.message;
    });
  }

  function load() {
    var version = ++requestVersion;
    mediaRequestVersion += 1;
    refresh.disabled = true;
    filter.disabled = true;
    rows = [];
    body.replaceChildren();
    status.textContent = "Loading works…";
    return service.readSeriesWorks({ target: target }).then(function (payload) {
      if (!current(version)) return;
      rows = readSeriesWorksRows(payload, target);
      seriesLabel = "Series " + payload.series_id + " — " + payload.title;
      table.setAttribute("aria-label", seriesLabel);
      renderRows();
      filter.disabled = false;
    }).catch(function (error) {
      if (current(version)) status.textContent = error.message;
    }).finally(function () {
      if (current(version)) refresh.disabled = false;
    });
  }

  filter.addEventListener("input", renderRows);
  refresh.addEventListener("click", load);
  return load().then(function () { return true; });
}
