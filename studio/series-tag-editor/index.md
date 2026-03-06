---
layout: default
title: Series Tag Editor
permalink: /studio/series-tag-editor/
section: works
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<article class="page tagStudioPage" id="seriesTagEditorRoot" hidden>
  <header class="tagStudioPage__header">
    <figure class="tagStudioPage__media" id="seriesTagEditorMedia" hidden>
      <a
        class="page__mediaLink"
        id="seriesTagEditorMediaLink"
        href="#"
        target="_blank"
        rel="noopener"
        style="--work-ar: 4 / 3;"
      >
        <img
          class="tagStudioPage__mediaImg"
          id="seriesTagEditorMediaImg"
          src=""
          srcset=""
          sizes="(max-width: 900px) 100vw, 40vw"
          alt=""
          loading="eager"
          fetchpriority="high"
          decoding="async"
        >
      </a>
    </figure>

    <section class="tagStudioPage__context">
      <h1 class="tagStudioPage__title" id="seriesTagEditorTitle">Series Tag Editor</h1>
      <div class="workCurator__rows" style="font-size:var(--meta-small-size);line-height:var(--meta-small-line);">
        <div class="page__row">
          cat
          <span id="seriesTagEditorCat">—</span>
        </div>
        <div class="page__row">year <span id="seriesTagEditorYear">—</span></div>
        <div class="page__row">year display <span id="seriesTagEditorYearDisplay">—</span></div>
        <div class="page__row">sort fields <span id="seriesTagEditorSortFields">—</span></div>
        <div class="page__row">primary work <span id="seriesTagEditorPrimaryWork">—</span></div>
        <div class="page__row">project folders <span id="seriesTagEditorFolders">—</span></div>
        <div class="page__row">notes <span id="seriesTagEditorNotes">—</span></div>
      </div>
    </section>
  </header>

  <section class="tagStudioPage__editor">
    <div id="tag-studio"></div>
  </section>
</article>
<p id="seriesTagEditorEmpty" hidden></p>

