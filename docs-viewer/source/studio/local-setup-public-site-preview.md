---
doc_id: local-setup-public-site-preview
title: Local Setup Public Site Preview
added_date: 2026-05-23
last_updated: 2026-06-13
parent_id: local-setup
---
# Local Setup Public Site Preview

The public site and Local Studio use separate commands.

Use `bin/local-studio` for Studio services.
Use `bin/site-preview` for public-site static preview work and `bin/site-validate` for deploy-root validation.

## Preview versus validation

`bin/site-preview` validates the checked-in static site root and serves `site/` with Python's HTTP server.
It is the normal command when you want to open the public site in a browser while editing public route HTML, CSS, JavaScript, public assets, generated public payloads, or public Docs Viewer runtime/config files.

```bash
bin/site-preview
```

The preview command runs validation first:

```bash
bin/site-validate --site-root site
```

Then it serves `site/` at `http://127.0.0.1:4000/`.

`bin/site-validate` runs the same deploy-root validation and exits.
Use it when you want to verify the checked-in static site without keeping a local preview server running.

```bash
bin/site-validate
```

## CSS and runtime changes

The static preview command serves files directly from `site/`.
After changing public CSS, JavaScript, route HTML, site-tools config, or generated public payloads, refresh the browser and rerun `bin/site-validate` when deploy readiness matters.

Browser cache can hide a CSS or JavaScript update; hard refresh if the page still shows the old assets.

## Site root boundary

`site/` is the tracked static deploy root.
Public browser URLs such as `/assets/...` resolve inside that root, so their filesystem paths live under `site/assets/...`.

`site-tools/config/site-tools.json` owns deploy-root validation requirements and durable site-level settings used by local Python tooling.

## Wrapper defaults

The preview wrapper:

- changes into the repo root
- loads `var/local/site.env` when present
- uses `SITE_PYTHON`, defaulting to `$HOME/miniconda3/bin/python3` when available
- uses `SITE_HOST`, defaulting to `127.0.0.1`
- uses `SITE_PORT`, defaulting to `4000`
- uses `SITE_ROOT`, defaulting to `site`
- runs validation unless `--no-validate` is passed

Examples:

```bash
bin/site-preview --port 4010
bin/site-preview --site-root site
bin/site-preview --no-validate
```

The preview server is a static HTTP server. It does not watch files, run LiveReload, or start Local Studio services.

## Related References

- [Local Setup](/docs/?scope=studio&doc=local-setup)
- [Local Studio Runner](/docs/?scope=studio&doc=scripts-local-studio)
- [Local Studio App](/docs/?scope=studio&doc=local-studio-app)
- [GitHub Actions](/docs/?scope=studio&doc=github-actions)
