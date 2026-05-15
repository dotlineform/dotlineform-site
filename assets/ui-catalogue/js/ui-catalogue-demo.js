function setDemoRouteReady() {
  document.querySelectorAll("[data-ui-catalogue-demo-route]").forEach((root) => {
    root.setAttribute("data-ui-catalogue-demo-ready", "true");
    root.setAttribute("data-ui-catalogue-demo-busy", "false");
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
  initDemoModals();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initUiCatalogueDemos);
} else {
  initUiCatalogueDemos();
}
