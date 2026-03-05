(function () {
  // Parameters are passed from Jekyll via data-* attributes on #seriesNav.
  // ?series=... controls navigation context; page-level series metadata comes from data-series.
  var nav = document.getElementById('seriesNav');
  var seriesLinkWrap = document.getElementById('workSeriesLinkWrap');
  if (!nav && !seriesLinkWrap) return;

  var baseurl = '';
  if (nav && nav.dataset && nav.dataset.baseurl) {
    baseurl = String(nav.dataset.baseurl);
  }
  baseurl = baseurl.replace(/\/$/, '');

  var params = new URLSearchParams(window.location.search);
  var seriesFromQuery = (params.get('series') || '').trim();
  var seriesPageRaw = Number(params.get('series_page') || '0');
  var seriesPage = (Number.isFinite(seriesPageRaw) && seriesPageRaw > 0) ? Math.floor(seriesPageRaw) : 0;

  var prevA = document.getElementById('seriesNavPrev');
  var nextA = document.getElementById('seriesNavNext');
  var counterEl = document.getElementById('seriesNavCounter');
  var pageSeriesId = (nav && nav.dataset) ? String(nav.dataset.series || '').trim() : '';
  var currentId = (nav && nav.dataset) ? String(nav.dataset.workId || '').trim() : '';

  function fetchJson(url) {
    return fetch(url, { cache: 'default' })
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      });
  }

  function normalizeIds(raw) {
    if (!Array.isArray(raw)) return [];
    return raw.map(function (id) { return String(id || '').trim(); }).filter(Boolean);
  }

  function extractSeriesIndexIds(payload, seriesId) {
    if (!payload || !payload.series || typeof payload.series !== 'object') return [];
    var row = payload.series[seriesId];
    if (!row || !Array.isArray(row.works)) return [];
    return normalizeIds(row.works);
  }

  function setSeriesLinkVisibilityFromIds(ids) {
    if (!seriesLinkWrap) return;
    seriesLinkWrap.hidden = ids.length <= 1;
  }

  function configureNav(ids) {
    if (!nav || !prevA || !nextA || !seriesFromQuery || !currentId) return;
    var i = ids.indexOf(currentId);
    if (i === -1 || ids.length < 2) {
      nav.hidden = true;
      if (counterEl) counterEl.hidden = true;
      return;
    }

    var prevId = ids[(i - 1 + ids.length) % ids.length];
    var nextId = ids[(i + 1) % ids.length];

    var qs = '?series=' + encodeURIComponent(seriesFromQuery);
    if (seriesPage > 0) qs += '&series_page=' + encodeURIComponent(String(seriesPage));
    prevA.href = baseurl + '/works/' + prevId + '/' + qs;
    nextA.href = baseurl + '/works/' + nextId + '/' + qs;

    if (counterEl) {
      counterEl.textContent = String(i + 1) + '/' + String(ids.length);
      counterEl.hidden = false;
    }
    nav.hidden = false;
  }

  var seriesIndexUrl = baseurl + '/assets/data/series_index.json';
  fetchJson(seriesIndexUrl)
    .then(function (seriesIndexData) {
      if (pageSeriesId) {
        setSeriesLinkVisibilityFromIds(extractSeriesIndexIds(seriesIndexData, pageSeriesId));
      }
      if (!seriesFromQuery) {
        if (nav) nav.hidden = true;
        return;
      }
      var idsForNav = extractSeriesIndexIds(seriesIndexData, seriesFromQuery);
      configureNav(idsForNav);
    })
    .catch(function () {
      if (seriesLinkWrap) seriesLinkWrap.hidden = true;
      if (nav) nav.hidden = true;
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
