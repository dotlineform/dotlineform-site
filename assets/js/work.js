(function () {
  // Parameters are passed from Jekyll via data-* attributes on #seriesNav:
  // data-series and data-baseurl. Querystring ?series=... overrides data-series.
  var nav = document.getElementById('seriesNav'); // series nav container (also holds data-* config)

  var baseurl = ''; // site baseurl, used to build absolute-ish paths
  if (nav && nav.dataset && nav.dataset.baseurl) {
    baseurl = String(nav.dataset.baseurl); // raw baseurl from data-baseurl
  }
  baseurl = baseurl.replace(/\/$/, ''); // normalize: no trailing slash

  var params = new URLSearchParams(window.location.search); // parsed query string
  var seriesFromQuery = (params.get('series') || '').trim(); // series context only when explicitly present

  if (!nav || !seriesFromQuery) {
    if (nav) nav.hidden = true;
    return;
  }

  var prevA = document.getElementById('seriesNavPrev');
  var nextA = document.getElementById('seriesNavNext');
  if (!prevA || !nextA) return;

  var currentId = (nav.dataset.workId || '').trim();
  if (!currentId) return;

  var jsonUrl = baseurl + '/assets/series/index/' + encodeURIComponent(seriesFromQuery) + '.json';

  fetch(jsonUrl, { cache: 'default' })
    .then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    })
    .then(function (data) {
      var ids = [];
      if (Array.isArray(data)) ids = data;
      else if (data && Array.isArray(data.work_ids)) ids = data.work_ids;
      else if (data && Array.isArray(data.items)) ids = data.items;
      ids = ids.map(String);

      var i = ids.indexOf(currentId);
      if (i === -1 || ids.length < 2) return;

      var prevId = ids[(i - 1 + ids.length) % ids.length];
      var nextId = ids[(i + 1) % ids.length];

      var qs = '?series=' + encodeURIComponent(seriesFromQuery);
      prevA.href = baseurl + '/works/' + prevId + '/' + qs;
      nextA.href = baseurl + '/works/' + nextId + '/' + qs;

      nav.hidden = false;
    })
    .catch(function () {
      nav.hidden = true;
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
