/* global document, window */

(() => {
  "use strict";

  const symbol = document.querySelector("#symbol");
  const button = document.querySelector("#rotate-symbol");
  const status = document.querySelector("#operation-status");
  let completedQuarterTurns = 0;

  function setOperationState(state, message) {
    button.disabled = state === "working";
    status.dataset.state = state;
    status.textContent = message;
  }

  function validateResult(value) {
    if (!value || typeof value !== "object" || Array.isArray(value)) {
      throw new Error("The application returned an invalid result.");
    }

    const keys = Object.keys(value).sort();

    if (
      value.state === "succeeded" &&
      value.quarterTurns === 1 &&
      keys.length === 2 &&
      keys[0] === "quarterTurns" &&
      keys[1] === "state"
    ) {
      return value;
    }

    if (
      value.state === "failed" &&
      typeof value.message === "string" &&
      value.message.length > 0 &&
      keys.length === 2 &&
      keys[0] === "message" &&
      keys[1] === "state"
    ) {
      throw new Error(value.message);
    }

    throw new Error("The application returned an invalid result.");
  }

  async function rotateSymbol() {
    setOperationState("working", "WORKING");

    try {
      const bridge = window.webkit?.messageHandlers?.about;
      if (!bridge) {
        throw new Error("The application bridge is unavailable.");
      }

      const result = validateResult(
        await bridge.postMessage({ action: "rotate-symbol" })
      );
      completedQuarterTurns = (completedQuarterTurns + result.quarterTurns) % 4;
      symbol.style.transform = `rotate(${completedQuarterTurns * 90}deg)`;
      setOperationState("succeeded", "ROTATED BY SWIFT");
    } catch (error) {
      const message = error instanceof Error ? error.message : "The operation failed.";
      setOperationState("failed", message.toUpperCase());
    }
  }

  button.addEventListener("click", rotateSymbol);
})();
