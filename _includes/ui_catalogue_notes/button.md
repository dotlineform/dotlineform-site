### Primitive Scope

1. `tagStudio__button` currently defines the shared command-button baseline for Studio actions such as `Save`, `Open`, `Import`, `New`, `OK`, and `Cancel`.
2. Clickable pills such as tag chips are out of scope for this primitive and should be defined separately.
3. Toolbar buttons are a subset of command buttons, not a separate primitive. Future icon-only toolbar buttons should still derive their size and box model from the same shared button contract.

### Current Baseline

1. The current shared implementation is a neutral bordered button with stable height, padding, radius, and inline-flex centering.
2. The same class is used on both native `<button>` elements and command-style `<a>` links on current Studio pages.
3. Disabled buttons keep the same geometry and currently communicate state mainly through muted text and the disabled cursor.

### Modal Actions

1. Modal buttons are in scope for this primitive. The action-row layout belongs to the modal shell, but the button geometry and styling should stay shared.
2. `OK`, `Cancel`, and similar modal actions should not introduce modal-only button shapes.
3. If modal actions need stronger emphasis differences later, add those as shared button variants rather than as one-off modal styles.

### Drift To Resolve

1. Current command buttons do not yet formalize emphasis levels such as primary, secondary, or destructive, even though the product already implies those roles.
2. Docs Viewer management buttons use a separate family today. They are a useful comparison point for future toolbar-button work but are not part of the Studio shared primitive yet.
3. The first pass of this primitive should capture current shared behavior and role boundaries before adding richer variants.

### Design Guidance

1. Treat button labels as commands, not as navigation nouns. If an element behaves like a page destination rather than a direct command, it may belong to a panel-link or another primitive instead.
2. Keep button copy short enough that the shared control height and padding remain intact.
3. When stronger emphasis is needed, prefer a shared variant system over changing button size, spacing, or typography per page.
