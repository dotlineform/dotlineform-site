---
title: "UI Demo Pattern: Select Menu"
permalink: /admin/ui-catalogue/demos/patterns/select-menu/
studio_page_doc: /docs/?scope=studio&doc=ui-pattern-select-menu
ui_catalogue_demo_pattern: select-menu
---

<link rel="stylesheet" href="{{ '/admin/ui-catalogue/assets/css/ui-catalogue-demo.css' | relative_url }}">

{% capture native_select_markup %}<label class="uiCatalogueDemoSelectField">
  <span class="uiCatalogueDemoField__label">scope</span>
  <select class="uiCatalogueDemoSelect" data-ui-demo-native-select>
    <option value="studio">🛠️ Studio</option>
    <option value="library">🌐 Library</option>
    <option value="analysis">📊 Analysis</option>
    <option value="local">💻 Local drafts</option>
  </select>
</label>
{% endcapture %}

{% capture custom_select_markup %}<div class="uiCatalogueDemoSelectMenu" data-ui-demo-select-menu data-ui-demo-select-value="studio">
  <button
    class="uiCatalogueDemoButton uiCatalogueDemoSelectMenu__trigger"
    type="button"
    aria-haspopup="listbox"
    aria-expanded="false"
    data-ui-demo-select-trigger
  >
    <span class="uiCatalogueDemoMenu__emoji" aria-hidden="true">🛠️</span>
    <span data-ui-demo-select-label>Studio</span>
  </button>
  <div class="uiCatalogueDemoMenu__surface" role="listbox" hidden data-ui-demo-select-list>
    <button class="uiCatalogueDemoMenu__item" type="button" role="option" aria-selected="true" data-ui-demo-select-option data-value="studio" data-label="Studio" data-emoji="🛠️">
      <span class="uiCatalogueDemoMenu__emoji" aria-hidden="true">🛠️</span>
      <span class="uiCatalogueDemoMenu__label">Studio</span>
      <span class="uiCatalogueDemoMenu__meta">local management</span>
    </button>
    <button class="uiCatalogueDemoMenu__item" type="button" role="option" aria-selected="false" data-ui-demo-select-option data-value="library" data-label="Library" data-emoji="🌐">
      <span class="uiCatalogueDemoMenu__emoji" aria-hidden="true">🌐</span>
      <span class="uiCatalogueDemoMenu__label">Library</span>
      <span class="uiCatalogueDemoMenu__meta">public scope</span>
    </button>
    <button class="uiCatalogueDemoMenu__item" type="button" role="option" aria-selected="false" data-ui-demo-select-option data-value="analysis" data-label="Analysis" data-emoji="📊">
      <span class="uiCatalogueDemoMenu__emoji" aria-hidden="true">📊</span>
      <span class="uiCatalogueDemoMenu__label">Analysis</span>
      <span class="uiCatalogueDemoMenu__meta">public scope</span>
    </button>
    <button class="uiCatalogueDemoMenu__item" type="button" role="option" aria-selected="false" disabled data-ui-demo-select-option data-value="archive" data-label="Archive" data-emoji="">
      <span class="uiCatalogueDemoMenu__emoji" aria-hidden="true"></span>
      <span class="uiCatalogueDemoMenu__label">Archive</span>
      <span class="uiCatalogueDemoMenu__meta">not available</span>
    </button>
  </div>
</div>
{% endcapture %}

{% capture option_record_markup %}const options = [
  {
    value: "studio",
    emoji: "🛠️",
    label: "Studio",
    meta: "local management"
  },
  {
    value: "library",
    emoji: "🌐",
    label: "Library",
    meta: "public scope"
  }
];{% endcapture %}

<div
  class="uiCatalogueDemoRoot uiCatalogueDemoPage"
  id="uiCatalogueDemoSelectMenuRoot"
  data-ui-catalogue-demo-route="ui-catalogue-demo-select-menu"
  data-ui-catalogue-demo-ready="false"
  data-ui-catalogue-demo-busy="false"
