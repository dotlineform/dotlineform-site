---
title: "UI Demo Primitive: Modal Shell"
permalink: /ui-catalogue/demos/primitives/modal-shell/
studio_page_doc: /docs/?scope=studio&doc=ui-primitive-modal-shell
ui_catalogue_demo_primitive: modal-shell
---

<link rel="stylesheet" href="{{ '/ui-catalogue/app/assets/css/ui-catalogue-demo.css' | relative_url }}">

{% capture shell_markup %}<div class="uiCatalogueDemoModal" id="exampleModal" data-ui-demo-modal data-open="false" aria-hidden="true" hidden>
  <div class="uiCatalogueDemoModal__backdrop" data-ui-demo-modal-close></div>
  <div class="uiCatalogueDemoModal__dialog" role="dialog" aria-modal="true" aria-labelledby="exampleModalTitle" tabindex="-1">
    <header class="uiCatalogueDemoModal__header">
      <div class="uiCatalogueDemoModal__headerCopy">
        <h3 class="uiCatalogueDemoModal__title" id="exampleModalTitle">Modal title</h3>
        <p class="uiCatalogueDemoModal__meta">Optional modal context</p>
      </div>
    </header>
    <div class="uiCatalogueDemoModal__body">
      <p class="uiCatalogueDemoModal__text">Modal body content belongs to the route or command.</p>
    </div>
    <p class="uiCatalogueDemoModal__status" data-ui-demo-modal-status hidden></p>
    <div class="uiCatalogueDemoModal__actions">
      <button class="uiCatalogueDemoButton uiCatalogueDemoButton--fixed" type="button" data-ui-demo-modal-close>Cancel</button>
      <button class="uiCatalogueDemoButton uiCatalogueDemoButton--fixed uiCatalogueDemoButton--primary" type="button" data-ui-demo-modal-submit data-ui-demo-modal-initial-focus>OK</button>
    </div>
  </div>
</div>
{% endcapture %}

{% capture input_markup %}<label class="uiCatalogueDemoField uiCatalogueDemoField--fill" for="exampleModalInput">
  <span class="uiCatalogueDemoField__label">Title</span>
  <span class="uiCatalogueDemoField__control">
    <input class="uiCatalogueDemoInput" id="exampleModalInput" type="text" data-ui-demo-modal-required-input>
  </span>
</label>
{% endcapture %}

<div
  class="uiCatalogueDemoRoot uiCatalogueDemoPage"
  id="uiCatalogueDemoModalShellRoot"
  data-ui-catalogue-demo-route="ui-catalogue-demo-modal-shell"
  data-ui-catalogue-demo-ready="false"
  data-ui-catalogue-demo-busy="false"
