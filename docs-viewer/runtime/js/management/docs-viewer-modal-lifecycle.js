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
  var EventConstructor = documentRef.defaultView && documentRef.defaultView.Event;
  if (EventConstructor) {
    next.dispatchEvent(new EventConstructor("input", { bubbles: true }));
    next.dispatchEvent(new EventConstructor("change", { bubbles: true }));
  }
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

function resolveNode(value) {
  return typeof value === "function" ? value() : value;
}

function focusNode(node, selectText) {
  if (!node || typeof node.focus !== "function") return;
  try {
    node.focus({ preventScroll: true });
  } catch (_error) {
    node.focus();
  }
  if (selectText && typeof node.select === "function") node.select();
}

export function createDocsViewerModalLifecycle(options = {}) {
  var modal = options.modal;
  if (!modal) throw new Error("Docs Viewer modal lifecycle requires a modal root");
  var documentRef = options.document || modal.ownerDocument || document;
  var windowRef = documentRef.defaultView || window;
  var cancelElements = Array.from(options.cancelElements || []);
  var active = false;
  var destroyed = false;
  var initialFocusTimer = null;
  var restoreFocusTimer = null;
  var restoreFocus = null;
  var scrollRoots = [];

  function requestClose(reason, event) {
    if (!active || typeof options.onRequestClose !== "function") return false;
    return options.onRequestClose({ event: event, reason: reason }) !== false;
  }

  function onCancelClick(event) {
    requestClose(
      event.currentTarget && event.currentTarget.classList.contains("docsViewer__modalBackdrop")
        ? "backdrop"
        : "cancel",
      event
    );
  }

  function onModalClick(event) {
    if (event.target === modal) requestClose("backdrop", event);
  }

  function onPointerDown() {
    delete modal.dataset.keyboardNavigation;
  }

  function onKeydown(event) {
    if (!active) return;
    if (
      event.key === "Tab" ||
      event.key === "ArrowDown" ||
      event.key === "ArrowRight" ||
      event.key === "ArrowUp" ||
      event.key === "ArrowLeft"
    ) {
      modal.dataset.keyboardNavigation = "true";
    }
    if (navigateDocsViewerModalRadioGroup(event, modal)) return;
    if (trapDocsViewerModalFocus(event, modal)) return;
    if (event.key !== "Escape") return;
    if (typeof options.consumeEscape === "function" && options.consumeEscape(event)) return;
    event.preventDefault();
    requestClose("escape", event);
  }

  function addListeners() {
    documentRef.addEventListener("keydown", onKeydown);
    modal.addEventListener("pointerdown", onPointerDown);
    modal.addEventListener("click", onModalClick);
    cancelElements.forEach(function (node) {
      node.addEventListener("click", onCancelClick);
    });
  }

  function removeListeners() {
    documentRef.removeEventListener("keydown", onKeydown);
    modal.removeEventListener("pointerdown", onPointerDown);
    modal.removeEventListener("click", onModalClick);
    cancelElements.forEach(function (node) {
      node.removeEventListener("click", onCancelClick);
    });
  }

  function lockScroll() {
    scrollRoots = [documentRef.documentElement, documentRef.body].filter(Boolean).map(function (node) {
      var overflow = node.style.overflow;
      node.style.overflow = "hidden";
      return { node: node, overflow: overflow };
    });
  }

  function restoreScroll() {
    scrollRoots.forEach(function (record) {
      record.node.style.overflow = record.overflow;
    });
    scrollRoots = [];
  }

  function focusInitial() {
    if (!active) return false;
    focusNode(resolveNode(options.initialFocus), options.selectInitialFocus === true);
    return true;
  }

  function open(openOptions = {}) {
    if (active || destroyed) return false;
    if (restoreFocusTimer !== null) {
      windowRef.clearTimeout(restoreFocusTimer);
      restoreFocusTimer = null;
    }
    restoreFocus = openOptions.restoreFocus ||
      resolveNode(options.restoreFocus) ||
      documentRef.activeElement;
    active = true;
    delete modal.dataset.keyboardNavigation;
    lockScroll();
    addListeners();
    initialFocusTimer = windowRef.setTimeout(function () {
      initialFocusTimer = null;
      focusInitial();
    }, 0);
    return true;
  }

  function close() {
    if (!active) return false;
    active = false;
    if (initialFocusTimer !== null) {
      windowRef.clearTimeout(initialFocusTimer);
      initialFocusTimer = null;
    }
    if (documentRef.activeElement && modal.contains(documentRef.activeElement)) {
      documentRef.activeElement.blur();
    }
    removeListeners();
    restoreScroll();
    delete modal.dataset.keyboardNavigation;
    var returnTarget = restoreFocus;
    restoreFocus = null;
    restoreFocusTimer = windowRef.setTimeout(function () {
      restoreFocusTimer = null;
      if (active) return;
      focusNode(returnTarget, false);
    }, 0);
    return true;
  }

  function destroy() {
    if (destroyed) return false;
    close();
    destroyed = true;
    return true;
  }

  return {
    close: close,
    destroy: destroy,
    focusInitial: focusInitial,
    isActive: function () { return active; },
    open: open
  };
}
