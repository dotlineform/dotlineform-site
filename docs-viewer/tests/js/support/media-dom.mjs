// Minimal non-browser DOM for deterministic Media View lifetime and data-flow contracts.
export class FakeElement {
  constructor(tagName, documentRef) {
    this.tagName = String(tagName || "").toUpperCase();
    this.ownerDocument = documentRef;
    this.attributes = new Map();
    this.children = [];
    this.parentElement = null;
    this.listeners = new Map();
    this.className = "";
    this.dataset = {};
    this.style = { setProperty() {} };
    this.textContent = "";
    this.tabIndex = -1;
  }

  appendChild(child) {
    if (child.parentElement) {
      child.parentElement.children = child.parentElement.children.filter((item) => item !== child);
    }
    child.parentElement = this;
    this.children.push(child);
    return child;
  }

  replaceChildren(...children) {
    this.children.forEach((child) => { child.parentElement = null; });
    this.children = [];
    children.forEach((child) => this.appendChild(child));
  }

  setAttribute(name, value) {
    this.attributes.set(String(name), String(value));
  }

  getAttribute(name) {
    return this.attributes.has(String(name)) ? this.attributes.get(String(name)) : null;
  }

  removeAttribute(name) {
    this.attributes.delete(String(name));
  }

  addEventListener(name, handler) {
    this.listeners.set(String(name), handler);
  }

  removeEventListener(name, handler) {
    if (this.listeners.get(String(name)) === handler) this.listeners.delete(String(name));
  }

  matches(selector) {
    if (selector === '[data-docs-content-detail="media"]') {
      return this.getAttribute("data-docs-content-detail") === "media";
    }
    if (selector === "[data-docs-media-open]") {
      return this.attributes.has("data-docs-media-open");
    }
    if (selector === "[data-docs-media-image]" || selector === "[data-docs-media-placeholder]") {
      return this.attributes.has(selector.slice(1, -1));
    }
    if (selector === 'script[type="application/json"][data-docs-media-presentation]') {
      return this.tagName === "SCRIPT"
        && this.getAttribute("type") === "application/json"
        && this.attributes.has("data-docs-media-presentation");
    }
    if (selector.startsWith(".")) {
      return this.className.split(/\s+/).includes(selector.slice(1));
    }
    return this.tagName === selector.toUpperCase();
  }

  querySelectorAll(selector) {
    var matches = [];
    this.children.forEach(function visit(child) {
      if (child.matches(selector)) matches.push(child);
      child.children.forEach(visit);
    });
    return matches;
  }

  querySelector(selector) {
    return this.querySelectorAll(selector)[0] || null;
  }

  contains(candidate) {
    if (candidate === this) return true;
    return this.children.some((child) => child.contains(candidate));
  }

  remove() {
    if (!this.parentElement) return;
    this.parentElement.children = this.parentElement.children.filter((item) => item !== this);
    this.parentElement = null;
  }

  focus() {
    this.focused = true;
  }

  dispatchClick() {
    var prevented = false;
    var handler = this.listeners.get("click");
    if (handler) {
      handler({ preventDefault() { prevented = true; } });
    }
    return prevented;
  }
}

export class FakeDocument {
  createElement(tagName) {
    return new FakeElement(tagName, this);
  }
}
