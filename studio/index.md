---
layout: studio
title: "Studio"
permalink: /studio/
studio_page_doc: /docs/?scope=studio&doc=new-pipeline-studio-implementation-plan
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

{% assign studio_home_panel_images = site.data.studio_panel_images.studio_home %}
{% assign studio_home_panel_image_base = studio_home_panel_images.base_path %}
{% assign studio_home_panel_image_format = studio_home_panel_images.format %}
{% assign studio_home_panel_image_default_width = studio_home_panel_images.default_width %}
{% assign studio_home_catalogue_panel_image = studio_home_panel_images.panels.catalogue %}
{% assign studio_home_library_panel_image = studio_home_panel_images.panels.library %}
{% assign studio_home_analytics_panel_image = studio_home_panel_images.panels.analytics %}
{% assign studio_home_search_panel_image = studio_home_panel_images.panels.search %}
{% capture studio_home_catalogue_panel_image_url %}{{ studio_home_panel_image_base }}/{{ studio_home_catalogue_panel_image.asset_id }}-{{ studio_home_catalogue_panel_image.variant }}-{{ studio_home_catalogue_panel_image.width | default: studio_home_panel_image_default_width }}.{{ studio_home_panel_image_format }}{% endcapture %}
{% capture studio_home_library_panel_image_url %}{{ studio_home_panel_image_base }}/{{ studio_home_library_panel_image.asset_id }}-{{ studio_home_library_panel_image.variant }}-{{ studio_home_library_panel_image.width | default: studio_home_panel_image_default_width }}.{{ studio_home_panel_image_format }}{% endcapture %}
{% capture studio_home_analytics_panel_image_url %}{{ studio_home_panel_image_base }}/{{ studio_home_analytics_panel_image.asset_id }}-{{ studio_home_analytics_panel_image.variant }}-{{ studio_home_analytics_panel_image.width | default: studio_home_panel_image_default_width }}.{{ studio_home_panel_image_format }}{% endcapture %}
{% capture studio_home_search_panel_image_url %}{{ studio_home_panel_image_base }}/{{ studio_home_search_panel_image.asset_id }}-{{ studio_home_search_panel_image.variant }}-{{ studio_home_search_panel_image.width | default: studio_home_panel_image_default_width }}.{{ studio_home_panel_image_format }}{% endcapture %}

<section class="studioHome" aria-label="Studio domains">
  <a class="tagStudio__panel tagStudio__panelLink tagStudio__panelLink--image" href="{{ '/studio/catalogue/' | relative_url }}" style="--panel-image: url('{{ studio_home_catalogue_panel_image_url | strip | relative_url }}');">
    <h3>Catalogue</h3>
    <p>Publish and maintain the works portfolio.</p>
  </a>
  <a class="tagStudio__panel tagStudio__panelLink tagStudio__panelLink--image" href="{{ '/studio/library/' | relative_url }}" style="--panel-image: url('{{ studio_home_library_panel_image_url | strip | relative_url }}');">
    <h3>Library</h3>
    <p>Publish reference and research documents.</p>
  </a>
  <a class="tagStudio__panel tagStudio__panelLink tagStudio__panelLink--image" href="{{ '/studio/analytics/' | relative_url }}" style="--panel-image: url('{{ studio_home_analytics_panel_image_url | strip | relative_url }}');">
    <h3>Analytics</h3>
    <p>Tools to support the analysis and contextualisation of the portfolio.</p>
  </a>
  <a class="tagStudio__panel tagStudio__panelLink tagStudio__panelLink--image" href="{{ '/studio/search/' | relative_url }}" style="--panel-image: url('{{ studio_home_search_panel_image_url | strip | relative_url }}');">
    <h3>Search</h3>
    <p>Configure and manage site search.</p>
  </a>
</section>

<section aria-labelledby="studioResourcesHeading">
  <h3 id="studioResourcesHeading">Resources</h3>
  <p><a href="{{ '/studio/ui-catalogue/' | relative_url }}">UI Catalogue</a></p>
</section>
