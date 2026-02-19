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
        <li
          class="worksList__item"
          data-cat="{{ detail_cat | default: '' | downcase | strip | escape }}"
          data-title="{{ d.title | default: '' | downcase | strip | escape }}"
        >
          <a class="worksList__cat" href="{{ d.url | relative_url }}">{{ detail_cat }}</a>
          <a class="worksList__title" href="{{ d.url | relative_url }}">{{ d.title }}</a>
        </li>
      {% endfor %}
    </ul>
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
      if (!validKeys[sortKey]) sortKey = 'cat';
      if (sortDir !== 'asc' && sortDir !== 'desc') sortDir = 'asc';

      function compareValues(a, b, key) {
        var as = String(a.getAttribute('data-' + key) || '');
        var bs = String(b.getAttribute('data-' + key) || '');
        return collator.compare(as, bs);
      }

      function applySort(key, dir) {
        var rows = Array.prototype.slice.call(list.querySelectorAll('.worksList__item'));
        rows.sort(function (a, b) {
          var primary = compareValues(a, b, key);
          if (primary !== 0) return dir === 'asc' ? primary : -primary;

          var tieTitle = compareValues(a, b, 'title');
          if (tieTitle !== 0) return tieTitle;
          return compareValues(a, b, 'cat');
        });
        rows.forEach(function (row) { list.appendChild(row); });
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
