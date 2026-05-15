function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function escapeHtml(value) {
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
    return '<button class="docsViewer__actionButton" type="button"' + roleAttr + '>' + escapeHtml(action.label) + '</button>';
  }).join("") + '</div>';
}

function renderModalFrame(options) {
  var titleId = normalizeText(options.titleId) || "docsViewerManagementModalTitle";
  return '' +
    '<div class="docsViewer__modal" data-role="docs-viewer-management-modal">' +
      '<div class="docsViewer__modalBackdrop" data-role="modal-cancel"></div>' +
      '<div class="docsViewer__modalCard" role="dialog" aria-modal="true" aria-labelledby="' + escapeHtml(titleId) + '">' +
        '<div class="docsViewer__modalHeader">' +
          '<div class="docsViewer__modalHeaderCopy">' +
            '<h2 class="docsViewer__modalTitle" id="' + escapeHtml(titleId) + '">' + escapeHtml(options.title) + '</h2>' +
          '</div>' +
          '<button class="docsViewer__modalClose" type="button" data-role="modal-cancel" aria-label="' + escapeHtml(options.closeLabel || "Close") + '">×</button>' +
        '</div>' +
        '<form class="docsViewer__modalForm" data-role="modal-form">' +
          (options.bodyHtml || "") +
          '<p class="docsViewer__modalNote muted small" data-role="modal-status" hidden></p>' +
          renderActions(options.actions || []) +
        '</form>' +
      '</div>' +
    '</div>';
}

function openManagementModal(options = {}) {
  var host = createModalHost({ root: options.root });
  var restoreFocus = document.activeElement;
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
      try {
        if (restoreFocus && typeof restoreFocus.focus === "function") {
          restoreFocus.focus({ preventScroll: true });
        }
      } catch (_error) {
        // Focus return is best effort.
      }
    }

    function close(value) {
      cleanup();
      resolve(value);
    }

    function cancel() {
      close({ confirmed: false });
    }

    function submit() {
      var result = typeof options.onSubmit === "function"
        ? options.onSubmit({ host: host, setStatus: setStatus })
        : { confirmed: true };
      if (result === false) return;
      close(result || { confirmed: true });
    }

    function onKeydown(event) {
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
      modal.addEventListener("click", function (event) {
        if (event.target === modal) cancel();
      });
    }

    window.setTimeout(function () {
      try {
        if (focusTarget && typeof focusTarget.focus === "function") focusTarget.focus();
        if (focusTarget && typeof focusTarget.select === "function") focusTarget.select();
      } catch (_error) {
        // Focus is a convenience only.
      }
    }, 0);
  });
}

export function openDocsViewerConfirmModal(options = {}) {
  return openManagementModal({
    root: options.root,
    title: options.title,
    closeLabel: options.closeLabel || options.cancelLabel,
    bodyHtml: bodyHtmlFromText(options.body),
    actions: [
      { role: "modal-primary", label: options.primaryLabel || "OK" },
      { role: "modal-cancel", label: options.cancelLabel || "Cancel" }
    ]
  }).then(function (result) {
    return Boolean(result && result.confirmed);
  });
}

export function openDocsViewerTextInputModal(options = {}) {
  var inputId = normalizeText(options.inputId) || "docsViewerManagementModalInput";
  var bodyHtml = bodyHtmlFromText(options.body) +
    '<label class="docsViewer__field" for="' + escapeHtml(inputId) + '">' +
      '<span class="docsViewer__fieldLabel">' + escapeHtml(options.label || "Title") + '</span>' +
      '<input class="docsViewer__fieldInput" id="' + escapeHtml(inputId) + '" type="text" autocomplete="off" spellcheck="false" value="' + escapeHtml(options.initialValue || "") + '">' +
    '</label>';

  return openManagementModal({
    root: options.root,
    title: options.title,
    closeLabel: options.closeLabel || options.cancelLabel,
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

  return openManagementModal({
    root: options.root,
    title: options.title,
    closeLabel: options.closeLabel || options.cancelLabel,
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

export function buildDocsViewerDeletePreviewBody(preview) {
  var lines = ["Delete " + normalizeText(preview && preview.title) + "?"];
  if (Array.isArray(preview && preview.warnings) && preview.warnings.length) {
    lines.push("Warnings:");
    preview.warnings.forEach(function (item) {
      lines.push("- " + item);
    });
  }
  if (Array.isArray(preview && preview.inbound_refs) && preview.inbound_refs.length) {
    lines.push("Inbound refs:");
    preview.inbound_refs.slice(0, 6).forEach(function (item) {
      lines.push("- " + item.doc_id);
    });
    if (preview.inbound_refs.length > 6) {
      lines.push("- +" + (preview.inbound_refs.length - 6) + " more");
    }
  }
  return lines;
}
