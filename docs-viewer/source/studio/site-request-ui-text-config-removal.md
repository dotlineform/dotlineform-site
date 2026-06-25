---
doc_id: site-request-ui-text-config-removal
title: UI Text Config Removal
added_date: 2026-06-25
last_updated: 2026-06-25
parent_id: change-requests
---
# UI Text Config Removal

Review each remaining app UI-text bundle and remove config-time UI text where the copy is design-time product copy.

The Docs Viewer cleanup is the model:

1. Review every value in the UI-text JSON bundle.
2. Classify each value as either design-time copy, runtime data, or no longer needed.
3. For design-time copy, move the literal to the module that owns the UI.
4. For labels already present in rendered markup, make the renderer authoritative and remove post-render label mutation.
5. For modal/action copy, split constants by ownership instead of creating a central replacement bucket.
6. For values set to an empty string, remove the label, hint, span, paragraph, or code path that existed only for that value.
7. Remove fallback copy in code when the UI-text source is retired.
8. Remove the JSON file, route/config references, service/static mappings, cache/version candidates, and fetch/merge plumbing.
9. Update tests, check contracts, and docs so they describe active assets only. Do not add negative tests for retired URLs.
10. Run targeted syntax, JSON, service, and stale-reference checks.

For Docs Viewer this meant:

- deleting `manage.json` and `public.json`
- removing `config_urls.ui_text`
- deleting the UI-text fetch/merge path from the runtime
- moving static labels into renderers
- moving modal/action copy into owner constants
- keeping only genuine runtime/config values as dedicated state, such as `docNonViewableEmoji`

Apply the same rule to other apps: UI text config should exist only when non-developer configuration is a real product requirement. Ordinary labels, buttons, modal prompts, status strings, and empty placeholder copy should be owned by the code module that renders or drives that UI.

Suggested migration checklist for each app:

- Scan for the bundle path and all key reads.
- Review the JSON values manually before editing code.
- Remove one bundle or feature group at a time.
- Prefer local constants over a new shared text registry.
- Keep tests focused on active behavior and active assets.
- End with a stale-reference scan for the deleted filename, config keys, loader functions, and route fields.
