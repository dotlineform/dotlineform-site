---
layout: default
title: Works
permalink: /works/
section: works
---

{% assign works_items = site.works %}
{% if works_items and works_items != empty %}
  {% assign works_sorted = works_items | sort_natural: "series_title" | sort_natural: "title" %}
  {% assign works_count = works_sorted.size %}
  {% assign series_ids_csv = "" %}
  {% for w in works_sorted %}
    {% assign sid = w.series_id | default: "" | strip %}
    {% if sid != "" %}
      {% assign token = "|" | append: sid | append: "|" %}
      {% unless series_ids_csv contains token %}
        {% assign series_ids_csv = series_ids_csv | append: token %}
      {% endunless %}
    {% endif %}
  {% endfor %}
  {% assign series_tokens = series_ids_csv | split: "|" %}
  {% assign series_count = 0 %}
  {% for t in series_tokens %}
    {% assign t_clean = t | strip %}
    {% if t_clean != "" %}
      {% assign series_count = series_count | plus: 1 %}
    {% endif %}
  {% endfor %}
  {% assign work_label = "works" %}
  {% if works_count == 1 %}
    {% assign work_label = "work" %}
  {% endif %}
  {% assign series_label = "series" %}

  <div class="index worksList">
    <h1 class="index__heading visually-hidden">works</h1>
    <p class="worksList__count" id="worksListCount">{{ works_count }} {{ work_label }} in {{ series_count }} {{ series_label }}</p>

    <div class="worksList__head" role="group" aria-label="Sort works">
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
    </div>

    <ul class="worksList__list" id="worksList">
      {% for w in works_sorted %}
        {% assign series_label = w.series_title | default: w.series_id %}
        {% assign series_href = "/series/" | append: w.series_id | append: "/" %}
        {% assign series_doc = site.series | where: "series_id", w.series_id | first %}
        {% assign series_primary_sort = "" %}
        {% if series_doc and series_doc.sort_fields %}
          {% assign sort_token = series_doc.sort_fields | split: "," | first | strip | downcase %}
          {% assign sort_token_first_char = sort_token | slice: 0, 1 %}
          {% if sort_token != "" and sort_token_first_char == "-" %}
            {% assign sort_token = sort_token | slice: 1, 999 %}
          {% endif %}
          {% if sort_token == "work_id" %}
            {% assign series_primary_sort = "cat" %}
          {% elsif sort_token == "year" %}
            {% assign series_primary_sort = "year" %}
          {% elsif sort_token == "title" or sort_token == "title_sort" %}
            {% assign series_primary_sort = "title" %}
          {% elsif sort_token == "series" or sort_token == "series_title" %}
            {% assign series_primary_sort = "series" %}
          {% endif %}
        {% endif %}
        <li
          class="worksList__item"
          data-cat="{{ w.work_id | default: '' | downcase | strip | escape }}"
          data-series-sort="{{ w.series_sort | default: w.work_id | downcase | strip | escape }}"
          data-series-primary-sort="{{ series_primary_sort | default: '' | downcase | strip | escape }}"
          data-year="{{ w.year | default: 0 }}"
          data-title="{{ w.title | downcase | strip | escape }}"
          data-series="{{ series_label | downcase | strip | escape }}"
          data-series-id="{{ w.series_id | default: '' | downcase | strip | escape }}"
          data-series-label="{{ series_label | strip | escape }}"
        >
          <a class="worksList__cat" href="{{ w.url | relative_url }}?from=works_index">{{ w.work_id }}</a>
          <span class="worksList__year">{{ w.year_display | default: w.year }}</span>
          <a class="worksList__title" href="{{ w.url | relative_url }}?from=works_index">{{ w.title }}</a>
          <a class="worksList__series" href="{{ series_href | relative_url }}">{{ series_label }}</a>
        </li>
      {% endfor %}
    </ul>

    <nav class="page__nav" id="worksIndexBackNav" hidden>
      <a
        class="page__back"
        id="worksIndexBackLink"
        href="{{ '/series/' | relative_url }}"
      >← series</a>
    </nav>
  </div>

  <script>
    (function () {
      var list = document.getElementById('worksList');
      if (!list) return;
      var buttons = Array.prototype.slice.call(document.querySelectorAll('.worksList__sortBtn'));
      if (!buttons.length) return;

      var validKeys = { cat: true, year: true, title: true, series: true, seriessort: true };
      var collator = new Intl.Collator(undefined, { numeric: true, sensitivity: 'base' });
      var params = new URLSearchParams(window.location.search);
      var sortParam = params.get('sort');
      var hasExplicitSort = !(sortParam == null || String(sortParam).trim() === '');
      var sortKey = String(sortParam || '').toLowerCase();
      var sortDir = String(params.get('dir') || 'asc').toLowerCase();
      var seriesFilter = String(params.get('series') || '').trim().toLowerCase();
      var hasSeriesFilter = seriesFilter.length > 0;
      var seriesBaseHref = '{{ "/series/" | relative_url }}';
      var countEl = document.getElementById('worksListCount');
      var backNav = document.getElementById('worksIndexBackNav');
      var backLink = document.getElementById('worksIndexBackLink');
      var worksListRoot = document.querySelector('.worksList');
      var visualSortKey = sortKey;
      if (!hasExplicitSort) sortKey = hasSeriesFilter ? 'seriessort' : 'cat';
      if (!validKeys[sortKey]) sortKey = hasSeriesFilter ? 'seriessort' : 'cat';
      if (!validKeys[sortKey]) sortKey = 'cat';
      if (sortDir !== 'asc' && sortDir !== 'desc') sortDir = 'asc';
      if (hasSeriesFilter && worksListRoot) {
        worksListRoot.classList.add('worksList--singleSeries');
      }

      function rowMatchesSeries(row) {
        if (!hasSeriesFilter) return true;
        var rowSeriesId = String(row.getAttribute('data-series-id') || '').trim().toLowerCase();
        return rowSeriesId === seriesFilter;
      }

      function updateCount(visibleRows) {
        if (!countEl || !hasSeriesFilter) return;
        var workCount = visibleRows.length;
        var workWord = workCount === 1 ? 'work' : 'works';
        var seriesLabel = '';
        if (visibleRows.length) {
          seriesLabel = String(visibleRows[0].getAttribute('data-series-label') || '').trim();
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
      }

      function compareValues(a, b, key) {
        if (key === 'year') {
          var av = Number(a.getAttribute('data-year') || '0');
          var bv = Number(b.getAttribute('data-year') || '0');
          return av - bv;
        }
        if (key === 'seriessort') {
          var aSeriesSort = String(a.getAttribute('data-series-sort') || '');
          var bSeriesSort = String(b.getAttribute('data-series-sort') || '');
          return collator.compare(aSeriesSort, bSeriesSort);
        }
        var as = String(a.getAttribute('data-' + key) || '');
        var bs = String(b.getAttribute('data-' + key) || '');
        return collator.compare(as, bs);
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
          return compareValues(a, b, 'series');
        });
        visibleRows.forEach(function (row) { list.appendChild(row); });
        updateCount(visibleRows);
        updateRowLinks(key, dir);
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
          query.set('from', 'works_index');
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
          var a = String(row.getAttribute('data-series-sort') || '');
          var b = String(row.getAttribute('data-cat') || '');
          return a === b;
        });
        if (sameAsCat) return 'cat';

        for (var i = 0; i < rows.length; i += 1) {
          var hint = String(rows[i].getAttribute('data-series-primary-sort') || '').toLowerCase();
          if (validKeys[hint] && hint !== 'seriessort') return hint;
        }
        return 'cat';
      }

      function persist(key, dir) {
        var next = new URLSearchParams(window.location.search);
        next.set('sort', key);
        next.set('dir', dir);
        var query = next.toString();
        var nextUrl = window.location.pathname + (query ? ('?' + query) : '') + window.location.hash;
        window.history.replaceState({}, '', nextUrl);
      }

      buttons.forEach(function (btn) {
        btn.addEventListener('click', function () {
          var key = String(btn.getAttribute('data-sort-key') || '').toLowerCase();
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
    })();
  </script>

{% else %}
  <p>no works yet</p>
{% endif %}
