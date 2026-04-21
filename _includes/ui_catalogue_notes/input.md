### Primitive Scope

1. The shared input primitive covers the common user intent of assigning one field value, whether the control is free text, a dropdown, or a stepped numeric value.
2. The base shell remains `tagStudio__input`; width, label placement, and add-on controls belong to the `tagStudioField` composition layer.
3. This primitive is about field entry and field display. Command buttons beside a field remain part of the button primitive.

### Current Baseline

1. Text inputs, selects, and stepped numeric controls should all keep the same control height as the small Studio button.
2. The default field width is `18rem` unless a page sets `--field-width` deliberately.
3. Use `tagStudioField--fill` when the field should take the available row width from the left edge.
4. Labels are optional, but when present they should use an explicit layout: stacked above, inline left, or a stronger two-column form row.
5. Numeric data should default to the plain input-box presentation. Do not infer stepper UI from storage type alone.

### States

1. Disabled means the field is temporarily unavailable because some other page state has not been satisfied yet.
2. Disabled fields keep their geometry but mute the displayed value.
3. If a value is always read-only, use `tagStudio__input--readonlyDisplay` instead of `disabled` so the text stays normal while the background becomes transparent.
4. If a page needs to show a visible default value in muted styling before the user edits it, use placeholder text for text-like fields and `tagStudio__input--defaultValue` for control types that do not support placeholder behavior cleanly.
5. Default text should read lighter than normal muted labels and helper text, so it remains visibly distinct from entered content.

### Design Guidance

1. Keep stepped value controls as one field plus full-height small buttons, and use them only when the page explicitly needs step actions. Avoid half-height split-arrow controls because they break the shared row rhythm.
2. Use the inline label only when the row already reads as one compact control group. Use the two-column label when several fields need aligned labels.
3. Keep explicit width overrides local with `--field-width` rather than redefining the default width globally.
4. In two-column field rows, labels should be vertically centered against single-line inputs and top-aligned only for multiline fields such as textareas.

### Copy Guidance

1. Live Studio pages should still source visible labels, placeholders, and default values from `studio_config.json` when that copy belongs to runtime UI.
2. The catalogue page is static reference markup, so its example values can stay hard-coded.
