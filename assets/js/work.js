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