<script type="module">
  (function () {
    var root = document.getElementById('seriesTagEditorRoot');
    var emptyEl = document.getElementById('seriesTagEditorEmpty');
    var mount = document.getElementById('tag-studio');
    if (!root || !emptyEl || !mount) return;

    var titleEl = document.getElementById('seriesTagEditorTitle');
    var catEl = document.getElementById('seriesTagEditorCat');
    var yearEl = document.getElementById('seriesTagEditorYear');
    var yearDisplayEl = document.getElementById('seriesTagEditorYearDisplay');
    var sortFieldsEl = document.getElementById('seriesTagEditorSortFields');
    var primaryWorkEl = document.getElementById('seriesTagEditorPrimaryWork');
    var foldersEl = document.getElementById('seriesTagEditorFolders');
    var notesEl = document.getElementById('seriesTagEditorNotes');
    var mediaFigureEl = document.getElementById('seriesTagEditorMedia');
    var mediaLinkEl = document.getElementById('seriesTagEditorMediaLink');
    var mediaImgEl = document.getElementById('seriesTagEditorMediaImg');
    var baseurl = {{ site.baseurl | default: '' | jsonify }};
    var mediaBase = {{ site.media_base | default: '' | jsonify }};
    var mediaPrefixRaw = {{ site.media_prefix | jsonify }};
    var mediaPrefix = (mediaPrefixRaw == null) ? '/assets' : String(mediaPrefixRaw);
    var params = new URLSearchParams(window.location.search);
    var seriesIdQuery = String(params.get('series') || '').trim().toLowerCase();
    var seriesIndexUrl = baseurl + '/assets/data/series_index.json';
    var defaultMediaWorkId = '';
    var defaultMediaTitle = '';
    var currentMediaWorkId = '';

    function showError(message) {
      root.hidden = true;
      emptyEl.hidden = false;
      emptyEl.textContent = message;
    }

    function textOrDash(value) {
      var text = String(value == null ? '' : value).trim();
      return text || '—';
    }

    function setLinkOrDash(el, href, label) {
      if (!el) return;
      var text = String(label == null ? '' : label).trim();
      if (!text) {
        el.textContent = '—';
        return;
      }
      el.textContent = '';
      var a = document.createElement('a');
      a.href = href;
      a.textContent = text;
      el.appendChild(a);
    }

    function normalizeSeriesMap(seriesMap) {
      var map = {};
      if (!seriesMap || typeof seriesMap !== 'object') return map;
      Object.keys(seriesMap).forEach(function (key) {
        var id = String(key || '').trim().toLowerCase();
        if (!id) return;
        map[id] = seriesMap[key];
      });
      return map;
    }

    function applyBaseurl(url) {
      if (/^[a-z]+:\/\//i.test(url)) return url;
      if (url.charAt(0) === '/') return baseurl + url;
      return url;
    }

    function worksImgBasePath() {
      var base = String(mediaBase || '').replace(/\/+$/, '');
      var prefix = String(mediaPrefix || '').replace(/\/+$/, '');
      if (base) return base + prefix + '/works/img/';
      return applyBaseurl((prefix || '') + '/works/img/').replace(/\/{2,}/g, '/');
    }

    function fetchWorkRecord(primaryWorkId) {
      var url = baseurl + '/assets/works/index/' + encodeURIComponent(primaryWorkId) + '.json';
      return fetch(url, { cache: 'default' })
        .then(function (response) {
          if (!response.ok) throw new Error('HTTP ' + response.status);
          return response.json();
        })
        .then(function (payload) {
          return payload && payload.work && typeof payload.work === 'object' ? payload.work : null;
        })
        .catch(function () {
          return null;
        });
    }

    function renderPrimaryMedia(primaryWorkId, displayTitle) {
      if (!mediaFigureEl || !mediaLinkEl || !mediaImgEl) return Promise.resolve();
      if (!primaryWorkId) {
        mediaFigureEl.hidden = true;
        return Promise.resolve();
      }

      var imgBase = worksImgBasePath();
      var src800 = imgBase + primaryWorkId + '-primary-800.webp';
      var src1200 = imgBase + primaryWorkId + '-primary-1200.webp';
      var src1600 = imgBase + primaryWorkId + '-primary-1600.webp';
      var src2400 = imgBase + primaryWorkId + '-primary-2400.webp';

      return fetchWorkRecord(primaryWorkId).then(function (work) {
        var widthCm = Number(work && work.width_cm);
        var heightCm = Number(work && work.height_cm);
        if (!Number.isFinite(widthCm) || widthCm <= 0) widthCm = 4;
        if (!Number.isFinite(heightCm) || heightCm <= 0) heightCm = 3;
        var has2400 = !!(work && work.has_primary_2400 === true);
        var fullSrc = has2400 ? src2400 : src1600;
        var srcset = src800 + ' 800w, ' + src1200 + ' 1200w, ' + src1600 + ' 1600w';
        if (has2400) srcset += ', ' + src2400 + ' 2400w';

        mediaLinkEl.href = fullSrc;
        mediaLinkEl.style.setProperty('--work-ar', String(widthCm) + ' / ' + String(heightCm));
        mediaImgEl.src = src1600;
        mediaImgEl.setAttribute('srcset', srcset);
        mediaImgEl.alt = displayTitle;
        mediaFigureEl.hidden = false;
      });
    }

    function syncHeaderMediaForWork(workId) {
      var nextWorkId = String(workId || '').trim();
      var targetWorkId = nextWorkId || defaultMediaWorkId;
      var targetTitle = defaultMediaTitle || titleEl.textContent || 'Series Tag Editor';
      if (!targetWorkId || currentMediaWorkId === targetWorkId) return;
      currentMediaWorkId = targetWorkId;
      renderPrimaryMedia(targetWorkId, targetTitle).catch(function (err) {
        console.error('series_tag_editor: failed to render selected media', err);
        if (mediaFigureEl) mediaFigureEl.hidden = true;
      });
    }

    if (!seriesIdQuery) {
      showError('Missing series id. Open this page with ?series=<series_id>.');
      return;
    }

    fetch(seriesIndexUrl, { cache: 'default' })
      .then(function (response) {
        if (!response.ok) throw new Error('HTTP ' + response.status);
        return response.json();
      })
      .then(function (payload) {
        var rawSeriesMap = (payload && payload.series && typeof payload.series === 'object') ? payload.series : {};
        var seriesMap = normalizeSeriesMap(rawSeriesMap);
        var row = seriesMap[seriesIdQuery];
        if (!row || typeof row !== 'object') {
          showError('Unknown series id: ' + seriesIdQuery);
          return;
        }

        var seriesTitle = textOrDash(row.title);
        titleEl.textContent = seriesTitle;
        setLinkOrDash(catEl, baseurl + '/series/' + encodeURIComponent(seriesIdQuery) + '/', seriesIdQuery);
        yearEl.textContent = textOrDash(row.year);
        yearDisplayEl.textContent = textOrDash(row.year_display);
        sortFieldsEl.textContent = textOrDash(row.sort_fields);

        var primaryWorkId = String(row.primary_work_id || '').trim();
        if (primaryWorkId) {
          setLinkOrDash(primaryWorkEl, baseurl + '/works/' + encodeURIComponent(primaryWorkId) + '/', primaryWorkId);
        } else {
          primaryWorkEl.textContent = '—';
        }

        var folders = Array.isArray(row.project_folders) ? row.project_folders.filter(Boolean) : [];
        foldersEl.textContent = folders.length ? folders.join(', ') : textOrDash(row.project_folders);
        notesEl.textContent = textOrDash(row.notes);
        defaultMediaWorkId = primaryWorkId;
        defaultMediaTitle = seriesTitle;
        currentMediaWorkId = '';
        renderPrimaryMedia(primaryWorkId, seriesTitle).then(function () {
          currentMediaWorkId = primaryWorkId;
        }).catch(function (err) {
          console.error('series_tag_editor: failed to render primary media', err);
          if (mediaFigureEl) mediaFigureEl.hidden = true;
        });

        window.addEventListener('series-tag-editor:selected-work-change', function (event) {
          var detail = event && event.detail && typeof event.detail === 'object' ? event.detail : {};
          var detailSeriesId = String(detail.seriesId || '').trim().toLowerCase();
          if (detailSeriesId !== seriesIdQuery) return;
          syncHeaderMediaForWork(detail.workId);
        });

        mount.setAttribute('data-series-id', seriesIdQuery);
        root.hidden = false;
        emptyEl.hidden = true;
        import('{{ '/assets/studio/js/tag-studio.js' | relative_url }}').catch(function (err) {
          console.error('series_tag_editor: failed to load tag-studio.js', err);
          showError('Failed to load tag editor module.');
        });
      })
      .catch(function (err) {
        console.error('series_tag_editor: failed to load series index', err);
        showError('Failed to load series metadata.');
      });
  })();
</script>
