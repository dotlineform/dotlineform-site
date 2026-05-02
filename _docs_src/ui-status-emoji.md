---
doc_id: ui-status-emoji
title: "UI Status Emoji"
added_date: 2026-05-02
last_updated: 2026-05-02
parent_id: change-requests
sort_order: 200
---

# UI Status Emoji

## Purpose

The purpose is to enable a single emoji to be inserted at the beginning of a document title as displayed in the Docs Viewer index panel.

The emoji would be determined by a ui_status field in the document’s front matter, with the options for this field enumerated in a section of the appropriate JSON config file:

For example:

```
“ui_status": [
    {
    	“ui_status": “done”,
    	“emoji": ✅
    }
    {
    	“ui_status”: “urgent”,
    	“emoji": ❗️
    }
    }
  ]
```

- This would be a shared feature available to all scopes (Studio docs, Library, Analysis).
- If the status is not present in front-matter, or the value does not correspond to a value in config, it is ignored by the viewer.
- The status can be edited in the Doc Viewer ‘Edit’ modal (in manage mode) by selecting from a dropdown control which lists the available config values. The default is the value entered in the front-matter, if that value corresponds to one defined in config. Otherwise the dropdown is blank.
- The available status values are also displayed as small circular pills next to the ‘favourites’ pill displayed above the document. The pills contain the associated emoji. When not selected, the pills show the emoji in grey. When selected, the pills show the coloured emoji. The pills can be toggle on/off in the same way as the favourites pill.

