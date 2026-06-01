---
layout: default
title: "Works"
permalink: /works/
section: works
---

{% assign public_text = site.public_runtime_text | default: nil %}
{% assign loading_text = public_text.loading | default: "loading..." %}
{% assign unavailable_text = public_text.unavailable | default: "info not available" %}
{% assign media_base = site.media_base | default: "" %}
{% assign media_image_works = site.media_image_works | default: "/works/img" %}
{% assign thumb_base = site.thumb_base | default: "" %}
{% assign thumb_work_details = site.thumb_work_details | default: "/assets/work_details/img" %}
{% assign pipeline = site.data.pipeline %}
{% assign primary_variants = pipeline.variants.primary %}
{% assign compatibility_variants = pipeline.variants.compatibility %}
{% assign thumb_variants = pipeline.variants.thumb %}
{% assign primary_render_widths = compatibility_variants.render_widths | default: primary_variants.widths %}
{% assign primary_display_width = primary_render_widths | last %}
{% assign primary_full_width = primary_variants.preferred_width | default: primary_display_width %}
{% assign primary_suffix = primary_variants.suffix | default: "primary" %}
{% assign thumb_suffix = thumb_variants.suffix | default: "thumb" %}
{% assign asset_format = pipeline.encoding.format | default: "webp" %}
{% assign works_img_base = media_base | append: media_image_works | append: "/" %}
{% assign details_thumb_base = thumb_base | append: thumb_work_details | append: "/" %}
{% assign works_img_base_out = works_img_base %}
{% assign details_thumb_base_out = details_thumb_base %}
{% unless works_img_base contains '://' %}
  {% assign works_img_base_out = works_img_base | relative_url %}
{% endunless %}
{% unless details_thumb_base contains '://' %}
  {% assign details_thumb_base_out = details_thumb_base | relative_url %}
{% endunless %}

<article
  class="page work"
  id="selectedWorkRoot"
  data-baseurl="{{ site.baseurl | default: '' }}"
  data-works-img-base="{{ works_img_base_out | escape }}"
  data-details-thumb-base="{{ details_thumb_base_out | escape }}"
  data-primary-render-widths="{{ primary_render_widths | jsonify | escape }}"
  data-primary-display-width="{{ primary_display_width | escape }}"
  data-primary-full-width="{{ primary_full_width | escape }}"
  data-primary-suffix="{{ primary_suffix | escape }}"
  data-detail-thumb-sizes="{{ thumb_variants.sizes | default: '96,192' | jsonify | escape }}"
  data-detail-thumb-suffix="{{ thumb_suffix | escape }}"
  data-asset-format="{{ asset_format | escape }}"
  data-loading-text="{{ loading_text | escape }}"
  data-unavailable-text="{{ unavailable_text | escape }}"
  hidden
>
  <h1 class="visually-hidden" id="selectedWorkTitleHidden">{{ loading_text }}</h1>
  <figure class="page__media">
    <a class="page__mediaLink" id="selectedWorkMediaLink" target="_blank" rel="noopener" style="--work-ar: 4 / 3;">
      <img class="page__mediaImg" id="selectedWorkImg" sizes="(max-width: 800px) 100vw, 72ch" alt="" loading="eager" fetchpriority="high" decoding="async" style="width:100%;height:auto;display:block;">
    </a>
  </figure>
  <section class="page__meta page__media">
    <h2 class="visually-hidden">work details</h2>
    <div class="page__caption page__metaList">
      <div class="page__row work__titleRow">
        <span class="work__titleMain"><span id="selectedWorkTitleText">{{ loading_text }}</span></span>
        <nav class="seriesNav seriesNav--title" id="seriesNav" aria-label="Series navigation" data-work-id="" data-series="" data-baseurl="{{ site.baseurl | default: '' }}" hidden>
          <span class="navCounter" id="seriesNavCounter" hidden></span>
          <a class="seriesNav__prev" id="seriesNavPrev" href="#">←</a>
          <a class="seriesNav__next" id="seriesNavNext" href="#">→</a>
        </nav>
      </div>
      <div class="page__row" id="selectedWorkYearRow" hidden><span id="selectedWorkYearText"></span></div>
      <div class="page__row" id="selectedWorkMediumRow" hidden><span id="selectedWorkMediumText"></span></div>
      <div class="page__row" id="selectedWorkDimensionsRow" hidden><span id="selectedWorkDimensionsText"></span></div>
      <div class="page__row" id="selectedWorkCatRow">cat. <span id="selectedWorkCatText"></span> <span id="workSeriesLinkWrap" hidden>| <a id="workSeriesLink" class="work__seriesLink" href="{{ '/series/' | relative_url }}"></a></span></div>
    </div>
  </section>
  <section class="content work__prose" id="selectedWorkProseSection" hidden>
    <div id="selectedWorkProseContent"></div>
  </section>
  <section class="workDetails" id="selectedWorkDetailsSection" hidden>
    <h2 class="visually-hidden">Additional details</h2>
    <div id="selectedWorkDetailsContent"></div>
  </section>
  <nav class="page__nav">
    <a id="pageBackLink" class="page__back" href="{{ '/series/' | relative_url }}" data-baseurl="{{ site.baseurl | default: '' }}" data-series-label="series">← works</a>
  </nav>
