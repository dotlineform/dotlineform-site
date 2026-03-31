---
doc_id: scripts-srcset-builder
title: Srcset Builder
last_updated: 2026-03-30
parent_id: scripts
sort_order: 40
---

# Srcset Builder

Stable shell entrypoint:

```bash
bash scripts/make_srcset_images.sh
```

The shell entrypoint remains stable, but it delegates to the shared config-driven Python implementation.

Works example:

```bash
MAKE_SRCSET_WORK_IDS_FILE=/tmp/copied_work_ids.txt \
MAKE_SRCSET_SUCCESS_IDS_FILE=/tmp/work_success_ids.txt \
bash scripts/make_srcset_images.sh \
  "$DOTLINEFORM_MEDIA_BASE_DIR/works/make_srcset_images" \
  "$DOTLINEFORM_MEDIA_BASE_DIR/works/srcset_images" \
  4
```

Moments example:

```bash
MAKE_SRCSET_WORK_IDS_FILE=/tmp/copied_moment_ids.txt \
MAKE_SRCSET_SUCCESS_IDS_FILE=/tmp/moment_success_ids.txt \
bash scripts/make_srcset_images.sh \
  "$DOTLINEFORM_MEDIA_BASE_DIR/moments/make_srcset_images" \
  "$DOTLINEFORM_MEDIA_BASE_DIR/moments/srcset_images" \
  4
```

Moment source discovery uses the configured moments images directory plus a fixed source filename of `<moment_id>.jpg`.
If that source file is missing, the copy step skips it.

## Related References

- [Scripts Overview](/docs/?scope=studio&doc=scripts-overview)
- [Main Draft Pipeline](/docs/?scope=studio&doc=scripts-main-pipeline)
- [Copy Draft Media](/docs/?scope=studio&doc=scripts-copy-draft-media)
