### Primitive Scope

1. `tagStudio__button` currently defines the shared command-button baseline for Studio actions such as `Save`, `Open`, `Import`, `New`, `OK`, and `Cancel`.
2. Buttons are commands, not links. If an element behaves as navigation, treat it as a link pattern rather than styling it as a button.
3. Clickable pills such as tag chips are out of scope for this primitive and should be defined separately.
4. Buttons do not need to live inside a toolbar. Toolbar remains an optional composition primitive to define later.

### Current Baseline

1. The shared implementation is a neutral bordered button with stable radius, inline-flex centering, and no special destructive styling.
2. The primitive now defines two sizes only: small and medium.
3. The primary use case for the small size is a command button placed next to a text field in the same row.
4. Button-related status, warning, and success messages should stay adjacent to the related command area, either on the same row or in a dedicated row immediately below it.
5. The shared contract also defines a standard default width, but existing live Studio pages still need a later sweep to adopt it consistently.
6. Disabled buttons keep the same geometry and currently communicate state mainly through muted text and the disabled cursor.

### Modal Actions

1. Modal buttons are in scope for this primitive. The action-row layout belongs to the modal shell, but the button geometry and styling should stay shared.
2. The default modal action should be explicit through bold text.
3. `OK`, `Cancel`, and similar modal actions should not introduce modal-only button shapes.

### Drift To Resolve

1. Some current Studio pages still use anchor-styled buttons for navigation actions such as creating a new related record. Those should move to a link pattern rather than staying inside the button primitive.
2. Current live pages also contain labels such as `Save Tags` that should likely be shortened to `Save` in a later consistency sweep.
3. The first pass of this primitive should capture the role boundary and size/width contract before wider page adoption.

### Design Guidance

1. Keep button copy short enough that the shared default width remains viable. `Session` is a reasonable practical width reference for the current contract.
2. If a button genuinely needs to be wider, override only that button rather than widening adjacent buttons to match it.
3. Buttons should contain either text or an icon, not both.
4. If buttons need grouping or a boundary, do not use a panel as the grouping device.
5. Destructive actions should continue to use warning or confirmation prompts, but they do not need a special button style by default.

### Feedback Placement

1. If a button needs status, warning, or result copy, place that copy directly beside the related button row or immediately below it.
2. Do not route button feedback into a distant shared message area when the button is associated with a specific field or local command group.
3. On a row that already needs space for another control such as save mode, prefer a dedicated feedback row below the buttons rather than forcing the message into the same line.