</article>

<div class="index worksList" id="worksIndexRoot" hidden>
  <h1 class="index__heading visually-hidden">works</h1>
  <p class="worksList__count" id="worksListCount"></p>

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

  <ul class="worksList__list" id="worksList"></ul>

  <nav class="page__nav" id="worksIndexBackNav" hidden>
    <a
      class="page__back"
      id="worksIndexBackLink"
      href="{{ '/series/' | relative_url }}"
    >← series</a>
  </nav>
</div>
<p id="worksEmpty" hidden>no works yet</p>

<script src="{{ '/assets/js/public-catalogue-runtime.js' | relative_url }}?v={{ site.time | date: '%s' }}"></script>
<script>
  (function () {
    var root = document.getElementById('selectedWorkRoot');
    var runtime = window.__dlfPublicCatalogueRuntime;
    if (!root || !runtime) return;

    var routeState = runtime.parseRouteState(window.location);
    var workId = String(routeState.work || '').trim();
    if (!workId) return;

    var baseurl = runtime.trimBaseurl(root.getAttribute('data-baseurl'));
    var worksImgBase = String(root.getAttribute('data-works-img-base') || '').trim();
    var detailsThumbBase = String(root.getAttribute('data-details-thumb-base') || '').trim();
    var primaryDisplayWidth = runtime.toPositiveInteger(root.getAttribute('data-primary-display-width')) || 1200;
    var primaryFullWidth = runtime.toPositiveInteger(root.getAttribute('data-primary-full-width')) || primaryDisplayWidth;
    var primarySuffix = runtime.text(root.getAttribute('data-primary-suffix')) || 'primary';
    var detailThumbSuffix = runtime.text(root.getAttribute('data-detail-thumb-suffix')) || 'thumb';
    var assetFormat = runtime.text(root.getAttribute('data-asset-format')) || 'webp';
    var unavailableText = String(root.getAttribute('data-unavailable-text') || 'info not available');
    var renderWidths = [];
    var detailThumbSizes = [];
    try {
      renderWidths = JSON.parse(root.getAttribute('data-primary-render-widths') || '[]');
    } catch (err) {
      renderWidths = [];
    }
    try {
      detailThumbSizes = JSON.parse(root.getAttribute('data-detail-thumb-sizes') || '[]');
    } catch (err) {
      detailThumbSizes = [];
    }
    renderWidths = runtime.normalizePositiveSizes(renderWidths, [primaryDisplayWidth]);
    detailThumbSizes = runtime.normalizePositiveSizes(detailThumbSizes, [96, 192]);

    function esc(value) {
      return String(value == null ? '' : value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
    }

    function setText(id, value) {
      var node = document.getElementById(id);
      if (node) node.textContent = value;
    }

    function setRow(rowId, textId, value) {
      var row = document.getElementById(rowId);
      if (!row) return;
      var text = runtime.text(value);
      setText(textId, text);
      row.hidden = !text;
    }

    function workImageUrl(id, width) {
      return worksImgBase + encodeURIComponent(id) + '-' + primarySuffix + '-' + String(width) + '.' + assetFormat;
    }

    function dimensionsText(meta) {
      var mediumType = runtime.text(meta && meta.medium_type).toLowerCase();
      if (mediumType === 'music') return '';
      var h = runtime.toNumber(meta && meta.height_cm);
      var w = runtime.toNumber(meta && meta.width_cm);
      var d = runtime.toNumber(meta && meta.depth_cm);
      if (h != null && w != null) {
        var base = String(h) + ' × ' + String(w);
        if (d != null && d > 0) base += ' × ' + String(d);
        return base + ' cm';
      }
      if (h != null) return String(h) + ' cm';
      if (w != null) return String(w) + ' cm';
      return '';
    }

    function updateBackLink(work) {
      var link = document.getElementById('pageBackLink');
      if (!link) return;
      if (routeState.series) {
        link.textContent = '← series';
        link.setAttribute('href', runtime.catalogueIndexUrl(baseurl, { series: routeState.series, seriesPage: routeState.seriesPage }));
        return;
      }
      if (routeState.from === 'recent') {
        link.textContent = '← recently added';
        link.setAttribute('href', baseurl + '/recent/');
        return;
      }
      link.textContent = '← works';
      link.setAttribute('href', runtime.catalogueIndexUrl(baseurl));
    }

    function renderMedia(work) {
      var link = document.getElementById('selectedWorkMediaLink');
      var img = document.getElementById('selectedWorkImg');
      if (!link || !img) return;
      var displaySrc = workImageUrl(workId, primaryDisplayWidth);
      var fullSrc = workImageUrl(workId, primaryFullWidth);
      var srcset = renderWidths.map(function (width) {
        return workImageUrl(workId, width) + ' ' + String(width) + 'w';
      }).join(', ');
      var widthPx = runtime.toNumber(work && work.width_px);
      var heightPx = runtime.toNumber(work && work.height_px);
      if (widthPx && heightPx) link.style.setProperty('--work-ar', String(widthPx) + ' / ' + String(heightPx));
      link.setAttribute('href', fullSrc);
      img.setAttribute('src', displaySrc);
      img.setAttribute('srcset', srcset);
      img.setAttribute('alt', runtime.text(work && work.title) || workId);
    }

    function renderDetails(payload, workTitle) {
      var section = document.getElementById('selectedWorkDetailsSection');
      var content = document.getElementById('selectedWorkDetailsContent');
      if (!section || !content) return;
      var sections = payload && Array.isArray(payload.sections) ? payload.sections : [];
      var html = '';
      sections.forEach(function (sec) {
        var label = runtime.text(sec && (sec.section_title || sec.project_subfolder)) || 'Details';
        var sectionId = runtime.slug(sec && (sec.section_id || label)) || 'details';
        var details = sec && Array.isArray(sec.details) ? sec.details : [];
        if (!details.length) return;
        html += '<section class="workDetails__group" id="details-' + esc(sectionId) + '">';
        html += '<h3 class="workDetails__title">' + esc(label) + '</h3>';
        html += '<div class="seriesGrid" aria-label="details for ' + esc(label) + '">';
        details.forEach(function (detail) {
          var uid = runtime.text(detail && detail.detail_uid);
          if (!uid) return;
          var title = runtime.text(detail && detail.title) || uid;
          var thumbPrimary = runtime.thumbUrl(detailsThumbBase, uid, detailThumbSuffix, detailThumbSizes[0], assetFormat);
          var thumbSrcset = runtime.thumbSrcset(detailsThumbBase, uid, detailThumbSizes.slice(0, 2), detailThumbSuffix, assetFormat);
          var href = runtime.workDetailUrl(uid, baseurl, {
            from_work: workId,
            from_work_title: workTitle,
            section: sectionId,
            details_section: sectionId,
            series: routeState.series,
            series_page: routeState.seriesPage
          });
          html += '<a class="seriesGrid__item" href="' + esc(href) + '" title="' + esc(title) + '">';
          html += '<img class="seriesGrid__img" src="' + esc(thumbPrimary) + '" srcset="' + esc(thumbSrcset) + '" sizes="(min-width: 1200px) 10vw, (min-width: 700px) 14vw, 22vw" width="' + esc(String(detailThumbSizes[0])) + '" height="' + esc(String(detailThumbSizes[0])) + '" loading="lazy" decoding="async" alt="' + esc(title) + '">';
          html += '</a>';
        });
        html += '</div></section>';
      });
      content.innerHTML = html;
      section.hidden = !html;
    }

    runtime.fetchJson(runtime.workPayloadUrl(workId, baseurl))
      .then(function (payload) {
        var work = payload && payload.work && typeof payload.work === 'object' ? payload.work : { work_id: workId, title: unavailableText };
        var title = runtime.text(work.title) || workId;
        root.hidden = false;
        setText('selectedWorkTitleHidden', title);
        setText('selectedWorkTitleText', title);
        setText('selectedWorkCatText', runtime.text(work.work_id) || workId);
        setRow('selectedWorkYearRow', 'selectedWorkYearText', runtime.text(work.year_display) || runtime.text(work.year));
        setRow('selectedWorkMediumRow', 'selectedWorkMediumText', runtime.text(work.medium_caption));
        setRow('selectedWorkDimensionsRow', 'selectedWorkDimensionsText', dimensionsText(work));
        document.title = title + ' | dotlineform';
        renderMedia(work);
        updateBackLink(work);

        var nav = document.getElementById('seriesNav');
        var seriesIds = Array.isArray(work.series_ids) ? work.series_ids.map(runtime.text).filter(Boolean) : [];
        var primarySeries = seriesIds.length ? seriesIds[0] : '';
        if (nav) {
          nav.setAttribute('data-work-id', workId);
          nav.setAttribute('data-series', primarySeries);
          nav.setAttribute('data-series-ids', seriesIds.join(','));
        }
        try {
          document.dispatchEvent(new CustomEvent('dlf:work-metadata-applied', {
            detail: { work_id: workId, series_id: primarySeries, series_ids: seriesIds }
          }));
        } catch (err) {
        }

        var proseSection = document.getElementById('selectedWorkProseSection');
        var prose = document.getElementById('selectedWorkProseContent');
        if (prose && typeof payload.content_html === 'string' && payload.content_html.trim()) {
          prose.innerHTML = payload.content_html;
          if (proseSection) proseSection.hidden = false;
        }
        renderDetails(payload, title);
      })
      .catch(function () {
        root.hidden = false;
        setText('selectedWorkTitleHidden', unavailableText);
        setText('selectedWorkTitleText', unavailableText);
        setText('selectedWorkCatText', workId);
        updateBackLink({});
      });
  })();
</script>
<script src="{{ '/assets/js/work.js' | relative_url }}?v={{ site.time | date: '%s' }}"></script>
<script>
  (function () {
    var routeRuntime = window.__dlfPublicCatalogueRuntime;
    if (routeRuntime && routeRuntime.parseRouteState(window.location).work) return;

    var worksListRoot = document.getElementById('worksIndexRoot');
    var emptyEl = document.getElementById('worksEmpty');
    var list = document.getElementById('worksList');
    var countEl = document.getElementById('worksListCount');
    var backNav = document.getElementById('worksIndexBackNav');
    var backLink = document.getElementById('worksIndexBackLink');
    var buttons = Array.prototype.slice.call(document.querySelectorAll('.worksList__sortBtn'));
    if (!worksListRoot || !emptyEl || !list || !countEl || !buttons.length) return;

    var runtime = window.__dlfPublicCatalogueRuntime;
    if (!runtime) return;

    var baseurl = {{ site.baseurl | default: '' | jsonify }};
    var worksIndexUrl = baseurl + '/assets/data/works_index.json';
    var seriesIndexUrl = baseurl + '/assets/data/series_index.json';
    var validKeys = { cat: true, year: true, title: true, series: true, seriessort: true };
    var collator = new Intl.Collator(undefined, { numeric: true, sensitivity: 'base' });
    var params = new URLSearchParams(window.location.search);
    var sortParam = params.get('sort');
    var hasExplicitSort = !(sortParam == null || String(sortParam).trim() === '');
    var sortKey = String(sortParam || '').toLowerCase();
    var sortDir = String(params.get('dir') || 'asc').toLowerCase();
    var seriesFilter = String(params.get('series') || '').trim().toLowerCase();
    var hasSeriesFilter = seriesFilter.length > 0;
    var seriesBaseHref = runtime.catalogueIndexUrl(baseurl);
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
          seriesLink.href = runtime.catalogueIndexUrl(baseurl, { series: seriesFilter });
          seriesLink.textContent = seriesLabel;
          countEl.appendChild(seriesLink);
        }
        if (backNav && backLink) {
          backNav.hidden = false;
          backLink.setAttribute('href', runtime.catalogueIndexUrl(baseurl, { series: seriesFilter }));
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
      var rawSeriesIds = Array.isArray(work && work.series_ids) ? work.series_ids : [];
      var sid = slugSortKey(rawSeriesIds.length ? rawSeriesIds[0] : '');
      var sm = sid ? (seriesMetaById[sid] || null) : null;
      var seriesLabel = (sm && sm.label) ? sm.label : (sid || '');
      var seriesPrimarySort = (sm && sm.primary_sort) ? sm.primary_sort : '';
      var yearVal = Number(work && work.year);
      if (!Number.isFinite(yearVal)) yearVal = 0;
      var yearDisplay = normalizeText(work && work.year_display) || normalizeText(work && work.year);
      var titleRaw = normalizeText(work && work.title) || wid;
      var titleSortRaw = normalizeText(work && work.title_sort);
      var titleSort = (titleSortRaw || numericAwareSortKey(titleRaw)).toLowerCase();
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
      li.setAttribute('data-series-id', sid);
      li.setAttribute('data-series-label', seriesLabel);

      var workHref = runtime.workUrl(wid, baseurl, { from: 'works_index' });

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
      seriesA.href = sid ? runtime.catalogueIndexUrl(baseurl, { series: sid }) : seriesBaseHref;
      seriesA.textContent = seriesLabel;
      li.appendChild(seriesA);

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
        initSortUi();
      })
      .catch(function () {
        worksListRoot.hidden = true;
        emptyEl.hidden = false;
      });
  })();
</script>
