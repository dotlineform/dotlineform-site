  (function () {
    var root = document.getElementById('selectedWorkRoot');
    var runtime = window.__dlfPublicCatalogueRuntime;
    if (!root || !runtime) return;

    var routeState = runtime.parseRouteState(window.location);
    var workId = String(routeState.work || '').trim();
    if (!workId) return;

    var baseurl = runtime.trimBaseurl(root.getAttribute('data-baseurl'));
    var worksImgBase = String(root.getAttribute('data-works-img-base') || '').trim();
    var worksFilesBase = String(root.getAttribute('data-works-files-base') || '').trim();
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

    function isAbsoluteUrl(value) {
      return /^(https?:)?\/\//i.test(value);
    }

    function safeHref(value) {
      var href = runtime.text(value);
      if (!href) return '';
      if (/^(https?:|mailto:)/i.test(href)) return href;
      if (href.charAt(0) === '/' || href.charAt(0) === '#') return href;
      return '';
    }

    function encodedPath(value) {
      return runtime.text(value).split('/').map(function (part) {
        return encodeURIComponent(part);
      }).join('/');
    }

    function workFileUrl(filename) {
      var name = runtime.text(filename);
      if (!name) return '';
      if (isAbsoluteUrl(name)) return name;
      if (name.charAt(0) === '/') return name;
      return worksFilesBase.replace(/\/$/, '') + '/' + encodedPath(name);
    }

    function arrayFromPayload(payload, work, key) {
      if (work && Array.isArray(work[key])) return work[key];
      if (payload && Array.isArray(payload[key])) return payload[key];
      return [];
    }

    function renderMetaLinks(rowId, labelId, linksId, singular, plural, entries, hrefForEntry) {
      var row = document.getElementById(rowId);
      var label = document.getElementById(labelId);
      var links = document.getElementById(linksId);
      if (!row || !label || !links) return;
      var items = (Array.isArray(entries) ? entries : []).map(function (entry) {
        var href = hrefForEntry(entry);
        var text = runtime.text(entry && entry.label) || runtime.text(entry && entry.filename) || runtime.text(entry && entry.url);
        if (!href || !text) return '';
        return '<a href="' + esc(href) + '" target="_blank" rel="noopener">' + esc(text) + '</a>';
      }).filter(Boolean);
      label.textContent = items.length === 1 ? singular : plural;
      links.innerHTML = items.join(', ');
      row.hidden = !items.length;
    }

    function renderDownloadsAndLinks(payload, work) {
      renderMetaLinks(
        'selectedWorkDownloadsRow',
        'selectedWorkDownloadsLabel',
        'selectedWorkDownloadsLinks',
        'download',
        'downloads',
        arrayFromPayload(payload, work, 'downloads'),
        function (entry) { return workFileUrl(entry && entry.filename); }
      );
      renderMetaLinks(
        'selectedWorkLinksRow',
        'selectedWorkLinksLabel',
        'selectedWorkLinksLinks',
        'link',
        'links',
        arrayFromPayload(payload, work, 'links'),
        function (entry) { return safeHref(entry && entry.url); }
      );
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
        renderDownloadsAndLinks(payload, work);
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
