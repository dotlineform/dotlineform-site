---
doc_id: d-20260911-152718-b21705
title: Data Model
added_date: "2026-09-11 15:27:18"
last_updated: "2026-10-03 15:00:00"
draft: false
---
# Data Model

All identities are described using doc front-matter fields.

## Concepts and Moments

**Concepts** and **Moments** have document-owned identities:

- the sub-scope defines the **type**: `sub-scope: concepts` or `sub-scope: moments`
- the doc title defines the entity: `title: absence`

The document itself is the defined concept, e.g. **all** docs in sub-scope `concepts` are by definition 'concepts'.

### UI

There is no specific UI for making a document a 'concept' or 'moment'.

The front matter fields are updated when:
- a new sub-scope doc is created
- doc is copied into the sub-scope
- a doc is imported into the sub-scope

[check: this should be owned by doc-build]

### JSON

No JSON files are used.


## Catalogue Subject associations

**Catalogue** subjects are owned by Studio. A doc subject-type field associates a document with a specific Catalogue subject:

- a work, e.g. `work_id: 00521`
- a work detail, e.g. `detail_uid: 00521-007`
- a series, e.g. `series_id: "001"`
- an external source folder, e.g. `folder_path: projects/3 symbols (book)`

This association between a doc and a Catalogue subject can only be made for docs in sub-scope `analysis/works`.  
However, associating a doc with a Catalogue subject is **optional**.

### UI Process

Docs are given a subject association using the **Assign subject** modal, called from a button on the doc toolbar.

### JSON

The selected subject is recorded in:  
`analysis/working/generated/sub-scopes/works/documents/subject-associations.json`

This example record describes the subject association of `doc_id: d-20260911-100212-71100f` with `work_id: 00520`:

```
{
  "subject": {
    "kind": "work",
    "key": "00520"
  },
  "documents": [
    {
      "target": {
        "scope": "analysis",
        "sub_scope": "works",
        "doc_id": "d-20260911-100212-71100f"
      },
      "locations": [
        {
          "access": "manage",
          "url": "/docs/?collection=works&doc=d-20260911-100212-71100f"
        }
      ]
    }
  ]
},
```

## Links

Any doc can link to any other doc, but **both** need to be publishable i.e. `publishable: true`

### Process

A link to another doc is inserted into body content using the **Insert doc link** modal, called from a button on the doc toolbar.

The link is a normal markdown doc link, e.g.  
`[3 symbols](</docs/?collection=works&doc=d-20260801-212422-df11f3>)`
