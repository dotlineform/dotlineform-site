---
layout: default
title: "Work Detail"
permalink: /work-details/
section: works
---

{% assign public_text = site.public_runtime_text | default: nil %}
{% assign loading_text = public_text.loading | default: "loading..." %}
{% assign unavailable_text = public_text.unavailable | default: "info not available" %}
{% assign media_base = site.media_base | default: "" %}
{% assign media_image_work_details = site.media_image_work_details | default: "/work_details/img" %}
{% assign pipeline = site.data.pipeline %}
{% assign primary_variants = pipeline.variants.primary %}
{% assign compatibility_variants = pipeline.variants.compatibility %}
{% assign primary_render_widths = compatibility_variants.render_widths | default: primary_variants.widths %}
{% assign primary_display_width = primary_render_widths | last %}
{% assign primary_full_width = primary_variants.preferred_width | default: primary_display_width %}
{% assign primary_suffix = primary_variants.suffix | default: "primary" %}
{% assign asset_format = pipeline.encoding.format | default: "webp" %}
{% assign img_base = media_base | append: media_image_work_details | append: "/" %}
{% assign img_base_out = img_base %}
{% unless img_base contains '://' %}
  {% assign img_base_out = img_base | relative_url %}
{% endunless %}

<article
  class="page work"
  id="detailPageRoot"
  data-baseurl="{{ site.baseurl | default: '' }}"
  data-img-base="{{ img_base_out | escape }}"
  data-primary-render-widths="{{ primary_render_widths | jsonify | escape }}"
  data-primary-display-width="{{ primary_display_width | escape }}"
  data-primary-full-width="{{ primary_full_width | escape }}"
  data-primary-suffix="{{ primary_suffix | escape }}"
  data-asset-format="{{ asset_format | escape }}"
  data-loading-text="{{ loading_text | escape }}"
  data-unavailable-text="{{ unavailable_text | escape }}"
  hidden
>
  <h1 class="visually-hidden" id="detailHiddenTitle">{{ loading_text }}</h1>

  <figure class="page__media">
    <a class="page__mediaLink" id="detailMediaLink" data-swipe-nav-zone="detail-media" target="_blank" rel="noopener" style="--work-ar: 4 / 3;">
      <img class="page__mediaImg" id="detailPrimaryImg" sizes="(max-width: 800px) 100vw, 72ch" alt="" loading="eager" fetchpriority="high" decoding="async" style="width:100%;height:auto;display:block;">
    </a>
  </figure>

  <section class="page__meta page__media">
    <h2 class="visually-hidden">work detail metadata</h2>
    <div class="page__caption page__metaList">
      <div class="page__row work__titleRow">
        <span class="work__titleMain"><span id="detailTitleText">{{ loading_text }}</span></span>
        <nav class="seriesNav seriesNav--title" id="detailNav" aria-label="Detail navigation" data-detail-uid="" data-work-id="" data-work-title="" data-baseurl="{{ site.baseurl | default: '' }}" data-default-section="" hidden>
          <span class="navCounter" id="detailTitleCounter" hidden></span>
          <a class="seriesNav__prev" id="detailNavPrev" href="#">←</a>
          <a class="seriesNav__next" id="detailNavNext" href="#">→</a>
        </nav>
      </div>
      <div class="page__row">cat. <span id="detailCatText"></span></div>
    </div>
  </section>

  <nav class="page__nav">
    <a id="detailBackLink" class="page__back" href="{{ '/series/' | relative_url }}">← work</a>
  </nav>
</article>

<p id="detailPageEmpty" hidden>{{ unavailable_text }}</p>

