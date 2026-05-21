(function () {
  // Parameters are passed from Jekyll via data-* attributes on #seriesNav.
  // ?series=... controls navigation context; page-level series metadata comes from data-series.
  var nav = document.getElementById('seriesNav');
  var seriesLinkWrap = document.getElementById('workSeriesLinkWrap');
  if (!nav && !seriesLinkWrap) return;
  var runtime = window.__dlfPublicCatalogueRuntime;
  if (!runtime) return;

  var baseurl = '';
  if (nav && nav.dataset && nav.dataset.baseurl) {
    baseurl = String(nav.dataset.baseurl);
  }
  baseurl = runtime.trimBaseurl(baseurl);

  var params = new URLSearchParams(window.location.search);
  var seriesFromQuery = (params.get('series') || '').trim();
  var seriesPageRaw = Number(params.get('series_page') || '0');
  var seriesPage = (Number.isFinite(seriesPageRaw) && seriesPageRaw > 0) ? Math.floor(seriesPageRaw) : 0;
  var fromContext = (params.get('from') || '').trim().toLowerCase();

  var prevA = document.getElementById('seriesNavPrev');
  var nextA = document.getElementById('seriesNavNext');
  var counterEl = document.getElementById('seriesNavCounter');
  var seriesLink = document.getElementById('workSeriesLink');
  var backLink = document.getElementById('pageBackLink');
  var seriesIndexData = null;

  function extractSeriesIndexIds(payload, seriesId) {
    return runtime.seriesIndexWorkIds(payload, seriesId);
  }

  function setSeriesLinkTarget(seriesId) {
    var projection = runtime.projectWorkSeriesLink(seriesIndexData, seriesId, baseurl);
    if (seriesLinkWrap) seriesLinkWrap.hidden = projection.hidden;
    if (!seriesLink) return;
    seriesLink.textContent = projection.label;
    seriesLink.setAttribute('href', projection.href);
  }

  function setBackLinkLabel(seriesId) {
    if (!backLink) return;
    var projection = runtime.projectWorkBackLink(seriesIndexData, {
      seriesId: seriesId,
      seriesFromQuery: seriesFromQuery,
      fromContext: fromContext,
      baseurl: baseurl
    });
    if (!projection) return;
    backLink.setAttribute('data-series-label', projection.seriesLabel);
    if (projection.label) backLink.textContent = projection.label;
    if (projection.href) {
      backLink.setAttribute('href', projection.href);
    }
  }

  function configureNav(ids, currentId) {
    if (!nav || !prevA || !nextA || !seriesFromQuery || !currentId) return;
    var projection = runtime.projectWorkSeriesNavigation(ids, currentId, {
      seriesId: seriesFromQuery,
      seriesPage: seriesPage,
      baseurl: baseurl
    });
    nav.hidden = projection.hidden;
    if (counterEl) {
      counterEl.textContent = projection.counterText || '';
      counterEl.hidden = projection.counterHidden;
    }
    if (projection.hidden) return;
    prevA.href = projection.prevHref;
    nextA.href = projection.nextHref;
  }

  function refreshFromCurrentMeta() {
    if (!seriesIndexData) return;
    var pageSeriesId = (nav && nav.dataset) ? String(nav.dataset.series || '').trim() : '';
    var currentId = (nav && nav.dataset) ? String(nav.dataset.workId || '').trim() : '';
    if (pageSeriesId) {
      setSeriesLinkTarget(pageSeriesId);
      setBackLinkLabel(pageSeriesId);
    } else if (seriesLinkWrap) {
      seriesLinkWrap.hidden = true;
      setSeriesLinkTarget('');
    }
    if (!seriesFromQuery) {
      if (nav) nav.hidden = true;
      return;
    }
    setBackLinkLabel(seriesFromQuery);
    var idsForNav = extractSeriesIndexIds(seriesIndexData, seriesFromQuery);
    configureNav(idsForNav, currentId);
  }

  var seriesIndexUrl = runtime.seriesIndexUrl(baseurl);
  runtime.fetchJson(seriesIndexUrl)
    .then(function (data) {
      seriesIndexData = data;
      // Local cache for fast refresh when work metadata is re-hydrated from JSON.
      refreshFromCurrentMeta();
    })
    .catch(function () {
      if (seriesLinkWrap) seriesLinkWrap.hidden = true;
      if (nav) nav.hidden = true;
    });

  document.addEventListener('dlf:work-metadata-applied', function () {
    refreshFromCurrentMeta();
  });
})();

(function () {
  // Keyboard navigation bootstrap for work + work detail pages.
  // How it is called:
  // - This file is loaded by the page layout via:
  //   <script src="/assets/js/work.js"></script>
  // - On load, this IIFE attaches one keydown listener to `document`.
  // - The listener checks for the visible Prev/Next nav links and routes
  //   ArrowLeft/ArrowRight to those URLs.

  function isTypingTarget(el) {
    if (!el) return false;
    var tag = (el.tagName || '').toLowerCase();
    return tag === 'input' || tag === 'textarea' || tag === 'select' || el.isContentEditable;
  }

  function firstUsableLink(ids) {
    for (var i = 0; i < ids.length; i += 1) {
      var a = document.getElementById(ids[i]);
      if (!a) continue;
      if (a.hidden) continue;
      var href = String(a.getAttribute('href') || '').trim();
      if (!href || href === '#') continue;
      return a;
    }
    return null;
  }

  document.addEventListener('keydown', function (e) {
    if (e.defaultPrevented) return;
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    if (isTypingTarget(document.activeElement)) return;

    // Prefer detail nav when present; otherwise fall back to series/work nav.
    var prev = firstUsableLink(['detailNavPrev', 'seriesNavPrev']);
    var next = firstUsableLink(['detailNavNext', 'seriesNavNext']);

    if (e.key === 'ArrowLeft' && prev) {
      e.preventDefault();
      window.location.href = prev.href;
      return;
    }
    if (e.key === 'ArrowRight' && next) {
      e.preventDefault();
      window.location.href = next.href;
    }
  });
})();