>
  <section class="uiCatalogueDemoSection" aria-labelledby="uiCatalogueDemoModalShellIntroHeading">
    <div class="uiCatalogueDemoSection__header">
      <p class="uiCatalogueDemoEyebrow"><a href="{{ '/ui-catalogue/demos/' | relative_url }}">&larr; UI catalogue demos</a></p>
      <p class="uiCatalogueDemoEyebrow"><a href="{{ '/docs/?scope=studio&doc=ui-primitive-modal-shell' | relative_url }}">Docs viewer: Modal Shell Primitive</a></p>
      <p class="uiCatalogueDemoEyebrow">Demo Primitive</p>
      <h3 class="uiCatalogueDemoHeading" id="uiCatalogueDemoModalShellIntroHeading">Modal shell demo namespace</h3>
      <p class="uiCatalogueDemoIntro">This page demonstrates the shared modal shell contract with demo-only classes and demo-owned JavaScript.</p>
    </div>
  </section>

  <section class="uiCatalogueDemoSection" aria-labelledby="uiCatalogueDemoModalShellLiveHeading">
    <div class="uiCatalogueDemoSection__header">
      <h3 class="uiCatalogueDemoHeading" id="uiCatalogueDemoModalShellLiveHeading">Demo Variants</h3>
      <p class="uiCatalogueDemoSummary">Each example uses the same shell anatomy: backdrop, dialog, header, body, status slot, and action row.</p>
    </div>

    <div class="uiCatalogueDemoGrid uiCatalogueDemoGrid--cards">
      <section class="uiCatalogueDemoExample uiCatalogueDemoExample--framed">
        <header class="uiCatalogueDemoExample__header">
          <h3 class="uiCatalogueDemoExample__title">Notice Result</h3>
          <p class="uiCatalogueDemoExample__summary">A completed command returns readable details and a close action.</p>
        </header>
        <button class="uiCatalogueDemoButton uiCatalogueDemoButton--fixed" type="button" data-ui-demo-modal-open="uiCatalogueDemoNoticeModal">Open</button>
      </section>

      <section class="uiCatalogueDemoExample uiCatalogueDemoExample--framed">
        <header class="uiCatalogueDemoExample__header">
          <h3 class="uiCatalogueDemoExample__title">Confirmation</h3>
          <p class="uiCatalogueDemoExample__summary">The opener keeps ownership of the destructive action.</p>
        </header>
        <button class="uiCatalogueDemoButton uiCatalogueDemoButton--fixed" type="button" data-ui-demo-modal-open="uiCatalogueDemoConfirmModal">Open</button>
      </section>

      <section class="uiCatalogueDemoExample uiCatalogueDemoExample--framed">
        <header class="uiCatalogueDemoExample__header">
          <h3 class="uiCatalogueDemoExample__title">Short Input</h3>
          <p class="uiCatalogueDemoExample__summary">Local completeness validation stays inside the modal.</p>
        </header>
        <button class="uiCatalogueDemoButton uiCatalogueDemoButton--fixed" type="button" data-ui-demo-modal-open="uiCatalogueDemoInputModal">Open</button>
      </section>

      <section class="uiCatalogueDemoExample uiCatalogueDemoExample--framed">
        <header class="uiCatalogueDemoExample__header">
          <h3 class="uiCatalogueDemoExample__title">Workflow</h3>
          <p class="uiCatalogueDemoExample__summary">A route-owned modal can contain several controls while keeping the same shell.</p>
        </header>
        <button class="uiCatalogueDemoButton uiCatalogueDemoButton--fixed" type="button" data-ui-demo-modal-open="uiCatalogueDemoWorkflowModal">Open</button>
      </section>
    </div>
  </section>

  <div class="uiCatalogueDemoModal" id="uiCatalogueDemoNoticeModal" data-ui-demo-modal data-open="false" aria-hidden="true" hidden>
    <div class="uiCatalogueDemoModal__backdrop" data-ui-demo-modal-close></div>
    <div class="uiCatalogueDemoModal__dialog uiCatalogueDemoModal__dialog--compact" role="dialog" aria-modal="true" aria-labelledby="uiCatalogueDemoNoticeModalTitle" tabindex="-1">
      <header class="uiCatalogueDemoModal__header">
        <div class="uiCatalogueDemoModal__headerCopy">
          <h3 class="uiCatalogueDemoModal__title" id="uiCatalogueDemoNoticeModalTitle">Prepare complete</h3>
          <p class="uiCatalogueDemoModal__meta">Library package</p>
        </div>
      </header>
      <div class="uiCatalogueDemoModal__body">
        <p class="uiCatalogueDemoModal__text">Generated a returned-package preview with three document updates.</p>
        <dl class="uiCatalogueDemoList uiCatalogueDemoList--simple">
          <div class="uiCatalogueDemoList__row">
            <dt class="uiCatalogueDemoList__meta">records</dt>
            <dd>3</dd>
          </div>
          <div class="uiCatalogueDemoList__row">
            <dt class="uiCatalogueDemoList__meta">warnings</dt>
            <dd>0</dd>
          </div>
        </dl>
      </div>
      <p class="uiCatalogueDemoModal__status" data-ui-demo-modal-status hidden></p>
      <div class="uiCatalogueDemoModal__actions">
        <button class="uiCatalogueDemoButton uiCatalogueDemoButton--fixed uiCatalogueDemoButton--primary" type="button" data-ui-demo-modal-close data-ui-demo-modal-initial-focus>Close</button>
      </div>
    </div>
  </div>

  <div class="uiCatalogueDemoModal" id="uiCatalogueDemoConfirmModal" data-ui-demo-modal data-open="false" aria-hidden="true" hidden>
    <div class="uiCatalogueDemoModal__backdrop" data-ui-demo-modal-close></div>
    <div class="uiCatalogueDemoModal__dialog uiCatalogueDemoModal__dialog--compact" role="dialog" aria-modal="true" aria-labelledby="uiCatalogueDemoConfirmModalTitle" tabindex="-1">
      <header class="uiCatalogueDemoModal__header">
        <div class="uiCatalogueDemoModal__headerCopy">
          <h3 class="uiCatalogueDemoModal__title" id="uiCatalogueDemoConfirmModalTitle">Delete alias</h3>
          <p class="uiCatalogueDemoModal__meta">analytics tag aliases</p>
        </div>
      </header>
      <div class="uiCatalogueDemoModal__body">
        <p class="uiCatalogueDemoModal__text">Delete the selected alias? The page command owns the write after confirmation.</p>
      </div>
      <p class="uiCatalogueDemoModal__status" data-ui-demo-modal-status hidden></p>
      <div class="uiCatalogueDemoModal__actions">
        <button class="uiCatalogueDemoButton uiCatalogueDemoButton--fixed" type="button" data-ui-demo-modal-close>Cancel</button>
        <button class="uiCatalogueDemoButton uiCatalogueDemoButton--fixed uiCatalogueDemoButton--primary" type="button" data-ui-demo-modal-submit data-ui-demo-modal-initial-focus>Delete</button>
      </div>
    </div>
  </div>

  <div class="uiCatalogueDemoModal" id="uiCatalogueDemoInputModal" data-ui-demo-modal data-open="false" aria-hidden="true" hidden data-ui-demo-modal-required-message="Enter a title before continuing.">
    <div class="uiCatalogueDemoModal__backdrop" data-ui-demo-modal-close></div>
    <div class="uiCatalogueDemoModal__dialog uiCatalogueDemoModal__dialog--compact" role="dialog" aria-modal="true" aria-labelledby="uiCatalogueDemoInputModalTitle" tabindex="-1">
      <header class="uiCatalogueDemoModal__header">
        <div class="uiCatalogueDemoModal__headerCopy">
          <h3 class="uiCatalogueDemoModal__title" id="uiCatalogueDemoInputModalTitle">New document</h3>
          <p class="uiCatalogueDemoModal__meta">Docs Viewer management</p>
        </div>
      </header>
      <div class="uiCatalogueDemoModal__body">
        <label class="uiCatalogueDemoField uiCatalogueDemoField--fill" for="uiCatalogueDemoModalTitleInput">
          <span class="uiCatalogueDemoField__label">Title</span>
          <span class="uiCatalogueDemoField__control">
            <input class="uiCatalogueDemoInput" id="uiCatalogueDemoModalTitleInput" type="text" autocomplete="off" data-ui-demo-modal-required-input data-ui-demo-modal-initial-focus>
          </span>
        </label>
      </div>
      <p class="uiCatalogueDemoModal__status" data-ui-demo-modal-status hidden></p>
      <div class="uiCatalogueDemoModal__actions">
        <button class="uiCatalogueDemoButton uiCatalogueDemoButton--fixed" type="button" data-ui-demo-modal-close>Cancel</button>
        <button class="uiCatalogueDemoButton uiCatalogueDemoButton--fixed uiCatalogueDemoButton--primary" type="button" data-ui-demo-modal-submit>Create</button>
      </div>
    </div>
  </div>

  <div class="uiCatalogueDemoModal" id="uiCatalogueDemoWorkflowModal" data-ui-demo-modal data-open="false" aria-hidden="true" hidden>
    <div class="uiCatalogueDemoModal__backdrop" data-ui-demo-modal-close></div>
    <div class="uiCatalogueDemoModal__dialog uiCatalogueDemoModal__dialog--wide" role="dialog" aria-modal="true" aria-labelledby="uiCatalogueDemoWorkflowModalTitle" tabindex="-1">
      <header class="uiCatalogueDemoModal__header">
        <div class="uiCatalogueDemoModal__headerCopy">
          <h3 class="uiCatalogueDemoModal__title" id="uiCatalogueDemoWorkflowModalTitle">Import review</h3>
          <p class="uiCatalogueDemoModal__meta">series tag assignments</p>
        </div>
      </header>
      <div class="uiCatalogueDemoModal__body uiCatalogueDemoModal__body--workflow">
        <label class="uiCatalogueDemoField uiCatalogueDemoField--fill" for="uiCatalogueDemoModalConflictSelect">
          <span class="uiCatalogueDemoField__label">Conflict handling</span>
          <span class="uiCatalogueDemoField__control">
            <select class="uiCatalogueDemoInput" id="uiCatalogueDemoModalConflictSelect" data-ui-demo-modal-initial-focus>
              <option>Keep existing assignment</option>
              <option>Use imported assignment</option>
              <option>Review each conflict</option>
            </select>
          </span>
        </label>
        <dl class="uiCatalogueDemoList uiCatalogueDemoList--simple">
          <div class="uiCatalogueDemoList__row">
            <dt class="uiCatalogueDemoList__meta">rows</dt>
            <dd>24</dd>
          </div>
          <div class="uiCatalogueDemoList__row">
            <dt class="uiCatalogueDemoList__meta">conflicts</dt>
            <dd>2</dd>
          </div>
        </dl>
      </div>
      <p class="uiCatalogueDemoModal__status" data-ui-demo-modal-status data-state="warning">Preview before applying imported changes.</p>
      <div class="uiCatalogueDemoModal__actions">
        <button class="uiCatalogueDemoButton uiCatalogueDemoButton--fixed" type="button" data-ui-demo-modal-close>Cancel</button>
        <button class="uiCatalogueDemoButton uiCatalogueDemoButton--fixed" type="button">Preview</button>
        <button class="uiCatalogueDemoButton uiCatalogueDemoButton--fixed uiCatalogueDemoButton--primary" type="button" data-ui-demo-modal-submit>Apply</button>
      </div>
    </div>
  </div>

  <section class="uiCatalogueDemoSection" aria-labelledby="uiCatalogueDemoModalShellCodeHeading">
    <div class="uiCatalogueDemoSection__header">
      <h3 class="uiCatalogueDemoHeading" id="uiCatalogueDemoModalShellCodeHeading">Demo Markup</h3>
      <p class="uiCatalogueDemoSummary">The snippets show shell anatomy and local input validation in the demo namespace.</p>
    </div>
    <div class="uiCatalogueDemoCode">
      <section class="uiCatalogueDemoCode__item">
        <h4 class="uiCatalogueDemoCode__title">Shell Anatomy</h4>
        <pre><code>{{ shell_markup | escape }}</code></pre>
      </section>
      <section class="uiCatalogueDemoCode__item">
        <h4 class="uiCatalogueDemoCode__title">Input Body Slot</h4>
        <pre><code>{{ input_markup | escape }}</code></pre>
      </section>
    </div>
  </section>
</div>

<script type="module" src="{{ '/ui-catalogue/app/assets/js/ui-catalogue-demo.js' | relative_url }}?v={{ site.time | date: '%s' }}"></script>
