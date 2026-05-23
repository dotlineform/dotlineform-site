---
doc_id: scripts-css-token-audit
title: CSS Token Audit
added_date: 2026-03-31
last_updated: "2026-05-09 22:35"
parent_id: ui
sort_order: 8000
viewable: true
---
# CSS Token Audit

Script:

```bash
python3 ./scripts/checks/css_token_audit.py
```

## Optional Flags

- `--md-out _docs/css-audit-latest.md`: override Markdown output path
- `assets/css/main.css assets/studio/css/studio.css`: optional file-list override

## Behavior

- scans CSS for `font-size` declarations and color literals
- reports repeated raw typography values and direct color literals
- writes the current snapshot to `_docs/css-audit-latest.md`

## Source And Target Artifacts

Source artifacts:

- default CSS inputs are whatever file list the command receives
- current common inputs are:
  - `assets/css/main.css`
  - `assets/studio/css/studio.css`

Target artifact:

- Markdown audit snapshot at `_docs/css-audit-latest.md` by default
- or the path passed through `--md-out`

## Related References

- [Scripts](/docs/?scope=studio&doc=scripts)
- [CSS Audit Spec](/docs/?scope=studio&doc=css-audit-spec)
- CSS Audit Latest
