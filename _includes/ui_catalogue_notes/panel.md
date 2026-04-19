The panel is the default shared surface wrapper for grouped content in Studio.

Use it when a section needs clear containment, stable spacing, and a predictable shell without becoming a full card system or a custom page-specific box.

For the first pass, keep the contract narrow:

- reuse the shared shell before inventing a page-local alternative
- vary internal content before varying the outer chrome
- treat `editor` and `compact` as named variants rather than one-off tweaks

The live examples above should stay tied to the real shared classes. If the production panel changes, this page should change with it.
