---
doc_id: tmp
title: "tmp"
added_date: 2026-05-26
last_updated: 2026-06-26
---

Docs Index Table
viewer_report: docs_index_table
viewer_report_access: public


we are looking at the data sharing workflow and UI at `/analytics/data-sharing/prepare/`


---

I’d bring back an `actions` concept, but not as a loose per-kind bag of behavior. I’d make the registry distinguish:

- **target kind**: `tag`
- **action/directive**: `link`, `field`, maybe later `list`
- **resolver**: which module knows how to fulfill that action

So `tag` can support more than one semantic operation without pretending they are the same thing.

Example shape:

```json
{
  "kind": "tag",
  "id": {
    "normalizer": "slug",
    "input_pattern": "^[a-z0-9][a-z0-9-]*$",
    "example": "slow-looking"
  },
  "source": {
    "type": "json_map",
    "path": "analytics-app/data/canonical/tag-registry.json",
    "root_key": "tags",
    "id_field": "tag_id"
  },
  "actions": {
    "link": {
      "route": {
        "type": "docs_viewer_doc",
        "scope": "analysis",
        "doc_id_from": "id"
      },
      "source_editor": {
        "picker": true,
        "selection_search": true
      }
    },
    "field": {
      "allowed_fields": ["description", "title"],
      "default_field": "description",
      "source_editor": {
        "picker": false
      }
    }
  }
}
```

Then the source syntax could stay explicit:

```md
[[ref:tag:slow-looking]]
[[field:tag:slow-looking:description]]
```

Or, if we wanted one token family:

```md
[[semantic:tag:slow-looking|action=link]]
[[semantic:tag:slow-looking|action=field field=description]]
```

I prefer separate token families for readability: `ref` links to a thing; `field` inserts a canonical value. They can still share the same registry kind.

The important bit is that `link` and `field` should not be two route variants. A field insertion has no route. It has data-source, allowed-field, escaping/rendering, missing-value, and provenance concerns. A link has route construction and relationship-artifact concerns.

So yes, the v1 removal of `actions` was right for simplicity, but for this next layer I’d reintroduce it with a stricter meaning:

```text
kind + action = supported semantic directive
```

That gives us:

- `tag + link`: link to Analysis doc
- `tag + field`: insert canonical tag description
- `tag + related_works`: render a generated work list
- `work + link`: current semantic reference behavior
- `series + link`: current semantic reference behavior

This also keeps the builder modular: the registry says what is allowed, but focused resolver modules implement each action family.

--- 

Current public-site config lives in `public-site/config/public-site.json`. Current repo-root detection uses that file.

Still elsewhere:
- local filesystem roots and media-generation env var names
  those live in **[Pipeline Config JSON](/docs/?scope=studio&doc=config-pipeline-json)**
- Studio/search browser text and JSON path settings
  those live in **[Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json)**
- dedicated `/catalogue/search/` runtime policy
  that lives in **[Search Policy JSON](/docs/?scope=studio&doc=config-search-policy-json)**

---

list document line counts:
`find ./docs-viewer/source/studio -name "*.md" -type f -print0 | xargs -0 wc -l | sort -nr`

scripts:
`find ./docs-viewer/runtime/js -name "*.js" -type f -print0 | xargs -0 wc -l | sort -nr`

with file size:

```
find ./docs-viewer/runtime/js -name "*.js" -type f -print0 |
while IFS= read -r -d '' file; do
  lines=$(wc -l < "$file")
  size=$(du -h "$file" | cut -f1)
  printf "%8s  %8s  %s\n" "$lines" "$size" "$file"
done | sort -nr
```

---

## servers

- `bin/local-all` - Studio, Docs Viewer, docs watcher
- `bin/local-studio` - Studio + Docs Watcher: `http://127.0.0.1:8765/studio/`
- local-all also starts Local Admin App: `http://127.0.0.1:8768/admin/`
- `docs-viewer/bin/docs-viewer` - Docs Viewer: `http://127.0.0.1:8776/docs/?scope=studio&mode=manage&doc=change-requests`

- `bin/site-validate`
- `bin/site-preview`

## scripts

./docs-viewer/build/build_docs.py --write
./docs-viewer/build/build_docs.py --scope studio
./docs-viewer/build/build_docs.py --scope studio --write
./docs-viewer/build/build_docs.py --scope studio --write --only-doc-ids example-doc
./docs-viewer/build/build_search.py

./studio/services/catalogue/search/build_search.py

./docs-viewer/build/build_docs.py --scope tmp --write

---