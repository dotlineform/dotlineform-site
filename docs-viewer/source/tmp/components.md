---
doc_id: components
title: "components"
added_date: 2026-06-26
last_updated: 2026-06-26
---

> I thought the component would take much more work away from the consumer, to the point where the consumer would just say 'here's what file to use for the data' as opposed to actually do the list population and search rules etc.

Right. What we extracted is a **UI interaction primitive**, not a complete “search this dataset” product component.

It takes away:

- popup rendering lifecycle
- focus behavior
- select-all-on-focus
- Escape reset
- Tab close/reset
- ArrowUp/ArrowDown behavior
- Enter commit
- active row scrolling
- pointer vs keyboard selection state
- ARIA wiring
- commit/cancel callbacks

It deliberately does **not** take away:

- where data comes from
- how records are shaped
- what field is committed
- matching rules
- row layout/content
- what committing means

That split is why the same primitive can support:
- folder prefix search in the file picker
- work id/title search in the Work editor
- later, maybe series/member search with different rules

If we made it “give me a JSON file and I’ll search it,” it would become a higher-level component. That may be useful, but it should probably be a wrapper on top of `search-list`, for example:

```js
bindRecordSearch(input, popup, {
  loadRecords,
  fields: ["title"],
  idField: "work_id",
  mode: "contains",
  renderRecord,
  onSelect
});
```

So the current component is the reusable engine. We can still build more opinionated components on top once two or three consumers prove the same data/search pattern is repeating.

> I suppose eventually you would get to a point where the component has evolved into a full-blown plugin

There’s a rough progression:

1. **Primitive**
   `search-list`: owns generic interaction behavior, knows nothing about works/folders/files.

2. **Pattern Component**
   `file-picker`: combines primitives into a reusable workflow, knows about folders/subfolders/files but not Studio project paths.

3. **App Adapter**
   `catalogue-project-media-picker`: maps the generic picker to Studio’s `project_folder/project_subfolder/project_filename` fields and Studio APIs.

4. **Plugin / Package**
   If the same thing needs to travel across apps or repos, it gets its own config, assets, tests, docs, versioning expectations, and integration contract.

The important bit is not to jump straight to stage 4. A plugin too early usually freezes bad assumptions. What we’re doing now is better: extract stable behavior once it repeats, then only promote it when the boundaries are proven.