---
doc_id: doc-ui-status
title: Doc UI Status
added_date: "2026-05-13 21:41"
last_updated: "2026-05-13 21:41"
parent_id: docs-viewer
sort_order: 6000
published: true
viewable: true
---
# Doc UI Status

✅ Done

🔄 In progress

😴 Deferred

❗ Urgent

⏸️ Paused

⛔ Blocked

👀 Needs review

📝 Draft

🧪 Testing

🏷️ Status menu


The popup reads from the generated browser config:

`docs-viewer/config/defaults/docs-viewer-config.json`

But that file is generated from the source config:

`docs-viewer/config/scopes/docs_scopes.json`

So the durable place to add/edit status options is:

```
"docs_viewer": {
  "ui_statuses_by_scope": {
    "studio": [
      { "ui_status": "paused", "label": "Paused", "emoji": "⏸️" },
      { "ui_status": "deferred", "label": "Deferred", "emoji": "😴" }
    ]
  }
}
```

Then regenerate with:

`./scripts/build_docs.rb --scope studio --write`

Editing `docs-viewer/config/defaults/docs-viewer-config.json` directly can work temporarily, but it will be overwritten by the next docs build.
