---
doc_id: local-setup-public-site-preview
title: Local Setup Public Site Preview
added_date: 2026-05-23
last_updated: 2026-06-12
parent_id: local-setup
---
# Local Setup Public Site Preview

The public site and Local Studio use separate commands.

Use `bin/local-studio` for Studio services.
Use `bin/public-site-preview` or `bin/public-site-build` for public-site static work.

## Preview versus build

`bin/public-site-preview` builds the static artifact and serves it with Python's HTTP server.
It is the normal command when you want to open the public site in a browser while editing public route renderers, CSS, JavaScript, public assets, generated public payloads, or public Docs Viewer runtime/config files.

```bash
bin/public-site-preview
```

The preview command runs the static builder first:

```bash
$HOME/miniconda3/bin/python3 public-site/build/build_site.py --destination _public_site --audit
```

Then it serves `_public_site/` at `http://127.0.0.1:4000/`.

`bin/public-site-build` runs the same builder and exits.
Use it when you want to produce or verify the built site output without keeping a local preview server running.

```bash
bin/public-site-build --destination /tmp/dlf-public-site-build --audit
```

## CSS and runtime changes

The static preview command rebuilds once at startup.
After changing public CSS, JavaScript, route renderer code, public config, or generated public payloads, restart `bin/public-site-preview` or rerun `bin/public-site-build`.

Browser cache can hide a CSS or JavaScript update; hard refresh if the page still shows the old assets.

## Artifact boundary

Only files copied or rendered into the configured destination are part of the public artifact.
`public-site/config/public-site.json` owns the public file/tree allowlists, required artifact checks, denied source paths, and public runtime config values.

Generated local output stays untracked:

- `_public_site/` for local preview output
- `/tmp/dlf-public-site-build` or another temporary destination for isolated checks

## Wrapper defaults

The wrapper:

- changes into the repo root
- loads `var/local/site.env` when present
- uses `PUBLIC_SITE_PYTHON`, defaulting to `$HOME/miniconda3/bin/python3` when available
- uses `PUBLIC_SITE_HOST`, defaulting to `127.0.0.1`
- uses `PUBLIC_SITE_PORT`, defaulting to `4000`
- uses `PUBLIC_SITE_DESTINATION`, defaulting to `_public_site`
- runs the artifact audit unless `--no-audit` is passed

Examples:

```bash
bin/public-site-preview --port 4010
bin/public-site-preview --destination /tmp/dlf-public-site-preview
bin/public-site-preview --no-audit
```

The preview server is a static HTTP server. It does not watch files, run LiveReload, or start Local Studio services.

## Related References

- [Local Setup](/docs/?scope=studio&doc=local-setup)
- [Local Studio Runner](/docs/?scope=studio&doc=scripts-local-studio)
- [Local Studio App](/docs/?scope=studio&doc=local-studio-app)
- [GitHub Actions](/docs/?scope=studio&doc=github-actions)
