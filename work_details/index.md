---
layout: default
title: Work Details
permalink: /work_details/
section: works
---

<div class="index worksList detailsList" id="workDetailsIndexRoot" hidden>
  <h1 class="index__heading visually-hidden">work details</h1>
  <p class="worksList__count" id="workDetailsListContext" hidden></p>

  <div class="worksList__head" role="group" aria-label="Sort work details">
    <button class="worksList__sortBtn" type="button" data-sort-key="cat">
      cat <span class="worksList__sortIcon" aria-hidden="true"></span>
    </button>
    <button class="worksList__sortBtn" type="button" data-sort-key="title">
      title <span class="worksList__sortIcon" aria-hidden="true"></span>
    </button>
  </div>

  <ul class="worksList__list" id="workDetailsList"></ul>

  <nav class="page__nav" id="workDetailsIndexBackNav" hidden>
    <a
      class="page__back"
      id="workDetailsIndexBackLink"
      href="{{ '/works/' | relative_url }}"
    >← work</a>
  </nav>
</div>
<p id="workDetailsEmpty" hidden>no work details yet</p>

<script>
  (function () {
    var root = document.getElementById('workDetailsIndexRoot');
    var emptyEl = document.getElementById('workDetailsEmpty');
    var list = document.getElementById('workDetailsList');
    var buttons = Array.prototype.slice.call(document.querySelectorAll('.worksList__sortBtn'));
    if (!root || !emptyEl || !list || !buttons.length) return;

    var validKeys = { cat: true, title: true };
    var collator = new Intl.Collator(undefined, { numeric: true, sensitivity: 'base' });
    var params = new URLSearchParams(window.location.search);
    var sortKey = String(params.get('sort') || 'cat').toLowerCase();
    var sortDir = String(params.get('dir') || 'asc').toLowerCase();
    var fromWork = String(params.get('from_work') || '').trim().toLowerCase();
    var fromWorkTitle = String(params.get('from_work_title') || '').trim();
    var sectionFilter = String(params.get('section') || '').trim().toLowerCase();
    var sectionLabelParam = String(params.get('section_label') || '').trim();
    var seriesParam = String(params.get('series') || '').trim().toLowerCase();
    var seriesPageRaw = Number(params.get('series_page') || '0');
    var seriesPage = (Number.isFinite(seriesPageRaw) && seriesPageRaw > 0) ? Math.floor(seriesPageRaw) : 0;
    var contextEl = document.getElementById('workDetailsListContext');
    var backNav = document.getElementById('workDetailsIndexBackNav');
    var backLink = document.getElementById('workDetailsIndexBackLink');
    var hasWorkFilter = fromWork.length > 0;
    var hasSectionFilter = sectionFilter.length > 0;
    var baseurl = {{ site.baseurl | default: '' | jsonify }};
    var detailsIndexUrl = baseurl + '/assets/data/work_details_index.json';
    if (!validKeys[sortKey]) sortKey = 'cat';
    if (sortDir !== 'asc' && sortDir !== 'desc') sortDir = 'asc';

    function normalize(v) {
      return String(v == null ? '' : v).trim();
    }

    function slug(v) {
      return normalize(v)
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-+|-+$/g, '');
    }

    function rowMatchesFilter(row) {
      if (hasWorkFilter) {
        var rowWorkId = String(row.getAttribute('data-work-id') || '').trim().toLowerCase();
        if (rowWorkId !== fromWork) return false;
      }
      if (hasSectionFilter) {
        var rowSectionId = String(row.getAttribute('data-section-id') || '').trim().toLowerCase();
        if (rowSectionId !== sectionFilter) return false;
      }
      return true;
    }

    function compareValues(a, b, key) {
      var as = String(a.getAttribute('data-' + key) || '');
      var bs = String(b.getAttribute('data-' + key) || '');
      return collator.compare(as, bs);
    }

    function applySort(key, dir) {
      var rows = Array.prototype.slice.call(list.querySelectorAll('.worksList__item'));
      var visibleRows = rows.filter(rowMatchesFilter);
      if (hasWorkFilter || hasSectionFilter) list.innerHTML = '';
      visibleRows.sort(function (a, b) {
        var primary = compareValues(a, b, key);
        if (primary !== 0) return dir === 'asc' ? primary : -primary;

        var tieTitle = compareValues(a, b, 'title');
        if (tieTitle !== 0) return tieTitle;
        return compareValues(a, b, 'cat');
      });
      visibleRows.forEach(function (row) { list.appendChild(row); });
      updateContextAndBack(visibleRows);
      updateRowLinks();
    }

    function updateContextAndBack(visibleRows) {
      var sectionLabel = sectionLabelParam;
      if (!sectionLabel && visibleRows.length) {
        sectionLabel = String(visibleRows[0].getAttribute('data-section-label') || '').trim();
      }
      var sectionId = sectionFilter;
      if (!sectionId && visibleRows.length) {
        sectionId = String(visibleRows[0].getAttribute('data-section-id') || '').trim().toLowerCase();
      }
      var href = baseurl + '/works/' + encodeURIComponent(fromWork) + '/';
      var q = [];
      if (seriesParam) q.push('series=' + encodeURIComponent(seriesParam));
      if (seriesPage > 0) q.push('series_page=' + encodeURIComponent(String(seriesPage)));
      if (q.length) href += '?' + q.join('&');
      var sectionHref = href;
      if (sectionId) sectionHref += '#details-' + encodeURIComponent(sectionId);
      if (hasWorkFilter) {
        if (contextEl) {
          contextEl.textContent = '';
          var workLink = document.createElement('a');
          workLink.className = 'worksList__countSeriesLink';
          workLink.href = href;
          workLink.textContent = fromWorkTitle || fromWork;
          contextEl.appendChild(workLink);
          if (sectionLabel) {
            contextEl.appendChild(document.createTextNode(' > '));
            var sectionLink = document.createElement('a');
            sectionLink.className = 'worksList__countSeriesLink';
            sectionLink.href = sectionHref;
            sectionLink.textContent = sectionLabel;
            contextEl.appendChild(sectionLink);
          }
          contextEl.hidden = false;
        }
      } else if (contextEl) {
        contextEl.hidden = true;
        contextEl.textContent = '';
      }

      if (!backNav || !backLink || !hasWorkFilter) return;
      var label = fromWorkTitle || fromWork;
      backLink.textContent = '← ' + label;
      backLink.setAttribute('href', sectionHref);
      backNav.hidden = false;
    }

    function updateRowLinks() {
      var rows = Array.prototype.slice.call(list.querySelectorAll('.worksList__item'));
      rows.forEach(function (row) {
        var catLink = row.querySelector('.worksList__cat');
        var titleLink = row.querySelector('.worksList__title');
        var rowSectionId = String(row.getAttribute('data-section-id') || '').trim().toLowerCase();
        var rowSectionLabel = String(row.getAttribute('data-section-label') || '').trim();
        [catLink, titleLink].forEach(function (link) {
          if (!link) return;
          var href = String(link.getAttribute('href') || '');
          var hashIndex = href.indexOf('#');
          var hash = '';
          if (hashIndex >= 0) {
            hash = href.slice(hashIndex);
            href = href.slice(0, hashIndex);
          }
          var qIndex = href.indexOf('?');
          var base = qIndex >= 0 ? href.slice(0, qIndex) : href;
          var query = new URLSearchParams(qIndex >= 0 ? href.slice(qIndex + 1) : '');
          if (hasWorkFilter) query.set('from_work', fromWork);
          if (fromWorkTitle) query.set('from_work_title', fromWorkTitle);
          var sec = sectionFilter || rowSectionId;
          if (sec) {
            query.set('section', sec);
            query.set('details_section', sec);
          }
          var secLabel = sectionLabelParam || rowSectionLabel;
          if (secLabel) query.set('section_label', secLabel);
          if (seriesParam) query.set('series', seriesParam);
          if (seriesPage > 0) query.set('series_page', String(seriesPage));
          link.setAttribute('href', base + '?' + query.toString() + hash);
        });
      });
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

    function persist(key, dir) {
      var next = new URLSearchParams(window.location.search);
      next.set('sort', key);
      next.set('dir', dir);
      var query = next.toString();
      var nextUrl = window.location.pathname + (query ? ('?' + query) : '') + window.location.hash;
      window.history.replaceState({}, '', nextUrl);
    }

    function makeRow(item) {
      var uid = normalize(item && item.detail_uid);
      if (!uid) return null;
      var title = normalize(item && item.title) || uid;
      var titleSort = normalize(item && item.title_sort).toLowerCase() || title.toLowerCase();
      var workId = normalize(item && item.work_id).toLowerCase();
      var sectionLabel = normalize(item && item.project_subfolder) || 'details';
      var sectionId = normalize(item && item.section_id).toLowerCase() || slug(sectionLabel);
      var href = baseurl + '/work_details/' + encodeURIComponent(uid) + '/';

      var li = document.createElement('li');
      li.className = 'worksList__item';
      li.setAttribute('data-cat', uid.toLowerCase());
      li.setAttribute('data-title', titleSort);
      li.setAttribute('data-work-id', workId);
      li.setAttribute('data-section-id', sectionId);
      li.setAttribute('data-section-label', sectionLabel);

      var cat = document.createElement('a');
      cat.className = 'worksList__cat';
      cat.href = href;
      cat.textContent = uid;
      li.appendChild(cat);

      var t = document.createElement('a');
      t.className = 'worksList__title';
      t.href = href;
      t.textContent = title;
      li.appendChild(t);

      return li;
    }

    function renderFromJson(payload) {
      var detailsMap = (payload && payload.details && typeof payload.details === 'object') ? payload.details : {};
      var rows = [];
      Object.keys(detailsMap).forEach(function (uid) {
        var row = makeRow(detailsMap[uid]);
        if (row) rows.push(row);
      });
      list.innerHTML = '';
      if (!rows.length) return false;
      var frag = document.createDocumentFragment();
      rows.forEach(function (row) { frag.appendChild(row); });
      list.appendChild(frag);
      return true;
    }

    fetch(detailsIndexUrl, { cache: 'default' })
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(function (payload) {
        var hasRows = renderFromJson(payload);
        if (!hasRows) {
          root.hidden = true;
          emptyEl.hidden = false;
          return;
        }

        buttons.forEach(function (btn) {
          btn.addEventListener('click', function () {
            var key = String(btn.getAttribute('data-sort-key') || '').toLowerCase();
            if (!validKeys[key]) return;
            if (key === sortKey) {
              sortDir = (sortDir === 'asc') ? 'desc' : 'asc';
            } else {
              sortKey = key;
              sortDir = 'asc';
            }
            applySort(sortKey, sortDir);
            updateHeaderState(sortKey, sortDir);
            persist(sortKey, sortDir);
          });
        });

        root.hidden = false;
        emptyEl.hidden = true;
        applySort(sortKey, sortDir);
        updateHeaderState(sortKey, sortDir);
        persist(sortKey, sortDir);
      })
      .catch(function () {
        root.hidden = true;
        emptyEl.hidden = false;
      });
  })();
</script>
