function setDemoRouteReady() {
  document.querySelectorAll("[data-ui-catalogue-demo-route]").forEach((root) => {
    root.setAttribute("data-ui-catalogue-demo-ready", "true");
    root.setAttribute("data-ui-catalogue-demo-busy", "false");
  });
}

function visibleMenuItems(surface, selector) {
  if (!surface) return [];
  return Array.from(surface.querySelectorAll(selector))
    .filter((item) => !item.hidden && !item.disabled && item.getClientRects().length);
}

function focusMenuItem(items, current, direction) {
  if (!items.length) return;
  const index = items.indexOf(current);
  const nextIndex = index < 0
    ? (direction > 0 ? 0 : items.length - 1)
    : (index + direction + items.length) % items.length;
  items[nextIndex].focus();
}

function handleMenuNavigation(event, surface, selector, close) {
  const items = visibleMenuItems(surface, selector);
  if (event.key === "Escape") {
    event.preventDefault();
    close({ restoreFocus: true });
    return true;
  }
  if (event.key === "ArrowDown") {
    event.preventDefault();
    focusMenuItem(items, document.activeElement, 1);
    return true;
  }
  if (event.key === "ArrowUp") {
    event.preventDefault();
    focusMenuItem(items, document.activeElement, -1);
    return true;
  }
  if (event.key === "Home") {
    event.preventDefault();
    if (items[0]) items[0].focus();
    return true;
  }
  if (event.key === "End") {
    event.preventDefault();
    if (items[items.length - 1]) items[items.length - 1].focus();
    return true;
  }
  if (event.key === "Tab") {
    close();
  }
  return false;
}

function initDemoActionMenus() {
  document.querySelectorAll("[data-ui-demo-action-menu]").forEach((menu) => {
    const trigger = menu.querySelector("[data-ui-demo-menu-trigger]");
    const surface = menu.querySelector("[data-ui-demo-menu-surface]");
    const status = menu.parentElement ? menu.parentElement.querySelector("[data-ui-demo-action-status]") : null;
    if (!trigger || !surface) return;

    const close = (options = {}) => {
      surface.hidden = true;
      trigger.setAttribute("aria-expanded", "false");
      if (options.restoreFocus && typeof trigger.focus === "function") {
        trigger.focus({ preventScroll: true });
      }
    };

    const open = (focusTarget = "first") => {
      if (trigger.disabled) return;
      surface.hidden = false;
      trigger.setAttribute("aria-expanded", "true");
      const items = visibleMenuItems(surface, "[role='menuitem']");
      const target = focusTarget === "last" ? items[items.length - 1] : items[0];
      if (target && typeof target.focus === "function") target.focus();
    };

    trigger.addEventListener("click", () => {
      if (surface.hidden) {
        open();
      } else {
        close();
      }
    });

    trigger.addEventListener("keydown", (event) => {
      if (event.key === "ArrowDown") {
        event.preventDefault();
        open();
      }
      if (event.key === "ArrowUp") {
        event.preventDefault();
        open("last");
      }
      if (event.key === "Escape") {
        close();
      }
    });

    surface.addEventListener("keydown", (event) => {
      handleMenuNavigation(event, surface, "[role='menuitem']", close);
    });

    surface.addEventListener("click", (event) => {
      const item = event.target instanceof Element ? event.target.closest("[data-ui-demo-action]") : null;
      if (!(item instanceof HTMLButtonElement) || item.disabled) return;
      if (status) {
        status.textContent = item.dataset.uiDemoActionMessage || `${item.textContent.trim()} selected.`;
        status.dataset.state = "success";
      }
      close({ restoreFocus: true });
    });

    document.addEventListener("click", (event) => {
      if (surface.hidden || menu.contains(event.target)) return;
      close();
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !surface.hidden) close({ restoreFocus: true });
    });
    window.addEventListener("scroll", () => close(), { passive: true });
    window.addEventListener("resize", () => close());
  });
}

function initDemoNativeSelects() {
  document.querySelectorAll("[data-ui-demo-native-select]").forEach((select) => {
    const example = select.closest(".uiCatalogueDemoExample");
    const status = example ? example.querySelector("[data-ui-demo-native-select-status]") : null;
    const update = () => {
      if (!status) return;
      const option = select.options[select.selectedIndex];
      status.textContent = `${option ? option.textContent.trim() : select.value} selected.`;
      status.dataset.state = "success";
    };
    select.addEventListener("change", update);
  });
}