<script src="{{ '/assets/js/swipe-nav.js' | relative_url }}?v={{ site.time | date: '%s' }}"></script>
<script src="{{ '/assets/js/public-catalogue-runtime.js' | relative_url }}?v={{ site.time | date: '%s' }}"></script>
<script>
  (function () {
    var root = document.getElementById('detailPageRoot');
    var empty = document.getElementById('detailPageEmpty');
    var runtime = window.__dlfPublicCatalogueRuntime;
    if (!root || !runtime) return;

    var routeState = runtime.parseRouteState(window.location);
    var detailUid = String(routeState.detail || '').trim();
    var unavailableText = String(root.getAttribute('data-unavailable-text') || 'info not available');
    if (!detailUid) {
      if (empty) {
        empty.hidden = false;
        empty.textContent = unavailableText;
      }
      return;
    }

    var params = new URLSearchParams(window.location.search);
    var baseurl = runtime.trimBaseurl(root.getAttribute('data-baseurl'));
    var imgBase = String(root.getAttribute('data-img-base') || '').trim();
    var primaryDisplayWidth = runtime.toPositiveInteger(root.getAttribute('data-primary-display-width')) || 1200;
    var primaryFullWidth = runtime.toPositiveInteger(root.getAttribute('data-primary-full-width')) || primaryDisplayWidth;
    var primarySuffix = runtime.text(root.getAttribute('data-primary-suffix')) || 'primary';
    var assetFormat = runtime.text(root.getAttribute('data-asset-format')) || 'webp';
    var renderWidths = [];
    try {
      renderWidths = JSON.parse(root.getAttribute('data-primary-render-widths') || '[]');
    } catch (err) {
      renderWidths = [];
    }
    renderWidths = runtime.normalizePositiveSizes(renderWidths, [primaryDisplayWidth]);

    var ctx = {
      detailUid: detailUid,
      fromWork: String(params.get('from_work') || (detailUid.indexOf('-') !== -1 ? detailUid.split('-', 1)[0] : '') || '').trim(),
      fromWorkTitle: String(params.get('from_work_title') || '').trim(),
      section: String(params.get('section') || '').trim().toLowerCase(),
      detailsSection: String(params.get('details_section') || '').trim().toLowerCase(),
      detailsPage: runtime.toPositiveInteger(params.get('details_page')) || 1,
      series: String(params.get('series') || '').trim(),
      seriesPage: runtime.toPositiveInteger(params.get('series_page')),
      title: detailUid,
      widthPx: 0,
      heightPx: 0
    };
    if (!ctx.detailsSection) ctx.detailsSection = ctx.section;
    if (!ctx.fromWorkTitle) ctx.fromWorkTitle = ctx.fromWork;

    function imageUrl(uid, width) {
      return imgBase + encodeURIComponent(uid) + '-' + primarySuffix + '-' + String(width) + '.' + assetFormat;
    }

    function updateTitle() {
      var hiddenTitle = document.getElementById('detailHiddenTitle');
      var titleText = document.getElementById('detailTitleText');
      var catText = document.getElementById('detailCatText');
      if (hiddenTitle) hiddenTitle.textContent = ctx.title || 'Untitled';
      if (titleText) titleText.textContent = ctx.title || 'Untitled';
      if (catText) catText.textContent = ctx.detailUid;
      if (ctx.title) document.title = ctx.title + ' | dotlineform';
    }

    function updateMedia() {
      var mediaLink = document.getElementById('detailMediaLink');
      var img = document.getElementById('detailPrimaryImg');
      if (!mediaLink || !img) return;
      if (ctx.widthPx > 0 && ctx.heightPx > 0) {
        mediaLink.style.setProperty('--work-ar', String(ctx.widthPx) + ' / ' + String(ctx.heightPx));
      }
      mediaLink.setAttribute('href', imageUrl(ctx.detailUid, primaryFullWidth));
      img.setAttribute('src', imageUrl(ctx.detailUid, primaryDisplayWidth));
      img.setAttribute('srcset', renderWidths.map(function (width) {
        return imageUrl(ctx.detailUid, width) + ' ' + String(width) + 'w';
      }).join(', '));
      img.setAttribute('alt', ctx.title || ctx.detailUid);
    }

    function updateBackLink() {
      var link = document.getElementById('detailBackLink');
      if (!link) return;
      if (!ctx.fromWork) {
        link.textContent = '← works';
        link.setAttribute('href', runtime.catalogueIndexUrl(baseurl));
        return;
      }
      var href = runtime.workUrl(ctx.fromWork, baseurl, {
        series: ctx.series,
        series_page: ctx.seriesPage,
        details_section: ctx.detailsSection,
        details_page: ctx.detailsPage
      });
      if (ctx.section) href += '#details-' + encodeURIComponent(ctx.section);
      link.textContent = '← ' + (ctx.fromWorkTitle || ctx.fromWork);
      link.setAttribute('href', href);
    }

    function detailHref(uid) {
      return runtime.workDetailUrl(uid, baseurl, {
        from_work: ctx.fromWork,
        from_work_title: ctx.fromWorkTitle,
        section: ctx.section,
        series: ctx.series,
        series_page: ctx.seriesPage,
        details_section: ctx.detailsSection,
        details_page: ctx.detailsPage
      });
    }

    function findDetailRecord(workPayload) {
      var sections = workPayload && Array.isArray(workPayload.sections) ? workPayload.sections : [];
      for (var i = 0; i < sections.length; i += 1) {
        var sec = sections[i] || {};
        var details = Array.isArray(sec.details) ? sec.details : [];
        for (var j = 0; j < details.length; j += 1) {
          var detail = details[j] || {};
          if (runtime.text(detail.detail_uid) === ctx.detailUid) {
            return {
              detail: detail,
              section_id: runtime.slug(sec.section_id || sec.section_title || sec.project_subfolder || 'details')
            };
          }
        }
      }
      return { detail: null, section_id: '' };
    }

    function setNavigation(workPayload) {
      var nav = document.getElementById('detailNav');
      var prevA = document.getElementById('detailNavPrev');
      var nextA = document.getElementById('detailNavNext');
      var counter = document.getElementById('detailTitleCounter');
      if (!nav || !prevA || !nextA) return;
      var sections = workPayload && Array.isArray(workPayload.sections) ? workPayload.sections : [];
      var details = [];
      sections.forEach(function (sec) {
        var sectionId = runtime.slug(sec && (sec.section_id || sec.section_title || sec.project_subfolder || 'details'));
        if (ctx.section && sectionId !== ctx.section) return;
        var list = sec && Array.isArray(sec.details) ? sec.details : [];
        list.forEach(function (detail) { details.push(detail); });
      });
      if (!details.length && ctx.section) {
        sections.forEach(function (sec) {
          var list = sec && Array.isArray(sec.details) ? sec.details : [];
          list.forEach(function (detail) { details.push(detail); });
        });
      }
      var ids = details.map(function (detail) { return runtime.text(detail && detail.detail_uid); }).filter(Boolean);
      var index = ids.indexOf(ctx.detailUid);
      if (ids.length < 2 || index < 0) {
        nav.hidden = true;
        if (counter) counter.hidden = true;
        return;
      }
      prevA.href = detailHref(ids[(index - 1 + ids.length) % ids.length]);
      nextA.href = detailHref(ids[(index + 1) % ids.length]);
      if (counter) {
        counter.textContent = String(index + 1) + '/' + String(ids.length);
        counter.hidden = false;
      }
      nav.hidden = false;
    }

    updateTitle();
    updateMedia();
    updateBackLink();
    root.hidden = false;

    runtime.fetchJson(runtime.workPayloadUrl(ctx.fromWork, baseurl))
      .then(function (workPayload) {
        var work = workPayload && workPayload.work && typeof workPayload.work === 'object' ? workPayload.work : null;
        var workTitle = runtime.text(work && work.title);
        if (workTitle && (!params.get('from_work_title') || !ctx.fromWorkTitle)) ctx.fromWorkTitle = workTitle;
        var found = findDetailRecord(workPayload);
        if (found.detail) {
          ctx.title = runtime.text(found.detail.title) || ctx.detailUid;
          ctx.widthPx = runtime.toNumber(found.detail.width_px) || 0;
          ctx.heightPx = runtime.toNumber(found.detail.height_px) || 0;
          if (!ctx.section && found.section_id) ctx.section = found.section_id;
          if (!ctx.detailsSection && found.section_id) ctx.detailsSection = found.section_id;
        }
        updateTitle();
        updateMedia();
        updateBackLink();
        setNavigation(workPayload);
      })
      .catch(function () {
        ctx.title = unavailableText;
        updateTitle();
        updateBackLink();
      });
  })();
</script>
<script src="{{ '/assets/js/work.js' | relative_url }}?v={{ site.time | date: '%s' }}"></script>
