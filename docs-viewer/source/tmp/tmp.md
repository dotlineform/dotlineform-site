---
doc_id: tmp
title: "tmp"
added_date: 2026-05-26
last_updated: 2026-06-26
---

If changing from `var/local/site.env` to `.env.local`, these are the main updates:

- Shell launchers: [bin/local-all](/Users/dlf/Developer/dotlineform/dotlineform-site/bin/local-all:8), [bin/local-studio](/Users/dlf/Developer/dotlineform/dotlineform-site/bin/local-studio:8), [bin/local-admin](/Users/dlf/Developer/dotlineform/dotlineform-site/bin/local-admin:8), [bin/local-analytics](/Users/dlf/Developer/dotlineform/dotlineform-site/bin/local-analytics:8), [bin/site-preview](/Users/dlf/Developer/dotlineform/dotlineform-site/bin/site-preview:8), [bin/site-validate](/Users/dlf/Developer/dotlineform/dotlineform-site/bin/site-validate:8).

- Python env loader: [local_env.py](/Users/dlf/Developer/dotlineform/dotlineform-site/studio/shared/python/local_env.py:12). This is the central constant used by R2 publishing and other Studio tooling.

- One direct hard-coded Docs Viewer service read: [docs_viewer_service.py](/Users/dlf/Developer/dotlineform/dotlineform-site/docs-viewer/services/docs_viewer_service.py:176).

- Error/help text in catalogue/media scripts that tells users to add values to `var/local/site.env`.

- Tests asserting the path, especially `test_local_env.py`, `test_publish_media_to_r2.py`, `test_docs_viewer_service_config.py`, and a catalogue detail-section test.

- Docs and repo instructions: [AGENTS.md](/Users/dlf/Developer/dotlineform/dotlineform-site/AGENTS.md:32), plus the Studio docs that explain local setup, local scripts, R2 publishing, Docs Viewer service config, and cloud environment behavior.

`.gitignore` already ignores `.env.local`, so that part is mostly done.

I’d probably implement this as dual support first: prefer `.env.local`, fall back to `var/local/site.env`, and warn/document that `var/local/site.env` is legacy. That avoids breaking existing local setups while making the new convention clear.

By “local setups” I mean each developer/machine’s private runtime configuration and habits around this repo.

In this repo, that likely includes:

- `var/local/site.env` containing local paths like `DOTLINEFORM_PROJECTS_BASE_DIR`
- local port overrides for Studio/Admin/Analytics/Docs Viewer
- R2/media credentials or bucket settings
- editor preferences like `DOCS_MANAGEMENT_DEFAULT_MARKDOWN_APP`
- any shell aliases, scripts, or muscle memory that assume `var/local/site.env`

So if the repo suddenly only read `.env.local`, your current machine would stop picking up the existing `var/local/site.env` until you renamed/copied it. Same for any other clone or Codespace that had followed the current docs.

“Dual support first” means the code could read `.env.local` when present, otherwise still read `var/local/site.env`, so nothing silently breaks during the transition.

`.env.local` is a common default ignore entry, and in this repo it looks like the implementation later standardized on `var/local/site.env` instead.

Current `.gitignore` has both:

```gitignore
.env.local
var/local/
var/local/site.env
```

So `.env.local` being ignored does not mean it is active. It just means it is protected if someone creates one.

Given the repo’s code and docs are consistently wired to `var/local/site.env`, I’d treat `.env.local` as an unused conventional fallback/placeholder unless you decide to migrate.

---

Docs Index Table
viewer_report: docs_index_table
viewer_report_access: public


we are looking at the data sharing workflow and UI at `/analytics/data-sharing/prepare/`

on `/analytics/data-sharing/review/`, staged 

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