function initDemoSelectMenus() {
  document.querySelectorAll("[data-ui-demo-select-menu]").forEach((menu) => {
    const trigger = menu.querySelector("[data-ui-demo-select-trigger]");
    const list = menu.querySelector("[data-ui-demo-select-list]");
    const labelNode = menu.querySelector("[data-ui-demo-select-label]");
    const triggerEmoji = trigger ? trigger.querySelector(".uiCatalogueDemoMenu__emoji") : null;
    const example = menu.closest(".uiCatalogueDemoExample");
    const status = example ? example.querySelector("[data-ui-demo-select-status]") : null;
    if (!trigger || !list || !labelNode) return;

    const close = (options = {}) => {
      list.hidden = true;
      trigger.setAttribute("aria-expanded", "false");
      if (options.restoreFocus && typeof trigger.focus === "function") {
        trigger.focus({ preventScroll: true });
      }
    };

    const open = (focusTarget = "selected") => {
      if (trigger.disabled) return;
      list.hidden = false;
      trigger.setAttribute("aria-expanded", "true");
      const items = visibleMenuItems(list, "[data-ui-demo-select-option]");
      let target = items.find((item) => item.getAttribute("aria-selected") === "true");
      if (focusTarget === "first") target = items[0];
      if (focusTarget === "last") target = items[items.length - 1];
      if (target && typeof target.focus === "function") target.focus();
    };

    const selectOption = (option) => {
      if (!(option instanceof HTMLButtonElement) || option.disabled) return;
      const label = option.dataset.label || option.textContent.trim();
      const emoji = option.dataset.emoji || "";
      menu.dataset.uiDemoSelectValue = option.dataset.value || "";
      labelNode.textContent = label;
      if (triggerEmoji) triggerEmoji.textContent = emoji;
      list.querySelectorAll("[data-ui-demo-select-option]").forEach((item) => {
        item.setAttribute("aria-selected", item === option ? "true" : "false");
      });
      if (status) {
        status.textContent = `${emoji ? `${emoji} ` : ""}${label} selected.`;
        status.dataset.state = "success";
      }
      close({ restoreFocus: true });
    };

    trigger.addEventListener("click", () => {
      if (list.hidden) {
        open();
      } else {
        close();
      }
    });

    trigger.addEventListener("keydown", (event) => {
      if (event.key === "ArrowDown") {
        event.preventDefault();
        open("first");
      }
      if (event.key === "ArrowUp") {
        event.preventDefault();
        open("last");
      }
      if (event.key === "Escape") {
        close();
      }
    });

    list.addEventListener("keydown", (event) => {
      handleMenuNavigation(event, list, "[data-ui-demo-select-option]", close);
      if (event.key === "Enter" || event.key === " ") {
        const option = document.activeElement;
        if (option && option.matches("[data-ui-demo-select-option]")) {
          event.preventDefault();
          selectOption(option);
        }
      }
    });

    list.addEventListener("click", (event) => {
      const option = event.target instanceof Element ? event.target.closest("[data-ui-demo-select-option]") : null;
      selectOption(option);
    });

    document.addEventListener("click", (event) => {
      if (list.hidden || menu.contains(event.target)) return;
      close();
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !list.hidden) close({ restoreFocus: true });
    });
    window.addEventListener("scroll", () => close(), { passive: true });
    window.addEventListener("resize", () => close());
  });
}

function initDemoModals() {
  const focusableSelector = [
    "a[href]",
    "button:not([disabled])",
    "input:not([disabled])",
    "select:not([disabled])",
    "textarea:not([disabled])",
    "[tabindex]:not([tabindex='-1'])"
  ].join(",");

  document.querySelectorAll("[data-ui-demo-modal]").forEach((modal) => {
    const openers = document.querySelectorAll(`[data-ui-demo-modal-open="${modal.id}"]`);
    const closeControls = modal.querySelectorAll("[data-ui-demo-modal-close]");
    const submitControls = modal.querySelectorAll("[data-ui-demo-modal-submit]");
    const dialog = modal.querySelector('[role="dialog"]');
    const status = modal.querySelector("[data-ui-demo-modal-status]");
    let returnFocusTarget = null;

    const setStatus = (message, state = "warning") => {
      if (!status) return;
      status.textContent = message || "";
      status.hidden = !message;
      if (message) {
        status.dataset.state = state;
      } else {
        delete status.dataset.state;
      }
    };

    const close = () => {
      modal.dataset.open = "false";
      modal.setAttribute("aria-hidden", "true");
      modal.hidden = true;
      setStatus("");
      if (returnFocusTarget && typeof returnFocusTarget.focus === "function") {
        returnFocusTarget.focus({ preventScroll: true });
      }
      returnFocusTarget = null;
    };

    const open = (event) => {
      returnFocusTarget = event.currentTarget;
      modal.hidden = false;
      modal.dataset.open = "true";
      modal.setAttribute("aria-hidden", "false");
      const focusTarget = modal.querySelector("[data-ui-demo-modal-initial-focus]")
        || modal.querySelector(focusableSelector)
        || dialog;
      if (focusTarget && typeof focusTarget.focus === "function") {
        focusTarget.focus();
      }
    };

    const focusableNodes = () => Array.from(modal.querySelectorAll(focusableSelector))
      .filter((node) => !node.closest("[hidden]") && node.getClientRects().length);

    const submit = () => {
      const requiredInput = modal.querySelector("[data-ui-demo-modal-required-input]");
      if (requiredInput && !String(requiredInput.value || "").trim()) {
        setStatus(modal.dataset.uiDemoModalRequiredMessage || "Complete the required field before continuing.");
        requiredInput.focus();
        return;
      }
      close();
    };

    const handleKeydown = (event) => {
      if (event.key === "Escape") {
        event.preventDefault();
        close();
        return;
      }
      if (event.key !== "Tab") return;

      const nodes = focusableNodes();
      if (!nodes.length) return;
      const first = nodes[0];
      const last = nodes[nodes.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
        return;
      }
      if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };

    openers.forEach((opener) => {
      opener.addEventListener("click", open);
    });

    closeControls.forEach((control) => {
      control.addEventListener("click", close);
    });

    submitControls.forEach((control) => {
      control.addEventListener("click", submit);
    });

    modal.addEventListener("keydown", handleKeydown);

    modal.addEventListener("submit", (event) => {
      event.preventDefault();
      submit();
    });
  });
}

function initUiCatalogueDemos() {
  setDemoRouteReady();
  initDemoActionMenus();
  initDemoNativeSelects();
  initDemoSelectMenus();
  initDemoModals();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initUiCatalogueDemos);
} else {
  initUiCatalogueDemos();
}
