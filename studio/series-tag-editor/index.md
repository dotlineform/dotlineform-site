---
layout: default
title: Series Tag Editor
permalink: /studio/series-tag-editor/
section: works
---

<link rel="stylesheet" href="{{ '/assets/css/studio.css' | relative_url }}">

<article class="page tagStudioPage" id="seriesTagEditorRoot" hidden>
  <header class="tagStudioPage__header">
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
    var baseurl = {{ site.baseurl | default: '' | jsonify }};
    var params = new URLSearchParams(window.location.search);
    var seriesIdQuery = String(params.get('series') || '').trim().toLowerCase();
    var seriesIndexUrl = baseurl + '/assets/data/series_index.json';

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

        mount.setAttribute('data-series-id', seriesIdQuery);
        root.hidden = false;
        emptyEl.hidden = true;
        import('{{ '/assets/js/tag-studio.js' | relative_url }}').catch(function (err) {
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
