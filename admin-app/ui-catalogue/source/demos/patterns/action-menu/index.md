---
title: "UI Demo Pattern: Action Menu"
permalink: /admin/ui-catalogue/demos/patterns/action-menu/
studio_page_doc: /docs/?scope=studio&doc=ui-pattern-action-menu
ui_catalogue_demo_pattern: action-menu
---

<link rel="stylesheet" href="{{ '/admin/ui-catalogue/assets/css/ui-catalogue-demo.css' | relative_url }}">

{% capture action_menu_markup %}<div class="uiCatalogueDemoToolbar" aria-label="Example command toolbar">
  <div class="uiCatalogueDemoMenu" data-ui-demo-action-menu>
    <button
      class="uiCatalogueDemoButton uiCatalogueDemoMenu__trigger"
      type="button"
      aria-haspopup="menu"
      aria-expanded="false"
      data-ui-demo-menu-trigger
    >Actions</button>
    <div class="uiCatalogueDemoMenu__surface" role="menu" hidden data-ui-demo-menu-surface>
      <button class="uiCatalogueDemoMenu__item" type="button" role="menuitem" data-ui-demo-action="rebuild" data-ui-demo-action-message="Rebuild docs selected.">
        <span class="uiCatalogueDemoMenu__emoji" aria-hidden="true">🔁</span>
        <span class="uiCatalogueDemoMenu__label">Rebuild docs</span>
      </button>
      <button class="uiCatalogueDemoMenu__item" type="button" role="menuitem" data-ui-demo-action="settings" data-ui-demo-action-message="Settings selected.">
        <span class="uiCatalogueDemoMenu__emoji" aria-hidden="true"></span>
        <span class="uiCatalogueDemoMenu__label">Settings</span>
      </button>
      <button class="uiCatalogueDemoMenu__item" type="button" role="menuitem" data-ui-demo-action="import" data-ui-demo-action-message="Import selected.">
        <span class="uiCatalogueDemoMenu__emoji" aria-hidden="true">📥</span>
        <span class="uiCatalogueDemoMenu__label">Import</span>
      </button>
      <button class="uiCatalogueDemoMenu__item" type="button" role="menuitem" disabled title="Unavailable while a command is running">
        <span class="uiCatalogueDemoMenu__emoji" aria-hidden="true">🗑️</span>
        <span class="uiCatalogueDemoMenu__label">Delete scope</span>
      </button>
    </div>
  </div>
  <p class="uiCatalogueDemoStatus" aria-live="polite" data-ui-demo-action-status>Choose an action.</p>
</div>
{% endcapture %}

{% capture action_record_markup %}const actions = [
  {
    id: "rebuild-docs",
    emoji: "🔁",
    label: "Rebuild docs",
    disabled: state.busy,
    run: handlers.rebuildDocs
  },
  {
    id: "settings",
    emoji: "",
    label: "Settings",
    disabled: state.busy,
    run: handlers.openSettings
  }
];{% endcapture %}

<div
  class="uiCatalogueDemoRoot uiCatalogueDemoPage"
  id="uiCatalogueDemoActionMenuRoot"
  data-ui-catalogue-demo-route="ui-catalogue-demo-action-menu"
  data-ui-catalogue-demo-ready="false"
  data-ui-catalogue-demo-busy="false"
>
  <section class="uiCatalogueDemoSection" aria-labelledby="uiCatalogueDemoActionMenuIntroHeading">
    <div class="uiCatalogueDemoSection__header">
      <p class="uiCatalogueDemoEyebrow"><a href="{{ '/admin/ui-catalogue/demos/' | relative_url }}">&larr; UI catalogue demos</a></p>
      <p class="uiCatalogueDemoEyebrow"><a href="{{ '/docs/?scope=studio&doc=ui-pattern-action-menu' | relative_url }}">Docs viewer: Action Menu Pattern</a></p>
      <p class="uiCatalogueDemoEyebrow">Demo Composition Pattern</p>
      <h3 class="uiCatalogueDemoHeading" id="uiCatalogueDemoActionMenuIntroHeading">Action menu demo namespace</h3>
      <p class="uiCatalogueDemoIntro">This page demonstrates a compact command menu with design-time action records, optional emoji slots, disabled-state projection, and demo-owned dispatch.</p>
    </div>
  </section>

  <section class="uiCatalogueDemoSection" aria-labelledby="uiCatalogueDemoActionMenuLiveHeading">
    <div class="uiCatalogueDemoSection__header">
      <h3 class="uiCatalogueDemoHeading" id="uiCatalogueDemoActionMenuLiveHeading">Demo Composition</h3>
      <p class="uiCatalogueDemoSummary">Open the menu and choose an enabled command. The disabled row stays visible but cannot dispatch.</p>
    </div>
    <section class="uiCatalogueDemoExample uiCatalogueDemoExample--framed" aria-label="Action menu demo">
      {{ action_menu_markup }}
    </section>
  </section>

  <section class="uiCatalogueDemoSection" aria-labelledby="uiCatalogueDemoActionMenuCodeHeading">
    <div class="uiCatalogueDemoSection__header">
      <h3 class="uiCatalogueDemoHeading" id="uiCatalogueDemoActionMenuCodeHeading">Demo Markup</h3>
      <p class="uiCatalogueDemoSummary">Live routes should map this menu structure into their own namespace and keep executable action records code-owned.</p>
    </div>
    <div class="uiCatalogueDemoCode">
      <section class="uiCatalogueDemoCode__item">
        <h4 class="uiCatalogueDemoCode__title">Menu Shell</h4>
        <pre><code>{{ action_menu_markup | escape }}</code></pre>
      </section>
      <section class="uiCatalogueDemoCode__item">
        <h4 class="uiCatalogueDemoCode__title">Design-Time Action Records</h4>
        <pre><code>{{ action_record_markup | escape }}</code></pre>
      </section>
    </div>
  </section>
</div>

<script type="module" src="{{ '/admin/ui-catalogue/assets/js/ui-catalogue-demo.js' | relative_url }}?v={{ site.time | date: '%s' }}"></script>
