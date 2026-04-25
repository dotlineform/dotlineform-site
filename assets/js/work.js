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
  var fromContext = (params.get('from') || '').trim().toLowerCase();

  var prevA = document.getElementById('seriesNavPrev');
  var nextA = document.getElementById('seriesNavNext');
  var counterEl = document.getElementById('seriesNavCounter');
  var seriesLink = document.getElementById('workSeriesLink');
  var backLink = document.getElementById('pageBackLink');
  var seriesIndexData = null;

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

  function extractSeriesRow(payload, seriesId) {
    if (!payload || !payload.series || typeof payload.series !== 'object') return null;
    var row = payload.series[seriesId];
    return row && typeof row === 'object' ? row : null;
  }

  function extractSeriesTitle(payload, seriesId) {
    var row = extractSeriesRow(payload, seriesId);
    if (!row) return '';
    return String(row.title || '').trim();
  }

  function setSeriesLinkVisibilityFromIds(ids) {
    if (!seriesLinkWrap) return;
    seriesLinkWrap.hidden = ids.length <= 1;
  }

  function setSeriesLinkTarget(seriesId) {
    if (!seriesLink) return;
    var sid = String(seriesId || '').trim();
    if (!sid) {
      seriesLink.textContent = '';
      seriesLink.setAttribute('href', baseurl + '/series/');
      return;
    }
    var label = extractSeriesTitle(seriesIndexData, sid) || sid;
    seriesLink.textContent = label;
    seriesLink.setAttribute('href', baseurl + '/series/' + encodeURIComponent(sid) + '/');
  }

  function setBackLinkLabel(seriesId) {
    if (!backLink) return;
    var sid = String(seriesId || '').trim();
    if (!sid) return;
    var label = extractSeriesTitle(seriesIndexData, sid);
    if (!label) return;
    backLink.setAttribute('data-series-label', label);
    if (seriesFromQuery && seriesFromQuery === sid) {
      backLink.textContent = '← ' + label;
    } else if (!seriesFromQuery && !fromContext) {
      backLink.textContent = '← ' + label;
      backLink.setAttribute('href', baseurl + '/series/' + encodeURIComponent(sid) + '/');
    }
  }

  function configureNav(ids, currentId) {
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

  function refreshFromCurrentMeta() {
    if (!seriesIndexData) return;
    var pageSeriesId = (nav && nav.dataset) ? String(nav.dataset.series || '').trim() : '';
    var currentId = (nav && nav.dataset) ? String(nav.dataset.workId || '').trim() : '';
    if (pageSeriesId) {
      setSeriesLinkTarget(pageSeriesId);
      setSeriesLinkVisibilityFromIds(extractSeriesIndexIds(seriesIndexData, pageSeriesId));
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

  var seriesIndexUrl = baseurl + '/assets/data/series_index.json';
  fetchJson(seriesIndexUrl)
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
