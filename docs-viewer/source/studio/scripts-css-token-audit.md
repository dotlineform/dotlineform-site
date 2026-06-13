---
doc_id: scripts-css-token-audit
title: CSS Token Audit
added_date: 2026-03-31
last_updated: "2026-05-26"
parent_id: ui
viewable: true
---
# CSS Token Audit

Script:

```bash
$HOME/miniconda3/bin/python3 admin-app/checks/css_token_audit.py
```

## Optional Flags

- `--md-out var/studio/reports/css-audit-latest.md`: override Markdown output path
- `site/assets/css/main.css assets/studio/css/studio.css`: optional file-list override

## Behavior

- scans CSS for `font-size` declarations and color literals
- reports repeated raw typography values and direct color literals
- writes the current snapshot to `var/studio/reports/css-audit-latest.md`

## Source And Target Artifacts

Source artifacts:

- default CSS inputs are whatever file list the command receives
- current common inputs are:
  - `site/assets/css/main.css`
  - `site/assets/studio/css/studio.css`

Target artifact:

- Markdown audit snapshot at `var/studio/reports/css-audit-latest.md` by default
- or the path passed through `--md-out`

## Related References

- [Scripts](/docs/?scope=studio&doc=scripts)
- [CSS Audit Spec](/docs/?scope=studio&doc=css-audit-spec)
- CSS Audit Latest
