---
layout: default
title: Work Details
permalink: /work_details/
section: works
---

{% assign details_items = site.work_details %}
{% if details_items and details_items != empty %}
  {% assign details_sorted = details_items | sort_natural: "title" %}
  {% assign details_count = details_sorted.size %}
  {% assign detail_label = "details" %}
  {% if details_count == 1 %}
    {% assign detail_label = "detail" %}
  {% endif %}

  <div class="index worksList detailsList">
    <h1 class="index__heading visually-hidden">work details</h1>
    <p class="worksList__count" id="workDetailsListCount">{{ details_count }} {{ detail_label }}</p>

    <div class="worksList__head" role="group" aria-label="Sort work details">
      <button class="worksList__sortBtn" type="button" data-sort-key="cat">
        cat <span class="worksList__sortIcon" aria-hidden="true"></span>
      </button>
      <button class="worksList__sortBtn" type="button" data-sort-key="title">
        title <span class="worksList__sortIcon" aria-hidden="true"></span>
      </button>
    </div>

    <ul class="worksList__list" id="workDetailsList">
      {% for d in details_sorted %}
        {% assign detail_cat = d.detail_uid %}
        {% assign detail_section = d.project_subfolder | default: "details" %}
        {% assign detail_section_id = detail_section | slugify %}
        <li
          class="worksList__item"
          data-cat="{{ detail_cat | default: '' | downcase | strip | escape }}"
          data-title="{{ d.title | default: '' | downcase | strip | escape }}"
          data-work-id="{{ d.work_id | default: '' | downcase | strip | escape }}"
          data-section-id="{{ detail_section_id | default: '' | downcase | strip | escape }}"
          data-section-label="{{ detail_section | default: '' | strip | escape }}"
        >
          <a class="worksList__cat" href="{{ d.url | relative_url }}">{{ detail_cat }}</a>
          <a class="worksList__title" href="{{ d.url | relative_url }}">{{ d.title }}</a>
        </li>
      {% endfor %}
    </ul>

    <nav class="page__nav" id="workDetailsIndexBackNav" hidden>
      <a
        class="page__back"
        id="workDetailsIndexBackLink"
        href="{{ '/works/' | relative_url }}"
      >← work</a>
    </nav>
  </div>

  <script>
    (function () {
      var list = document.getElementById('workDetailsList');
      if (!list) return;
      var buttons = Array.prototype.slice.call(document.querySelectorAll('.worksList__sortBtn'));
      if (!buttons.length) return;

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
      var countEl = document.getElementById('workDetailsListCount');
      var backNav = document.getElementById('workDetailsIndexBackNav');
      var backLink = document.getElementById('workDetailsIndexBackLink');
      var hasWorkFilter = fromWork.length > 0;
      var hasSectionFilter = sectionFilter.length > 0;
      var baseurl = '{{ site.baseurl | default: "" }}';
      if (!validKeys[sortKey]) sortKey = 'cat';
      if (sortDir !== 'asc' && sortDir !== 'desc') sortDir = 'asc';

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
        updateCountAndBack(visibleRows);
        updateRowLinks();
      }

      function updateCountAndBack(visibleRows) {
        if (!countEl) return;
        var count = visibleRows.length;
        var word = count === 1 ? 'detail' : 'details';
        countEl.textContent = '';
        countEl.appendChild(document.createTextNode(String(count) + ' ' + word));
        var sectionLabel = sectionLabelParam;
        if (!sectionLabel && visibleRows.length) {
          sectionLabel = String(visibleRows[0].getAttribute('data-section-label') || '').trim();
        }
        var href = baseurl + '/works/' + encodeURIComponent(fromWork) + '/';
        var q = [];
        if (seriesParam) q.push('series=' + encodeURIComponent(seriesParam));
        if (seriesPage > 0) q.push('series_page=' + encodeURIComponent(String(seriesPage)));
        if (q.length) href += '?' + q.join('&');
        if (sectionFilter) href += '#details-' + encodeURIComponent(sectionFilter);
        if (hasWorkFilter) {
          countEl.appendChild(document.createTextNode(' in '));
          var targetLabel = sectionLabel || fromWorkTitle || fromWork;
          var countLink = document.createElement('a');
          countLink.className = 'worksList__countSeriesLink';
          countLink.href = href;
          countLink.textContent = targetLabel;
          countEl.appendChild(countLink);
        } else if (sectionLabel) {
          countEl.appendChild(document.createTextNode(' in ' + sectionLabel));
        }

        if (!backNav || !backLink || !hasWorkFilter) return;
        var label = fromWorkTitle || fromWork;
        backLink.textContent = '← ' + label;
        backLink.setAttribute('href', href);
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

      applySort(sortKey, sortDir);
      updateHeaderState(sortKey, sortDir);
      persist(sortKey, sortDir);
    })();
  </script>

{% else %}
  <p>no work details yet</p>
{% endif %}
