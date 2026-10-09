We need to make incremental updates to the Catalogue metadata **and** media, and apply the same principle to Publish.

current state:
- media is saved in `assets/works/`. it is updated by Studio when a work's media is edited and Saved. This is shared between `working` and `preview`, so media in both is always current in both.
- metadata is saved by Studio in `working/generated/catalogue/`, it is current in Working after Studio Refresh, current in Preview after Publish.
- `working/source/collections/catalogue/updates-pending.json` accumulates changed/deleted Work IDs from Studio Refresh's generated-file writes/deletions and clears them only after the required Catalogue Regenerate source/Build work completes.

proposed:
- media is saved in `working/assets/works/`. it is updated by Studio when a work's media is edited and Saved.
- media is Published to `preview/assets/works/`. it is updated by Publish
- metadata is saved by Studio in `working/generated/catalogue/`, it is current in Working after Studio Refresh.
- `working/catalogue-updates-pending.json` accumulates changed/deleted Work IDs from Studio Refresh's generated-file writes/deletions and clears them only after the required Catalogue Regenerate source/Build work completes.
- When a work has been updated in Catalogue, the pending record is copied into `working/catalogue-publish-pending.json`. This indicates to Publish what Catalogue metadata and media have been changed since last Publish.
- Publish uses `publish-pending.json` to copy:
  - metadata into `preview/catalogue/`
  - Catalogue docs into `preview/collections/catalogue/`
  - media into `preview/assets/works/`

current `updates-pending.json`:
```
{
  "schema": "catalogue_updates_pending_v1",
  "current_work_ids": [
    "03181",
    "04625"
  ],
  "deleted_work_ids": []
}
```
proposed, show what has changed by work:
```
{
  "schema": "catalogue_updates_pending_v2",
  "current_work_ids": [
    "03181":{
      metadata: true,
      image: true,
      files: true
    },
    "04625"{
      metadata: true,
      image: false,
      files: false
    }
  ],
  "deleted_work_ids": []
}
```

- regenerate one work at a time: copy json and/or media, regenerate the Catalogue doc.
- the pending record is deleted after copy and regenerate completes and `catalogue-publish-pending.json` has been updated.
- stop on error, report the `work_id` that failed.