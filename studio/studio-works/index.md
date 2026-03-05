---
layout: default
title: Studio Works
permalink: /studio/studio-works/
section: works
---
<div class="index worksList worksList--curator" id="worksCuratorRoot" hidden>
  <h1 class="index__heading visually-hidden">works curator</h1>
  <div class="worksList__metaRow">
    <p class="worksList__count" id="worksListCount"></p>
    <a class="worksList__metaLink" href="{{ '/site_map/' | relative_url }}">site map</a>
  </div>

  <div class="worksList__head" role="group" aria-label="Sort works curator">
    <button class="worksList__sortBtn" type="button" data-sort-key="cat">
      cat <span class="worksList__sortIcon" aria-hidden="true"></span>
    </button>
    <button class="worksList__sortBtn" type="button" data-sort-key="year">
      year <span class="worksList__sortIcon" aria-hidden="true"></span>
    </button>
    <button class="worksList__sortBtn" type="button" data-sort-key="title">
      title <span class="worksList__sortIcon" aria-hidden="true"></span>
    </button>
    <button class="worksList__sortBtn" type="button" data-sort-key="series">
      series <span class="worksList__sortIcon" aria-hidden="true"></span>
    </button>
    <button class="worksList__sortBtn" type="button" data-sort-key="storage">
      storage <span class="worksList__sortIcon" aria-hidden="true"></span>
    </button>
  </div>

  <ul class="worksList__list" id="worksList"></ul>

  <nav class="page__nav" id="worksIndexBackNav" hidden>
    <a
      class="page__back"
      id="worksIndexBackLink"
      href="{{ '/series/' | relative_url }}"
    >← series</a>
  </nav>
</div>
<p id="worksCuratorEmpty" hidden>no curator works yet</p>

