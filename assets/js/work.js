(function () {
  // Parameters are passed from Jekyll via data-* attributes on #seriesNav:
  // data-series and data-baseurl. Querystring ?series=... overrides data-series.
  var nav = document.getElementById('seriesNav'); // series nav container (also holds data-* config)
  var link = document.querySelector('.page__back'); // back/index link element

  var baseurl = ''; // site baseurl, used to build absolute-ish paths
  if (nav && nav.dataset && nav.dataset.baseurl) {
    baseurl = String(nav.dataset.baseurl); // raw baseurl from data-baseurl
  }
  baseurl = baseurl.replace(/\/$/, ''); // normalize: no trailing slash

  var worksIndex = '/works/'; // default index path fallback
  if (link) {
    worksIndex = link.getAttribute('data-fallback') || link.getAttribute('href') || worksIndex; // prefer layout-provided fallback
  }

  var params = new URLSearchParams(window.location.search); // parsed query string
  var seriesParam = params.get('series'); // explicit ?series=... from URL
  var seriesFallback = nav && nav.dataset ? (nav.dataset.series || '') : ''; // layout-provided series id
  var series = (seriesParam || seriesFallback || '').trim(); // final series id (URL wins)

  if (link) {
    if (series) {
      var seriesHref = baseurl + '/series/' + encodeURIComponent(series) + '/';
      link.textContent = '← series';
      link.setAttribute('href', seriesHref);
    } else {
      var ref = document.referrer || '';
      var sameOriginReferrer = ref && ref.indexOf(window.location.origin) === 0;
      var hasHistory = window.history.length > 1;

      if (sameOriginReferrer || hasHistory) {
        link.textContent = '← back';
        link.addEventListener('click', function (e) {
          e.preventDefault();
          window.history.back();
        });
        link.setAttribute('href', worksIndex);
      } else {
        link.textContent = '← index';
        link.setAttribute('href', worksIndex);
      }
    }
  }

  if (!nav || !series) {
    if (nav) nav.hidden = true;
    return;
  }

  var prevA = document.getElementById('seriesNavPrev');
  var nextA = document.getElementById('seriesNavNext');
  if (!prevA || !nextA) return;

  var currentId = (nav.dataset.workId || '').trim();
  if (!currentId) return;

  var jsonUrl = baseurl + '/assets/series/index/' + encodeURIComponent(series) + '.json';

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

      var qs = '?series=' + encodeURIComponent(series);
      prevA.href = baseurl + '/works/' + prevId + '/' + qs;
      nextA.href = baseurl + '/works/' + nextId + '/' + qs;

      nav.hidden = false;
    })
    .catch(function () {
      nav.hidden = true;
    });
})();
