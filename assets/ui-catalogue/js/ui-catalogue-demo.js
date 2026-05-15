function setDemoRouteReady() {
  document.querySelectorAll("[data-ui-catalogue-demo-route]").forEach((root) => {
    root.setAttribute("data-ui-catalogue-demo-ready", "true");
    root.setAttribute("data-ui-catalogue-demo-busy", "false");
  });
}

function initDemoModals() {
  document.querySelectorAll("[data-ui-demo-modal]").forEach((modal) => {
    const openers = document.querySelectorAll(`[data-ui-demo-modal-open="${modal.id}"]`);
    const closeControls = modal.querySelectorAll("[data-ui-demo-modal-close]");
    let returnFocusTarget = null;

    const close = () => {
      modal.dataset.open = "false";
      modal.setAttribute("aria-hidden", "true");
      if (returnFocusTarget && typeof returnFocusTarget.focus === "function") {
        returnFocusTarget.focus();
      }
      returnFocusTarget = null;
    };

    const open = (event) => {
      returnFocusTarget = event.currentTarget;
      modal.dataset.open = "true";
      modal.setAttribute("aria-hidden", "false");
      const focusTarget = modal.querySelector("[data-ui-demo-modal-initial-focus]");
      if (focusTarget && typeof focusTarget.focus === "function") {
        focusTarget.focus();
      }
    };

    openers.forEach((opener) => {
      opener.addEventListener("click", open);
    });

    closeControls.forEach((control) => {
      control.addEventListener("click", close);
    });

    modal.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        close();
      }
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