>
  <section class="uiCatalogueDemoSection" aria-labelledby="uiCatalogueDemoSelectMenuIntroHeading">
    <div class="uiCatalogueDemoSection__header">
      <p class="uiCatalogueDemoEyebrow"><a href="{{ '/admin/ui-catalogue/demos/' | relative_url }}">&larr; UI catalogue demos</a></p>
      <p class="uiCatalogueDemoEyebrow"><a href="{{ '/docs/?scope=studio&doc=ui-pattern-select-menu' | relative_url }}">Docs viewer: Select Menu Pattern</a></p>
      <p class="uiCatalogueDemoEyebrow">Demo Composition Pattern</p>
      <h3 class="uiCatalogueDemoHeading" id="uiCatalogueDemoSelectMenuIntroHeading">Select menu demo namespace</h3>
      <p class="uiCatalogueDemoIntro">This page demonstrates user-config-shaped option records, emoji scope markers, native-select behavior, and a custom compact menu variant.</p>
    </div>
  </section>

  <section class="uiCatalogueDemoSection" aria-labelledby="uiCatalogueDemoSelectMenuLiveHeading">
    <div class="uiCatalogueDemoSection__header">
      <h3 class="uiCatalogueDemoHeading" id="uiCatalogueDemoSelectMenuLiveHeading">Demo Composition</h3>
      <p class="uiCatalogueDemoSummary">Use the native select by default. Use the custom menu only where the route needs richer rows or stronger toolbar alignment.</p>
    </div>
    <div class="uiCatalogueDemoGrid uiCatalogueDemoGrid--cards">
      <section class="uiCatalogueDemoExample uiCatalogueDemoExample--framed">
        <header class="uiCatalogueDemoExample__header">
          <h3 class="uiCatalogueDemoExample__title">Native Select</h3>
          <p class="uiCatalogueDemoExample__summary">Config-backed options remain native when basic labels are enough.</p>
        </header>
        {{ native_select_markup }}
        <p class="uiCatalogueDemoStatus" aria-live="polite" data-ui-demo-native-select-status>Studio selected.</p>
      </section>
      <section class="uiCatalogueDemoExample uiCatalogueDemoExample--framed">
        <header class="uiCatalogueDemoExample__header">
          <h3 class="uiCatalogueDemoExample__title">Custom Select Menu</h3>
          <p class="uiCatalogueDemoExample__summary">The custom variant keeps emoji and labels aligned across richer option rows.</p>
        </header>
        {{ custom_select_markup }}
        <p class="uiCatalogueDemoStatus" aria-live="polite" data-ui-demo-select-status>Studio selected.</p>
      </section>
    </div>
  </section>

  <section class="uiCatalogueDemoSection" aria-labelledby="uiCatalogueDemoSelectMenuCodeHeading">
    <div class="uiCatalogueDemoSection__header">
      <h3 class="uiCatalogueDemoHeading" id="uiCatalogueDemoSelectMenuCodeHeading">Demo Markup</h3>
      <p class="uiCatalogueDemoSummary">Live routes should map option records into either native select markup or a custom menu only when required.</p>
    </div>
    <div class="uiCatalogueDemoCode">
      <section class="uiCatalogueDemoCode__item">
        <h4 class="uiCatalogueDemoCode__title">Native Select</h4>
        <pre><code>{{ native_select_markup | escape }}</code></pre>
      </section>
      <section class="uiCatalogueDemoCode__item">
        <h4 class="uiCatalogueDemoCode__title">Custom Select Menu</h4>
        <pre><code>{{ custom_select_markup | escape }}</code></pre>
      </section>
      <section class="uiCatalogueDemoCode__item">
        <h4 class="uiCatalogueDemoCode__title">User-Config-Shaped Option Records</h4>
        <pre><code>{{ option_record_markup | escape }}</code></pre>
      </section>
    </div>
  </section>
</div>

<script type="module" src="{{ '/admin/ui-catalogue/assets/js/ui-catalogue-demo.js' | relative_url }}?v={{ site.time | date: '%s' }}"></script>
