---
doc_id: "_tmp"
title: tmp
added_date: 2026-05-20
last_updated: "2026-05-20 19:37"
parent_id: ""
sort_order: 40000
viewable: false
---
# tmp

docs viewer extraction:

- docs viewer needs to be self contained in a folder .docs-viewer/
- it is known to the host repo through repo owned config
- it is not part of Local Studio app. it runs in its own shell, which is started/stopped independently of Local Studio.
- it advertises it's running local host location e.g port, through config so that other pages (e.g. studio or jekyll hosted pages) can link to documents hosted by docs viewer in either public read-only docs viewer pages or local-only manage-mode docs hosted by docs viewer.


---

normal development should use:

- `bin/local-studio` for Studio
- `bin/public-site-preview` for public Jekyll preview
- `bin/public-site-preview --livereload`



---

<https://developers.openai.com/codex/migrate?utm_campaign=ML_MIX_GWT_AW_codexnewsletter_OF_EX_MAY_18&utm_content=utm_content&utm_medium=email&utm_source=sendgrid&utm_term=utm_term>

<https://developers.openai.com/codex/skills>

---