<script>
  (function () {
    var worksListRoot = document.getElementById('worksCuratorRoot');
    var emptyEl = document.getElementById('worksCuratorEmpty');
    var list = document.getElementById('worksList');
    var countEl = document.getElementById('worksListCount');
    var backNav = document.getElementById('worksIndexBackNav');
    var backLink = document.getElementById('worksIndexBackLink');
    var buttons = Array.prototype.slice.call(document.querySelectorAll('.worksList__sortBtn'));
    if (!worksListRoot || !emptyEl || !list || !countEl || !buttons.length) return;

    var baseurl = {{ site.baseurl | default: '' | jsonify }};
    var worksIndexUrl = baseurl + '/assets/data/works_index.json';
    var seriesIndexUrl = baseurl + '/assets/data/series_index.json';
    var validKeys = { cat: true, year: true, title: true, series: true, storage: true, seriessort: true };
    var collator = new Intl.Collator(undefined, { numeric: true, sensitivity: 'base' });
    var params = new URLSearchParams(window.location.search);
    var sortParam = params.get('sort');
    var hasExplicitSort = !(sortParam == null || String(sortParam).trim() === '');
    var sortKey = String(sortParam || '').toLowerCase();
    var sortDir = String(params.get('dir') || 'asc').toLowerCase();
    var seriesFilter = String(params.get('series') || '').trim().toLowerCase();
    var hasSeriesFilter = seriesFilter.length > 0;
    var seriesBaseHref = baseurl + '/series/';
    var visualSortKey = sortKey;
    var totalWorksAll = 0;
    var totalSeriesAll = 0;

    if (!hasExplicitSort) sortKey = hasSeriesFilter ? 'seriessort' : 'cat';
    if (!validKeys[sortKey]) sortKey = hasSeriesFilter ? 'seriessort' : 'cat';
    if (!validKeys[sortKey]) sortKey = 'cat';
    if (sortDir !== 'asc' && sortDir !== 'desc') sortDir = 'asc';
    if (hasSeriesFilter) {
      worksListRoot.classList.add('worksList--singleSeries');
    }

    function fetchJson(url) {
      return fetch(url, { cache: 'default' })
        .then(function (r) {
          if (!r.ok) throw new Error('HTTP ' + r.status);
          return r.json();
        });
    }

    function normalizeText(v) {
      return String(v == null ? '' : v).trim();
    }

    function slugSortKey(v) {
      return normalizeText(v).toLowerCase();
    }

    function numericAwareSortKey(v) {
      return normalizeText(v).replace(/\d+/g, function (m) {
        return m.padStart(3, '0');
      });
    }

    function seriesPrimarySortFromSortFields(sortFieldsRaw) {
      var token = normalizeText(sortFieldsRaw).split(',')[0] || '';
      token = slugSortKey(token);
      if (token.charAt(0) === '-') token = token.slice(1);
      if (token === 'work_id') return 'cat';
      if (token === 'year') return 'year';
      if (token === 'title' || token === 'title_sort') return 'title';
      if (token === 'series' || token === 'series_title') return 'series';
      if (token === 'storage' || token === 'storage_location') return 'storage';
      return '';
    }

    function isCustomSeriesSort(sortFieldsRaw) {
      var raw = normalizeText(sortFieldsRaw);
      if (!raw) return false;
      var parts = raw.split(',');
      var nonWork = 0;
      for (var i = 0; i < parts.length; i += 1) {
        var t = slugSortKey(parts[i]);
        if (t.charAt(0) === '-') t = t.slice(1);
        if (!t || t === 'work_id') continue;
        nonWork += 1;
      }
      return nonWork > 0;
    }

    function buildSeriesMeta(seriesMap) {
      var out = {};
      if (!seriesMap || typeof seriesMap !== 'object') return out;
      Object.keys(seriesMap).forEach(function (sidRaw) {
        var sid = slugSortKey(sidRaw);
        if (!sid) return;
        var row = seriesMap[sidRaw];
        if (!row || typeof row !== 'object') return;
        var works = Array.isArray(row.works) ? row.works.map(normalizeText).filter(Boolean) : [];
        var rankMap = {};
        var rankWidth = Math.max(3, String(works.length).length);
        for (var i = 0; i < works.length; i += 1) {
          var wid = works[i];
          var rank = String(i + 1).padStart(rankWidth, '0');
          rankMap[wid] = rank + '-' + wid;
        }
        out[sid] = {
          label: normalizeText(row.title) || sid,
          sort_fields: normalizeText(row.sort_fields),
          primary_sort: seriesPrimarySortFromSortFields(row.sort_fields),
          custom_sort: isCustomSeriesSort(row.sort_fields),
          rank_map: rankMap
        };
      });
      return out;
    }

    function rowMatchesSeries(row) {
      if (!hasSeriesFilter) return true;
      var rowSeriesId = slugSortKey(row.getAttribute('data-series-id'));
      return rowSeriesId === seriesFilter;
    }

    function updateCount(visibleRows) {
      if (hasSeriesFilter) {
        var workCount = visibleRows.length;
        var workWord = workCount === 1 ? 'work' : 'works';
        var seriesLabel = '';
        if (visibleRows.length) {
          seriesLabel = normalizeText(visibleRows[0].getAttribute('data-series-label'));
        }
        countEl.textContent = '';
        countEl.appendChild(document.createTextNode(String(workCount) + ' ' + workWord));
        if (seriesLabel) {
          countEl.appendChild(document.createTextNode(' in '));
          var seriesLink = document.createElement('a');
          seriesLink.className = 'worksList__countSeriesLink';
          seriesLink.href = seriesBaseHref + encodeURIComponent(seriesFilter) + '/';
          seriesLink.textContent = seriesLabel;
          countEl.appendChild(seriesLink);
        }
        if (backNav && backLink) {
          backNav.hidden = false;
          backLink.setAttribute('href', seriesBaseHref + encodeURIComponent(seriesFilter) + '/');
          backLink.textContent = seriesLabel ? ('← ' + seriesLabel) : '← series';
        }
        return;
      }

      var workWordAll = totalWorksAll === 1 ? 'work' : 'works';
      countEl.textContent = String(totalWorksAll) + ' ' + workWordAll + ' in ' + String(totalSeriesAll) + ' series';
      if (backNav) backNav.hidden = true;
    }

    function compareValues(a, b, key) {
      if (key === 'year') {
        var av = Number(a.getAttribute('data-year') || '0');
        var bv = Number(b.getAttribute('data-year') || '0');
        return av - bv;
      }
      if (key === 'seriessort') {
        var aSeriesSort = normalizeText(a.getAttribute('data-series-sort'));
        var bSeriesSort = normalizeText(b.getAttribute('data-series-sort'));
        return collator.compare(aSeriesSort, bSeriesSort);
      }
      var as = normalizeText(a.getAttribute('data-' + key));
      var bs = normalizeText(b.getAttribute('data-' + key));
      return collator.compare(as, bs);
    }

    function updateRowLinks(key, dir) {
      var rows = Array.prototype.slice.call(list.querySelectorAll('.worksList__item'));
      rows.forEach(function (row) {
        var titleLink = row.querySelector('.worksList__title');
        if (!titleLink) return;
        var href = String(titleLink.getAttribute('href') || '');
        var hashIndex = href.indexOf('#');
        var hash = '';
        if (hashIndex >= 0) {
          hash = href.slice(hashIndex);
          href = href.slice(0, hashIndex);
        }
        var qIndex = href.indexOf('?');
        var base = qIndex >= 0 ? href.slice(0, qIndex) : href;
        var query = new URLSearchParams(qIndex >= 0 ? href.slice(qIndex + 1) : '');
        query.set('from', 'works_curator_index');
        query.set('return_sort', key);
        query.set('return_dir', dir);
        if (hasSeriesFilter) {
          query.set('return_series', seriesFilter);
        } else {
          query.delete('return_series');
        }
        titleLink.setAttribute('href', base + '?' + query.toString() + hash);
      });
    }

    function applySort(key, dir) {
      var rows = Array.prototype.slice.call(list.querySelectorAll('.worksList__item'));
      var visibleRows = rows.filter(rowMatchesSeries);
      if (hasSeriesFilter) list.innerHTML = '';
      visibleRows.sort(function (a, b) {
        var primary = compareValues(a, b, key);
        if (primary !== 0) return dir === 'asc' ? primary : -primary;

        var tieTitle = compareValues(a, b, 'title');
        if (tieTitle !== 0) return tieTitle;
        var tieCat = compareValues(a, b, 'cat');
        if (tieCat !== 0) return tieCat;
        var tieSeries = compareValues(a, b, 'series');
        if (tieSeries !== 0) return tieSeries;
        return compareValues(a, b, 'storage');
      });
      visibleRows.forEach(function (row) { list.appendChild(row); });
      updateCount(visibleRows);
      updateRowLinks(key, dir);
    }

    function updateHeaderState(key, dir) {
      buttons.forEach(function (btn) {
        var btnKey = btn.getAttribute('data-sort-key');
        var icon = btn.querySelector('.worksList__sortIcon');
        var active = (btnKey === key);
        btn.classList.toggle('is-active', active);
        if (!icon) return;
        icon.textContent = active ? (dir === 'asc' ? '▲' : '▼') : '';
      });
    }

    function visualSortKeyFor(rows, key) {
      if (key !== 'seriessort') return key;
      if (!hasSeriesFilter) return 'cat';

      var sameAsCat = rows.length > 0 && rows.every(function (row) {
        var a = normalizeText(row.getAttribute('data-series-sort'));
        var b = normalizeText(row.getAttribute('data-cat'));
        return a === b;
      });
      if (sameAsCat) return 'cat';

      for (var i = 0; i < rows.length; i += 1) {
        var hint = slugSortKey(rows[i].getAttribute('data-series-primary-sort'));
        if (validKeys[hint] && hint !== 'seriessort') return hint;
      }
      return 'cat';
    }

    function persist(key, dir) {
      var next = new URLSearchParams(window.location.search);
      next.set('sort', key);
      next.set('dir', dir);
      var query = next.toString();
      var path = String(window.location.pathname || '/');
      path = '/' + path.replace(/^\/+/, '').replace(/\/{2,}/g, '/');
      var nextUrl = path + (query ? ('?' + query) : '') + window.location.hash;
      window.history.replaceState({}, '', nextUrl);
    }

    function makeWorkRow(work, seriesMetaById) {
      var wid = normalizeText(work && work.work_id);
      if (!wid) return null;
      var sid = slugSortKey(work && work.series_id);
      var sm = sid ? (seriesMetaById[sid] || null) : null;
      var seriesLabel = (sm && sm.label) ? sm.label : (sid || '');
      var seriesPrimarySort = (sm && sm.primary_sort) ? sm.primary_sort : '';
      var yearVal = Number(work && work.year);
      if (!Number.isFinite(yearVal)) yearVal = 0;
      var yearDisplay = normalizeText(work && work.year_display) || normalizeText(work && work.year);
      var titleRaw = normalizeText(work && work.title) || wid;
      var titleSortRaw = normalizeText(work && work.title_sort);
      var titleSort = (titleSortRaw || numericAwareSortKey(titleRaw)).toLowerCase();
      var storageRaw = normalizeText(work && work.storage);
      if (!storageRaw) storageRaw = normalizeText(work && work.storage_location);
      var seriesSort = wid;
      if (sm && sm.custom_sort && sm.rank_map && sm.rank_map[wid]) {
        seriesSort = sm.rank_map[wid];
      }

      var li = document.createElement('li');
      li.className = 'worksList__item';
      li.setAttribute('data-cat', wid.toLowerCase());
      li.setAttribute('data-series-sort', seriesSort.toLowerCase());
      li.setAttribute('data-series-primary-sort', seriesPrimarySort.toLowerCase());
      li.setAttribute('data-year', String(yearVal));
      li.setAttribute('data-title', titleSort);
      li.setAttribute('data-series', seriesLabel.toLowerCase());
      li.setAttribute('data-storage', storageRaw.toLowerCase());
      li.setAttribute('data-series-id', sid);
      li.setAttribute('data-series-label', seriesLabel);

      var workHref = baseurl + '/works/' + encodeURIComponent(wid) + '/?from=works_curator_index';

      var catA = document.createElement('a');
      catA.className = 'worksList__cat';
      catA.href = workHref;
      catA.textContent = wid;
      li.appendChild(catA);

      var yearSpan = document.createElement('span');
      yearSpan.className = 'worksList__year';
      yearSpan.textContent = yearDisplay;
      li.appendChild(yearSpan);

      var titleA = document.createElement('a');
      titleA.className = 'worksList__title';
      titleA.href = workHref;
      titleA.textContent = titleRaw;
      li.appendChild(titleA);

      var seriesA = document.createElement('a');
      seriesA.className = 'worksList__series';
      seriesA.href = sid ? (seriesBaseHref + encodeURIComponent(sid) + '/') : seriesBaseHref;
      seriesA.textContent = seriesLabel;
      li.appendChild(seriesA);

      var storageSpan = document.createElement('span');
      storageSpan.className = 'worksList__storage';
      storageSpan.textContent = storageRaw || '—';
      li.appendChild(storageSpan);

      return li;
    }

    function renderFromJson(worksPayload, seriesPayload) {
      var worksMap = (worksPayload && worksPayload.works && typeof worksPayload.works === 'object') ? worksPayload.works : {};
      var seriesMap = (seriesPayload && seriesPayload.series && typeof seriesPayload.series === 'object') ? seriesPayload.series : {};
      var seriesMetaById = buildSeriesMeta(seriesMap);
      var rows = [];
      var seriesIdSet = {};

      Object.keys(worksMap).forEach(function (wid) {
        var row = makeWorkRow(worksMap[wid], seriesMetaById);
        if (!row) return;
        rows.push(row);
        var sid = slugSortKey(row.getAttribute('data-series-id'));
        if (sid) seriesIdSet[sid] = true;
      });

      totalWorksAll = rows.length;
      totalSeriesAll = Object.keys(seriesIdSet).length;
      list.innerHTML = '';
      if (!rows.length) return false;

      var frag = document.createDocumentFragment();
      rows.forEach(function (row) { frag.appendChild(row); });
      list.appendChild(frag);
      return true;
    }

    function initSortUi() {
      buttons.forEach(function (btn) {
        btn.addEventListener('click', function () {
          var key = slugSortKey(btn.getAttribute('data-sort-key'));
          if (!validKeys[key]) return;
          if (key === visualSortKey) {
            sortDir = (sortDir === 'asc') ? 'desc' : 'asc';
          } else {
            sortKey = key;
            sortDir = 'asc';
          }
          sortKey = key;
          applySort(sortKey, sortDir);
          var rows = Array.prototype.slice.call(list.querySelectorAll('.worksList__item')).filter(rowMatchesSeries);
          visualSortKey = visualSortKeyFor(rows, sortKey);
          updateHeaderState(visualSortKey, sortDir);
          persist(sortKey, sortDir);
        });
      });

      applySort(sortKey, sortDir);
      var initialRows = Array.prototype.slice.call(list.querySelectorAll('.worksList__item')).filter(rowMatchesSeries);
      visualSortKey = visualSortKeyFor(initialRows, sortKey);
      updateHeaderState(visualSortKey, sortDir);
      persist(sortKey, sortDir);
    }

    Promise.all([
      fetchJson(worksIndexUrl),
      fetchJson(seriesIndexUrl).catch(function () { return null; })
    ])
      .then(function (parts) {
        var hasRows = renderFromJson(parts[0], parts[1]);
        if (!hasRows) {
          worksListRoot.hidden = true;
          emptyEl.hidden = false;
          return;
        }
        worksListRoot.hidden = false;
        emptyEl.hidden = true;
        try {
          initSortUi();
        } catch (err) {
          console.error('works_curator: initSortUi failed', err);
        }
      })
      .catch(function (err) {
        console.error('works_curator: render failed', err);
        worksListRoot.hidden = true;
        emptyEl.hidden = false;
      });
  })();
</script>
