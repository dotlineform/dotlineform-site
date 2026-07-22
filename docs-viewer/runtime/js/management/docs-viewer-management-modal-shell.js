export function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

export function escapeHtml(value) {
  return String(value == null ? "" : value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function createModalHost(options = {}) {
  var root = options.root || document.body;
  var host = root.querySelector('[data-docs-viewer-management-modal-host="true"]');
  if (host) return host;

  host = document.createElement("div");
  host.setAttribute("data-docs-viewer-management-modal-host", "true");
  root.appendChild(host);
  return host;
}

function bodyHtmlFromText(body) {
  var lines = Array.isArray(body) ? body : String(body || "").split(/\n+/);
  return lines.map(function (line) {
    return normalizeText(line);
  }).filter(Boolean).map(function (line) {
    return '<p class="docsViewer__modalNote muted small">' + escapeHtml(line) + '</p>';
  }).join("");
}

function renderActions(actions) {
  return '<div class="docsViewer__modalActions">' + actions.map(function (action) {
    var roleAttr = action.role ? ' data-role="' + escapeHtml(action.role) + '"' : "";
    var disabledAttr = action.disabled ? " disabled" : "";
    return '<button class="docsViewer__actionButton docsViewer__actionButton--defaultWidth" type="button"' + roleAttr + disabledAttr + '>' + escapeHtml(action.label) + '</button>';
  }).join("") + '</div>';
}

function renderModalFrame(options) {
  var titleId = normalizeText(options.titleId) || "docsViewerManagementModalTitle";
  var size = normalizeText(options.size);
  var sizeClass = size ? " docsViewer__modalCard--" + escapeHtml(size) : "";
  return "" +
    '<div class="docsViewer__modal" data-role="docs-viewer-management-modal">' +
      '<div class="docsViewer__modalBackdrop" data-role="modal-cancel"></div>' +
      '<div class="docsViewer__modalCard' + sizeClass + '" role="dialog" aria-modal="true" aria-labelledby="' + escapeHtml(titleId) + '">' +
        '<div class="docsViewer__modalHeader">' +
          '<div class="docsViewer__modalHeaderCopy">' +
            '<h2 class="docsViewer__modalTitle" id="' + escapeHtml(titleId) + '">' + escapeHtml(options.title) + '</h2>' +
          '</div>' +
        '</div>' +
        '<form class="docsViewer__modalForm" data-role="modal-form">' +
          (options.bodyHtml || "") +
          '<p class="docsViewer__modalNote muted small" data-role="modal-status" hidden></p>' +
          renderActions(options.actions || []) +
        '</form>' +
      '</div>' +
    '</div>';
}

export function openDocsViewerManagementModal(options = {}) {
  var host = createModalHost({ root: options.root });
  var restoreFocus = options.restoreFocus || document.activeElement;
  var scrollRoots = [document.documentElement, document.body].filter(Boolean).map(function (node) {
    var overflow = node.style.overflow;
    node.style.overflow = "hidden";
    return { node: node, overflow: overflow };
  });
  host.innerHTML = renderModalFrame(options);

  var modal = host.querySelector('[data-role="docs-viewer-management-modal"]');
  var form = host.querySelector('[data-role="modal-form"]');
  var primary = host.querySelector('[data-role="modal-primary"]');
  var cancelNodes = host.querySelectorAll('[data-role="modal-cancel"]');
  var statusNode = host.querySelector('[data-role="modal-status"]');
  var focusTarget = options.focusSelector ? host.querySelector(options.focusSelector) : primary;

  return new Promise(function (resolve) {
    function setStatus(message) {
      if (!statusNode) return;
      statusNode.textContent = message || "";
      statusNode.hidden = !message;
      if (message) {
        statusNode.dataset.state = "error";
      } else {
        delete statusNode.dataset.state;
      }
    }

    function cleanup() {
      host.innerHTML = "";
      document.removeEventListener("keydown", onKeydown);
      scrollRoots.forEach(function (record) {
        record.node.style.overflow = record.overflow;
      });
      try {
        if (restoreFocus && typeof restoreFocus.focus === "function") {
          restoreFocus.focus({ preventScroll: true });
        }
      } catch (_error) {
        // Focus return is best effort.
      }
    }

    var api = {
      host: host,
      setStatus: setStatus
    };

    function close(value) {
      cleanup();
      resolve(value);
    }

    function cancel() {
      close({ confirmed: false });
    }

    function submit() {
      if (primary && primary.disabled) return;
      var result = typeof options.onSubmit === "function"
        ? options.onSubmit(api)
        : { confirmed: true };
      if (result === false) return;
      close(result || { confirmed: true });
    }

    function onKeydown(event) {
      if (modal && (
        event.key === "Tab" ||
        event.key === "ArrowDown" ||
        event.key === "ArrowRight" ||
        event.key === "ArrowUp" ||
        event.key === "ArrowLeft"
      )) {
        modal.dataset.keyboardNavigation = "true";
      }
      if (navigateDocsViewerModalRadioGroup(event, modal)) return;
      if (trapDocsViewerModalFocus(event, modal)) return;
      if (event.key === "Escape") {
        event.preventDefault();
        cancel();
      }
    }

    document.addEventListener("keydown", onKeydown);
    cancelNodes.forEach(function (node) {
      node.addEventListener("click", cancel);
    });
    if (primary) primary.addEventListener("click", submit);
    if (form) {
      form.addEventListener("submit", function (event) {
        event.preventDefault();
        submit();
      });
    }
    if (modal) {
      modal.addEventListener("pointerdown", function () {
        delete modal.dataset.keyboardNavigation;
      });
      modal.addEventListener("click", function (event) {
        if (event.target === modal) cancel();
      });
    }
    if (typeof options.onOpen === "function") {
      options.onOpen(api);
    }

    window.setTimeout(function () {
      try {
        if (focusTarget && typeof focusTarget.focus === "function") focusTarget.focus({ preventScroll: true });
        if (focusTarget && typeof focusTarget.select === "function") focusTarget.select();
      } catch (_error) {
        // Focus is a convenience only.
      }
    }, 0);
  });
}

function focusableControls(container) {
  if (!container) return [];
  var controls = Array.from(container.querySelectorAll([
    "button:not([disabled])",
    "input:not([disabled])",
    "select:not([disabled])",
    "textarea:not([disabled])",
    "a[href]",
    "[tabindex]:not([tabindex='-1'])"
  ].join(","))).filter(function (node) {
    return !node.hidden && node.getClientRects && node.getClientRects().length;
  });
  return controls.filter(function (node) {
    if (node.type !== "radio" || !node.name) return true;
    var group = controls.filter(function (candidate) {
      return candidate.type === "radio" &&
        candidate.name === node.name &&
        candidate.form === node.form;
    });
    var checked = group.find(function (candidate) { return candidate.checked; });
    return node === (checked || group[0]);
  });
}

export function navigateDocsViewerModalRadioGroup(event, modal) {
  var directions = {
    ArrowDown: 1,
    ArrowRight: 1,
    ArrowUp: -1,
    ArrowLeft: -1
  };
  var direction = directions[event && event.key];
  if (!direction || !modal) return false;
  var documentRef = modal.ownerDocument || document;
  var active = documentRef.activeElement;
  if (!active || !modal.contains(active) || active.type !== "radio" || !active.name) return false;
  var radios = Array.from(modal.querySelectorAll('input[type="radio"]')).filter(function (candidate) {
    return !candidate.disabled &&
      !candidate.hidden &&
      candidate.name === active.name &&
      candidate.form === active.form &&
      candidate.getClientRects &&
      candidate.getClientRects().length;
  });
  var activeIndex = radios.indexOf(active);
  if (activeIndex < 0 || !radios.length) return false;

  event.preventDefault();
  var nextIndex = (activeIndex + direction + radios.length) % radios.length;
  var next = radios[nextIndex];
  if (next === active) return true;
  next.checked = true;
  next.focus({ preventScroll: true });
  next.dispatchEvent(new Event("input", { bubbles: true }));
  next.dispatchEvent(new Event("change", { bubbles: true }));
  return true;
}

export function trapDocsViewerModalFocus(event, modal) {
  if (!modal || event.key !== "Tab") return false;
  var controls = focusableControls(modal);
  if (!controls.length) return false;
  var documentRef = modal.ownerDocument || document;
  var active = documentRef.activeElement;
  var activeIndex = modal.contains(active) ? controls.indexOf(active) : -1;
  var nextIndex;
  if (event.shiftKey) {
    nextIndex = activeIndex <= 0 ? controls.length - 1 : activeIndex - 1;
  } else {
    nextIndex = activeIndex < 0 || activeIndex >= controls.length - 1 ? 0 : activeIndex + 1;
  }
  event.preventDefault();
  controls[nextIndex].focus({ preventScroll: true });
  return true;
}

export function openDocsViewerConfirmModal(options = {}) {
  return openDocsViewerManagementModal({
    root: options.root,
    title: options.title,
    closeLabel: options.closeLabel || options.cancelLabel,
    size: options.size || "compact",
    bodyHtml: bodyHtmlFromText(options.body),
    focusSelector: options.primaryDisabled ? 'button[data-role="modal-cancel"]' : "",
    actions: [
      { role: "modal-primary", label: options.primaryLabel || "OK", disabled: options.primaryDisabled },
      { role: "modal-cancel", label: options.cancelLabel || "Cancel" }
    ]
  }).then(function (result) {
    return Boolean(result && result.confirmed);
  });
}

export function openDocsViewerNoticeModal(options = {}) {
  return openDocsViewerManagementModal({
    root: options.root,
    title: options.title,
    size: options.size || "compact",
    bodyHtml: bodyHtmlFromText(options.body),
    actions: [
      { role: "modal-primary", label: options.primaryLabel || options.closeLabel || "OK" }
    ]
  });
}

export function openDocsViewerTextInputModal(options = {}) {
  var inputId = normalizeText(options.inputId) || "docsViewerManagementModalInput";
  var bodyHtml = bodyHtmlFromText(options.body) +
    '<label class="docsViewer__field" for="' + escapeHtml(inputId) + '">' +
      '<span class="docsViewer__fieldLabel">' + escapeHtml(options.label || "Title") + '</span>' +
      '<input class="docsViewer__fieldInput" id="' + escapeHtml(inputId) + '" type="text" autocomplete="off" spellcheck="false" value="' + escapeHtml(options.initialValue || "") + '">' +
    '</label>';

  return openDocsViewerManagementModal({
    root: options.root,
    title: options.title,
    closeLabel: options.closeLabel || options.cancelLabel,
    size: options.size || "compact",
    bodyHtml: bodyHtml,
    focusSelector: "#" + inputId,
    actions: [
      { role: "modal-primary", label: options.primaryLabel || "OK" },
      { role: "modal-cancel", label: options.cancelLabel || "Cancel" }
    ],
    onSubmit: function (api) {
      var input = api.host.querySelector("#" + inputId);
      var value = normalizeText(input && input.value) || normalizeText(options.defaultValue);
      if (options.required && !value) {
        api.setStatus(options.requiredMessage || "Enter a value.");
        if (input) input.focus();
        return false;
      }
      return { confirmed: true, value: value };
    }
  });
}

export function openDocsViewerChoiceModal(options = {}) {
  var name = normalizeText(options.name) || "docsViewerManagementModalChoice";
  var selected = normalizeText(options.value);
  var choices = Array.isArray(options.choices) ? options.choices : [];
  var bodyHtml = bodyHtmlFromText(options.body) + choices.map(function (choice) {
    var value = normalizeText(choice && choice.value);
    var label = normalizeText(choice && choice.label) || value;
    var checkedAttr = value === selected ? " checked" : "";
    return '<label class="docsViewer__field docsViewer__field--checkbox">' +
      '<input class="docsViewer__checkboxInput" type="radio" name="' + escapeHtml(name) + '" value="' + escapeHtml(value) + '"' + checkedAttr + '>' +
      '<span class="docsViewer__fieldLabel">' + escapeHtml(label) + '</span>' +
    '</label>';
  }).join("");

  return openDocsViewerManagementModal({
    root: options.root,
    title: options.title,
    closeLabel: options.closeLabel || options.cancelLabel,
    size: options.size || "compact",
    bodyHtml: bodyHtml,
    focusSelector: 'input[name="' + name + '"]',
    actions: [
      { role: "modal-primary", label: options.primaryLabel || "OK" },
      { role: "modal-cancel", label: options.cancelLabel || "Cancel" }
    ],
    onSubmit: function (api) {
      var input = api.host.querySelector('input[name="' + name + '"]:checked');
      var value = normalizeText(input && input.value);
      if (!value) {
        api.setStatus(options.requiredMessage || "Choose an option.");
        return false;
      }
      return { confirmed: true, value: value };
    }
  });
}
