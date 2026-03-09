Yes. That is the actual problem.

On pages like Tag Studio, the visual contract is buried inside JS-generated HTML in [tag-studio.js](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/studio/js/tag-studio.js#L300), where it emits classes like `tagStudio__panel`, `tagStudio__inputRow`, `tagStudio__button`, `tagStudio__popupInner`. Those classes are then styled in [studio.css](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/studio/css/studio.css), but you cannot see the markup shape from the template file. That makes CSS editing harder because the DOM is effectively hidden in JS.

So there are really two separate issues:

1. JS/CSS coupling
- JS logic queries or toggles style classes.
- Fix with `data-role` and ARIA/data-state for behavior.

2. Hidden markup
- The markup carrying those classes only exists inside JS strings.
- Fix by making the generated structure more visible and centralized.

For this repo, I think the practical approach is:

- Keep `class` for styling.
- Keep `data-role` for JS lookup.
- Move JS-generated markup into a small render contract instead of scattering raw class strings through behavior code.

Example shape:

```js
// studio-ui.js
export const UI = {
  role: {
    saveButton: "save",
    popup: "popup",
    popupList: "popup-list"
  },
  selector: {
    saveButton: '[data-role="save"]',
    popup: '[data-role="popup"]',
    popupList: '[data-role="popup-list"]'
  },
  className: {
    panel: "tagStudio__panel",
    editorPanel: "tagStudio__panel--editor",
    inputRow: "tagStudio__inputRow",
    button: "tagStudio__button",
    buttonPrimary: "tagStudio__button--primary",
    popup: "tagStudio__popup",
    popupInner: "tagStudio__popupInner"
  }
};
```

Then rendering code uses `UI.className.*`, and behavior code uses `UI.selector.*`.

That does not make the markup fully visible in the Jekyll template, but it does make the styling contract visible in one file instead of hidden across many JS functions.

If your main goal is “I want to see the DOM structure when editing CSS”, the stronger solution is to move more of that shell markup into actual HTML templates:
- Jekyll include or page markup if mostly static
- `<template>` element in the page if JS needs to clone/fill it

That is cleaner than long JS template strings, but it is a bigger refactor.

So my recommendation is:
- Short term: introduce a small UI contract for JS-generated Studio markup and stop JS behavior from depending on CSS classes.
- Medium term: for the biggest Studio shells, move repeated HTML structure out of JS strings and into template markup.

Benefits:
- CSS classes become easier to find and rename.
- JS behavior becomes independent from presentation names.
- Studio DOM structure becomes more legible.

Risks:
- A contract file adds some indirection.
- Moving markup into templates is cleaner but larger in scope.

If you want, I can outline the smallest safe refactor for `tag-studio.js` specifically, without changing behavior.